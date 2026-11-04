"""Small inspectable evaluation core; Stage 06 extends statistical reporting."""
from __future__ import annotations
from collections import Counter
from typing import Sequence
import numpy as np

def evaluate_labels(y_true:Sequence[str],y_pred:Sequence[str],classes:Sequence[str],probabilities:np.ndarray|None=None,threshold:float=.95)->dict:
    if len(y_true)!=len(y_pred) or len(y_true)==0: raise ValueError('Prediction lengths are empty or inconsistent')
    if len(set(classes))!=len(classes) or len(classes)<2:raise ValueError('Invalid class universe')
    if set(y_true)|set(y_pred) > set(classes):raise ValueError('Unknown label')
    confusion=[[sum(yt==a and yp==b for yt,yp in zip(y_true,y_pred)) for b in classes] for a in classes]
    per=[];observed=[]
    for idx,c in enumerate(classes):
        tp=confusion[idx][idx];support=sum(confusion[idx]);predicted=sum(row[idx] for row in confusion)
        precision=tp/predicted if predicted else None
        recall=tp/support if support else None
        denom=2*tp+predicted-tp+support-tp
        f1=2*tp/denom if support and denom else (0.0 if support else None)
        per.append({'class':c,'support':support,'predicted_count':predicted,'tp':tp,'precision':precision,'recall':recall,'f1':f1,
            'undefined_reasons':{'precision':'NO_PREDICTIONS' if precision is None else None,'recall':'NO_TRUE_SUPPORT' if recall is None else None,'f1':'NO_TRUE_SUPPORT' if f1 is None else None}})
        if support:observed.append(per[-1])
    n=len(y_true); correct=sum(a==b for a,b in zip(y_true,y_pred))
    result={'n':n,'n_correct':correct,'accuracy':correct/n,'class_order':list(classes),'confusion_matrix':confusion,
       'per_class':per,'observed_true_classes':[x['class'] for x in observed],
       'absent_true_classes':[x['class'] for x in per if x['support']==0],
       'supported_class_macro_f1':float(np.mean([x['f1'] for x in observed])),
       'balanced_accuracy_observed':float(np.mean([x['recall'] for x in observed])),
       'macro_denominator':len(observed),'comparison_scope':'limited_class_support' if len(observed)<len(classes) else 'all_declared_classes'}
    if probabilities is not None:
        p=np.asarray(probabilities,dtype=float)
        if p.shape!=(n,len(classes)) or not np.isfinite(p).all() or not 0<=threshold<=1:
            raise ValueError('Invalid probability array or threshold')
        conf=np.max(p,axis=1);kept=conf>=threshold
        count=int(kept.sum());retained_errors=int(sum(yt!=yp for i,(yt,yp) in enumerate(zip(y_true,y_pred)) if kept[i]))
        result['selective']={'threshold':float(threshold),'retained':count,'coverage':count/n,'retained_errors':retained_errors,
           'selective_accuracy':(count-retained_errors)/count if count else None,
           'undefined_reason':'EMPTY_RETAINED_SET' if count==0 else None,
           'interpretation':'Threshold is predeclared; model confidence is not clinically calibrated certainty.'}
    else:result['selective']=None
    return result
