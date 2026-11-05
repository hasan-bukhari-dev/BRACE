"""Maintenance release contracts: names, offline help and exact engine parity."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_official_names_agree_in_ui_readme_and_manual():
    source = (ROOT/'brace_app/static/js/identity.js').read_text(encoding='utf-8')
    names = dict(re.findall(r"^ (\w+):'([^']+)'", source, re.M))
    assert set(names) == {'BRACE','RACE','ACE','CE','EMBRACE','SPACE','FACE','TRACE'}
    assert names['RACE'] == 'Replication Assessment of Cohort Effects'
    assert names['ACE'] == 'Algorithmic Classifier Evaluation'
    assert names['CE'] == 'Cohort Evaluation'
    for path in ['README.md','docs/manual/USER_MANUAL.md']:
        text = (ROOT/path).read_text(encoding='utf-8')
        for expansion in names.values():
            assert expansion in text, (path, expansion)


def test_maintenance_preserves_every_recorded_scientific_engine_byte():
    record = json.loads((ROOT/'docs/quality/MAINTENANCE_ENGINE_SHA256.json').read_text())
    assert record['baseline_release'] == '1.2.2'
    for name, expected in record['sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name


def test_manual_is_local_and_packaged():
    from fastapi.testclient import TestClient
    from brace_app.server import app
    response = TestClient(app).get('/manual')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/pdf'
    assert response.content == (ROOT/'docs/USER_MANUAL.pdf').read_bytes()
    assert response.content.startswith(b'%PDF-')
    assert 'USER_MANUAL.pdf' in (ROOT/'packaging/BRACE.spec').read_text()
    assert 'href="/manual"' in (ROOT/'brace_app/static/index.html').read_text(encoding='utf-8')


def test_baseline_and_archived_prediction_labels_stay_distinct(tmp_path):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js is needed for the actual presentation module')
    module_path = tmp_path/'identity.mjs'
    module_path.write_bytes((ROOT/'brace_app/static/js/identity.js').read_bytes())
    module = module_path.as_uri()
    code = f"import {{evaluationTitle}} from {json.dumps(module)}; console.log(JSON.stringify([evaluationTitle(680),evaluationTitle(90,true)]));"
    result = subprocess.run([node,'--input-type=module','-e',code], check=True, capture_output=True, text=True)
    saved, baseline = json.loads(result.stdout)
    assert saved == 'Evaluate 680 saved predictions'
    assert baseline == 'Evaluate source-trained baseline on 90 target samples'
