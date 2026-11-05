"""Start BRACE on 127.0.0.1 only; never expose the research app to a network."""
from __future__ import annotations
import os,threading,webbrowser,socket,errno
import uvicorn
from brace_app.local_settings import local_port

def reserve_port():
    requested=local_port()
    candidates=[requested] if 'BRACE_PORT' in os.environ else range(requested,requested+21)
    for port in candidates:
        listener=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            if hasattr(socket,'SO_EXCLUSIVEADDRUSE'):
                listener.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
            listener.bind(('127.0.0.1',port))
            listener.listen(128)
            return listener,port
        except OSError as exc:
            listener.close()
            if exc.errno not in (errno.EADDRINUSE,10048) and getattr(exc,'winerror',None)!=10048:
                raise
    raise SystemExit('BRACE could not reserve a local port. Leave other services running; set BRACE_PORT to an unused port and start again. No browser was opened.')

def main():
    listener,port=reserve_port()
    # Set this before the application is imported: write-origin checks must use
    # the exact port that was reserved, including an automatic fallback.
    os.environ['BRACE_PORT']=str(port)
    address=f'http://127.0.0.1:{port}'
    from brace_app.version import VERSION
    print('\n BRACE '+VERSION+' · Research Workbench')
    if port!=8765:print(' Using an available local port; other services were left running.')
    print(' Local address: '+address)
    print(' Press Ctrl+C to stop.\n')
    server=uvicorn.Server(uvicorn.Config('brace_app.server:app',host='127.0.0.1',port=port,log_level='warning',access_log=False))
    finished=threading.Event()
    def open_when_ready():
        while not finished.wait(.05):
            if server.started:
                webbrowser.open(address)
                return
    if os.environ.get('BRACE_NO_BROWSER') != '1':
        threading.Thread(target=open_when_ready,daemon=True).start()
    try:server.run(sockets=[listener])
    finally:
        finished.set()
        listener.close()

if __name__=='__main__':main()
