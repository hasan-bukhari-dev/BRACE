"""Check Git's exact staged/tracked payload; never prints discovered secret values."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BLOCKED = {'.venv','venv','runs','work','.work','build','dist','release-assets','__pycache__','.pytest_cache'}
PATTERNS = [re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
            re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),
            re.compile(rb'github_pat_[A-Za-z0-9_]{40,}'),
            re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}')]


def main():
    names = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    names = [n for n in names if n]
    assert names, 'No tracked files to inspect'
    failures = []
    for name in names:
        p = Path(name)
        if set(p.parts)&BLOCKED or p.name == '.env' or p.suffix.lower() in ('.pfx','.p12','.key','.pem'):
            failures.append((name,'private/runtime file must not be tracked'))
        path = ROOT/p
        if path.stat().st_size >= 100*1024*1024:
            failures.append((name,'exceeds GitHub normal file limit'))
        if path.suffix.lower() in ('.py','.md','.txt','.json','.yml','.yaml','.sh','.bat','.ps1','.csv','.html','.js'):
            data = path.read_bytes()
            if any(pattern.search(data) for pattern in PATTERNS):
                failures.append((name,'possible credential/private key; value suppressed'))
    if failures:
        for name,reason in failures:
            print(name+': '+reason)
        raise SystemExit(1)
    print(f'Repository payload check: PASS; {len(names)} tracked files, no blocked runtime/private paths or matched credential patterns')


if __name__ == '__main__':
    main()
