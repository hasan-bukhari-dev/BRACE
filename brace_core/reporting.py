"""Deterministic preflight report generation; optional explicit aligned-data export."""
from pathlib import Path
from dataclasses import dataclass
from html import escape
import csv, hashlib, json
import numpy as np
from .contracts import Compatibility


def generate_report(result:Compatibility,out_dir:str|Path,export_aligned:bool=False)->dict:
    root=Path(out_dir)
    root.mkdir(parents=True,exist_ok=True)
    report=result.to_dict()
    hashes=[]
    for coh in (result.source,result.target):
        for key in ('expression','metadata','manifest'):
            hashes.append(coh.input_files[key]['sha256'])
    report['input_fingerprint']=hashlib.sha256(('|'.join(hashes)+'|'+result.mode).encode()).hexdigest()
    report['warnings_count']=sum(i['severity']=='warning' for i in report['issues'])
    report['blocking_count']=sum(i['severity']=='block' for i in report['issues'])
    (root/'compatibility_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    if result.eligible and result.shared_features:
        with (root/'aligned_feature_ids.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f);w.writerow(['feature_id']);w.writerows((k,) for k in result.shared_features)
        if export_aligned:
            for c,indices in ((result.source,result.source_indices),(result.target,result.target_indices)):
                with (root/f'{c.role}_aligned_expression.csv').open('w',encoding='utf-8',newline='') as f:
                    w=csv.writer(f);w.writerow(['feature_id',*c.sample_ids]);
                    for idx,feature in zip(indices,result.shared_features):
                        w.writerow([feature,*[format(float(v),'.17g') for v in c.values[:,idx]]])
    else:
        # Remove potentially stale files if writing over existing output directory
        for file in ('aligned_feature_ids.csv','source_aligned_expression.csv','target_aligned_expression.csv'):
            (root/file).unlink(missing_ok=True)
    html_parts=[
      '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
      '<title>BRACE · Cohort compatibility</title><style>body{margin:0;background:#0d1421;color:#e4ecf7;font:15px system-ui,sans-serif;line-height:1.55}',
      'main{max-width:900px;margin:auto;padding:40px 25px}h1{font-size:32px;margin:0}h2{margin-top:35px}small,.muted{color:#9aabc3}',
      '.panel{background:#162239;padding:20px;border:1px solid #30425e;border-radius:12px;margin:18px 0}',
      '.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:650px){.grid{grid-template-columns:1fr}}',
      'table{border-collapse:collapse;width:100%}td,th{padding:9px;border-bottom:1px solid #30425e;text-align:left;vertical-align:top}',
      '.block{border-left:3px solid #f78387}.warning{border-left:3px solid #e4ae6b}.info{border-left:3px solid #4c9edb}',
      'code{word-break:break-all}a{color:#a8cfff}</style></head><body><main>',
      '<small>BRACE / Stage 04 / Cohort preflight</small><h1>Compatibility report</h1>',
      f'<p class="muted">Mode: {escape(result.mode)} · Verdict: <strong>{escape(report["verdict"].replace("_"," ").upper())}</strong></p>',
      '<div class="grid">'
    ]
    for cohort in (report['source'],report['target']):
        html_parts.extend([
          '<section class="panel">',f'<small>{escape(cohort["role"].upper())}</small>',
          f'<h2>{escape(cohort["cohort_id"])}</h2>',
          f'<p>{cohort["n_samples"]} samples · {cohort["n_features"]} features</p>',
          f'<p class="muted">{escape(cohort["measurement_type"])}<br>{escape(cohort["processing_description"])}</p></section>'
        ])
    html_parts.extend(['</div><section class="panel">',f'<strong>{report["counts"]["shared_features"]} shared features</strong>',
        f'<p>Source overlap: {report["counts"]["source_overlap_fraction"]:.1%}; target overlap: {report["counts"]["target_overlap_fraction"]:.1%}.</p>',
        '</section><h2>Findings and next actions</h2>'])
    if not report['issues']:html_parts.append('<p>No structural warnings detected. Scientific independence and comparability are not certified.</p>')
    for issue in report['issues']:
        html_parts.extend([f'<div class="panel {escape(issue["severity"])}">',f'<small>{escape(issue["severity"].upper())} · {escape(issue["code"])}</small>',
            f'<p>{escape(issue["message"])}</p><p class="muted">Next: {escape(issue["next_action"])}</p></div>'])
    html_parts.extend(['<h2>Interpretation boundary</h2>',f'<p>{escape(report["note"])}</p>',
        '<p class="muted">BRACE does not auto-normalize, impute, certify patient independence or calculate model accuracy in Stage 04.</p>',
        f'<small>Input fingerprint: <code>{escape(report["input_fingerprint"])}</code></small></main></body></html>'])
    (root/'compatibility_report.html').write_text(''.join(html_parts),encoding='utf-8')
    return report
