"""Shared atomic local records and explicit application contract version."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = '1.0.0'


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('w', encoding='utf-8', newline='\n') as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def study_name(name: str | None, default: str) -> str:
    title = (name or '').strip() or default
    if len(title) > 200 or any(ord(character) < 32 for character in title):
        raise ValueError('Study name must be at most 200 characters without control characters.')
    return title


def require_schema(version: str) -> None:
    if version != SCHEMA_VERSION:
        from fastapi import HTTPException
        raise HTTPException(422, {'code': 'SCHEMA_VERSION_UNSUPPORTED',
            'message': f'Unsupported application schema {version!r}. Use {SCHEMA_VERSION}.'})


def run_identity(root: Path, config: dict) -> dict:
    """Read cohort identity only from this run; never browser or other study state."""
    if config.get('schema_version', SCHEMA_VERSION) != SCHEMA_VERSION:
        raise ValueError('Saved run uses an unsupported application schema.')
    cohorts = {}
    for role in ('source', 'target'):
        path = root / 'input' / (role + '_manifest.json')
        if path.is_file():
            cohorts[role] = json.loads(path.read_text(encoding='utf-8-sig'))
    if not cohorts and config.get('mode') == 'race':
        methods_path = root / 'race' / 'race_methods.json'
        if methods_path.is_file():
            methods = json.loads(methods_path.read_text(encoding='utf-8'))
            cohorts = {role: methods[role + '_manifest'] for role in ('source', 'target')
                       if role + '_manifest' in methods}
    if not cohorts:
        cohorts = {role: record['summary']['manifest'] for role, record in config.get('dataset_provenance', {}).items()
                   if record.get('summary', {}).get('manifest')}
    return {'schema_version': config.get('schema_version', SCHEMA_VERSION),
            'study_id': config.get('study_id'), 'created_utc': config.get('created_utc'),
            'datasets': config.get('datasets', {}), 'cohorts': cohorts or None}
