"""Scientific validation and IO regression tests for Stage 06."""
from __future__ import annotations
import copy,csv,hashlib,json
from pathlib import Path
import numpy as np
import pytest
from brace_core.metrics06 import reliability_analysis,wilson
from brace_core.stage06_cli import evaluate_existing,train,replay,main

BASE=Path(__file__).resolve().parents[1]
CPTAC=BASE/'examples/cancershift_historical_cptac'
SMALL=BASE/'examples/synthetic_prediction_input'
DATA=BASE/'examples/synthetic_valid'

def examine(truth,pred,classes,prob=None,threshold=.95,studies=None,role='external_exploratory'):
    ids=[f's{i}' for i in range(len(truth))]
    meta=[{'study_id': x} for x in studies] if studies else None
    return reliability_analysis(ids,truth,pred,classes,prob,threshold,meta,role)

def test_perfect_counts_and_matrix():
    a=examine(['A','A','B','B'],['A','A','B','B'],['A','B'])
    assert a['metrics']['accuracy']==1
    assert a['metrics']['confusion_matrix']==[[2,0],[0,2]]
    assert a['metrics']['supported_class_macro_f1']==1
    assert a['metrics']['balanced_accuracy_observed']==1
    assert len(a['errors'])==0

def test_missed_class_counts_against_macro_f1():
    a=examine(['A','A','B','B'],['A','A','A','A'],['A','B','C'])
    assert a['metrics']['per_class'][1]['f1']==0
    assert a['metrics']['per_class'][1]['precision'] is None
    assert a['metrics']['per_class'][2]['f1'] is None
    assert a['metrics']['macro_denominator']==2
    assert a['metrics']['supported_class_macro_f1']==pytest.approx(1/3)
    assert a['metrics']['balanced_accuracy_observed']==pytest.approx(.5)
    assert 'LIMITED_CLASS_SUPPORT' in [w['code'] for w in a['warnings']]

def test_absent_true_label_not_assumed_negative():
    a=examine(['A']*7,['A']*5+['B']*2,['A','B'])
    assert a['metrics']['comparison_scope']=='limited_class_support'
    assert a['metrics']['per_class'][1]['recall'] is None
    assert a['metrics']['macro_denominator']==1

def test_zero_denominators_wilson():
    z=wilson(0,0)
    assert z['lower'] is None and z['undefined_reason']=='ZERO_DENOMINATOR'
    assert wilson(0,10)['lower']==0
    assert wilson(10,10)['upper']==1
    assert wilson(5,10)['lower']<.5<wilson(5,10)['upper']

@pytest.mark.parametrize('s,n',[(-1,10),(11,10),(1,0)])
def test_wilson_rejects_impossible_counts(s,n):
    with pytest.raises(ValueError):wilson(s,n)

def test_empty_retained_and_reference_threshold_exact():
    p=np.array([[.6,.4],[.2,.8]])
    a=examine(['A','B'],['A','B'],['A','B'],p,1.)
    assert a['frozen_threshold_result']['retained']==0
    assert a['frozen_threshold_result']['selective_accuracy'] is None
    assert a['metrics']['selective']['accuracy_wilson_95']['undefined_reason']=='ZERO_DENOMINATOR'
    assert 'EMPTY_RETAINED_SET' in [w['code'] for w in a['warnings']]

def test_cutoff_boundary_and_exploratory_role():
    p=np.array([[.95,.05],[.15,.85],[.1,.9]])
    a=examine(['A','B','A'],['A','B','B'],['A','B'],p,.95)
    assert a['frozen_threshold_result']['retained']==1
    assert a['frozen_threshold_result']['selective_accuracy']==1
    assert len([x for x in a['threshold_curve'] if x['threshold_role']=='predeclared_reference'])==1
    assert all(x['threshold_role']=='exploratory_display' for x in a['threshold_curve'] if x['threshold']!=.95)
    assert a['threshold_curve'][0]['retained']==3

def test_missing_probabilities_skips_confidence_metrics():
    a=examine(['A','B'],['A','A'],['A','B'])
    assert a['confidence_bins']==[] and a['threshold_curve']==[]
    assert a['expected_calibration_error_10bin'] is None
    assert all(x['confidence'] is None for x in a['records'])

def test_calibration_bins_and_ece_computation():
    p=np.array([[.8,.2],[.2,.8]])
    a=examine(['A','B'],['A','B'],['A','B'],p)
    assert sum(x['count'] for x in a['confidence_bins'])==2
    assert a['expected_calibration_error_10bin']==pytest.approx(.2)
    assert a['confidence_bins'][8]['count']==2

def test_confident_incorrect_case_retained():
    p=np.array([[.01,.99],[.01,.99]])
    a=examine(['A','B'],['B','B'],['A','B'],p)
    assert len(a['errors'])==1
    assert a['errors'][0]['confidence']==.99
    assert a['errors'][0]['retained_at_frozen_threshold'] is True
    assert a['frozen_threshold_result']['errors']==1

def test_study_class_confounding_flag():
    a=examine(['A','A','B','B'],['A','A','B','A'],['A','B'],studies=['S1','S1','S2','S2'])
    assert 'STUDY_CLASS_CONFOUNDING' in [w['code'] for w in a['warnings']]
    assert len(a['study_summaries'])==2

def test_study_mixed_class_does_not_trigger_confounding():
    a=examine(['A','B','A','B'],['A','A','A','B'],['A','B'],studies=['S1','S1','S2','S2'])
    assert 'STUDY_CLASS_CONFOUNDING' not in [w['code'] for w in a['warnings']]

def test_bootstrap_reproducible_and_bounded():
    truth=['A']*30+['B']*30
    pred=['A']*27+['B']*3+['B']*26+['A']*4
    a=examine(truth,pred,['A','B']);b=examine(truth,pred,['A','B'])
    assert a==b
    ci=a['metrics']['macro_f1_bootstrap_95']
    assert ci['replicates']==1000 and 0<=ci['lower']<=ci['upper']<=1
    assert ci['method']=='stratified percentile bootstrap'

def test_bootstrap_refuses_insufficient_support():
    a=examine(['A']*35+['B']*3,['A']*38,['A','B'])
    assert a['metrics']['macro_f1_bootstrap_95']['undefined_reason']=='INSUFFICIENT_SUPPORT_FOR_BOOTSTRAP'

def test_invalid_probability_shape_sum_and_argmax():
    with pytest.raises(ValueError):examine(['A'],['A'],['A','B'],np.array([[.2,.2]]))
    with pytest.raises(ValueError):examine(['A'],['A'],['A','B'],np.array([[.2,.8]]))
    with pytest.raises(ValueError):examine(['A'],['A'],['A','B'],np.array([[np.nan,.8]]))

def test_duplicate_sample_identifiers_block():
    with pytest.raises(ValueError):reliability_analysis(['x','x'],['A','B'],['A','B'],['A','B'],None)

def test_historical_real_data_reproduced(tmp_path):
    a=evaluate_existing(CPTAC/'predictions.tsv',CPTAC/'manifest.json',tmp_path/'r')
    assert a['n']==680 and a['metrics']['n_correct']==668
    assert a['metrics']['accuracy']==pytest.approx(668/680)
    assert a['metrics']['absent_true_classes']==['prostate']
    assert a['frozen_threshold_result']['retained']==584
    assert a['frozen_threshold_result']['errors']==1
    assert a['frozen_threshold_result']['selective_accuracy']==pytest.approx(583/584)
    assert 'STUDY_CLASS_CONFOUNDING' in [w['code'] for w in a['warnings']]
    assert len(a['records'])==680 and len(a['errors'])==12
    assert 'NOT_LOCKED_INDEPENDENT_VALIDATION' in [w['code'] for w in a['warnings']]
    result=json.loads((tmp_path/'r'/'validation_result.json').read_text())
    assert result['provenance']['prediction_manifest']['evaluation_role']=='historical_reference'
    assert len(list(csv.DictReader((tmp_path/'r'/'sample_level.csv').open())))==680
    assert 'Exploratory threshold' in (tmp_path/'r'/'run_report.html').read_text()

def test_historical_outputs_exactly_repeat(tmp_path):
    a=evaluate_existing(CPTAC/'predictions.tsv',CPTAC/'manifest.json',tmp_path/'one')
    b=evaluate_existing(CPTAC/'predictions.tsv',CPTAC/'manifest.json',tmp_path/'two')
    assert a==b
    for name in ['validation_result.json','per_class.csv','threshold_curve.csv','confidence_bins.csv','run_report.html']:
        assert (tmp_path/'one'/name).read_bytes()==(tmp_path/'two'/name).read_bytes()

def test_without_probabilities_mode_a_exports_empty_curve(tmp_path):
    manifest=json.loads((SMALL/'manifest.json').read_text())
    manifest['probability_columns']={}
    mp=tmp_path/'noprob.json';mp.write_text(json.dumps(manifest))
    a=evaluate_existing(SMALL/'predictions.csv',mp,tmp_path/'o')
    assert a['threshold_curve']==[]
    assert len((tmp_path/'o'/'threshold_curve.csv').read_text().splitlines())==1

def test_train_replay_consistency_and_artifacts(tmp_path):
    args={f'{side}_{name}':DATA/f'{side}_{ext}' for side in ('source','target') for name,ext in [('expression','expression.csv'),('metadata','samples.csv'),('manifest','manifest.json')]}
    a=train(out=tmp_path/'a',**args)
    b=replay(tmp_path/'a'/'stage05'/'frozen_model.json',DATA/'target_expression.csv',DATA/'target_samples.csv',DATA/'target_manifest.json',tmp_path/'b')
    assert a['metrics']['accuracy']==b['metrics']['accuracy']
    assert a['records']==b['records']
    assert (tmp_path/'a'/'stage05'/'frozen_model.json').exists()
    assert (tmp_path/'a'/'threshold_curve.csv').exists()
    html=(tmp_path/'a'/'run_report.html').read_text()
    assert 'Source out-of-fold accuracy' in html
    assert a['independence_declaration']=='unknown'

def test_unlabeled_replay_never_fabricates_metrics(tmp_path):
    manifest=json.loads((DATA/'target_manifest.json').read_text());manifest['labels']='unlabeled'
    mp=tmp_path/'unlabeled.json';mp.write_text(json.dumps(manifest))
    obj=replay(BASE/'examples/synthetic_baseline_output/frozen_model.json',DATA/'target_expression.csv',DATA/'target_samples.csv',mp,tmp_path/'r')
    assert obj['metrics'] is None
    assert not (tmp_path/'r'/'validation_result.json').exists()
    assert (tmp_path/'r'/'stage05'/'target_predictions_unlabeled.csv').exists()

def test_cli_historical_smoke(tmp_path):
    status=main(['evaluate','--predictions',str(CPTAC/'predictions.tsv'),'--manifest',str(CPTAC/'manifest.json'),'--out',str(tmp_path/'r')])
    assert status==0

def test_html_escapes_user_supplied_study_ids(tmp_path):
    p=tmp_path/'evil.csv'
    p.write_text('sample_id,true_label,predicted_label,study_id,prob_A,prob_B\n1,A,A,"<img src=x onerror=alert(1)>",.9,.1\n',encoding='utf-8')
    m={'schema_version':'1.0.0','dataset_id':'demo','model_id':'demo','classes':['A','B'],'probability_columns':{'A':'prob_A','B':'prob_B'},'prediction_origin':'external_model','evaluation_role':'external_exploratory','independence_declaration':'unknown','label_source_description':'test'}
    mp=tmp_path/'manifest.json';mp.write_text(json.dumps(m))
    evaluate_existing(p,mp,tmp_path/'r')
    h=(tmp_path/'r'/'run_report.html').read_text()
    assert '<img src=x' not in h
    assert '&lt;img src=x' in h
