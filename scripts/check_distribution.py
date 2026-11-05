"""Exercise an actual bundled executable without importing project Python code."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
import zipfile


def main():
    p = argparse.ArgumentParser()
    p.add_argument('executable', type=Path)
    p.add_argument('--output', type=Path, default=Path('release-assets/BINARY_VERIFICATION.json'))
    args = p.parse_args()
    executable = args.executable.resolve()
    with tempfile.TemporaryDirectory(prefix='brace-binary-check-') as tmp:
        root = Path(tmp)
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]
        env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME','BRACE_PORT','BRACE_RUNS_DIR','BRACE_DATA_DIR')}
        env.update(BRACE_PORT=str(port), BRACE_RUNS_DIR=str(root/'runs'), BRACE_DATA_DIR=str(root/'data'),
                   BRACE_NO_BROWSER='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
        checks = []
        log = (root/'server.log').open('w')
        process = subprocess.Popen([str(executable), '--headless'], cwd=root, env=env,
                                   stdout=log, stderr=subprocess.STDOUT)
        base = 'http://127.0.0.1:'+str(port)
        def get(path):
            with urllib.request.urlopen(base+path, timeout=90) as r:
                return r.read()
        def post(path):
            with urllib.request.urlopen(urllib.request.Request(base+path, method='POST'), timeout=120) as r:
                return json.load(r)
        try:
            for _ in range(900):
                if process.poll() is not None:
                    raise RuntimeError('Bundled server exited: '+(root/'server.log').read_text(errors='replace'))
                try:
                    health = json.loads(get('/api/health'))
                    break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Bundled server readiness timeout')
            assert health['geo_expression_data_available']
            checks.append('Bundled runtime starts from unrelated writable cwd with project Python paths removed')
            assert b'BRACE' in get('/') and b'wordmark' in get('/assets/js/wordmark.js')
            public = json.loads(get('/api/example/public-er'))
            assert public['race']['aggregate']['supported'] == 14 and public['race']['aggregate']['selected'] == 20
            checks.append('Pinned real public result available: 14/20')
            past = json.loads(get('/api/example/cptac'))
            assert past['validation']['n'] == 680 and past['validation']['metrics']['n_correct'] == 668
            checks.append('Original historical prediction evidence: 668/680')
            cohorts = post('/api/demo/public-cohorts')
            assert cohorts['shift']['feature_coverage']['shared'] == 10000
            assert cohorts['shift']['inference']['available'] is False
            assert all(g['ks_bh_q_exploratory'] is None for g in cohorts['shift']['gene_shifts'])
            assert json.loads(get('/api/runs/'+cohorts['id']))['id'] == cohorts['id']
            with zipfile.ZipFile(io.BytesIO(get('/api/embrace/'+cohorts['id']))) as z:
                assert z.testzip() is None
            checks.append('Real public CE demo computes 10,000 shared features, withholds invalid inference, reopens and exports')
            synthetic = post('/api/demo/synthetic')
            assert synthetic['kind'] == 'synthetic' and synthetic['shift']['feature_coverage']['shared'] == 120
            checks.append('Frozen scientific stack performs actual synthetic source-CV/model/target/shift computation')
            package = get('/api/embrace/'+synthetic['id'])
            with zipfile.ZipFile(io.BytesIO(package)) as z:
                assert z.testzip() is None
                manifest = json.loads(z.read('reproducibility_manifest.json'))
                for name, value in manifest['artifact_sha256'].items():
                    assert hashlib.sha256(z.read(name)).hexdigest() == value['sha256'], name
            checks.append('Actual computed EMBRACE ZIP CRC and every recorded artifact SHA-256 agree')
            assert json.loads(get('/api/example/public-er/exclusions/target'))['downloaded_samples'] == 90
            checks.append('Public preparation and additive V6 endpoints present')
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({'status':'PASS', 'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
                'checks':checks, 'scope':'Actual current-OS bundled backend; no physical-device or native GUI acceptance implied'},indent=2)+'\n')
            print(json.dumps({'status':'PASS','checks':checks},indent=2))
        finally:
            process.terminate()
            process.wait(timeout=20)
            log.close()


if __name__ == '__main__':
    main()
