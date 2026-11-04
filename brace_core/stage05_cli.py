"""Stage 05 runnable CLI: supplied predictions OR fresh source-only baseline."""
from __future__ import annotations
import argparse,csv,json,hashlib,sys,html
from pathlib import Path
from .intake import parse_cohort,InputProblem
from .compatibility import evaluate_compatibility
from .prediction_io import load_predictions
from .metrics05 import evaluate_labels
from .baseline05 import train_baseline,predict_frozen,canonical_sha,SOFTWARE,SCIENCE


def write_json(path,obj):
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def write_rows(path,columns,rows):
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(columns);w.writerows(rows)

def report_html(path,result):
    st=result['status'];x=result.get('outputs',{})
    content=['<!doctype html><html lang="en"><meta charset="utf-8"><title>BRACE Stage 05</title>',
      '<style>body{font:16px/1.5 system-ui;background:#0e1726;color:#ecf3fa;max-width:920px;margin:auto;padding:38px}pre{background:#17283f;padding:20px;white-space:pre-wrap;overflow:auto;border-radius:9px}h1{margin:0}p{color:#aabbd0}</style>',
      '<h1>BRACE · Model integration</h1>',f'<p>Mode: {html.escape(result["mode"])} · Status: {html.escape(st)} · Research only</p>',
      '<p>Source-only training and model replay are separate from target-label scoring. This is not a clinical diagnostic result.</p>',
      '<h2>Computed evidence</h2><pre>'+html.escape(json.dumps(x,indent=2,allow_nan=False))+'</pre>',
      '<h2>Warnings</h2><pre>'+html.escape(json.dumps(result.get('warnings',[]),indent=2))+'</pre>',
      '<h2>Integrity &amp; freeze</h2><pre>'+html.escape(json.dumps(result.get('freeze',{}),indent=2))+'</pre>',
      '</html>']
    Path(path).write_text(''.join(content),encoding='utf-8')

def _finish(root,result):
    # Files are generated in a newly created run directory only.
    write_json(root/'run_result.json',result)
    report_html(root/'run_report.html',result)
    files={}
    for p in sorted(root.iterdir()):
        if p.name=='run_result.json' or not p.is_file():continue
        files[p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
    result['files']=files
    write_json(root/'run_result.json',result)
    return result

def _prep_output(out):
    out=Path(out)
    if out.exists() and any(out.iterdir()):raise ValueError('Output directory must be new or empty: '+str(out))
    out.mkdir(parents=True,exist_ok=True)
    return out

def run_evaluate(predictions,manifest,out):
    root=_prep_output(out)
    batch=load_predictions(predictions,manifest)
    threshold=batch.manifest.get('primary_confidence_threshold',.95)
    metrics=evaluate_labels(batch.true_labels,batch.predicted_labels,batch.classes,batch.probabilities,threshold)
    conf=batch.probabilities.max(axis=1) if batch.probabilities is not None else [None]*len(batch.sample_ids)
    cols=['sample_id','study_id','true_label','predicted_label','correct','model_confidence']
    write_rows(root/'evaluated_predictions.csv',cols,[(sid,meta.get('study_id',''),yt,yp,int(yt==yp),'' if c is None else format(float(c),'.17g')) for sid,meta,yt,yp,c in zip(batch.sample_ids,batch.metadata,batch.true_labels,batch.predicted_labels,conf)])
    warnings=[issue.to_dict() for issue in batch.issues]
    if metrics['absent_true_classes']:
        warnings.append({'code':'LIMITED_CLASS_SUPPORT','severity':'warning','message':'Some declared true classes are absent; supported-class macro F1 is not a full class-universe estimate.'})
    freeze={'configuration_sha256':canonical_sha({'manifest':batch.manifest,'input_sha256':batch.files['predictions']['sha256']}),
        'primary_confidence_threshold':threshold,'label_use':'evaluation_only','evaluation_role':batch.manifest['evaluation_role'],
        'origin_attestation':'User-declared metadata, not independently verified'}
    result={'stage':'05','mode':'evaluate_predictions','result_origin':'new_computation','software_version':SOFTWARE,
      'science_version':SCIENCE,'status':'completed_with_warnings' if warnings else 'completed',
      'inputs':batch.files,'freeze':freeze,'outputs':{'metrics':metrics,'n_samples':len(batch.sample_ids)},
      'warnings':warnings,'files':{}}
    return _finish(root,result)

def run_train(source_expression,source_metadata,source_manifest,target_expression,target_metadata,target_manifest,out,classes=('normal','tumor'),positive_class='tumor',scientific_role='external_exploratory'):
    root=_prep_output(out)
    s=parse_cohort(source_expression,source_metadata,source_manifest,'source')
    t=parse_cohort(target_expression,target_metadata,target_manifest,'target')
    c=evaluate_compatibility(s,t,'train_validate',tuple(classes),scientific_role)
    if not c.eligible:
        raise InputProblem('COMPATIBILITY_BLOCKED','Stage 04 blocks supervised comparison: '+', '.join(i.code for i in c.issues if i.severity=='block'),
          'Inspect stage04 compatibility issues, correct data and rerun','preflight')
    z=train_baseline(c,tuple(classes),positive_class)
    write_json(root/'frozen_model.json',z['frozen_model'])
    order=list(classes)
    def make_preds(ids,ys,yp,prob):
        return [(sid,yt,pr,*[format(float(n),'.17g') for n in row]) for sid,yt,pr,row in zip(ids,ys,yp,prob)]
    cols=['sample_id','true_label','predicted_label',*['prob_'+str(x) for x in classes]]
    write_rows(root/'source_oof_predictions.csv',['fold',*cols],[(f,*r) for f,r in zip(z['oof_fold'],make_preds(z['source_ids'],z['oof_true'],z['oof_pred'],z['oof_prob']))])
    write_rows(root/'target_scored_predictions.csv',cols,make_preds(z['target_ids'],z['target_true'],z['target_pred'],z['target_prob']))
    write_rows(root/'target_predictions_unlabeled.csv',['sample_id','predicted_label',*cols[3:]],
      [(sid,pr,*[format(float(n),'.17g') for n in row]) for sid,pr,row in zip(z['target_ids'],z['target_pred'],z['target_prob'])])
    issues=z['warnings']
    if z['target_metrics']['absent_true_classes']:
        issues.append({'code':'LIMITED_CLASS_SUPPORT','severity':'warning','message':'Target lacks at least one true class; cannot establish full two-class generalization.'})
    freeze={'configuration_sha256':canonical_sha(z['config']),
            'frozen_model_sha256':z['frozen_model']['model_sha256'],
            'target_labels_used_for_model_selection':False,
            'primary_confidence_threshold':.95,'scientific_role':scientific_role,
            'source_cv_folds':z['config']['cv_folds'],'target_feature_presence_consulted':True,
            'target_expression_used_for_fitting':False,'target_labels_used_for_fitting':False}
    result={'stage':'05','mode':'train_validate','result_origin':'new_computation','software_version':SOFTWARE,
       'science_version':SCIENCE,'status':'completed_with_warnings' if issues else 'completed',
       'inputs':{'source':s.input_files,'target':t.input_files},'freeze':freeze,
       'outputs':{'source_cv':z['source_metrics'],'external':z['target_metrics'],'n_features_aligned':len(c.shared_features),
          'n_features_after_source_variance_filter':len(z['frozen_model']['variance_support_indices']),
          'classes':order,'source_cv_method':z['config']['cv_method']},
       'warnings':issues,'files':{}}
    return _finish(root,result)

def run_replay(model_path,target_expression,target_metadata,target_manifest,out):
    """Reapply frozen source parameters to a compatible target, no model deserialization."""
    root=_prep_output(out)
    model_path=Path(model_path)
    try:model=json.loads(model_path.read_text('utf-8-sig'))
    except (ValueError,UnicodeError) as ex:raise InputProblem('MODEL_FREEZE_INVALID',f'Invalid JSON model freeze: {ex}','Use a BRACE frozen_model.json','model') from ex
    if not isinstance(model,dict) or 'config' not in model:
        raise InputProblem('MODEL_FREEZE_INVALID','Incomplete frozen-model document','Use an original verified BRACE freeze','model')
    tgt=parse_cohort(target_expression,target_metadata,target_manifest,'target')
    c=model['config'];manifest=tgt.manifest
    if c.get('feature_namespace')!=manifest['feature_namespace'] or c.get('measurement_type')!=manifest['measurement_type']:
        raise InputProblem('MEASUREMENT_INCOMPATIBLE','Target feature namespace or measurement type differs from frozen source','Use the documented source-compatible format','target_manifest')
    if c.get('measurement_type')=='microarray_log2_normalized' and c.get('source_platform')!=manifest.get('platform'):
        raise InputProblem('PLATFORM_DIFFERENCE','Frozen source and target microarray platforms differ','Use a common validated platform','target_manifest')
    lookup={g:i for i,g in enumerate(tgt.feature_ids)}
    missing=[g for g in model['feature_ids'] if g not in lookup]
    if missing:raise InputProblem('FEATURE_MISSING','Required frozen source features are absent from target: '+repr(missing[:5]),'Provide all features expected by the frozen model','target_expression')
    feature_order=model['feature_ids']
    X=tgt.values[:,[lookup[g] for g in feature_order]]
    labels,probs=predict_frozen(model,X,feature_order)
    order=model['classes']
    write_rows(root/'target_predictions_unlabeled.csv',['sample_id','predicted_label',*['prob_'+cl for cl in order]],
         [(sid,pred,*[format(float(x),'.17g') for x in v]) for sid,pred,v in zip(tgt.sample_ids,labels,probs)])
    warnings=[x.to_dict() for x in tgt.warnings]
    if c.get('source_processing_description')!=manifest['processing_description']:
        warnings.append({'code':'PROCESSING_DIFFERENCE','severity':'warning','message':'Target preprocessing declaration differs from original source.'})
    if manifest['independence_declaration']!='independent_documented':
        warnings.append({'code':'TARGET_INDEPENDENCE_UNKNOWN','severity':'warning','message':'Independent acquisition has not been established.'})
    metrics=None
    if manifest['labels']=='binary':
        truth=[tgt.metadata[sid].get('condition','') for sid in tgt.sample_ids]
        if not set(truth)<=set(order):
            raise InputProblem('LABEL_MAPPING_INCONSISTENT','Target labels differ from frozen source classes','Use original source class vocabulary','target_metadata.condition')
        metrics=evaluate_labels(truth,labels.tolist(),order,probs,threshold=.95)
        write_rows(root/'target_scored_predictions.csv',['sample_id','true_label','predicted_label',*['prob_'+cl for cl in order]],
          [(sid,t,p,*[format(float(x),'.17g') for x in v]) for sid,t,p,v in zip(tgt.sample_ids,truth,labels,probs)])
    result={'stage':'05','mode':'replay_frozen','result_origin':'new_computation','software_version':SOFTWARE,'science_version':SCIENCE,
        'status':'completed_with_warnings' if warnings else 'completed',
        'inputs':{'target':tgt.input_files,'frozen_model':{'sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(), 'bytes':model_path.stat().st_size}},
        'freeze':{'model_sha256':model['model_sha256'],'configuration_sha256':model['config_sha256'],
                  'target_labels_used_for_model_selection':False,'target_expression_used_for_fitting':False},
        'outputs':{'n_samples':len(tgt.sample_ids),'external':metrics,'evaluation_possible':metrics is not None},
        'warnings':warnings,'files':{}}
    return _finish(root,result)

def main(argv=None):
    parser=argparse.ArgumentParser(description='BRACE Stage 05 — prediction import or source-only model validation')
    sub=parser.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('evaluate',help='Evaluate user-supplied prediction table');a.add_argument('--predictions',required=True);a.add_argument('--manifest',required=True);a.add_argument('--out',required=True)
    b=sub.add_parser('train',help='Train a fresh binary source-only baseline')
    for name in ('source-expression','source-metadata','source-manifest','target-expression','target-metadata','target-manifest'):
        b.add_argument('--'+name,required=True)
    b.add_argument('--classes',nargs=2,default=['normal','tumor']);b.add_argument('--positive-class',default='tumor')
    b.add_argument('--scientific-role',choices=['external_locked','external_exploratory'],default='external_exploratory')
    b.add_argument('--out',required=True)
    replay=sub.add_parser('replay',help='Apply safe frozen JSON model to a new compatible cohort')
    for key in ('model','target-expression','target-metadata','target-manifest','out'):
        replay.add_argument('--'+key,required=True)
    args=parser.parse_args(argv)
    try:
        if args.mode=='evaluate':res=run_evaluate(args.predictions,args.manifest,args.out)
        elif args.mode=='replay':res=run_replay(args.model,args.target_expression,args.target_metadata,args.target_manifest,args.out)
        else:res=run_train(args.source_expression,args.source_metadata,args.source_manifest,
            args.target_expression,args.target_metadata,args.target_manifest,args.out,args.classes,args.positive_class,args.scientific_role)
    except InputProblem as ex:
        print(json.dumps({'status':'blocked','issue':ex.to_dict()},indent=2));return 2
    except (OSError,ValueError) as ex:
        print(f'BRACE failed: {type(ex).__name__}: {ex}',file=sys.stderr);return 1
    print(json.dumps({'status':res['status'],'mode':res['mode'],'out':args.out,'outputs':list(res['outputs'])},indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
