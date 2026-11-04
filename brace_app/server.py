"""BRACE Stage 08: localhost-only API and read-only scientific study viewer.

Never executes uploaded code or model binaries. Every user run gets its own random output
folder; only allowlisted files can be downloaded. All input science routes delegate to
the previously tested Stage 04-07 engines.
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse
from brace_core.intake import InputProblem
from brace_core import stage06_cli, stage07_cli
from brace_app.release09 import finalize_run, build_historical_package
from brace_app.local_settings import local_port

BASE = Path(__file__).resolve().parent.parent
EXAMPLES = BASE / 'examples'
STATIC = Path(__file__).resolve().parent / 'static'
RUNS = Path(os.environ.get('BRACE_RUNS_DIR', str(BASE/'runs'))).resolve()
MAX_FILE = 25 * 1024 * 1024
LOCAL_PORT = local_port()
ALLOWED_EXPORTS = {
    'HTML_PRESENTATION.json',
    'confusion_matrix.csv','analysis_methods.json','compatibility_summary.json','warning_exclusion_records.json','consistency_audit.json','CSV_TEXT_ENCODING.json','REPRODUCE.md','PRIVACY.md','race_config.json',
    'validation_result.json','shift_result.json','run_report.html','gene_shifts.csv',
    'pca_samples.csv','per_class.csv','error_cases.csv','sample_level.csv','threshold_curve.csv',
    'confidence_bins.csv','study_summary.csv','error_shift_samples.csv','error_shift_quartiles.csv',
    'target_scored_predictions.csv','target_predictions_unlabeled.csv','source_oof_predictions.csv',
    'frozen_model.json','run_result.json','FILE_SHA256_MANIFEST.csv','research_summary.html','reproducibility_manifest.json'
}

app = FastAPI(title='BRACE Research Workbench', version='1.0.0', docs_url=None, redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1','localhost','testserver'])

@app.middleware('http')
async def reject_foreign_write_origins(request, call_next):
    # A local app should not accept scripted cross-site writes initiated from arbitrary websites.
    if request.method not in ('GET','HEAD','OPTIONS'):
        origin=request.headers.get('origin')
        if origin and origin not in (f'http://127.0.0.1:{LOCAL_PORT}',f'http://localhost:{LOCAL_PORT}',
                                      'http://testserver'):
            return PlainTextResponse('Cross-origin writes are not supported',status_code=403)
    return await call_next(request)
app.mount('/assets', StaticFiles(directory=STATIC), name='assets')


@app.get('/')
def index():
    return FileResponse(STATIC/'index.html', media_type='text/html', headers={'Cache-Control':'no-store'})


@app.get('/api/templates')
def templates():
    path=BASE/'templates'/'BRACE_INPUT_EXAMPLES.zip'
    return FileResponse(path,filename=path.name,media_type='application/zip')


@app.get('/api/health')
def health():
    from brace_app.study_api import public_paths
    try:
        public_paths()
        public_available=True
    except HTTPException:
        public_available=False
    return {'status':'ok','version':'1.0.0','scope':'research_only','network':'localhost_only',
            'geo_expression_data_available':public_available,
            'note':'Approved public ER example is a saved exploratory computation; CPTAC predictions remain archived historical evidence.'}


def read_json(p:Path):
    return json.loads(p.read_text(encoding='utf-8'))


def csv_rows(path):
    with path.open(newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def mini_validation(raw):
    a=raw['analysis'] if 'analysis' in raw else raw
    return {'origin':a.get('origin'), 'role':a.get('evaluation_role'), 'independence':a.get('independence_declaration'),
            'n':a.get('n'), 'classes':a.get('class_order'), 'metrics':a.get('metrics'),
            'threshold':a.get('fixed_threshold'), 'threshold_curve':a.get('threshold_curve',[]),
            'calibration_bins':a.get('confidence_bins',[]), 'study_summaries':a.get('study_summaries',[]),
            'records':a.get('records',[]), 'errors':a.get('errors',[]),'warnings':a.get('warnings',[]),
            'interpretation':a.get('interpretation','')}


def mini_shift(raw):
    return {'origin':raw.get('result_origin'), 'mode':raw.get('mode'),
            'compatibility':raw.get('compatibility'),
            'feature_coverage':raw.get('feature_coverage'), 'pca':raw.get('pca'),
            'gene_shifts':raw.get('gene_shifts',[]), 'label_based_exploratory':raw.get('label_based_exploratory'),
            'error_association':raw.get('error_association'), 'warnings':raw.get('warnings',[]),
            'provenance':raw.get('provenance'), 'interpretation':raw.get('interpretation','')}


@app.get('/api/example/cptac')
def cptac():
    raw=read_json(EXAMPLES/'stage06_cptac_report'/'validation_result.json')
    return {'id':'historical_cptac','kind':'historical','name':'CancerShift · CPTAC-GDC',
            'data_label':'Real archived research predictions · not new inference',
            'validation':mini_validation(raw), 'shift':None,
            'provenance':raw.get('provenance'),
            'notes':['Historical one-shot evaluation; independent acquisition has not been authenticated here.',
                     'Study/class confounding and absent true classes limit generalization claims.']}


@app.get('/api/example/historical-shift')
def historical_shift():
    root=EXAMPLES/'stage07_historical_cancershift'
    return {'kind':'historical','name':'CancerShift · GSE2109 exploratory adaptation',
            'methods':csv_rows(root/'historical_adaptation_comparison.csv'),
            'provenance':read_json(root/'HISTORICAL_PROVENANCE.json'),
            'note':'Historical values copied from preserved research evidence; not fresh adaptation runs.'}


@app.get('/api/example/synthetic')
def synthetic_preview():
    shift=read_json(EXAMPLES/'stage07_synthetic_shift'/'shift_result.json')
    return {'id':'synthetic_preview','kind':'synthetic','name':'Synthetic cohort demonstration',
            'data_label':'Artificial measurements for software verification; not patient findings',
            'validation':None,'shift':mini_shift(shift),'provenance':shift.get('provenance')}


def safe_run_dir(run_id):
    if len(run_id)!=32 or not all(c in '0123456789abcdef' for c in run_id):
        raise HTTPException(404,'Run not found')
    root=RUNS/run_id
    if not root.is_dir():raise HTTPException(404,'Run not found')
    from brace_app.export_safety import within
    try:return within(RUNS,root)
    except ValueError as exc:raise HTTPException(404,'Run not found') from exc


def run_response(root):
    if (root/'race'/'race_result.json').is_file():
        return race_response(root)
    val_path=root/'validation'/'validation_result.json'
    shift_path=root/'shift'/'shift_result.json'
    v=mini_validation(read_json(val_path)) if val_path.is_file() else None
    s=mini_shift(read_json(shift_path)) if shift_path.is_file() else None
    config=read_json(root/'run.json')
    finalize_run(root)
    from brace_app.embrace import REPORT_FILES
    exports=[{'section':'report','filename':name,'bytes':(root/name).stat().st_size} for name in sorted(REPORT_FILES|{'reproducibility_manifest.json'}) if (root/name).is_file()]
    for group in ('validation','shift','model'):
        target=root/('validation/stage05' if group=='model' else group)
        if target.is_dir():
            exports += [{'section':group,'filename':p.name,'bytes':p.stat().st_size}
                        for p in sorted(target.iterdir()) if p.is_file() and p.name in ALLOWED_EXPORTS]
    if not v and not s:
        raise HTTPException(500,'Run has no scientific results')
    return {'id':config['id'], 'kind':config.get('kind','user_computed'),'name':config['name'],
            'data_label':config.get('data_label','Computed from user-supplied files; provenance declarations are not independently authenticated'),
            'mode':config['mode'], 'validation':v, 'shift':s,
            'exports':exports, 'notes':config['notes'], 'provenance':config['input_hashes']}


@app.get('/api/runs/{run_id}')
def get_run(run_id:str):
    root=safe_run_dir(run_id)
    try:return run_response(root)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        raise HTTPException(409,{'code':'EVIDENCE_MISMATCH','message':'Saved run evidence is missing or changed. Restore matching files and retry. '+str(exc)}) from exc


@app.get('/api/runs/{run_id}/export/{group}/{filename}')
def download(run_id:str, group:str, filename:str):
    root=safe_run_dir(run_id)
    from brace_core.signature import FILES as RACE_FILES
    if group not in {'shift','validation','model','report','race'} or filename not in (ALLOWED_EXPORTS | set(RACE_FILES)):
        raise HTTPException(404,'Export unavailable')
    path=(root/filename) if group=='report' else root/('validation/stage05' if group=='model' else group)/filename
    if not path.is_file():raise HTTPException(404,'Export unavailable')
    from brace_app.embrace import exported_path
    try:path=exported_path(root,path)
    except (ValueError,OSError,KeyError,TypeError) as exc:raise HTTPException(409,{'code':'EXPORT_EVIDENCE_MISMATCH','message':str(exc)}) from exc
    return FileResponse(path,filename=filename,media_type='application/octet-stream',headers={'X-Content-Type-Options':'nosniff'})


@app.get('/api/runs/{run_id}/bundle')
def download_bundle(run_id:str):
    root=safe_run_dir(run_id)
    try:finalize_run(root)
    except (ValueError,OSError,KeyError,TypeError) as exc:raise HTTPException(409,{'code':'EXPORT_EVIDENCE_MISMATCH','message':str(exc)}) from exc
    path=root/'RESEARCH_PACKAGE.zip'
    return FileResponse(path,filename='BRACE_reproducibility_package.zip',media_type='application/zip',headers={'X-Content-Type-Options':'nosniff'})


@app.get('/api/example/bundle/cptac')
def historical_bundle():
    path=build_historical_package()
    return FileResponse(path,filename='BRACE_CancerShift_archived_evidence.zip',media_type='application/zip',headers={'X-Content-Type-Options':'nosniff'})


@app.get('/api/example/export/{kind}/{filename}')
def example_download(kind:str,filename:str):
    groups={'cptac':'stage06_cptac_report','shift':'stage07_synthetic_shift',
            'historical':'stage07_historical_cancershift'}
    historical_files={'historical_adaptation_comparison.csv','HISTORICAL_PROVENANCE.json'}
    if kind not in groups or filename not in (ALLOWED_EXPORTS|historical_files if kind=='historical' else ALLOWED_EXPORTS):raise HTTPException(404,'Export unavailable')
    path=EXAMPLES/groups[kind]/filename
    if not path.is_file():raise HTTPException(404,'Export unavailable')
    return FileResponse(path,filename=filename,media_type='application/octet-stream',headers={'X-Content-Type-Options':'nosniff'})


async def save_file(file:UploadFile|None, base:Path, field:str, types:tuple[str,...], required=True):
    if file is None:
        if required:raise HTTPException(422,{'field':field,'code':'MISSING_FILE','message':f'{field.replace("_"," ").capitalize()} is required.'})
        return None
    name=Path(file.filename or '').name
    if not name or Path(name).suffix.lower() not in types:
        raise HTTPException(422,{'field':field,'code':'UNSUPPORTED_FORMAT',
                                 'message':f'Use {", ".join(types)} for {field.replace("_"," ")}.'})
    target=base/f'{field}{Path(name).suffix.lower()}'
    data=await file.read(MAX_FILE+1)
    if len(data)>MAX_FILE:
        raise HTTPException(413,{'field':field,'code':'FILE_TOO_LARGE','message':'Maximum 25 MB per file.'})
    if not data:raise HTTPException(422,{'field':field,'code':'EMPTY_FILE','message':'The file is empty.'})
    target.write_bytes(data)
    import hashlib
    return target, {'filename':name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}


@app.post('/api/demo/synthetic')
def demo_synthetic():
    """Run the real model/shift engines on the explicitly synthetic example."""
    run_id=uuid.uuid4().hex
    root=RUNS/run_id
    root.mkdir(parents=True,exist_ok=False)
    try:
        files=[EXAMPLES/'synthetic_valid'/n for n in (
            'source_expression.csv','source_samples.csv','source_manifest.json',
            'target_expression.csv','target_samples.csv','target_manifest.json')]
        stage06_cli.train(*files,out=root/'validation')
        make_supervised_shift(files,root)
        (root/'run.json').write_text(json.dumps({'id':run_id,'name':'Synthetic · complete computed workflow',
         'mode':'train_validate','kind':'synthetic', 'data_label':'Newly computed synthetic demonstration; not biological or patient evidence',
         'notes':['Synthetic measurements; useful for demonstrating computations only.',
         'Results are NOT discoveries about cancer, genes, or people.'],'input_hashes':{p.name:{'sha256':__import__('hashlib').sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files}}))
        return run_response(root)
    except Exception:
        shutil.rmtree(root,ignore_errors=True)
        raise


def make_supervised_shift(files,root):
    """Use the already trained model's held-out target predictions for shift associations."""
    validation_dir=root/'validation'
    preds=validation_dir/'stage05'/'target_scored_predictions.csv'
    prediction_manifest=root/'generated_prediction_manifest.json'
    classes=['normal','tumor']
    prediction_manifest.write_text(json.dumps({
        'schema_version':'1.0.0','dataset_id':'BRACE_new_baseline_target','model_id':'BRACE_stage05_logistic_baseline',
        'classes':classes,'probability_columns':{c:'prob_'+c for c in classes},
        'prediction_origin':'external_model','evaluation_role':'external_exploratory',
        'independence_declaration':'unknown','primary_confidence_threshold':.95,
        'label_source_description':'Source-trained BRACE baseline, target labels for post-hoc evaluation only.'
    },indent=2))
    stage07_cli.execute(*files,out=root/'shift',mode='train_validate',
                        classes=tuple(classes),predictions=preds,prediction_manifest=prediction_manifest)


@app.post('/api/analyze')
async def analyze(
    mode: Annotated[str,Form()],
    source_expression: Annotated[UploadFile|None,File()] = None,
    source_metadata: Annotated[UploadFile|None,File()] = None,
    source_manifest: Annotated[UploadFile|None,File()] = None,
    target_expression: Annotated[UploadFile|None,File()] = None,
    target_metadata: Annotated[UploadFile|None,File()] = None,
    target_manifest: Annotated[UploadFile|None,File()] = None,
    predictions: Annotated[UploadFile|None,File()] = None,
    prediction_manifest: Annotated[UploadFile|None,File()] = None,
):
    if mode not in {'evaluate_predictions','train_validate','diagnose_shift'}:
        raise HTTPException(422,{'code':'INVALID_MODE','message':'Choose a supported analysis mode.'})
    run_id=uuid.uuid4().hex
    root=RUNS/run_id
    raw=root/'input'
    raw.mkdir(parents=True,exist_ok=False)
    try:
        file_data={}
        pairs= [('predictions',predictions,('.csv','.tsv')),('prediction_manifest',prediction_manifest,('.json',))] if mode=='evaluate_predictions' else [
            ('source_expression',source_expression,('.csv','.tsv')),
            ('source_metadata',source_metadata,('.csv','.tsv')),
            ('source_manifest',source_manifest,('.json',)),
            ('target_expression',target_expression,('.csv','.tsv')),
            ('target_metadata',target_metadata,('.csv','.tsv')),
            ('target_manifest',target_manifest,('.json',))]
        paths={}
        for field,file,types in pairs:
            saved=await save_file(file,raw,field,types)
            paths[field]=saved[0]
            file_data[field]=saved[1]
        def compute():
            if mode=='evaluate_predictions':
                stage06_cli.evaluate_existing(paths['predictions'],paths['prediction_manifest'],root/'validation')
            else:
                cohort_args=[paths[k] for k in ('source_expression','source_metadata','source_manifest',
                                              'target_expression','target_metadata','target_manifest')]
                if mode=='diagnose_shift':
                    stage07_cli.execute(*cohort_args,out=root/'shift',mode='diagnose_shift')
                else:
                    stage06_cli.train(*cohort_args,out=root/'validation')
                    make_supervised_shift(cohort_args,root)
            config={'id':run_id,'name':'My cohort analysis' if mode!='evaluate_predictions' else 'My prediction evaluation',
                    'mode':mode,'notes':['Source and target provenance is user-declared, not independently verified.',
                                        'Research-only; no medical diagnosis or clinical certification.'],
                    'input_hashes':file_data}
            (root/'run.json').write_text(json.dumps(config,indent=2))
            return run_response(root)
        return await run_in_threadpool(compute)
    except (InputProblem,ValueError) as exc:
        shutil.rmtree(root,ignore_errors=True)
        if isinstance(exc,InputProblem):
            detail=exc.to_dict()
        else:
            detail={'code':'ANALYSIS_BLOCKED','message':str(exc),'next_action':'Review file formats and declared study metadata.'}
        raise HTTPException(422,detail) from exc
    except HTTPException:
        shutil.rmtree(root,ignore_errors=True)
        raise
    except Exception:
        shutil.rmtree(root,ignore_errors=True)
        raise

# Additive Pass 2 API. Legacy analysis modes and report generation remain intact.
def race_response(root):
    from brace_core.signature import FILES
    result=read_json(root/'race'/'race_result.json');config=read_json(root/'run.json')
    from brace_app.provenance_origin import identify_public
    public=identify_public(config['input_hashes'])
    finalize_run(root)
    return {'id':config['id'],'kind':'user_computed','name':'RACE gene replication','mode':'race',
            'input_origin':'verified_public' if public else 'user_declared',
            'data_label':'Fresh computation from byte-matched verified public ER inputs; exploratory only' if public else 'Computed from user-supplied measurements; provenance declarations are not authenticated',
            'race':result,'validation':None,'shift':None,'notes':config['notes'],
            'provenance':config['input_hashes'],
            'exports':[{'section':'race','filename':n,'bytes':(root/'race'/n).stat().st_size} for n in FILES]+[{'section':'report','filename':n,'bytes':(root/n).stat().st_size} for n in ('research_summary.html','reproducibility_manifest.json','consistency_audit.json') if (root/n).is_file()]}


@app.post('/api/race')
async def race_analyze(
    race_config: Annotated[str,Form()],
    source_expression: Annotated[UploadFile,File()],
    source_metadata: Annotated[UploadFile,File()],
    source_manifest: Annotated[UploadFile,File()],
    target_expression: Annotated[UploadFile,File()],
    target_metadata: Annotated[UploadFile,File()],
    target_manifest: Annotated[UploadFile,File()],
):
    from brace_core.signature import run, settings, RaceBlocked
    from brace_core.intake import parse_cohort
    if len(race_config.encode('utf-8'))>65536:
        raise HTTPException(413,{'code':'CONFIG_TOO_LARGE','message':'RACE settings exceed 64 KiB.'})
    try:
        def unique(pairs):
            result={}
            for key,value in pairs:
                if key in result:raise ValueError('Duplicate RACE setting')
                result[key]=value
            return result
        config=settings(json.loads(race_config,object_pairs_hook=unique))
    except (ValueError,TypeError) as exc:
        raise HTTPException(422,{'code':'RACE_CONFIG','message':str(exc)}) from exc
    run_id=uuid.uuid4().hex;root=RUNS/run_id;raw=root/'input'
    raw.mkdir(parents=True,exist_ok=False)
    try:
        uploads={'source_expression':source_expression,'source_metadata':source_metadata,'source_manifest':source_manifest,
                 'target_expression':target_expression,'target_metadata':target_metadata,'target_manifest':target_manifest}
        paths={};hashes={}
        for name,file in uploads.items():
            paths[name],hashes[name]=await save_file(file,raw,name,('.json',) if name.endswith('manifest') else ('.csv','.tsv'))
        def compute():
            cohorts=[parse_cohort(paths[r+'_expression'],paths[r+'_metadata'],paths[r+'_manifest'],r) for r in ('source','target')]
            run(*cohorts,config,root/'race')
            from brace_app.provenance_origin import identify_public,public_preparation
            (root/'run.json').write_text(json.dumps({'id':run_id,'mode':'race','input_hashes':hashes,'input_origin':'user_declared',**public_preparation(hashes),
                'notes':['Exploratory unpaired gene association; no clinical, causal or locked-validation claim.']}),encoding='utf-8')
            return race_response(root)
        return await run_in_threadpool(compute)
    except (RaceBlocked,InputProblem,ValueError) as exc:
        shutil.rmtree(root,ignore_errors=True)
        detail={'code':'RACE_BLOCKED','status':'blocked','eligible':False,'message':str(exc)}
        if isinstance(exc,RaceBlocked):detail['issues']=[i.to_dict() for i in exc.issues]
        if isinstance(exc,InputProblem):detail['issues']=[exc.to_dict()]
        raise HTTPException(422,detail) from exc
    except Exception:
        shutil.rmtree(root,ignore_errors=True)
        raise

from brace_app.study_api import router as study_router
app.include_router(study_router)

from brace_app.molecular_api import router as molecular_router
app.include_router(molecular_router)

from brace_app.evidence_api import router as evidence_router
app.include_router(evidence_router)

from brace_app.embrace import router as embrace_router
app.include_router(embrace_router)

# Read-only workspace integration.
from brace_app.workspace_api import router as workspace_router
app.include_router(workspace_router)

from brace_app.discovery import router as discovery_router
app.include_router(discovery_router)
