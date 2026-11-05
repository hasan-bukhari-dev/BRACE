"""Headless acceptance of the downloaded release, not a rendered UI check."""
import argparse,hashlib,io,json,os,socket,subprocess,time,urllib.request,urllib.parse,uuid,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('app',type=Path);p.add_argument('out',type=Path);p.add_argument('--offline-reference',action='store_true',help='Use a labelled controlled reference fixture instead of requiring NCBI availability');args=p.parse_args()
app=args.app.resolve(strict=True);out=args.out.resolve()
if out.exists() and any(out.iterdir()):raise ValueError('Use a new empty output directory.')
out.mkdir(parents=True,exist_ok=True)
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','BRACE_PORT','BRACE_RUNS_DIR','BRACE_DATA_DIR']}
env.update(BRACE_PORT=str(port),BRACE_RUNS_DIR=str(out/'runs'),BRACE_DATA_DIR=str(out/'data'),BRACE_NO_BROWSER='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
base='http://127.0.0.1:'+str(port)
def request(path,body=None,raw=None,content_type=None):
    data=raw if raw is not None else json.dumps(body).encode() if body is not None else None
    headers={'Content-Type':content_type or 'application/json'} if data is not None else {}
    req=urllib.request.Request(base+path,data=data,headers=headers)
    with urllib.request.urlopen(req,timeout=240) as response:
        result=response.read()
        return json.loads(result) if response.headers.get_content_type()=='application/json' else result
def multipart(path,file,mapping=None):
    boundary=uuid.uuid4().hex
    body=(f'--{boundary}\r\nContent-Disposition: form-data; name="table"; filename="new_predictions.csv"\r\nContent-Type: text/csv\r\n\r\n').encode()+file+b'\r\n'
    if mapping is not None:body+=(f'--{boundary}\r\nContent-Disposition: form-data; name="mapping"\r\n\r\n').encode()+json.dumps(mapping).encode()+b'\r\n'
    body+=(f'--{boundary}--\r\n').encode()
    return request(path,raw=body,content_type='multipart/form-data; boundary='+boundary)
log=(out/'server.log').open('w')
process=subprocess.Popen([str(app),'--headless'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
try:
    deadline=time.monotonic()+90
    while True:
        if process.poll() is not None:raise RuntimeError('Executable exited: '+(out/'server.log').read_text(errors='replace'))
        try:health=request('/api/health');break
        except OSError:
            if time.monotonic()>deadline:raise
            time.sleep(.2)
    assert health['version']==Path(__file__).resolve().parents[1].joinpath('VERSION').read_text().strip()
    assert b'identifier_panel' in request('/assets/js/preparation.js')
    assert b'prediction-map-form' in request('/assets/js/workspace-tools.js')
    table=b'case,observed,called,pA,pB\na,alpha,alpha,0.9,0.1\nb,beta,alpha,0.6,0.4\nc,beta,beta,0.2,0.8\n'
    assert multipart('/api/predictions/inspect',table)['count']==3
    mapping={'name':'ARTIFICIAL software QA mapped predictions','model_id':'Technical fixture, not biological evidence','label_source_description':'Controlled software-check labels',
        'classes':['alpha','beta'],'probability_columns':{'alpha':'pA','beta':'pB'},'sample_id':'case','true_label':'observed','predicted_label':'called','reviewed':True}
    predictions=multipart('/api/predictions/import',table,mapping)
    ace=request('/api/dataset-analysis/run',{'name':'ARTIFICIAL software QA ACE mapped input','mode':'evaluate_predictions','datasets':{'predictions':predictions['id']}})
    assert ace['validation']['n']==3 and ace['validation']['metrics']['n_correct']==2
    pair=request('/api/datasets/reviewed-public',{'reviewed':True})
    datasets={'source':pair['datasets']['target']['id'],'target':pair['datasets']['source']['id']}
    ce=request('/api/dataset-analysis/run',{'name':'Real reversed-role CE','mode':'diagnose_shift','datasets':datasets})
    assert ce['shift']['feature_coverage']['shared']==10000 and not ce['shift']['inference']['available']
    race=request('/api/dataset-analysis/run',{'name':'Exploratory reciprocal public RACE','mode':'race','datasets':datasets,'race_config':pair['race_config']})
    gene_data=request('/api/race/studies/'+race['id']+'/genes');genes=gene_data['genes']
    if args.offline_reference:
        selected=next(g for g in genes if not g.get('biological_context'))
        key=hashlib.sha256(json.dumps([selected['feature_id'],selected['feature_namespace'],gene_data['cohorts']['source']['platform']]).encode()).hexdigest()
        reference={'feature_id':selected['feature_id'],'feature_namespace':selected['feature_namespace'],'status':'resolved','entrez_id':selected['feature_id'],
          'gene_symbol':'CONTROLLED_REFERENCE','biological_context':{'current_symbol':'CONTROLLED_REFERENCE','name':'Offline software-check reference',
          'function_excerpt':'Controlled fixture, not biological evidence or an NCBI response.','source_url':'https://example.invalid/software-fixture',
          'retrieved_date':'controlled fixture','source_snapshot_sha256':'a'*64,'note':'Software test only.'}}
        folder=out/'runs/_annotations';folder.mkdir(exist_ok=True)
        envelope={'record':reference,'sha256':hashlib.sha256(json.dumps(reference,sort_keys=True).encode()).hexdigest()}
        (folder/(key+'.json')).write_text(json.dumps(envelope),encoding='utf-8')
    enriched=None
    for gene in [g for g in genes if not g.get('biological_context')]:
        annotation=request('/api/race/studies/'+race['id']+'/gene-context?'+urllib.parse.urlencode({'feature_id':gene['feature_id']}),{})
        if annotation.get('biological_context'):
            enriched=(gene['feature_id'],annotation);break
    assert enriched,'No non-catalog selected gene could be resolved.'
    feature,annotation=enriched
    detail=request('/api/race/studies/'+race['id']+'/gene?'+urllib.parse.urlencode({'feature_id':feature}))
    assert detail['feature']['biological_context']['current_symbol']
    assert request('/api/trace/studies/'+race['id']+'?'+urllib.parse.urlencode({'feature_id':feature}))
    raw=request('/api/embrace/'+race['id'])
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('reproducibility_manifest.json'))
        for name,entry in manifest['artifact_sha256'].items():assert hashlib.sha256(z.read(name)).hexdigest()==entry['sha256']
        context=json.loads(z.read('BIOLOGICAL_CONTEXT.json'))[feature]
        assert context['identifier_mapping']['feature_id']==feature
    backup=request('/api/workspace/backup',{})
    with zipfile.ZipFile(io.BytesIO(request(backup['url']))) as z:
        m=json.loads(z.read('BACKUP_MANIFEST.json'))
        assert any(name.startswith('_annotations/') for name in z.namelist())
        for name,sha in m['sha256'].items():assert hashlib.sha256(z.read(name)).hexdigest()==sha
    receipt={'status':'PASS','version':health['version'],'executable_sha256':hashlib.sha256(app.read_bytes()).hexdigest(),
        'unfamiliar_prediction_columns':{'n':3,'correct':2,'scope':'Explicit artificial software fixture'},
        'real_reversed_role_ce':True,'reciprocal_race_aggregate':race['race']['aggregate'],
        'non_catalog_gene':{'feature_id':feature,'symbol':annotation['biological_context']['current_symbol'],'source_url':annotation['biological_context']['source_url']},
        'face_trace_and_export_mapping':True,'private_backup_all_recorded_hashes':True,'cached_references_in_backup':True,
        'reference_provider':'controlled offline fixture' if args.offline_reference else 'live NCBI Gene',
        'scope':'Actual Windows headless executable; not a rendered visual, independent human or clinical acceptance test.'}
    (out/'BINARY_NON_DEMO_ACCEPTANCE.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))
finally:
    process.terminate()
    try:process.wait(timeout=20)
    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
    log.close()
