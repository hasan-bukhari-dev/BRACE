"""EMBRACE: audited, conventional, deterministic evidence ZIPs.

Internal scientific files are never rewritten. Download views encode unsafe CSV
text, with a reversible cell ledger; JSON remains the exact identifier authority.
"""
import csv
import hashlib
import html
import io
import json
import os
import shutil
import threading
import zipfile
from functools import lru_cache
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from brace_app import release09 as release
from brace_app.export_safety import csv_bytes,within
from brace_app.evidence_audit import audit
from brace_core.signature import FILES as RACE_FILES
from brace_app.presentation import warning_view,uncertainty_view

VERSION='brace-embrace/0.8.0'
REPORT_FILES={'research_summary.html','HTML_PRESENTATION.json','analysis_methods.json','compatibility_summary.json','warning_exclusion_records.json',
              'consistency_audit.json','CSV_TEXT_ENCODING.json','FILE_SHA256_MANIFEST.csv','REPRODUCE.md','PRIVACY.md','race_config.json','confusion_matrix.csv'}
router=APIRouter()


def publish_evidence(root, contents, provenance):
    """Shared atomic publication for all scientific workflows; manifest commits last."""
    from brace_app.persistence import atomic_bytes,atomic_json
    provenance['published_artifact_sha256']={name:record(data) for name,data in contents.items()}
    staging=within(root,root/'embrace');staging.mkdir(exist_ok=True)
    for name,data in contents.items():
        atomic_bytes(within(root,staging/name),data)
    for name in REPORT_FILES:
        if name in contents:atomic_bytes(within(root,root/name),contents[name])
    bundle=within(root,root/'RESEARCH_PACKAGE.zip')
    temporary=within(root,root/'RESEARCH_PACKAGE.zip.tmp')
    try:
        with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for name,data in sorted(contents.items()):
                info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                archive.writestr(info,data)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:raise ValueError('Evidence ZIP failed CRC')
            for name,data in contents.items():
                if record(archive.read(name))!=record(data):raise ValueError('Evidence ZIP failed SHA verification')
        os.replace(temporary,bundle)
        atomic_json(root/'reproducibility_manifest.json',provenance)
        atomic_json(root/'EMBRACE_RECEIPT.json',{'version':VERSION,'bundle':record(bundle.read_bytes())})
    finally:
        temporary.unlink(missing_ok=True)
    return bundle
def json_bytes(value):return (json.dumps(value,indent=2,sort_keys=True,allow_nan=False,ensure_ascii=False)+'\n').encode('utf-8')
def record(data):return dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
def obj(path):return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None
def encoded(path):return csv_bytes(path.read_bytes())[0] if path.suffix=='.csv' else path.read_bytes()

@lru_cache(maxsize=64)
def export_lock(root):return threading.RLock()

def original_files(root,race=False):
    candidates=[root/'race'/name for name in RACE_FILES] if race else release._scientific_files(root)
    return [within(root,p) for p in candidates]

def verify_previous(root,manifest):
    """Do not bless changed completed scientific evidence while upgrading a bundle."""
    if not manifest:return
    expected=manifest.get('scientific_artifact_sha256',manifest.get('artifact_sha256',{}))
    if manifest.get('mode')=='race' and not expected:expected={'race/'+name:r for name,r in manifest['artifacts'].items()}
    for name,entry in expected.items():
        path=within(root,root/name)
        if not path.is_file() or release.sha(path)!=entry['sha256'] or path.stat().st_size!=entry['bytes']:
            raise ValueError('Completed evidence changed: '+name)

def reproduction(mode,historical=False):
    common=f"""# Reproducing this evidence

Evidence format: {VERSION}. Extract the ZIP and open research_summary.html without
a server or network. Input hashes, methods and output tables are enclosed.
Original uploaded files are excluded. Obtain the matching originals separately
and verify their SHA-256; this package alone cannot recreate private inputs.
Use the matching BRACE source and dependency versions in analysis_methods.json.
CSV_TEXT_ENCODING.json records reversible spreadsheet-safe text encoding.
Run configuration and declared evaluation role must match; declarations do not
authenticate acquisition or observation independence.

"""
    if mode=='evaluate_predictions':
        command="""Evaluate the same labeled prediction records and class/column declaration:
python -m brace_core.stage06_cli evaluate --predictions ORIGINAL.csv --manifest ORIGINAL_MANIFEST.json --out NEW_DIRECTORY

This evaluates supplied predictions; it does not execute or retrain their model.
"""
        if historical:command+='Historical CancerShift predictions only; original classifier weights and expression are unavailable. No new original-model inference is reproduced.\n'
    elif mode=='race':
        command="""Parse the six source/target expression, metadata and manifest files with
brace_core.intake.parse_cohort, then call brace_core.signature.run(source, target,
the JSON race_config.json contents, a new output directory). The source-only rule
screens the full family and freezes selected IDs before target testing.
Never select features or alter the rule from target outcomes. For the public ER
example, use the checkpoint's actual preparation README, hashes and exclusions.
Source/target processing and phenotype differences remain exploratory limits.
"""
    elif mode=='train_validate':
        command="""Run python -m brace_core.stage06_cli train with --source-expression,
--source-metadata, --source-manifest, --target-expression, --target-metadata,
--target-manifest and --out pointing to the matching inputs/a new output folder.
The existing binary baseline expects normal/tumor classes; source fold seed42
and full source-fitted parameters are recorded. Never fit to target outcomes.
Source out-of-fold and target scoring use different evaluation designs.
"""
    else:
        command="""Run python -m brace_core.stage07_cli with the six matching expression,
metadata and manifest arguments, --mode diagnose_shift and --out NEW_DIRECTORY.
Scaling/PCA fit the source only. Outcome labels stay excluded; this comparison
does not produce target accuracy or outcome-conditioned error explanations.
"""
    return common+command+"""
Where computed, uncertainty uses saved Wilson intervals and a1000-replicate
class-stratified row bootstrap, seed20261101. These assume independent rows and
do not correct unknown group/batch dependence. Confidence>=cutoff retains equal
values; a nonreference cutoff viewed after outcomes is exploratory.
Compare numerical artifacts. Software-version changes and random run IDs can
change provenance hashes without changing numerical results. Repeated export of
an unchanged run/version is byte-stable. Verify FILE_SHA256_MANIFEST.csv and
the published-byte hashes, separate from original scientific-source hashes.
"""


def report(config,validation,shift,race,methods,compat,warnings,check):
    e=lambda value:html.escape(str(value),quote=True)
    def table(headers,rows):
        return release._table(headers,[[('Unavailable' if cell is None else cell) for cell in row] for row in rows])
    mode=config['mode'];kind=config.get('kind','user_computed');a=(validation or {}).get('analysis')
    role='exploratory' if race else a['evaluation_role'] if a else 'unlabeled_shift_only'
    generic=bool(a and not race and not shift and kind!='historical' and mode=='evaluate_predictions')
    warnings=warning_view(warnings,generic)
    question='Gene-expression associations: source selection and target tests' if race else 'Measured distribution differences' if not a else 'Classification predictions against known labels'
    if race:
        ag=race['aggregate']
        conclusion=f"{ag['supported']} of {ag['selected']} source-selected associations had target statistical support in the same direction; {ag['target_testable']} were testable. Support requires target BH q ≤ 0.05 across the full frozen family."
    elif a:
        m=a['metrics'];conclusion=f"{m['n_correct']} correct predictions among {a['n']} evaluated records; {a['n']-m['n_correct']} incorrect. Accuracy applies to the supplied labels and records, not an untested population."
    else:
        conclusion=f"{shift['feature_coverage']['shared']} matched features were compared. This unlabeled analysis reports distributions and source-fitted projection, not prediction accuracy or a cause of error."
    brand='BRACE' if generic else 'BRACE · Biological Reliability Assessment across Cohorts and Experiments'
    sections=[f'<p class="eyebrow">{e(brand)} · {e(kind)} · {e(role)}</p><h1>{e(config.get("name",question))}</h1><h2>{question}</h2>',f'<p class="lead">{e(conclusion)}</p>',
        f'<p>{e(config.get("data_label","Computed from supplied evidence; acquisition and evaluation-role declarations are not independently authenticated."))}</p>',
        table(['Identity','Recorded value'],[['Study',config.get('name',question)],['Study ID',config.get('study_id','Legacy study identity unavailable')],['Run ID',config['id']],['Analysis',mode],['Evidence origin',kind],['Evaluation role',role],['Independent provenance authenticated','No']]),
        ('<p>This evaluation is not certification of a model or a new evaluation population. Original uploaded records and declarations are excluded; input hashes identify the matching originals.</p>' if generic else '<p>Research use only. No clinical certification or causal conclusion is established. Raw uploaded expression/metadata files are excluded; input hashes identify the originals.</p>')]
    if config.get('input_origin')=='verified_public':sections+=['<p><strong>Verified public inputs; fresh computation.</strong> The uploaded expression, sample metadata and declaration bytes match the bundled GSE42568 / GSE20711 ER inputs. This identifies file origin, not independent patient acquisition or clinical validity.</p>']
    if race:
        legend=public_annotation_legend(config,race)
        if legend:sections += ['<h2>Pinned feature annotation legend</h2>',table(['Feature ID','Gene symbol','Platform probe'],[[r['feature_id'],r.get('gene_symbol') or 'Unavailable',r.get('probe_id') or 'Unavailable'] for r in legend['annotations']]),'<p>Symbols are convenience labels for the immutable identifiers, from the pinned public platform annotation. Current nomenclature was not independently revalidated. Mapping provenance is in GENE_ANNOTATIONS.json; no statistical values or feature identities were changed.</p>']
    if kind=='historical':sections+=['<p class="warning"><strong>Historical CancerShift research.</strong> Archived predictions rescored by BRACE, not new five-class model inference. Original trained checkpoints and expression matrices are unavailable. Source CV/training is not reconstructed.</p>']
    if kind=='synthetic':sections+=['<p class="warning"><strong>Synthetic software demonstration.</strong> Artificial observations are not findings about patients or biomarkers.</p>']
    sections+=[('<h2>Record inputs and evaluation role</h2><p>Supplied labels, class mapping and input hashes describe this evaluation; they do not reconstruct an original training dataset.</p>' if generic else '<h2>Study inputs and task eligibility</h2><p>Recorded declarations, counts and task-specific restrictions; declarations are not acquisition audits.</p>')]
    if race or shift:
        contexts=compat['declarations'] if race else {r:compat[r] for r in ('source','target')}
        def value(role,key):
            c=contexts[role]
            if key=='samples':return compat['counts'][role]['samples'] if race else c['n_samples']
            if key=='features':return compat['counts'][role]['features'] if race else c['n_features']
            if key=='conditions':return compat['counts'][role]['conditions'] if race else c.get('observed_conditions','Excluded by unlabeled analysis contract')
            return c.get(key,'Not declared')
        sections+=[table(['Recorded field','Source','Target'],[[label,value('source',key),value('target',key)] for key,label in [
            ('cohort_id','Cohort identity'),('accession','Accession'),('samples','Included samples'),('features','Features'),('conditions','Observed class support'),
            ('platform','Platform'),('measurement_type','Measurement units/type'),('processing_description','Deposited processing'),('independence_declaration','Independence declaration')]])]
    else:sections+=['<p>Only the supplied prediction records were evaluated. Group IDs in those rows do not authenticate an original training or evaluation split.</p>']
    sections+=['<details><summary>Complete task checks and input declarations</summary><pre>'+e(json.dumps(compat,indent=2))+'</pre></details>']
    if race:
        ag=race['aggregate'];genes=race['genes'];frozen=methods['frozen_signature']
        if not ag['selected']:sections+=['<p>No genes passed the frozen source selection rule; no target gene tests were performed.</p>']
        sections+=['<h2>Source screen and frozen target family</h2>',table(['Quantity','Count'],[
            ['Source features screened',ag['source_features_screened']],['Source BH q ≤ 0.05',ag['source_q_passing']],['Frozen selected genes',ag['selected']],
            ['Testable in target',ag['target_testable']],['Matching + target BH support',ag['supported']],['Matching without sufficient support',sum(g['classification']=='matching_direction_without_support' for g in genes)],
            ['Opposite estimates',ag['opposite']],['Untestable',ag['untestable']],['Direction denominator',ag['direction_denominator']]]),
            '<p>Contrast: '+e(methods['race']['config']['source_conditions'])+'. Signed effect is positive-group mean minus negative-group mean in each cohort’s deposited normalized log-intensity units. Absolute source/target scales are not assumed comparable.</p>',
            '<p>Source BH correction covers the entire screened family; target BH correction covers every frozen hypothesis, including missing tests as p=1 for correction and displayed q=null. Matching without support is inconclusive; opposite signs alone do not establish effect reversal.</p>',
            '<p>Frozen hypothesis SHA-256: <code>'+e(frozen['hypothesis_hash'])+'</code>. Source-only selection settings: '+e(frozen['selection_rule'])+'.</p>',
            '<h2>Every selected association, including threshold-not-met and unavailable outcomes</h2>',
            table(['Rank','Feature ID','Source effect','Source p','Source q','Target effect','Target p','Target q','Direction','Evidence / reason'],[
                [g['selection_rank'],g['feature_id'],g['source_effect'],s['p'],g['source_q'],g['effect'],g['p'],g['q'],g['direction_agreement'],g['classification']+(' · '+g['reason'] if g['reason'] else '')]
                for g,s in zip(genes,frozen['selected'])]),
            '<p>None means unavailable, never an assumed zero. Exact source/target group sizes, Hedges’ g, pointwise intervals and reasons remain in race/*.json and CSV. Pointwise intervals are not simultaneous or adjusted for source selection. No model transfer is established.</p>']
    if a:
        m=a['metrics'];stage=methods.get('source_model_result');source=stage['outputs']['source_cv'] if stage else None
        def metricrows(x):return [[x['n'],x['n_correct'],x['n']-x['n_correct'],x['accuracy'],x['balanced_accuracy_observed'],x['supported_class_macro_f1'],x['macro_denominator'],', '.join(x['absent_true_classes']) or 'None']]
        head=['Evaluated','Correct','Incorrect','Accuracy fraction','Balanced accuracy fraction','Supported macro-F1','Supported classes','Absent true classes']
        sections+=['<h2>Full evaluation and class support</h2>']
        if source:sections+=['<h3>Source out-of-fold cross-validation</h3>',table(head,metricrows(source)),'<p>Source CV and target scoring use different samples and evaluation designs; a paired performance difference is not calculated. Source OOF intervals were not saved.</p>']
        else:sections+=['<p>Source cross-validation is unavailable for these supplied/archived predictions. Original training and preprocessing are declared or absent, not performed by this evaluation.</p>']
        sections+=['<h3>'+('Archived supplied predictions' if kind=='historical' else 'Target / supplied prediction evaluation')+'</h3>',table(head,metricrows(m)),
            '<p>Accuracy = correct/all evaluated. Balanced accuracy is mean recall over true-supported classes; supported-class macro-F1 is mean F1 over those same classes. Missing true classes are not evaluated.</p>',
            '<h3>Confusion matrix — true rows, predicted columns</h3>',table(['True / Predicted',*m['class_order']],[[label,*row] for label,row in zip(m['class_order'],m['confusion_matrix'])]),
            '<h3>Per-class support and undefined denominators</h3>',table(['Class','Support','Predicted count','TP','Precision','Recall','F1','Undefined reasons'],[[c['class'],c['support'],c['predicted_count'],c['tp'],c['precision'],c['recall'],c['f1'],c['undefined_reasons']] for c in m['per_class']]),
            '<h3>Saved uncertainty</h3><pre>'+e(json.dumps(uncertainty_view(m,generic),indent=2))+'</pre><p>Intervals assume independent rows and do not correct grouped or batch dependence. Unavailable intervals and reasons remain explicit.</p>',
            '<h2>Confidence and coverage at the saved reference</h2><p>Adjusting the threshold does not retrain the model. Retain when confidence ≥ cutoff. The maximum supplied class probability is not automatically calibrated probability of correctness; non-reference curve points are exploratory.</p>']
        point=a['frozen_threshold_result']
        if point:sections +=[table(['Reference threshold','Retained','Withheld','Coverage fraction','Correct retained','Incorrect retained','Selective accuracy','Selective risk'],[[point['threshold'],point['retained'],a['n']-point['retained'],point['coverage'],point['correct'],point['errors'],point['selective_accuracy'],point['selective_risk']]]),'<p>'+('No predictions retained; selective accuracy/risk are undefined.' if not point['retained'] else 'Selective accuracy applies only to retained predictions, not withheld cases.')+'</p>']
        else:sections+=['<p>No valid probability vectors were supplied. Confidence, selective accuracy/risk and coverage curves are unavailable.</p>']
        sections+=['<h3>Every observed error</h3>',table(['Record ID','Recorded group','True label','Predicted label','Maximum class probability','Retained at reference'],[[r['sample_id'],r['study_id'],r['true_label'],r['predicted_label'],r['confidence'],r['retained_at_frozen_threshold']] for r in a['errors']]),
            '<p>Complete rows, class vectors, confidence bins, descriptive ECE and all curve points are in validation/*.json/CSV. An absent expression/shift result must not be inferred from these model errors.</p>']
    if shift:
        sections+=['<h2>Source-fitted cohort shift</h2>',table(['Quantity','Recorded value'],[['Shared features',shift['feature_coverage']['shared']],['PCA available',shift['pca']['available']],['PCA source-fitted',shift['pca']['source_fitted']],['Projected points',len(shift['pca']['samples'])]]),
            '<p>PCA scaling, feature selection and projection space are fitted on source. KS, BH q and target-minus-source medians are descriptive; source-IQR normalization can be undefined. Shift does not establish that it caused a model error.</p>',
            table(['Feature','KS D','Exploratory BH q','Median target−source','Difference / source IQR'],[[g['feature_id'],g['ks_d'],g['ks_bh_q_exploratory'],g['median_difference_target_minus_source'],g['median_shift_per_source_iqr']] for g in shift['gene_shifts'][:20]]),
            '<p>Complete shift tables and exact PCA coordinates are in shift/*.csv/JSON. '+('Mode C excludes outcome labels: no supervised accuracy, target class counts or outcome-conditioned findings were calculated.' if shift['mode']=='diagnose_shift' else 'Same-run error/shift associations, where present, are observational and post hoc.')+'</p>']
    sections+=['<h2>Warnings and restrictions</h2><ul>'+''.join('<li><strong>'+e(w.get('code','CAUTION'))+'</strong> · '+e(w['message'])+'</li>' for w in warnings)+'</ul>',
        '<h2>Methods, provenance, exclusions and reproduction</h2><p>For linked files, extract the complete EMBRACE ZIP beside this HTML report. See analysis_methods.json, compatibility_summary.json and warning_exclusion_records.json for full recorded context. Exclusions before uploaded files are unknown unless a verified preparation record is supplied. No imputation or silent exclusion is added by this export.</p>',
        '<p>Read REPRODUCE.md and PRIVACY.md. Input file hashes identify original measurements; raw data must be acquired separately. CSV_TEXT_ENCODING.json records spreadsheet-safe text encoding without changing JSON identifiers. FILE_SHA256_MANIFEST.csv and reproducibility_manifest.json cover the published evidence.</p>',
        '<h2>Consistency audit</h2><pre>'+e(json.dumps(check,indent=2))+'</pre>']
    style='body{font:15px/1.55 system-ui,sans-serif;color:#142b38;background:#fff;margin:0}main{max-width:1100px;margin:auto;padding:28px}h1{font-size:30px}.lead{font-size:20px;line-height:1.5;max-width:980px}h2{margin-top:32px}h3{margin-top:24px}.eyebrow{font-size:12px;color:#315f62}.warning{border-left:4px solid #916400;padding:12px;background:#fff7df}.scroll{max-width:100%;overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px}td,th{padding:9px;text-align:left;border-bottom:1px solid #b8c6ca}th{background:#edf2f3}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4f5;padding:16px;font-size:12px}code{overflow-wrap:anywhere}@media print{main{padding:0}h2{break-after:avoid}.scroll{overflow:visible}table{font-size:9px}}'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:"><title>BRACE · EMBRACE scientific evidence</title><style>'+style+'</style></head><body><main>'+''.join(sections)+'</main></body></html>').encode('utf-8')

def finalize(root):
    root=Path(root).resolve()
    with export_lock(str(root)):return _finalize(root)

def _finalize(root):
    root=Path(root).resolve();config=obj(within(root,root/'run.json'))
    if config is None:raise ValueError('Only completed runs can be exported')
    if config.get('mode')=='replay_frozen':
        from brace_app.frozen_workflow import finalize as finalize_replay
        return finalize_replay(root)
    previous=obj(within(root,root/'reproducibility_manifest.json'));verify_previous(root,previous)
    if previous:
        if previous.get('run_id')!=config['id'] or previous.get('mode')!=config['mode']:raise ValueError('Run configuration identity changed')
        if previous.get('run_configuration_sha256') and previous['run_configuration_sha256']!=record((root/'run.json').read_bytes()):raise ValueError('Run configuration changed')
    from brace_app import server
    if config.get('kind') not in ('public_computed','historical'):
        for field,entry in config.get('input_hashes',{}).items():
            if config.get('kind')=='synthetic':
                if field not in {'source_expression.csv','source_samples.csv','source_manifest.json','target_expression.csv','target_samples.csv','target_manifest.json'}:raise ValueError('Unexpected example input')
                path=server.EXAMPLES/'synthetic_valid'/field
            else:
                if field not in {'source_expression','source_metadata','source_manifest','target_expression','target_metadata','target_manifest','predictions','prediction_manifest'}:raise ValueError('Unexpected input field')
                paths=[root/'input'/(field+ext) for ext in (('.json',) if field.endswith('manifest') else ('.csv','.tsv'))]
                matches=[within(root,p) for p in paths if p.is_file()]
                if len(matches)!=1:raise ValueError('Input missing or ambiguous: '+field)
                path=matches[0]
            if release.sha(path)!=entry['sha256']:raise ValueError('Input hash mismatch: '+field)
    bundle=within(root,root/'RESEARCH_PACKAGE.zip');receipt_path=within(root,root/'EMBRACE_RECEIPT.json');receipt=obj(receipt_path)
    if previous and bundle.is_file() and receipt:
        if record(bundle.read_bytes())!=receipt['bundle']:raise ValueError('Cached evidence ZIP changed')
        for name,entry in previous['published_artifact_sha256'].items():
            p=within(root,root/'embrace'/name)
            if not p.is_file() or record(p.read_bytes())!=entry:raise ValueError('Published evidence changed: '+name)
        if previous.get('embrace_version')==VERSION:return bundle
    for directory in ('validation','validation/stage05','shift','race'):
        folder=root/directory
        if folder.exists():
            within(root,folder)
            for p in folder.iterdir():within(root,p)
    validation=obj(root/'validation/validation_result.json');shift=obj(root/'shift/shift_result.json');race=obj(root/'race/race_result.json')
    if not any((validation,shift,race)):raise ValueError('Run has no scientific result')
    check=audit(root,validation,shift,race)
    methods=dict(export_version=VERSION,software_versions=release.package_versions(),scientific_methods={},input_hashes=config['input_hashes'],
        input_origin=config.get('input_origin','see_evidence_category'),provenance_authenticated=False,evidence_category=config.get('kind','user_computed'),mode=config['mode'])
    methods['study_identity']={key:config.get(key) for key in ('name','study_id','datasets','created_utc','schema_version')}
    methods['dataset_provenance']=config.get('dataset_provenance',{})
    warnings=release._warnings(validation,shift,race);compat={};preparation=config.get('public_preparation')
    if race:
        methods['race']=obj(root/'race/race_methods.json');frozen=obj(root/'race/selected_signature.json')
        methods['frozen_signature']={k:frozen[k] for k in ('hypothesis_hash','selection_rule','selected','condition_definitions')}
        methods['scientific_methods']['race']=methods['race']['version']
        compat=dict(eligible=race['eligible'],evaluation_role=race['evaluation_role'],counts=race['counts'],feature_coverage=race['feature_coverage'],warnings=race['warnings'],
            declarations={role:methods['race'][role+'_manifest'] for role in ('source','target')},preparation=preparation)
    if validation:
        methods['validation']={k:validation['analysis'][k] for k in ('method_version','evaluation_role','independence_declaration','fixed_threshold','class_order','interpretation','origin')}
        methods['prediction_provenance']=validation['provenance'];methods['scientific_methods']['validation']=validation['analysis']['method_version']
        stage=obj(root/'validation/stage05/run_result.json')
        if stage:
            methods['source_model_result']=stage
            methods['source_model_configuration']=obj(root/'validation/stage05/frozen_model.json')['config']
        if not shift:compat=dict(note='This evaluation checks supplied labels and predictions; original training measurements are not reconstructed.',declared_prediction_provenance=validation['provenance'],source_cv_available=False)
    if shift:
        compat=shift['compatibility'];methods['shift']=dict(science_version=shift['science_version'],provenance=shift.get('provenance'),pca={k:v for k,v in shift['pca'].items() if k!='samples'})
        methods['scientific_methods']['shift']=shift['science_version']
    scientific=original_files(root,bool(race));raw_records={p.relative_to(root).as_posix():record(p.read_bytes()) for p in scientific}
    contents={p.relative_to(root).as_posix():p.read_bytes() for p in scientific if p.name!='FILE_SHA256_MANIFEST.csv'}
    encoding={}
    for name,data in list(contents.items()):
        if name.endswith('.csv'):
            contents[name],changes=csv_bytes(data)
            if changes:encoding[name]=changes
    # A fresh inventory per scientific folder agrees with the published CSV view.
    for directory in sorted({str(Path(n).parent).replace('\\','/') for n in contents}):
        inventory=io.StringIO(newline='');w=csv.writer(inventory,lineterminator='\n');w.writerow(['filename','sha256','bytes'])
        for name,data in sorted(contents.items()):
            if Path(name).parent.as_posix()==directory:w.writerow([Path(name).name,record(data)['sha256'],len(data)])
        contents[directory+'/FILE_SHA256_MANIFEST.csv']=inventory.getvalue().encode()
    exclusions=dict(warnings=warnings,preparation=preparation,prior_upload_exclusions_known=preparation is not None,
        unknown_exclusions_note='BRACE includes the supplied valid finite cells; exclusions before those inputs are unknown unless documented in the verified public preparation.',
        source_untestable=race.get('source_untestable',[]) if race else [],target_untestable=[g for g in race['genes'] if g['p'] is None] if race else [])
    additions={'analysis_methods.json':json_bytes(methods),'compatibility_summary.json':json_bytes(compat),'warning_exclusion_records.json':json_bytes(exclusions),
        'consistency_audit.json':json_bytes(check),'CSV_TEXT_ENCODING.json':json_bytes(dict(rule='Only dangerous text cells are apostrophe-prefixed in the published CSV view. Rows/columns are 1-based including headers. Exact originals remain here and in JSON. Negative numeric values stay numeric. RACE also retains its pre-existing apostrophe encoding of dangerous identifiers.',changed_cells=encoding)),
        'REPRODUCE.md':reproduction(config['mode'],config.get('kind')=='historical').encode(),
        'PRIVACY.md':b'Original uploaded files, environment variables and executable models are excluded. Derived identifiers, scores, saved calculation records and declared provenance remain. Review them before sharing; identifiers/labels can still contain sensitive information. Hashes do not authenticate acquisition, legal permission or row independence.\n'}
    if race:additions['race_config.json']=json_bytes(methods['race']['config'])
    if config.get('dataset_provenance'):
        additions['DATASET_LINEAGE.json']=json_bytes(config['dataset_provenance'])
    if config.get('public_data_document'):
        additions['PUBLIC_DATA_PREPARATION.md']=config['public_data_document'].encode('utf-8')
    if race:
        legend=public_annotation_legend(config,race)
        if legend:
            additions['GENE_ANNOTATIONS.json']=json_bytes(legend)
    additions['research_summary.html']=report(config,validation,shift,race,methods,compat,warnings,check)
    contents.update(additions)
    if config['mode']=='evaluate_predictions' and config.get('kind')!='historical' and not shift and 'validation/run_report.html' in contents:
        # The legacy route remains usable, with the same task-neutral report view.
        # Original HTML/JSON and every numerical scientific artifact stay intact.
        contents['validation/run_report.html']=additions['research_summary.html']
        contents['HTML_PRESENTATION.json']=json_bytes(dict(
            reason='Prediction-only HTML uses neutral record vocabulary; numerical results and identifiers are unchanged.',
            legacy_path='validation/run_report.html',original_scientific_html=raw_records.get('validation/run_report.html'),
            published_html=record(contents['validation/run_report.html']),
            warning_wording='The independence warning refers to grouped records/batches; exact original engine wording remains in machine-readable evidence.'))
        additions['HTML_PRESENTATION.json']=contents['HTML_PRESENTATION.json']
        inventory=io.StringIO(newline='');writer=csv.writer(inventory,lineterminator='\n');writer.writerow(['filename','sha256','bytes'])
        for name,data in sorted(contents.items()):
            if str(Path(name).parent)=='validation' and Path(name).name!='FILE_SHA256_MANIFEST.csv':writer.writerow([Path(name).name,record(data)['sha256'],len(data)])
        contents['validation/FILE_SHA256_MANIFEST.csv']=inventory.getvalue().encode()
    if validation:
        m=validation['analysis']['metrics'];stream=io.StringIO(newline='');w=csv.writer(stream,lineterminator='\n')
        w.writerow(['true_label',*m['class_order']])
        w.writerows([[label,*row] for label,row in zip(m['class_order'],m['confusion_matrix'])])
        data,changes=csv_bytes(stream.getvalue().encode());contents['confusion_matrix.csv']=data
        if changes:
            encoding['confusion_matrix.csv']=changes
            contents['CSV_TEXT_ENCODING.json']=json_bytes(dict(rule='Dangerous text cells have an apostrophe prefix; negative numeric values remain numeric. 1-based row/column records preserve exact originals; JSON is authoritative.',changed_cells=encoding))
    # Canonical sections; legacy artifact paths remain compatibility aliases.
    for name,data in list(contents.items()):
        if name.startswith(('race/','validation/','shift/')):
            contents['results/'+name]=data
    contents['summary/report.html']=contents['research_summary.html']
    contents['methods/analysis_methods.json']=contents['analysis_methods.json']
    contents['methods/compatibility_summary.json']=contents['compatibility_summary.json']
    contents['provenance/DATASET_LINEAGE.json']=json_bytes(config.get('dataset_provenance',{}))
    contents['provenance/study.json']=json_bytes({key:config.get(key) for key in ('schema_version','name','study_id','datasets','created_utc')})
    contents['integrity/consistency_audit.json']=contents['consistency_audit.json']
    link_names=set(contents)|{'FILE_SHA256_MANIFEST.csv','reproducibility_manifest.json'}
    links='<h2>Inspect the enclosed evidence</h2><ul>'+''.join('<li><a href="'+html.escape(name,quote=True)+'">'+html.escape(name)+'</a></li>' for name in sorted(link_names) if name!='research_summary.html')+'</ul>'
    contents['research_summary.html']=contents['research_summary.html'].replace(b'</main>',links.encode('utf-8')+b'</main>')
    # Runtime manifest checks ORIGINAL files; packaged manifest checks published files.
    provenance=dict(embrace_version=VERSION,release=release.RELEASE_VERSION,run_id=config['id'],study_name=config.get('name'),study_id=config.get('study_id'),datasets=config.get('datasets',{}),schema_version=config.get('schema_version','1.0.0'),created_utc=config.get('created_utc'),mode=config['mode'],input_origin=config.get('input_origin','see_data_origin'),data_origin=config.get('kind','user_computed'),
        run_configuration_sha256=record((root/'run.json').read_bytes()),
        evidence_label=config.get('data_label','Computed from supplied files; provenance is not independently authenticated'),
        scientific_role='exploratory' if race else validation['analysis']['evaluation_role'] if validation else 'unlabeled_shift_only',
        independence_declaration=validation['analysis']['independence_declaration'] if validation else 'unknown',
        input_file_hashes_and_descriptions=config['input_hashes'],input_hashes=config['input_hashes'],
        software_versions=methods['software_versions'],scientific_method_versions={k:methods['scientific_methods'].get(k) for k in ('race','validation','shift')},
        model_frozen_before_external_evaluation=config['mode']=='train_validate',warnings=warnings,provenance_authenticated=False,
        scientific_artifact_sha256=raw_records,artifact_sha256=raw_records,
        published_artifact_sha256={n:record(data) for n,data in contents.items()})
    declared={}
    fields=('cohort_id','dataset_id','model_id','organism','role','accession','platform','feature_namespace','measurement_type','processing_description','labels','evaluation_role','independence_declaration','primary_confidence_threshold')
    for name in ('source_manifest','target_manifest','prediction_manifest'):
        doc=obj(root/'input'/(name+'.json'))
        if doc is None and race:doc=methods['race'].get(name)
        if doc is not None:declared[name]={key:doc[key] for key in fields if key in doc}
    provenance.update(declared_study_metadata=declared,
        analysis_parameters=dict(fixed_threshold=validation['analysis']['fixed_threshold'] if validation else None,
            class_order=validation['analysis']['class_order'] if validation else None,confidence_threshold_curve_is_post_hoc=True,
            source_fitted_pca=shift['pca']['source_fitted'] if shift else None,
            frozen_baseline_configuration=methods.get('source_model_configuration')),
        limitations=['Acquisition and observation independence are not independently authenticated.',
            'Descriptive associations do not establish cause or use in an untested population.',
            'Non-reference confidence thresholds are post hoc. Row uncertainty does not resolve grouped dependence.'])
    if race:provenance.update(artifacts={name:raw_records['race/'+name] for name in RACE_FILES},evaluation_role='exploratory',validated_evidence_claim=False)
    published=dict(provenance,artifact_sha256=provenance['published_artifact_sha256'])
    # Public manifest never claims its own digest: top CSV covers this manifest.
    contents['reproducibility_manifest.json']=json_bytes(published)
    stream=io.StringIO(newline='');w=csv.writer(stream,lineterminator='\n');w.writerow(['path','sha256','bytes'])
    for name,data in sorted(contents.items()):w.writerow([name,record(data)['sha256'],len(data)])
    contents['FILE_SHA256_MANIFEST.csv']=stream.getvalue().encode()
    return publish_evidence(root,contents,provenance)

def exported_path(root,path):
    root=Path(root).resolve();path=within(root,path)
    finalize(root)
    relative=path.relative_to(root);published=within(root,root/'embrace'/relative)
    if not published.is_file():raise ValueError('Output not in the published evidence inventory')
    return published

def example_root(study_id):
    """Build new report views in RUNS, never inside historical/public source folders."""
    from brace_app import server
    folder=server.RUNS/('_embrace_'+study_id);folder.mkdir(parents=True,exist_ok=True)
    folder=within(server.RUNS,folder)
    if study_id=='public_er_pass2':
        from brace_app.study_api import public_paths
        pair=public_paths();source=pair/'race_final';names=RACE_FILES;target=folder/'race';mode='race';kind='public_computed'
        result=obj(source/'race_result.json');config=dict(id=study_id,name='Public GEO ER association',mode=mode,kind=kind,input_hashes=result['input_files'],
            data_label='Saved public-cohort computation: GSE42568 source → GSE20711 target; exploratory ER association, not locked or clinical validation.',
            public_preparation=obj(pair/'prepared/summary.json'))
        config['public_data_document']=(pair/'README.md').read_text(encoding='utf-8')
    elif study_id=='historical_cptac':
        from brace_app.evidence_api import ace_context
        ace_context(study_id);source=server.EXAMPLES/'stage06_cptac_report';names=['validation_result.json','sample_level.csv','error_cases.csv','per_class.csv','study_summary.csv','threshold_curve.csv','confidence_bins.csv','run_report.html']
        target=folder/'validation';mode='evaluate_predictions';kind='historical'
        config=dict(id=study_id,name='CancerShift CPTAC archived prediction evidence',mode=mode,kind=kind,input_hashes=obj(source/'validation_result.json')['provenance']['input_files'],data_label='Archived CancerShift research predictions rescored by BRACE; no new five-class inference.')
    else:raise HTTPException(404,'Example not available')
    target.mkdir(exist_ok=True)
    for name in names:
        dest=within(folder,target/name)
        if dest.exists() and dest.read_bytes()!=(source/name).read_bytes():raise ValueError('Cached example scientific evidence changed')
        if not dest.exists():shutil.copyfile(source/name,dest)
    config_path=folder/'run.json'
    if not config_path.exists():config_path.write_bytes(json_bytes(config))
    return folder

@router.get('/api/embrace/{study_id}')
def download(study_id:str):
    from brace_app import server
    try:
        if study_id in ('public_er_pass2','historical_cptac'):
            with export_lock(str((server.RUNS/('_embrace_'+study_id)).resolve())):
                root=example_root(study_id);path=finalize(root)
        else:root=server.safe_run_dir(study_id);path=finalize(root)
        return FileResponse(path,filename='BRACE_EMBRACE_'+study_id+'.zip',media_type='application/zip',headers={'X-Content-Type-Options':'nosniff'})
    except HTTPException:raise
    except (ValueError,OSError,KeyError,TypeError) as exc:
        raise HTTPException(409,dict(code='EXPORT_EVIDENCE_MISMATCH',message='EMBRACE export blocked: '+str(exc)+'. Restore matching evidence and retry; scientific values were not repaired or replaced.')) from exc

@router.get('/api/embrace/{study_id}/report')
def readable_report(study_id:str):
    """Serve the exact audited HTML bytes already published in the evidence ZIP."""
    from fastapi import Response
    result=download(study_id)
    with zipfile.ZipFile(result.path) as archive:
        data=archive.read('research_summary.html')
    return Response(data,media_type='text/html',headers={
        'X-Content-Type-Options':'nosniff',
        'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; img-src data:; frame-ancestors 'self'",
        'Content-Disposition':'inline; filename="BRACE_research_summary.html"',
    })


def public_annotation_legend(config,race):
    from brace_app.provenance_origin import identify_public
    if config.get('kind')!='public_computed' and not identify_public(config.get('input_hashes',{})):return None
    from brace_app.study_api import public_paths
    root=public_paths();path=root/'race_final/gene_annotations.json';annotations=obj(path);selected={g['feature_id'] for g in race['genes']}
    return dict(source='Pinned public GPL570 feature annotation supplied with the verified ER example',source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),annotations=[r for r in annotations if r['feature_id'] in selected],note='Convenience mapping only; original identifiers and numerical artifacts unchanged.')

@router.get('/api/embrace/{study_id}/artifact/{member:path}')
def published_artifact(study_id:str,member:str):
    from pathlib import PurePosixPath
    from fastapi import Response
    import mimetypes
    parts=PurePosixPath(member).parts
    if not parts or any(p in ('..','.') for p in parts) or member.startswith('/') or '\\' in member or ':' in member or PurePosixPath(member).suffix not in ('.json','.csv','.md'):
        raise HTTPException(404,'Published artifact unavailable')
    result=download(study_id)
    with zipfile.ZipFile(result.path) as archive:
        if member not in archive.namelist():raise HTTPException(404,'Published artifact unavailable')
        data=archive.read(member)
    return Response(data,media_type=mimetypes.guess_type(member)[0] or 'application/octet-stream',headers={'Content-Disposition':'attachment; filename="'+PurePosixPath(member).name+'"','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'"})
