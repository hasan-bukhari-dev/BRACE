"""Non-demo input contracts, immutable role binding and public annotation safety."""
import gzip
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from brace_app import server, dataset_registry as registry, gene_info
from brace_app.preparation import prepare_general

BASE=Path(__file__).resolve().parents[1]


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'RUNS',tmp_path/'runs')
    return TestClient(server.app)


def test_roles_are_study_assignments_and_do_not_duplicate_assets(client):
    pair=client.post('/api/datasets/reviewed-public',json={'reviewed':True}).json()['datasets']
    ids={role:record['id'] for role,record in pair.items()}
    originals={role:registry.asset_path(id,'manifest').read_bytes() for role,id in ids.items()}
    body={'name':'Reversed cohort roles','mode':'diagnose_shift','datasets':{'source':ids['target'],'target':ids['source']}}
    checked=client.post('/api/dataset-analysis/preflight',json=body)
    assert checked.status_code==200 and checked.json()['eligible'],checked.text
    result=client.post('/api/dataset-analysis/run',json=body)
    assert result.status_code==200,result.text
    run=result.json()
    assert run['datasets']==body['datasets']
    assert len(client.get('/api/datasets').json()['datasets'])==4
    for role,id in ids.items():assert registry.asset_path(id,'manifest').read_bytes()==originals[role]
    with zipfile.ZipFile(io.BytesIO(client.get('/api/embrace/'+run['id']).content)) as z:
        lineage=json.loads(z.read('DATASET_LINEAGE.json'))
        assert lineage['source']['id']==ids['target']
        assert lineage['source']['assigned_role']=='source'


def test_source_variance_is_label_independent_and_target_aligns_exactly(tmp_path,monkeypatch):
    from brace_app import preparation
    monkeypatch.setattr(preparation,'MAX_FEATURES',2)
    source=tmp_path/'source.gz'
    source.write_bytes(gzip.compress(b'!series_matrix_table_begin\nID_REF\tS1\tS2\na\t1\t1\nb\t0\t9\nc\t2\t3\n!series_matrix_table_end\n'))
    output=tmp_path/'output';output.mkdir()
    manifest={'role':'source','labels':'binary'}
    args=dict(manifest=manifest,condition_by_sample={'S1':'A','S2':'B'},feature_mapping={},mapping_reference='',excluded_samples={},feature_policy='source_variance')
    paths,report=prepare_general(source,output,**args)
    first=paths['expression'].read_bytes()
    _,second=prepare_general(source,output,**{**args,'condition_by_sample':{'S1':'B','S2':'A'}})
    assert first==paths['expression'].read_bytes()
    assert second['feature_mapping']==report['feature_mapping']
    assert report['selection_uses_labels'] is False
    assert report['unmapped_features']==['a']
    with pytest.raises(ValueError,match='source-only'):
        prepare_general(source,output,**{**args,'manifest':{'role':'target','labels':'binary'}})
    _,aligned=prepare_general(source,output,**{**args,'manifest':{'role':'target','labels':'binary'},'feature_policy':'source_features','reference_ids':['b','c']})
    assert aligned['retained_features']==2 and aligned['unmapped_features']==['a']
    with pytest.raises(ValueError,match='lacks source'):
        prepare_general(source,output,**{**args,'feature_policy':'source_features','reference_ids':['missing']})


def test_unfamiliar_prediction_columns_reach_real_ace(client):
    table=b'case,observed,called,pA,pB\na,alpha,alpha,0.9,0.1\nb,beta,alpha,0.6,0.4\nc,beta,beta,0.2,0.8\n'
    preview=client.post('/api/predictions/inspect',files={'table':('new.csv',table)})
    assert preview.status_code==200 and preview.json()['count']==3
    mapping={'name':'New external prediction table','model_id':'External instrument 7','label_source_description':'Technical fixture labels',
        'classes':['alpha','beta'],'probability_columns':{'alpha':'pA','beta':'pB'},'reviewed':True,
        'sample_id':'case','true_label':'observed','predicted_label':'called'}
    imported=client.post('/api/predictions/import',files={'table':('new.csv',table)},data={'mapping':json.dumps(mapping)})
    assert imported.status_code==200,imported.text
    record=imported.json()
    body={'name':'Non-demo ACE','mode':'evaluate_predictions','datasets':{'predictions':record['id']}}
    result=client.post('/api/dataset-analysis/run',json=body)
    assert result.status_code==200,result.text
    assert result.json()['validation']['n']==3
    assert result.json()['validation']['metrics']['n_correct']==2
    partial={**mapping,'probability_columns':{'alpha':'pA'}}
    assert client.post('/api/predictions/import',files={'table':('new.csv',table)},data={'mapping':json.dumps(partial)}).status_code==422


def test_gene_functions_are_general_cached_and_not_guessed(client,monkeypatch):
    from brace_app import discovery
    calls=[]
    def fetch(url,*args,**kwargs):
        calls.append(url)
        return json.dumps({'result':{'672':{'name':'BRCA1','description':'BRCA1 DNA repair associated','currentid':'',
            'organism':{'taxid':9606},'summary':'Reference functional summary from a controlled API response.'}}}).encode()
    monkeypatch.setattr(discovery,'public_bytes',fetch)
    result=gene_info.lookup('672','entrez_gene',online=True)
    assert result['biological_context']['current_symbol']=='BRCA1'
    assert 'source_snapshot_sha256' in result['biological_context']
    assert gene_info.lookup('672','entrez_gene')['biological_context']==result['biological_context']
    assert len(calls)==1
    ambiguous=gene_info.lookup('1007_s_at','probe_id','GPL570',online=True)
    assert ambiguous['status']=='ambiguous' and not ambiguous.get('biological_context')
    assert len(calls)==1
    unmapped=gene_info.lookup('novel-probe','probe_id','GPL_UNKNOWN',online=True)
    assert unmapped['status']=='unmapped' and len(calls)==1


def test_private_backup_is_consistent_and_has_originals(client,tmp_path):
    original=tmp_path/'original.gz';original.write_bytes(b'private technical fixture')
    record=registry.register({'original':original},name='Backup fixture',source={'type':'technical_test'})
    response=client.post('/api/workspace/backup')
    assert response.status_code==200,response.text
    with zipfile.ZipFile(io.BytesIO(client.get(response.json()['url']).content)) as z:
        manifest=json.loads(z.read('BACKUP_MANIFEST.json'))
        assert any(record['id'] in name for name in z.namelist())
        assert '_workspace/registry.sqlite3' in z.namelist()
        for name,sha in manifest['sha256'].items():assert hashlib.sha256(z.read(name)).hexdigest()==sha
    assert client.get('/api/workspace/storage').json()['bytes']>0
    assert client.get('/api/workspace/backup/not-a-token').status_code==404


def test_history_is_not_silently_truncated(client):
    for i in range(53):
        root=server.RUNS/f'{i:032x}';root.mkdir(parents=True)
        (root/'run.json').write_text(json.dumps({'name':f'History {i}','mode':'diagnose_shift'}))
    result=client.get('/api/runs').json()
    assert len(result['runs'])==53 and result['maximum'] is None


def test_characteristic_fields_align_by_key_not_geo_row(client,tmp_path):
    path=tmp_path/'original.gz'
    path.write_bytes(gzip.compress(b'!Sample_characteristics_ch1\t"er: 0"\t"tissue: tumor"\n!Sample_characteristics_ch1\t"tissue: tumor"\t"er: 1"\n!series_matrix_table_begin\nID_REF\tS1\tS2\na\t1\t2\n!series_matrix_table_end\n'))
    record=registry.register({'original':path},name='Shifted GEO annotations',source={'type':'technical_test'})
    preview=client.get('/api/datasets/'+record['id']+'/inspect').json()
    fields={column['name']:column['values'] for column in preview['phenotype_fields']}
    assert fields['er']==['0','1'] and fields['tissue']==['tumor','tumor']


def test_identifier_panel_does_not_use_expression_values(tmp_path,monkeypatch):
    from brace_app import preparation
    monkeypatch.setattr(preparation,'MAX_FEATURES',2)
    original=tmp_path/'input.gz';out=tmp_path/'out';out.mkdir()
    args=dict(manifest={'role':'source','labels':'unlabeled'},condition_by_sample={'S1':'','S2':''},feature_mapping={},mapping_reference='',excluded_samples={},feature_policy='identifier_panel')
    def write(values):
        original.write_bytes(gzip.compress(('!series_matrix_table_begin\nID_REF\tS1\tS2\n'+''.join(f'{name}\t{a}\t{b}\n' for name,a,b in values)+'!series_matrix_table_end\n').encode()))
    write([('a',1,1),('b',0,10),('c',2,3)])
    _,first=prepare_general(original,out,**args)
    write([('a',0,10000),('b',2,2),('c',-999,999)])
    _,second=prepare_general(original,out,**args)
    assert first['feature_mapping']==second['feature_mapping']
    assert 'No expression values' in second['mapping_reference']


def test_archive_is_reversible_and_preserves_data(client,tmp_path):
    study=registry.create_study('Reusable study')
    for value in [True,False]:
        response=client.patch('/api/studies/'+study['id']+'/visibility',json={'archived':value})
        assert response.status_code==200 and response.json()['archived'] is value
        assert response.json()['datasets']=={}


def test_registry_baseline_rejects_variance_prefilter_outside_cv(client):
    root=BASE/'examples/synthetic_valid'
    records={}
    for role in ['source','target']:
        paths={kind:root/(role+'_'+('samples' if kind=='metadata' else kind)+('.json' if kind=='manifest' else '.csv')) for kind in ['expression','metadata','manifest']}
        records[role]=registry.register_cohort(paths,name='Technical '+role,source={'type':'technical_test'},
            history=[{'feature_policy':'source_variance'}] if role=='source' else [])
    response=client.post('/api/dataset-analysis/preflight',json={'name':'Prefilter leakage guard','mode':'train_validate',
        'datasets':{role:record['id'] for role,record in records.items()}})
    assert response.status_code==422 and 'before cross-validation' in response.text
