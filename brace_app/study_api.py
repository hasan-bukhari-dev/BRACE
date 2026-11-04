from starlette.concurrency import run_in_threadpool
"""Read-only approved example and non-computational study preflight for Pass 3."""
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from brace_core.intake import parse_cohort, InputProblem
from brace_core.compatibility import evaluate_compatibility
from brace_core.signature import settings, eligibility, RaceBlocked, FILES
from brace_core.contracts import cohort_summary
from brace_core.prediction_io import load_predictions

router=APIRouter()

def public_paths():
    from brace_app import server
    base=server.BASE
    try:
        records=json.loads((base/'docs/PASS03_PUBLIC_REFERENCE.json').read_text())
    except (OSError,ValueError) as exc:
        raise HTTPException(503,{'message':'The public-example verification record is unavailable. Restore the checkpoint and retry.'}) from exc
    for name,record in records.items():
        path=base/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
            raise HTTPException(503,{'message':'The approved public example is missing or changed. Restore the checkpoint files and retry.'})
    return base/'examples/public_er_pair'

@router.get('/api/example/public-er')
def public_example():
    root=public_paths();result=json.loads((root/'race_final/race_result.json').read_text())
    result.pop('source_screen',None)
    methods=json.loads((root/'race_final/race_methods.json').read_text())
    return dict(id='public_er_pass2',kind='public_computed',mode='race',name='Breast tumor · ER association',
        data_label='Public GEO measurements · saved exploratory computation, not a new run',race=result,
        validation=None,shift=None,provenance=methods['input_files'],
        cohorts={r:{'cohort_id':methods[r+'_manifest']['cohort_id'],**result['counts'][r]} for r in ('source','target')},
        notes=['GSE42568 source → GSE20711 target. ER-positive versus ER-negative tumors.',
               'Exploratory only: GC-RMA versus RMA, different ER assays and incompletely authenticated donor independence.',
               'Normal tissue excluded. This example does not establish model-transfer eligibility.'],
        exports=[dict(section='race',filename=n,url='/api/example/public-er/export/'+n) for n in FILES])

@router.get('/api/example/public-er/export/{filename}')
def public_export(filename:str):
    if filename not in FILES:raise HTTPException(404,'Export unavailable')
    root=public_paths()
    return FileResponse(root/'race_final'/filename,filename=filename,headers={'X-Content-Type-Options':'nosniff'})

PUBLIC_INPUT_FILES = {
    role+'_'+kind+suffix
    for role in ('source','target')
    for kind,suffix in (('expression','.tsv'),('metadata','.tsv'),('manifest','.json'))
}

@router.get('/api/example/public-er/input/{filename}')
def public_input(filename:str):
    """Only the approved, hash-checked built-in public inputs; never user uploads."""
    if filename not in PUBLIC_INPUT_FILES | {'race_config.json'}:
        raise HTTPException(404,'Public input unavailable')
    root=public_paths()
    path=root/'race_config.json' if filename=='race_config.json' else root/'prepared'/filename
    if filename=='race_config.json' and (not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!='bc19b3c080bce6355e608af805464fadfd98579f5658b288cbe3091977639896'):
        raise HTTPException(503,'The recorded public contrast is missing or changed. Restore the release file and retry.')
    return FileResponse(path,filename=filename,headers={'X-Content-Type-Options':'nosniff'})

@router.post('/api/preflight')
async def preflight(
    mode:Annotated[str,Form()],race_config:Annotated[str,Form()]='{}',
    name:Annotated[str,Form()]='',schema_version:Annotated[str,Form()]='1.0.0',
    source_expression:Annotated[UploadFile|None,File()]=None,source_metadata:Annotated[UploadFile|None,File()]=None,
    source_manifest:Annotated[UploadFile|None,File()]=None,target_expression:Annotated[UploadFile|None,File()]=None,
    target_metadata:Annotated[UploadFile|None,File()]=None,target_manifest:Annotated[UploadFile|None,File()]=None,
    predictions:Annotated[UploadFile|None,File()]=None,prediction_manifest:Annotated[UploadFile|None,File()]=None,
):
    from brace_app import server
    from brace_app.persistence import require_schema,study_name
    require_schema(schema_version)
    try:title=study_name(name,'My prediction evaluation' if mode=='evaluate_predictions' else 'My cohort analysis')
    except ValueError as exc:raise HTTPException(422,{'code':'INVALID_STUDY','message':str(exc)}) from exc
    if mode not in ('race','evaluate_predictions','train_validate','diagnose_shift'):raise HTTPException(422,'Unsupported task')
    if len(race_config.encode())>65536:raise HTTPException(413,'Settings exceed 64 KiB')
    uploads={'source_expression':source_expression,'source_metadata':source_metadata,'source_manifest':source_manifest,
        'target_expression':target_expression,'target_metadata':target_metadata,'target_manifest':target_manifest} if mode!='evaluate_predictions' else {'predictions':predictions,'prediction_manifest':prediction_manifest}
    try:
        with tempfile.TemporaryDirectory(prefix='brace-preflight-') as directory:
            paths={}
            for name,file in uploads.items():
                paths[name],_=await server.save_file(file,Path(directory),name,('.json',) if name.endswith('manifest') else ('.csv','.tsv'))
            def inspect():
                if mode=='evaluate_predictions':
                    p=load_predictions(paths['predictions'],paths['prediction_manifest'])
                    return dict(eligible=True,status='ready',mode=mode,preview={'prediction_rows':len(p.sample_ids),'classes':p.classes},issues=[i.to_dict() for i in p.issues],note='Input checks only. No metrics or model fitting executed.')
                source,target=[parse_cohort(paths[r+'_expression'],paths[r+'_metadata'],paths[r+'_manifest'],r) for r in ('source','target')]
                if mode=='race':
                    try:issues=eligibility(source,target,settings(json.loads(race_config)));eligible=True
                    except RaceBlocked as exc:issues=exc.issues;eligible=False
                else:
                    comp=evaluate_compatibility(source,target,mode,scientific_role='unlabeled_shift_only' if mode=='diagnose_shift' else 'external_exploratory')
                    issues=comp.issues;eligible=comp.eligible
                summaries={r:cohort_summary(c) for r,c in [('source',source),('target',target)]}
                if mode=='diagnose_shift':
                    for summary in summaries.values():summary.pop('observed_conditions',None)
                # Use existing compatibility functions; no new numerical rule.
                checks={mode:dict(status='eligible_with_caveats' if eligible and issues else 'eligible' if eligible else 'blocked',issues=[i.to_dict() for i in issues])}
                for candidate in ('train_validate','diagnose_shift'):
                    if candidate==mode:continue
                    if mode=='diagnose_shift' and candidate=='train_validate':
                        checks[candidate]=dict(status='not_checked',reason='Labels are not inspected by this unlabeled task.');continue
                    other=evaluate_compatibility(source,target,candidate,scientific_role='unlabeled_shift_only' if candidate=='diagnose_shift' else 'external_exploratory')
                    checks[candidate]=dict(status='eligible_with_caveats' if other.eligible and other.issues else 'eligible' if other.eligible else 'blocked',issues=[i.to_dict() for i in other.issues])
                if mode!='race':checks['race']=dict(status='not_checked',reason='Gene testing requires explicit biological contrast definitions and its own eligibility check.')
                return dict(eligible=eligible,status='ready_with_warnings' if eligible and issues else 'ready' if eligible else 'blocked',mode=mode,
                    preview=summaries,issues=[i.to_dict() for i in issues],task_eligibility=checks,note='Input and task checks only; no model fitting or gene association tests executed. A parser verdict does not authenticate acquisition or directly comparable scales.')
            result=await run_in_threadpool(inspect)
            return {**result,'schema_version':schema_version,'name':title}
    except RaceBlocked as exc:
        return dict(eligible=False,status='blocked',mode=mode,issues=[i.to_dict() for i in exc.issues])
    except (InputProblem,ValueError) as exc:
        return dict(eligible=False,status='blocked',mode=mode,issues=[exc.to_dict()] if isinstance(exc,InputProblem) else [{'severity':'block','code':'INVALID_SETTINGS','message':str(exc),'next_action':'Review the declared conditions and metadata.'}])
