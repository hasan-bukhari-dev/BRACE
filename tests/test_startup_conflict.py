import socket
import pytest
import launch

def test_default_conflict_reserves_another_loopback_port(monkeypatch):
    monkeypatch.delenv('BRACE_PORT',raising=False)
    blocker=socket.socket();blocker.bind(('127.0.0.1',0));blocker.listen()
    port=blocker.getsockname()[1]
    monkeypatch.setattr(launch,'local_port',lambda:port)
    try:
        listener,chosen=launch.reserve_port()
        try:assert chosen>port and listener.getsockname()==('127.0.0.1',chosen)
        finally:listener.close()
    finally:blocker.close()

def test_explicit_occupied_port_fails_without_browser(monkeypatch):
    blocker=socket.socket();blocker.bind(('127.0.0.1',0));blocker.listen()
    monkeypatch.setenv('BRACE_PORT',str(blocker.getsockname()[1]))
    try:
        with pytest.raises(SystemExit,match='No browser was opened'):launch.reserve_port()
    finally:blocker.close()

def test_reserved_port_is_used_by_server_and_origin_configuration(monkeypatch):
    probe=socket.socket();probe.bind(('127.0.0.1',0));port=probe.getsockname()[1];probe.close()
    monkeypatch.setenv('BRACE_PORT',str(port))
    monkeypatch.setenv('BRACE_NO_BROWSER','1')
    seen=[]
    class FakeServer:
        def __init__(self,config):pass
        def run(self,sockets):seen.append((int(launch.os.environ['BRACE_PORT']),sockets[0].getsockname()))
    monkeypatch.setattr(launch.uvicorn,'Server',FakeServer)
    launch.main()
    assert seen[0][0]==seen[0][1][1] and seen[0][1][0]=='127.0.0.1'
