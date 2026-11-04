"""Pass 5 evidence linkage and independent row reconciliation; no new engine."""
import csv
import hashlib
import io
import json
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from brace_app import server
from brace_core import stage06_cli, metrics06

BASE=Path(__file__).resolve().parents[1]

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'RUNS',tmp_path/'runs')
    return TestClient(server.app)

def upload_predictions(client,prob=True,threshold=.955,empty=False):
    manifest=dict(schema_version='1.0.0',dataset_id='controlled_test',model_id='supplied_test_scores',classes=['A','B','C'],
        probability_columns={c:'p_'+c for c in 'ABC'} if prob else {},prediction_origin='external_model',evaluation_role='external_exploratory',
        independence_declaration='unknown',label_source_description='Explicit test fixture',primary_confidence_threshold=threshold)
    data='sample_id,true_label,predicted_label'+(',p_A,p_B,p_C' if prob else '')+'\n'
    for sid,truth,score in [('equal','B',.955),('certain','A',1.),('lower','A',.6)]:
        if empty:score=.6
        data+=sid+','+truth+',A'+(f',{score},{1-score},0' if prob else '')+'\n'
    response=client.post('/api/analyze',data={'mode':'evaluate_predictions'},files={
        'predictions':('test.csv',data,'text/csv'),'prediction_manifest':('manifest.json',json.dumps(manifest),'application/json')})
    assert response.status_code==200,response.text
    return response.json()

def test_historical_metrics_and_every_curve_point_reconcile(client):
    response=client.get('/api/ace/studies/historical_cptac');assert response.status_code==200,response.text
    info=response.json();v=info['validation'];m=v['metrics'];rows=v['records']
    assert len(rows)==m['n']==680 and sum(r['correct'] for r in rows)==m['n_correct']==668
    assert len(v['errors'])==12 and info['source_cv'] is None and info['kind']=='historical'
    for i,truth in enumerate(m['class_order']):
        assert m['confusion_matrix'][i]==[sum(r['true_label']==truth and r['predicted_label']==pred for r in rows) for pred in m['class_order']]
    observed=[]
    for c in m['per_class']:
        support=sum(r['true_label']==c['class'] for r in rows);predicted=sum(r['predicted_label']==c['class'] for r in rows)
        tp=sum(r['true_label']==r['predicted_label']==c['class'] for r in rows)
        assert (c['support'],c['predicted_count'],c['tp'])==(support,predicted,tp)
        if support:observed.append(c);assert c['f1']==pytest.approx(2*tp/(predicted+support))
        else:assert c['recall'] is None and c['f1'] is None
    assert m['balanced_accuracy_observed']==pytest.approx(sum(c['recall'] for c in observed)/len(observed))
    assert m['supported_class_macro_f1']==pytest.approx(sum(c['f1'] for c in observed)/len(observed))
    assert m['absent_true_classes']==['prostate'] and m['macro_denominator']==4
    for p in v['threshold_curve']:
        kept=[r for r in rows if r['confidence']>=p['threshold']];right=sum(r['correct'] for r in kept)
        assert (p['retained'],p['correct'],p['errors'])==(len(kept),right,len(kept)-right)
        assert p['selective_accuracy']==(right/len(kept) if kept else None)
        assert p['selective_risk']==((len(kept)-right)/len(kept) if kept else None)
    fixed=next(p for p in v['threshold_curve'] if p['threshold']==.95)
    assert fixed['retained']==584 and fixed['correct']==583

def test_actual_high_confidence_error_and_archived_trace(client):
    v=client.get('/api/ace/studies/historical_cptac').json()['validation']
    row=max(v['errors'],key=lambda r:r['confidence'])
    assert row['confidence']==.998692106 and row['true_label']=='breast' and row['predicted_label']=='ovary'
    detail=client.get('/api/ace/studies/historical_cptac',params={'sample_id':row['sample_id']}).json()
    assert detail['selection']['record']==row and detail['selection']['related_shift'] is None
    trace=client.get('/api/trace/studies/historical_cptac',params={'sample_id':row['sample_id']}).json()
    assert trace['selection']=={'sample_id':row['sample_id']} and trace['kind']=='historical'
    steps={s['key']:s for s in trace['steps']}
    assert steps['folds']['status']=='not_performed' and steps['scoring']['status']=='not_performed'
    assert steps['model']['status']=='declared' and steps['result']['data']['record']==row
    assert all('public-er' not in a['url'] for a in trace['artifacts'])
    for artifact in trace['artifacts']:
        response=client.get(artifact['url']);assert response.status_code==200
        assert hashlib.sha256(response.content).hexdigest()==artifact['sha256']

@pytest.mark.parametrize('prob,empty',[(True,False),(False,False),(True,True)])
def test_imported_scores_exact_reference_missing_classes_and_empty(client,prob,empty):
    run=upload_predictions(client,prob=prob,empty=empty);info=client.get('/api/ace/studies/'+run['id']).json();v=info['validation']
    assert info['source_cv'] is None and info['frozen_model_hash'] is None
    absent=next(c for c in v['metrics']['per_class'] if c['class']=='C')
    assert absent['precision'] is None and absent['recall'] is None and absent['f1'] is None
    if prob:
        fixed=next(p for p in v['threshold_curve'] if p['threshold']==.955)
        assert fixed['threshold_role']=='predeclared_reference'
        if empty:assert fixed['retained']==0 and fixed['selective_accuracy'] is None and fixed['selective_risk'] is None
        else:assert fixed['retained']==2 and fixed['errors']==1
        assert v['threshold_curve'][0]['retained']==3
        assert v['threshold_curve'][-1]['retained']==(0 if empty else 1)
    else:assert v['threshold_curve']==[] and all(r['confidence'] is None for r in v['records'])
    trace=client.get('/api/trace/studies/'+run['id'],params={'sample_id':'equal'}).json()
    assert trace['selection']['sample_id']=='equal' and trace['evaluation_role']=='external_exploratory'
    assert not trace['provenance_authenticated']

def test_source_cv_frozen_model_and_same_run_shift(client,monkeypatch):
    run=client.post('/api/demo/synthetic').json();rid=run['id']
    monkeypatch.setattr(stage06_cli,'train',lambda *a,**k:pytest.fail('Trace must not train'))
    monkeypatch.setattr(metrics06,'reliability_analysis',lambda *a,**k:pytest.fail('Trace must not recalculate metrics'))
    response=client.get('/api/ace/studies/'+rid);assert response.status_code==200,response.text
    info=response.json()
    stage=json.loads((server.RUNS/rid/'validation/stage05/run_result.json').read_text())
    assert info['source_cv']['metrics']==stage['outputs']['source_cv']
    assert info['source_cv']['seed']==42 and info['source_cv']['folds']==5
    row=run['validation']['records'][0]
    detail=client.get('/api/ace/studies/'+rid,params={'sample_id':row['sample_id']}).json()
    assert detail['selection']['record']==row
    assert detail['selection']['related_shift']['association']['sample_id']==row['sample_id']
    chain=client.get('/api/trace/studies/'+rid,params={'sample_id':row['sample_id']}).json()
    assert chain['kind']=='synthetic' and chain['study_id']==rid
    steps={s['key']:s for s in chain['steps']};assert steps['model']['data']['model_sha256']==info['frozen_model_hash']
    assert steps['folds']['status']=='computed' and steps['scoring']['status']=='computed'
    for artifact in chain['artifacts']:
        data=client.get(artifact['url']);assert data.status_code==200
        assert hashlib.sha256(data.content).hexdigest()==artifact['sha256']

@pytest.mark.parametrize('path',['input/predictions.csv','validation/validation_result.json'])
def test_changed_inputs_or_outputs_fail_closed(client,path):
    run=upload_predictions(client);p=server.RUNS/run['id']/path;p.write_bytes(p.read_bytes()+b'\n')
    for endpoint in ('ace','trace'):
        response=client.get(f'/api/{endpoint}/studies/'+run['id'])
        assert response.status_code==409 and response.json()['detail']['code']=='TRACE_EVIDENCE_UNAVAILABLE'

def test_changed_historical_evidence_fails_closed(client,tmp_path,monkeypatch):
    for name in ('stage06_cptac_report','cancershift_historical_cptac'):
        shutil.copytree(BASE/'examples'/name,tmp_path/'examples'/name)
    (tmp_path/'docs').mkdir();shutil.copy2(BASE/'docs/PASS05_ARCHIVED_REFERENCE.json',tmp_path/'docs/PASS05_ARCHIVED_REFERENCE.json')
    monkeypatch.setattr(server,'BASE',tmp_path);monkeypatch.setattr(server,'EXAMPLES',tmp_path/'examples')
    p=tmp_path/'examples/stage06_cptac_report/validation_result.json';p.write_bytes(p.read_bytes()+b'\n')
    assert client.get('/api/ace/studies/historical_cptac').status_code==409

def test_race_trace_exact_gene_and_hash(client):
    response=client.get('/api/trace/studies/public_er_pass2',params={'feature_id':'135112'})
    assert response.status_code==200,response.text
    chain=response.json();result=json.loads((BASE/'examples/public_er_pair/race_final/race_result.json').read_text())
    assert chain['selection']=={'feature_id':'135112'} and chain['hypothesis_hash']==result['hypothesis_hash']
    assert [s['key'] for s in chain['steps']]==['inputs','compatibility','screen','freeze','target','result']
    assert chain['steps'][4]['data']['selected_gene_target_record']==result['genes'][0]
    assert len(chain['steps'][3]['data']['selected_feature_ids'])==20
    assert client.get('/api/trace/studies/public_er_pass2',params={'feature_id':'missing'}).status_code==404
    assert client.get('/api/trace/studies/public_er_pass2',params={'feature_id':'135112','sample_id':'other'}).status_code==422

def test_mode_c_trace_excludes_outcomes_even_if_input_labels_exist(client):
    folder=BASE/'examples/synthetic_valid'
    names={f'{role}_{field}':f'{role}_{"samples" if field=="metadata" else field}.{ext}' for role in ('source','target') for field,ext in (('expression','csv'),('metadata','csv'),('manifest','json'))}
    files={key:(name,(folder/name).read_bytes()) for key,name in names.items()}
    run=client.post('/api/analyze',data={'mode':'diagnose_shift'},files=files).json();rid=run['id']
    info=client.get('/api/ace/studies/'+rid).json();assert info['validation'] is None and info['source_cv'] is None
    trace=client.get('/api/trace/studies/'+rid).json()
    text=json.dumps(trace)
    assert trace['evaluation_role']=='unlabeled_shift_only'
    assert all(key not in text for key in ('observed_conditions','true_label','predicted_label','class_composition','confusion_matrix','n_correct'))
    assert client.get('/api/trace/studies/'+rid,params={'sample_id':'not-allowed'}).status_code==404

def test_trace_paths_and_unrelated_selection(client):
    for endpoint in ('ace','trace'):assert client.get(f'/api/{endpoint}/studies/not-a-run').status_code==404
    assert client.get('/api/ace/studies/historical_cptac',params={'sample_id':'../../other'}).status_code==404
    assert client.get('/api/trace/studies/public_er_pass2').status_code==404
