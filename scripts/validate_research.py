"""Recompute public evidence and numerical references; writes only under work/."""
from pathlib import Path
import csv, io, json, os, sys, time, uuid, zipfile
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'work'/('validation_'+uuid.uuid4().hex[:8])
OUT.mkdir(parents=True)
os.environ['BRACE_RUNS_DIR']=str(OUT/'runs')
import numpy as np
from scipy import stats, special
from fastapi.testclient import TestClient
from brace_app import server
from brace_core import signature
from brace_core.intake import parse_cohort

client=TestClient(server.app)
report={'scope':'Agent-run scientific and software verification; no clinical or human usability validation.',
        'output_directory':str(OUT.relative_to(ROOT)),'timings_seconds':{}}
def api(method,path,**kwargs):
    start=time.perf_counter();response=getattr(client,method)(path,**kwargs)
    report['timings_seconds'].setdefault(path,[]).append(time.perf_counter()-start)
    assert response.status_code==200,(path,response.status_code,response.text[:1000])
    return response

prepared=api('post','/api/datasets/reviewed-public',json={'reviewed':True}).json()
ids={r:d['id'] for r,d in prepared['datasets'].items()}
body={'name':'Verified public ER replication','mode':'race','datasets':ids,'race_config':prepared['race_config']}
assert api('post','/api/dataset-analysis/preflight',json=body).json()['eligible']
race=api('post','/api/dataset-analysis/run',json=body).json()
again=api('post','/api/dataset-analysis/run',json={**body,'study_id':race['study_id']}).json()
assert race['race']['hypothesis_hash']==again['race']['hypothesis_hash']
assert race['race']['aggregate']==again['race']['aggregate']
assert TestClient(server.app).get('/api/runs/'+race['id']).json()['race']==race['race']
bundle=api('get','/api/embrace/'+race['id']).content
with zipfile.ZipFile(io.BytesIO(bundle)) as z:
    assert json.loads(z.read('race/race_result.json'))==race['race']
    assert 'DATASET_LINEAGE.json' in z.namelist()
    assert json.loads(z.read('consistency_audit.json'))['status']=='PASS'
report['race']={'aggregate':race['race']['aggregate'],'counts':race['race']['counts'],
                'hypothesis_hash':race['race']['hypothesis_hash'],'repeat_and_reopen':'PASS','export_consistency':'PASS'}

p=ROOT/'examples/public_er_pair/prepared'
cohorts=[parse_cohort(p/f'{r}_expression.tsv',p/f'{r}_metadata.tsv',p/f'{r}_manifest.json',r) for r in ('source','target')]
s,t=cohorts;cfg=prepared['race_config'];snapshot=signature.discover(s,cfg)
frozen=json.loads(snapshot)
# Independent vectorized SciPy Welch implementation across all prepared source features.
def reference(c):
    pos=[i for i,sid in enumerate(c.sample_ids) if c.metadata[sid]['condition']==cfg['positive']]
    neg=[i for i,sid in enumerate(c.sample_ids) if c.metadata[sid]['condition']==cfg['negative']]
    ref=stats.ttest_ind(c.values[pos],c.values[neg],axis=0,equal_var=False)
    return ref,pos,neg
ref,ps,ns=reference(s)
# Match the declared conservative undefined-test rule, independently of BRACE.
usable=(np.var(s.values[ps],axis=0,ddof=1)>0)&(np.var(s.values[ns],axis=0,ddof=1)>0)
source_q=stats.false_discovery_control(np.where(usable,np.nan_to_num(ref.pvalue,nan=1.),1.))
max_p=0.;max_q=0.;max_g=0.
for row in frozen['screen']:
    j=s.feature_ids.index(row['feature_id'])
    if row['p'] is None:continue
    max_p=max(max_p,abs(row['p']-ref.pvalue[j]));max_q=max(max_q,abs(row['q']-source_q[j]))
    a=s.values[ps,j];b=s.values[ns,j];df=len(a)+len(b)-2
    correction=float(special.gamma(df/2)/(np.sqrt(df/2)*special.gamma((df-1)/2)))
    g=correction*(a.mean()-b.mean())/np.sqrt(((len(a)-1)*a.var(ddof=1)+(len(b)-1)*b.var(ddof=1))/df)
    max_g=max(max_g,abs(g-row['hedges_g']))
print('Independent reference maximum absolute errors:',max_p,max_q,max_g,flush=True)
assert max_p<1e-12 and max_q<1e-12 and max_g<1e-10
target_ref,pt,nt=reference(t)
target_p=[float(target_ref.pvalue[t.feature_ids.index(r['feature_id'])]) for r in race['race']['genes']]
target_q=stats.false_discovery_control(target_p)
for r,q in zip(race['race']['genes'],target_q):
    assert abs(r['q']-q)<1e-12
    j=t.feature_ids.index(r['feature_id'])
    ci=stats.ttest_ind(t.values[pt,j],t.values[nt,j],equal_var=False).confidence_interval()
    np.testing.assert_allclose(r['ci95'],ci,rtol=1e-10,atol=1e-12)
report['independent_references']={'source_features':len(frozen['screen']),'target_features':len(target_p),
    'max_absolute_p_error':float(max_p),'max_absolute_q_error':float(max_q),'max_absolute_hedges_error':float(max_g),
    'reference':'scipy.stats.ttest_ind and false_discovery_control; direct gamma-corrected pooled effect; target Welch intervals'}
report['selection_sensitivity']=[]
for cap in (5,20,50,100):
    start=time.perf_counter();result=signature.run(s,t,{**cfg,'selection_count':cap},OUT/f'cap_{cap}')
    report['selection_sensitivity'].append({'cap':cap,'aggregate':result['aggregate'],'seconds':time.perf_counter()-start})
# Fixed-source, target-label negative controls; not evidence of calibrated false positive rates.
rng=np.random.default_rng(20261104);labels=[t.metadata[sid]['condition'] for sid in t.sample_ids];controls=[]
for _ in range(10):
    perm=rng.permutation(labels)
    altered=replace(t,metadata={sid:{**t.metadata[sid],'condition':str(lab)} for sid,lab in zip(t.sample_ids,perm)})
    genes=signature.replicate(snapshot,altered,cfg)
    controls.append(sum(r['classification']=='supported_matching_direction' for r in genes))
report['target_label_permutations']={'seed':20261104,'replicates':10,'supported_counts':controls,'source_freeze_unchanged':signature.discover(s,cfg)==snapshot,'scope':'Exploratory negative control, not an empirical type-I-error validation.'}
reversed_source=replace(t,role='source',manifest={**t.manifest,'role':'source'})
reversed_target=replace(s,role='target',manifest={**s.manifest,'role':'target'})
reverse=signature.run(reversed_source,reversed_target,cfg,OUT/'reverse')
report['exploratory_role_reversal']=reverse['aggregate']

shift=api('post','/api/dataset-analysis/run',json={**body,'name':'ER deposited measurement comparison','mode':'diagnose_shift'}).json()
assert shift['shift']['inference']['available'] is False
assert all(g['ks_bh_q_exploratory'] is None for g in shift['shift']['gene_shifts'])
api('get','/api/embrace/'+shift['id'])
report['ce']={'p_values_withheld':True,'feature_count':len(shift['shift']['gene_shifts']),
              'reasons':shift['shift']['inference']['reasons'],'pca_available':shift['shift']['pca']['available'],'evidence_export':'PASS'}

folder=ROOT/'examples/cancershift_historical_cptac'
files={k:(name,(folder/name).read_bytes()) for k,name in [('predictions','predictions.tsv'),('prediction_manifest','manifest.json')]}
ace=api('post','/api/analyze',data={'mode':'evaluate_predictions','name':'CancerShift archived predictions - recomputed evaluation'},files=files).json()
rows=list(csv.DictReader((folder/'predictions.tsv').open(encoding='utf-8'),delimiter='\t'))
correct=lambda r:r['true_label']==r['predicted_label']
conf=lambda r:max(float(v) for k,v in r.items() if k.startswith('prob_'))
kept=[r for r in rows if conf(r)>=.95];errors=[r for r in rows if not correct(r)]
assert (len(rows),sum(map(correct,rows)),len(kept),sum(map(correct,kept)))==(680,668,584,583)
assert ace['validation']['metrics']['n_correct']==668
api('get','/api/embrace/'+ace['id'])
report['ace']={'n':680,'correct':668,'retained_095':584,'correct_retained':583,'excluded':96,
    'absent_true_classes':ace['validation']['metrics']['absent_true_classes'],
    'most_confident_error':{'true':max(errors,key=conf)['true_label'],'predicted':max(errors,key=conf)['predicted_label'],'score':conf(max(errors,key=conf))},
    'note':'Original model was not executed. Calibration summaries describe this archive; deployment calibration and patient independence are unverified.'}

synthetic=api('post','/api/demo/synthetic').json()
replay=api('post','/api/dataset-analysis/replay',json={'name':'Synthetic frozen replay','frozen_run_id':synthetic['id'],'target_dataset_id':synthetic['datasets']['target']}).json()
api('get','/api/embrace/'+replay['id'])
report['synthetic_baseline']={'source_training':'PASS','frozen_replay':'PASS','scope':'Artificial software fixture only, not biological validation.'}
report['software_versions']=__import__('brace_app.release09',fromlist=['package_versions']).package_versions()
report['status']='PASS'
(OUT/'validation.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
(ROOT/'work/research_validation.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2,allow_nan=False))
