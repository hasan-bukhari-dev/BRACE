"""Explicit public GEO metadata discovery and bounded public matrix acquisition.
No uploaded data are read or transmitted. Metadata never grants scientific eligibility.
"""
from __future__ import annotations
import hashlib,json,re,threading,time,uuid,urllib.parse,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
from html.parser import HTMLParser
from typing import Literal
from fastapi import APIRouter,HTTPException
from fastapi.responses import FileResponse,Response
from pydantic import BaseModel,ConfigDict,Field
from brace_app.persistence import atomic_json
router=APIRouter();_lock=threading.Lock();_last=0.;TTL=86400;MAX_DOWNLOAD=25*1024*1024
# Reviewed demonstration original, 25.65 MiB. This exception permits only the
# exact pinned bytes from the exact verified official URL, never a larger file.
REVIEWED_OVERSIZE={
 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE20nnn/GSE20711/matrix/GSE20711_series_matrix.txt.gz':
 {'bytes':26895121,'sha256':'14d4f4ae57234d1e8deaeed9131d40b98664866f462eaab2b0309a9f96e107c1'}}
POLICY='https://www.ncbi.nlm.nih.gov/home/about/policies/'
class Query(BaseModel):
 model_config=ConfigDict(extra='forbid')
 question:str=Field(min_length=3,max_length=180)
 tissue:str=Field(default='',max_length=80)
 organism:Literal['Homo sapiens','Mus musculus']='Homo sapiens'
 assay:Literal['microarray','rnaseq','any']='microarray'
 task:Literal['race','train_validate','diagnose_shift']='race'
 refresh:bool=False
class Acquisition(BaseModel):
 model_config=ConfigDict(extra='forbid')
 accession:str=Field(pattern=r'^GSE[1-9][0-9]{1,8}$')
 filename:str=Field(pattern=r'^[A-Za-z0-9_.-]{1,180}\.txt\.gz$')
def cache_root():
 from brace_app import server
 root=server.RUNS/'_discovery';root.mkdir(parents=True,exist_ok=True);return root
def now():return datetime.now(timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
def public_bytes(url,limit=2*1024*1024):
 global _last
 parsed=urllib.parse.urlsplit(url)
 if parsed.scheme!='https' or parsed.hostname not in ('eutils.ncbi.nlm.nih.gov','ftp.ncbi.nlm.nih.gov') or parsed.username or parsed.port:raise ValueError('Unapproved public endpoint')
 with _lock:
  delay=max(0.,.36-(time.monotonic()-_last))
  if delay:time.sleep(delay)
  _last=time.monotonic()
 req=urllib.request.Request(url,headers={'User-Agent':'BRACE-local-research/1.0 (explicit public GEO lookup)','Accept':'application/json,text/html,application/gzip'})
 try:
  with urllib.request.build_opener(NoRedirect).open(req,timeout=12) as r:
   length=r.headers.get('Content-Length')
   if length and (not length.isdigit()):raise HTTPException(502,'NCBI returned an invalid response size header.')
   if length and int(length)>limit:raise HTTPException(413,'The public file exceeds the acquisition limit. Use a documented preparation workflow; the API limit remains 25 MiB.')
   data=r.read(limit+1)
   if len(data)>limit:raise HTTPException(413,'The public response exceeds the size limit.')
   return data
 except urllib.error.HTTPError as e:
  raise HTTPException(429 if e.code==429 else 502,'NCBI rate-limited this request. Wait and retry.' if e.code==429 else 'The official NCBI endpoint could not serve this request. Retry later or use the source link.') from e
 except (urllib.error.URLError,TimeoutError,OSError) as e:raise HTTPException(503,'Public lookup is unavailable or timed out. Your local studies remain available; retry when online.') from e

def cached(key,refresh=False):
 p=cache_root()/(sha(key.encode())+'.json')
 if refresh or not p.is_file():return None
 try:
  envelope=json.loads(p.read_text());payload=envelope['payload']
  if sha(json.dumps(payload,sort_keys=True).encode())!=envelope['sha256']:return None
  if time.time()-p.stat().st_mtime>TTL:return None
  return {**payload,'cached':True}
 except (ValueError,KeyError,TypeError):return None

def store(key,data):
 p=cache_root()/(sha(key.encode())+'.json');payload={**data,'cached':False};raw=json.dumps(payload,sort_keys=True).encode();tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp');tmp.write_text(json.dumps({'payload':payload,'sha256':sha(raw)}));tmp.replace(p);return payload

def source(url,data):return {'url':url,'sha256':sha(data),'bytes':len(data)}
@router.post('/api/discovery/search')
def search(q:Query):
 key='search:'+q.model_dump_json(exclude={'refresh'});old=cached(key,q.refresh)
 if old:return old
 text=q.question.strip()
 if not text:raise HTTPException(422,'Enter a public research question or GEO accession.')
 term=f'({text}) AND "{q.organism}"[Organism] AND gse[ETYP]'
 if q.tissue.strip():term+=' AND ('+q.tissue.strip()+')'
 if q.assay=='microarray':term+=' AND "expression profiling by array"[DataSet Type]'
 if q.assay=='rnaseq':term+=' AND "expression profiling by high throughput sequencing"[DataSet Type]'
 base='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
 url=base+'esearch.fcgi?'+urllib.parse.urlencode({'db':'gds','retmode':'json','retmax':6,'term':term,'tool':'BRACE'})
 raw=public_bytes(url)
 try:found=json.loads(raw)['esearchresult'];ids=found['idlist'];count=int(found['count'])
 except (ValueError,KeyError,TypeError):raise HTTPException(502,'NCBI returned an unexpected search format. No candidate was approved.')
 records=[];sources=[source(url,raw)]
 if not isinstance(ids,list) or len(ids)>6 or count<0:raise HTTPException(502,'NCBI returned an unexpected search record list.')
 if ids:
  if any(not re.fullmatch(r'[0-9]{1,15}',str(i)) for i in ids):raise HTTPException(502,'NCBI returned invalid record identifiers.')
  url2=base+'esummary.fcgi?'+urllib.parse.urlencode({'db':'gds','retmode':'json','id':','.join(ids),'tool':'BRACE'});data=public_bytes(url2);sources.append(source(url2,data))
  try:
   result=json.loads(data)['result']
   for uid in result.get('uids',[]):
    r=result[uid];acc=str(r.get('accession',''))
    if not re.fullmatch(r'GSE[1-9][0-9]{1,8}',acc):continue
    records.append({'accession':acc,'title':str(r.get('title','Title not provided'))[:600],'summary':str(r.get('summary',''))[:3500],'organism':str(r.get('taxon','Not reported')),'samples':r.get('n_samples'),'platforms':r.get('gpl',[]),'publication_ids':r.get('pubmedids',[]) if isinstance(r.get('pubmedids'),list) else [],'source_url':'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc='+acc,'stage':'metadata_found','eligible':False,'unknowns':['Phenotype/group definitions and group counts','Processing and normalization equivalence','Patient independence and overlap','Feature mapping and original-file integrity','Licensing and task-specific preparation']})
  except (ValueError,KeyError,TypeError):raise HTTPException(502,'NCBI returned an unexpected summary format. No candidate was approved.')
 return store(key,{'query':q.model_dump(exclude={'refresh'}),'retrieved_utc':now(),'total_matches':count,'candidates':records,'sources':sources,'scope':'Official public metadata only. Candidates are not prepared inputs or scientifically approved pairs.','policy_url':POLICY})
class Links(HTMLParser):
 def __init__(self):super().__init__();self.hrefs=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':self.hrefs += [v for k,v in attrs if k=='href']
def matrix_files(accession):
 if not re.fullmatch(r'GSE[1-9][0-9]{1,8}',accession):raise HTTPException(422,'Use an exact GEO Series accession, for example GSE42568.')
 digits=accession[3:];bucket='GSE'+(digits[:-3] if len(digits)>3 else '')+'nnn'
 url=f'https://ftp.ncbi.nlm.nih.gov/geo/series/{bucket}/{accession}/matrix/'
 raw=public_bytes(url,1024*1024);p=Links();p.feed(raw.decode('utf-8',errors='replace'));files=[]
 for href in p.hrefs:
  name=href.split('/')[-1]
  if re.fullmatch(re.escape(accession)+r'(?:-[A-Za-z0-9_]+)?_series_matrix\.txt\.gz',name):
   pinned=REVIEWED_OVERSIZE.get(url+name)
   files.append({'filename':name,'url':url+name,'acquisition_limit_bytes':pinned['bytes'] if pinned else MAX_DOWNLOAD,
                 'acquisition_policy':'Exact size and SHA-256 of the reviewed original only' if pinned else 'Generic 25 MiB acquisition limit'})
 return {'accession':accession,'retrieved_utc':now(),'files':files,'sources':[source(url,raw)],'stage':'file_links_verified','eligible':False,'note':'The filenames were found in the official directory. Matrix content, sample labels and biological compatibility still require review. GEO Series Matrix/SOFT format is not directly a BRACE prepared input.'}
@router.get('/api/discovery/study/{accession}')
def study(accession:str):
 key='matrix:2:'+accession;old=cached(key)
 if old:return old
 return store(key,matrix_files(accession))
@router.post('/api/discovery/acquire')
def acquire(q:Acquisition):
 listing=matrix_files(q.accession);file=next((f for f in listing['files'] if f['filename']==q.filename),None)
 if not file:raise HTTPException(404,'That file was not found in the official directory. No guessed download path was used.')
 pinned=REVIEWED_OVERSIZE.get(file['url'])
 data=public_bytes(file['url'],pinned['bytes'] if pinned else MAX_DOWNLOAD)
 if pinned and (len(data)!=pinned['bytes'] or sha(data)!=pinned['sha256']):
  raise HTTPException(409,{'code':'PUBLIC_PIN_MISMATCH','message':'The reviewed original differs from its exact expected size or SHA-256. No oversized dataset was registered. Restore the pinned original or supply a documented prepared input.'})
 if not data.startswith(b'\x1f\x8b'):raise HTTPException(502,'The public response was not a gzip matrix file. Nothing was accepted as data.')
 token=sha(data);root=cache_root();dest=root/(token+'.gz')
 temporary=root/(token+'.'+uuid.uuid4().hex+'.tmp')
 try:
  temporary.write_bytes(data);temporary.replace(dest)
 finally:temporary.unlink(missing_ok=True)
 receipt={'token':token,'accession':q.accession,'filename':q.filename,'url':file['url'],'bytes':len(data),'sha256':token,'retrieved_utc':now(),'stage':'original_file_acquired','eligible':False,'note':'Original compressed public matrix only; not normalized, label-curated or prepared for BRACE. Decompressed/prepared inputs must independently satisfy intake limits.','download_url':'/api/discovery/acquired/'+token}
 from brace_app.dataset_api import register_acquisition
 receipt['dataset_id']=register_acquisition(receipt,dest)['id']
 atomic_json(root/(token+'.receipt.json'),receipt);return receipt
@router.get('/api/discovery/acquired/{token}')
def acquired(token:str):
 if not re.fullmatch(r'[0-9a-f]{64}',token):raise HTTPException(404,'Public acquisition not found')
 root=cache_root();path=root/(token+'.gz');meta=root/(token+'.receipt.json')
 try:r=json.loads(meta.read_text())
 except (OSError,ValueError):raise HTTPException(404,'Public acquisition not found')
 if not path.is_file() or sha(path.read_bytes())!=token:raise HTTPException(409,'The cached public file failed its hash check. Acquire it again.')
 return FileResponse(path,filename=r['filename'],headers={'X-Content-Type-Options':'nosniff'})
@router.get('/api/example/public-er/inputs')
def input_bundle():
 import io,zipfile
 from brace_app.study_api import public_paths,PUBLIC_INPUT_FILES,public_input
 root=public_paths();buf=io.BytesIO()
 with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
  for name in sorted(PUBLIC_INPUT_FILES|{'race_config.json'}):
   response=public_input(name);z.write(response.path,name)
  z.writestr('README.txt','Verified public ER example inputs. Source GSE42568, target GSE20711. Exploratory only: processing/ER assays differ and donor independence is incompletely authenticated. Use the guided setup and review both declarations. No raw assay normalization is performed by BRACE.')
 return Response(buf.getvalue(),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="BRACE_public_ER_inputs.zip"','X-Content-Type-Options':'nosniff'})

@router.get('/api/example/public-er/exclusions/{role}')
def public_exclusions(role:str):
 import csv
 from collections import Counter
 from brace_app.study_api import public_paths
 if role not in ('source','target'):raise HTTPException(404,'Public cohort role unavailable')
 root=public_paths();path=root/'prepared'/(role+'_all_samples.tsv')
 with path.open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream,delimiter='\t'))
 counts=Counter(r['inclusion'] for r in rows)
 return {'role':role,'accession':'GSE42568' if role=='source' else 'GSE20711','downloaded_samples':len(rows),'included':counts.get('included',0),'exclusion_counts':{k:v for k,v in counts.items() if k!='included'},'records':[{k:r.get(k,'') for k in ('sample_id','title','inclusion','condition')} for r in rows if r['inclusion']!='included'],'source_sha256':sha(path.read_bytes()),'scope':'Pinned public preparation records; not a new exclusion or inference.'}
