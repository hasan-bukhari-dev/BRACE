"""Read-only ACE summaries and contextual TRACE, composed from checked artifacts.

No fitting, inference, statistical testing, threshold optimization or provenance
authentication is performed by these endpoints.
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from brace_app.molecular_api import obj, sha, context as race_context
from brace_core.baseline05 import canonical_sha
from brace_core.signature import FILES

router=APIRouter()

def ace_context(study_id):
    from brace_app import server
    try:
        historical=study_id=='historical_cptac'
        if historical:
            pins=obj(server.BASE/'docs/PASS05_ARCHIVED_REFERENCE.json')
            for name,record in pins.items():
                path=server.BASE/name
                if sha(path)!=record['sha256']:raise ValueError('Archived evidence changed: '+name)
            root=server.EXAMPLES/'stage06_cptac_report'
            raw=obj(root/'validation_result.json');analysis=raw['analysis']
            config=dict(id=study_id,mode='evaluate_predictions',kind='historical',name='CancerShift · CPTAC-GDC')
            inputs=raw['provenance'];manifest=None;shift=None;stage=None;model=None
            artifacts=[dict(path=p.name,sha256=sha(p),bytes=p.stat().st_size,
                url='/api/example/export/cptac/'+p.name) for p in sorted(root.iterdir()) if p.is_file() and p.name in server.ALLOWED_EXPORTS]
        else:
            root=server.safe_run_dir(study_id);config=obj(root/'run.json');manifest=obj(root/'reproducibility_manifest.json')
            if config['id']!=study_id or manifest['run_id']!=study_id or config['mode']!=manifest['mode']:raise ValueError('Run identity mismatch')
            if config['mode'] not in ('evaluate_predictions','train_validate','diagnose_shift'):raise HTTPException(404,'No ACE evidence for this run')
            artifacts=[]
            for name,record in manifest['artifact_sha256'].items():
                path=Path(name)
                group=path.parent.as_posix()
                if group not in ('validation','validation/stage05','shift','.') or path.name not in server.ALLOWED_EXPORTS or path.is_absolute() or '..' in path.parts:
                    raise ValueError('Unexpected artifact path')
                p=root/path
                if p.is_symlink() or sha(p)!=record['sha256'] or p.stat().st_size!=record['bytes']:raise ValueError('Scientific artifact hash mismatch: '+name)
                section='model' if group=='validation/stage05' else 'report' if group=='.' else group
                published=manifest.get('published_artifact_sha256',{}).get(name,record)
                artifacts.append(dict(path=name,**published,scientific_source_sha256=record['sha256'],url=f'/api/runs/{study_id}/export/{section}/{path.name}'))
            required={'shift/shift_result.json'} if config['mode']=='diagnose_shift' else {'validation/validation_result.json'}
            if config['mode']=='train_validate':required|={'validation/stage05/run_result.json','validation/stage05/frozen_model.json','validation/stage05/source_oof_predictions.csv'}
            if not required.issubset(manifest['artifact_sha256']):raise ValueError('Required scientific evidence not inventoried')
            inputs=config['input_hashes']
            for field,record in inputs.items():
                if config.get('kind')=='synthetic':
                    if field not in {'source_expression.csv','source_samples.csv','source_manifest.json','target_expression.csv','target_samples.csv','target_manifest.json'}:raise ValueError('Unexpected demonstration input')
                    p=server.EXAMPLES/'synthetic_valid'/field
                else:
                    if field not in {'source_expression','source_metadata','source_manifest','target_expression','target_metadata','target_manifest','predictions','prediction_manifest'}:raise ValueError('Unexpected saved input field')
                    choices=[root/'input'/(field+ext) for ext in (('.json',) if field.endswith('manifest') else ('.csv','.tsv'))]
                    found=[p for p in choices if p.is_file()]
                    if len(found)!=1:raise ValueError('Saved input missing or ambiguous: '+field)
                    p=found[0]
                if sha(p)!=record['sha256']:raise ValueError('Input hash mismatch: '+field)
            raw=obj(root/'validation/validation_result.json') if config['mode']!='diagnose_shift' else None
            analysis=raw['analysis'] if raw else None
            shift=obj(root/'shift/shift_result.json') if (root/'shift/shift_result.json').is_file() else None
            stage=obj(root/'validation/stage05/run_result.json') if config['mode']=='train_validate' else None
            model=obj(root/'validation/stage05/frozen_model.json') if stage else None
            if model:
                if canonical_sha({k:v for k,v in model.items() if k!='model_sha256'})!=model['model_sha256'] or stage['freeze']['frozen_model_sha256']!=model['model_sha256'] or canonical_sha(model['config'])!=model['config_sha256']:
                    raise ValueError('Frozen model/method identity mismatch')
            if config['mode']=='diagnose_shift' and (analysis is not None or shift.get('label_based_exploratory') is not None or shift.get('error_association') is not None):raise ValueError('Shift-only evidence contains label-conditioned results')
        return dict(root=root,config=config,analysis=analysis,raw=raw,shift=shift,stage=stage,model=model,
                    inputs=inputs,manifest=manifest,artifacts=artifacts,historical=historical)
    except HTTPException:raise
    except (OSError,ValueError,KeyError,TypeError) as exc:
        raise HTTPException(409,dict(code='TRACE_EVIDENCE_UNAVAILABLE',message='Saved evidence cannot be verified: '+str(exc)+'. Restore the matching checkpoint or run files and retry.')) from exc

def selected_sample(c,sample_id):
    if sample_id is None:return None
    a=c['analysis']
    record=next((r for r in (a or {}).get('records',[]) if r['sample_id']==sample_id),None)
    if record is None:raise HTTPException(404,'Sample not in this evaluated run')
    related=None
    shift=c['shift'] or {}
    rows=(shift.get('error_association') or {}).get('samples',[])
    match=next((r for r in rows if r['sample_id']==sample_id),None)
    if match:
        if any(match[k]!=record[k] for k in ('true_label','predicted_label','correct')):raise HTTPException(409,'Shift association and prediction row disagree')
        point=next((p for p in shift.get('pca',{}).get('samples',[]) if p['sample_id']==sample_id and p['cohort']=='target'),None)
        related=dict(association=match,pca_point=point,note='Same checked run and target sample. Descriptive shift does not establish a cause of this error.')
    return dict(record=record,related_shift=related,
                provenance_note='Saved prediction row from this run only. No linkage to unrelated RACE expression cohorts.')

@router.get('/api/ace/studies/{study_id}')
def ace(study_id:str,sample_id:str|None=None):
    from brace_app import server
    c=ace_context(study_id);a=c['analysis'];stage=c['stage'];model=c['model']
    return dict(study_id=study_id,kind=c['config'].get('kind','user_computed'),mode=c['config']['mode'],
        validation=server.mini_validation(c['raw']) if a else None,
        source_cv=dict(role='source_cv',metrics=stage['outputs']['source_cv'],method=stage['outputs']['source_cv_method'],
            folds=model['config']['cv_folds'],seed=model['config']['seed'],
            interval_note='Source OOF Wilson/bootstrap intervals were not calculated in the saved Stage 05 artifact.') if stage else None,
        source_target_comparison='Source out-of-fold estimates and target scoring use different samples and evaluation designs; no paired performance difference or universal generalization score is calculated.' if stage else 'Source CV is not recorded for these imported/archived predictions; a source–target performance comparison is unavailable.',
        frozen_model_hash=model['model_sha256'] if model else None,
        expected_calibration_error_10bin=a.get('expected_calibration_error_10bin') if a else None,
        selection=selected_sample(c,sample_id),artifacts=c['artifacts'],
        scientific_role=a['evaluation_role'] if a else 'unlabeled_shift_only',
        methods=dict(version=a.get('method_version'),interpretation=a.get('interpretation')) if a else None,
        provenance_authenticated=False)

def step(key,title,status,data,artifacts):return dict(key=key,title=title,status=status,data=data,artifacts=artifacts)

@router.get('/api/trace/studies/{study_id}')
def trace(study_id:str,feature_id:str|None=None,sample_id:str|None=None):
    from brace_app import server
    from brace_app.dataset_registry import valid_id
    if valid_id(study_id):
        root=server.safe_run_dir(study_id)
        config=obj(root/'run.json')
        if config.get('mode')=='replay_frozen':
            from brace_app.frozen_workflow import trace as replay_trace
            server.run_response(root)
            if feature_id is not None or sample_id is not None:raise HTTPException(422,'Frozen replay exposes the complete prediction trace; select its run-level record.')
            return replay_trace(root)
    if feature_id is not None:
        if sample_id is not None:raise HTTPException(422,'Choose a gene or sample, not both')
        result,methods,frozen,cohorts,annotations,preparation=race_context(study_id)
        gene=next((r for r in result['genes'] if r['feature_id']==feature_id),None)
        if gene is None:raise HTTPException(404,'Feature not in this frozen signature')
        source=next(r for r in frozen['selected'] if r['feature_id']==feature_id)
        base=server.BASE/'examples/public_er_pair/race_final' if study_id=='public_er_pass2' else server.safe_run_dir(study_id)/'race'
        artifacts=[dict(path=name,sha256=sha(base/name),bytes=(base/name).stat().st_size,
            url='/api/example/public-er/export/'+name if study_id=='public_er_pass2' else f'/api/runs/{study_id}/export/race/{name}') for name in FILES]
        def links(*names):return [a for a in artifacts if a['path'] in names]
        steps=[
            step('inputs','Input cohorts','recorded',dict(input_files=methods['input_files'],source=methods['source_manifest'],target=methods['target_manifest'],dataset_provenance=config.get('dataset_provenance',{}) if valid_id(study_id) else {},provenance_authenticated=False),links('race_methods.json')),
            step('compatibility','Compatibility','recorded',dict(eligible=result['eligible'],evaluation_role=result['evaluation_role'],warnings=result['warnings'],counts=result['counts'],note='Saved eligibility and warnings, not a new compatibility run or authenticated acquisition.'),links('race_result.json')),
            step('screen','Source screening','computed',dict(family_size=methods['source_family_size'],rule=frozen['selection_rule'],selected_gene_source_record=source,test=methods['test'],multiplicity=methods['multiplicity']),links('source_gene_screen.csv')),
            step('freeze','Frozen signature','recorded',dict(hypothesis_hash=frozen['hypothesis_hash'],selected_feature_ids=[r['feature_id'] for r in frozen['selected']],frozen_before_target_tests=True),links('selected_signature.json')),
            step('target','Target tests','computed',dict(family_size=methods['target_family_size'],selected_gene_target_record=gene,test=methods['test'],effect=methods['effect'],standardized=methods['standardized'],ci=methods['ci'],multiplicity=methods['multiplicity'],undefined_tests=methods['undefined_tests']),links('replication_genes.csv','race_methods.json')),
            step('result','Gene result','recorded',dict(feature_id=feature_id,classification=gene['classification'],hypothesis_hash=result['hypothesis_hash']),links('race_result.json'))]
        return dict(study_id=study_id,analysis='race',selection=dict(feature_id=feature_id),evaluation_role=result['evaluation_role'],
            hypothesis_hash=frozen['hypothesis_hash'],steps=steps,warnings=result['warnings'],software=methods['software'],artifacts=artifacts,provenance_authenticated=False)
    c=ace_context(study_id);a=c['analysis'];stage=c['stage'];model=c['model'];selected=selected_sample(c,sample_id)
    artifacts=c['artifacts']
    def links(*names):return [r for r in artifacts if r['path'] in names]
    if c['historical']:
        validation_links=[r for r in artifacts if r['path']=='validation_result.json']
        prediction_links=[r for r in artifacts if r['path']=='sample_level.csv']
    else:
        validation_links=links('validation/validation_result.json');prediction_links=links('validation/sample_level.csv','validation/stage05/target_scored_predictions.csv')
    input_data=dict(files=c['inputs'],dataset_provenance=c['config'].get('dataset_provenance',{}),provenance_authenticated=False)
    if c['config']['mode']=='diagnose_shift':
        shift=c['shift']
        steps=[step('inputs','Input cohorts','recorded',input_data,[]),
            step('compatibility','Unlabeled compatibility','recorded',shift['compatibility'],links('shift/shift_result.json')),
            step('projection','Source-fitted projection and feature shift','computed',dict(pca={k:v for k,v in shift['pca'].items() if k!='samples'},feature_coverage=shift['feature_coverage'],note='Outcome labels excluded by the Mode C contract.'),links('shift/pca_samples.csv','shift/gene_shifts.csv')),
            step('result','Unlabeled result','recorded',dict(note='No model training, target scoring, accuracy, target class counts or outcome-conditioned findings were produced.'),links('shift/shift_result.json'))]
        warnings=shift['warnings'];role='unlabeled_shift_only'
    else:
        steps=[step('inputs','Input cohorts / predictions','recorded',input_data,validation_links),
            step('folds','Source preprocessing and folds','computed' if model else 'not_performed',
                dict(config=model['config'],source_cv=stage['outputs']['source_cv'],note='Each fold fits variance filtering, scaling and model using its training partition only.') if model else dict(note='BRACE did not perform source training or cross-validation for these imported prediction records. Original training is unavailable or declared only.'),links('validation/stage05/source_oof_predictions.csv','validation/stage05/run_result.json')),
            step('model','Frozen model / supplied predictions','recorded' if model else 'declared',
                dict(model_sha256=model['model_sha256'],config_sha256=model['config_sha256'],features_aligned=len(model['feature_ids']),features_retained=len(model['variance_support_indices']),feature_preview=[model['feature_ids'][i] for i in model['variance_support_indices'][:20]],full_feature_contract='See linked frozen_model.json',freeze=stage['freeze']) if model else dict(prediction_origin=a['origin'],note='Saved scores were supplied. BRACE does not possess or execute the original classifier, or authenticate its training history.'),links('validation/stage05/frozen_model.json') if model else prediction_links),
            step('scoring','Target scoring','computed' if model else 'not_performed',dict(evaluation_role=a['evaluation_role'],n=a['n'],note='Frozen source parameters generated target predictions before label scoring.' if model else 'No new inference: BRACE evaluated supplied saved predictions against their supplied labels.'),prediction_links),
            step('metrics','Metrics and uncertainty','computed',dict(method_version=a['method_version'],classes=a['class_order'],metrics=a['metrics'],fixed_threshold=a['fixed_threshold'],frozen_threshold_result=a['frozen_threshold_result'],interpretation=a['interpretation']),validation_links),
            step('result','Selected sample result' if selected else 'Evaluation result','recorded',selected or dict(n=a['n'],note='Select a prediction row in ACE to trace a specific sample.'),prediction_links)]
        warnings=a['warnings'];role=a['evaluation_role']
    return dict(study_id=study_id,analysis='ace',kind=c['config'].get('kind','user_computed'),mode=c['config']['mode'],
        selection=dict(sample_id=sample_id) if selected else None,evaluation_role=role,steps=steps,
        warnings=warnings,artifacts=artifacts,provenance_authenticated=False,
        software=c['manifest'].get('software_versions') if c['manifest'] else dict(note='Historical evidence: runtime versions of the original classifier are not authenticated by this trace.'))
