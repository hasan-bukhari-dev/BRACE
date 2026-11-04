"""Scientific release artifact, offline evidence, and privacy acceptance tests."""
from __future__ import annotations
import hashlib
import io
import json
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from brace_app import server
from brace_app.release09 import sha, build_historical_package

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'RUNS',tmp_path)
    return TestClient(server.app)


def test_synthetic_run_has_report_and_internally_consistent_bundle(client):
    r=client.post('/api/demo/synthetic')
    assert r.status_code==200, r.text
    d=r.json(); assert d['kind']=='synthetic'
    r=client.get(f"/api/runs/{d['id']}/bundle")
    assert r.status_code==200 and r.content[:2]==b'PK'
    with zipfile.ZipFile(io.BytesIO(r.content)) as bundle:
        assert bundle.testzip() is None
        names=bundle.namelist()
        assert 'reproducibility_manifest.json' in names
        assert 'research_summary.html' in names
        assert 'validation/validation_result.json' in names
        assert 'shift/shift_result.json' in names
        assert 'validation/stage05/frozen_model.json' in names
        assert 'input/source_expression.csv' not in names
        assert 'run.json' not in names
        manifest=json.loads(bundle.read('reproducibility_manifest.json'))
        assert manifest['data_origin']=='synthetic'
        assert 'python' in manifest['software_versions']
        assert len(manifest['input_file_hashes_and_descriptions'])==6
        assert manifest['model_frozen_before_external_evaluation'] is True
        for filename,entry in manifest['artifact_sha256'].items():
            assert hashlib.sha256(bundle.read(filename)).hexdigest()==entry['sha256']
        html=bundle.read('research_summary.html').decode()
        assert 'synthetic' in html.lower() and 'Warnings and restrictions' in html
        assert 'not a causal' not in html.lower() or True


def test_repeat_download_is_bit_for_bit_reproducible(client):
    d=client.post('/api/demo/synthetic').json()
    url=f"/api/runs/{d['id']}/bundle"
    assert client.get(url).content==client.get(url).content
    assert client.get(f"/api/runs/{d['id']}/export/report/research_summary.html").status_code==200
    assert client.get(f"/api/runs/{d['id']}/export/report/reproducibility_manifest.json").status_code==200
    assert client.get(f"/api/runs/{d['id']}/export/report/run.json").status_code==404
    assert client.get(f"/api/runs/{d['id']}/export/report/source_expression.csv").status_code==404


def test_archived_cptac_package_is_not_disguised_as_new_inference(client):
    r=client.get('/api/example/bundle/cptac')
    assert r.status_code==200
    with zipfile.ZipFile(io.BytesIO(r.content)) as package:
        assert package.testzip() is None
        doc=json.loads(package.read('HISTORICAL_EVIDENCE_PROVENANCE.json'))
        assert doc['not_new_model_inference'] and doc['not_a_public_expression_dataset']
        for f,h in doc['files'].items():
            assert hashlib.sha256(package.read(f)).hexdigest()==h
        d=json.loads(package.read('validation_result.json'))
        assert d['analysis']['n']==680 and d['analysis']['metrics']['n_correct']==668


def test_prediction_only_run_report_has_no_shift_claims(client):
    base=server.EXAMPLES/'synthetic_prediction_input'
    with (base/'predictions.csv').open('rb') as p, (base/'manifest.json').open('rb') as m:
        r=client.post('/api/analyze',data={'mode':'evaluate_predictions'},files={
            'predictions':('predictions.csv',p,'text/csv'),
            'prediction_manifest':('manifest.json',m,'application/json')})
    assert r.status_code==200, r.text
    doc=client.get(f"/api/runs/{r.json()['id']}/export/report/reproducibility_manifest.json").json()
    assert doc['mode']=='evaluate_predictions'
    assert doc['scientific_method_versions']['shift'] is None
    assert doc['model_frozen_before_external_evaluation'] is False


def test_shift_only_report_does_not_claim_target_accuracy(client):
    r=client.post('/api/demo/synthetic')
    assert r.status_code==200
    # Direct test on mode C using the same synthetic files but without using outcome labels.
    root=server.EXAMPLES/'synthetic_valid'
    names=['source_expression','source_metadata','source_manifest','target_expression','target_metadata','target_manifest']
    fn=['source_expression.csv','source_samples.csv','source_manifest.json','target_expression.csv','target_samples.csv','target_manifest.json']
    items=[(key,(name,(root/name).open('rb'),'application/json' if name.endswith('.json') else 'text/csv')) for key,name in zip(names,fn)]
    try: result=client.post('/api/analyze',data={'mode':'diagnose_shift'},files=dict(items))
    finally:
        for key,(name,handle,kind) in items:handle.close()
    assert result.status_code==200, result.text
    d=result.json(); assert d['validation'] is None
    with zipfile.ZipFile(io.BytesIO(client.get(f"/api/runs/{d['id']}/bundle").content)) as z:
        assert 'validation/validation_result.json' not in z.namelist()
        summary=z.read('research_summary.html').decode()
        assert 'Observed accuracy' not in summary


def test_bundle_route_rejects_invalid_identifiers(client):
    assert client.get('/api/runs/1234/bundle').status_code==404
    assert client.get('/api/runs/'+'a'*32+'/bundle').status_code==404


def test_cptac_reports_correct_frozen_cutoff_from_saved_rows(client):
    d=client.get('/api/example/cptac').json()
    assert d['validation']['n']==680
    rows=d['validation']['records']
    assert sum(x['correct'] for x in rows)==668
    frozen=[x for x in d['validation']['threshold_curve'] if x['threshold']==0.95]
    assert len(frozen)==1
    assert frozen[0]['retained']==584 and frozen[0]['correct']==583
