"""BRACE Stage 07: descriptive cross-cohort shift diagnostics.

No target labels are used in feature selection, normalization, or PCA fitting.
Causation and model performance cannot be inferred from expression shift alone.
"""
from __future__ import annotations
from collections import Counter
from typing import Any
import numpy as np
from scipy.stats import ks_2samp
from sklearn.decomposition import PCA
from .contracts import Compatibility

VERSION='brace-shift/0.7.1'
MAX_PCA_FEATURES=250


def _finite_float(x):
    z=float(x)
    return z if np.isfinite(z) else None


def _bh(pvalues):
    """Benjamini-Hochberg q-values; invalid entries remain None."""
    out=[None]*len(pvalues)
    idx=[i for i,p in enumerate(pvalues) if p is not None and np.isfinite(p) and 0<=p<=1]
    idx.sort(key=lambda i:pvalues[i])
    adj=1.
    for rank in range(len(idx),0,-1):
        i=idx[rank-1]
        adj=min(adj,float(pvalues[i])*len(idx)/rank)
        out[i]=float(adj)
    return out


def _matrix(comp:Compatibility):
    if not comp.eligible:
        raise ValueError('Cannot compute shift for a blocked cohort comparison')
    # Source and target indices were computed by Stage 04 lexicographic ID alignment.
    sx=comp.source.values[:,list(comp.source_indices)]
    tx=comp.target.values[:,list(comp.target_indices)]
    if not sx.shape[1] or sx.shape[1]!=tx.shape[1]:
        raise ValueError('No aligned shared features')
    return sx,tx


def _rows(sx,tx,features,inference_available=True):
    a_med=np.median(sx,axis=0);b_med=np.median(tx,axis=0)
    q25=np.percentile(sx,25,axis=0);q75=np.percentile(sx,75,axis=0)
    iqr=q75-q25
    smean=sx.mean(axis=0);tmean=tx.mean(axis=0)
    # One test for each aligned feature; reported as exploratory/non-causal.
    ks_results=[ks_2samp(sx[:,i],tx[:,i],method='auto') for i in range(len(features))]
    pvalues=[float(r.pvalue) for r in ks_results]
    qvalues=_bh(pvalues)
    result=[]
    for i,g in enumerate(features):
        md=float(b_med[i]-a_med[i]);denom=float(iqr[i])
        std=md/denom if denom>1e-12 else None
        result.append({'feature_id':g,'source_mean':float(smean[i]),'target_mean':float(tmean[i]),
                       'source_median':float(a_med[i]),'target_median':float(b_med[i]),
                       'median_difference_target_minus_source':md,'source_iqr':denom,
                       'median_shift_per_source_iqr':_finite_float(std) if std is not None else None,
                       'standardized_shift_reason':'ZERO_SOURCE_IQR' if std is None else None,
                       'ks_d':float(ks_results[i].statistic),
                       'ks_p_exploratory':pvalues[i] if inference_available else None,
                       'ks_bh_q_exploratory':qvalues[i] if inference_available else None})
    result.sort(key=lambda row:(-row['ks_d'], -abs(row['median_difference_target_minus_source']),row['feature_id']))
    return result


def _pca(sx,tx,features,source_ids,target_ids):
    n_features=sx.shape[1]
    variances=np.var(sx,axis=0,ddof=0)
    usable=[i for i in range(n_features) if variances[i]>1e-12]
    usable.sort(key=lambda i:(-variances[i],features[i]))
    selected=usable[:MAX_PCA_FEATURES]
    if len(selected)<2 or sx.shape[0]<3:
        return {'available':False,'reason':'PCA_REQUIRES_TWO_SOURCE_VARIABLE_FEATURES_AND_THREE_SOURCE_SAMPLES',
                'source_fitted':True,'samples':[]},None
    # Entirely source-fitted: target values are transformed only.
    mu=sx[:,selected].mean(axis=0)
    sd=sx[:,selected].std(axis=0)
    zs=(sx[:,selected]-mu)/sd
    zt=(tx[:,selected]-mu)/sd
    pca=PCA(n_components=2,svd_solver='full')
    ps=pca.fit_transform(zs)
    # A second numerical axis can exist even when the source has rank one.
    # Dividing that axis by an arbitrary epsilon produces enormous distances.
    if pca.singular_values_[1] <= pca.singular_values_[0]*1e-10:
        return {'available':False,'reason':'SOURCE_PCA_RANK_BELOW_TWO',
                'source_fitted':True,'samples':[]},None
    pt=pca.transform(zt)
    # Euclidean distance in the source PC coordinate system, normalized by
    # source PC standard deviation. This is a heuristic distance, not a risk.
    source_origin=ps.mean(axis=0)
    axis_sd=ps.std(axis=0)
    ds=np.linalg.norm((ps-source_origin)/axis_sd,axis=1)
    dt=np.linalg.norm((pt-source_origin)/axis_sd,axis=1)
    cut=float(np.percentile(ds,95))
    points=[]
    for cohort,ids,p,d in [('source',source_ids,ps,ds),('target',target_ids,pt,dt)]:
        for sid,row,dist in zip(ids,p,d):
            points.append({'cohort':cohort,'sample_id':sid,'pc1':float(row[0]),'pc2':float(row[1]),
                           'source_scaled_pc_distance':float(dist),'beyond_source_95pct_distance':bool(dist>cut)})
    info={'available':True,'source_fitted':True,'preprocessing':'source-only mean/standard deviation; source-only variance ranking',
          'selected_feature_count':len(selected),'selected_features':[features[i] for i in selected],
          'explained_variance_ratio_source':pca.explained_variance_ratio_.tolist(),
          'source_95pct_distance_threshold':cut,
          'target_beyond_source_95pct_count':int(np.sum(dt>cut)),
          'target_beyond_source_95pct_fraction':float(np.mean(dt>cut)),
          'samples':points}
    return info,{sid:float(d) for sid,d in zip(target_ids,dt)}


def _class_composition(cohort, classes):
    return {k:int(sum(cohort.metadata[s].get('condition','')==k for s in cohort.sample_ids)) for k in classes}


def _class_conditioned(sx,tx,comp,classes):
    # Only invoked when explicitly allowed in supervised mode. Not used for
    # parameter fitting, PCA selection, or marker gene selection.
    result=[]
    for label in classes:
        ids_s=[i for i,sid in enumerate(comp.source.sample_ids) if comp.source.metadata[sid].get('condition')==label]
        ids_t=[i for i,sid in enumerate(comp.target.sample_ids) if comp.target.metadata[sid].get('condition')==label]
        if len(ids_s)<3 or len(ids_t)<3:
            result.append({'class':label,'source_n':len(ids_s),'target_n':len(ids_t),
                           'status':'insufficient_samples','top_genes':[]})
            continue
        x=sx[ids_s];y=tx[ids_t]
        s_m=np.median(x,axis=0);t_m=np.median(y,axis=0)
        d=(t_m-s_m)
        v=[]
        for j in range(len(comp.shared_features)):
            v.append({'feature_id':comp.shared_features[j], 'median_difference_target_minus_source':float(d[j])})
        v.sort(key=lambda r:(-abs(r['median_difference_target_minus_source']),r['feature_id']))
        result.append({'class':label,'source_n':len(ids_s),'target_n':len(ids_t),
                       'status':'exploratory','top_genes':v[:25]})
    return result


def _prediction_associations(target_ids,distances,prediction_rows,mode,comp):
    if prediction_rows is None:return None
    if mode!='train_validate':raise ValueError('Prediction-error associations require supervised train_validate mode')
    if distances is None:
        return {'available':False,'reason':'SOURCE_FITTED_PCA_UNAVAILABLE'}
    records={r['sample_id']:r for r in prediction_rows}
    if len(records)!=len(prediction_rows) or set(records)!=set(target_ids):
        raise ValueError('Target prediction sample IDs must match exactly, without duplicates')
    classes_for_prediction=set(comp.source.metadata[sid].get('condition','') for sid in comp.source.sample_ids)
    ordered=[]
    for sid in target_ids:
        row=records[sid]
        truth=comp.target.metadata[sid].get('condition','')
        if truth!=row['true_label']:
            raise ValueError('Prediction true_label does not match target metadata for '+sid)
        if row['predicted_label'] not in classes_for_prediction:
            raise ValueError('Prediction label is outside the declared cohort class vocabulary')
        confidence=row.get('confidence')
        if confidence is not None and (not np.isfinite(confidence) or not 0<=confidence<=1):
            raise ValueError('Invalid confidence for '+sid)
        ordered.append({'sample_id':sid,'true_label':truth,'predicted_label':row['predicted_label'],
                        'correct':truth==row['predicted_label'],'confidence':confidence,
                        'source_scaled_pc_distance':distances[sid]})
    # Disjoint quartiles via stable sorting so tied distances do not create
    # undefined or arbitrary floating-point percentile boundaries.
    bydist=sorted(ordered,key=lambda r:(r['source_scaled_pc_distance'],r['sample_id']))
    summaries=[]
    for k,part in enumerate(np.array_split(np.arange(len(bydist)),4),1):
        chunk=[bydist[int(i)] for i in part]
        if not chunk:continue
        err=sum(not r['correct'] for r in chunk)
        cf=[r['confidence'] for r in chunk if r['confidence'] is not None]
        summaries.append({'distance_quartile':k,'n':len(chunk),'errors':err,
                          'error_rate':err/len(chunk),
                          'mean_confidence':float(np.mean(cf)) if cf else None,
                          'min_distance':chunk[0]['source_scaled_pc_distance'],
                          'max_distance':chunk[-1]['source_scaled_pc_distance']})
    return {'available':True,'n':len(ordered),'n_errors':sum(not r['correct'] for r in ordered),
            'error_by_source_distance_quartile':summaries,'sample_errors':[r for r in ordered if not r['correct']],
            'samples':ordered,
            'interpretation':'Exploratory descriptive association; source-fitted PC distance is not a calibrated error predictor or a causal explanation.'}


def analyze_shift(comp:Compatibility,classes=('normal','tumor'), prediction_rows=None)->dict[str,Any]:
    if comp.mode not in ('train_validate','diagnose_shift'):raise ValueError('Unsupported mode')
    sx,tx=_matrix(comp)
    mode=comp.mode
    pca,distances=_pca(sx,tx,comp.shared_features,comp.source.sample_ids,comp.target.sample_ids)
    inference_reasons=[]
    if any(i.code=='PROCESSING_DIFFERENCE' for i in comp.issues):
        inference_reasons.append('Processing declarations differ; directly comparable measurement scales are not established.')
    if set(comp.source.sample_ids)&set(comp.target.sample_ids) or any(i.code in ('PATIENT_OVERLAP','KNOWN_NONINDEPENDENCE') for i in comp.issues):
        inference_reasons.append('Known overlapping or dependent observations invalidate the independent-sample test.')
    for cohort in (comp.source,comp.target):
        patients=[cohort.metadata[s].get('patient_id') for s in cohort.sample_ids]
        known=[p for p in patients if p]
        if len(set(known))!=len(known) or any(cohort.metadata[s].get('pair_id') for s in cohort.sample_ids):
            inference_reasons.append(cohort.role+' contains repeated patients or declared pairs; clustered/paired inference is unsupported.')
    features=_rows(sx,tx,comp.shared_features,not inference_reasons)
    result={'stage':'07','science_version':VERSION,'mode':mode,'result_origin':'new_expression_computation',
            'data_type':'user_or_synthetic_expression_as_declared_in_manifests',
            'compatibility':comp.to_dict(),
            'feature_coverage':{'shared':len(comp.shared_features),
                                'source_only':len(comp.source.feature_ids)-len(comp.shared_features),
                                'target_only':len(comp.target.feature_ids)-len(comp.shared_features)},
            'gene_shifts':features,'pca':pca,
            'inference':{'available':not inference_reasons,'reasons':inference_reasons,
                         'note':'KS D, medians and source PCA describe deposited measurements. P/q values are withheld for incompatible processing or known dependence. Unknown independence remains a limitation, not an authenticated fact.'},
            'warnings':[{'code':i.code,'severity':i.severity,'message':i.message} for i in comp.issues],
            'interpretation':'Descriptive shift only; cohort differences do not establish causes of model errors, technical batch effects or biological mechanisms.'}
    if inference_reasons:
        result['warnings'].append({'code':'SHIFT_INFERENCE_WITHHELD','severity':'warning',
                                  'message':'P/q values withheld. '+' '.join(inference_reasons)})
    if mode=='train_validate':
        result['label_based_exploratory']={'class_composition':{
            'source':_class_composition(comp.source,classes),'target':_class_composition(comp.target,classes)},
            'class_conditioned':_class_conditioned(sx,tx,comp,classes),
            'note':'Target labels used for post-hoc diagnostic summaries only; no model fitting or method selection.'}
        result['error_association']=_prediction_associations(comp.target.sample_ids,distances,prediction_rows,mode,comp)
        if prediction_rows is not None:
            result['warnings'].append({'code':'ERROR_SHIFT_NONCAUSAL','severity':'warning',
              'message':'Observed errors and PCA distance may be associated; this analysis does not establish causation or model safety.'})
    elif prediction_rows is not None:
        raise ValueError('Shift-only mode cannot inspect labels, correctness or predictions')
    return result
