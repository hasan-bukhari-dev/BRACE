"""Test-only ASGI adapter for browser verification on spare port 8766.

The installed production app occupies 8765. Normalize only this test origin
to the app's existing canonical localhost origin; foreign origins are unchanged.
Not imported by the production launcher.
"""
from brace_app.server import app as production_app

async def app(scope,receive,send):
    if scope['type']=='http':
        scope=dict(scope)
        scope['headers']=[(k,b'http://127.0.0.1:8765' if k==b'origin' and v==b'http://127.0.0.1:8766' else v) for k,v in scope['headers']]
    await production_app(scope,receive,send)
