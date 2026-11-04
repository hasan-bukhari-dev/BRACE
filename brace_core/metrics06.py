"""BRACE Stage 06: deterministic, inspectable classification reliability analysis.

Inputs are frozen prediction records. This module NEVER fits models or selects a
threshold by target-label performance. Interval estimates assume independent
rows and are presented as descriptive approximations, not clinical guarantees.
"""
from __future__ import annotations

from collections import Counter
from math import sqrt
from statistics import NormalDist
from typing import Sequence
import numpy as np
from .metrics05 import evaluate_labels

SEED = 20261101
METHOD_VERSION = 'brace-reliability/0.6.0'
BOOTSTRAP_REPS = 1000


def wilson(success: int, total: int, level: float = .95) -> dict:
    if total < 0 or success < 0 or success > total: raise ValueError('Invalid binomial counts')
    if total == 0:
        return {'lower': None, 'upper': None, 'method': 'Wilson score', 'confidence_level': level,
                'undefined_reason': 'ZERO_DENOMINATOR'}
    if not (0 < level < 1): raise ValueError('Invalid confidence level')
    z = NormalDist().inv_cdf((1+level)/2)
    p = success/total
    d = 1+z*z/total
    center = (p+z*z/(2*total))/d
    half = z/d*sqrt(p*(1-p)/total+z*z/(4*total*total))
    return {'lower': 0. if success == 0 else max(0., center-half), 'upper': 1. if success == total else min(1., center+half),
            'method': 'Wilson score', 'confidence_level': level, 'numerator': success,
            'denominator': total, 'assumption': 'Independent Bernoulli observations; descriptive if independence is unverified'}


def _bootstrap_macro(y_true: np.ndarray, y_pred: np.ndarray, classes: tuple[str,...], n_reps: int) -> dict:
    """Label-stratified row bootstrap: class proportions are fixed by design."""
    supports={c:np.flatnonzero(y_true==c) for c in classes}
    selected=[i for i in supports.values() if len(i)]
    n=len(y_true)
    if n<30 or min(map(len,selected))<5:
        return {'lower':None, 'upper':None, 'method':'stratified percentile bootstrap',
                'undefined_reason':'INSUFFICIENT_SUPPORT_FOR_BOOTSTRAP', 'replicates':0}
    rng=np.random.default_rng(SEED)
    vals=[]
    for _ in range(n_reps):
        idx=np.concatenate([rng.choice(group,size=len(group),replace=True) for group in selected]);
        res=evaluate_labels(y_true[idx].tolist(),y_pred[idx].tolist(),classes)
        vals.append(res['supported_class_macro_f1'])
    a,b=np.quantile(vals,[.025,.975])
    return {'lower':float(a),'upper':float(b),'method':'stratified percentile bootstrap',
            'confidence_level':.95,'replicates':n_reps,'seed':SEED,
            'assumption':'Independent sampled rows; label-stratified and fixed observed class support. Does not capture study or patient clustering.'}


def _curve(y_true, y_pred, confidence, fixed_threshold):
    n=len(y_true); correct=(y_true==y_pred)
    # Dense enough for interactive inspection, with an EXACT predeclared threshold.
    thresholds=sorted(set([round(i/100,2) for i in range(101)]+[float(fixed_threshold)]))
    result=[]
    for threshold in thresholds:
        keep=confidence>=threshold
        retained=int(keep.sum()); right=int(np.sum(correct & keep))
        result.append({'threshold':threshold, 'retained':retained,'correct':right,
                       'errors':retained-right,'coverage':retained/n,
                       'selective_accuracy':right/retained if retained else None,
                       'selective_risk':(retained-right)/retained if retained else None,
                       'empty_reason':'EMPTY_RETAINED_SET' if not retained else None,
                       'threshold_role':'predeclared_reference' if threshold==fixed_threshold else 'exploratory_display'})
    return result


def _bins(y_true, y_pred, confidence):
    correct=y_true==y_pred
    bins=[];weighted=0.
    for i in range(10):
        lo=i/10;hi=(i+1)/10
        mask=(confidence>=lo)&(confidence<hi if i<9 else confidence<=hi)
        k=int(mask.sum());acc=float(np.mean(correct[mask])) if k else None
        mean_conf=float(np.mean(confidence[mask])) if k else None
        if k: weighted+=k/len(y_true)*abs(acc-mean_conf)
        bins.append({'lower':lo,'upper':hi,'count':k,'accuracy':acc,'mean_confidence':mean_conf,
                     'absolute_gap':abs(acc-mean_conf) if k else None})
    return bins,float(weighted)


def reliability_analysis(sample_ids:Sequence[str], y_true:Sequence[str], y_pred:Sequence[str],
                         classes:Sequence[str], probabilities:np.ndarray|None,
                         fixed_threshold:float=.95, metadata:Sequence[dict]|None=None,
                         evaluation_role:str='external_exploratory',
                         independence_declaration:str='unknown',
                         origin:str='user_supplied') -> dict:
    """Analysis in a fixed class universe. Probabilities must follow class order."""
    if not (0 <= fixed_threshold <= 1) or not np.isfinite(fixed_threshold):raise ValueError('Invalid frozen cutoff')
    n=len(sample_ids)
    if n==0 or len(set(sample_ids))!=n or len(y_true)!=n or len(y_pred)!=n:
        raise ValueError('Sample IDs and predictions must be unique and aligned')
    if metadata is not None and len(metadata)!=n:raise ValueError('Metadata length mismatch')
    order=tuple(classes);truth=np.asarray(y_true,dtype=str);pred=np.asarray(y_pred,dtype=str)
    if len(order)<2 or len(set(order))!=len(order) or not set(truth).issubset(order) or not set(pred).issubset(order):
        raise ValueError('Invalid class universe')
    p=None;confidence=None;warnings=[]
    if probabilities is not None:
        p=np.asarray(probabilities,dtype=float)
        if p.shape!=(n,len(order)) or not np.all(np.isfinite(p)) or np.any((p<0)|(p>1)) or np.any(np.abs(p.sum(axis=1)-1)>1e-4):
            raise ValueError('Invalid probability matrix')
        # Do not validate ties against manifest because imported rows may use documented tie breaking.
        for i in range(n):
            best=np.flatnonzero(p[i]==p[i].max())
            if len(best)==1 and order[best[0]]!=pred[i]:raise ValueError('Predicted class and probability maximum disagree')
        confidence=np.max(p,axis=1)
    base=evaluate_labels(truth.tolist(),pred.tolist(),order,p,fixed_threshold)
    base['accuracy_wilson_95']=wilson(base['n_correct'],n)
    for c in base['per_class']:
        c['recall_wilson_95']=wilson(c['tp'],c['support'])
        c['precision_wilson_95']=wilson(c['tp'],c['predicted_count'])
    base['macro_f1_bootstrap_95']=_bootstrap_macro(truth,pred,order,BOOTSTRAP_REPS)
    if base['absent_true_classes']:
        warnings.append({'code':'LIMITED_CLASS_SUPPORT','severity':'warning',
                         'message':'At least one declared true class is absent. Supported-class macro F1 and balanced accuracy exclude absent true classes.'})
    if independence_declaration!='independent_documented':
        warnings.append({'code':'INDEPENDENCE_NOT_ESTABLISHED','severity':'warning',
                         'message':'Sample independence is not documented; row-level intervals do not account for correlated patients or batches.'})
    if n<30:
        warnings.append({'code':'SMALL_EVALUATION_SET','severity':'warning',
                         'message':'Fewer than 30 prediction records; interval estimates will be imprecise.'})
    if base['macro_f1_bootstrap_95'].get('undefined_reason'):
        warnings.append({'code':'MACRO_F1_INTERVAL_UNAVAILABLE','severity':'info',
                         'message':'Too few cases for the pre-specified class-stratified bootstrap; point estimate remains available.'})
    if evaluation_role!='external_locked':
        warnings.append({'code':'NOT_LOCKED_INDEPENDENT_VALIDATION','severity':'info',
                         'message':'The supplied study role is not locked independent evaluation; do not represent these results as a new blind test.'})
    studies=[]
    if metadata is not None:
        groups={}
        for i,m in enumerate(metadata):
            v=str(m.get('study_id','')).strip()
            if v:groups.setdefault(v,[]).append(i)
        for key in sorted(groups):
            ix=groups[key];r=evaluate_labels(truth[ix].tolist(),pred[ix].tolist(),order)
            studies.append({'study_id':key,'n':len(ix),'accuracy':r['accuracy'],
                            'class_support':{x['class']:x['support'] for x in r['per_class']},
                            'observed_class_macro_f1':r['supported_class_macro_f1'],
                            'macro_denominator':r['macro_denominator']})
        if len(studies)>1 and all(len([c for c,s in x['class_support'].items() if s>0])==1 for x in studies):
            warnings.append({'code':'STUDY_CLASS_CONFOUNDING','severity':'warning',
                             'message':'Every study_id contains only one observed class; study-specific variation cannot be separated from true class effects.'})
    curve=[];bins=[];ece=None;errors=[]
    records=[]
    for i,sid in enumerate(sample_ids):
        wrong=bool(truth[i]!=pred[i]);
        row={'sample_id':sid,'true_label':str(truth[i]),'predicted_label':str(pred[i]),
             'correct':not wrong,'confidence':float(confidence[i]) if confidence is not None else None,
             'retained_at_frozen_threshold':bool(confidence[i]>=fixed_threshold) if confidence is not None else None,
             'study_id':str(metadata[i].get('study_id','')) if metadata is not None else '',
             'probabilities':{c:float(p[i,j]) for j,c in enumerate(order)} if p is not None else None}
        records.append(row)
        if wrong:errors.append(row)
    if p is not None:
        curve=_curve(truth,pred,confidence,fixed_threshold)
        bins,ece=_bins(truth,pred,confidence)
        # Do not imply the probability is clinically calibrated just because a score is high.
        warnings.append({'code':'UNCALIBRATED_MODEL_CONFIDENCE','severity':'info',
                         'message':'Confidence scores and expected calibration error are descriptive; clinical calibration is not demonstrated.'})
        frozen=next(x for x in curve if x['threshold']==fixed_threshold)
        base['selective']['coverage_wilson_95']=wilson(frozen['retained'],n)
        base['selective']['accuracy_wilson_95']=wilson(frozen['correct'],frozen['retained'])
        if frozen['retained']==0:
            warnings.append({'code':'EMPTY_RETAINED_SET','severity':'info','message':'No predictions satisfy the predeclared confidence cutoff.'})
    else:
        frozen=None
        warnings.append({'code':'NO_PROBABILITIES','severity':'info',
                         'message':'Confidence, calibration summaries and risk–coverage curves require class probability vectors.'})
    # Entire curve outside the predeclared point is exploratory, even when it looks favorable.
    return {'method_version':METHOD_VERSION,'n':n,'class_order':list(order),'evaluation_role':evaluation_role,
            'independence_declaration':independence_declaration,'origin':origin,
            'metrics':base,'fixed_threshold':fixed_threshold,'frozen_threshold_result':frozen,
            'threshold_curve':curve,'confidence_bins':bins,'expected_calibration_error_10bin':ece,
            'study_summaries':studies,'errors':errors,'records':records,'warnings':warnings,
            'interpretation':{
              'frozen_threshold':'Frozen reference if predeclared in input manifest or source config; historical references are not newly blinded.',
              'exploratory_thresholds':'All other cutoffs are post hoc displays of the same predictions; their apparent performance must not be claimed as independent confirmation.',
              'intervals':'Wilson scores and stratified bootstrap describe sample-level uncertainty under independence assumptions; neither accounts for unmeasured study, batch, or patient clustering.',
              'performance':'External accuracy is conditional on the observed cohort and class support, not universal clinical transportability.'}}
