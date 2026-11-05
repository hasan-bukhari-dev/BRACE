"""Exercise a freshly built Windows app using only its bundled runtime."""
import argparse
import csv
import hashlib
import io
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


def main(app: Path, output: Path, port: int):
    app = app.resolve(strict=True)
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('Choose a new empty verification directory; existing data is never removed.')
    output.mkdir(parents=True, exist_ok=True)
    address = f'http://127.0.0.1:{port}'
    env = dict(os.environ, BRACE_DATA_DIR=str(output / 'data'), BRACE_PORT=str(port),
               OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', BRACE_NO_BROWSER='1')
    process = None
    started = time.perf_counter()

    def request(path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(address + path, data=data,
            headers={'Content-Type': 'application/json'} if data is not None else {})
        with urllib.request.urlopen(req, timeout=180) as response:
            raw = response.read()
            return json.loads(raw) if response.headers.get_content_type() == 'application/json' else raw

    def start():
        nonlocal process
        process = subprocess.Popen([str(app), '--headless'], env=env, cwd=app.parent,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError('Bundled application exited during startup; inspect its isolated desktop log.')
            try:
                return request('/api/health')
            except (OSError, urllib.error.URLError):
                time.sleep(.2)
        raise RuntimeError('Bundled application did not become ready within 60 seconds.')

    def stop():
        nonlocal process
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process = None

    try:
        health = start()
        assert health['geo_expression_data_available']
        prepared = request('/api/datasets/reviewed-public', {'reviewed': True})
        body = {'name': 'Portable public ER verification', 'mode': 'race',
                'datasets': {role: record['id'] for role, record in prepared['datasets'].items()},
                'race_config': prepared['race_config']}
        assert request('/api/dataset-analysis/preflight', body)['eligible']
        run = request('/api/dataset-analysis/run', body)
        assert run['race']['aggregate']['supported'] == 14
        gene = run['race']['genes'][0]['feature_id']
        assert request(f"/api/race/studies/{run['id']}/gene?feature_id={gene}")['feature']['feature_id'] == gene
        assert request(f"/api/trace/studies/{run['id']}?feature_id={gene}")['analysis'] == 'race'
        bundle = request('/api/embrace/' + run['id'])
        with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
            assert archive.testzip() is None
            for row in csv.DictReader(io.StringIO(archive.read('FILE_SHA256_MANIFEST.csv').decode())):
                assert hashlib.sha256(archive.read(row['path'])).hexdigest() == row['sha256']
            assert json.loads(archive.read('reproducibility_manifest.json'))['study_name'] == body['name']
            assert json.loads(archive.read('reproducibility_manifest.json'))['embrace_version']=='brace-embrace/0.8.1'
            assert 'BIOLOGICAL_CONTEXT.json' in archive.namelist()
            assert json.loads(archive.read('BIOLOGICAL_CONTEXT.json'))
            lineage=json.loads(archive.read('DATASET_LINEAGE.json'))
            assert lineage['source']['parent_records'][0]['source']['url'].startswith('https://ftp.ncbi.nlm.nih.gov/')
            assert lineage['source']['parent_records'][0]['assets']['original']['sha256']
        (output / 'public-evidence.zip').write_bytes(bundle)
        stop()
        start()
        reopened = request('/api/runs/' + run['id'])
        assert reopened['name'] == run['name'] and reopened['datasets'] == run['datasets']
        assert reopened['race']['aggregate'] == run['race']['aggregate']
        synthetic = request('/api/demo/synthetic', {})
        replay = request('/api/dataset-analysis/replay', {'name': 'Portable artificial freeze verification',
            'frozen_run_id': synthetic['id'], 'target_dataset_id': synthetic['datasets']['target']})
        assert replay['kind'] == 'synthetic' and replay['replay']['evaluation_possible']
        report = dict(status='PASS', platform='Windows x64 portable', health=health,
            executable_sha256=hashlib.sha256(app.read_bytes()).hexdigest(),
            public_aggregate=run['race']['aggregate'], public_face_and_trace=True,
            export_all_member_hashes_verified=True, reopens_after_process_restart=True,
            original_acquisition_ancestor_receipts_included=True,
            synthetic_freeze_keeps_artificial_provenance=True,
            elapsed_seconds=time.perf_counter() - started,
            not_tested=['Installer registration/uninstall', 'macOS/Linux binaries', 'Human usability acceptance'])
        (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, indent=2))
    finally:
        stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8877)
    options = parser.parse_args()
    main(options.app, options.out, options.port)
