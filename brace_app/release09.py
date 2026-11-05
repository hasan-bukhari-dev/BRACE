"""BRACE Stage 09: export-only scientific reporting and reproducibility bundles.

Read-only composition of completed Stage 05-07 outputs. No model fitting,
threshold tuning, or transformation of scientific outputs happens here.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import platform
import zipfile
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from typing import Any

from brace_app.version import VERSION as RELEASE_VERSION
ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_CPTAC = ROOT / 'examples' / 'stage06_cptac_report'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def obj(path: Path) -> dict[str, Any] | None:
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None


def package_versions() -> dict[str, str]:
    dependencies = ['numpy','scipy','scikit-learn','pandas','fastapi','uvicorn','python-multipart']
    versions = {'python': platform.python_version(), 'brace': RELEASE_VERSION}
    for item in dependencies:
        try: versions[item] = version(item)
        except PackageNotFoundError: versions[item] = 'not-installed'
    return versions


def _warnings(*documents: dict | None) -> list[dict[str, str]]:
    observed = set()
    output = []
    for doc in documents:
        if not doc: continue
        analysis = doc.get('analysis', doc)
        for warning in analysis.get('warnings', []):
            code = str(warning.get('code', 'UNSPECIFIED'))
            message = str(warning.get('message',''))
            key = (code,message)
            if key not in observed:
                observed.add(key)
                output.append({'code':code, 'severity':str(warning.get('severity','info')), 'message':message})
    return output


def _scientific_files(root: Path) -> list[Path]:
    """Allow only enumerated, generated numerical evidence; never include input uploads."""
    allow = {
        'validation_result.json','shift_result.json','run_report.html','gene_shifts.csv',
        'pca_samples.csv','per_class.csv','error_cases.csv','sample_level.csv',
        'threshold_curve.csv','confidence_bins.csv','study_summary.csv',
        'error_shift_samples.csv','error_shift_quartiles.csv',
        'target_scored_predictions.csv','target_predictions_unlabeled.csv',
        'source_oof_predictions.csv','frozen_model.json','run_result.json',
        'FILE_SHA256_MANIFEST.csv',
    }
    files = []
    for folder in ('validation','validation/stage05','shift'):
        p = root / folder
        if p.is_dir():
            files += [f for f in sorted(p.iterdir()) if f.is_file() and f.name in allow and not f.is_symlink()]
    return files


def _human_pct(v: Any) -> str:
    return 'Not available' if v is None else f'{float(v) * 100:.2f}%'


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    e = html.escape
    return '<div class="scroll"><table><thead><tr>' + ''.join('<th>'+e(str(h))+'</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>'+e(str(item))+'</td>' for item in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def _scientific_summary(root: Path, config: dict, validation: dict | None, shift: dict | None, warning_rows: list[dict]) -> str:
    e = html.escape
    analysis = (validation or {}).get('analysis', validation or {})
    metrics = analysis.get('metrics', {})
    rows = [['Run',config.get('name','Unknown')],['Evidence classification',config.get('kind','user_computed')],['Analysis mode',config.get('mode','Unknown')],['Scientific role',analysis.get('evaluation_role','Not applicable')],['Independence declaration',analysis.get('independence_declaration','Not independently verified')]]
    if metrics:
        rows += [['Evaluation samples',analysis.get('n')], ['Correct predictions',metrics.get('n_correct')],['Observed accuracy',_human_pct(metrics.get('accuracy'))],['Observed-class macro F1',_human_pct(metrics.get('supported_class_macro_f1'))],['Frozen/reference confidence threshold',analysis.get('fixed_threshold','Not available')]]
    if shift:
        rows += [['Aligned features',shift.get('feature_coverage',{}).get('shared')],['Shift computed from',shift.get('data_type','Uploaded or bundled expression data')],['PCA fitted from source samples',shift.get('pca',{}).get('source_fitted','Not available')]]
    warnings_html = ''.join(f'<li><strong>{e(w["code"])}</strong> · {e(w["message"])}</li>' for w in warning_rows) or '<li>No engine warnings; source provenance is still user-declared.</li>'
    source_labels = config.get('input_hashes',{})
    p = ['<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BRACE · Scientific evidence summary</title><style>body{background:#0b1729;color:#eaf1fb;font:15px/1.5 system-ui,sans-serif;margin:0}main{max-width:1080px;margin:0 auto;padding:28px}h1{font-size:32px}h2{font-size:19px;margin-top:30px}small,p.note{color:#aec1d9}table{width:100%;border-collapse:collapse}td,th{padding:9px 12px;text-align:left;border-bottom:1px solid #31445b}th{background:#1c304b}.scroll{overflow:auto}code,pre{color:#c4e3f3;white-space:pre-wrap;overflow-wrap:anywhere}.panel{background:#15263e;padding:18px;border:1px solid #31445b;border-radius:12px;margin:16px 0}li{margin:7px 0}</style></head><body><main>',
      '<small>BRACE 1.0 · LOCAL RESEARCH EVIDENCE · '+e(str(config.get('kind','user_computed'))).upper()+'</small>',
      '<h1>External validation and cohort analysis</h1>',
      '<p>'+e(config.get('data_label','Researcher-provided evidence; independently verified provenance not established.'))+'</p>',
      '<section class="panel"><h2>Scientific summary</h2>'+_table(['Field','Result'],rows)+'</section>']
    if metrics.get('per_class'):
        p += ['<h2>Class-specific performance</h2>', _table(['Class','Support','Precision','Recall','F1'], [[r['class'],r['support'],_human_pct(r['precision']),_human_pct(r['recall']),_human_pct(r['f1'])] for r in metrics['per_class']])]
    if shift and shift.get('gene_shifts'):
        genes = shift['gene_shifts'][:20]
        p += ['<h2>Top observed distribution differences</h2><p class="note">Exploratory feature comparisons; not proof of batch-effect causality or biomarker status.</p>', _table(['Feature','KS D','Median difference','BH q'],[[r['feature_id'],f'{r["ks_d"]:.3f}',f'{r["median_difference_target_minus_source"]:.3f}',(f'{r["ks_bh_q_exploratory"]:.4g}' if r["ks_bh_q_exploratory"] is not None else "Withheld")] for r in genes])]
    p += ['<h2>Warnings and restrictions</h2><ul>'+warnings_html+'</ul>',
          '<div class="panel"><h2>Input provenance</h2><p class="note">Uploaded files are not included in the downloadable bundle. Hashes allow independent matching to originals.</p><pre>'+e(json.dumps(source_labels,indent=2,sort_keys=True))+'</pre></div>',
          '<h2>How to reproduce</h2><p>Use the enclosed numerical CSV/JSON evidence and the BRACE source release, with matching input data, declared assay processing and frozen parameters. Consult <code>reproducibility_manifest.json</code> for SHA-256 hashes and software versions. BRACE does not automatically validate cohort independence or clinical reliability.</p>',
          '<p class="note">Changing displayed confidence thresholds after viewing target outcomes is exploratory, not a new locked independent evaluation. Reported intervals may assume independent sampled rows.</p>',
          '</main></body></html>']
    return '\n'.join(p)


def finalize_run(root: Path) -> None:
    """Compose the audited EMBRACE view; never rewrite numerical source files."""
    from brace_app.embrace import finalize
    finalize(root)


def build_historical_package() -> Path:
    """Offline, clearly labeled archived-prediction example; not a GEO expression demo."""
    out = EXAMPLE_CPTAC / 'BRACE_CPTAC_ARCHIVED_EVIDENCE.zip'
    if out.exists(): return out
    source_files = ['validation_result.json','sample_level.csv','error_cases.csv','per_class.csv',
                    'study_summary.csv','threshold_curve.csv','confidence_bins.csv','run_report.html']
    about = {
        'package_role':'Historical CancerShift CPTAC-GDC archived prediction evidence, independently re-scored by BRACE',
        'not_new_model_inference':True,
        'not_a_public_expression_dataset':True,
        'original_frozen_models_or_expression_matrices_available':False,
        'source_evidence_folder':'examples/cancershift_historical_cptac',
        'files':{f:sha(EXAMPLE_CPTAC/f) for f in source_files},
        'warnings':['Study/class confounding','Prostate true class missing','Not prospective clinical validation']
    }
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('HISTORICAL_EVIDENCE_PROVENANCE.json',json.dumps(about,indent=2))
        for f in source_files:z.write(EXAMPLE_CPTAC/f,f)
    return out
