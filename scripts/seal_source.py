"""Seal this source checkout, excluding Git and all local runtime/build state."""
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.git','.venv','venv','runs','work','build','dist','release-assets','__pycache__',
            '.pytest_cache','.mypy_cache','.ruff_cache','node_modules','generated'}


def main():
    files = sorted(p for p in ROOT.rglob('*') if p.is_file()
                   and not set(p.relative_to(ROOT).parts)&EXCLUDED and p.suffix not in ('.pyc','.pyo')
                   and p.name not in ('.DS_Store','Thumbs.db'))
    index = {p.relative_to(ROOT).as_posix(): {'bytes':p.stat().st_size,
             'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files
             if p not in (ROOT/'CHECKPOINT_SHA256.json',ROOT/'FILE_SHA256_MANIFEST.csv')}
    (ROOT/'CHECKPOINT_SHA256.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'FILE_SHA256_MANIFEST.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['path','bytes','sha256'])
        for p in files:
            if p != ROOT/'FILE_SHA256_MANIFEST.csv':
                writer.writerow([p.relative_to(ROOT).as_posix(),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()])
    print(f'Sealed {len(files)-1} source/data files; local private and build directories excluded')


if __name__ == '__main__':
    main()
