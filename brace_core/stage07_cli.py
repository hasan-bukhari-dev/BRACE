"""BRACE Stage 07: run new expression-cohort forensics or inspect archived CancerShift evidence."""
from __future__ import annotations
import argparse,csv,hashlib,html,json
from pathlib import Path
from .intake import parse_cohort, InputProblem
from .compatibility import evaluate_compatibility
from .prediction_io import load_predictions
from .shift07 import analyze_shift


def _json(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')


def _csv(path,rows,cols):
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader()
        for r in rows:w.writerow(r)


def _manifest(root):
    with (root/'FILE_SHA256_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['filename','sha256','bytes'])
        for p in sorted(root.iterdir()):
            if p.is_file() and p.name!='FILE_SHA256_MANIFEST.csv':
                w.writerow([p.name,hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_size])


def _safe(s):return html.escape(str(s),quote=True)


def _plot(pca):
    if not pca.get('available'):return '<p>No PCA: insufficient variable source features.</p>'
    pts=pca['samples']
    xs=[p['pc1'] for p in pts];ys=[p['pc2'] for p in pts]
    minx,maxx=min(xs),max(xs);miny,maxy=min(ys),max(ys)
    width=780;height=350;pad=35
    def pos(x,low,high,extent):return pad+(x-low)/max(high-low,1e-12)*(extent-2*pad)
    parts=[f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Source-fitted PCA of source and target cohorts">',
           f'<rect x="0" y="0" width="{width}" height="{height}" rx="12" fill="#15263a"/>',
           f'<line x1="{pad}" y1="{height-pad}" x2="{width-pad}" y2="{height-pad}" stroke="#56718b"/>',
           f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{height-pad}" stroke="#56718b"/>']
    for p in pts:
        cx=pos(p['pc1'],minx,maxx,width);cy=height-pos(p['pc2'],miny,maxy,height)
        color='#60c9fa' if p['cohort']=='source' else '#f5a354'
        parts.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="3.6" fill="{color}" opacity="0.72"><title>{_safe(p["cohort"])} · {_safe(p["sample_id"])}</title></circle>')
    parts+=['</svg>','<p class="legend"><span style="color:#60c9fa">● Source</span> &nbsp; <span style="color:#f5a354">● Target</span> &nbsp; · PCA fitted on source samples only</p>']
    return ''.join(parts)


def _table(rows,cols,limit=40):
    if not rows:return '<p>No records.</p>'
    head='<thead><tr>'+''.join('<th>'+_safe(c)+'</th>' for c in cols)+'</tr></thead>'
    body='<tbody>'+''.join('<tr>'+''.join('<td>'+_safe('' if r.get(c) is None else (f"{r[c]:.5g}" if isinstance(r.get(c),float) else r.get(c,'')))+'</td>' for c in cols)+'</tr>' for r in rows[:limit])+'</tbody>'
    return '<div class="table-wrap"><table>'+head+body+'</table></div>'


def report(root,result):
    pca=result['pca']; a=result.get('error_association'); lab=result.get('label_based_exploratory')
    count=result['feature_coverage'];
    warnings='<ul>'+''.join('<li><strong>'+_safe(w['code'])+'</strong> — '+_safe(w['message'])+'</li>' for w in result['warnings'])+'</ul>'
    html_errors=''
    if a and a.get('available'):
        html_errors='<h2>Errors versus source-fit distance</h2><p>These are associations, not evidence that shift caused the errors. Distances are not model probabilities.</p>'
        html_errors+=_table(a['error_by_source_distance_quartile'],['distance_quartile','n','errors','error_rate','mean_confidence'],4)
        html_errors+='<h3>Observed errors</h3>'+_table(a['sample_errors'],['sample_id','true_label','predicted_label','confidence','source_scaled_pc_distance'],40)
    elif a:html_errors='<p>Prediction association unavailable: '+_safe(a.get('reason'))+'</p>'
    class_section=''
    if lab:
        class_section='<h2>Post-hoc labeled comparisons</h2><p>Labels were used only for descriptive summaries, never for PCA fitting or feature selection.</p>'
        class_section+='<pre>'+_safe(json.dumps(lab['class_composition'],indent=2))+'</pre>'
        for c in lab['class_conditioned']:
            class_section+='<h3>'+_safe(c['class'])+' ('+str(c['source_n'])+' source, '+str(c['target_n'])+' target)</h3>'
            class_section+=_table(c['top_genes'],['feature_id','median_difference_target_minus_source'],10) if c['status']=='exploratory' else '<p>Insufficient within-class sample counts.</p>'
    report_html='''<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BRACE · Shift Forensics</title>
    <style>body{font:15px/1.55 system-ui;background:#091423;color:#e7f0fa;max-width:1150px;margin:auto;padding:28px}h1{font-size:2.3rem;margin-bottom:0}h2{margin:32px 0 10px}h3{margin-top:20px}p,small{color:#a8bdd2}a{color:#8acdf9}pre,.panel{background:#15263a;border:1px solid #29415a;border-radius:11px;padding:15px;white-space:pre-wrap}table{border-collapse:collapse;width:100%;font-size:13px}th{text-align:left;color:#a8c5de}td,th{padding:10px;border-bottom:1px solid #2b4156}td{font-variant-numeric:tabular-nums}.table-wrap{overflow:auto;background:#112134;border-radius:9px}.warn{border-left:3px solid #eda364;padding:14px;background:#1d2632}svg{max-width:100%}.legend{font-size:13px}.pill{background:#183047;border-radius:99px;padding:5px 10px;font-size:12px}li{margin:6px 0}input{background:#183047;border:1px solid #456;color:white;border-radius:5px;padding:8px;max-width:100%}</style></head><body>'''
    report_html+='<small>BRACE / STAGE 07 · '+_safe(result['mode'])+' · descriptive research analysis</small><h1>When cohorts change, what changes with them?</h1>'
    report_html+='<p>These figures were calculated from the supplied expression matrices. No batch correction or target-label fitting was performed.</p>'
    report_html+=f'<div class="panel"><strong>{count["shared"]} shared features</strong> · {count["source_only"]} source-only · {count["target_only"]} target-only<br>Source-fitted PCA: {"available" if pca["available"] else "unavailable"}</div>'
    report_html+='<h2>Source-fitted cohort projection</h2>'+_plot(pca)
    report_html+='<p>Projection reflects the top variable features in the source cohort. Distances between points are descriptive and do not identify a causal batch effect.</p>'
    report_html+='<h2>Gene-level distribution shifts</h2><p>Sorted by two-sample Kolmogorov–Smirnov D; BH q-values are exploratory and assume valid sample-level independence. Large effects may be technical or biological.</p>'
    report_html+=_table(result['gene_shifts'],['feature_id','source_median','target_median','median_difference_target_minus_source','median_shift_per_source_iqr','ks_d','ks_bh_q_exploratory'],30)
    report_html+='<p>All gene-level rows, including undefined IQR denominators, are in gene_shifts.csv.</p>'
    report_html+=class_section+html_errors
    report_html+='<h2>Scientific caveats</h2><div class="warn">'+warnings+'<p>Observed shift ≠ cause of model errors. Cohort separation ≠ invalid model. Only external labeled predictions support claims about predictive performance.</p></div>'
    report_html+='<p>Input provenance, feature tables, PCA points, warnings and optional error associations are exported as separate machine-readable files.</p></body></html>'
    (root/'run_report.html').write_text(report_html,encoding='utf-8')


def execute(source_expression,source_metadata,source_manifest,target_expression,target_metadata,target_manifest,out,
            mode='diagnose_shift',classes=('normal','tumor'),predictions=None,prediction_manifest=None):
    root=Path(out)
    if root.exists() and any(root.iterdir()):raise ValueError('Output path must be empty')
    if mode=='diagnose_shift' and (predictions or prediction_manifest):
        raise ValueError('Mode C cannot consume labeled predictions or their metadata')
    if bool(predictions)!=bool(prediction_manifest):
        raise ValueError('Prediction records and manifest must be provided together')
    source=parse_cohort(source_expression,source_metadata,source_manifest,'source')
    target=parse_cohort(target_expression,target_metadata,target_manifest,'target')
    role='unlabeled_shift_only' if mode=='diagnose_shift' else 'external_exploratory'
    comp=evaluate_compatibility(source,target,mode,tuple(classes),role)
    if not comp.eligible:
        raise InputProblem('COMPATIBILITY_BLOCKED','Stage 04 compatibility blocked analysis: '+', '.join(i.code for i in comp.issues if i.severity=='block'),
                           'Correct incompatible cohort inputs before running shift forensics','preflight')
    records=None;provenance={'source':source.input_files,'target':target.input_files,'analytical_mode':mode,
                             'source_cohort_id':source.cohort_id,'target_cohort_id':target.cohort_id,
                             'input_origin_note':'Origin is based on supplied files and manifest declarations, not independently authenticated.'}
    if predictions:
        batch=load_predictions(predictions,prediction_manifest)
        if set(batch.classes)!=set(classes):raise ValueError('Prediction class vocabulary does not match supervised cohort class vocabulary')
        records=[]
        for idx,sid in enumerate(batch.sample_ids):
            conf=float(max(batch.probabilities[idx])) if batch.probabilities is not None else None
            records.append({'sample_id':sid,'true_label':batch.true_labels[idx],
                            'predicted_label':batch.predicted_labels[idx],'confidence':conf})
        provenance['prediction_files']=batch.files
        provenance['prediction_evaluation_role']=batch.manifest['evaluation_role']
        provenance['prediction_origin']=batch.manifest['prediction_origin']
    result=analyze_shift(comp,classes=tuple(classes),prediction_rows=records)
    result['provenance']=provenance
    root.mkdir(parents=True,exist_ok=True)
    _json(root/'shift_result.json',result)
    _csv(root/'gene_shifts.csv',result['gene_shifts'],['feature_id','source_mean','target_mean','source_median','target_median','median_difference_target_minus_source','source_iqr','median_shift_per_source_iqr','standardized_shift_reason','ks_d','ks_p_exploratory','ks_bh_q_exploratory'])
    _csv(root/'pca_samples.csv',result['pca']['samples'],['cohort','sample_id','pc1','pc2','source_scaled_pc_distance','beyond_source_95pct_distance'])
    if result.get('error_association') and result['error_association'].get('available'):
        _csv(root/'error_shift_samples.csv',result['error_association']['samples'],['sample_id','true_label','predicted_label','correct','confidence','source_scaled_pc_distance'])
        _csv(root/'error_shift_quartiles.csv',result['error_association']['error_by_source_distance_quartile'],['distance_quartile','n','errors','error_rate','mean_confidence','min_distance','max_distance'])
    report(root,result);_manifest(root)
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description='BRACE Stage 07 - cross-cohort shift and error forensics')
    for key in ['source-expression','source-metadata','source-manifest','target-expression','target-metadata','target-manifest','out']:
        p.add_argument('--'+key,required=True)
    p.add_argument('--mode',choices=('diagnose_shift','train_validate'),default='diagnose_shift')
    p.add_argument('--classes',nargs=2,default=['normal','tumor'])
    p.add_argument('--predictions');p.add_argument('--prediction-manifest')
    args=p.parse_args(argv)
    try:
        result=execute(args.source_expression,args.source_metadata,args.source_manifest,
                       args.target_expression,args.target_metadata,args.target_manifest,args.out,
                       args.mode,args.classes,args.predictions,args.prediction_manifest)
        print('BRACE Stage 07 complete:',Path(args.out,'run_report.html'))
        print('Shared features:',len(result['gene_shifts']),'PCA:',result['pca']['available'])
    except (InputProblem,ValueError) as e:
        print('BRACE blocked:',str(e));return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
