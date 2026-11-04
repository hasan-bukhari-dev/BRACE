"""Stage 08 browser-app HTTP contract tests; no clinical assumptions."""
import json
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from brace_app import server

APP_ROOT=Path(__file__).resolve().parents[1]
EX=APP_ROOT/'examples'

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'RUNS',tmp_path)
    return TestClient(server.app)


def test_local_app_serves_frontend_and_endpoints(client):
    r=client.get('/')
    assert r.status_code==200 and 'BRACE' in r.text and 'view-validation' in r.text
    js=client.get('/assets/app.js')
    assert js.status_code==200 and 'Source-fitted' in js.text
    # Pass 3 connects the approved, hash-checked GEO example.
    assert client.get('/api/health').json()['geo_expression_data_available'] is True


def test_historical_example_references_real_archived_rows(client):
    r=client.get('/api/example/cptac');assert r.status_code==200
    d=r.json();assert d['kind']=='historical'
    v=d['validation']; assert v['n']==680 and v['metrics']['n_correct']==668
    assert v['metrics']['absent_true_classes']==['prostate']
    assert v['threshold']==0.95
    assert v['metrics']['selective']['retained']==584 if 'retained' in v['metrics'].get('selective',{}) else True
    assert any(not e['correct'] and e['confidence']>0.998 for e in v['errors'])


def test_historical_shift_is_labeled_historical(client):
    d=client.get('/api/example/historical-shift').json()
    assert d['kind']=='historical'
    assert 'NOT a freshly calculated' in d['provenance']['data_origin']
    assert len(d['methods'])>=3


def test_synthetic_preview_is_never_disguised_as_real_data(client):
    d=client.get('/api/example/synthetic').json()
    assert d['kind']=='synthetic' and 'Artificial' in d['data_label']
    assert len(d['shift']['gene_shifts'])==120


def test_full_synthetic_analysis_runs_and_export_is_real(client):
    response=client.post('/api/demo/synthetic')
    assert response.status_code==200,response.text
    d=response.json();assert d['kind']=='synthetic' and d['mode']=='train_validate'
    assert d['validation']['n']==14
    assert d['shift']['feature_coverage']['shared']==120
    assert d['shift']['error_association']['available']
    assert d['validation']['origin']=='new_frozen_source_baseline'
    for name in ('validation_result.json','sample_level.csv'):
        result=client.get(f"/api/runs/{d['id']}/export/validation/{name}")
        assert result.status_code==200 and len(result.content)>100
    # A run can be reloaded after completion and must remain the same.
    d2=client.get('/api/runs/'+d['id']).json()
    assert d['validation']['metrics']==d2['validation']['metrics']


def test_manual_prediction_upload(client):
    root=EX/'synthetic_prediction_input'
    with (root/'predictions.csv').open('rb') as predictions, (root/'manifest.json').open('rb') as manifest:
        r=client.post('/api/analyze',data={'mode':'evaluate_predictions'},
           files={'predictions':('predictions.csv',predictions,'text/csv'),
                  'prediction_manifest':('manifest.json',manifest,'application/json')})
    assert r.status_code==200,r.text
    d=r.json();assert d['kind']=='user_computed' and d['validation']['n']>0 and d['shift'] is None


def test_manual_unlabeled_upload(client):
    root=EX/'synthetic_valid'
    paths={'source_expression':'source_expression.csv','source_metadata':'source_samples.csv',
           'source_manifest':'source_manifest.json','target_expression':'target_expression.csv',
           'target_metadata':'target_samples.csv','target_manifest':'target_manifest.json'}
    opened={k:(v,(root/v).open('rb'),'application/json' if v.endswith('.json') else 'text/csv') for k,v in paths.items()}
    try:r=client.post('/api/analyze',data={'mode':'diagnose_shift'},files=opened)
    finally:
        for _,f,_ in opened.values():f.close()
    assert r.status_code==200,r.text
    d=r.json();assert d['validation'] is None and d['shift']['mode']=='diagnose_shift'
    assert d['shift']['label_based_exploratory'] is None


def test_missing_file_is_actionable(client):
    r=client.post('/api/analyze',data={'mode':'evaluate_predictions'})
    assert r.status_code==422
    assert r.json()['detail']['code']=='MISSING_FILE'


def test_disallowed_binary_model_file_rejected(client):
    r=client.post('/api/analyze',data={'mode':'evaluate_predictions'},files={
      'predictions':('danger.pkl',b'payload','application/octet-stream'),
      'prediction_manifest':('meta.json',b'{}','application/json')})
    assert r.status_code==422
    assert r.json()['detail']['code']=='UNSUPPORTED_FORMAT'


def test_unrecognized_mode_rejected_before_processing(client):
    r=client.post('/api/analyze',data={'mode':'predict_patient'})
    assert r.status_code==422


def test_downloads_are_allowlisted(client):
    r=client.post('/api/demo/synthetic');id=r.json()['id'];assert len(id)==32
    assert client.get(f'/api/runs/{id}/export/validation/run_report.html').status_code==200
    assert client.get(f'/api/runs/{id}/export/validation/run.json').status_code==404
    assert client.get(f'/api/runs/{id}/export/input/source_manifest.json').status_code==404
    assert client.get('/api/runs/not-an-id').status_code==404
    assert client.get('/api/example/export/cptac/sample_level.csv').status_code==200


def test_input_template_download(client):
    r=client.get('/api/templates')
    assert r.status_code==200 and r.content[:2]==b'PK'
    assert len(r.content)>1000


def test_historical_adaptation_export(client):
    r=client.get('/api/example/export/historical/historical_adaptation_comparison.csv')
    assert r.status_code==200 and b'gse2109_macro_f1_historical' in r.content
    assert client.get('/api/example/export/historical/../manifest.json').status_code in (404,422)


def test_cross_origin_writes_blocked(client):
    r=client.post('/api/demo/synthetic',headers={'Origin':'https://example.com'})
    assert r.status_code==403
    assert b'Cross-origin' in r.content


def test_manual_supervised_six_file_upload(client):
    root=EX/'synthetic_valid'
    paths={'source_expression':'source_expression.csv','source_metadata':'source_samples.csv',
           'source_manifest':'source_manifest.json','target_expression':'target_expression.csv',
           'target_metadata':'target_samples.csv','target_manifest':'target_manifest.json'}
    opened={k:(v,(root/v).open('rb'),'application/json' if v.endswith('.json') else 'text/csv') for k,v in paths.items()}
    try:r=client.post('/api/analyze',data={'mode':'train_validate'},files=opened)
    finally:
        for _,f,_ in opened.values():f.close()
    assert r.status_code==200,r.text
    d=r.json()
    assert d['mode']=='train_validate' and d['validation']['n']==14
    assert d['shift']['error_association']['available']
    assert any(x['filename']=='frozen_model.json' for x in d['exports'])
    assert d['provenance']['source_expression']['sha256']
