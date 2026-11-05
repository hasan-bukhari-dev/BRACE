import csv
import io
import json
from dataclasses import replace
from pathlib import Path
import numpy as np
import pytest
from scipy import stats
from brace_core.contracts import Cohort
from brace_core import signature as race

CONFIG=dict(positive='positive',negative='negative',source_conditions={'positive':'ER positive tumor','negative':'ER negative tumor'},target_conditions={'positive':'ER positive tumor','negative':'ER negative tumor'})

@pytest.mark.parametrize('value',[0,1001,-1,True,1.5,'20',None])
def test_selection_count_rejects_invalid_values(value):
    with pytest.raises(ValueError,match='Selection count'):
        race.settings(dict(CONFIG,selection_count=value))

def test_explicit_cap_is_source_only_and_bound_to_freeze(tmp_path):
    s=cohort('source');t=cohort('target')
    cfg=dict(CONFIG,selection_count=1)
    frozen=race.discover(s,cfg)
    result=race.run(s,t,cfg,tmp_path/'one')
    assert result['aggregate']['selected']==1
    assert result['aggregate']['source_q_passing']==2
    assert result['selection_rule']['max_genes']==1
    assert result['method_version']=='brace-race/0.2.0'
    changed=replace(t,values=t.values*-2)
    race.run(s,changed,cfg,tmp_path/'changed')
    assert (tmp_path/'changed/selected_signature.json').read_bytes()==frozen
    with pytest.raises(ValueError,match='selection count'):
        race.replicate(frozen,t,CONFIG)
    assert race.discover(s,CONFIG)==race.discover(s,dict(CONFIG,selection_count=20))

def cohort(role,values=None,features=('a','b','noise')):
    values=np.array(values if values is not None else [[i+10,i+10,i%3] for i in range(6)]+[[i,i,i%3] for i in range(6)],dtype=float)
    ids=tuple(role+str(i).zfill(2) for i in range(len(values)))
    manifest=dict(schema_version='1.0.0',organism='Homo sapiens',role=role,feature_namespace='gene_symbol',measurement_type='microarray_log2_normalized',platform='GPL570',processing_description='log2 RMA',labels='binary',independence_declaration='unknown')
    return Cohort(role,role,ids,features,values,{s:{'condition':'positive' if i<6 else 'negative','patient_id':s,'study_id':role} for i,s in enumerate(ids)},manifest,{},())

def test_hand_welch_effect_hedges_bh():
    r=race.feature_test([3,4,5],[1,2,3])
    assert r['effect']==2
    assert r['t']==pytest.approx(np.sqrt(6))
    assert r['df']==pytest.approx(4)
    assert r['p']==pytest.approx(0.07048399691021993)
    assert r['hedges_g']==pytest.approx(2*np.sqrt(2/np.pi))
    assert r['ci95']==pytest.approx([2-2.7764451051977987*np.sqrt(2/3),2+2.7764451051977987*np.sqrt(2/3)])
    assert race.bh([.01,.04,.03,.2])==pytest.approx([.04,.05333333333333333,.05333333333333333,.2])
    assert race.bh([])==[]

def test_independent_scipy_reference():
    rng=np.random.default_rng(17)
    for _ in range(20):
        a=rng.normal(1,3,17);b=rng.normal(-1,1,9)
        ref=stats.ttest_ind(a,b,equal_var=False);actual=race.feature_test(a,b)
        assert actual['p']==pytest.approx(ref.pvalue,rel=1e-12)
        assert actual['t']==pytest.approx(ref.statistic,rel=1e-12)
        assert actual['ci95']==pytest.approx(ref.confidence_interval())
    p=rng.uniform(size=40).tolist()
    assert race.bh(p)==pytest.approx(stats.false_discovery_control(p))

def test_target_leakage_reordering_repeatability(tmp_path):
    s=cohort('source');t=cohort('target')
    before=race.discover(s,CONFIG)
    labels={sid:dict(row,condition='negative' if row['condition']=='positive' else 'positive') for sid,row in t.metadata.items()}
    changed=replace(t,metadata=labels)
    first=race.run(s,t,CONFIG,tmp_path/'a');second=race.run(s,changed,CONFIG,tmp_path/'b')
    assert before==race.discover(s,CONFIG)
    assert (tmp_path/'a/selected_signature.json').read_bytes()==(tmp_path/'b/selected_signature.json').read_bytes()
    assert first['aggregate']['supported']==2 and second['aggregate']['opposite']==2
    for c in (s,t):
        reversed_c=replace(c,sample_ids=c.sample_ids[::-1],feature_ids=c.feature_ids[::-1],values=c.values[::-1,::-1].copy())
        if c.role=='source':assert race.discover(reversed_c,CONFIG)==before
        else:assert race.replicate(before,reversed_c,CONFIG)==race.replicate(before,t,CONFIG)
    assert [r['feature_id'] for r in json.loads(before)['selected']]==['a','b']
    assert race.run(s,t,CONFIG,tmp_path/'c')==first

def test_zero_selection_and_untestable_target(tmp_path):
    s=cohort('source');t=cohort('target')
    zero=replace(s,values=np.tile(np.arange(6),2).reshape(12,1).astype(float),feature_ids=('x',))
    result=race.run(zero,replace(t,feature_ids=('x',),values=t.values[:,2:3].copy()),CONFIG,tmp_path/'zero')
    assert result['aggregate']['selected']==0 and result['aggregate']['direction_concordance'] is None
    missing=replace(t,feature_ids=('noise',),values=t.values[:,2:3].copy())
    r=race.run(s,missing,CONFIG,tmp_path/'missing')
    assert r['aggregate']['untestable']==2 and r['aggregate']['target_testable']==0
    assert all(g['reason']=='missing_target_feature' for g in r['genes'])

def test_partial_frozen_family_retains_missing_hypothesis(tmp_path):
    s=cohort('source');t=cohort('target')
    partial=replace(t,feature_ids=('a','noise'),values=t.values[:,[0,2]].copy())
    result=race.run(s,partial,CONFIG,tmp_path/'out')
    a,b=result['genes']
    assert a['q']==pytest.approx(min(2*a['p'],1))
    assert b['q'] is None and b['classification']=='untestable'
    assert result['aggregate']['direction_denominator']==1
    assert result['aggregate']['direction_concordance']==1

@pytest.mark.parametrize('a,b,reason',[([1,1],[2,2],'zero_within_group_variance'),([1,2],[2,2],'zero_within_group_variance'),([1],[2,3],'fewer_than_two_per_group')])
def test_undefined(a,b,reason):
    r=race.feature_test(a,b);assert r['reason']==reason and r['p'] is None

@pytest.mark.parametrize('change',[
    {'design':'paired'},{'covariates':['age']},{'evaluation_role':'external_locked'},
    {'positive':'negative'}, {'target_conditions':{'positive':'normal tissue','negative':'breast tumor'}},
    {'allow_processing_difference':'yes'}, {'unknown':True}])
def test_invalid_config(change):
    with pytest.raises(ValueError):race.settings(dict(CONFIG,**change))

@pytest.mark.parametrize('field,value', [('platform','GPL96'),('feature_namespace','entrez_gene'),('measurement_type','raw_counts'),('organism','Mus musculus'),('independence_declaration','not_independent')])
def test_invalid_cohorts(field,value,tmp_path):
    t=cohort('target');t=replace(t,manifest=dict(t.manifest,**{field:value}))
    with pytest.raises(race.RaceBlocked):race.run(cohort('source'),t,CONFIG,tmp_path/'out')
    assert not (tmp_path/'out').exists()

@pytest.mark.parametrize('case',['repeated','overlap','paired','confounding','bad_label','source_small'])
def test_design_attacks(case,tmp_path):
    s=cohort('source');t=cohort('target');md={k:dict(v) for k,v in s.metadata.items()}
    if case=='repeated':md[s.sample_ids[1]]['patient_id']=md[s.sample_ids[0]]['patient_id']
    if case=='overlap':md[s.sample_ids[0]]['patient_id']=t.sample_ids[0]
    if case=='paired':md[s.sample_ids[0]]['pair_id']='pair1'
    if case=='confounding':
        for r in md.values():r['study_id']=r['condition']
    if case=='bad_label':md[s.sample_ids[0]]['condition']='tumor'
    if case=='source_small':
        for i,r in enumerate(md.values()):r['condition']='positive' if i==0 else 'negative'
    s=replace(s,metadata=md)
    with pytest.raises(race.RaceBlocked):race.run(s,t,CONFIG,tmp_path/'out')

def test_processing_and_missing_class_and_denominators(tmp_path):
    s=cohort('source');t=cohort('target');t=replace(t,manifest=dict(t.manifest,processing_description='GC-RMA'))
    with pytest.raises(race.RaceBlocked):race.run(s,t,CONFIG,tmp_path/'blocked')
    cfg=dict(CONFIG,allow_processing_difference=True)
    result=race.run(s,t,cfg,tmp_path/'ok')
    assert result['evaluation_role']=='exploratory' and result['validated_evidence_claim'] is False
    assert result['aggregate']['direction_concordance']==1
    assert result['aggregate']['direction_denominator']==2
    assert any(w['code']=='PROCESSING_DIFFERENCE' for w in result['warnings'])
    missing=replace(t,metadata={k:dict(v,condition='positive') for k,v in t.metadata.items()})
    result=race.run(s,missing,cfg,tmp_path/'oneclass')
    assert result['aggregate']['target_testable']==0
    assert result['aggregate']['direction_concordance'] is None

def test_frozen_integrity_and_export(tmp_path):
    s=cohort('source');t=cohort('target');result=race.run(s,t,CONFIG,tmp_path/'out')
    snapshot=json.loads((tmp_path/'out/selected_signature.json').read_bytes());snapshot['positive']='tampered'
    with pytest.raises(ValueError,match='hash mismatch'):race.replicate(json.dumps(snapshot).encode(),t,CONFIG)
    rows=list(csv.DictReader((tmp_path/'out/replication_genes.csv').open()))
    assert len(rows)==result['aggregate']['selected']
    for r,g in zip(rows,result['genes']):assert float(r['p'])==g['p'] and r['classification']==g['classification']
    stream=tmp_path/'formula.csv';race.write_csv(stream,[{'feature_id':'=1+1','effect':-2.0}],['feature_id','effect'])
    row=next(csv.DictReader(stream.open()));assert row['feature_id']=="'=1+1" and row['effect']=='-2.0'

def api_files():
    root=Path(__file__).resolve().parents[1]/'examples/synthetic_valid'
    files={}
    for role in ('source','target'):
        for field,suffix in [('expression','expression.csv'),('metadata','samples.csv'),('manifest','manifest.json')]:
            name=f'{role}_{suffix}';data=(root/name).read_bytes()
            # Legacy synthetic fixture uses fictional GENE IDs while declaring Entrez.
            # Correct the declaration in this API-test copy; never modify archived fixtures.
            if field=='manifest':
                obj=json.loads(data);obj['feature_namespace']='gene_symbol';data=json.dumps(obj).encode()
            files[f'{role}_{field}']=(name,data)
    return files

def test_api_security_exports_reload_and_blocking(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from brace_app import server
    monkeypatch.setattr(server,'RUNS',tmp_path)
    client=TestClient(server.app)
    cfg=dict(positive='tumor',negative='normal',source_conditions={'tumor':'tumor tissue','normal':'normal tissue'},target_conditions={'tumor':'tumor tissue','normal':'normal tissue'})
    response=client.post('/api/race',data={'race_config':json.dumps(cfg)},files=api_files())
    assert response.status_code==200,response.text
    d=response.json();rid=d['id'];assert d['race']['eligible'] and d['kind']=='user_computed'
    assert client.get('/api/runs/'+rid).json()['race']==d['race']
    import zipfile
    bundle=zipfile.ZipFile(io.BytesIO(client.get(f'/api/runs/{rid}/bundle').content))
    assert 'race/race_result.json' in bundle.namelist()
    assert not any('input/' in f for f in bundle.namelist())
    assert json.loads(bundle.read('race/race_result.json'))==d['race']
    for name in race.FILES:assert client.get(f'/api/runs/{rid}/export/race/{name}').status_code==200
    assert client.get(f'/api/runs/{rid}/export/race/input.json').status_code==404
    assert client.get('/api/runs/not-a-run').status_code==404
    assert client.post('/api/race',data={'race_config':json.dumps(cfg)},files=api_files(),headers={'Origin':'https://evil.example'}).status_code==403
    cfg['design']='paired'
    response=client.post('/api/race',data={'race_config':json.dumps(cfg)},files=api_files());assert response.status_code==422
    # Persistent dataset records are separate from completed analysis directories.
    assert {path.name for path in tmp_path.iterdir()}=={rid,'_workspace'}
    cfg['design']='unpaired'
    monkeypatch.setattr(server,'MAX_FILE',10)
    assert client.post('/api/race',data={'race_config':json.dumps(cfg)},files=api_files()).status_code==413
    assert {path.name for path in tmp_path.iterdir()}=={rid,'_workspace'}
