"""Stage 07 forensic engine: isolation, evidence, edge cases, and negative controls."""
from __future__ import annotations
import csv,json,math
from pathlib import Path
import numpy as np
import pytest
from brace_core.intake import parse_cohort,InputProblem
from brace_core.compatibility import evaluate_compatibility
from brace_core.shift07 import analyze_shift,_bh
from brace_core.stage07_cli import execute

BASE=Path(__file__).resolve().parents[1]/'examples/synthetic_valid'

def paths():
    return [BASE/(f'{role}_{n}.{ext}') for role in ('source','target') for n,ext in [('expression','csv'),('samples','csv'),('manifest','json')]]

def comp(mode='diagnose_shift'):
    s=parse_cohort(*paths()[:3],'source')
    t=parse_cohort(*paths()[3:],'target')
    role='unlabeled_shift_only' if mode=='diagnose_shift' else 'external_exploratory'
    return evaluate_compatibility(s,t,mode,('normal','tumor'),role)

def test_bh_known_values():
    assert _bh([.01,.02,.5])==pytest.approx([.03,.03,.5])

def test_bh_missing_preserved():
    assert _bh([None,.01])==[None,.01]

def test_unlabeled_analysis():
    r=analyze_shift(comp())
    assert r['mode']=='diagnose_shift' and len(r['gene_shifts'])==120
    assert 'label_based_exploratory' not in r and 'error_association' not in r
    assert 'observed_conditions' not in r['compatibility']['source']
    assert 'observed_conditions' not in r['compatibility']['target']

def test_source_fit_pca():
    r=analyze_shift(comp())
    assert r['pca']['source_fitted'] is True
    assert len(r['pca']['samples'])==34
    assert r['pca']['selected_feature_count']<=250
    assert len(r['pca']['explained_variance_ratio_source'])==2

def test_sample_distance_nonnegative():
    r=analyze_shift(comp())
    assert all(p['source_scaled_pc_distance']>=0 for p in r['pca']['samples'])

def test_features_are_deterministically_sorted():
    c=comp(); a=analyze_shift(c); b=analyze_shift(c)
    assert a['gene_shifts']==b['gene_shifts'] and a['pca']==b['pca']

def test_no_automatic_normalization():
    c=comp(); before=c.source.values.copy();analyze_shift(c)
    np.testing.assert_array_equal(c.source.values,before)
    assert c.source.values.flags.writeable is False

def test_shift_detects_added_target_signal():
    from dataclasses import replace
    c=comp();t=c.target; altered=t.values.copy();altered[:,0]+=20
    t2=replace(t,values=altered)
    c2=replace(c,target=t2)
    a=analyze_shift(c);b=analyze_shift(c2)
    feature=t.feature_ids[0]
    ra=next(x for x in a['gene_shifts'] if x['feature_id']==feature)
    rb=next(x for x in b['gene_shifts'] if x['feature_id']==feature)
    assert rb['median_difference_target_minus_source']==pytest.approx(ra['median_difference_target_minus_source']+20)
    # source points unchanged when only target expression changes
    assert [x for x in a['pca']['samples'] if x['cohort']=='source']==[x for x in b['pca']['samples'] if x['cohort']=='source']

def test_unlabeled_ignores_labels():
    from dataclasses import replace
    c=comp();t=c.target
    newmeta={sid:{**m,'condition':'NONSENSE'} for sid,m in t.metadata.items()}
    c2=replace(c,target=replace(t,metadata=newmeta))
    a=analyze_shift(c);b=analyze_shift(c2)
    assert a['gene_shifts']==b['gene_shifts'] and a['pca']==b['pca']

def test_supervised_class_composition():
    r=analyze_shift(comp('train_validate'))
    assert r['label_based_exploratory']['class_composition']['source']=={'normal':10,'tumor':10}
    assert r['label_based_exploratory']['class_composition']['target']=={'normal':7,'tumor':7}

def test_no_class_fields_in_unlabeled_mode():
    r=analyze_shift(comp('diagnose_shift'))
    assert 'class_composition' not in r
    assert 'class_conditioned' not in r

def test_supervised_predictions():
    c=comp('train_validate')
    r=analyze_shift(c,prediction_rows=[{
        'sample_id':sid,'true_label':c.target.metadata[sid]['condition'],
        'predicted_label':c.target.metadata[sid]['condition'],
        'confidence':.7} for sid in c.target.sample_ids])
    assert r['error_association']['available'] and r['error_association']['n_errors']==0
    assert sum(x['n'] for x in r['error_association']['error_by_source_distance_quartile'])==14

def test_one_wrong_prediction():
    c=comp('train_validate');rec=[]
    for i,sid in enumerate(c.target.sample_ids):
        truth=c.target.metadata[sid]['condition'];pr=truth if i else ('tumor' if truth=='normal' else 'normal')
        rec.append({'sample_id':sid,'true_label':truth,'predicted_label':pr,'confidence':.8})
    r=analyze_shift(c,prediction_rows=rec)
    assert r['error_association']['n_errors']==1
    assert len(r['error_association']['sample_errors'])==1

def test_unlabeled_refuses_predictions():
    with pytest.raises(ValueError,match='supervised|Shift-only'):
        analyze_shift(comp(),prediction_rows=[{'sample_id':'x'}])

def test_duplicate_predictions_fail():
    c=comp('train_validate'); records=[{'sample_id':sid,'true_label':c.target.metadata[sid]['condition'],'predicted_label':'tumor'} for sid in c.target.sample_ids]
    records[1]['sample_id']=records[0]['sample_id']
    with pytest.raises(ValueError,match='exactly'):
        analyze_shift(c,prediction_rows=records)

def test_missing_predictions_fail():
    c=comp('train_validate'); records=[{'sample_id':sid,'true_label':c.target.metadata[sid]['condition'],'predicted_label':'tumor'} for sid in c.target.sample_ids[:-1]]
    with pytest.raises(ValueError,match='exactly'):
        analyze_shift(c,prediction_rows=records)

def test_false_truth_mismatch_fails():
    c=comp('train_validate'); records=[{'sample_id':sid,'true_label':'tumor','predicted_label':'tumor'} for sid in c.target.sample_ids]
    with pytest.raises(ValueError,match='true_label'):
        analyze_shift(c,prediction_rows=records)

def test_invalid_confidence_fails():
    c=comp('train_validate');records=[{'sample_id':sid,'true_label':c.target.metadata[sid]['condition'],'predicted_label':'tumor','confidence':2.0} for sid in c.target.sample_ids]
    with pytest.raises(ValueError,match='confidence'):
        analyze_shift(c,prediction_rows=records)

def test_blocked_raises():
    from dataclasses import replace
    c=comp();blocked=replace(c,issues=c.issues+(type(c.issues[0])('INVALID','block','stop','fix'),))
    with pytest.raises(ValueError,match='blocked'):
        analyze_shift(blocked)

def test_cli_writes_all_files(tmp_path):
    r=execute(*paths(),out=tmp_path/'out')
    assert (tmp_path/'out'/'run_report.html').exists()
    assert (tmp_path/'out'/'gene_shifts.csv').exists()
    assert len(list(csv.DictReader((tmp_path/'out'/'gene_shifts.csv').open())))==120
    assert json.loads((tmp_path/'out'/'shift_result.json').read_text())['mode']=='diagnose_shift'

def test_cli_refuses_overwrite(tmp_path):
    execute(*paths(),out=tmp_path/'out')
    with pytest.raises(ValueError,match='empty'):
        execute(*paths(),out=tmp_path/'out')

def test_cli_refuses_predictions_in_mode_c(tmp_path):
    with pytest.raises(ValueError,match='Mode C'):
        execute(*paths(),out=tmp_path/'x',predictions='dummy',prediction_manifest='dummy')

def test_supervised_cli_with_stage05_predictions(tmp_path):
    root=Path(__file__).resolve().parents[1]
    pd=root/'examples/synthetic_prediction_input'
    r=execute(*paths(),out=tmp_path/'out',mode='train_validate',
              predictions=pd/'predictions.csv',prediction_manifest=pd/'manifest.json')
    assert r['error_association']['available']
    assert len(list(csv.DictReader((tmp_path/'out'/'error_shift_samples.csv').open())))==14

def test_pca_rejects_constant_source_features():
    from dataclasses import replace
    c=comp();source=c.source
    data=np.zeros_like(source.values)
    c2=replace(c,source=replace(source,values=data))
    r=analyze_shift(c2)
    assert r['pca']['available'] is False
    assert all(x['median_shift_per_source_iqr'] is None for x in r['gene_shifts'])

def test_source_only_pca_variables():
    from dataclasses import replace
    c=comp();t=c.target
    newvalues=t.values.copy();newvalues[:,:]+=500
    r1=analyze_shift(c);r2=analyze_shift(replace(c,target=replace(t,values=newvalues)))
    assert r1['pca']['selected_features']==r2['pca']['selected_features']
    assert r1['pca']['explained_variance_ratio_source']==r2['pca']['explained_variance_ratio_source']

def test_unknown_prediction_label_fails():
    c=comp('train_validate')
    records=[{'sample_id':sid,'true_label':c.target.metadata[sid]['condition'],'predicted_label':'alien'} for sid in c.target.sample_ids]
    with pytest.raises(ValueError,match='vocabulary'):
        analyze_shift(c,prediction_rows=records)

def test_historical_reference_is_explicitly_not_new():
    root=Path(__file__).resolve().parents[1]/'examples/stage07_historical_cancershift'
    provenance=json.loads((root/'HISTORICAL_PROVENANCE.json').read_text())
    assert 'NOT a freshly calculated' in provenance['data_origin']
    assert provenance['study_role'].startswith('exploratory')
    rows=list(csv.DictReader((root/'historical_adaptation_comparison.csv').open()))
    quantile=next(x for x in rows if x['method']=='quantile_gene_mapping')
    loc=next(x for x in rows if x['method']=='combat_style_gene_location_scale')
    assert float(quantile['cohort_detectability_auroc_historical'])<float(loc['cohort_detectability_auroc_historical'])
    assert float(quantile['gse2109_macro_f1_historical'])<float(loc['gse2109_macro_f1_historical'])
