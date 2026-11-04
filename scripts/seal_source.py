"""Seal this source checkout, excluding Git and all local runtime/build state."""
from pathlib import Path
import csv
import hashlib

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.git','.venv','venv','runs','work','.work','build','dist','release-assets','__pycache__',
            '.pytest_cache','.mypy_cache','.ruff_cache','node_modules','generated'}


def main():
    files = sorted(p for p in ROOT.rglob('*') if p.is_file()
                   and not set(p.relative_to(ROOT).parts)&EXCLUDED and p.suffix not in ('.pyc','.pyo')
                   and p.name not in ('.DS_Store','Thumbs.db'))
    manifest=ROOT/'packaging/source-manifest.csv'
    count=0
    with manifest.open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['path','bytes','sha256'])
        for p in files:
            if p != manifest:
                writer.writerow([p.relative_to(ROOT).as_posix(),p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()]);count+=1
    print(f'Sealed {count} source/data files; local private and build directories excluded')


if __name__ == '__main__':
    main()
