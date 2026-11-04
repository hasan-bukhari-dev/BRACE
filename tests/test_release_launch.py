"""Real launcher and offline-wheel failure paths, without installing globally."""
import os,shutil,subprocess,sys
from pathlib import Path
import pytest
BASE=Path(__file__).resolve().parents[1]
def script_root(tmp_path):
    root=tmp_path/'release with spaces';(root/'scripts').mkdir(parents=True)
    for name in ('WINDOWS_PYTHON.bat','check_python.py','wheelhouse_manifest.py'):shutil.copy2(BASE/'scripts'/name,root/'scripts'/name)
    return root
@pytest.mark.skipif(os.name!='nt',reason='Windows batch launcher')
def test_windows_python_explicit_path_with_spaces_and_missing_interpreter(tmp_path):
    root=script_root(tmp_path);env=dict(os.environ,BRACE_PYTHON_EXE=sys.executable)
    result=subprocess.run([os.environ['COMSPEC'],'/d','/c',r'call scripts\WINDOWS_PYTHON.bat'],cwd=root,env=env,capture_output=True,text=True,timeout=20)
    assert result.returncode==0 and 'selected' in result.stdout
    env['BRACE_PYTHON_EXE']=str(root/'missing python.exe')
    result=subprocess.run([os.environ['COMSPEC'],'/d','/c',r'call scripts\WINDOWS_PYTHON.bat'],cwd=root,env=env,capture_output=True,text=True,timeout=20)
    assert result.returncode!=0 and 'not found' in result.stdout
@pytest.mark.parametrize('mutation',['wheel','requirements','target'])
def test_offline_wheelhouse_rejects_corruption_and_wrong_target(tmp_path,mutation):
    root=script_root(tmp_path);folder=root/'wheelhouse';folder.mkdir();wheel=folder/'explicit_test_fixture.whl';wheel.write_bytes(b'not installed: hash-boundary fixture')
    requirements=root/'requirements-release.txt';requirements.write_text('fixture==1\n')
    command=[sys.executable,'scripts/wheelhouse_manifest.py']
    subprocess.run(command,cwd=root,check=True,capture_output=True)
    subprocess.run(command+['--verify'],cwd=root,check=True,capture_output=True)
    if mutation=='wheel':wheel.write_bytes(b'changed')
    elif mutation=='requirements':requirements.write_text('fixture==2\n')
    else:
        import json
        p=folder/'WHEELHOUSE_SHA256.json';m=json.loads(p.read_text());m['target']['python']=[0,0];p.write_text(json.dumps(m))
    result=subprocess.run(command+['--verify'],cwd=root,capture_output=True,text=True)
    assert result.returncode!=0 and 'verification failed' in result.stdout

@pytest.mark.parametrize('port',['80','65536','8766.0','127.0.0.1:8766'])
def test_port_configuration_fails_closed(monkeypatch,port):
    from brace_app.local_settings import local_port
    monkeypatch.setenv('BRACE_PORT',port)
    with pytest.raises(ValueError):local_port()

def test_nondefault_port_origin_is_exact_and_loopback_only(monkeypatch):
    from brace_app import server
    from fastapi.testclient import TestClient
    monkeypatch.setattr(server,'LOCAL_PORT',8766)
    with TestClient(server.app) as client:
        assert client.post('/api/analyze',headers={'origin':'http://127.0.0.1:8766'}).status_code==422
        for origin in ('http://127.0.0.1:8765','http://evil.example:8766','null'):
            assert client.post('/api/analyze',headers={'origin':origin}).status_code==403
