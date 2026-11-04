"""Actual neutral Mode A workflows, capability-specific checks and saved history."""
import csv,hashlib,io,json,re,zipfile
from collections import Counter
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from brace_app import server
BASE=Path(__file__).resolve().parents[1]
@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'RUNS',tmp_path/'runs');server.RUNS.mkdir()
    with TestClient(server.app) as client:yield client
def predictions(client,name):
    folder=BASE/'examples/design3_prediction_fixtures'/name
    return client.post('/api/analyze',data={'mode':'evaluate_predictions'},files={'predictions':('predictions.csv',(folder/'predictions.csv').read_bytes(),'text/csv'),'prediction_manifest':('manifest.json',(folder/'manifest.json').read_bytes(),'application/json')})
@pytest.mark.parametrize('name',['equipment_faults','text_categories'])
def test_controlled_nonbiological_predictions_compute_and_export(client,name):
    response=predictions(client,name);assert response.status_code==200,response.text
    d=response.json();v=d['validation'];assert (v['n'],v['metrics']['n_correct'])==(6,4)
    rows=list(csv.DictReader((BASE/'examples/design3_prediction_fixtures'/name/'predictions.csv').open()))
    classes=v['metrics']['class_order'];confusion=[[sum(r['true_label']==a and r['predicted_label']==b for r in rows) for b in classes] for a in classes]
    assert v['metrics']['confusion_matrix']==confusion
    at95=next(p for p in v['threshold_curve'] if p['threshold']==.95);at1=next(p for p in v['threshold_curve'] if p['threshold']==1)
    assert (at95['retained'],at95['correct'])==(2,1) and at1['retained']==0 and at1['selective_accuracy'] is None
    package=client.get('/api/embrace/'+d['id']);assert package.status_code==200,package.text
    with zipfile.ZipFile(io.BytesIO(package.content)) as z:
        assert z.testzip() is None;html=z.read('research_summary.html').decode();text=re.sub('<[^>]+>',' ',html)
        for name in ('research_summary.html','validation/run_report.html'):
            view=re.sub('<[^>]+>',' ',z.read(name).decode())
            bad=re.search(r'\b(patients?|tumou?rs?|cohorts?|genes?|biomarkers?)\b',view,re.I)
            assert bad is None,view[max(0,bad.start()-80):bad.end()+100] if bad else ''
        assert '4 correct predictions among 6 evaluated records' in text and text.index('4 correct')<text.index('Run ID')
        for row in csv.DictReader(io.StringIO(z.read('FILE_SHA256_MANIFEST.csv').decode())):assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
        assert not any(n.startswith('input/') for n in z.namelist())
    assert client.get('/api/ace/studies/'+d['id']).status_code==200
    listing=client.get('/api/runs').json()['runs'];assert len(listing)==1 and listing[0]['id']==d['id'] and listing[0]['has_result']
def test_capabilities_match_existing_file_contracts(client):
    data=client.get('/api/capabilities').json();assert data['schema_version']=='brace.tasks/1.0'
    tasks=data['tasks'];assert set(tasks)=={'race','evaluate_predictions','train_validate','diagnose_shift'}
    assert tasks['evaluate_predictions']['files']==['predictions','prediction_manifest']
    assert tasks['evaluate_predictions']['domain']=='structured_classification'
    assert all(len(tasks[k]['files'])==6 for k in ('race','train_validate','diagnose_shift'))
    assert data['limits']['upload_bytes']==server.MAX_FILE==25*1024*1024
def cohort_uploads(folder,public=False):
    entries={}
    for role in ('source','target'):
        for field,filename in ([('expression',role+'_expression.tsv'),('metadata',role+'_metadata.tsv'),('manifest',role+'_manifest.json')] if public else [('expression',role+'_expression.csv'),('metadata',role+'_samples.csv'),('manifest',role+'_manifest.json')]):
            entries[role+'_'+field]=(filename,(folder/filename).read_bytes(),'application/json' if field=='manifest' else 'text/csv')
    return entries
def test_public_contrast_has_distinct_existing_task_eligibility(client):
    pair=BASE/'examples/public_er_pair';response=client.post('/api/preflight',data={'mode':'race','race_config':(pair/'race_config.json').read_text()},files=cohort_uploads(pair/'prepared',True));assert response.status_code==200
    data=response.json();assert data['eligible'] and data['preview']['source']['n_samples']==101 and data['preview']['target']['n_samples']==87
    checks=data['task_eligibility'];assert checks['race']['status']=='eligible_with_caveats';assert checks['train_validate']['status']=='blocked'
    assert any(i['code']=='LABEL_MAPPING_INCONSISTENT' for i in checks['train_validate']['issues'])
    assert checks['diagnose_shift']['status']=='eligible_with_caveats'
def test_unlabeled_preflight_does_not_infer_supervised_eligibility(client):
    response=client.post('/api/preflight',data={'mode':'diagnose_shift'},files=cohort_uploads(BASE/'examples/synthetic_valid'));assert response.status_code==200
    data=response.json();assert data['eligible'];assert all('observed_conditions' not in c for c in data['preview'].values())
    assert data['task_eligibility']['train_validate']['status']=='not_checked'
def test_history_skips_nonruns_and_malformed_configs(client):
    (server.RUNS/'private.txt').write_text('do not expose')
    folder=server.RUNS/('a'*32);folder.mkdir();(folder/'run.json').write_text('invalid JSON')
    folder=server.RUNS/'not-a-run';folder.mkdir();(folder/'run.json').write_text('{"mode":"race","name":"not a generated id"}')
    response=client.get('/api/runs');assert response.status_code==200 and response.json()['runs']==[]
    assert 'do not expose' not in response.text
def test_regression_shaped_input_is_not_silently_treated_as_declared_classes(client):
    folder=BASE/'examples/design3_prediction_fixtures/equipment_faults';manifest=json.loads((folder/'manifest.json').read_text());manifest['task']='regression'
    response=client.post('/api/analyze',data={'mode':'evaluate_predictions'},files={'predictions':('regression.csv','sample_id,true_label,predicted_label\nx,0.5,0.7\n'),'prediction_manifest':('manifest.json',json.dumps(manifest))})
    assert response.status_code==422

@pytest.mark.parametrize('tamper',[False,True])
def test_report_upgrade_preserves_science_and_rejects_old_zip_tampering(client,monkeypatch,tamper):
    from brace_app import embrace
    current=embrace.VERSION;monkeypatch.setattr(embrace,'VERSION','explicit-previous-report-fixture')
    response=predictions(client,'equipment_faults');assert response.status_code==200
    rid=response.json()['id'];folder=server.RUNS/rid;original=(folder/'validation/validation_result.json').read_bytes()
    if tamper:(folder/'RESEARCH_PACKAGE.zip').write_bytes(b'changed published evidence')
    monkeypatch.setattr(embrace,'VERSION',current)
    result=client.get('/api/embrace/'+rid)
    assert result.status_code==(409 if tamper else 200)
    assert (folder/'validation/validation_result.json').read_bytes()==original
