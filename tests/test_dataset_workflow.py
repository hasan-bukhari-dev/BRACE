"""Real persisted data → preflight → computation → reopen → evidence contracts."""
import gzip
import hashlib
import io
import json
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from brace_app import server, dataset_registry as registry

BASE = Path(__file__).resolve().parents[1]


def test_public_cohort_demo_is_real_descriptive_and_reopens(client):
    response = client.post('/api/demo/public-cohorts')
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['mode'] == 'diagnose_shift'
    assert result['shift']['feature_coverage']['shared'] == 10000
    assert result['shift']['inference']['available'] is False
    assert all(row['ks_bh_q_exploratory'] is None for row in result['shift']['gene_shifts'])
    assert client.get('/api/runs/' + result['id']).status_code == 200
    assert client.get('/api/embrace/' + result['id']).status_code == 200


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(server, 'RUNS', tmp_path / 'runs')
    return TestClient(server.app)


def uploaded_predictions():
    root = BASE / 'examples/synthetic_prediction_input'
    return {'predictions': ('records.csv', (root / 'predictions.csv').read_bytes()),
            'prediction_manifest': ('classes.json', (root / 'manifest.json').read_bytes())}


def test_prediction_study_name_identity_reopen_and_export(client):
    name = 'Instrument QA · independent evaluation 日本語'
    response = client.post('/api/analyze', data={'mode': 'evaluate_predictions', 'name': name},
                           files=uploaded_predictions())
    assert response.status_code == 200, response.text
    run = response.json()
    assert run['name'] == name and run['cohorts'] is None
    assert run['schema_version'] == '1.0.0' and run['study_id']
    assert client.get('/api/runs/' + run['id']).json()['name'] == name
    assert client.get('/api/studies/' + run['study_id']).json()['datasets'] == run['datasets']
    with zipfile.ZipFile(io.BytesIO(client.get('/api/embrace/' + run['id']).content)) as archive:
        manifest = json.loads(archive.read('reproducibility_manifest.json'))
        assert manifest['study_name'] == name and manifest['datasets'] == run['datasets']
        assert name in archive.read('research_summary.html').decode()
        lineage = json.loads(archive.read('DATASET_LINEAGE.json'))
        assert lineage['predictions']['assets']['predictions']['filename'] == 'records.csv'
    # A new API client uses on-disk SQLite and assets, with no browser state.
    restarted = TestClient(server.app)
    assert restarted.get('/api/runs/' + run['id']).json()['study_id'] == run['study_id']
    assert restarted.get('/api/datasets').json()['datasets'][0]['id'] == run['datasets']['predictions']


def test_public_registry_pipeline_keeps_science_and_lineage(client):
    response = client.post('/api/datasets/reviewed-public', json={'reviewed': True})
    assert response.status_code == 200, response.text
    prepared = response.json()
    ids = {role: record['id'] for role, record in prepared['datasets'].items()}
    again = client.post('/api/datasets/reviewed-public', json={'reviewed': True}).json()
    assert ids == {role: record['id'] for role, record in again['datasets'].items()}
    assert len(client.get('/api/datasets').json()['datasets']) == 4
    body = {'name': 'ER association · registry', 'mode': 'race', 'datasets': ids,
            'race_config': prepared['race_config']}
    check = client.post('/api/dataset-analysis/preflight', json=body)
    assert check.status_code == 200 and check.json()['eligible'], check.text
    baseline_check = client.post('/api/dataset-analysis/preflight', json={**body, 'mode': 'train_validate'})
    assert not baseline_check.json()['eligible']  # ER is not normal/tumor
    response = client.post('/api/dataset-analysis/run', json=body)
    assert response.status_code == 200, response.text
    run = response.json()
    assert run['name'] == body['name'] and run['datasets'] == ids
    assert run['cohorts']['source']['cohort_id'] == 'GSE42568_ER'
    assert run['race']['aggregate']['supported'] == 14
    reference = json.loads((BASE / 'examples/public_er_pair/race_final/race_result.json').read_text())
    assert [gene['feature_id'] for gene in run['race']['genes']] == [gene['feature_id'] for gene in reference['genes']]
    for actual, expected in zip(run['race']['genes'], reference['genes']):
        for key in ('effect', 'p', 'q', 'hedges_g', 't'):
            assert actual[key] == pytest.approx(expected[key], rel=1e-10, abs=1e-12)
    reopened = TestClient(server.app).get('/api/runs/' + run['id']).json()
    assert reopened['cohorts'] == run['cohorts'] and reopened['name'] == run['name']
    gene = run['race']['genes'][0]['feature_id']
    assert client.get(f"/api/trace/studies/{run['id']}?feature_id={gene}").status_code == 200
    face = client.get(f"/api/race/studies/{run['id']}/gene", params={'feature_id': gene})
    assert face.status_code == 200
    assert len(face.json()['cohorts']['source']['groups'][0]['samples']) > 0
    with zipfile.ZipFile(io.BytesIO(client.get('/api/embrace/' + run['id']).content)) as archive:
        lineage = json.loads(archive.read('DATASET_LINEAGE.json'))
        assert lineage['target']['parent_dataset_ids'] == lineage['source']['parent_dataset_ids']
        assert lineage['source']['preprocessing_history'][0]['mapping_sha256']
        assert lineage['source']['parent_records'][0]['source']['url'].startswith('https://ftp.ncbi.nlm.nih.gov/')
        assert lineage['source']['parent_records'][0]['assets']['original']['sha256']
        assert json.loads(archive.read('race/race_result.json'))['aggregate'] == run['race']['aggregate']
        context=json.loads(archive.read('BIOLOGICAL_CONTEXT.json'))
        assert context[gene]['source_url']=='https://www.ncbi.nlm.nih.gov/gene/'+gene
        assert context[gene]['retrieved_date']=='2026-11-04'
    # A second computation can share a persisted study while retaining a distinct run ID.
    repeat = client.post('/api/dataset-analysis/run', json={**body, 'study_id': run['study_id']}).json()
    assert repeat['id'] != run['id'] and repeat['study_id'] == run['study_id']
    assert repeat['race']['hypothesis_hash'] == run['race']['hypothesis_hash']


def test_dataset_asset_tamper_and_unknown_schema_fail_closed(client):
    run = client.post('/api/analyze', data={'mode': 'evaluate_predictions'}, files=uploaded_predictions()).json()
    dataset_id = run['datasets']['predictions']
    path = registry.asset_path(dataset_id, 'predictions')
    path.write_bytes(b'changed')
    assert client.get(f'/api/datasets/{dataset_id}/assets/predictions').status_code == 409
    assert client.post('/api/analyze', data={'mode': 'evaluate_predictions', 'schema_version': '99'},
                       files=uploaded_predictions()).status_code == 422
    assert client.post('/api/dataset-analysis/run', json={'schema_version': '99', 'mode': 'race',
                       'name': 'Invalid', 'datasets': {}}).status_code == 422
    assert client.get('/api/datasets/not-an-id').status_code == 404


def test_history_orders_recorded_times_not_directory_order_or_export(client):
    runs = []
    for name in ['First study', 'Second study']:
        response = client.post('/api/analyze', data={'mode': 'evaluate_predictions', 'name': name},
                               files=uploaded_predictions())
        assert response.status_code == 200, response.text
        runs.append(response.json())
    # Artificially touch the oldest folder; that must not make its result newest.
    os.utime(server.RUNS / runs[0]['id'], (2_000_000_000, 2_000_000_000))
    client.get('/api/embrace/' + runs[0]['id'])
    indexed = client.get('/api/runs').json()['runs']
    assert [row['id'] for row in indexed] == [run['id'] for run in reversed(runs)]
    assert all(row['timestamp_source'] == 'recorded' for row in indexed)
    assert client.get('/api/runs/' + runs[0]['id']).json()['name'] == 'First study'


def test_concurrent_identical_registration_deduplicates(client, tmp_path):
    path = tmp_path / 'fixture.txt'
    path.write_text('immutable bytes')
    def create(_):
        return registry.register({'original': path}, name='Fixture', source={'type': 'test'})['id']
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(create, range(4)))
    assert len(set(ids)) == 1 and len(registry.list_datasets()) == 1


def register_matrix(tmp_path, content):
    path = tmp_path / 'fixture.gz'
    path.write_bytes(gzip.compress(content.encode()))
    return registry.register({'original': path}, name='GEO technical fixture',
        source={'type': 'geo', 'accession': 'GSE12345', 'url': 'https://example.invalid/fixture'})


def test_general_preparation_is_explicit_versioned_and_reports_losses(client, tmp_path):
    original = register_matrix(tmp_path, '!Sample_geo_accession\t"GSM1"\t"GSM2"\n'
        '!series_matrix_table_begin\n"ID_REF"\t"GSM1"\t"GSM2"\n"probeA"\t1.5\t2.5\n"probeB"\t2\t3\n!series_matrix_table_end\n')
    preview = client.get(f"/api/datasets/{original['id']}/inspect")
    assert preview.status_code == 200 and not preview.json()['eligible']
    manifest = json.loads((BASE / 'examples/synthetic_valid/source_manifest.json').read_text())
    request = {'name': 'Reviewed technical fixture', 'reviewed': True, 'manifest': manifest,
        'condition_by_sample': {'GSM1': 'normal', 'GSM2': 'tumor'},
        'feature_mapping': {'probeA': 'GENEA'}, 'mapping_reference': 'Explicit test mapping v1'}
    response = client.post(f"/api/datasets/{original['id']}/prepare", json=request)
    assert response.status_code == 200, response.text
    prepared = response.json()
    assert prepared['parent_dataset_ids'] == [original['id']]
    assert prepared['summary']['n_features'] == 1
    history = prepared['preprocessing_history'][0]
    assert history['unmapped_features'] == ['probeB'] and not history['automatic_normalization']
    incomplete = {**request, 'condition_by_sample': {'GSM1': 'normal'}}
    assert client.post(f"/api/datasets/{original['id']}/prepare", json=incomplete).status_code == 422
    ambiguous = {**request, 'feature_mapping': {'probeA': 'GENEA', 'probeB': 'GENEA'}}
    assert client.post(f"/api/datasets/{original['id']}/prepare", json=ambiguous).status_code == 422


def test_guided_large_matrix_subset_is_explicit_and_auditable(client, tmp_path):
    text = '!series_matrix_table_begin\nID_REF\tS1\tS2\n'
    text += ''.join(f'probe{i}\t{i + 1}\t{i + 2}\n' for i in range(25002))
    text += '!series_matrix_table_end\n'
    original = register_matrix(tmp_path, text)
    manifest = json.loads((BASE / 'examples/synthetic_valid/source_manifest.json').read_text())
    manifest.update(labels='unlabeled', feature_namespace='probe_id', platform='GPL_TEST')
    body = {'name': 'Explicit subset technical check', 'reviewed': True, 'manifest': manifest,
            'condition_by_sample': {'S1': '', 'S2': ''}}
    endpoint = f"/api/datasets/{original['id']}/prepare"
    # A large file is never silently truncated by the legacy/default path.
    assert client.post(endpoint, json=body).status_code == 422
    response = client.post(endpoint, json={**body, 'feature_policy': 'bounded_original_order'})
    assert response.status_code == 200, response.text
    prepared = response.json()
    assert prepared['summary']['n_features'] == 25000
    history = prepared['preprocessing_history'][0]
    assert history['unmapped_features'] == ['probe25000', 'probe25001']
    assert history['feature_policy'] == 'bounded_original_order'
    assert history['automatic_normalization'] is False
    assert prepared['parent_dataset_ids'] == [original['id']]
    assert client.post(endpoint, json={**body, 'feature_policy': 'bounded_original_order',
        'feature_mapping': {'probe0': 'GENE'}}).status_code == 422
    assert client.post(endpoint, json={**body, 'feature_policy': 'silent_filter'}).status_code == 422


def test_bounded_preparation_respects_serialized_file_size(tmp_path):
    from brace_app.preparation import prepare_general
    original = tmp_path / 'large.gz'
    number = '1.' + '0' * 600
    text = '!series_matrix_table_begin\nID_REF\tS1\tS2\n'
    text += ''.join(f'probe{i}\t{number}\t{number}\n' for i in range(23000))
    text += '!series_matrix_table_end\n'
    original.write_bytes(gzip.compress(text.encode()))
    paths, report = prepare_general(original, tmp_path, manifest={'labels': 'unlabeled'},
        condition_by_sample={'S1': '', 'S2': ''}, excluded_samples={},
        feature_mapping={}, mapping_reference='', feature_policy='bounded_original_order')
    assert paths['expression'].stat().st_size < 25 * 1024 * 1024
    assert 1 < report['retained_features'] < 23000
    assert report['unmapped_features'][0] == f"probe{report['retained_features']}"
    assert report['original_features'] == 23000


def test_unsupported_matrix_preserves_original_and_explains_blocker(client, tmp_path):
    original = register_matrix(tmp_path, '!series_matrix_table_begin\nID_REF\tS1\tS2\ngene\tNA\t2\n!series_matrix_table_end\n')
    response = client.get(f"/api/datasets/{original['id']}/inspect")
    assert response.status_code == 422 and response.json()['detail']['code'] == 'GEO_PREPARATION_BLOCKED'
    assert client.get(f"/api/datasets/{original['id']}/assets/original").status_code == 200
    assert client.get('/api/datasets').json()['datasets'][0]['status'] == 'acquired'


def test_registry_study_assignment_mismatch_is_blocked(client):
    run = client.post('/api/analyze', data={'mode': 'evaluate_predictions', 'name': 'A'}, files=uploaded_predictions()).json()
    body = {'mode': 'evaluate_predictions', 'name': 'B', 'datasets': run['datasets'], 'study_id': run['study_id']}
    assert client.post('/api/dataset-analysis/run', json=body).status_code == 409


def test_dataset_display_rename_preserves_identity_and_saved_run_snapshot(client):
    run = client.post('/api/analyze', data={'mode': 'evaluate_predictions', 'name': 'Original'}, files=uploaded_predictions()).json()
    dataset_id = run['datasets']['predictions']
    old = registry.get_dataset(dataset_id)
    renamed = client.patch('/api/datasets/' + dataset_id, json={'name': 'New display name'}).json()
    assert renamed['id'] == old['id'] and renamed['assets'] == old['assets']
    assert client.get('/api/runs/' + run['id']).json()['name'] == 'Original'


def test_reviewed_label_and_role_transformation_keeps_measurements(client):
    folder = BASE / 'examples/synthetic_valid'
    parent = registry.register_cohort({kind: folder / ('source_' + filename) for kind, filename in
        [('expression', 'expression.csv'), ('metadata', 'samples.csv'), ('manifest', 'manifest.json')]},
        name='Original labels', source={'type': 'test_fixture'})
    request = {'name': 'Reviewed common contrast', 'role': 'target', 'reviewed': True,
        'condition_mapping': {'normal': 'reference', 'tumor': 'case'},
        'biological_definitions': {'reference': 'Original normal reference', 'case': 'Original tumor condition'}}
    response = client.post('/api/datasets/' + parent['id'] + '/transform', json=request)
    assert response.status_code == 200, response.text
    transformed = response.json()
    assert transformed['id'] != parent['id'] and transformed['parent_dataset_ids'] == [parent['id']]
    assert transformed['assets']['expression']['sha256'] == parent['assets']['expression']['sha256']
    assert transformed['summary']['observed_conditions'] == {'reference': 10, 'case': 10}
    assert transformed['summary']['manifest']['role'] == 'target'
    assert registry.get_dataset(parent['id'])['summary']['manifest']['role'] == 'source'
    assert client.post('/api/datasets/' + parent['id'] + '/transform', json={**request, 'biological_definitions': {}}).status_code == 422


def test_json_resource_and_foreign_origin_limits(client):
    response = client.post('/api/datasets/reviewed-public', content=b' ' * (2 * 1024 * 1024 + 1),
                           headers={'Content-Type': 'application/json'})
    assert response.status_code == 413
    assert client.post('/api/datasets/reviewed-public', json={'reviewed': True},
                       headers={'Origin': 'https://foreign.example'}).status_code == 403
    duplicate=client.post('/api/datasets/reviewed-public',content='{"reviewed":true,"reviewed":false}',headers={'Content-Type':'application/json'})
    assert duplicate.status_code==422 and duplicate.json()['detail']['code']=='INVALID_JSON'


def test_damaged_gzip_is_blocked_without_losing_acquisition(client, tmp_path):
    path = tmp_path / 'bad.gz'
    path.write_bytes(b'\x1f\x8btruncated')
    original = registry.register({'original': path}, name='Damaged gzip fixture', source={'type': 'test_fixture'})
    assert client.get(f"/api/datasets/{original['id']}/inspect").status_code == 422
    assert registry.asset_path(original['id'], 'original').read_bytes() == path.read_bytes()


def test_general_geo_numeric_preparation_reaches_real_ce_and_race(client, tmp_path, monkeypatch):
    from brace_app import discovery
    prepared = {}
    for role in ('source', 'target'):
        samples = [role + str(index) for index in range(6)]
        text = '!series_matrix_table_begin\nID_REF\t' + '\t'.join(samples) + '\n'
        text += 'probeA\t1\t1.1\t1.2\t4\t4.1\t4.2\nprobeB\t2\t2.1\t2.2\t5\t5.1\t5.2\n!series_matrix_table_end\n'
        # Only the external transport is a synthetic fixture. Exercise the actual
        # discovery listing, acquisition, registry, preparation and compute APIs.
        accession='GSE12345' if role=='source' else 'GSE12346'
        filename=accession+'_series_matrix.txt.gz'
        original_bytes=gzip.compress(text.encode())
        def public_bytes(url,limit=2*1024*1024):
            if url.endswith(filename):return original_bytes
            return ('<a href="'+filename+'">matrix</a>').encode()
        monkeypatch.setattr(discovery,'public_bytes',public_bytes)
        listing=client.get('/api/discovery/study/'+accession)
        assert listing.status_code==200 and not listing.json()['eligible']
        receipt=client.post('/api/discovery/acquire',json={'accession':accession,'filename':filename})
        assert receipt.status_code==200 and not receipt.json()['eligible']
        original=client.get('/api/datasets/'+receipt.json()['dataset_id']).json()
        manifest = json.loads((BASE / 'examples/synthetic_valid/source_manifest.json').read_text())
        manifest.update(role=role, cohort_id='technical_' + role, feature_namespace='entrez_gene',
                        measurement_type='microarray_log2_normalized', platform='GPL570')
        response = client.post('/api/datasets/' + original['id'] + '/prepare', json={
            'name': 'Technical matrix ' + role, 'reviewed': True, 'manifest': manifest,
            'condition_by_sample': {sample: 'normal' if index < 3 else 'tumor' for index, sample in enumerate(samples)},
            'feature_mapping': {'probeA': '101', 'probeB': '102'}, 'mapping_reference': 'Technical one-to-one fixture v1'})
        assert response.status_code == 200, response.text
        prepared[role] = response.json()['id']
        assert response.json()['parent_dataset_ids']==[original['id']]
    body = {'name': 'General-format technical check', 'mode': 'diagnose_shift', 'datasets': prepared}
    assert client.post('/api/dataset-analysis/preflight', json=body).json()['eligible']
    result = client.post('/api/dataset-analysis/run', json=body)
    assert result.status_code == 200 and result.json()['shift']['feature_coverage']['shared'] == 2
    body.update(mode='race', race_config={'positive': 'tumor', 'negative': 'normal',
        'source_conditions': {'tumor': 'Technical condition A', 'normal': 'Technical condition B'},
        'target_conditions': {'tumor': 'Technical condition A', 'normal': 'Technical condition B'}})
    result = client.post('/api/dataset-analysis/run', json=body)
    assert result.status_code == 200, result.text
    assert result.json()['race']['aggregate']['selected'] == 2


def test_reviewed_er_plan_rejects_other_originals(client, tmp_path):
    original=register_matrix(tmp_path,'not the reviewed GSE21653 bytes')
    response=client.get('/api/datasets/'+original['id']+'/reviewed-er-plan')
    assert response.status_code==422 and 'exact reviewed' in response.json()['detail']
    assert registry.get_dataset(original['id'])['status']=='acquired'


def test_reviewed_er_plan_requires_exact_explicit_annotations(monkeypatch, tmp_path):
    from brace_app import public_recipes as recipe
    original=tmp_path/'original.gz';original.write_bytes(b'transport fixture')
    real_digest=registry.digest
    monkeypatch.setattr(registry,'asset_path',lambda *args:original)
    monkeypatch.setattr(registry,'digest',lambda p:recipe.GSE21653_SHA256 if p==original else real_digest(p))
    ids=['GSM'+str(i) for i in range(266)]
    er=['er ihc: 1']*150+['er ihc: 0']*113+['er ihc: NA']*3
    mapping=BASE/'examples/public_er_pair/prepared/selected_features.tsv'
    import csv
    with mapping.open(encoding='utf-8',newline='') as stream:features=[r['probe_id'] for r in csv.DictReader(stream,delimiter='\t')]
    metadata={'!Sample_platform_id':[['GPL570']*266],
        '!Sample_data_processing':[['RMA using a quantile normalization']*266],
        '!Sample_characteristics_ch1':[er,['tissue: breast cancer tumor']*266]}
    monkeypatch.setattr(recipe,'series_matrix',lambda p:dict(sample_ids=ids,feature_ids=features,metadata=metadata))
    plan=recipe.er_21653_plan('fixture')
    assert plan['summary']['included']==263 and plan['summary']['retained_features']==10000
    assert len(plan['preparation']['excluded_samples'])==3
    assert 'reviewed' not in plan['preparation']  # loading never approves or computes
    er[0]='er ihc: unknown'
    with pytest.raises(ValueError,match='Unrecognized ER IHC'):recipe.er_21653_plan('fixture')
