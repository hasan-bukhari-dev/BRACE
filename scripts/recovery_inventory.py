"""Reproducible Git-blob provenance; never modifies historical references."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REFS = {'v6': 'v1.0.0-v6', 'main': '871472bc6a9be8387930218b4340ba3e10b83006',
        'dev': 'v1.1.0-dev', 'dev2': 'v1.1.0-dev.2'}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def tree(ref):
    result = {}
    for row in git('ls-tree', '-rz', ref).split(b'\0'):
        if row:
            meta, path = row.split(b'\t', 1)
            result[path.decode()] = meta.split()[2].decode()
    return result


def main(output):
    output.mkdir(parents=True, exist_ok=True)
    trees = {name: tree(ref) for name, ref in REFS.items()}
    changed = {}
    commit = ''
    for line in git('log', '--all', '--format=@@%H', '--name-only').decode().splitlines():
        if line.startswith('@@'):
            commit = line[2:]
        elif line:
            changed.setdefault(line, commit)
    extra = git('ls-files', '--others', '--exclude-standard', '-z').decode().split('\0')
    paths = sorted(set().union(*trees.values(), tree('HEAD'), filter(None, extra)))
    rows = []
    for path in paths:
        p = ROOT/path
        data = p.read_bytes() if p.is_file() else None
        final = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() if data is not None else ''
        hashes = {name: entries.get(path, '') for name, entries in trees.items()}
        if not final:
            decision = 'Historical material retained in V6 tag; not restored to runtime'
        elif final == hashes['main']:
            decision = 'Original application preserved byte-identical'
        elif final == hashes['dev2']:
            decision = 'Development implementation preserved byte-identical'
        else:
            decision = 'Recovery integration; see RECOVERY.md and patch'
        owner = 'scientific' if path.startswith('brace_core/') else 'frontend' if '/static/' in path else 'backend' if path.startswith('brace_app/') else 'verification' if path.startswith(('tests/', 'scripts/', 'docs/')) else 'distribution/support'
        rows.append(dict(path=path, **hashes, final=final, ownership=owner,
            introduced_or_modified_commit=changed.get(path,'Recovery working tree'),
            decision=decision, verification='Git blob identity; runtime evidence in RECOVERY.md',
            user_facing_dependencies='Original workbench' if owner == 'frontend' else '',
            api_backend_dependencies='Preserved dev.2 API contracts' if owner in ('frontend','backend') else '',
            scientific_dependencies='Preserved brace_core engines' if owner in ('frontend','backend','scientific') else '',
            provenance_scope='Tree snapshots; shallow history does not prove first introduction'))
    with (output/'file-provenance.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = {'refs': {name: git('rev-parse', ref+'^{commit}').decode().strip() for name,ref in REFS.items()},
        'counts': {name: len(entries) for name,entries in trees.items()},
        'dev2_files_deleted': [r['path'] for r in rows if r['dev2'] and not r['final']],
        'frontend_byte_identical_to_main': [r['path'] for r in rows if r['ownership']=='frontend' and r['main'] and r['main']==r['final']],
        'frontend_modified_from_main': [r['path'] for r in rows if r['ownership']=='frontend' and r['main'] and r['main']!=r['final']],
        'scientific_changed_from_dev2': [r['path'] for r in rows if r['ownership']=='scientific' and r['dev2'] and r['dev2']!=r['final']]}
    (output/'provenance-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k in ('counts','dev2_files_deleted','scientific_changed_from_dev2')},indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--out',type=Path,default=ROOT/'docs/recovery')
    main(parser.parse_args().out)
