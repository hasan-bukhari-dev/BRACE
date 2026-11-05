"""RACE 0.1: unpaired, exploratory processed-microarray association replication."""
from __future__ import annotations
import csv
import hashlib
import json
import platform
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import scipy
from scipy import stats, special
from .contracts import Issue
from .compatibility import evaluate_compatibility
from .intake import parse_cohort

VERSION='brace-race/0.1.0'
FILES=('race_result.json','source_gene_screen.csv','selected_signature.json','replication_genes.csv','race_methods.json')

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def issue(code,severity,message,field='race'):
    return Issue(code,severity,message,'Review study design, labels and provenance before rerunning.',field)

class RaceBlocked(ValueError):
    def __init__(self,issues):
        self.issues=issues
        super().__init__('; '.join(i.message for i in issues if i.severity=='block'))

def settings(config):
    allowed={'positive','negative','source_conditions','target_conditions','design','covariates','allow_processing_difference','evaluation_role','selection_count'}
    if not isinstance(config,dict) or set(config)-allowed:
        raise ValueError('Unsupported RACE configuration fields')
    c=dict(config)
    c.setdefault('design','unpaired');c.setdefault('covariates',[])
    c.setdefault('allow_processing_difference',False);c.setdefault('evaluation_role','exploratory')
    c.setdefault('selection_count',20)
    if type(c['selection_count']) is not int or not 1<=c['selection_count']<=1000:
        raise ValueError('Selection count must be an integer from 1 to 1000; this is an implementation limit, not a biological optimum')
    if c['design']!='unpaired' or c['covariates'] or c['evaluation_role']!='exploratory':
        raise ValueError('Only unpaired, unadjusted exploratory RACE is supported; locked claims are unavailable')
    if type(c['allow_processing_difference']) is not bool: raise ValueError('Processing acknowledgement must be boolean')
    a,b=c.get('positive'),c.get('negative')
    if not isinstance(a,str) or not isinstance(b,str) or not a.strip() or not b.strip() or a==b:
        raise ValueError('Declare distinct nonempty positive and negative conditions')
    for key in ('source_conditions','target_conditions'):
        d=c.get(key)
        if not isinstance(d,dict) or set(d)!={a,b} or any(not isinstance(v,str) or not v.strip() for v in d.values()):
            raise ValueError('Provide explicit biological definitions for both conditions in each cohort')
    if c['source_conditions']!=c['target_conditions'] or len(set(c['source_conditions'].values()))!=2:
        raise ValueError('Incompatible or indistinguishable phenotype definitions; no silent label remapping')
    return c

def cohort_issues(c,config,is_source):
    issues=[];labels=[c.metadata[s].get('condition','') for s in c.sample_ids]
    counts=Counter(labels);classes={config['positive'],config['negative']}
    if c.manifest['labels']!='binary' or set(labels)-classes:
        issues.append(issue('RACE_LABELS','block','Missing or contradictory phenotype labels'))
    if c.manifest['measurement_type']!='microarray_log2_normalized':
        issues.append(issue('RACE_SCALE','block','RACE 0.1 supports only declared processed log2 microarray intensities'))
    if c.manifest['organism']!='Homo sapiens':issues.append(issue('RACE_ORGANISM','block','Unsupported organism'))
    if is_source and any(counts[x]<2 for x in classes):issues.append(issue('SOURCE_GROUP_TOO_SMALL','block','Welch source screen requires at least two observations in each group'))
    if any(counts[x]<10 for x in classes):issues.append(issue('RACE_SMALL_GROUP','warning',f'{c.role} class support below 10: {dict(counts)}'))
    patients=[c.metadata[s].get('patient_id','') for s in c.sample_ids];known=[p for p in patients if p]
    if len(known)!=len(set(known)):issues.append(issue('RACE_REPEATED_PATIENT','block','Repeated subjects require an unsupported paired or clustered method'))
    # Explicit paired declarations in user metadata must not be ignored.
    if any(c.metadata[s].get('pair_id','') for s in c.sample_ids):issues.append(issue('RACE_PAIRED','block','Pair identifiers require a paired-design method'))
    bystudy=defaultdict(set)
    for s,lab in zip(c.sample_ids,labels):
        study=c.metadata[s].get('study_id','')
        if study:bystudy[study].add(lab)
    if len(bystudy)>1 and all(c.metadata[s].get('study_id','') for s in c.sample_ids) and all(len(v)==1 for v in bystudy.values()):
        issues.append(issue('RACE_CLASS_STUDY_CONFOUNDING','block','Condition and study are perfectly confounded'))
    if not np.isfinite(c.values).all():issues.append(issue('RACE_NONFINITE','block','Nonfinite expression values'))
    if np.isfinite(c.values).all() and np.max(np.abs(c.values))>1024:
        issues.append(issue('RACE_SCALE_RANGE','block','Declared log2 microarray values exceed the supported numeric range (-1024 to 1024); verify the assay and scale'))
    if c.manifest['feature_namespace']=='entrez_gene' and any(not f.isdigit() for f in c.feature_ids):
        issues.append(issue('RACE_MAPPING','block','Entrez IDs must be unambiguous numeric identifiers'))
    if any('///' in f for f in c.feature_ids):issues.append(issue('RACE_MAPPING','block','Ambiguous feature mapping is unsupported'))
    if len(set(c.sample_ids))!=len(c.sample_ids) or len(set(c.feature_ids))!=len(c.feature_ids):
        issues.append(issue('RACE_DUPLICATES','block','Duplicate sample or feature identifiers'))
    return issues

def eligibility(source,target,config):
    # Reuse assay/namespace/independence checks without importing model CV assumptions.
    comp=evaluate_compatibility(source,target,'diagnose_shift',scientific_role='unlabeled_shift_only')
    issues=list(comp.issues)+cohort_issues(source,config,True)+cohort_issues(target,config,False)
    if set(source.sample_ids)&set(target.sample_ids):issues.append(issue('RACE_SAMPLE_OVERLAP','block','Source and target sample identifiers overlap'))
    for i in tuple(issues):
        if i.code in ('PATIENT_OVERLAP','KNOWN_NONINDEPENDENCE'):
            issues.append(issue('RACE_NONINDEPENDENCE','block',i.message))
        if i.code=='PROCESSING_DIFFERENCE' and not config['allow_processing_difference']:
            issues.append(issue('RACE_PROCESSING_REVIEW','block','Different processing requires explicit exploratory acknowledgement'))
    issues.append(issue('EXPLORATORY_ONLY','warning','Acquisition, patient independence and phenotype equivalence are declarations, not authenticated facts. No locked or clinical validation claim.'))
    if any(i.severity=='block' for i in issues):raise RaceBlocked(issues)
    return issues

def bh(pvalues):
    """BH over the complete declared family; undefined p values enter as 1."""
    if not pvalues:return []
    p=np.array([1.0 if v is None else v for v in pvalues]);order=np.argsort(p,kind='stable');m=len(p)
    q=np.minimum.accumulate((p[order]*m/np.arange(1,m+1))[::-1])[::-1]
    out=np.empty(m);out[order]=np.minimum(q,1)
    return out.tolist()

def feature_test(positive,negative):
    a=np.asarray(positive,dtype=float);b=np.asarray(negative,dtype=float);n,m=len(a),len(b)
    out=dict(n_positive=n,n_negative=m,effect=None,hedges_g=None,t=None,df=None,p=None,ci95=None,reason=None)
    if min(n,m)<2:out['reason']='fewer_than_two_per_group';return out
    delta=float(a.mean()-b.mean());va=float(a.var(ddof=1));vb=float(b.var(ddof=1));se2=va/n+vb/m
    out['effect']=delta
    if not np.isfinite([delta,va,vb,se2]).all():out['reason']='numerical_overflow';return out
    if np.ptp(a)==0 or np.ptp(b)==0 or va==0 or vb==0:
        out['reason']='zero_within_group_variance';return out
    if se2<=0:out['reason']='undefined_standard_error';return out
    df=se2**2/((va/n)**2/(n-1)+(vb/m)**2/(m-1));t=delta/np.sqrt(se2)
    pooled=((n-1)*va+(m-1)*vb)/(n+m-2);d=n+m-2
    j=float(np.exp(special.gammaln(d/2)-.5*np.log(d/2)-special.gammaln((d-1)/2)))
    margin=float(stats.t.ppf(.975,df)*np.sqrt(se2))
    out.update(hedges_g=float(j*delta/np.sqrt(pooled)),t=float(t),df=float(df),p=float(2*stats.t.sf(abs(t),df)),ci95=[delta-margin,delta+margin])
    return out

def screen(cohort,config):
    ordered=sorted(range(len(cohort.sample_ids)),key=lambda i:cohort.sample_ids[i])
    a=[i for i in ordered if cohort.metadata[cohort.sample_ids[i]].get('condition')==config['positive']]
    b=[i for i in ordered if cohort.metadata[cohort.sample_ids[i]].get('condition')==config['negative']]
    rows=[]
    for j in sorted(range(len(cohort.feature_ids)),key=lambda i:cohort.feature_ids[i]):
        rows.append(dict(feature_id=cohort.feature_ids[j],**feature_test(cohort.values[a,j],cohort.values[b,j])))
    for r,q in zip(rows,bh([r['p'] for r in rows])):r['q']=q if r['p'] is not None else None
    return rows

def discover(source,config):
    """Accepts no target cohort. Immutable JSON snapshot returned as bytes."""
    config=settings(config);issues=cohort_issues(source,config,True)
    if any(i.severity=='block' for i in issues):raise RaceBlocked(issues)
    rows=screen(source,config)
    qualifying=sorted((r for r in rows if r['q'] is not None and r['q']<=.05 and r['hedges_g'] is not None),key=lambda r:(-abs(r['hedges_g']),r['feature_id']))
    limit=config['selection_count']
    ranks={r['feature_id']:i+1 for i,r in enumerate(qualifying[:limit])}
    for r in rows:r.update(selected=r['feature_id'] in ranks,selection_rank=ranks.get(r['feature_id']))
    frozen=dict(method_version=VERSION if limit==20 else 'brace-race/0.2.0',source_id=source.cohort_id,source_input_hashes=source.input_files,
        source_sample_ids=sorted(source.sample_ids),source_patient_ids=sorted({source.metadata[s].get('patient_id','') for s in source.sample_ids}-{''}),
        positive=config['positive'],negative=config['negative'],condition_definitions=config['source_conditions'],
        selection_rule=dict(source_bh_q_max=.05,max_genes=limit,rank='descending absolute Hedges g, then feature ID'),
        screened_family=[r['feature_id'] for r in rows],screen=rows,
        selected=[dict(r,source_sign=int(np.sign(r['effect']))) for r in qualifying[:limit]],
        source_manifest=source.manifest,software=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
        random_seed=None)
    frozen['hypothesis_hash']=digest(frozen)
    return json.dumps(frozen,sort_keys=True,allow_nan=False).encode()

def replicate(snapshot,target,config):
    frozen=json.loads(snapshot);claim=frozen.pop('hypothesis_hash')
    if digest(frozen)!=claim:raise ValueError('Frozen hypothesis hash mismatch')
    config=settings(config)
    if config['selection_count']!=frozen['selection_rule']['max_genes']:
        raise ValueError('Target selection count differs from the frozen source rule')
    if any(frozen[k]!=config[k] for k in ('positive','negative')) or frozen['condition_definitions']!=config['source_conditions']:
        raise ValueError('Target testing configuration differs from frozen contrast')
    issues=cohort_issues(target,config,False)
    for key in ('platform','feature_namespace','measurement_type','organism'):
        if target.manifest.get(key)!=frozen['source_manifest'].get(key):issues.append(issue('RACE_FROZEN_ASSAY','block','Target assay or feature definitions differ from frozen source'))
    if set(target.sample_ids)&set(frozen['source_sample_ids']) or set(frozen['source_patient_ids'])&{target.metadata[s].get('patient_id','') for s in target.sample_ids}:
        issues.append(issue('RACE_FROZEN_OVERLAP','block','Target samples or patients overlap frozen source'))
    if target.manifest.get('independence_declaration')=='not_independent':issues.append(issue('RACE_NONINDEPENDENCE','block','Target declares nonindependence'))
    if target.manifest['processing_description']!=frozen['source_manifest']['processing_description'] and not config['allow_processing_difference']:
        issues.append(issue('RACE_PROCESSING_REVIEW','block','Different target processing requires exploratory acknowledgement'))
    if any(i.severity=='block' for i in issues):raise RaceBlocked(issues)
    # Only frozen genes are evaluated; target availability cannot alter selection.
    ids={f:i for i,f in enumerate(target.feature_ids)}
    order=sorted(range(len(target.sample_ids)),key=lambda i:target.sample_ids[i])
    a=[i for i in order if target.metadata[target.sample_ids[i]]['condition']==config['positive']]
    b=[i for i in order if target.metadata[target.sample_ids[i]]['condition']==config['negative']]
    rows=[]
    for s in frozen['selected']:
        f=s['feature_id']
        result=feature_test(target.values[a,ids[f]],target.values[b,ids[f]]) if f in ids else dict(n_positive=len(a),n_negative=len(b),effect=None,hedges_g=None,t=None,df=None,p=None,ci95=None,reason='missing_target_feature')
        rows.append(dict(feature_id=f,source_effect=s['effect'],source_q=s['q'],source_sign=s['source_sign'],selection_rank=s['selection_rank'],hypothesis_hash=claim,**result))
    # Full frozen family is retained; unavailable tests enter as p=1 conservatively.
    for r,q in zip(rows,bh([r['p'] for r in rows])):
        r['q']=q if r['p'] is not None else None
        r['direction_agreement']=bool(np.sign(r['effect'])==r['source_sign']) if r['p'] is not None and r['effect']!=0 else None
        r['classification']=('untestable' if r['p'] is None else 'indeterminate' if r['direction_agreement'] is None else
            'opposite_direction' if not r['direction_agreement'] else 'supported_matching_direction' if q<=.05 else 'matching_direction_without_support')
    return rows

def write_json(path,obj):path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')

def write_csv(path,rows,fields):
    with path.open('w',newline='',encoding='utf-8') as stream:
        w=csv.DictWriter(stream,fieldnames=fields);w.writeheader()
        for row in rows:
            safe={k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in row.items()}
            # Protect exported text against spreadsheet formula interpretation.
            safe={k:("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v) for k,v in safe.items()}
            w.writerow(safe)

def run(source,target,config,out):
    config=settings(config);issues=eligibility(source,target,config)
    snapshot=discover(source,config)
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    # Persist the frozen source evidence before any target statistic is computed.
    (out/'selected_signature.json').write_bytes(snapshot)
    genes=replicate(snapshot,target,config);frozen=json.loads(snapshot)
    testable=[r for r in genes if r['p'] is not None];matching=sum(r['direction_agreement'] is True for r in testable)
    aggregate=dict(source_features_screened=len(frozen['screen']),source_q_passing=sum(r['q'] is not None and r['q']<=.05 for r in frozen['screen']),
        selected=len(genes),target_testable=len(testable),direction_matching=matching,
        direction_concordance=matching/len(testable) if testable else None,direction_denominator=len(testable),
        supported=sum(r['classification']=='supported_matching_direction' for r in genes),
        opposite=sum(r['classification']=='opposite_direction' for r in genes),
        not_statistically_supported=sum(r['q']>.05 for r in testable),untestable=len(genes)-len(testable),
        indeterminate=sum(r['classification']=='indeterminate' for r in genes))
    methods=dict(version=frozen['method_version'],config=config,source_family_size=len(frozen['screen']),target_family_size=len(genes),
        selection_rule=frozen['selection_rule'],
        selection_interpretation='Selection count is a declared source-only cap, not a biological optimum or display limit. Sensitivity runs after viewing the target remain exploratory; do not select a favorable cap as independent confirmation.',
        undefined_tests='p=1 for family correction, q=null in displayed row; never selected or supported',
        test='Two-sided Welch t; unpaired, unadjusted; minimum 2/group; either zero within-group variance is untestable',
        effect='positive-group mean minus negative-group mean in deposited normalized log-intensity units; not labeled log2 fold change',
        standardized='Hedges g: pooled sample SD and exact gamma bias correction; descriptive under unequal variance',
        ci='Pointwise 95% Welch t interval on within-cohort mean difference, not simultaneous or selection-adjusted',
        multiplicity='BH across entire source family and entire frozen target family including untestable hypotheses as p=1; BH assumes independence or suitable positive dependence',
        independence='Unverified declarations remain exploratory; repeated patients, overlap and paired designs blocked',
        software=frozen['software'],source_manifest=source.manifest,target_manifest=target.manifest,
        input_files=dict(source=source.input_files,target=target.input_files),source_hypothesis_hash=frozen['hypothesis_hash'])
    result=dict(method_version=frozen['method_version'],status='completed_with_warnings' if issues else 'completed',eligible=True,
        selection_rule=frozen['selection_rule'],
        evaluation_role='exploratory',validated_evidence_claim=False,hypothesis_hash=frozen['hypothesis_hash'],
        positive=config['positive'],negative=config['negative'],aggregate=aggregate,source_screen=frozen['screen'],genes=genes,
        warnings=[i.to_dict() for i in issues],input_files=methods['input_files'],
        counts={c.role:dict(samples=len(c.sample_ids),features=len(c.feature_ids),conditions=dict(Counter(c.metadata[s].get('condition','') for s in c.sample_ids)),patient_ids_available=sum(bool(c.metadata[s].get('patient_id')) for s in c.sample_ids)) for c in (source,target)},
        interpretation='Exploratory cross-study association support, not locked validation, biomarker certification, causality or model transfer. Lack of significance does not establish absence of effect.')
    shared=len(set(source.feature_ids)&set(target.feature_ids))
    result['feature_coverage']=dict(shared=shared,source_total=len(source.feature_ids),target_total=len(target.feature_ids),source_fraction=shared/len(source.feature_ids),target_fraction=shared/len(target.feature_ids))
    result['source_untestable']=[dict(feature_id=r['feature_id'],reason=r['reason']) for r in frozen['screen'] if r['p'] is None]
    write_json(out/'race_result.json',result);write_json(out/'race_methods.json',methods)
    write_csv(out/'source_gene_screen.csv',frozen['screen'],list(frozen['screen'][0]) if frozen['screen'] else ['feature_id'])
    write_csv(out/'replication_genes.csv',genes,list(genes[0]) if genes else ['feature_id','classification'])
    return result

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--prepared',type=Path,required=True);ap.add_argument('--config',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();p=args.prepared
    cohorts=[parse_cohort(p/f'{r}_expression.tsv',p/f'{r}_metadata.tsv',p/f'{r}_manifest.json',r) for r in ('source','target')]
    result=run(*cohorts,json.loads(args.config.read_text(encoding='utf-8')),args.out)
    print(json.dumps(result['aggregate'],indent=2))
