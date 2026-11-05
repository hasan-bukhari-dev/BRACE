import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import csv,hashlib,io,json,zipfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from brace_app import server,dataset_registry as registry,gene_info

ROOT=Path(__file__).resolve().parents[1]
import argparse
parser=argparse.ArgumentParser(description='Reproduce the specific public acceptance cases, not general dataset eligibility.')
parser.add_argument('--er-source',type=Path,required=True,help='Original GSE21653 gzip')
parser.add_argument('--normal-source',type=Path,required=True,help='Original GSE42568 gzip')
parser.add_argument('--target',type=Path,required=True,help='Original GSE20711 gzip')
parser.add_argument('--out',type=Path,required=True,help='New empty output directory')
args=parser.parse_args()
if args.out.exists() and any(args.out.iterdir()):raise ValueError('Use a new empty directory; existing data are preserved.')
server.RUNS=args.out.resolve()
client=TestClient(server.app)
receipts={}
def post(url,body):
    r=client.post(url,json=body)
    if r.status_code!=200:raise RuntimeError(str(r.status_code)+' '+r.text[:1000])
    return r.json()
def acquire(accession,path,sha):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
    return registry.register({'original':path},name=accession+' original',source={'type':'geo_public_acceptance','accession':accession,'url':f'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}'})
def prepare(record,role,field,mapping,cap=1000,reference=None):
    p=client.get('/api/datasets/'+record['id']+'/inspect').json()
    if field=='source_name':values=p['metadata']['!Sample_source_name_ch1'][0]
    else:values=next(row['values'] for row in p['phenotype_fields'] if row['name']==field)
    included={};excluded={}
    for sample,value in zip(p['sample_ids'],values):
        if value in mapping:included[sample]=mapping[value]
        else:excluded[sample]='Excluded: recorded phenotype '+value+' is outside the declared contrast.'
    processing='; '.join(dict.fromkeys(x for row in p['metadata']['!Sample_data_processing'] for x in row))
    manifest={'schema_version':'1.0.0','cohort_id':record['source']['accession'],'accession':record['source']['accession'],
      'role':role,'organism':'Homo sapiens','feature_namespace':'probe_id','platform':'GPL570',
      'measurement_type':'microarray_log2_normalized','processing_description':processing+'; normalized log2 convention declared from deposited methods, not reprocessed by BRACE.',
      'labels':'binary','independence_declaration':'unknown'}
    return post('/api/datasets/'+record['id']+'/prepare',{'name':record['source']['accession']+' '+field,'reviewed':True,'manifest':manifest,
       'condition_by_sample':included,'excluded_samples':excluded,'feature_policy':'source_features' if reference else 'identifier_panel' if field=='source_name' else 'source_variance',
       'source_feature_cap':cap,'feature_reference_dataset':reference})
def evidence(run):
    raw=client.get('/api/embrace/'+run['id']).content
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        m=json.loads(z.read('reproducibility_manifest.json'))
        for name,entry in m['artifact_sha256'].items():assert hashlib.sha256(z.read(name)).hexdigest()==entry['sha256']
    assert client.get('/api/runs/'+run['id']).status_code==200
    return len(m['artifact_sha256'])
source_sha='f13e3bf972bd92a6fd53a1fbe42ad7c84caf4651df3a5e836f70dd3b22b5e76f'
target_sha='14d4f4ae57234d1e8deaeed9131d40b98664866f462eaab2b0309a9f96e107c1'
a=acquire('GSE21653',args.er_source,source_sha)
b=acquire('GSE20711',args.target,target_sha)
source=prepare(a,'source','er ihc',{'1':'ER_positive','0':'ER_negative'},cap=5000)
target=prepare(b,'target','er status',{'1':'ER_positive','0':'ER_negative'},reference=source['id'])
definitions={'ER_positive':'Recorded estrogen-receptor-positive breast tumor','ER_negative':'Recorded estrogen-receptor-negative breast tumor'}
config={'positive':'ER_positive','negative':'ER_negative','source_conditions':definitions,'target_conditions':definitions,
  'selection_count':20,'allow_processing_difference':True,'evaluation_role':'exploratory','design':'unpaired','covariates':[]}
body={'name':'Additional public cohort: GSE21653 to GSE20711','mode':'race','datasets':{'source':source['id'],'target':target['id']},'race_config':config}
check=post('/api/dataset-analysis/preflight',body);assert check['eligible'],check
run=post('/api/dataset-analysis/run',body)
receipts['race']={'run':run['id'],'aggregate':run['race']['aggregate'],'source_samples':source['summary']['n_samples'],'target_samples':target['summary']['n_samples']}
genes=client.get('/api/race/studies/'+run['id']+'/genes').json()['genes']
for gene in genes:
    response=client.get('/api/race/studies/'+run['id']+'/gene',params={'feature_id':gene['feature_id']})
    assert response.status_code==200,response.text
    assert response.json()['cohorts']['source']['groups']
receipts['race']['face_features']=len(genes)
for gene in genes:
    context=post('/api/race/studies/'+run['id']+'/gene-context?feature_id='+gene['feature_id'],{})
    if context.get('biological_context'):
        receipts['gene']={'feature':gene['feature_id'],'symbol':context['biological_context']['current_symbol'],'source':context['biological_context']['source_url']};break
assert 'gene' in receipts
assert client.get('/api/trace/studies/'+run['id'],params={'feature_id':genes[0]['feature_id']}).status_code==200
receipts['race']['export_hashes']=evidence(run)
ce=post('/api/dataset-analysis/run',{'name':'Additional public CE','mode':'diagnose_shift','datasets':body['datasets']})
receipts['ce']={'run':ce['id'],'shared':ce['shift']['feature_coverage']['shared'],'inference':ce['shift']['inference'],'export_hashes':evidence(ce)}
normal_sha='43b93f72f1d81838dcd2a5b6ccc3bc1875e46230dad0d7346236773a99e32b76'
normal=acquire('GSE42568',args.normal_source,normal_sha)
train=prepare(normal,'source','source_name',{'Breast tissue, normal':'normal','Breast tissue, cancer':'tumor'},cap=1000)
test=prepare(b,'target','source_name',{'Breast tumor':'tumor','Normal breast tissue':'normal'},reference=train['id'])
baseline=post('/api/dataset-analysis/run',{'name':'Real breast-tissue baseline · exploratory','mode':'train_validate','datasets':{'source':train['id'],'target':test['id']}})
receipts['baseline']={'run':baseline['id'],'n':baseline['validation']['n'],'metrics':baseline['validation']['metrics'],'target_normal_count':2,'export_hashes':evidence(baseline)}
replay=post('/api/dataset-analysis/replay',{'name':'Real frozen baseline replay','frozen_run_id':baseline['id'],'target_dataset_id':test['id']})
receipts['replay']={'run':replay['id'],'export_hashes':evidence(replay)}
receipts['status']='PASS'
receipts['limitations']=['Exploratory post-hoc cohort choice; not independent prospective confirmation.','Declared processed measurement scale; no raw CEL reprocessing.','Only two target normal samples; no clinical validation.','Baseline uses a fixed identifier-hash panel; no expression values selected this panel. Its performance is not a full-transcriptome estimate.']
(server.RUNS/'ACCEPTANCE.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
print(json.dumps(receipts,indent=2))
