"""Apply only an existing verified BRACE JSON freeze; no executable uploads."""
from __future__ import annotations

import csv
import html
import io
import json
import shutil
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from brace_app import dataset_registry as registry
from brace_app.dataset_api import Name
from brace_app.export_safety import csv_bytes, within
from brace_app.persistence import atomic_json, run_identity, study_name, utc_now
from brace_core.baseline05 import canonical_sha
from brace_core.intake import InputProblem

router = APIRouter()


class Replay(Name):
    frozen_run_id: str
    target_dataset_id: str


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def trace(root: Path) -> dict:
    config = read(root / 'run.json')
    stage = read(root / 'validation/stage05/run_result.json')
    return dict(study_id=config['id'], analysis='ace', mode='replay_frozen', evaluation_role='external_exploratory',
        steps=[
            dict(key='inputs', title='Target dataset and original freeze', status='recorded',
                 data={'dataset': config['dataset_provenance']['target'], 'frozen_run_id': config['frozen_run_id'],
                       'frozen_source_provenance':config.get('frozen_source_provenance'),
                       'input_hashes': config['input_hashes']}, artifacts=[]),
            dict(key='model', title='Frozen source transformation and model', status='recorded',
                 data={'freeze': stage['freeze'], 'note': 'Parameters and features were frozen in the original source run. No refit occurs.'}, artifacts=[]),
            dict(key='scoring', title='Apply frozen source parameters', status='computed',
                 data={'n': stage['outputs']['n_samples'], 'note': 'Required frozen features are aligned by exact identifier; source scaling and coefficients are reused.'}, artifacts=[]),
            dict(key='metrics', title='Labeled evaluation or prediction-only result', status='computed' if stage['outputs']['evaluation_possible'] else 'not_performed',
                 data={'metrics': stage['outputs']['external'], 'note': 'Accuracy is unavailable without target reference labels.'}, artifacts=[])],
        warnings=stage['warnings'], artifacts=[], provenance_authenticated=False)


def finalize(root: Path) -> Path:
    """Audit, publish and hash a replay without inventing OOF or unlabeled metrics."""
    from brace_app.embrace import json_bytes, record, verify_previous, VERSION
    from brace_app.release09 import package_versions
    config = read(root / 'run.json')
    previous_path = root / 'reproducibility_manifest.json'
    previous = read(previous_path) if previous_path.is_file() else None
    if previous:
        verify_previous(root, previous)
        if previous['run_configuration_sha256'] != record((root / 'run.json').read_bytes()):
            raise ValueError('Frozen replay run configuration changed')
    for field, entry in config['input_hashes'].items():
        suffix = '.json' if field in ('frozen_model', 'target_manifest') else Path(entry['storage_name']).suffix
        path = within(root, root / 'input' / (field + suffix))
        if registry.digest(path) != entry['sha256']:
            raise ValueError('Frozen replay input changed: ' + field)
    model = read(root / 'input/frozen_model.json')
    if canonical_sha({key: value for key, value in model.items() if key != 'model_sha256'}) != model['model_sha256']:
        raise ValueError('Frozen replay model hash mismatch')
    stage = read(root / 'validation/stage05/run_result.json')
    if stage['freeze']['model_sha256'] != model['model_sha256']:
        raise ValueError('Frozen replay result/model identity mismatch')
    output = stage['outputs']
    prediction_path = root / 'validation/stage05/target_predictions_unlabeled.csv'
    with prediction_path.open(encoding='utf-8', newline='') as stream:
        predictions = list(csv.DictReader(stream))
    if len(predictions) != output['n_samples'] or len({row['sample_id'] for row in predictions}) != len(predictions):
        raise ValueError('Frozen replay prediction sample identity mismatch')
    validation = read(root / 'validation/validation_result.json') if output['evaluation_possible'] else None
    if validation:
        from brace_app.evidence_audit import prediction_audit
        prediction_audit(root, validation)
        if {row['sample_id']: row['predicted_label'] for row in predictions} != {
                row['sample_id']: row['predicted_label'] for row in validation['analysis']['records']}:
            raise ValueError('Frozen replay prediction/evaluation identity mismatch')
    elif output['external'] is not None or not (root / 'validation/unlabeled_result.json').is_file():
        raise ValueError('Unlabeled replay must not publish accuracy')
    scientific = {}
    for folder in ('validation', 'validation/stage05'):
        for path in sorted((root / folder).iterdir()):
            if path.is_file() and path.suffix in ('.csv', '.json', '.html'):
                scientific[path.relative_to(root).as_posix()] = record(path.read_bytes())
    bundle = root / 'RESEARCH_PACKAGE.zip'
    if previous and bundle.is_file():
        if record(bundle.read_bytes()) != read(root / 'EMBRACE_RECEIPT.json')['bundle']:
            raise ValueError('Frozen replay package changed')
        for name, expected in previous['published_artifact_sha256'].items():
            if record(within(root, root / 'embrace' / name).read_bytes()) != expected:
                raise ValueError('Published frozen replay evidence changed')
        if previous.get('embrace_version')==VERSION:
            return bundle
    contents = {}
    encoding = {}
    for name in scientific:
        data = (root / name).read_bytes()
        if name.endswith('.csv'):
            data, changes = csv_bytes(data)
            if changes:
                encoding[name] = changes
        contents[name] = data
    metrics = output['external']
    result_text = (f"{metrics['n_correct']} correct predictions among {metrics['n']} labeled samples."
                   if metrics else f"{len(predictions)} predictions. No target reference labels; accuracy is unavailable.")
    escaped = html.escape
    report = ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + escaped(config['name']) + '</title><main><h1>' + escaped(config['name']) + '</h1><h2>ACE · Frozen baseline application</h2><p>'
        + result_text + '</p><p>' + escaped(config.get('data_label','Researcher-declared target provenance.')) + '</p><p>Frozen source parameters were applied without fitting on target data. '
        'Source/target processing and independently acquired samples remain researcher-reviewed assumptions.</p><pre>'
        + escaped(json.dumps({'study_id': config['study_id'], 'run_id': config['id'], 'original_run_id': config['frozen_run_id'],
                             'model_sha256': model['model_sha256'], 'metrics': metrics, 'warnings': stage['warnings']}, indent=2))
        + '</pre><p>Original input files are excluded. Match their hashes before reproducing this analysis.</p>'
        '<p>Reproduce with python -m brace_core.stage06_cli replay --model ORIGINAL_FREEZE.json '
        '--target-expression TARGET.tsv --target-metadata METADATA.tsv --target-manifest MANIFEST.json --out NEW_DIRECTORY.</p></main></html>')
    lineage={**config['dataset_provenance'],'frozen_source_run':config.get('frozen_source_provenance')}
    contents.update({'research_summary.html': report.encode(),
        'analysis_methods.json': json_bytes(trace(root)), 'DATASET_LINEAGE.json': json_bytes(lineage),
        'consistency_audit.json': json_bytes({'status': 'PASS', 'prediction_rows': len(predictions),
            'model_sha256': model['model_sha256'], 'labeled_evaluation_audited': metrics is not None}),
        'CSV_TEXT_ENCODING.json': json_bytes({'changed_cells': encoding}),
        'methods/frozen_model.json': json_bytes(model),
        'methods/TRACE.json': json_bytes(trace(root)),
        'provenance/study.json': json_bytes({key: config[key] for key in ('name', 'study_id', 'datasets', 'created_utc')}),
        'provenance/DATASET_LINEAGE.json': json_bytes(lineage),
        'results/predictions.json': json_bytes({'metrics': metrics, 'records': predictions}),
        'summary/report.html': report.encode()})
    manifest = dict(embrace_version=VERSION, schema_version='1.0.0', mode='replay_frozen', run_id=config['id'],data_origin=config.get('kind','user_computed'),
        study_id=config['study_id'], study_name=config['name'], datasets=config['datasets'],
        frozen_run_id=config['frozen_run_id'], input_hashes=config['input_hashes'],
        run_configuration_sha256=record((root / 'run.json').read_bytes()), scientific_artifact_sha256=scientific,
        artifact_sha256=scientific, software_versions=package_versions(),
        metrics_available=metrics is not None, target_labels_used_for_fitting=False,
        published_artifact_sha256={name: record(data) for name, data in contents.items()})
    contents['reproducibility_manifest.json'] = json_bytes(manifest)
    inventory = io.StringIO(newline='')
    writer = csv.writer(inventory)
    writer.writerow(['path', 'sha256', 'bytes'])
    for name, data in sorted(contents.items()):
        writer.writerow([name, record(data)['sha256'], len(data)])
    contents['FILE_SHA256_MANIFEST.csv'] = inventory.getvalue().encode()
    contents['integrity/FILE_SHA256_MANIFEST.csv'] = contents['FILE_SHA256_MANIFEST.csv']
    from brace_app.embrace import publish_evidence
    return publish_evidence(root, contents, manifest)


def response(root: Path) -> dict:
    from brace_app import server
    server.finalize_run(root)
    config = read(root / 'run.json')
    stage = read(root / 'validation/stage05/run_result.json')
    labeled = stage['outputs']['evaluation_possible']
    with (root / 'validation/stage05/target_predictions_unlabeled.csv').open(encoding='utf-8', newline='') as stream:
        predictions = list(csv.DictReader(stream))
    return {'id': config['id'], 'name': config['name'], 'kind': config.get('kind','user_computed'), 'mode': 'replay_frozen',
        **run_identity(root, config), 'validation': server.mini_validation(read(root / 'validation/validation_result.json')) if labeled else None,
        'shift': None, 'replay': {'n': stage['outputs']['n_samples'], 'records': predictions,
            'metrics': stage['outputs']['external'], 'evaluation_possible': labeled,
            'frozen_run_id': config['frozen_run_id'], 'model_sha256': stage['freeze']['model_sha256']},
        'notes': ['Existing source freeze applied without refitting. Accuracy requires target reference labels.'],
        'data_label': config.get('data_label','Frozen BRACE baseline application; target acquisition and processing are user-declared.'),
        'provenance': config['input_hashes'], 'exports': []}


@router.post('/api/dataset-analysis/replay')
async def replay(request: Replay):
    from brace_app import server
    from brace_core.stage06_cli import replay as compute_replay
    source_root = server.safe_run_dir(request.frozen_run_id)
    source = server.get_run(request.frozen_run_id)  # structured 409 if the original evidence changed
    if source['mode'] != 'train_validate':
        raise HTTPException(422, 'Select an original source-trained BRACE baseline run.')
    target = registry.lineage_snapshot(request.target_dataset_id)
    if request.target_dataset_id == source.get('datasets',{}).get('source'):
        raise HTTPException(422, 'This is the original training dataset. Choose a different target for a transfer evaluation.')
    if not (target.get('summary') or {}).get('manifest'):
        raise HTTPException(422,'Choose a prepared expression target, not an acquired original or prediction table.')
    paths = {kind: registry.asset_path(target['id'], kind) for kind in ('expression', 'metadata', 'manifest')}
    target['assigned_role'] = 'target'
    root = server.RUNS / uuid.uuid4().hex
    raw = root / 'input'
    raw.mkdir(parents=True, exist_ok=False)
    try:
        hashes = {}
        for kind, original in {**{'target_' + kind: path for kind, path in paths.items()},
                               'frozen_model': source_root / 'validation/stage05/frozen_model.json'}.items():
            filename = kind + original.suffix
            shutil.copyfile(original, raw / filename)
            if kind == 'target_manifest' and target['summary']['manifest']['role'] != 'target':
                bound = json.loads((raw / filename).read_text(encoding='utf-8-sig'))
                bound['role'] = 'target'
                (raw / filename).write_text(json.dumps(bound),encoding='utf-8')
            hashes[kind] = {'filename': original.name, 'storage_name': filename,
                            'sha256': registry.digest(raw / filename), 'bytes': (raw / filename).stat().st_size}
        def execute():
            compute_replay(raw / 'frozen_model.json', *(raw / ('target_' + kind + paths[kind].suffix)
                for kind in ('expression', 'metadata', 'manifest')), root / 'validation')
            title = study_name(request.name, 'Frozen baseline application')
            study = registry.create_study(title, {'target': target['id']})
            atomic_json(root / 'run.json', {'schema_version': '1.0.0', 'id': root.name,
                'name': title, 'mode': 'replay_frozen', 'study_id': study['id'], 'created_utc': utc_now(),
                'kind':'synthetic' if source.get('kind')=='synthetic' else 'user_computed',
                'data_label':'Artificial source-trained model; software demonstration, not biological evidence.' if source.get('kind')=='synthetic' else 'Frozen BRACE baseline application; target acquisition and processing are user-declared.',
                'datasets': study['datasets'], 'dataset_provenance': {'target': target},
                'frozen_run_id': request.frozen_run_id,
                'frozen_source_provenance':{key:read(source_root/'run.json').get(key) for key in ('id','name','study_id','datasets','dataset_provenance','input_hashes','created_utc')},
                'input_hashes': hashes})
            return response(root)
        return await run_in_threadpool(execute)
    except (InputProblem, ValueError, KeyError, TypeError) as exc:
        shutil.rmtree(root, ignore_errors=True)
        raise HTTPException(422, exc.to_dict() if isinstance(exc, InputProblem) else {'code': 'FROZEN_REPLAY_BLOCKED', 'message': str(exc)}) from exc
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
