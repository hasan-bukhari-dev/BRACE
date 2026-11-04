"""Scientific and adversarial invariants for Stage 05."""
from __future__ import annotations
import copy,csv,json,hashlib
from pathlib import Path
from dataclasses import replace
import numpy as np
import pytest
from brace_core.intake import InputProblem,parse_cohort
from brace_core.compatibility import evaluate_compatibility
from brace_core.prediction_io import load_predictions
from brace_core.baseline05 import train_baseline,predict_frozen,canonical_sha,_folds
from brace_core.metrics05 import evaluate_labels
from brace_core.stage05_cli import run_evaluate,run_train

BASE=Path(__file__).resolve().parents[1]
FILES=BASE/'examples'/'synthetic_valid'
EX=BASE/'examples'/'synthetic_prediction_input'

def base():
    a=parse_cohort(FILES/'source_expression.csv',FILES/'source_samples.csv',FILES/'source_manifest.json','source')
    b=parse_cohort(FILES/'target_expression.csv',FILES/'target_samples.csv',FILES/'target_manifest.json','target')
    return a,b

def compat(a=None,b=None):
    sa,ta=base()
    return evaluate_compatibility(a or sa,b or ta,'train_validate')

def mutate_prediction(tmp_path,mutator,manifest_mutator=None):
    with (EX/'predictions.csv').open(newline='') as f:rows=list(csv.reader(f))
    mutator(rows)
    p=tmp_path/'preds.csv'
    with p.open('w',newline='') as f:csv.writer(f).writerows(rows)
    m=json.loads((EX/'manifest.json').read_text())
    if manifest_mutator:manifest_mutator(m)
    mp=tmp_path/'manifest.json';mp.write_text(json.dumps(m))
    return p,mp

def bad(code,op):
    with pytest.raises(InputProblem) as e:op()
    assert e.value.issue.code==code

def test_valid_prediction_import_and_alignment():
    p=load_predictions(EX/'predictions.csv',EX/'manifest.json')
    assert len(p.sample_ids)==14
    assert tuple(sorted(p.sample_ids))==p.sample_ids
    assert p.probabilities.shape==(14,2) and not p.probabilities.flags.writeable
    assert all(c in p.classes for c in p.predicted_labels)

def test_prediction_report(tmp_path):
    r=run_evaluate(EX/'predictions.csv',EX/'manifest.json',tmp_path/'a')
    assert r['outputs']['n_samples']==14
    assert (tmp_path/'a'/'run_report.html').exists()
    assert (tmp_path/'a'/'evaluated_predictions.csv').exists()
    assert r['result_origin']=='new_computation'

def test_deterministic_prediction_reports(tmp_path):
    p=EX/'predictions.csv';m=EX/'manifest.json'
    a=run_evaluate(p,m,tmp_path/'run1');b=run_evaluate(p,m,tmp_path/'run2')
    assert a==b
    assert (tmp_path/'run1'/'evaluated_predictions.csv').read_bytes()==(tmp_path/'run2'/'evaluated_predictions.csv').read_bytes()

@pytest.mark.parametrize('index,code',[(0,'DUPLICATE_SAMPLE_ID'),(1,'LABEL_MAPPING_INCONSISTENT'),(2,'LABEL_MAPPING_INCONSISTENT'),(3,'PROBABILITY_VECTOR_INVALID'),(4,'PROBABILITY_VECTOR_INVALID'),(5,'PREDICTION_ARGMAX_MISMATCH')])
def test_malformed_predictions_block(tmp_path,index,code):
    def mut(r):
        if index==0:r[2][0]=r[1][0]
        elif index==1:r[1][1]='nonsense'
        elif index==2:r[1][2]='nonsense'
        elif index==3:r[1][3]='NaN'
        elif index==4:r[1][3]='.01';r[1][4]='.01'
        else:r[1][2]='tumor' if r[1][2]=='normal' else 'normal'
    p,m=mutate_prediction(tmp_path,mut)
    bad(code,lambda:load_predictions(p,m))

def test_duplicate_header_rejected(tmp_path):
    p,m=mutate_prediction(tmp_path,lambda r:r[0].__setitem__(4,r[0][3]))
    bad('PREDICTION_FILE_INVALID',lambda:load_predictions(p,m))

def test_reordered_rows_dont_change_predictions(tmp_path):
    p,m=mutate_prediction(tmp_path,lambda r:r.__setitem__(slice(1,None),list(reversed(r[1:]))))
    original=load_predictions(EX/'predictions.csv',EX/'manifest.json');new=load_predictions(p,m)
    assert original.sample_ids==new.sample_ids
    np.testing.assert_array_equal(original.probabilities,new.probabilities)

def test_missing_probability_mapping_mode_a(tmp_path):
    p,m=mutate_prediction(tmp_path,lambda r:None,lambda m:m.__setitem__('probability_columns',{}))
    pred=load_predictions(p,m)
    assert pred.probabilities is None
    assert evaluate_labels(pred.true_labels,pred.predicted_labels,pred.classes)['selective'] is None

def test_incomplete_mapping_block(tmp_path):
    p,m=mutate_prediction(tmp_path,lambda r:None,lambda m:m.__setitem__('probability_columns',{'normal':'prob_normal'}))
    bad('PROBABILITY_VECTOR_INVALID',lambda:load_predictions(p,m))

def test_locked_without_independence_block(tmp_path):
    p,m=mutate_prediction(tmp_path,lambda r:None,lambda m:m.__setitem__('evaluation_role','external_locked'))
    bad('TARGET_INDEPENDENCE_UNKNOWN',lambda:load_predictions(p,m))

def test_multi_class_missing_true_support_and_completely_missed_class():
    r=evaluate_labels(['A','A','B','B'],['A','B','A','A'],['A','B','C'])
    assert r['per_class'][1]['f1']==0.0 and r['per_class'][1]['recall']==0.0
    assert r['per_class'][2]['recall'] is None and r['per_class'][2]['f1'] is None
    assert r['macro_denominator']==2 and r['comparison_scope']=='limited_class_support'

def test_no_positive_prediction_not_undefined_f1():
    r=evaluate_labels(['A','B','B'],['A','A','A'],['A','B'])
    assert r['per_class'][1]['precision'] is None and r['per_class'][1]['f1']==0.0

def test_empty_retained_set_defined_null():
    r=evaluate_labels(['A','B'],['A','B'],['A','B'],np.array([[.55,.45],[.49,.51]]),.95)
    assert r['selective']['selective_accuracy'] is None
    assert r['selective']['undefined_reason']=='EMPTY_RETAINED_SET'

def test_source_model_baseline_and_replay():
    c=compat();z=train_baseline(c)
    assert z['config']['cv_folds']==5
    assert z['config']['target_labels_used_for_model_selection'] is False
    assert len(z['oof_fold'])==len(c.source.sample_ids)
    X=c.target.values[:,c.target_indices]
    labels,probs=predict_frozen(z['frozen_model'],X,c.shared_features)
    assert labels.tolist()==z['target_pred']
    np.testing.assert_allclose(probs,z['target_prob'],atol=1e-14,rtol=1e-14)
    assert z['frozen_model']['model_sha256']==canonical_sha({k:v for k,v in z['frozen_model'].items() if k!='model_sha256'})

def test_source_training_repeated_identically():
    z1=train_baseline(compat());z2=train_baseline(compat())
    assert z1['frozen_model']==z2['frozen_model']
    np.testing.assert_array_equal(z1['oof_prob'],z2['oof_prob'])
    np.testing.assert_array_equal(z1['target_prob'],z2['target_prob'])

def test_external_label_permutation_does_not_change_model_or_predictions():
    a,b=base()
    reversed_labels=list(reversed([b.metadata[s]['condition'] for s in b.sample_ids]))
    new_meta={k:dict(v) for k,v in b.metadata.items()}
    for sid,label in zip(b.sample_ids,reversed_labels):new_meta[sid]['condition']=label
    b2=replace(b,metadata=new_meta)
    z1=train_baseline(compat(a,b));z2=train_baseline(compat(a,b2))
    assert z1['frozen_model']==z2['frozen_model']
    np.testing.assert_array_equal(z1['target_prob'],z2['target_prob'])
    assert z1['target_pred']==z2['target_pred']

def test_external_expression_changes_do_not_affect_fitted_model():
    a,b=base();new=replace(b,values=b.values.copy()+.7)
    z1=train_baseline(compat(a,b));z2=train_baseline(compat(a,new))
    assert z1['frozen_model']==z2['frozen_model']
    assert z1['source_metrics']==z2['source_metrics']
    assert not np.array_equal(z1['target_prob'],z2['target_prob'])

def test_external_metadata_cannot_reconfigure_threshold():
    z=train_baseline(compat())
    assert z['config']['primary_confidence_threshold']==.95

def test_frozen_hash_tampering_rejected():
    c=compat();z=train_baseline(c);f=copy.deepcopy(z['frozen_model'])
    f['coefficient'][0]+=1
    with pytest.raises(ValueError,match='integrity'):predict_frozen(f,c.target.values[:,c.target_indices],c.shared_features)

def test_feature_order_mismatch_rejected():
    c=compat();z=train_baseline(c)
    with pytest.raises(ValueError,match='feature'):predict_frozen(z['frozen_model'],c.target.values[:,c.target_indices],c.shared_features[::-1])

def test_source_cv_group_folds_keep_patients_separate():
    groups=[f'P{i:02d}' for i in range(10) for _ in range(2)]
    y=np.array(['normal','tumor']*10)
    folds,n,kind=_folds(y,groups)
    assert kind=='StratifiedGroupKFold'
    for tr,te in folds:
        assert not set(groups[i] for i in tr)&set(groups[i] for i in te)

def test_source_cv_unsplittable_groups_block():
    y=np.array(['normal']*10+['tumor']*10)
    groups=['ALL_NORMAL']*10+['ALL_TUMOR']*10
    bad('SOURCE_CV_UNSUPPORTED',lambda:_folds(y,groups))

def test_source_cv_low_class_block():
    y=['normal']*4+['tumor']*20
    bad('SOURCE_CV_UNSUPPORTED',lambda:_folds(y,[f'P{i}' for i in range(24)]))

def test_stage05_end_to_end_files(tmp_path):
    d=tmp_path/'run'
    r=run_train(*(FILES/f'{role}_{type_}.{ext}' for role in ('source','target') for type_,ext in [('expression','csv'),('samples','csv'),('manifest','json')]),out=d)
    assert r['outputs']['n_features_aligned']==120
    for path in ('frozen_model.json','source_oof_predictions.csv','target_predictions_unlabeled.csv','target_scored_predictions.csv','run_result.json','run_report.html'):
        assert (d/path).exists(),path
    assert not any(path.suffix in ('.pkl','.joblib') for path in d.iterdir())
    d2=tmp_path/'run2'
    r2=run_train(*(FILES/f'{role}_{type_}.{ext}' for role in ('source','target') for type_,ext in [('expression','csv'),('samples','csv'),('manifest','json')]),out=d2)
    assert r==r2
    for file in ('frozen_model.json','source_oof_predictions.csv','target_predictions_unlabeled.csv','target_scored_predictions.csv'):
        assert (d/file).read_bytes()==(d2/file).read_bytes()

def test_blocked_preflight_does_not_write_model(tmp_path):
    source,target=base()
    m=json.loads((FILES/'target_manifest.json').read_text());m['measurement_type']='raw_counts'
    p=tmp_path/'incompatible.json';p.write_text(json.dumps(m))
    bad('COMPATIBILITY_BLOCKED',lambda:run_train(FILES/'source_expression.csv',FILES/'source_samples.csv',FILES/'source_manifest.json',
        FILES/'target_expression.csv',FILES/'target_samples.csv',p,tmp_path/'run'))
    assert not (tmp_path/'run'/'frozen_model.json').exists()


def test_replay_matches_frozen_original_target_predictions(tmp_path):
    from brace_core.stage05_cli import run_replay
    d=tmp_path/'replay'
    result=run_replay(BASE/'examples/synthetic_baseline_output/frozen_model.json',
        FILES/'target_expression.csv',FILES/'target_samples.csv',FILES/'target_manifest.json',d)
    assert result['outputs']['evaluation_possible'] is True
    with (d/'target_predictions_unlabeled.csv').open() as f:replayed=list(csv.DictReader(f))
    with (BASE/'examples/synthetic_baseline_output/target_predictions_unlabeled.csv').open() as f:original=list(csv.DictReader(f))
    # The archived CSV was produced on another OS/math-library build. Keep
    # identity and labels exact while allowing at most 1e-15 absolute roundoff
    # in the two probabilities (observed Windows difference ~1e-17).
    assert len(replayed)==len(original)
    for actual,expected in zip(replayed,original):
        assert actual.keys()==expected.keys()
        assert actual['sample_id']==expected['sample_id']
        assert actual['predicted_label']==expected['predicted_label']
        for key in ('prob_normal','prob_tumor'):
            assert float(actual[key])==pytest.approx(float(expected[key]),rel=0,abs=1e-15)


def test_replay_frozen_model_supports_unlabeled_target(tmp_path):
    from brace_core.stage05_cli import run_replay
    manifest=json.loads((FILES/'target_manifest.json').read_text());manifest['labels']='unlabeled'
    mp=tmp_path/'unlabeled_manifest.json';mp.write_text(json.dumps(manifest))
    d=tmp_path/'replay'
    result=run_replay(BASE/'examples/synthetic_baseline_output/frozen_model.json',
        FILES/'target_expression.csv',FILES/'target_samples.csv',mp,d)
    assert result['outputs']['external'] is None
    assert not (d/'target_scored_predictions.csv').exists()
    assert (d/'target_predictions_unlabeled.csv').exists()


def test_replay_different_measurement_block(tmp_path):
    from brace_core.stage05_cli import run_replay
    manifest=json.loads((FILES/'target_manifest.json').read_text());manifest['measurement_type']='rnaseq_vst'
    mp=tmp_path/'different_manifest.json';mp.write_text(json.dumps(manifest))
    bad('MEASUREMENT_INCOMPATIBLE',lambda:run_replay(BASE/'examples/synthetic_baseline_output/frozen_model.json',
        FILES/'target_expression.csv',FILES/'target_samples.csv',mp,tmp_path/'replay'))


def test_historical_cancershift_v08_reference_reproduced():
    p=BASE/'examples/cancershift_historical_cptac'
    x=load_predictions(p/'predictions.tsv',p/'manifest.json')
    r=evaluate_labels(x.true_labels,x.predicted_labels,x.classes,x.probabilities,.95)
    assert r['n']==680 and r['n_correct']==668
    assert r['selective']['retained']==584 and r['selective']['retained_errors']==1
    assert 'prostate' in r['absent_true_classes']
    assert x.manifest['prediction_origin']=='historical_reference'


def test_probability_argmax_tie_allowed_with_warning(tmp_path):
    def tie(rows):
        rows[1][3]='0.5';rows[1][4]='0.5'
    p,m=mutate_prediction(tmp_path,tie)
    z=load_predictions(p,m)
    assert 'PROBABILITY_TIE' in [issue.code for issue in z.issues]
