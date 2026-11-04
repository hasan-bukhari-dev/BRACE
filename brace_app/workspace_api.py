"""Read-only task descriptions and existing local run index; no new engine."""
import json,re
from datetime import datetime,timezone
from pathlib import Path
from fastapi import APIRouter
from brace_app.export_safety import within
router=APIRouter()
CAPABILITIES=Path(__file__).with_name('task_capabilities.json')
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
            items.append(dict(id=path.name,name=str(config.get('name') or 'Local analysis'),mode=config['mode'],kind=config.get('kind','user_computed'),has_result=any((folder/name).is_file() for name in ('race/race_result.json','validation/validation_result.json','shift/shift_result.json')),folder_modified_utc=datetime.fromtimestamp(folder.stat().st_mtime,timezone.utc).isoformat(),integrity='Checked when opened'))
        except (ValueError,OSError,KeyError,TypeError):continue
    return dict(runs=items[-50:],scope='Local generated run folders only; input paths and uploaded data are not listed.',maximum=50)
