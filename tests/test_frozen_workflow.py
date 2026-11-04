import csv
import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from brace_app import server, dataset_registry as registry

BASE = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(server, 'RUNS', tmp_path / 'runs')
    return TestClient(server.app)


def train(client):
    root = BASE / 'examples/synthetic_valid'
    uploads = {role + '_' + kind: (role + '_' + filename, (root / (role + '_' + filename)).read_bytes())
        for role in ('source', 'target') for kind, filename in
        [('expression', 'expression.csv'), ('metadata', 'samples.csv'), ('manifest', 'manifest.json')]}
    response = client.post('/api/analyze', data={'mode': 'train_validate', 'name': 'Frozen source training'}, files=uploads)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize('unlabeled', [True, False])
def test_verified_freeze_to_registered_target_has_honest_metrics(client, tmp_path, unlabeled):
    original = train(client)
    target = registry.get_dataset(original['datasets']['target'])
    if unlabeled:
        paths = {kind: registry.asset_path(target['id'], kind) for kind in ('expression', 'metadata', 'manifest')}
        manifest = json.loads(paths['manifest'].read_text())
        manifest['labels'] = 'unlabeled'
        manifest['cohort_id'] = 'Unlabeled technical target'
        new_manifest = tmp_path / 'unlabeled_manifest.json'
        new_manifest.write_text(json.dumps(manifest))
        rows = list(csv.DictReader(paths['metadata'].open()))
        new_metadata = tmp_path / 'unlabeled_metadata.csv'
        with new_metadata.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows({**row, 'condition': ''} for row in rows)
        target = registry.register_cohort({**paths, 'manifest': new_manifest, 'metadata': new_metadata},
            name='Unlabeled technical target', source={'type': 'test_fixture'})
    body = {'name': 'Target application · no refit', 'frozen_run_id': original['id'], 'target_dataset_id': target['id']}
    response = client.post('/api/dataset-analysis/replay', json=body)
    assert response.status_code == 200, response.text
    run = response.json()
    assert run['mode'] == 'replay_frozen' and run['replay']['evaluation_possible'] is not unlabeled
    assert (run['replay']['metrics'] is None) is unlabeled
    assert (run['validation'] is None) is unlabeled
    assert len(run['replay']['records']) == run['replay']['n']
    if not unlabeled:
        assert run['replay']['metrics']['accuracy'] == original['validation']['metrics']['accuracy']
    assert client.get('/api/runs/' + run['id']).json()['replay'] == run['replay']
    trace = client.get('/api/trace/studies/' + run['id'])
    assert trace.status_code == 200 and trace.json()['steps'][1]['data']['freeze']['target_expression_used_for_fitting'] is False
    exported = client.get('/api/embrace/' + run['id'])
    assert exported.status_code == 200
    assert client.get('/api/embrace/' + run['id']).content == exported.content
    with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
        assert archive.testzip() is None
        manifest = json.loads(archive.read('reproducibility_manifest.json'))
        assert manifest['metrics_available'] is not unlabeled
        assert manifest['frozen_run_id'] == original['id']
        assert not any(name.startswith('input/') for name in archive.namelist())
        assert 'accuracy is unavailable' in archive.read('research_summary.html').decode() if unlabeled else True


def test_freeze_tampering_blocks_replay_before_scoring(client):
    original = train(client)
    model = server.RUNS / original['id'] / 'validation/stage05/frozen_model.json'
    model.write_bytes(b'{"changed":true}')
    response = client.post('/api/dataset-analysis/replay', json={'name': 'Blocked',
        'frozen_run_id': original['id'], 'target_dataset_id': original['datasets']['target']})
    assert response.status_code == 409


def test_assay_catalog_does_not_advertise_unvalidated_modalities(client):
    catalog = client.get('/api/assays').json()
    assert {adapter['id'] for adapter in catalog['adapters']} == {
        'microarray_log2_normalized', 'rnaseq_log2_normalized', 'rnaseq_vst'}
    assert 'Processed proteomics' in catalog['not_implemented']
    assert 'race' not in catalog['adapters'][1]['operations']
