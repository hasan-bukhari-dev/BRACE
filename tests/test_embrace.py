"""Independent package/report/reference checks and real security failure paths."""
import copy,csv,hashlib,io,json,math,os,shutil,subprocess,zipfile
import threading
from html.parser import HTMLParser
from pathlib import Path,PurePosixPath
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import numpy as np
import pytest
from scipy import stats
from fastapi.testclient import TestClient
from brace_app import server
from brace_app.evidence_audit import audit
from brace_app.export_safety import csv_bytes
from brace_core.intake import parse_cohort
from brace_core import signature
from brace_app.embrace import finalize
from test_evidence_api import upload_predictions
from test_race import cohort,CONFIG
from test_race import api_files

BASE=Path(__file__).resolve().parents[1];PAIR=BASE/'examples/public_er_pair'
@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'RUNS',tmp_path/'runs');server.RUNS.mkdir()
    return TestClient(server.app)

class Tables(HTMLParser):
    def __init__(self):super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='table':self.table=[]
        if tag=='tr':self.row=[]
        if tag in ('td','th'):self.cell=[]
    def handle_data(self,text):
        if self.cell is not None:self.cell.append(text)
    def handle_endtag(self,tag):
        if tag in ('td','th'):self.row.append(''.join(self.cell));self.cell=None
        if tag=='tr':self.table.append(self.row)
        if tag=='table':self.tables.append(self.table);self.table=None

def package(response):
    assert response.status_code==200,response.text
    z=zipfile.ZipFile(io.BytesIO(response.content));assert z.testzip() is None
    names=z.namelist();assert len(names)==len(set(names))
    assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n and ':' not in n for n in names)
    assert not any(n.startswith('input/') or n.endswith(('.pkl','.joblib','.exe','.env')) for n in names)
    for row in csv.DictReader(io.StringIO(z.read('FILE_SHA256_MANIFEST.csv').decode())):
        data=z.read(row['path']);assert hashlib.sha256(data).hexdigest()==row['sha256'] and len(data)==int(row['bytes'])
    manifest=json.loads(z.read('reproducibility_manifest.json'))
    for name,r in manifest['artifact_sha256'].items():assert hashlib.sha256(z.read(name)).hexdigest()==r['sha256']
    return z,manifest

def test_public_race_standalone_report_agrees_with_full_selected_family(client):
    response=client.get('/api/embrace/public_er_pass2');z,m=package(response)
    original=json.loads((PAIR/'race_final/race_result.json').read_text());result=json.loads(z.read('race/race_result.json'))
    assert result==original and m['data_origin']=='public_computed'
    assert (json.loads(z.read('compatibility_summary.json'))['counts'])==original['counts']
    exclusions=json.loads(z.read('warning_exclusion_records.json'))['preparation']
    assert exclusions['GSE42568']['included']==101 and exclusions['GSE20711']['included']==87
    html=z.read('research_summary.html').decode();parsed=Tables();parsed.feed(html)
    selected=next(t for t in parsed.tables if t[0][0]=='Rank')
    assert len(selected)==21
    frozen=json.loads(z.read('race/selected_signature.json'))
    for row,g,source in zip(selected[1:],original['genes'],frozen['selected']):
        assert (row[0],row[1])==(str(g['selection_rank']),g['feature_id'])
        for cell,value in zip(row[2:8],[g['source_effect'],source['p'],g['source_q'],g['effect'],g['p'],g['q']]):assert float(cell)==value
        assert row[8]==str(g['direction_agreement']) and row[9].startswith(g['classification'])
    assert 'normalized log-intensity' in html and 'not simultaneous' in html and 'GSE42568' in html and 'GSE20711' in html
    assert json.loads(z.read('consistency_audit.json'))['status']=='PASS'
    assert client.get('/api/embrace/public_er_pass2').content==response.content

def test_real_public_statistics_against_vectorized_scipy_and_independent_ranking():
    config=json.loads((PAIR/'race_config.json').read_text());result=json.loads((PAIR/'race_final/race_result.json').read_text())
    frozen=json.loads((PAIR/'race_final/selected_signature.json').read_text())
    cohorts=[parse_cohort(*(PAIR/f'prepared/{r}_{field}.{ext}' for field,ext in [('expression','tsv'),('metadata','tsv'),('manifest','json')]),r) for r in ('source','target')]
    source,target=cohorts
    def groups(c):return [c.values[[i for i,s in enumerate(c.sample_ids) if c.metadata[s]['condition']==label],:] for label in (config['positive'],config['negative'])]
    pos,neg=groups(source)
    # Honor the recorded eligibility policy: either constant group is untestable.
    # SciPy alone also tests a variable group against a constant group, which is
    # a different declared design and must not change this correction family.
    valid=(np.ptp(pos,axis=0)>0)&(np.ptp(neg,axis=0)>0)&(pos.var(axis=0,ddof=1)>0)&(neg.var(axis=0,ddof=1)>0)
    ref=stats.ttest_ind(pos[:,valid],neg[:,valid],axis=0,equal_var=False)
    pvalues=np.ones(len(source.feature_ids));pvalues[valid]=ref.pvalue;q=stats.false_discovery_control(pvalues)
    index={f:i for i,f in enumerate(source.feature_ids)}
    for row in frozen['screen']:
        i=index[row['feature_id']]
        if valid[i]:assert row['p']==pytest.approx(pvalues[i],rel=1e-9,abs=1e-14);assert row['q']==pytest.approx(q[i],rel=1e-9,abs=1e-14)
        else:assert row['p'] is None and row['q'] is None
    df=len(pos)+len(neg)-2;j=math.gamma(df/2)/(math.sqrt(df/2)*math.gamma((df-1)/2))
    g=(pos.mean(axis=0)-neg.mean(axis=0))/np.sqrt(((len(pos)-1)*pos.var(axis=0,ddof=1)+(len(neg)-1)*neg.var(axis=0,ddof=1))/df)*j
    ranked=sorted((source.feature_ids[i] for i in np.flatnonzero(q<=.05)),key=lambda f:(-abs(g[index[f]]),f))[:20]
    assert ranked==[r['feature_id'] for r in frozen['selected']]
    p,n=groups(target);ix=[target.feature_ids.index(f) for f in ranked];ref=stats.ttest_ind(p[:,ix],n[:,ix],axis=0,equal_var=False);q=stats.false_discovery_control(ref.pvalue)
    assert [r['p'] for r in result['genes']]==pytest.approx(ref.pvalue,rel=1e-9,abs=1e-14)
    assert [r['q'] for r in result['genes']]==pytest.approx(q,rel=1e-9,abs=1e-14)

def test_archived_model_package_metrics_and_error_survive_without_new_inference(client):
    z,m=package(client.get('/api/embrace/historical_cptac'));a=json.loads(z.read('validation/validation_result.json'))['analysis']
    assert m['data_origin']=='historical' and not m['model_frozen_before_external_evaluation']
    assert a['n']==680 and a['metrics']['n_correct']==668
    curve=next(p for p in a['threshold_curve'] if p['threshold']==.95);assert (curve['retained'],curve['correct'])==(584,583)
    html=z.read('research_summary.html').decode();parsed=Tables();parsed.feed(html)
    matrix=next(t for t in parsed.tables if t[0][0]=='True / Predicted')
    assert [[int(x) for x in row[1:]] for row in matrix[1:]]==a['metrics']['confusion_matrix']
    assert 'not new five-class model inference' in html and 'Source cross-validation is unavailable' in html
    assert '0.998692106' in html and 'prostate' in html and 'Unavailable' in html

def test_csv_formula_boundary_is_reversible_and_keeps_original_science(client):
    manifest=dict(schema_version='1.0.0',dataset_id='injection_fixture',model_id='none_executed',classes=['=A','@B'],probability_columns={},prediction_origin='external_model',evaluation_role='external_exploratory',independence_declaration='unknown',label_source_description='Security test')
    stream=io.StringIO(newline='');w=csv.writer(stream);w.writerow(['sample_id','study_id','true_label','predicted_label']);w.writerow(['=1+1','+study','=A','@B']);w.writerow(['-sample','@study','@B','@B'])
    r=client.post('/api/analyze',data={'mode':'evaluate_predictions'},files={'predictions':('scores.csv',stream.getvalue()),'prediction_manifest':('manifest.json',json.dumps(manifest))})
    assert r.status_code==200,r.text
    rid=r.json()['id'];z,m=package(client.get('/api/embrace/'+rid));raw=json.loads(z.read('validation/validation_result.json'))['analysis']
    assert raw['records'][0]['sample_id']=='-sample' or raw['records'][0]['sample_id']=='=1+1'
    encoding=json.loads(z.read('CSV_TEXT_ENCODING.json'))['changed_cells'];assert encoding
    for name,changes in encoding.items():
        rows=list(csv.reader(io.StringIO(z.read(name).decode())))
        for c in changes:assert rows[c['row']-1][c['column']-1]=="'"+c['original']
    saved=(server.RUNS/rid/'validation/sample_level.csv').read_bytes()
    published=client.get(f'/api/runs/{rid}/export/validation/sample_level.csv').content
    assert published==z.read('validation/sample_level.csv') and saved!=published
    assert any(r['sample_id']=='=1+1' for r in raw['records'])
    info=client.get('/api/ace/studies/'+rid).json()
    for artifact in info['artifacts']:
        response=client.get(artifact['url']);assert response.status_code==200,response.text
        assert hashlib.sha256(response.content).hexdigest()==artifact['sha256']

def test_numeric_signs_and_control_prefixed_text_are_not_confused():
    data=b'feature_id,effect,source_sign\n@bad,-2.5,-1\n =1+1,3,1\n'
    output,ledger=csv_bytes(data);rows=list(csv.reader(io.StringIO(output.decode())))
    assert rows[1]==["'@bad",'-2.5','-1'] and rows[2][0]=="' =1+1"
    assert len(ledger)==2

@pytest.mark.parametrize('changed',['validation/validation_result.json','validation/sample_level.csv','RESEARCH_PACKAGE.zip','input/predictions.csv','run.json'])
def test_mutated_completed_evidence_or_zip_blocks_export_without_repair(client,changed):
    run=upload_predictions(client);rid=run['id'];p=server.RUNS/rid/changed;modified=p.read_bytes()+b'\n';p.write_bytes(modified)
    r=client.get('/api/embrace/'+rid);assert r.status_code==409 and p.read_bytes()==modified
    assert client.get(f'/api/runs/{rid}/bundle').status_code==409
    assert client.get('/api/runs/'+rid).status_code==409

def test_unknown_files_raw_uploads_and_machine_paths_are_not_exported(client):
    run=upload_predictions(client);rid=run['id'];root=server.RUNS/rid
    (root/'.env').write_text('SECRET_SENTINEL=not_for_export');(root/'validation/private.csv').write_text('secret,sentinel')
    z,m=package(client.get('/api/embrace/'+rid))
    for name in z.namelist():
        assert 'SECRET_SENTINEL' not in z.read(name).decode('utf-8')
        assert str(root).encode() not in z.read(name)
    assert not any('predictions.csv'==Path(name).name for name in z.namelist())
    assert 'scientific_artifact_sha256' in m and 'CSV_TEXT_ENCODING.json' in z.namelist()

@pytest.mark.parametrize('attack',['correct','threshold'])
def test_independent_arithmetic_audit_rejects_fabricated_summary(client,attack):
    run=upload_predictions(client);root=server.RUNS/run['id'];doc=json.loads((root/'validation/validation_result.json').read_text())
    if attack=='correct':doc['analysis']['metrics']['n_correct']+=1
    else:doc['analysis']['threshold_curve'][0]['retained']-=1
    with pytest.raises(ValueError,match='Evidence consistency'):audit(root,validation=doc)

@pytest.mark.parametrize('extension',['.pkl','.joblib','.exe'])
def test_unsupported_model_execution_files_are_rejected_and_cleaned(client,extension):
    r=client.post('/api/analyze',data={'mode':'evaluate_predictions'},files={'predictions':('attack'+extension,b'not executable by BRACE'),'prediction_manifest':('x.json',b'{}')})
    assert r.status_code==422 and list(server.RUNS.iterdir())==[]

def test_binary_disguised_as_csv_is_rejected_and_cleaned(client):
    r=client.post('/api/analyze',data={'mode':'evaluate_predictions'},files={'predictions':('x.csv',b'\x80\x04\x00not-utf8'),'prediction_manifest':('x.json',json.dumps(dict(schema_version='1.0.0',dataset_id='test',model_id='test',classes=['A','B'],probability_columns={},prediction_origin='external_model',evaluation_role='external_exploratory',independence_declaration='unknown',label_source_description='test')))})
    assert r.status_code==422 and list(server.RUNS.iterdir())==[]

def test_actual_25_mib_limit_and_origins_hosts_paths(client):
    r=client.post('/api/analyze',data={'mode':'evaluate_predictions'},files={'predictions':('too-big.csv',b'x'*(25*1024*1024+1)),'prediction_manifest':('x.json',b'{}')})
    assert r.status_code==413 and list(server.RUNS.iterdir())==[]
    assert client.get('/api/health',headers={'Host':'evil.example'}).status_code==400
    assert client.post('/api/demo/synthetic',headers={'Origin':'null'}).status_code==403
    for path in ['/api/embrace/../private','/api/runs/not-a-run/bundle','/api/runs/'+'a'*32+'/export/report/..%2f.env']:
        assert client.get(path).status_code==404

def test_windows_junction_run_cannot_escape_run_root(client,tmp_path):
    target=tmp_path/'outside';target.mkdir();link=server.RUNS/('b'*32)
    if os.name=='nt':
        quote=lambda p:str(p).replace("'","''")
        result=subprocess.run(['powershell','-NoProfile','-Command',f"New-Item -ItemType Junction -Path '{quote(link)}' -Target '{quote(target)}' | Out-Null"],capture_output=True)
        assert result.returncode==0,result.stderr.decode(errors='replace')
    else:link.symlink_to(target,target_is_directory=True)
    assert client.get('/api/runs/'+link.name+'/bundle').status_code==404
    assert client.get('/api/embrace/'+link.name).status_code==404

def test_parallel_example_exports_are_identical(client):
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _:client.get('/api/embrace/public_er_pass2'),range(2)))
    assert all(r.status_code==200 for r in responses)
    assert responses[0].content==responses[1].content

def test_published_directory_junction_cannot_redirect_export(client,tmp_path):
    run=upload_predictions(client);root=server.RUNS/run['id'];(root/'embrace').rename(root/'original_publication')
    outside=tmp_path/'unrelated';outside.mkdir();sentinel=outside/'sentinel';sentinel.write_text('untouched')
    link=root/'embrace'
    if os.name=='nt':
        quote=lambda p:str(p).replace("'","''")
        result=subprocess.run(['powershell','-NoProfile','-Command',f"New-Item -ItemType Junction -Path '{quote(link)}' -Target '{quote(outside)}' | Out-Null"],capture_output=True)
        assert result.returncode==0
    else:link.symlink_to(outside,target_is_directory=True)
    assert client.get('/api/embrace/'+run['id']).status_code==409
    assert sentinel.read_text()=='untouched' and len(list(outside.iterdir()))==1

@pytest.mark.parametrize('case',['zero','missing','unsupported','opposite','constant_target'])
def test_inconclusive_race_packages_keep_exact_denominators(tmp_path,case):
    s=cohort('source');t=cohort('target')
    if case=='zero':s=replace(s,values=np.tile(np.arange(6),2).reshape(12,1).astype(float),feature_ids=('x',));t=replace(t,feature_ids=('x',),values=t.values[:,2:3].copy())
    if case=='missing':t=replace(t,feature_ids=('noise',),values=t.values[:,2:3].copy())
    if case=='unsupported':
        values=t.values.copy();values[:6,:2]=np.arange(6)[:,None]*5;values[6:,:2]=np.arange(6)[:,None]*5-.1;t=replace(t,values=values)
    if case=='opposite':t=replace(t,metadata={sid:dict(r,condition='negative' if r['condition']=='positive' else 'positive') for sid,r in t.metadata.items()})
    if case=='constant_target':t=replace(t,values=np.ones_like(t.values))
    root=tmp_path/case;result=signature.run(s,t,CONFIG,root/'race')
    (root/'run.json').write_text(json.dumps(dict(id='c'*32,mode='race',kind='user_computed',input_hashes={})))
    path=finalize(root)
    with zipfile.ZipFile(path) as z:
        assert json.loads(z.read('race/race_result.json'))==result
        assert json.loads(z.read('consistency_audit.json'))['status']=='PASS'
        if case=='zero':assert result['aggregate']['selected']==0 and result['aggregate']['direction_concordance'] is None
        if case in ('missing','constant_target'):assert result['aggregate']['target_testable']==0 and 'Unavailable' in z.read('research_summary.html').decode()
        if case=='unsupported':assert result['aggregate']['supported']==0 and all(g['classification']=='matching_direction_without_support' for g in result['genes'])
        if case=='opposite':assert result['aggregate']['opposite']==2

@pytest.mark.parametrize('task',['prediction','race','preflight'])
def test_long_science_work_does_not_block_local_requests(client,monkeypatch,task):
    from brace_app import study_api
    from brace_core import stage06_cli
    module,name=(stage06_cli,'evaluate_existing') if task=='prediction' else (signature,'run') if task=='race' else (study_api,'parse_cohort')
    original=getattr(module,name);started=threading.Event();release=threading.Event()
    def gated(*args,**kwargs):
        started.set();assert release.wait(8),'Test failed to release controlled work gate'
        return original(*args,**kwargs)
    monkeypatch.setattr(module,name,gated)
    cfg=dict(positive='tumor',negative='normal',source_conditions={'tumor':'tumor tissue','normal':'normal tissue'},target_conditions={'tumor':'tumor tissue','normal':'normal tissue'})
    with TestClient(server.app) as shared,ThreadPoolExecutor(max_workers=2) as pool:
        if task=='prediction':work=pool.submit(upload_predictions,shared)
        else:work=pool.submit(shared.post,'/api/race' if task=='race' else '/api/preflight',data={'race_config':json.dumps(cfg),**({'mode':'race'} if task=='preflight' else {})},files=api_files())
        try:
            assert started.wait(5),'Scientific operation was not reached'
            response=pool.submit(shared.get,'/api/health').result(timeout=2)
            assert response.status_code==200 and not release.is_set()
        finally:release.set()
        outcome=work.result(timeout=20)
        if task!='prediction':assert outcome.status_code==200,outcome.text
