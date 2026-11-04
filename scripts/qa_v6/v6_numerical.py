"""Independent calculations from actual prepared matrices and exported files."""
from pathlib import Path
import csv,hashlib,io,json,math,zipfile,warnings
import numpy as np
from scipy import stats
ROOT=Path(__file__).resolve().parents[2];APP=ROOT;OUT=APP/'docs/v6';pair=APP/'examples/public_er_pair'
def bh(p):
    ordered=sorted(enumerate(p),key=lambda x:(x[1],x[0]));q=[1.]*len(p);running=1.
    for rank in range(len(p),0,-1):
        index,value=ordered[rank-1];running=min(running,value*len(p)/rank);q[index]=running
    return q
def cohort(role):
    folder=pair/'prepared';metadata={r['sample_id']:r['condition'] for r in csv.DictReader((folder/(role+'_metadata.tsv')).open(),delimiter='\t')}
    with (folder/(role+'_expression.tsv')).open() as f:
        rd=csv.reader(f,delimiter='\t');header=next(rd);samples=header[1:];assert set(samples)==set(metadata);rows=sorted([(r[0],[float(v) for v in r[1:]]) for r in rd]);ids=[r[0] for r in rows];x=np.array([r[1] for r in rows])
    assert np.isfinite(x).all() and len(ids)==len(set(ids))==10000
    indices=sorted(range(len(samples)),key=lambda i:samples[i]);pos=[i for i in indices if metadata[samples[i]]=='ER_positive'];neg=[i for i in indices if metadata[samples[i]]=='ER_negative'];a=x[:,pos];b=x[:,neg]
    with warnings.catch_warnings():warnings.simplefilter('ignore');p=stats.ttest_ind(a,b,axis=1,equal_var=False).pvalue
    invalid=(np.ptp(a,axis=1)==0)|(np.ptp(b,axis=1)==0);p=np.where(invalid,1,p);assert np.isfinite(p).all();q=np.array(bh(p));effect=a.mean(axis=1)-b.mean(axis=1);n,m=len(pos),len(neg);d=n+m-2;j=math.exp(math.lgamma(d/2)-.5*math.log(d/2)-math.lgamma((d-1)/2));pooled=((n-1)*a.var(axis=1,ddof=1)+(m-1)*b.var(axis=1,ddof=1))/d
    with np.errstate(divide='ignore',invalid='ignore'):g=j*effect/np.sqrt(pooled)
    return dict(ids=ids,lookup={f:i for i,f in enumerate(ids)},p=p,q=q,effect=effect,g=g,invalid=invalid,samples=len(samples),positive=n,negative=m)
source,target=cohort('source'),cohort('target')
with zipfile.ZipFile(OUT/'after/public_fresh_evidence.zip') as z:
    result=json.loads(z.read('race/race_result.json'));frozen=json.loads(z.read('race/selected_signature.json'));rep=list(csv.DictReader(io.StringIO(z.read('race/replication_genes.csv').decode())))
    assert z.testzip() is None
    for r in csv.DictReader(io.StringIO(z.read('FILE_SHA256_MANIFEST.csv').decode())):assert hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256']
qualifying=[i for i in range(10000) if not source['invalid'][i] and source['q'][i]<=.05]
selected=sorted(qualifying,key=lambda i:(-abs(source['g'][i]),source['ids'][i]))[:20];ids=[source['ids'][i] for i in selected];assert ids==[g['feature_id'] for g in result['genes']]==[g['feature_id'] for g in frozen['selected']]
tp=[target['p'][target['lookup'][fid]] for fid in ids];tq=bh(tp);errors={'source_effect':0.,'source_q':0.,'target_effect':0.,'target_p':0.,'target_q':0.};counts={'supported_matching_direction':0,'matching_direction_without_support':0,'opposite_direction':0}
for k,(fid,row,flat) in enumerate(zip(ids,result['genes'],rep)):
    si=source['lookup'][fid];ti=target['lookup'][fid]
    for name,a,b in [('source_effect',source['effect'][si],row['source_effect']),('source_q',source['q'][si],row['source_q']),('target_effect',target['effect'][ti],row['effect']),('target_p',tp[k],row['p']),('target_q',tq[k],row['q'])]:
        errors[name]=max(errors[name],abs(a-b));assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-12),(fid,name,a,b)
    matching=np.sign(source['effect'][si])==np.sign(target['effect'][ti]);category='supported_matching_direction' if matching and tq[k]<=.05 else 'matching_direction_without_support' if matching else 'opposite_direction';counts[category]+=1;assert category==row['classification']==flat['classification']
assert list(counts.values())==[14,5,1] and len(qualifying)==1339 and sum(source['invalid'])==4
original=json.loads((pair/'race_final/selected_signature.json').read_text());different=[k for k in original if original[k]!=frozen[k]];assert set(different)=={'hypothesis_hash','software'},different
baseline=APP/'docs/v6/BASELINE_SCIENCE_SHA256.json';expected=json.loads(baseline.read_text());preserved={}
for prefix in ('brace_core/','examples/','tests/'):
 paths=[n for n in expected if n.startswith(prefix)]
 for name in paths:
  actual=hashlib.sha256((APP/name).read_bytes()).hexdigest()
  if actual!=expected[name]:
   patch=json.loads((APP/'docs/release/PORTABILITY_PATCH.json').read_text())['files'][name]
   assert patch['original_sha256']==expected[name] and patch['current_sha256']==actual,name
 preserved[prefix]=sum(hashlib.sha256((APP/name).read_bytes()).hexdigest()==expected[name] for name in paths)
receipt=dict(status='PASS',scope='Independently written SciPy ttest_ind and reverse-rank BH calculation from prepared matrices; not an external human scientific review',source={k:source[k] for k in ('samples','positive','negative')},target={k:target[k] for k in ('samples','positive','negative')},source_family=10000,source_untestable=4,source_q_passing=len(qualifying),selected=len(ids),outcomes=counts,maximum_absolute_discrepancy=errors,tolerances=dict(relative=1e-9,absolute=1e-12),frozen_differing_fields=different,original_software=original['software'],fresh_software=frozen['software'],preserved_baseline_files=preserved,baseline_source_snapshot_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest())
(APP/'docs/release/NUMERICAL_PRESERVATION.json').write_text(json.dumps(receipt,indent=2,default=lambda v:int(v) if isinstance(v,np.integer) else float(v))+'\n');print(json.dumps(receipt,default=lambda v:int(v) if isinstance(v,np.integer) else float(v)))
