"""Check local Markdown file references without fetching remote or future-tag URLs."""
from pathlib import Path
from urllib.parse import unquote
import argparse
import json
import re
import csv
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    sources = [ROOT/'README.md', *sorted((ROOT/'docs').rglob('*.md'))]
    if (ROOT/'.git').exists():
        names = subprocess.check_output(['git','ls-files','-z'], cwd=ROOT).decode('utf-8').split('\0')
    else:
        with (ROOT/'packaging/source-manifest.csv').open(encoding='utf-8', newline='') as stream:
            names = [row['path'] for row in csv.DictReader(stream)]
    payload = {name for name in names if name}
    checked, missing = 0, []
    for source in sources:
        for target in re.findall(r'\]\(([^)]+)\)', source.read_text(encoding='utf-8')):
            if target.startswith(('https:', 'http:', '#', 'mailto:')):
                continue
            local = unquote(target.split('#')[0].split('?')[0])
            resolved = (source.parent/local).resolve()
            checked += 1
            relative = resolved.relative_to(ROOT).as_posix() if resolved.is_relative_to(ROOT) else ''
            shipped = relative in payload or resolved.is_dir() and any(name.startswith(relative+'/') for name in payload)
            if not relative or not resolved.exists() or not shipped:
                missing.append({'source':source.relative_to(ROOT).as_posix(), 'target':target})
    result = {'status':'FAIL' if missing else 'PASS', 'sources':len(sources),
              'local_references':checked, 'missing':missing,
              'scope':'Local Markdown targets must exist in the Git/source-manifest payload; remote URLs and heading anchors are not network-verified.'}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))
    if missing:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
