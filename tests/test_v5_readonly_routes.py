"""V5 read-only input delivery and audited report integration contracts."""
import hashlib,io,json,zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from brace_app import server
from brace_app.study_api import PUBLIC_INPUT_FILES
BASE=Path(__file__).resolve().parents[1]
@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'RUNS',tmp_path/'runs');server.RUNS.mkdir()
    return TestClient(server.app)
@pytest.mark.parametrize('filename',sorted(PUBLIC_INPUT_FILES|{'race_config.json'}))
def test_public_guided_inputs_are_exact_recorded_bytes(client,filename):
    root=BASE/'examples/public_er_pair';original=root/filename if filename=='race_config.json' else root/'prepared'/filename
    response=client.get('/api/example/public-er/input/'+filename)
    assert response.status_code==200 and response.content==original.read_bytes()
    assert response.headers['x-content-type-options']=='nosniff'
    assert len(response.content)<25*1048576
@pytest.mark.parametrize('filename',['prepare.py','../server.py','source_expression.csv','selected_signature.json'])
def test_public_input_whitelist(client,filename):
    assert client.get('/api/example/public-er/input/'+filename).status_code==404
@pytest.mark.parametrize('filename',['source_expression.tsv','race_config.json'])
def test_input_tampering_fails_closed(client,tmp_path,monkeypatch,filename):
    monkeypatch.setattr(server,'BASE',tmp_path);(tmp_path/'docs').mkdir();(tmp_path/'docs/PASS03_PUBLIC_REFERENCE.json').write_text('{}')
    root=tmp_path/'examples/public_er_pair';(root/'prepared').mkdir(parents=True)
    path=root/filename if filename=='race_config.json' else root/'prepared'/filename;path.write_text('changed')
    if filename!='race_config.json':(tmp_path/'docs/PASS03_PUBLIC_REFERENCE.json').write_text(json.dumps({str(path.relative_to(tmp_path)):{'sha256':'not-matching'}}))
    assert client.get('/api/example/public-er/input/'+filename).status_code==503
@pytest.mark.parametrize('study_id',['public_er_pass2','historical_cptac'])
def test_readable_report_is_the_audited_export_html(client,study_id):
    response=client.get('/api/embrace/'+study_id+'/report');package=client.get('/api/embrace/'+study_id)
    assert response.status_code==200 and response.headers['content-type'].startswith('text/html')
    with zipfile.ZipFile(io.BytesIO(package.content)) as z:
        assert response.content==z.read('research_summary.html')
    assert "default-src 'none'" in response.headers['content-security-policy']
    assert response.headers['x-content-type-options']=='nosniff'
def test_missing_report_cannot_publish_success(client):
    assert client.get('/api/embrace/no_such_run/report').status_code==404
