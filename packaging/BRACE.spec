# Build on the target OS. No scientific source or evidence is generated here.
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, copy_metadata
ROOT = Path(SPECPATH).parent
datas = [(str(ROOT/name), name) for name in ('examples', 'templates')]
datas += [(str(ROOT/'brace_app/static'), 'brace_app/static'),
          (str(ROOT/'brace_app/task_capabilities.json'), 'brace_app'),
          (str(ROOT/'packaging/brace.ico'), '.'),
          (str(ROOT/'packaging/generated'), 'distribution-notices')]
for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md', 'DATA_SOURCES.md', 'VERSION'):
    datas.append((str(ROOT/name), '.'))
for name in ('PASS03_PUBLIC_REFERENCE.json', 'PASS05_ARCHIVED_REFERENCE.json'):
    datas.append((str(ROOT/'docs'/name), 'docs'))
for line in (ROOT/'requirements-release.txt').read_text().splitlines():
    if '==' in line:
        datas += copy_metadata(line.split('==')[0])
a = Analysis([str(ROOT/'desktop.py')], pathex=[str(ROOT)], binaries=[], datas=datas,
             hiddenimports=collect_submodules('brace_app')+collect_submodules('brace_core'),
             hookspath=[], runtime_hooks=[],
             excludes=['pytest', 'IPython', 'jupyter', 'matplotlib', 'pandas'],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='BRACE',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, icon=str(ROOT/'packaging/brace.ico'))
collection = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='BRACE')
if __import__('sys').platform == 'darwin':
    app = BUNDLE(collection, name='BRACE.app', bundle_identifier='org.brace.workbench',
                 info_plist={'CFBundleShortVersionString':'1.0.0',
                             'NSHighResolutionCapable':True})
