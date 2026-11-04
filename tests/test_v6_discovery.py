"""New public discovery boundaries, provenance and exact-input bundle integration."""
import hashlib,io,json,zipfile
from pathlib import Path
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from brace_app import server,discovery
from brace_app.provenance_origin import identify_public
A=Path(__file__).resolve().parents[1]
@pytest.fixture
def client(tmp_path,monkeypatch):
 monkeypatch.setattr(server,'RUNS',tmp_path/'runs');server.RUNS.mkdir();return TestClient(server.app)
def mock_search(monkeypatch,empty=False):
 calls=[]
 def fake(url,limit=2097152):
  calls.append(url)
  if 'esearch' in url:return json.dumps({'esearchresult':{'count':'0' if empty else '1','idlist':[] if empty else ['200042568']}}).encode()
  return json.dumps({'result':{'uids':['200042568'],'200042568':{'accession':'GSE42568','title':'Actual endpoint schema fixture','taxon':'Homo sapiens','n_samples':121,'gpl':['570'],'summary':'Metadata only; fixture, not a live result'}}}).encode()
 monkeypatch.setattr(discovery,'public_bytes',fake);return calls

def test_search_explicit_metadata_not_approval_and_cache_integrity(client,monkeypatch):
 calls=mock_search(monkeypatch);body={'question':'breast estrogen receptor'}
 r=client.post('/api/discovery/search',json=body);assert r.status_code==200
 d=r.json();assert d['candidates'][0]['eligible'] is False and d['candidates'][0]['stage']=='metadata_found'
 assert len(calls)==2 and d['sources'][0]['sha256'] and not d['cached']
 assert client.post('/api/discovery/search',json=body).json()['cached'];assert len(calls)==2
 path=next(discovery.cache_root().glob('*.json'));x=json.loads(path.read_text());x['payload']['total_matches']=999;path.write_text(json.dumps(x))
 assert client.post('/api/discovery/search',json=body).json()['total_matches']==1;assert len(calls)==4
 assert client.post('/api/discovery/search',json={**body,'refresh':True}).status_code==200 and len(calls)==6

def test_empty_search_is_not_synthetic_fallback(client,monkeypatch):
 mock_search(monkeypatch,True);d=client.post('/api/discovery/search',json={'question':'no results fixture'}).json();assert d['candidates']==[] and d['total_matches']==0
@pytest.mark.parametrize('body',[{'question':'x'},{'question':'   '},{'question':'valid question','private_labels':['secret']},{'question':'valid question','assay':'arbitrary'},{'question':'x'*181}])
def test_query_validation_and_no_upload_fields(client,body):assert client.post('/api/discovery/search',json=body).status_code==422

def test_malformed_remote_data_fail_honestly(client,monkeypatch):
 monkeypatch.setattr(discovery,'public_bytes',lambda *a,**k:b'<html>not JSON</html>');r=client.post('/api/discovery/search',json={'question':'public question'});assert r.status_code==502 and 'approved' in r.text
@pytest.mark.parametrize('code',[429,503])
def test_remote_failure_is_recoverable_not_compatibility_failure(client,monkeypatch,code):
 def fail(*a,**k):raise HTTPException(code,'Official endpoint unavailable')
 monkeypatch.setattr(discovery,'public_bytes',fail);assert client.post('/api/discovery/search',json={'question':'public question'}).status_code==code

def test_directory_verifies_actual_filenames(client,monkeypatch):
 monkeypatch.setattr(discovery,'public_bytes',lambda *a,**k:b'<a href="GSE42568_series_matrix.txt.gz">matrix</a><a href="../">parent</a><a href="not_matrix.txt.gz">other</a>');d=client.get('/api/discovery/study/GSE42568').json();assert [x['filename'] for x in d['files']]==['GSE42568_series_matrix.txt.gz'];assert not d['eligible'];assert d['sources'][0]['url']=='https://ftp.ncbi.nlm.nih.gov/geo/series/GSE42nnn/GSE42568/matrix/'
@pytest.mark.parametrize('acc',['GSE0','GSE42568evil','GPL570','x','..'])
def test_invalid_accessions(client,acc):assert client.get('/api/discovery/study/'+acc).status_code==(404 if acc=='..' else 422)

def test_missing_matrix_is_not_unsuitable_study(client,monkeypatch):
 monkeypatch.setattr(discovery,'public_bytes',lambda *a,**k:b'<html>No matrix listed</html>');d=client.get('/api/discovery/study/GSE42568').json();assert d['files']==[] and not d['eligible']

def test_acquisition_is_exact_bounded_public_file_and_tamper_checked(client,monkeypatch):
 data=b'\x1f\x8btechnical gzip-header fixture, not biological data'
 def fake(url,limit=0):return b'<a href="GSE42568_series_matrix.txt.gz">matrix</a>' if url.endswith('/') else data
 monkeypatch.setattr(discovery,'public_bytes',fake);body={'accession':'GSE42568','filename':'GSE42568_series_matrix.txt.gz'};d=client.post('/api/discovery/acquire',json=body).json();assert d['sha256']==hashlib.sha256(data).hexdigest() and not d['eligible'];assert client.get(d['download_url']).content==data
 (discovery.cache_root()/(d['token']+'.gz')).write_bytes(b'changed');assert client.get(d['download_url']).status_code==409
 assert client.post('/api/discovery/acquire',json={**body,'filename':'GSE42568_fake.txt.gz'}).status_code==404

def test_non_gzip_response_is_not_accepted(client,monkeypatch):
 monkeypatch.setattr(discovery,'public_bytes',lambda url,*a,**k:b'<a href="GSE42568_series_matrix.txt.gz">matrix</a>' if url.endswith('/') else b'captcha');assert client.post('/api/discovery/acquire',json={'accession':'GSE42568','filename':'GSE42568_series_matrix.txt.gz'}).status_code==502

def test_reviewed_target_size_exception_requires_exact_pinned_bytes(client,monkeypatch):
 data=(A/'examples/public_er_pair/raw/GSE20711_series_matrix.txt.gz').read_bytes();limits=[]
 def fake(url,limit=0):
  if url.endswith('/'):return b'<a href="GSE20711_series_matrix.txt.gz">matrix</a>'
  limits.append(limit);return data
 monkeypatch.setattr(discovery,'public_bytes',fake)
 response=client.post('/api/discovery/acquire',json={'accession':'GSE20711','filename':'GSE20711_series_matrix.txt.gz'})
 assert response.status_code==200,response.text
 assert limits==[26895121] and response.json()['bytes']==26895121 and response.json()['dataset_id']
 assert discovery.MAX_DOWNLOAD==25*1024*1024
 monkeypatch.setattr(discovery,'public_bytes',lambda url,limit=0:b'<a href="GSE20711_series_matrix.txt.gz">matrix</a>' if url.endswith('/') else data[:-1])
 rejected=client.post('/api/discovery/acquire',json={'accession':'GSE20711','filename':'GSE20711_series_matrix.txt.gz'})
 assert rejected.status_code==409 and rejected.json()['detail']['code']=='PUBLIC_PIN_MISMATCH'
@pytest.mark.parametrize('url',['http://ftp.ncbi.nlm.nih.gov/file','https://evil.test/file','https://ftp.ncbi.nlm.nih.gov:443/file','https://user@ftp.ncbi.nlm.nih.gov/file'])
def test_public_fetch_cannot_be_arbitrary_proxy(url):
 with pytest.raises(ValueError):discovery.public_bytes(url)

def test_complete_public_input_bundle_is_exact(client):
 r=client.get('/api/example/public-er/inputs');assert r.status_code==200
 with zipfile.ZipFile(io.BytesIO(r.content)) as z:
  assert z.testzip() is None and len(z.namelist())==8
  for role in ['source','target']:
   for kind,suffix in [('expression','.tsv'),('metadata','.tsv'),('manifest','.json')]:
    name=role+'_'+kind+suffix;assert z.read(name)==(A/'examples/public_er_pair/prepared'/name).read_bytes()

def test_origin_requires_all_six_verified_input_hashes():
 folder=A/'examples/public_er_pair/prepared';hashes={p.stem:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.iterdir() if p.name.startswith(('source_','target_')) and p.suffix in ['.tsv','.json']};assert identify_public(hashes)
 hashes['source_metadata']['sha256']='tampered';assert not identify_public(hashes)


def test_fresh_public_run_keeps_verified_origin_and_preparation(client):
 folder=A/'examples/public_er_pair';files={}
 for role in ['source','target']:
  for kind,suffix in [('expression','.tsv'),('metadata','.tsv'),('manifest','.json')]:
   name=role+'_'+kind+suffix;files[role+'_'+kind]=(name,(folder/'prepared'/name).read_bytes())
 r=client.post('/api/race',data={'race_config':(folder/'race_config.json').read_text()},files=files)
 assert r.status_code==200,r.text[:200]
 d=r.json();assert d['input_origin']=='verified_public' and d['race']['aggregate']['supported']==14
 report=client.get('/api/embrace/'+d['id']+'/report');assert b'Verified public inputs; fresh computation' in report.content
 package=client.get('/api/embrace/'+d['id']);z=zipfile.ZipFile(io.BytesIO(package.content))
 legend=json.loads(z.read('GENE_ANNOTATIONS.json'));assert len(legend['annotations'])==20
 assert {a['feature_id'] for a in legend['annotations']}=={a['feature_id'] for a in d['race']['genes']}
 assert json.loads(z.read('reproducibility_manifest.json'))['input_origin']=='verified_public'
 exclusions=json.loads(z.read('warning_exclusion_records.json'));assert exclusions['preparation']['GSE42568']['included']==101
 artifact=client.get('/api/embrace/'+d['id']+'/artifact/race/race_result.json');assert artifact.content==z.read('race/race_result.json')
 assert client.get('/api/embrace/'+d['id']+'/artifact/GENE_ANNOTATIONS.json').content==z.read('GENE_ANNOTATIONS.json')
 assert client.get('/api/embrace/'+d['id']+'/artifact/private.exe').status_code==404
 assert client.get('/api/embrace/'+d['id']+'/artifact/does_not_exist.json').status_code==404


@pytest.mark.parametrize('role,total,included,excluded',[('source',121,101,20),('target',90,87,3)])
def test_public_exclusion_records_match_actual_preparation(client,role,total,included,excluded):
 d=client.get('/api/example/public-er/exclusions/'+role).json();assert (d['downloaded_samples'],d['included'],len(d['records']))==(total,included,excluded);assert sum(d['exclusion_counts'].values())==excluded
 assert client.get('/api/example/public-er/exclusions/private').status_code==404
