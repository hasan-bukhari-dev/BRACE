"""Data placement and release boundaries, independent of the freezer tool."""
import importlib.util
from pathlib import Path
import json
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('brace_desktop', ROOT/'desktop.py')
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)


@pytest.mark.parametrize('system,env,tail', [
    ('win32', {}, 'AppData/Local/BRACE'),
    ('darwin', {}, 'Library/Application Support/BRACE'),
    ('linux', {}, '.local/share/BRACE'),
])
def test_desktop_data_outside_installed_resources(tmp_path, system, env, tail):
    assert desktop.data_directory(env, system, tmp_path) == tmp_path/tail


def test_explicit_data_and_xdg_paths(tmp_path):
    assert desktop.data_directory({'BRACE_DATA_DIR':str(tmp_path/'chosen')}) == (tmp_path/'chosen').resolve()
    assert desktop.data_directory({'XDG_DATA_HOME':str(tmp_path/'xdg')}, 'linux', tmp_path) == tmp_path/'xdg/BRACE'
    assert desktop.data_directory({'LOCALAPPDATA':str(tmp_path/'local')}, 'win32', tmp_path) == tmp_path/'local/BRACE'


def test_public_reference_assets_are_in_distributed_data_roots():
    pins = json.loads((ROOT/'docs/PASS03_PUBLIC_REFERENCE.json').read_text())
    assert pins
    for relative in pins:
        assert relative.startswith('examples/') and (ROOT/relative).is_file()
    assert (ROOT/'docs/PASS05_ARCHIVED_REFERENCE.json').is_file()


def test_version_and_no_bundled_private_runs():
    assert desktop.VERSION == (ROOT/'VERSION').read_text().strip()
    ignore = (ROOT/'.gitignore').read_text()
    assert 'runs/' in ignore and '.venv/' in ignore and '.env' in ignore
    source = (ROOT/'packaging/BRACE.spec').read_text()
    assert "'runs'" not in source and 'user_data' not in source
