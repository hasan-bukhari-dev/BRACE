"""Transactional local dataset/study registry. Scientific rules remain in brace_core.

Asset directories are staged before a SQLite transaction publishes their records.
Content and transformation hashes deduplicate only identical dataset versions.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

from fastapi import HTTPException

from brace_app.export_safety import within
from brace_app.persistence import SCHEMA_VERSION, study_name, utc_now


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def registry_root() -> Path:
    from brace_app import server
    root = within(server.RUNS, server.RUNS / '_workspace')
    root.mkdir(parents=True, exist_ok=True)
    return root


@contextmanager
def database():
    root = registry_root()
    with sqlite3.connect(root / 'registry.sqlite3', timeout=30) as connection:
        connection.execute('PRAGMA foreign_keys=ON')
        version = connection.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0, 1):
            raise HTTPException(409, {'code': 'REGISTRY_SCHEMA_UNSUPPORTED',
                                     'message': 'This workspace needs a compatible BRACE version.'})
        connection.executescript('''
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY, identity TEXT NOT NULL UNIQUE, record TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS studies (
                id TEXT PRIMARY KEY, record TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS study_datasets (
                study_id TEXT NOT NULL REFERENCES studies(id),
                role TEXT NOT NULL, dataset_id TEXT NOT NULL REFERENCES datasets(id),
                PRIMARY KEY(study_id, role));
            CREATE TABLE IF NOT EXISTS dataset_checks (
                id TEXT PRIMARY KEY, record TEXT NOT NULL);
            PRAGMA user_version=1;
        ''')
        yield connection


def valid_id(value: str) -> bool:
    return bool(re.fullmatch(r'[0-9a-f]{32}', value))


def get_dataset(dataset_id: str) -> dict:
    if not valid_id(dataset_id):
        raise HTTPException(404, 'Dataset not found')
    with database() as connection:
        row = connection.execute('SELECT record FROM datasets WHERE id=?', (dataset_id,)).fetchone()
    if row is None:
        raise HTTPException(404, 'Dataset not found')
    try:
        record = json.loads(row[0])
    except (ValueError, TypeError) as exc:
        raise HTTPException(409, {'code': 'REGISTRY_RECORD_INVALID',
            'message': 'This dataset record is damaged. Restore its matching workspace backup.'}) from exc
    if record.get('schema_version') != SCHEMA_VERSION:
        raise HTTPException(409, 'Unsupported dataset record schema')
    return record


def list_datasets() -> list[dict]:
    with database() as connection:
        rows = connection.execute('SELECT record FROM datasets').fetchall()
    return sorted((json.loads(row[0]) for row in rows),
                  key=lambda record: (record['created_utc'], record['id']), reverse=True)


def lineage_snapshot(dataset_id: str, ancestors: frozenset[str] = frozenset()) -> dict:
    """Exportable ancestor records, including original acquisition URLs and hashes."""
    if dataset_id in ancestors or len(ancestors) >= 32:
        raise HTTPException(409, {'code':'DATASET_LINEAGE_INVALID',
            'message':'Dataset ancestry is cyclic or exceeds the supported 32-version chain. Restore a valid registry.'})
    record = get_dataset(dataset_id)
    return {**record, 'parent_records': [lineage_snapshot(parent, ancestors | {dataset_id})
                                       for parent in record.get('parent_dataset_ids', [])]}


def asset_path(dataset_id: str, kind: str) -> Path:
    record = get_dataset(dataset_id)
    asset = record['assets'].get(kind)
    if not asset:
        raise HTTPException(404, 'Dataset asset unavailable')
    folder = within(registry_root(), registry_root() / dataset_id)
    path = within(folder, folder / asset['storage_name'])
    if not path.is_file() or digest(path) != asset['sha256']:
        raise HTTPException(409, {'code': 'DATASET_INTEGRITY_MISMATCH',
            'message': 'This dataset asset is missing or changed. Restore the matching file or register a new version.'})
    return path


def register(paths: dict[str, Path], *, name: str, source: dict, summary: dict | None = None,
             history: list | None = None, parent_ids: list[str] | None = None,
             original_names: dict[str, str] | None = None) -> dict:
    """Copy immutable verified assets; publish only complete records."""
    parents = parent_ids or []
    for parent in parents:
        get_dataset(parent)
    assets = {kind: {'filename': (original_names or {}).get(kind, path.name),
                     'storage_name': kind + path.suffix.lower(), 'sha256': digest(path),
                     'bytes': path.stat().st_size}
              for kind, path in paths.items()}
    identity = hashlib.sha256(json.dumps({
        'assets': {kind: value['sha256'] for kind, value in assets.items()},
        'source': source, 'history': history or [], 'parents': parents}, sort_keys=True).encode()).hexdigest()
    with database() as connection:
        previous = connection.execute('SELECT id FROM datasets WHERE identity=?', (identity,)).fetchone()
    if previous:
        record = get_dataset(previous[0])
        for kind in record['assets']:
            asset_path(record['id'], kind)
        return record
    root = registry_root()
    with tempfile.TemporaryDirectory(prefix='stage-', dir=root) as temporary:
        staging = Path(temporary)
        for kind, path in paths.items():
            destination = staging / assets[kind]['storage_name']
            shutil.copyfile(path, destination)
            if digest(destination) != assets[kind]['sha256']:
                raise HTTPException(409, 'Dataset changed during registration. Retry with stable inputs.')
        dataset_id = uuid.uuid4().hex
        timestamp = utc_now()
        record = dict(schema_version=SCHEMA_VERSION, id=dataset_id,
            name=study_name(name, 'Local dataset'), source=source, assets=assets,
            status='prepared' if summary else 'acquired', summary=summary,
            preprocessing_history=history or [], parent_dataset_ids=parents,
            created_utc=timestamp, modified_utc=timestamp,
            warnings=(summary or {}).get('warnings', []),
            eligibility={'status': 'pair_specific', 'reason': 'Decisions belong to exact task/pair/contrast records at /api/datasets/{id}/checks.'})
        with database() as connection:
            connection.execute('BEGIN IMMEDIATE')
            previous = connection.execute('SELECT id FROM datasets WHERE identity=?', (identity,)).fetchone()
            if previous:
                # A matching index never excuses a corrupted asset.
                old_id = previous[0]
                old_record = json.loads(connection.execute('SELECT record FROM datasets WHERE id=?', (old_id,)).fetchone()[0])
                for kind, asset in old_record['assets'].items():
                    old_folder = within(root, root / old_id)
                    old_path = within(old_folder, old_folder / asset['storage_name'])
                    if not old_path.is_file() or digest(old_path) != asset['sha256']:
                        raise HTTPException(409, 'An existing identical dataset has damaged assets. Restore its original files.')
                return old_record
            destination = root / dataset_id
            # The directory stays unlisted if an interrupted transaction leaves an orphan.
            staging.rename(destination)
            connection.execute('INSERT INTO datasets VALUES(?,?,?)',
                               (dataset_id, identity, json.dumps(record, ensure_ascii=False)))
        return record


def register_cohort(paths: dict[str, Path], *, name: str, source: dict,
                    history: list | None = None, parent_ids: list[str] | None = None,
                    original_names: dict[str, str] | None = None) -> dict:
    from brace_core.intake import parse_cohort
    from brace_core.contracts import cohort_summary
    from brace_core.assays import identifier_hints
    manifest = json.loads(paths['manifest'].read_text(encoding='utf-8-sig'))
    if not isinstance(manifest,dict) or manifest.get('role') not in ('source','target'):
        from brace_core.intake import InputProblem
        raise InputProblem('MANIFEST_INVALID','Declare source or target role in the dataset manifest.',
                           'Provide the complete BRACE cohort manifest.','manifest.role')
    cohort = parse_cohort(paths['expression'], paths['metadata'], paths['manifest'], manifest['role'])
    summary = {**cohort_summary(cohort), 'sample_ids': list(cohort.sample_ids),
        'manifest': cohort.manifest, 'missing_values': 0,
        'phenotype_mapping': {label: label for label in cohort_summary(cohort)['observed_conditions']},
        'identifier_hints': identifier_hints(cohort.feature_ids),
        'warnings': [issue.to_dict() for issue in cohort.warnings]}
    return register(paths, name=name, source=source, summary=summary, history=history,
                    parent_ids=parent_ids, original_names=original_names)


def rename_dataset(dataset_id: str, name: str) -> dict:
    record = get_dataset(dataset_id)
    record.update(name=study_name(name, record['name']), modified_utc=utc_now())
    with database() as connection:
        connection.execute('UPDATE datasets SET record=? WHERE id=?', (json.dumps(record), dataset_id))
    return record


def create_study(name: str, assignments: dict[str, str] | None = None) -> dict:
    assignments = assignments or {}
    if set(assignments) - {'source', 'target', 'predictions'}:
        raise HTTPException(422, 'Unsupported dataset role')
    for dataset_id in assignments.values():
        get_dataset(dataset_id)
    timestamp = utc_now()
    record = dict(schema_version=SCHEMA_VERSION, id=uuid.uuid4().hex,
                  name=study_name(name, 'Local study'), created_utc=timestamp, modified_utc=timestamp)
    with database() as connection:
        connection.execute('INSERT INTO studies VALUES(?,?)', (record['id'], json.dumps(record)))
        for role, dataset_id in assignments.items():
            connection.execute('INSERT INTO study_datasets VALUES(?,?,?)', (record['id'], role, dataset_id))
    return {**record, 'datasets': assignments}


def get_study(study_id: str) -> dict:
    with database() as connection:
        row = connection.execute('SELECT record FROM studies WHERE id=?', (study_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'Study not found')
        datasets = dict(connection.execute('SELECT role,dataset_id FROM study_datasets WHERE study_id=?', (study_id,)))
    return {**json.loads(row[0]), 'datasets': datasets}


def list_studies() -> list[dict]:
    with database() as connection:
        ids = [row[0] for row in connection.execute('SELECT id FROM studies')]
    return sorted((get_study(study_id) for study_id in ids), key=lambda record: record['created_utc'], reverse=True)


def save_check(request: dict, result: dict) -> dict:
    record = dict(id=uuid.uuid4().hex, schema_version=SCHEMA_VERSION,
                  created_utc=utc_now(), request=request, result=result)
    with database() as connection:
        connection.execute('INSERT INTO dataset_checks VALUES(?,?)', (record['id'], json.dumps(record)))
    return record


def dataset_checks(dataset_id: str) -> list[dict]:
    get_dataset(dataset_id)
    with database() as connection:
        rows = connection.execute('SELECT record FROM dataset_checks').fetchall()
    records = [json.loads(row[0]) for row in rows]
    return sorted((record for record in records if dataset_id in record['request']['datasets'].values()),
                  key=lambda record: record['created_utc'], reverse=True)[:50]


def provenance_for_mode(records: dict, mode: str) -> dict:
    if mode != 'diagnose_shift':
        return records
    # Unlabeled evidence carries structural lineage, never phenotype values/counts.
    record_fields = ('schema_version', 'id', 'name', 'source', 'assets', 'status',
                     'parent_dataset_ids', 'created_utc', 'modified_utc')
    summary_fields = ('cohort_id', 'role', 'n_samples', 'n_features', 'sample_ids',
                      'feature_namespace', 'measurement_type', 'platform', 'processing_description',
                      'independence_declaration', 'missing_values', 'input_files')
    history_fields = ('operation', 'version', 'recipe_sha256', 'mapping_sha256',
                      'feature_selection', 'automatic_normalization', 'original_features',
                      'retained_features', 'unmapped_features', 'feature_mapping', 'mapping_reference')
    def structural_record(record):
        return {**{key: record[key] for key in record_fields if key in record},
                   'summary': {key: value for key, value in (record.get('summary') or {}).items() if key in summary_fields},
                   'preprocessing_history': [{key: value for key, value in step.items() if key in history_fields}
                                             for step in record.get('preprocessing_history', [])],
                   'parent_records': [structural_record(parent) for parent in record.get('parent_records', [])],
                   'note': 'Phenotypes are omitted from this unlabeled analysis record.'}
    return {role: structural_record(record) for role, record in records.items()}


def register_run_inputs(paths: dict[str, Path], hashes: dict, mode: str, title: str,
                        study_id: str | None = None, dataset_ids: dict | None = None) -> dict:
    """Bind run snapshots to exact dataset versions; never infer IDs from filenames."""
    datasets = dataset_ids or {}
    for role in ('predictions',) if mode == 'evaluate_predictions' else ('source', 'target'):
        kinds = ('predictions', 'prediction_manifest') if role == 'predictions' else ('expression', 'metadata', 'manifest')
        role_paths = {kind: paths[kind if role == 'predictions' else role + '_' + kind] for kind in kinds}
        if role in datasets:
            for kind, path in role_paths.items():
                if digest(asset_path(datasets[role], kind)) != digest(path):
                    raise HTTPException(409, 'Selected dataset version does not match these analysis inputs.')
        else:
            names = {kind: hashes[kind if role == 'predictions' else role + '_' + kind]['filename'] for kind in kinds}
            if role == 'predictions':
                record = register(role_paths, name=title + ' · predictions', source={'type': 'imported_file'},
                    summary={'kind': 'saved_predictions'}, original_names=names)
            else:
                record = register_cohort(role_paths, name=title + ' · ' + role,
                    source={'type': 'imported_file'}, original_names=names)
            datasets[role] = record['id']
    study = get_study(study_id) if study_id else create_study(title, datasets)
    if study['datasets'] != datasets:
        raise HTTPException(409, 'Study assignments differ from the selected dataset versions. Create a new study.')
    if study['name'] != title:
        raise HTTPException(409, 'Study name differs from the saved study. Create a new study for a new research question.')
    return {'schema_version': SCHEMA_VERSION, 'study_id': study['id'],
            'datasets': datasets, 'created_utc': utc_now(),
            'dataset_provenance': provenance_for_mode({role: lineage_snapshot(dataset_id) for role, dataset_id in datasets.items()}, mode)}
