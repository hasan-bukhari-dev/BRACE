import csv
import hashlib
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from brace_app import server
from brace_core.intake import parse_cohort
from brace_core import signature

BASE=Path(__file__).resolve().parents[1]
PAIR=BASE/'examples/public_er_pair'

@pytest.fixture
def client():return TestClient(server.app)

def test_all_public_rows_and_values_match_saved_evidence(client,monkeypatch):
    result=json.loads((PAIR/'race_final/race_result.json').read_text())
    frozen=json.loads((PAIR/'race_final/selected_signature.json').read_text())
    originals={}
    for role in ('source','target'):
        with (PAIR/f'prepared/{role}_expression.tsv').open() as stream:
            rows=csv.reader(stream,delimiter='\t');head=next(rows)
            originals[role]={row[0]:dict(zip(head[1:],map(float,row[1:]))) for row in rows if row[0] in {r['feature_id'] for r in result['genes']}}
    monkeypatch.setattr(signature,'feature_test',lambda *args:pytest.fail('FACE must not run tests'))
    monkeypatch.setattr(signature,'run',lambda *args:pytest.fail('FACE must not rerun RACE'))
    meta=client.get('/api/race/studies/public_er_pass2/genes').json()
    assert meta['aggregate']==result['aggregate']
    assert len(meta['genes'])==20 and meta['genes'][0]['gene_symbol']=='NCOA7'
    assert meta['cohorts']['source']['n_samples']==101 and meta['cohorts']['target']['n_samples']==87
    for actual,saved in zip(meta['genes'],result['genes']):
        assert all(actual[k]==v for k,v in saved.items())
        response=client.get('/api/race/studies/public_er_pass2/gene',params={'feature_id':saved['feature_id']})
        assert response.status_code==200,response.text
        detail=response.json();src=next(r for r in frozen['selected'] if r['feature_id']==saved['feature_id'])
        assert detail['cohorts']['source']['statistics']==src
        assert detail['cohorts']['target']['statistics']==saved
        for role,c in detail['cohorts'].items():
            samples=[s for g in c['groups'] for s in g['samples']]
            assert {s['sample_id']:s['value'] for s in samples}==originals[role][saved['feature_id']]
            assert sum(g['observed_n'] for g in c['groups'])==c['n_samples']
            assert c['missing_values']==0
        assert detail['cohorts']['source']['preparation']['exclusions']=={'non_tumor':17,'ER_missing':3}
        assert detail['trace']['no_statistical_rerun'] is True
        assert detail['trace']['hypothesis_hash']==result['hypothesis_hash']

@pytest.fixture
def user_run(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'RUNS',tmp_path)
    rid='a'*32;root=tmp_path/rid;raw=root/'input';raw.mkdir(parents=True)
    for role in ('source','target'):
        ids=[f'{role}{i}' for i in range(12)]
        manifest=dict(schema_version='1.0.0',cohort_id=role,role=role,organism='Homo sapiens',feature_namespace='gene_symbol',
            measurement_type='microarray_log2_normalized',processing_description='log2 RMA',labels='binary',independence_declaration='unknown',platform='GPL570')
        (raw/f'{role}_manifest.json').write_text(json.dumps(manifest))
        with (raw/f'{role}_metadata.tsv').open('w',newline='') as f:
            w=csv.writer(f,delimiter='\t');w.writerow(['sample_id','condition','patient_id','study_id'])
            w.writerows([s,'positive' if i<6 else 'negative',s,role] for i,s in enumerate(ids))
        with (raw/f'{role}_expression.tsv').open('w',newline='') as f:
            w=csv.writer(f,delimiter='\t');w.writerow(['feature_id',*ids])
            for feature in (('a','b','noise') if role=='source' else ('a','noise')):
                w.writerow([feature,*[i%3 if feature=='noise' else i%6+(10 if i<6 else 0) for i in range(12)]])
    cohorts=[parse_cohort(raw/f'{r}_expression.tsv',raw/f'{r}_metadata.tsv',raw/f'{r}_manifest.json',r) for r in ('source','target')]
    cfg=dict(positive='positive',negative='negative',source_conditions={'positive':'positive tumor','negative':'negative tumor'},target_conditions={'positive':'positive tumor','negative':'negative tumor'})
    signature.run(*cohorts,cfg,root/'race')
    (root/'run.json').write_text(json.dumps(dict(id=rid,mode='race',input_hashes={},notes=[])))
    server.race_response(root)
    return rid,root

def test_missing_target_gene_is_unavailable_not_zero(client,user_run):
    rid,root=user_run
    detail=client.get(f'/api/race/studies/{rid}/gene',params={'feature_id':'b'}).json()
    assert detail['feature']['classification']=='untestable'
    target=detail['cohorts']['target'];assert not target['available']
    assert target['statistics']['q'] is None and target['missing_values'] is None
    assert all(not g['samples'] for g in target['groups'])
    assert target['unavailable_reason']=='missing_target_feature'
    assert detail['feature']['gene_symbol'] is None
    assert detail['cohorts']['source']['preparation'] is None

@pytest.mark.parametrize('changed',['input/source_expression.tsv','race/race_result.json','race/selected_signature.json'])
def test_mutated_input_or_evidence_fails_closed(client,user_run,changed):
    rid,root=user_run;p=root/changed;p.write_bytes(p.read_bytes()+b'\n')
    response=client.get(f'/api/race/studies/{rid}/gene',params={'feature_id':'a'})
    assert response.status_code==409 and 'no replacement' in response.json()['detail']['message']

def test_unavailable_ids_and_safe_paths(client,user_run):
    rid,_=user_run
    assert client.get(f'/api/race/studies/{rid}/gene',params={'feature_id':'../source_manifest.json'}).status_code==404
    assert client.get('/api/race/studies/not-a-run/genes').status_code==404
    assert client.get('/api/race/studies/public_er_pass2/gene',params={'feature_id':'9999999'}).status_code==404

def test_generic_measurements_do_not_require_public_example(client,user_run,monkeypatch,tmp_path):
    rid,_=user_run;monkeypatch.setattr(server,'BASE',tmp_path/'absent-example')
    response=client.get(f'/api/race/studies/{rid}/gene',params={'feature_id':'a'})
    assert response.status_code==200 and response.json()['feature']['gene_symbol'] is None
