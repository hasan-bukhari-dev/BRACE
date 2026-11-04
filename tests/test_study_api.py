import hashlib
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from brace_app import server

BASE=Path(__file__).resolve().parents[1]

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'RUNS',tmp_path)
    return TestClient(server.app)

def uploads(predictions=False,invalid=False):
    folder=BASE/'examples'/('synthetic_prediction_input' if predictions else 'synthetic_valid')
    names={'predictions':'predictions.csv','prediction_manifest':'manifest.json'} if predictions else {f'{r}_{k}':f'{r}_{v}' for r in ('source','target') for k,v in [('expression','expression.csv'),('metadata','samples.csv'),('manifest','manifest.json')]}
    result={k:(v,(folder/v).read_bytes()) for k,v in names.items()}
    if invalid:result['source_expression']=('bad.csv',b'feature_id,S,S\na,1,2\n')
    return result

def test_real_example_is_pinned_and_saved(client):
    r=client.get('/api/example/public-er');assert r.status_code==200
    d=r.json();assert d['kind']=='public_computed' and 'saved' in d['data_label']
    assert d['race']['aggregate']['supported']==14 and d['cohorts']['source']['samples']==101
    assert 'source_screen' not in d['race']
    result=client.get('/api/example/public-er/export/race_result.json').json()
    assert result['hypothesis_hash']==d['race']['hypothesis_hash']
    assert client.get('/api/example/public-er/export/prepare.py').status_code==404

def test_changed_public_data_fail_closed(client,tmp_path,monkeypatch):
    monkeypatch.setattr(server,'BASE',tmp_path)
    (tmp_path/'docs').mkdir();(tmp_path/'docs/PASS03_PUBLIC_REFERENCE.json').write_text(json.dumps({'missing':{'sha256':'x'}}))
    assert client.get('/api/example/public-er').status_code==503

@pytest.mark.parametrize('mode',['train_validate','diagnose_shift'])
def test_cohort_preflight_does_not_compute(client,mode):
    d=client.post('/api/preflight',data={'mode':mode},files=uploads()).json()
    assert d['eligible'] and d['preview']['source']['n_samples']==20
    if mode=='diagnose_shift':assert 'observed_conditions' not in d['preview']['source']
    assert not list(server.RUNS.iterdir())

def test_prediction_preflight_has_no_cohort_requirements(client):
    d=client.post('/api/preflight',data={'mode':'evaluate_predictions'},files=uploads(predictions=True)).json()
    assert d['eligible'] and d['preview']['prediction_rows']>0

def test_invalid_and_missing_and_origin(client):
    d=client.post('/api/preflight',data={'mode':'diagnose_shift'},files=uploads(invalid=True)).json()
    assert not d['eligible'] and d['status']=='blocked'
    assert client.post('/api/preflight',data={'mode':'diagnose_shift'}).status_code==422
    assert client.post('/api/preflight',data={'mode':'diagnose_shift'},files=uploads(),headers={'Origin':'https://foreign.example'}).status_code==403

def test_race_preflight_uses_race_gate(client):
    cfg=json.loads((BASE/'examples/public_er_pair/race_config.json').read_text())
    cfg['design']='paired'
    d=client.post('/api/preflight',data={'mode':'race','race_config':json.dumps(cfg)},files=uploads()).json()
    assert not d['eligible'] and 'unpaired' in d['issues'][0]['message']

