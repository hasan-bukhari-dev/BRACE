"""Build the current platform's bundled app and record actual build dependencies."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def notices():
    target = ROOT/'packaging/generated'
    target.mkdir(parents=True, exist_ok=True)
    dependencies = []
    names = [l.split('==')[0] for l in (ROOT/'requirements-release.txt').read_text().splitlines() if '==' in l]
    names += ['PyInstaller', 'pyinstaller-hooks-contrib']
    for name in names:
        dist = metadata.distribution(name)
        info = {'name': dist.metadata['Name'], 'version': dist.version,
                'license_expression': dist.metadata.get('License-Expression'),
                'license_metadata': dist.metadata.get('License'), 'notices': []}
        for file in dist.files or []:
            text = str(file).replace('\\', '/')
            base = Path(text).name.lower()
            if ('.dist-info/' in text or '.egg-info/' in text) and (
                    base.startswith(('license', 'licence', 'copying', 'notice', 'authors')) or '/licenses/' in text):
                source = Path(dist.locate_file(file))
                if source.is_file():
                    destination = target/'licenses'/name/Path(text).name
                    if destination.exists() and destination.read_bytes() != source.read_bytes():
                        destination = destination.with_name(hashlib.sha256(text.encode()).hexdigest()[:10]+'-'+destination.name)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, destination)
                    info['notices'].append(destination.relative_to(target).as_posix())
        dependencies.append(info)
    python_license = Path(sys.base_prefix)/'LICENSE.txt'
    if not python_license.exists():
        python_license = Path(sys.base_prefix)/'LICENSE'
    if not python_license.exists():
        raise RuntimeError('The Python distribution license is required for a bundled runtime')
    shutil.copyfile(python_license, target/'PYTHON_LICENSE.txt')
    (target/'BUILD_ENVIRONMENT.json').write_text(json.dumps({
        'python': sys.version, 'platform': platform.platform(), 'architecture': platform.machine(),
        'scope': 'Installed pinned runtime/build dependencies; not a claim that every package is imported into the executable',
        'packages': dependencies}, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--incremental', action='store_true', help='Reuse PyInstaller analysis; release builds clean by default')
    options = parser.parse_args()
    notices()
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm']
    if not options.incremental:
        command.append('--clean')
    subprocess.run(command + [str(ROOT/'packaging/BRACE.spec')], cwd=ROOT, check=True)
    version = (ROOT/'VERSION').read_text().strip()
    system = {'win32': 'windows', 'darwin': 'macos'}.get(sys.platform, 'linux')
    arch = {'amd64': 'x64', 'x86_64': 'x64', 'aarch64': 'arm64'}.get(platform.machine().lower(), platform.machine().lower())
    assets = ROOT/'release-assets'
    assets.mkdir(exist_ok=True)
    archive = assets/f'BRACE-{version}-{system}-{arch}-portable.zip'
    folder = ROOT/('dist/BRACE.app' if sys.platform == 'darwin' else 'dist/BRACE')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                z.write(path, path.relative_to(folder.parent))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
    (assets/(archive.name+'.sha256')).write_text(
        hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
    print(archive)


if __name__ == '__main__':
    main()
