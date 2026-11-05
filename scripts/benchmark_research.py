"""Measured loopback workflow benchmark, isolated from the user's runtime."""
from pathlib import Path
import ctypes,json,os,socket,subprocess,sys,time,urllib.request,uuid
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work'/('benchmark_'+uuid.uuid4().hex[:8]);OUT.mkdir(parents=True)
def memory(pid):
    if os.name!='nt':return None
    class Counters(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(k,ctypes.c_size_t) for k in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);psapi=ctypes.WinDLL('psapi',use_last_error=True)
    kernel.OpenProcess.restype=ctypes.c_void_p;kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
    handle=kernel.OpenProcess(0x410,False,pid)
    if not handle:return None
    try:
        counter=Counters();counter.cb=ctypes.sizeof(counter)
        if not psapi.GetProcessMemoryInfo(handle,ctypes.byref(counter),counter.cb):return None
        return {'peak_working_set_bytes':counter.PeakWorkingSetSize,'current_working_set_bytes':counter.WorkingSetSize,'private_bytes':counter.PrivateUsage}
    finally:kernel.CloseHandle(handle)
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
env=dict(os.environ,BRACE_PORT=str(port),BRACE_NO_BROWSER='1',BRACE_RUNS_DIR=str(OUT/'runs'))
base='http://127.0.0.1:'+str(port)
def api(path,body=None):
    data=json.dumps(body).encode() if body is not None else None
    request=urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json'} if body is not None else {})
    with urllib.request.urlopen(request,timeout=120) as response:return response.read()
report={'scope':'Local HTTP end-to-end API timings with persistence; warm filesystem caches, no browser rendering or internet transfer included. Not a capacity benchmark.',
    'python':sys.version,'platform':sys.platform,'startup_seconds':None,'race_seconds':[]}
with (OUT/'server.log').open('w') as log:
    start=time.perf_counter();process=subprocess.Popen([sys.executable,'-u','launch.py'],cwd=ROOT,env=env,stdout=log,stderr=log)
    try:
        while time.perf_counter()-start<60:
            if process.poll() is not None:raise RuntimeError('Benchmark server exited; inspect '+str(OUT/'server.log'))
            try:health=json.loads(api('/api/health'));break
            except (OSError,TimeoutError):time.sleep(.1)
        else:raise TimeoutError('Application did not become ready in 60 seconds')
        report['startup_seconds']=time.perf_counter()-start
        start=time.perf_counter();pair=json.loads(api('/api/datasets/reviewed-public',{'reviewed':True}));report['public_registration_seconds']=time.perf_counter()-start
        body={'mode':'race','name':'Measured public workflow','datasets':{r:d['id'] for r,d in pair['datasets'].items()},'race_config':pair['race_config']}
        start=time.perf_counter();check=json.loads(api('/api/dataset-analysis/preflight',body));assert check['eligible'];report['eligibility_seconds']=time.perf_counter()-start
        for _ in range(3):
            start=time.perf_counter();run=json.loads(api('/api/dataset-analysis/run',body));report['race_seconds'].append(time.perf_counter()-start)
            assert run['race']['aggregate']['supported']==14
        start=time.perf_counter();bundle=api('/api/embrace/'+run['id']);report['evidence_seconds']=time.perf_counter()-start;report['evidence_bytes']=len(bundle)
        # Windows virtual-environment python.exe may be a small redirector.
        # Measure the actual serving interpreter, never the launcher stub.
        report['memory_after_three_runs']=memory(health['process_id'])
        report['workload']={'source_samples':101,'target_samples':87,'prepared_features_per_cohort':10000,'source_expression_bytes':(ROOT/'examples/public_er_pair/prepared/source_expression.tsv').stat().st_size,'target_expression_bytes':(ROOT/'examples/public_er_pair/prepared/target_expression.tsv').stat().st_size}
        report['status']='PASS'
    finally:
        if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
        else:process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()
(ROOT/'work/benchmark.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
