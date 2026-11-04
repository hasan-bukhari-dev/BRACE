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
    if not server.RUNS.is_dir():return dict(runs=[],scope='No local generated run folder exists yet.',maximum=50)
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
    return dict(runs=items[:50],scope='Local generated run folders only; input paths and uploaded data are not listed.',maximum=50)
