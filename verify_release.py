"""Verify the release SHA manifest without overwriting or executing other code."""
import csv
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
INDEX=ROOT/'FILE_SHA256_MANIFEST.csv'

def main():
    rows=list(csv.DictReader(INDEX.open(encoding='utf-8',newline='')))
    bad=[]
    for row in rows:
        p=ROOT/row['path']
        if not p.is_file():bad.append(f"MISSING {row['path']}");continue
        if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256'] or p.stat().st_size!=int(row['bytes']):
            bad.append(f"MISMATCH {row['path']}")
    print(f"BRACE release verification: {len(rows)-len(bad)}/{len(rows)} files verified")
    for item in bad:print(item)
    return 1 if bad else 0
if __name__=='__main__':raise SystemExit(main())
