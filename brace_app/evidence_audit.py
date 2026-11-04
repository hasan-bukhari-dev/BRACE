"""Independent arithmetic/cross-format audit before exporting completed evidence.

Does not fit models, run gene tests, tune thresholds or repair numerical results.
"""
import csv
import json
import math
from pathlib import Path
from brace_core.signature import digest
from brace_core.baseline05 import canonical_sha

def require(condition,message):
    if not condition:raise ValueError('Evidence consistency: '+message)

def same(actual,expected,message):
    if actual is None or expected is None:require(actual is expected,message);return
    require(math.isclose(float(actual),float(expected),rel_tol=1e-10,abs_tol=1e-12),message)

def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def labels(metrics,records):
    order=metrics['class_order'];n=len(records)
    require(n>0 and n==metrics['n'],'evaluation sample denominator')
    require(len({r['sample_id'] for r in records})==n,'duplicate prediction IDs')
    matrix=[[sum(r['true_label']==a and r['predicted_label']==b for r in records) for b in order] for a in order]
    require(matrix==metrics['confusion_matrix'],'confusion cells disagree with sample rows')
    correct=sum(r['true_label']==r['predicted_label'] for r in records)
    require(sum(map(sum,matrix))==n and correct==metrics['n_correct'],'confusion total / correct count')
    same(metrics['accuracy'],correct/n,'accuracy denominator')
    recalls=[];f1s=[];absent=[]
    require([c['class'] for c in metrics['per_class']]==order,'per-class ordering')
    for i,c in enumerate(metrics['per_class']):
        tp=matrix[i][i];support=sum(matrix[i]);pred=sum(row[i] for row in matrix)
        require((c['support'],c['predicted_count'],c['tp'])==(support,pred,tp),'class support / true positives')
        same(c['precision'],tp/pred if pred else None,'precision denominator')
        same(c['recall'],tp/support if support else None,'recall denominator')
        same(c['f1'],2*tp/(support+pred) if support else None,'supported F1 denominator')
        if support:recalls.append(tp/support);f1s.append(2*tp/(support+pred))
        else:absent.append(c['class'])
    require(metrics['absent_true_classes']==absent and metrics['macro_denominator']==len(recalls),'missing-class denominator')
    same(metrics['balanced_accuracy_observed'],sum(recalls)/len(recalls),'balanced accuracy')
    same(metrics['supported_class_macro_f1'],sum(f1s)/len(f1s),'supported macro-F1')
    return n

def prediction_audit(root,raw):
    a=raw['analysis'];records=a['records'];n=labels(a['metrics'],records)
    require(n==a['n'] and a['errors']==[r for r in records if not r['correct']],'error identity/count')
    for r in records:
        require(r['correct']==(r['true_label']==r['predicted_label']),'sample correctness')
        probs=r['probabilities']
        if probs is None:require(r['confidence'] is None,'missing vector has confidence');continue
        require(set(probs)==set(a['class_order']),'probability class universe')
        require(all(math.isfinite(v) and 0<=v<=1 for v in probs.values()) and abs(sum(probs.values())-1)<=1e-4,'invalid saved vector')
        same(r['confidence'],max(probs.values()),'confidence maximum')
    for point in a['threshold_curve']:
        kept=[r for r in records if r['confidence'] is not None and r['confidence']>=point['threshold']];correct=sum(r['correct'] for r in kept)
        require((point['retained'],point['correct'],point['errors'])==(len(kept),correct,len(kept)-correct),'threshold equality/counts')
        same(point['coverage'],len(kept)/n,'coverage denominator')
        same(point['selective_accuracy'],correct/len(kept) if kept else None,'selective accuracy')
        same(point['selective_risk'],(len(kept)-correct)/len(kept) if kept else None,'selective risk')
    fixed=next((p for p in a['threshold_curve'] if p['threshold']==a['fixed_threshold']),None)
    require(fixed==a['frozen_threshold_result'],'frozen cutoff point')
    if fixed:
        for r in records:require(r['retained_at_frozen_threshold']==(r['confidence']>=a['fixed_threshold']),'frozen sample retention')
    for filename,expected in [('sample_level.csv',records),('error_cases.csv',a['errors'])]:
        actual=rows(root/'validation'/filename)
        require(len(actual)==len(expected),'prediction CSV row count')
        for row,saved in zip(actual,expected):
            require(all(row[k]==saved[k] for k in ('sample_id','study_id','true_label','predicted_label')),'prediction CSV identity')
            require(int(row['correct'])==int(saved['correct']),'prediction CSV correctness')
            same(float(row['model_confidence']) if row['model_confidence'] else None,saved['confidence'],'prediction CSV confidence')
    for row,point in zip(rows(root/'validation/threshold_curve.csv'),a['threshold_curve']):
        for key in ('threshold','retained','correct','errors','coverage','selective_accuracy','selective_risk'):
            same(float(row[key]) if row[key] else None,point[key],'threshold CSV '+key)
    require(len(rows(root/'validation/threshold_curve.csv'))==len(a['threshold_curve']),'threshold CSV family')
    modelpath=root/'validation/stage05/frozen_model.json'
    if modelpath.is_file():
        model=json.loads(modelpath.read_text());stage=json.loads((root/'validation/stage05/run_result.json').read_text())
        require(canonical_sha({k:v for k,v in model.items() if k!='model_sha256'})==model['model_sha256'],'canonical model hash')
        require(canonical_sha(model['config'])==model['config_sha256'] and stage['freeze']['frozen_model_sha256']==model['model_sha256'],'model/config freeze identity')
        labels(stage['outputs']['source_cv'],rows(root/'validation/stage05/source_oof_predictions.csv'))
        scored=rows(root/'validation/stage05/target_scored_predictions.csv')
        require({r['sample_id']:(r['true_label'],r['predicted_label']) for r in scored}=={r['sample_id']:(r['true_label'],r['predicted_label']) for r in records},'target model scoring linkage')
    return dict(evaluation_rows=n,correct=a['metrics']['n_correct'],errors=len(a['errors']),threshold_points=len(a['threshold_curve']),class_support='reconciled',source_oof_audited=modelpath.is_file())

def race_audit(root,result):
    frozen=json.loads((root/'race/selected_signature.json').read_text());methods=json.loads((root/'race/race_methods.json').read_text())
    h=frozen['hypothesis_hash'];require(digest({k:v for k,v in frozen.items() if k!='hypothesis_hash'})==h==result['hypothesis_hash']==methods['source_hypothesis_hash'],'frozen signature hash')
    genes=result['genes'];selected=frozen['selected'];source=frozen['screen'];a=result['aggregate']
    require([r['feature_id'] for r in selected]==[r['feature_id'] for r in genes],'selected gene identity/order')
    require(len(genes)==a['selected']==methods['target_family_size'] and len(source)==a['source_features_screened']==methods['source_family_size'],'testing-family counts')
    for i,(s,g) in enumerate(zip(selected,genes),1):
        require(s['selection_rank']==g['selection_rank']==i,'gene rank')
        same(g['source_effect'],s['effect'],'frozen source effect');same(g['source_q'],s['q'],'frozen source q')
        agreement=(g['effect']*s['effect']>0) if g['p'] is not None and g['effect'] is not None and g['effect']!=0 and s['effect']!=0 else None
        require(g['direction_agreement']==agreement,'effect direction')
        expected='untestable' if g['p'] is None else 'indeterminate' if agreement is None else 'opposite_direction' if not agreement else 'supported_matching_direction' if g['q']<=.05 else 'matching_direction_without_support'
        require(g['classification']==expected,'gene classification')
    require(a['target_testable']==sum(g['p'] is not None for g in genes),'testable denominator')
    require(a['supported']==sum(g['classification']=='supported_matching_direction' for g in genes),'supported count')
    require(a['opposite']==sum(g['classification']=='opposite_direction' for g in genes),'opposite count')
    require(a['untestable']==sum(g['classification']=='untestable' for g in genes),'untestable count')
    for filename,expected in [('source_gene_screen.csv',source),('replication_genes.csv',genes)]:
        actual=rows(root/'race'/filename);require(len(actual)==len(expected),'gene CSV count')
        for row,saved in zip(actual,expected):
            fid=saved['feature_id'];encoded="'"+fid if fid.startswith(('=','+','-','@','\t','\r')) else fid
            require(row['feature_id']==encoded,'gene CSV identifier encoding')
            for key in ('effect','p','q','source_effect','source_q','selection_rank'):
                if key in saved:same(float(row[key]) if row[key] else None,saved[key],'gene CSV '+key)
    for role in ('source','target'):
        counts=result['counts'][role];require(sum(counts['conditions'].values())==counts['samples'],'cohort sample labels')
    return dict(source_screened=len(source),frozen=len(genes),target_testable=a['target_testable'],supported=a['supported'],untestable=a['untestable'],hypothesis_hash=h)

def shift_audit(root,shift):
    actual=rows(root/'shift/gene_shifts.csv');expected=shift['gene_shifts']
    require(len(actual)==len(expected)==shift['feature_coverage']['shared'],'shift feature count')
    for row,saved in zip(actual,expected):
        require(row['feature_id']==saved['feature_id'],'shift feature identity')
        for key in ('source_mean','target_mean','source_median','target_median','ks_d','ks_bh_q_exploratory','median_difference_target_minus_source','median_shift_per_source_iqr'):
            same(float(row[key]) if row[key] else None,saved[key],'shift CSV '+key)
    points=rows(root/'shift/pca_samples.csv');stored=shift['pca']['samples']
    require(len(points)==len(stored),'PCA row count')
    for row,saved in zip(points,stored):
        require(row['sample_id']==saved['sample_id'] and row['cohort']==saved['cohort'],'PCA sample identity')
        same(row['pc1'],saved['pc1'],'PCA PC1');same(row['pc2'],saved['pc2'],'PCA PC2')
    if shift['mode']=='diagnose_shift':
        require(not shift.get('label_based_exploratory') and not shift.get('error_association'),'Mode C contains supervised findings')
        require(all('observed_conditions' not in shift['compatibility'][r] for r in ('source','target')),'Mode C exposes outcome counts')
    return dict(features=len(expected),pca_points=len(stored),mode=shift['mode'],supervised_results_excluded=shift['mode']=='diagnose_shift')

def audit(root,validation=None,shift=None,race=None):
    results={}
    if validation:results['ace']=prediction_audit(root,validation)
    if shift:results['shift']=shift_audit(root,shift)
    if race:results['race']=race_audit(root,race)
    return dict(status='PASS',checks=results,note='Independent count/formula/CSV/JSON/freeze audit; no model refit, threshold tuning or replacement of scientific estimates.')
