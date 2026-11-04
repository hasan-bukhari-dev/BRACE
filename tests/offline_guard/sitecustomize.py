"""TEST ONLY: deny non-loopback outbound networking in the acceptance process.

Enabled explicitly using PYTHONPATH. Never imported by the normal launcher.
"""
import ipaddress,os,sys
def local(host):
    if host in ('localhost',None,''):return True
    try:return ipaddress.ip_address(str(host)).is_loopback
    except ValueError:return False
def guard(event,args):
    if event=='socket.connect':
        address=args[1]
        if isinstance(address,tuple) and not local(address[0]):deny(event,address[0])
    elif event=='socket.getaddrinfo' and not local(args[0]):deny(event,args[0])
def deny(event,host):
    path=os.environ.get('BRACE_NETWORK_DENIAL_LOG')
    if path:
        with open(path,'a',encoding='utf-8') as stream:stream.write(event+' '+str(host)+'\n')
    raise PermissionError('Acceptance test denies non-loopback networking')
sys.addaudithook(guard)

# Optional test-only evidence that ASGI/Uvicorn shutdown completed before exit.
if os.environ.get('BRACE_SHUTDOWN_MARKER'):
    import uvicorn
    original_shutdown=uvicorn.Server.shutdown
    async def checked_shutdown(self,*args,**kwargs):
        await original_shutdown(self,*args,**kwargs)
        with open(os.environ['BRACE_SHUTDOWN_MARKER'],'w',encoding='utf-8') as stream:stream.write('Uvicorn graceful shutdown completed\n')
    uvicorn.Server.shutdown=checked_shutdown
