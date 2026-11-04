"""Stage 06 CLI: full external reliability reports for imported or frozen predictions.

Composes, rather than modifies, the Stage 05 source-only training implementation.
"""
from __future__ import annotations
import argparse,csv,hashlib,html,json,math,sys
from pathlib import Path
import numpy as np
from .prediction_io import load_predictions
from .intake import InputProblem
from .stage05_cli import run_train as run_stage05_train,run_replay as run_stage05_replay
from .metrics06 import reliability_analysis


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')


def output_dir(location):
    p=Path(location)
    if p.exists() and any(p.iterdir()):raise ValueError('Output directory must be new or empty')
    p.mkdir(parents=True,exist_ok=True)
    return p


def _read_stage05_rows(path,classes):
    path=Path(path)
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        required={'sample_id','true_label','predicted_label',*('prob_'+c for c in classes)}
        if not required.issubset(reader.fieldnames or []):raise ValueError('Stage 05 prediction columns missing')
        rows=list(reader)
    if not rows:raise ValueError('Empty Stage 05 predictions')
    if len({r['sample_id'] for r in rows})!=len(rows):raise ValueError('Duplicate Stage 05 prediction samples')
    rows.sort(key=lambda r:r['sample_id'])
    probs=np.array([[float(r['prob_'+c]) for c in classes] for r in rows])
    return rows,probs


def csv_export(root,analysis):
    def save(name, cols, rows):
        with (root/name).open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f);w.writerow(cols);w.writerows(rows)
    a=analysis;classes=a['class_order']
    samples=[];wrong=[]
    for item in a['records']:
        row=[item['sample_id'],item['study_id'],item['true_label'],item['predicted_label'],
             int(item['correct']),item['confidence'] if item['confidence'] is not None else '',
             '' if item['retained_at_frozen_threshold'] is None else int(item['retained_at_frozen_threshold'])]
        row += [item['probabilities'][c] if item['probabilities'] else '' for c in classes]
        samples.append(row)
        if not item['correct']:wrong.append(row)
    cols=['sample_id','study_id','true_label','predicted_label','correct','model_confidence','retained_at_frozen_threshold']+['prob_'+c for c in classes]
    save('sample_level.csv',cols,samples)
    save('error_cases.csv',cols,wrong)
    save('threshold_curve.csv',['threshold','retained','correct','errors','coverage','selective_accuracy','selective_risk','threshold_role'],
         [[r[k] if r[k] is not None else '' for k in ('threshold','retained','correct','errors','coverage','selective_accuracy','selective_risk','threshold_role')] for r in a['threshold_curve']])
    save('confidence_bins.csv',['lower','upper','count','mean_confidence','accuracy','absolute_gap'],
         [[r[k] if r[k] is not None else '' for k in ('lower','upper','count','mean_confidence','accuracy','absolute_gap')] for r in a['confidence_bins']])
    save('per_class.csv',['class','support','predicted_count','tp','precision','recall','f1','precision_lower_95','precision_upper_95','recall_lower_95','recall_upper_95'],
         [[c['class'],c['support'],c['predicted_count'],c['tp'], c['precision'] if c['precision'] is not None else '',
           c['recall'] if c['recall'] is not None else '',c['f1'] if c['f1'] is not None else '',
           c['precision_wilson_95']['lower'] if c['precision_wilson_95']['lower'] is not None else '',
           c['precision_wilson_95']['upper'] if c['precision_wilson_95']['upper'] is not None else '',
           c['recall_wilson_95']['lower'] if c['recall_wilson_95']['lower'] is not None else '',
           c['recall_wilson_95']['upper'] if c['recall_wilson_95']['upper'] is not None else ''] for c in a['metrics']['per_class']])
    save('study_summary.csv',['study_id','n','accuracy','observed_class_macro_f1','macro_denominator','class_support_json'],
        [[s['study_id'],s['n'],s['accuracy'],s['observed_class_macro_f1'],s['macro_denominator'],json.dumps(s['class_support'],sort_keys=True)] for s in a['study_summaries']])


def _pct(v):return 'Undefined' if v is None else f'{v*100:.2f}%'


def html_report(root,a, context):
    m=a['metrics'];classes=a['class_order'];conf=m['confusion_matrix']
    esc=html.escape
    matrix=['<table><thead><tr><th>True \\ Predicted</th>'+''.join('<th>'+esc(c)+'</th>' for c in classes)+'</tr></thead><tbody>']
    for i,c in enumerate(classes):
        matrix.append('<tr><th>'+esc(c)+'</th>'+''.join(f'<td>{n}</td>' for n in conf[i])+'</tr>')
    matrix.append('</tbody></table>')
    per=['<table><thead><tr><th>Class</th><th>True support</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead><tbody>']
    for row in m['per_class']:
        per.append('<tr><th>'+esc(row['class'])+f'</th><td>{row["support"]}</td><td>{_pct(row["precision"])}</td><td>{_pct(row["recall"])}</td><td>{_pct(row["f1"])}</td></tr>')
    per.append('</tbody></table>')
    errors=sorted(a['errors'],key=lambda r:-(r['confidence'] if r['confidence'] is not None else -1))[:30]
    err_rows=[]
    for row in errors:
        err_rows.append('<tr><td>'+esc(row['sample_id'])+'</td><td>'+esc(row['true_label'])+'</td><td>'+esc(row['predicted_label'])+'</td><td>'+_pct(row['confidence'])+'</td></tr>')
    error_table='<table><thead><tr><th>Sample</th><th>True</th><th>Predicted</th><th>Confidence</th></tr></thead><tbody>'+''.join(err_rows)+'</tbody></table>' if errors else '<p>No observed errors in the supplied labeled records.</p>'
    warnings=''.join('<div class="warning"><strong>'+esc(x['code'])+'</strong> · '+esc(x['message'])+'</div>' for x in a['warnings'])
    curve=json.dumps(a['threshold_curve'],separators=(',',':'),allow_nan=False).replace('<','\\u003c')
    point= a['frozen_threshold_result'];selected=point['selective_accuracy'] if point else None
    ctx=esc(str(context))
    script='''<script>
const curve=__DATA__;
const picker=document.getElementById('threshold-picker');
const stats=document.getElementById('threshold-results');
const xaxis=document.getElementById('threshold-role');
function percentage(v){return v===null?'Undefined':(v*100).toFixed(2)+'%'}
if(picker && curve.length){
  picker.max=curve.length-1;
  picker.value=curve.findIndex(x=>x.threshold_role==='predeclared_reference');
  function update(){const d=curve[+picker.value];
    stats.textContent='Cutoff '+d.threshold.toFixed(2)+' · retained '+d.retained+' · coverage '+percentage(d.coverage)+' · selective accuracy '+percentage(d.selective_accuracy)+' · errors '+d.errors;
    xaxis.textContent=d.threshold_role==='predeclared_reference'?'Predeclared reference from input/source configuration':'Exploratory threshold (post hoc; not new independent validation)';
  } picker.addEventListener('input',update);update();
}
</script>'''.replace('__DATA__',curve)
    body=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>BRACE · External reliability</title>
<style>body{{margin:0;background:#0b1626;color:#e4edf8;font:15px/1.5 system-ui,Arial,sans-serif}}main{{max-width:1100px;margin:auto;padding:34px 24px}}small,.muted{{color:#a0b3cd}}h1{{font-size:35px;margin:4px 0}}h2{{font-size:20px;margin-top:32px}}.headline{{font-size:17px;color:#bccfe7}}.cards{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}.card,.panel{{background:#15263e;border:1px solid #304562;border-radius:12px;padding:18px}}.card b{{font-size:27px;display:block;margin:4px 0}}.warning{{border-left:3px solid #d8a75b;background:#182a42;margin:9px 0;padding:10px 16px}}table{{border-collapse:collapse;width:100%;font-size:13px;display:block;overflow-x:auto}}td,th{{padding:9px 12px;text-align:left;border-bottom:1px solid #354764;white-space:nowrap}}th{{color:#aebfd2}}a{{color:#a9cfff}}input[type=range]{{width:100%;accent-color:#6ebbed}}.note{{color:#a0b3cd;font-size:13px}}@media(max-width:650px){{.cards{{grid-template-columns:1fr}}}}</style></head><body><main>
<small>BRACE / Stage 06 / Research validation</small><h1>External reliability</h1><p class="headline">{esc(a['origin'])} · {esc(a['evaluation_role'])} · {m['n']} prediction records</p>
<div class="cards"><section class="card"><small>Accuracy</small><b>{_pct(m['accuracy'])}</b><small>{m['n_correct']} correct / {m['n']} total</small></section><section class="card"><small>Observed-class macro F1</small><b>{_pct(m['supported_class_macro_f1'])}</b><small>{m['macro_denominator']} supported classes; not full universe if absent</small></section><section class="card"><small>Retained accuracy at reference cutoff</small><b>{_pct(selected)}</b><small>Cutoff {a['fixed_threshold']:.4g}; reference, not a safety guarantee</small></section></div>
<h2>Coverage vs. accuracy</h2><section class="panel"><p class="note">Only the original specified cutoff is a frozen reference. Moving the slider explores the same labeled predictions post hoc.</p>'''
    if a['threshold_curve']:
        body+='<input id="threshold-picker" type="range" min="0" step="1" aria-label="Exploratory confidence threshold"><p id="threshold-results"></p><p id="threshold-role" class="note"></p>'
    else:body+='<p>Unavailable: no complete probability vectors were supplied.</p>'
    body+='</section>'
    if isinstance(context,dict) and context.get('stage05_result',{}).get('outputs',{}).get('source_cv') is not None:
        src=context['stage05_result']['outputs']['source_cv']
        body+=('<h2>Source-only cross-validation comparison</h2><div class="panel"><p>Source out-of-fold accuracy: <b>'+_pct(src['accuracy'])+'</b> · External cohort accuracy: <b>'+_pct(m['accuracy'])+'</b></p><p class="note">The source metric uses out-of-fold predictions. The external metric uses a frozen model. Different sample composition and class support limit direct comparisons.</p></div>')
    body+='<h2>Per-class performance</h2>'+''.join(per)+'<h2>Confusion matrix</h2>'+''.join(matrix)
    if a['study_summaries']:
        body+='<h2>Study-specific results</h2><p class="note">Comparisons may be confounded when different studies contribute different classes.</p><table><thead><tr><th>Study ID</th><th>Samples</th><th>Accuracy</th><th>Observed classes</th></tr></thead><tbody>'
        for item in a['study_summaries']:
            observed=', '.join(c for c,k in item['class_support'].items() if k)
            body+='<tr><td>'+esc(item['study_id'])+'</td><td>'+str(item['n'])+'</td><td>'+_pct(item['accuracy'])+'</td><td>'+esc(observed)+'</td></tr>'
        body+='</tbody></table>'
    body+='<h2>Most confident observed errors</h2><p class="note">Up to 30 shown here; export contains all cases.</p>'+error_table
    body+='<h2>Warnings and limitations</h2>'+warnings+'<p class="note">Uncertainty intervals assume independent observations. No clinical safety, causal attribution or deployment clearance is established by these results.</p>'
    body+='<h2>Provenance and scientific role</h2><div class="panel"><pre style="white-space:pre-wrap;overflow-wrap:anywhere">'+ctx+'</pre></div>'
    body+='<p class="note">Exports: validation_result.json, sample_level.csv, error_cases.csv, per_class.csv, threshold_curve.csv, confidence_bins.csv, study_summary.csv.</p></main>'+script+'</body></html>'
    (root/'run_report.html').write_text(body,encoding='utf-8')


def finish(root,analysis, provenance):
    csv_export(root,analysis)
    write_json(root/'validation_result.json',{'stage':'06','analysis':analysis,'provenance':provenance,
             'interpretation':'Scientific research only. This tool evaluates supplied labels and predictions; it does not certify clinical reliability.'})
    html_report(root,analysis,provenance)
    hashes=[]
    for p in sorted(root.iterdir()):
        if p.is_file() and p.name!='FILE_SHA256_MANIFEST.csv':
            hashes.append([p.name,hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_size])
    with (root/'FILE_SHA256_MANIFEST.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['filename','sha256','bytes']);w.writerows(hashes)
    return analysis


def evaluate_existing(predictions,manifest,out):
    batch=load_predictions(predictions,manifest)
    root=output_dir(out)
    a=reliability_analysis(batch.sample_ids,batch.true_labels,batch.predicted_labels,batch.classes,
                           batch.probabilities,batch.manifest.get('primary_confidence_threshold',.95),batch.metadata,
                           batch.manifest['evaluation_role'],batch.manifest['independence_declaration'],
                           batch.manifest['prediction_origin'])
    a['warnings']=[x.to_dict() for x in batch.issues]+a['warnings']
    provenance={'input_files':batch.files,'prediction_manifest':batch.manifest,
                'warning':'The input independence declaration is user-supplied, not audited by BRACE.'}
    return finish(root,a,provenance)


def _wrap_stage05(stage05,root,kind,independence):
    result=json.loads((stage05/'run_result.json').read_text('utf-8'))
    if kind=='train':
        classes=result['outputs']['classes'];csv_path=stage05/'target_scored_predictions.csv'
        role=result['freeze']['scientific_role'];source={'stage05_result_sha256':hashlib.sha256((stage05/'run_result.json').read_bytes()).hexdigest(),
            'frozen_model_sha256':result['freeze']['frozen_model_sha256'],'source_cv_method':result['outputs']['source_cv_method']}
        # Independence is read from the input manifest, not inferred from the role.
    elif kind=='replay':
        classes=json.loads((Path(stage05/'frozen_model.json')).read_text())['classes'] if (stage05/'frozen_model.json').exists() else None
        # Replayed freezes reside outside this folder; caller provides original model separately.
        raise RuntimeError('Replay must use _wrap_replay')
    else:raise ValueError('Unsupported stage 05 mode')
    rows,p=_read_stage05_rows(csv_path,classes)
    a=reliability_analysis([r['sample_id'] for r in rows],[r['true_label'] for r in rows],
        [r['predicted_label'] for r in rows],classes,p,result['freeze']['primary_confidence_threshold'],
        rows,role,independence,'new_frozen_source_baseline')
    return finish(root,a,{'model':source,'stage05_result':result,'stage05_artifacts_directory':'stage05',
                          'warning':'Independent acquisition comes from supplied dataset manifest; not independently certified by BRACE.'})


def train(*args,**kwargs):
    root=output_dir(kwargs.pop('out'))
    target_manifest_path=kwargs.get('target_manifest')
    if target_manifest_path is None:
        # Stage 05 positional order: source 3 files, then target expression/metadata/manifest.
        if len(args)<6:raise ValueError('Missing target manifest')
        target_manifest_path=args[5]
    independence=json.loads(Path(target_manifest_path).read_text('utf-8-sig')).get('independence_declaration','unknown')
    run_stage05_train(*args,out=root/'stage05',**kwargs)
    return _wrap_stage05(root/'stage05',root,'train',independence)


def replay(model,target_expression,target_metadata,target_manifest,out):
    root=output_dir(out)
    old=run_stage05_replay(model,target_expression,target_metadata,target_manifest,root/'stage05')
    if not old['outputs']['evaluation_possible']:
        # Do not invent external performance from unlabeled target data.
        notice={'stage':'06','status':'unlabeled_predictions_only','metrics':None,'warnings':[{'code':'UNLABELED_TARGET','message':'No target reference labels; external performance is not computable.'}],
                'stage05_output':'stage05/target_predictions_unlabeled.csv'}
        write_json(root/'unlabeled_result.json',notice)
        return notice
    model_doc=json.loads(Path(model).read_text(encoding='utf-8-sig'))
    classes=model_doc['classes'];rows,p=_read_stage05_rows(root/'stage05'/'target_scored_predictions.csv',classes)
    target_doc=json.loads(Path(target_manifest).read_text('utf-8-sig'))
    a=reliability_analysis([r['sample_id'] for r in rows],[r['true_label'] for r in rows],
        [r['predicted_label'] for r in rows],classes,p,.95,rows,
        'external_exploratory',target_doc.get('independence_declaration','unknown'),'frozen_model_replay')
    return finish(root,a,{'model_sha256':hashlib.sha256(Path(model).read_bytes()).hexdigest(),
         'stage05_result':old,'warning':'Replaying frozen predictions is not automatically blind independent validation.'})


def main(argv=None):
    parser=argparse.ArgumentParser(description='BRACE Stage 06 — scientific external validation and uncertainty')
    sub=parser.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('evaluate');a.add_argument('--predictions',required=True);a.add_argument('--manifest',required=True);a.add_argument('--out',required=True)
    b=sub.add_parser('train')
    for key in ('source-expression','source-metadata','source-manifest','target-expression','target-metadata','target-manifest','out'):
        b.add_argument('--'+key,required=True)
    b.add_argument('--classes',nargs=2,default=['normal','tumor']);b.add_argument('--positive-class',default='tumor')
    b.add_argument('--scientific-role',choices=['external_exploratory','external_locked'],default='external_exploratory')
    c=sub.add_parser('replay')
    for key in ('model','target-expression','target-metadata','target-manifest','out'):c.add_argument('--'+key,required=True)
    opts=vars(parser.parse_args(argv));mode=opts.pop('mode');
    try:
        if mode=='evaluate':r=evaluate_existing(opts['predictions'],opts['manifest'],opts['out'])
        elif mode=='train':r=train(**{k.replace('-','_'):v for k,v in opts.items()})
        else:r=replay(**opts)
    except InputProblem as e:
        print(json.dumps({'status':'blocked','issue':e.to_dict()},indent=2));return 2
    except (ValueError,RuntimeError,OSError,KeyError,TypeError) as e:
        print(f'BRACE: {type(e).__name__}: {e}',file=sys.stderr);return 1
    print(json.dumps({'status':'completed','mode':mode,'n':r.get('n'),'accuracy':r.get('metrics',{}).get('accuracy') if r.get('metrics') else None},indent=2));return 0

if __name__=='__main__':raise SystemExit(main())
