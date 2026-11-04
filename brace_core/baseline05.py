"""Leakage-resistant binary source model and portable non-executable JSON freeze."""
from __future__ import annotations
import hashlib,json,math
from collections import Counter
from dataclasses import dataclass
import numpy as np
from scipy.special import expit
from sklearn.model_selection import StratifiedKFold, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from .contracts import Compatibility, Issue
from .intake import InputProblem
from .metrics05 import evaluate_labels

SCIENCE='brace-science/0.2.0'
SOFTWARE='brace-model/0.5.0'
SEED=42

def canonical_sha(payload:dict)->str:
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False,ensure_ascii=False).encode()).hexdigest()

def pipeline():
    return Pipeline([('variance',VarianceThreshold(threshold=0.0)),
       ('scale',StandardScaler()),
       ('model',LogisticRegression(C=1.0,class_weight='balanced',max_iter=2000,random_state=SEED))])

def _folds(y,groups):
    counts=Counter(y)
    if len(counts)!=2 or min(counts.values())<5:
        raise InputProblem('SOURCE_CV_UNSUPPORTED','Need at least 5 examples per source class','Provide more source samples','source.condition')
    nonempty=[g for g in groups if g]
    repeated=len(nonempty)!=len(set(nonempty))
    if not repeated:
        return list(StratifiedKFold(n_splits=5,shuffle=True,random_state=SEED).split(np.zeros(len(y)),y)),5,'StratifiedKFold'
    if any(not s for s in groups):
        raise InputProblem('SOURCE_CV_UNSUPPORTED','Repeated patients have missing group identifiers','Provide patient IDs for all source samples','source.patient_id')
    for k in (5,4,3):
        splitter=StratifiedGroupKFold(n_splits=k,shuffle=True,random_state=SEED)
        try: folds=list(splitter.split(np.zeros(len(y)),y,groups))
        except ValueError:continue
        if all(len(set(y[i] for i in train))==2 and len(set(y[i] for i in test))==2
               and set(groups[i] for i in train).isdisjoint(groups[i] for i in test) for train,test in folds):
            return folds,k,'StratifiedGroupKFold'
    raise InputProblem('SOURCE_CV_UNSUPPORTED','Cannot construct 3–5 independent, two-class patient-aware folds','Review patient groups and supply enough independent cases','source.patient_id')

def freeze_pipeline(fitted,features,classes,config):
    selector=fitted.named_steps['variance'];scaler=fitted.named_steps['scale'];mdl=fitted.named_steps['model']
    if not np.array_equal(mdl.classes_,np.array(sorted(classes))):
        raise RuntimeError('Model class mapping unexpectedly changed')
    model={'format':'brace-freeze-json/1.0.0','science_version':SCIENCE,'software_version':SOFTWARE,
           'classes':list(mdl.classes_), 'feature_ids':list(features),
           'variance_support_indices':np.flatnonzero(selector.get_support()).astype(int).tolist(),
           'scale_mean':scaler.mean_.astype(float).tolist(),'scale_scale':scaler.scale_.astype(float).tolist(),
           'coefficient':mdl.coef_.ravel().astype(float).tolist(),'intercept':float(mdl.intercept_[0]),
           'config':config,'config_sha256':canonical_sha(config),
           'warning':'Non-executable research baseline artifact, NOT a clinical model. Do not fit/adapt it to target data.'}
    model['model_sha256']=canonical_sha(model)
    return model

def predict_frozen(model:dict,X,features,require_hash:bool=True):
    if model.get('format')!='brace-freeze-json/1.0.0':raise ValueError('Unsupported model freeze format')
    if require_hash:
        got=model.get('model_sha256');raw={k:v for k,v in model.items() if k!='model_sha256'}
        if got!=canonical_sha(raw):raise ValueError('Frozen model integrity check failed')
    if list(features)!=model['feature_ids']:raise ValueError('Input feature identifiers/order do not match frozen feature contract')
    X=np.asarray(X,dtype=float)
    if X.ndim!=2 or X.shape[1]!=len(features) or not np.isfinite(X).all():raise ValueError('Invalid external matrix shape/values')
    ix=model['variance_support_indices'];mean=np.asarray(model['scale_mean'],dtype=float);scale=np.asarray(model['scale_scale'],dtype=float)
    coef=np.asarray(model['coefficient'],dtype=float)
    if len(ix)!=len(mean) or len(mean)!=len(scale) or len(coef)!=len(ix) or not len(ix) or any(scale<=0) or not np.isfinite(coef).all() or not np.isfinite(scale).all():
        raise ValueError('Corrupt frozen transformation or coefficients')
    values=(X[:,ix]-mean)/scale
    p1=expit(values@coef+float(model['intercept']))
    probs=np.column_stack((1-p1,p1))
    classes=model['classes']
    return np.asarray([classes[i] for i in np.argmax(probs,axis=1)]),probs

def train_baseline(compat:Compatibility,classes=('normal','tumor'),positive_class='tumor'):
    if compat.mode!='train_validate' or not compat.eligible:
        raise InputProblem('COMPATIBILITY_BLOCKED','Supervised compatibility gate did not pass','Resolve Stage 04 blocking issues before training','preflight')
    if len(classes)!=2 or len(set(classes))!=2 or positive_class not in classes:
        raise InputProblem('LABEL_MAPPING_INCONSISTENT','Invalid binary class order/positive class','Declare two distinct classes with positive_class member','classes')
    src=compat.source;tgt=compat.target
    features=compat.shared_features
    Xs=np.asarray(src.values[:,compat.source_indices],dtype=float)
    Xt=np.asarray(tgt.values[:,compat.target_indices],dtype=float)
    ys=np.asarray([src.metadata[s]['condition'] for s in src.sample_ids])
    # IMPORTANT: target labels are NOT fetched until after the frozen predictions exist.
    groups=[src.metadata[s].get('patient_id','') for s in src.sample_ids]
    folds,k,fold_kind=_folds(ys,groups)
    config={'science_version':SCIENCE,'classes':list(classes),'positive_class':positive_class,
      'seed':SEED,'cv_folds':k,'cv_method':fold_kind,
      'model':{'name':'LogisticRegression','penalty':'l2','C':1.0,'class_weight':'balanced','max_iter':2000},
      'preprocessing':['VarianceThreshold(0.0)','StandardScaler(source_only)'],
      'prediction_policy':'model_predict_argmax','primary_confidence_threshold':0.95,
      'shared_features_sha256':hashlib.sha256('\n'.join(features).encode()).hexdigest(),
      'source_input_sha256':{key:src.input_files[key]['sha256'] for key in sorted(src.input_files)},
      'target_labels_used_for_model_selection':False,
      'feature_namespace':src.manifest['feature_namespace'],'measurement_type':src.manifest['measurement_type'],
      'source_platform':src.manifest.get('platform',''),'source_processing_description':src.manifest['processing_description']}
    oof=np.empty(len(ys),dtype=object);oof_proba=np.full((len(ys),2),np.nan)
    seen=np.zeros(len(ys),dtype=bool);fold_id=np.zeros(len(ys),dtype=int)
    for index,(tr,te) in enumerate(folds,1):
        p=pipeline()
        try:p.fit(Xs[tr],ys[tr])
        except ValueError as ex:raise InputProblem('SOURCE_CV_UNSUPPORTED',f'CV pipeline failed: {ex}','Check feature variability and class balance','source') from ex
        model_classes=p.named_steps['model'].classes_
        if set(model_classes)!=set(classes):raise RuntimeError('Unexpected fold class universe')
        predicted=p.predict(Xs[te]);probs=p.predict_proba(Xs[te])
        order=[list(model_classes).index(c) for c in classes]
        oof[te]=predicted;oof_proba[te]=probs[:,order];fold_id[te]=index;seen[te]=True
    if not seen.all():raise RuntimeError('CV did not cover every source sample')
    fit=pipeline()
    try: fit.fit(Xs,ys)
    except ValueError as ex:raise InputProblem('SOURCE_CV_UNSUPPORTED',f'Final model fit failed: {ex}','Review source variation','source') from ex
    frozen=freeze_pipeline(fit,features,classes,config)
    # The model is now frozen; the target is transformed using source-only fitted parameters.
    predicted,rawproba=predict_frozen(frozen,Xt,features)
    oof_metrics=evaluate_labels(ys,oof,classes,oof_proba,threshold=.95)
    yt=[tgt.metadata[s]['condition'] for s in tgt.sample_ids]
    order=[list(frozen['classes']).index(c) for c in classes]
    target_probs=rawproba[:,order]
    target_metrics=evaluate_labels(yt,predicted,classes,target_probs,threshold=.95)
    return {'config':config,'frozen_model':frozen,'source_ids':src.sample_ids,
       'oof_true':ys.tolist(),'oof_pred':oof.tolist(),'oof_prob':oof_proba,'oof_fold':fold_id.tolist(),
       'source_metrics':oof_metrics,'target_ids':tgt.sample_ids,'target_true':yt,
       'target_pred':predicted.tolist(),'target_prob':target_probs,'target_metrics':target_metrics,
       'warnings':[i.to_dict() for i in compat.issues]}
