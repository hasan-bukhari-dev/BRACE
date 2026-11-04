"""Package an unpublished candidate; verify every source static asset first."""
import csv,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(path,base,files,prefix):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(files):z.write(p,prefix+'/'+p.relative_to(base).as_posix())
    with zipfile.ZipFile(path) as z:assert z.testzip() is None


def main():
    version=(ROOT/'VERSION').read_text().strip();assets=ROOT/'release-assets';assets.mkdir(exist_ok=True)
    bundle=ROOT/'dist/BRACE';static=ROOT/'brace_app/static';bundled=bundle/'_internal/brace_app/static'
    verified={}
    for p in static.rglob('*'):
        if p.is_file():
            relative=p.relative_to(static);assert digest(p)==digest(bundled/relative),relative
            verified[relative.as_posix()]=digest(p)
    portable=assets/f'BRACE-{version}-windows-x64-portable.zip'
    archive(portable,bundle,[p for p in bundle.rglob('*') if p.is_file()],'BRACE')
    rows=list(csv.DictReader((ROOT/'packaging/source-manifest.csv').open(encoding='utf-8')))
    for row in rows:assert digest(ROOT/row['path'])==row['sha256'],row['path']
    source=assets/f'BRACE-{version}-source.zip'
    archive(source,ROOT,[ROOT/r['path'] for r in rows]+[ROOT/'packaging/source-manifest.csv'],'BRACE')
    receipt=assets/f'BRACE-{version}-package-verification.json'
    receipt.write_text(json.dumps({'version':version,'status':'PASS','scope':'Archive integrity and source/bundle static equality; installer acceptance separate',
        'static_assets':verified,'portable_sha256':digest(portable),'source_sha256':digest(source)},indent=2),encoding='utf-8')
    names=[portable,source,receipt]
    (assets/f'BRACE-{version}-SHA256SUMS.txt').write_text(''.join(digest(p)+'  '+p.name+'\n' for p in names),encoding='utf-8')
    print('\n'.join(str(p) for p in names))


if __name__=='__main__':main()
