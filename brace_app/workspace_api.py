"""Read-only task descriptions and existing local run index; no new engine."""
import json,re
from datetime import datetime,timezone
from pathlib import Path
from fastapi import APIRouter
from brace_app.export_safety import within
router=APIRouter()
CAPABILITIES=Path(__file__).with_name('task_capabilities.json')
@router.get('/api/assays')
def assays():
    from brace_core.assays import catalog
    return catalog()
@router.get('/api/capabilities')
def capabilities():
    return json.loads(CAPABILITIES.read_text(encoding='utf-8'))
@router.get('/api/runs')
def existing_runs():
    from brace_app import server
    items=[]
    if not server.RUNS.is_dir():return dict(runs=[],scope='No local generated run folder exists yet.',maximum=None)
    for path in server.RUNS.iterdir():
        if not re.fullmatch(r'[0-9a-f]{32}',path.name):continue
        try:
            folder=within(server.RUNS,path);config_path=within(folder,folder/'run.json')
            if not config_path.is_file():continue
            config=json.loads(config_path.read_text(encoding='utf-8'))
            # An index is not a scientific integrity approval. Opening verifies it.
            recorded=config.get('created_utc')
            # Legacy runs use the configuration file's timestamp, never the folder.
            # Opening/exporting a result changes folder mtime and must not reorder history.
            timestamp=datetime.fromisoformat(recorded).astimezone(timezone.utc).isoformat() if recorded else datetime.fromtimestamp(config_path.stat().st_mtime,timezone.utc).isoformat()
            items.append(dict(id=path.name,study_id=config.get('study_id'),name=str(config.get('name') or ('RACE gene replication' if config['mode']=='race' else 'Local analysis')),mode=config['mode'],kind=config.get('kind','user_computed'),has_result=any((folder/name).is_file() for name in ('race/race_result.json','validation/validation_result.json','shift/shift_result.json','validation/unlabeled_result.json')),created_utc=timestamp,timestamp_source='recorded' if recorded else 'legacy_run_file',folder_modified_utc=timestamp,integrity='Checked when opened'))
        except (ValueError,OSError,KeyError,TypeError):continue
    items.sort(key=lambda item:(item['created_utc'],item['id']),reverse=True)
    return dict(runs=items,scope='All saved local analyses; integrity is checked when opened.',maximum=None)


@router.get('/api/workspace/storage')
def storage():
    from brace_app import server, dataset_registry as registry
    groups = {'datasets':0,'analyses':0,'public_cache':0,'backups':0,'other':0}
    for path in server.RUNS.rglob('*') if server.RUNS.is_dir() else []:
        if not path.is_file() or path.is_symlink(): continue
        first=path.relative_to(server.RUNS).parts[0]
        category='datasets' if first=='_workspace' else 'public_cache' if first in ('_discovery','_annotations') else 'backups' if first=='_backups' else 'analyses' if re.fullmatch('[0-9a-f]{32}',first) else 'other'
        groups[category]+=path.stat().st_size
    return {'bytes':sum(groups.values()),'categories':groups,'datasets':len(registry.list_datasets()),'studies':len(registry.list_studies())}


@router.post('/api/workspace/backup')
def backup():
    """Consistent registry snapshot plus immutable assets and completed runs."""
    import hashlib,sqlite3,tempfile,uuid,zipfile
    from contextlib import closing
    from fastapi import HTTPException
    from brace_app import server, dataset_registry as registry
    folder=server.RUNS/'_backups';folder.mkdir(parents=True,exist_ok=True)
    token=uuid.uuid4().hex;destination=folder/(token+'.zip');partial=folder/(token+'.tmp')
    hashes={}
    try:
        with tempfile.TemporaryDirectory(prefix='brace-backup-') as temporary:
            snapshot=Path(temporary)/'registry.sqlite3'
            with registry.database() as db,closing(sqlite3.connect(snapshot)) as copy,copy:
                db.backup(copy)
                records=[json.loads(row[0]) for row in copy.execute('SELECT record FROM datasets')]
            with zipfile.ZipFile(partial,'w',zipfile.ZIP_DEFLATED) as archive:
                def add(path,name):
                    data=path.read_bytes();archive.writestr(name,data);hashes[name]=hashlib.sha256(data).hexdigest()
                add(snapshot,'_workspace/registry.sqlite3')
                for record in records:
                    for kind,asset in record['assets'].items():
                        path=registry.asset_path(record['id'],kind)
                        add(path,'_workspace/'+record['id']+'/'+asset['storage_name'])
                for run in existing_runs()['runs']:
                    if not run['has_result']:continue
                    root=server.safe_run_dir(run['id']);server.finalize_run(root)
                    for path in root.rglob('*'):
                        if path.is_file() and not path.is_symlink():add(path,path.relative_to(server.RUNS).as_posix())
                archive.writestr('BACKUP_MANIFEST.json',json.dumps({'sha256':hashes,'scope':'Private local backup: original uploads included. Stop BRACE before restoring into a separate empty workspace.','restore':'Extract into a new empty directory and set BRACE_RUNS_DIR to that directory. Keep the existing workspace until the restored studies open correctly.'},indent=2))
            partial.replace(destination)
        return {'url':'/api/workspace/backup/'+token,'bytes':destination.stat().st_size,'files':len(hashes)}
    except Exception:
        partial.unlink(missing_ok=True)
        raise


@router.get('/api/workspace/backup/{token}')
def download_backup(token:str):
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    from brace_app import server
    if not re.fullmatch('[0-9a-f]{32}',token):raise HTTPException(404,'Backup not found.')
    path=server.RUNS/'_backups'/(token+'.zip')
    if not path.is_file():raise HTTPException(404,'Backup not found.')
    return FileResponse(path,filename='BRACE-private-workspace-backup.zip',headers={'X-Content-Type-Options':'nosniff'})
