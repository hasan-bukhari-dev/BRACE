"""Release-boundary regression: browsers must be able to execute shipped modules."""
import mimetypes
from fastapi.testclient import TestClient
from brace_app.server import app


def test_windows_mime_override_cannot_disable_modules(monkeypatch):
    mimetypes.init()
    monkeypatch.setitem(mimetypes.types_map, '.js', 'text/plain')
    with TestClient(app) as client:
        for path in ('js/boot.js', 'js/space.js', 'app.js', 'js/datasets.js'):
            response = client.get('/assets/' + path)
            assert response.status_code == 200
            assert response.headers['content-type'].startswith('text/javascript')
            assert response.headers['cache-control'] == 'no-store'
        assert client.get('/assets/v6.css').headers['content-type'].startswith('text/css')


def test_missing_module_remains_an_error():
    with TestClient(app) as client:
        assert client.get('/assets/js/missing-recovery-module.js').status_code == 404
