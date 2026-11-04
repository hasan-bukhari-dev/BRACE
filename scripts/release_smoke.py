"""Reproduce the offline engine and archive tests without a running web browser."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from brace_app import server

client=TestClient(server.app)
assert client.get('/api/health').status_code==200
assert 'BRACE' in client.get('/').text
past=client.get('/api/example/cptac').json()
assert past['kind']=='historical'
assert past['validation']['n']==680 and past['validation']['metrics']['n_correct']==668
new=client.post('/api/demo/synthetic')
assert new.status_code==200,new.text[:200]
d=new.json()
assert d['kind']=='synthetic' and d['shift']['feature_coverage']['shared']==120
url=f"/api/runs/{d['id']}/bundle"
bundle=client.get(url)
assert bundle.status_code==200
import io
with zipfile.ZipFile(io.BytesIO(bundle.content)) as f:
    assert f.testzip() is None
    manifest=json.loads(f.read('reproducibility_manifest.json'))
    assert manifest['data_origin']=='synthetic'
    for filename,entry in manifest['artifact_sha256'].items():
        assert hashlib.sha256(f.read(filename)).hexdigest()==entry['sha256']
    assert 'research_summary.html' in f.namelist()
    assert not any(x.startswith('input/') for x in f.namelist())
print('BRACE offline scientific smoke: historical=680/668; synthetic full compute=PASS; reproducibility ZIP=PASS')
