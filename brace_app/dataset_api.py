"""Prepared datasets hand off to existing preflight and computation routes."""
from __future__ import annotations

import json
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from brace_app import dataset_registry as registry
from brace_app.persistence import SCHEMA_VERSION
from brace_core.intake import InputProblem

router = APIRouter()


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal['1.0.0'] = SCHEMA_VERSION


class Name(Contract):
    name: str = Field(min_length=1, max_length=200)


class Study(Name):
    datasets: dict[Literal['source', 'target', 'predictions'], str] = Field(default_factory=dict)


class Reviewed(Contract):
    reviewed: Literal[True]


class Analysis(Name):
    mode: Literal['race', 'train_validate', 'diagnose_shift', 'evaluate_predictions']
    datasets: dict[Literal['source', 'target', 'predictions'], str]
    study_id: str | None = None
    race_config: dict = Field(default_factory=dict)


class GeneralPreparation(Name):
    reviewed: Literal[True]
    manifest: dict
    condition_by_sample: dict[str, str]
    excluded_samples: dict[str, str] = Field(default_factory=dict)
    feature_mapping: dict[str, str] = Field(default_factory=dict)
    mapping_reference: str = Field(default='', max_length=2000)


class Transformation(Name):
    reviewed: Literal[True]
    role: Literal['source', 'target']
    condition_mapping: dict[str, str] = Field(default_factory=dict)
    biological_definitions: dict[str, str] = Field(default_factory=dict)


@router.get('/api/datasets')
def datasets():
    return {'schema_version': SCHEMA_VERSION, 'datasets': registry.list_datasets()}


@router.get('/api/datasets/{dataset_id}')
def dataset(dataset_id: str):
    return registry.get_dataset(dataset_id)


@router.patch('/api/datasets/{dataset_id}')
def rename_dataset(dataset_id: str, request: Name):
    try:
        return registry.rename_dataset(dataset_id, request.name)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get('/api/datasets/{dataset_id}/assets/{kind}')
def dataset_asset(dataset_id: str, kind: str):
    record = registry.get_dataset(dataset_id)
    path = registry.asset_path(dataset_id, kind)
    return FileResponse(path, filename=record['assets'][kind]['filename'],
                        headers={'X-Content-Type-Options': 'nosniff'})


@router.get('/api/datasets/{dataset_id}/checks')
def dataset_checks(dataset_id: str):
    return {'schema_version': SCHEMA_VERSION, 'checks': registry.dataset_checks(dataset_id)}


@router.get('/api/studies')
def studies():
    return {'schema_version': SCHEMA_VERSION, 'studies': registry.list_studies()}


@router.post('/api/studies')
def create_study(request: Study):
    try:
        return registry.create_study(request.name, request.datasets)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get('/api/studies/{study_id}')
def study(study_id: str):
    return registry.get_study(study_id)


@router.post('/api/datasets/import')
async def import_dataset(name: Annotated[str, Form()],
                         expression: Annotated[UploadFile, File()],
                         metadata: Annotated[UploadFile, File()],
                         manifest: Annotated[UploadFile, File()]):
    from brace_app import server
    try:
        with tempfile.TemporaryDirectory(prefix='brace-import-') as temporary:
            paths = {}
            names = {}
            for kind, file in [('expression', expression), ('metadata', metadata), ('manifest', manifest)]:
                paths[kind], info = await server.save_file(file, Path(temporary), kind,
                    ('.json',) if kind == 'manifest' else ('.csv', '.tsv'))
                names[kind] = info['filename']
            return await run_in_threadpool(registry.register_cohort, paths, name=name,
                source={'type': 'imported_file'}, original_names=names)
    except (InputProblem, ValueError) as exc:
        raise HTTPException(422, exc.to_dict() if isinstance(exc, InputProblem) else str(exc)) from exc


def register_acquisition(receipt: dict, path: Path) -> dict:
    return registry.register({'original': path}, name=receipt['accession'] + ' · original matrix',
        source={'type': 'geo', 'accession': receipt['accession'], 'url': receipt['url'],
                'original_sha256': receipt['sha256']},
        history=[{'operation': 'public_acquisition', 'original_filename': receipt['filename']}],
        original_names={'original': receipt['filename']})


@router.post('/api/datasets/reviewed-public')
def reviewed_public(request: Reviewed):
    """Use byte-pinned recipe outputs, linked to verified originals; works offline."""
    from brace_app.study_api import public_paths
    pair = public_paths()
    downloads = json.loads((pair / 'evidence/downloads.json').read_text(encoding='utf-8'))
    originals = []
    for accession in ('GSE42568', 'GSE20711'):
        entry = next(row for row in downloads if row['file'] == accession + '_series_matrix.txt.gz')
        path = pair / 'raw' / entry['file']
        if not path.is_file() or registry.digest(path) != entry['sha256']:
            raise HTTPException(409, 'Reviewed public original is missing or changed. Restore the pinned original.')
        originals.append(register_acquisition(dict(accession=accession, filename=entry['file'],
            url=entry['url'], sha256=entry['sha256']), path)['id'])
    recipe = {'operation': 'pinned_public_er_recipe', 'version': '1.0.0',
              'recipe_sha256': registry.digest(pair / 'prepare.py'),
              'mapping_sha256': registry.digest(pair / 'evidence/GPL570_mapping.tsv'),
              'feature_selection': 'Source-only population variance; original GPL570 one-probe-per-Entrez mapping',
              'preparation_summary': json.loads((pair / 'prepared/summary.json').read_text()),
              'limitations': 'Exploratory ER associations only; processing and ER assays differ; donor independence unknown.'}
    prepared = {}
    for role in ('source', 'target'):
        paths = {kind: pair / 'prepared' / (role + '_' + kind + suffix)
                 for kind, suffix in [('expression', '.tsv'), ('metadata', '.tsv'), ('manifest', '.json')]}
        manifest = json.loads(paths['manifest'].read_text())
        prepared[role] = registry.register_cohort(paths, name=manifest['cohort_id'],
            source={'type': 'prepared_example', 'accession': manifest['accession']},
            history=[recipe], parent_ids=originals)
    return {'schema_version': SCHEMA_VERSION, 'datasets': prepared,
            'race_config': json.loads((pair / 'race_config.json').read_text()),
            'note': recipe['limitations']}


@router.get('/api/datasets/{dataset_id}/inspect')
def inspect_original(dataset_id: str):
    from brace_app.preparation import series_matrix
    from brace_core.assays import identifier_hints
    try:
        parsed = series_matrix(registry.asset_path(dataset_id, 'original'))
        return {'schema_version': SCHEMA_VERSION, 'sample_ids': parsed['sample_ids'],
            'feature_count': len(parsed['feature_ids']), 'feature_preview': parsed['feature_ids'][:30],
            'identifier_hints': identifier_hints(parsed['feature_ids']),
            'metadata': parsed['metadata'], 'eligible': False,
            'note': 'Numeric parsing only. Review phenotypes, identifiers, measurement scale and processing before preparing.'}
    except InputProblem as exc:
        raise HTTPException(422, exc.to_dict()) from exc


@router.post('/api/datasets/{dataset_id}/transform')
def transform_dataset(dataset_id: str, request: Transformation):
    """Explicit phenotype/role changes always create a separate immutable version."""
    import csv
    record = registry.get_dataset(dataset_id)
    if not (record.get('summary') or {}).get('manifest'):
        raise HTTPException(422, 'Choose a prepared expression dataset for transformation.')
    paths = {kind: registry.asset_path(dataset_id, kind) for kind in ('expression', 'metadata', 'manifest')}
    mapping = request.condition_mapping
    observed = set(record['summary']['observed_conditions'])
    if mapping and (set(mapping) != observed or any(not label.strip() for label in mapping.values())):
        raise HTTPException(422, 'Map every observed condition to a nonempty reviewed biological class.')
    if mapping and (set(request.biological_definitions) != set(mapping.values()) or
                    any(not definition.strip() for definition in request.biological_definitions.values())):
        raise HTTPException(422, 'Provide a biological definition for every mapped class.')
    with tempfile.TemporaryDirectory(prefix='brace-remap-') as temporary:
        folder = Path(temporary)
        manifest = dict(record['summary']['manifest'], role=request.role)
        manifest_path = folder / 'manifest.json'
        manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
        metadata_path = paths['metadata']
        if mapping:
            with metadata_path.open(encoding='utf-8-sig', newline='') as stream:
                reader = csv.DictReader(stream, delimiter='\t' if metadata_path.suffix == '.tsv' else ',')
                columns = reader.fieldnames
                rows = [{**row, 'condition': mapping.get(row.get('condition', ''), '')} for row in reader]
            metadata_path = folder / 'metadata.tsv'
            with metadata_path.open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=columns, delimiter='\t')
                writer.writeheader()
                writer.writerows(rows)
        try:
            return registry.register_cohort({**paths, 'metadata': metadata_path, 'manifest': manifest_path},
                name=request.name, source={'type': 'reviewed_transformation'}, parent_ids=[dataset_id],
                history=[{'operation': 'phenotype_and_role_review', 'role': request.role,
                          'condition_mapping': mapping, 'biological_definitions': request.biological_definitions,
                          'expression_unchanged': True}])
        except (InputProblem, ValueError) as exc:
            raise HTTPException(422, exc.to_dict() if isinstance(exc, InputProblem) else str(exc)) from exc


@router.post('/api/datasets/{dataset_id}/prepare')
def prepare_original(dataset_id: str, request: GeneralPreparation):
    from brace_app.preparation import prepare_general
    try:
        with tempfile.TemporaryDirectory(prefix='brace-prepare-') as temporary:
            paths, report = prepare_general(registry.asset_path(dataset_id, 'original'), Path(temporary),
                manifest=request.manifest, condition_by_sample=request.condition_by_sample,
                excluded_samples=request.excluded_samples, feature_mapping=request.feature_mapping,
                mapping_reference=request.mapping_reference)
            from brace_app import server
            if any(path.stat().st_size > server.MAX_FILE for path in paths.values()):
                raise ValueError('Prepared assets exceed the 25 MiB limit. Supply a documented smaller preparation.')
            return registry.register_cohort(paths, name=request.name, source={'type': 'prepared_geo'},
                history=[report], parent_ids=[dataset_id])
    except (InputProblem, ValueError) as exc:
        raise HTTPException(422, exc.to_dict() if isinstance(exc, InputProblem) else str(exc)) from exc


@router.get('/api/datasets/{dataset_id}/reviewed-er-plan')
def reviewed_er_plan(dataset_id: str):
    from brace_app.public_recipes import er_21653_plan
    try:
        return er_21653_plan(dataset_id)
    except (InputProblem, ValueError) as exc:
        raise HTTPException(422, exc.to_dict() if isinstance(exc, InputProblem) else str(exc)) from exc


async def delegate(request: Analysis, compute: bool):
    from brace_app import server, study_api
    needed = {'predictions'} if request.mode == 'evaluate_predictions' else {'source', 'target'}
    if set(request.datasets) != needed:
        raise HTTPException(422, 'Select exactly the dataset roles required for this task.')
    if request.study_id:
        saved_study = registry.get_study(request.study_id)
        if saved_study['datasets'] != request.datasets or saved_study['name'] != request.name.strip():
            raise HTTPException(409, 'Study name or dataset assignments differ. Create a new study for these inputs.')
    with ExitStack() as stack:
        uploads = {}
        for role, dataset_id in request.datasets.items():
            record = registry.get_dataset(dataset_id)
            if record['status']!='prepared':
                raise HTTPException(422, {'code':'DATASET_PREPARATION_REQUIRED',
                    'message':'This is an acquired original. Inspect its annotations and prepare a reviewed dataset version before analysis.'})
            kinds = ('predictions', 'prediction_manifest') if role == 'predictions' else ('expression', 'metadata', 'manifest')
            for kind in kinds:
                path = registry.asset_path(dataset_id, kind)
                # Reads immutable assets; no data download/re-upload through the browser.
                file = stack.enter_context(path.open('rb'))
                uploads[kind if role == 'predictions' else role + '_' + kind] = UploadFile(
                    file=file, filename=record['assets'][kind]['filename'])
        if not compute:
            result = await study_api.preflight(mode=request.mode, race_config=json.dumps(request.race_config),
                                              name=request.name, **uploads)
            check = registry.save_check(request.model_dump(), result)
            return {**result, 'check_id': check['id'], 'schema_version': SCHEMA_VERSION, 'name': request.name,
                    'datasets': request.datasets, 'study_id': request.study_id}
        common = dict(name=request.name, study_id=request.study_id,
                      dataset_ids=json.dumps(request.datasets), **uploads)
        if request.mode == 'race':
            return await server.race_analyze(race_config=json.dumps(request.race_config), **common)
        return await server.analyze(mode=request.mode, **common)


@router.post('/api/dataset-analysis/preflight')
async def preflight(request: Analysis):
    return await delegate(request, False)


@router.post('/api/dataset-analysis/run')
async def analyze(request: Analysis):
    return await delegate(request, True)
