"""Hash/check prepared local wheels and their interpreter target, without network."""
import hashlib,json,platform,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];FOLDER=ROOT/'wheelhouse';MANIFEST=FOLDER/'WHEELHOUSE_SHA256.json'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    wheels=sorted(FOLDER.glob('*.whl'));target=dict(python=list(sys.version_info[:2]),machine=platform.machine(),platform=sys.platform)
    if '--verify' in sys.argv:
        saved=json.loads(MANIFEST.read_text());assert saved['target']==target,'Wheelhouse requires matching Python minor version and architecture'
        assert saved['requirements_sha256']==digest(ROOT/'requirements-release.txt'),'Requirements changed'
        assert set(saved['files'])=={p.name for p in wheels},'Wheel inventory differs'
        for p in wheels:assert saved['files'][p.name]==dict(sha256=digest(p),bytes=p.stat().st_size),'Wheel changed: '+p.name
        print(str(len(wheels))+' local wheel hashes verified.');return
    assert wheels,'No wheels were downloaded'
    MANIFEST.write_text(json.dumps(dict(target=target,requirements_sha256=digest(ROOT/'requirements-release.txt'),files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in wheels}),indent=2)+'\n')
    print(str(len(wheels))+' wheels hashed for '+str(target))
if __name__=='__main__':
    try:main()
    except (AssertionError,OSError,ValueError,KeyError) as exc:print('Offline wheel verification failed: '+str(exc));raise SystemExit(1)
