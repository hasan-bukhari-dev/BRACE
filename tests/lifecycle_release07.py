"""Measured two-start lifecycle on an explicitly supplied offline-installed copy."""
import argparse,ctypes,json,os,signal,subprocess,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
def peak(pid):
    from ctypes import wintypes as w
    class Counters(ctypes.Structure):
        _fields_=[('cb',w.DWORD),('PageFaultCount',w.DWORD)]+[(name,ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    k=ctypes.WinDLL('kernel32',use_last_error=True);p=ctypes.WinDLL('psapi',use_last_error=True);k.OpenProcess.restype=w.HANDLE;k.CloseHandle.argtypes=[w.HANDLE];p.GetProcessMemoryInfo.argtypes=[w.HANDLE,ctypes.POINTER(Counters),w.DWORD]
    h=k.OpenProcess(0x0400|0x0010,False,pid);c=Counters();c.cb=ctypes.sizeof(c)
    try:
        if not h or not p.GetProcessMemoryInfo(h,ctypes.byref(c),c.cb):return None
        return c.PeakWorkingSetSize
    finally:
        if h:k.CloseHandle(h)
def own_python_tree(root_pid):
    from ctypes import wintypes as w
    class Process(ctypes.Structure):
        _fields_=[('dwSize',w.DWORD),('cntUsage',w.DWORD),('th32ProcessID',w.DWORD),('th32DefaultHeapID',ctypes.c_size_t),('th32ModuleID',w.DWORD),('cntThreads',w.DWORD),('th32ParentProcessID',w.DWORD),('pcPriClassBase',w.LONG),('dwFlags',w.DWORD),('szExeFile',w.WCHAR*260)]
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateToolhelp32Snapshot.restype=w.HANDLE;k.Process32FirstW.argtypes=[w.HANDLE,ctypes.POINTER(Process)];k.Process32NextW.argtypes=[w.HANDLE,ctypes.POINTER(Process)];k.CloseHandle.argtypes=[w.HANDLE]
    snapshot=k.CreateToolhelp32Snapshot(2,0);row=Process();row.dwSize=ctypes.sizeof(row);records=[]
    try:
        ok=k.Process32FirstW(snapshot,ctypes.byref(row))
        while ok:
            records.append((row.th32ProcessID,row.th32ParentProcessID,row.szExeFile));ok=k.Process32NextW(snapshot,ctypes.byref(row))
    finally:k.CloseHandle(snapshot)
    owned={root_pid}
    for _ in range(4):owned.update(pid for pid,parent,name in records if parent in owned)
    return [{'pid':pid,'parent_pid':parent,'name':name,'peak_working_set_bytes':peak(pid)} for pid,parent,name in records if pid in owned and 'python' in name.lower()]
def main(app,runs,record,scratch):
    app=app.resolve();runs=runs.resolve();scratch=scratch.resolve();scratch.mkdir(exist_ok=True);url='http://127.0.0.1:8766';opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    environment=dict(os.environ,BRACE_PORT='8766',BRACE_NO_BROWSER='1',BRACE_RUNS_DIR=str(runs),PYTHONIOENCODING='utf-8',PYTHONPATH=str(app/'tests/offline_guard'),BRACE_NETWORK_DENIAL_LOG=str(scratch/'nonlocal_denials.log'))
    attempts=[];process=None
    candidates=sorted(p.parent.parent.name for p in runs.glob('*/race/race_result.json') if len(p.parent.parent.name)==32)
    assert candidates,'Run rehearse_release07.py first to create a real saved user RACE run'
    run_id=candidates[0]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True);context=browser.new_context(viewport={'width':1280,'height':720},reduced_motion='reduce');page=context.new_page();page.set_default_timeout(30000);expect.set_options(timeout=30000)
        try:
            for number in (1,2):
                marker=scratch/f'shutdown{number}.txt'
                if marker.exists():marker.unlink()
                environment['BRACE_SHUTDOWN_MARKER']=str(marker)
                log=(scratch/f'server{number}.log').open('w',encoding='utf-8');start=time.perf_counter()
                process=subprocess.Popen([str(app/'.venv/Scripts/python.exe'),'launch.py'],cwd=app,env=environment,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                while True:
                    if process.poll() is not None:raise RuntimeError('Launch failed: '+(scratch/f'server{number}.log').read_text())
                    try:
                        with opener.open(url+'/api/health',timeout=2) as response:health=json.load(response)
                        if health.get('version')=='1.0.0':break
                    except (OSError,ValueError):pass
                    if time.perf_counter()-start>60:raise TimeoutError('Startup exceeded60seconds')
                    time.sleep(.05)
                ready=time.perf_counter()-start
                if number==1:
                    page.goto(url);page.wait_for_function("document.documentElement.dataset.ready==='true'");page.locator('#explore-public').click();page.locator('#study-results').click();page.locator('[data-select-gene="135112"]').click();expect(page.locator('#face-body .expression-plot')).to_have_count(2);page.locator('#trace-gene').click()
                else:
                    page.reload();page.wait_for_function("document.documentElement.dataset.ready==='true'");expect(page.locator('#race-trace-panel')).to_contain_text('135112');assert 'public_er_pass2' in page.locator('#context').inner_text()
                completed=json.loads((runs/run_id/'race/race_result.json').read_text())
                saved=page.request.get(url+'/api/runs/'+run_id);assert saved.status==200 and saved.json()['race']['genes']==completed['genes']
                tree=own_python_tree(process.pid);stop=time.perf_counter();graceful=True;note='CTRL_BREAK sent to own process group'
                try:process.send_signal(signal.CTRL_BREAK_EVENT);process.wait(timeout=15)
                except (OSError,subprocess.TimeoutExpired):
                    graceful=False;note='Console signal unavailable; own test process terminated';process.terminate();process.wait(timeout=10)
                # The venv redirector can exit before the actual interpreter.
                until=time.perf_counter()+10
                while not marker.exists() and time.perf_counter()<until:time.sleep(.05)
                graceful=graceful and marker.exists();stopped=time.perf_counter()-stop;code=process.returncode;process=None;log.close()
                attempts.append(dict(start=number,ready_s=ready,shutdown_s=stopped,process_exit=code,graceful_signal=graceful,shutdown_completed_marker=marker.exists(),shutdown_note=note,owned_python_processes=tree,peak_server_working_set_bytes=max((r['peak_working_set_bytes'] or 0 for r in tree),default=0),memory_scope='Largest peak working set among owned Python interpreter/venv-redirector tree; after saved evidence retrieval, not fresh computation',persistent_user_run_checked=True,tab_gene_trace_restored=(number==2)))
                print(json.dumps(attempts[-1]),flush=True)
            result=dict(status='VERIFIED' if all(a['graceful_signal'] for a in attempts) else 'PARTIAL',attempts=attempts,port=8766,default8765='Unavailable on host; first real batch launch failed10048; no unrelated service stopped',environment='Fresh project venv installed from31 local hashed wheels with no-index/no-cache; standardCPython3.11.9, path containing spaces; same Windows host, not a cleanOS/event laptop',external_application_attempts=(scratch/'nonlocal_denials.log').read_text() if (scratch/'nonlocal_denials.log').exists() else '',scope='App non-loopback networking denied by test-only audit guard. Physical Wi-Fi-off not performed. Startup includes imports and public health/hash verification, not OS/browser cold boot.')
            record.write_text(json.dumps(result,indent=2)+'\n')
        finally:
            if process and process.poll() is None:process.terminate();process.wait(timeout=10)
            browser.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--app',type=Path,required=True);p.add_argument('--runs',type=Path,required=True);p.add_argument('--record',type=Path,required=True);p.add_argument('--scratch',type=Path,required=True);a=p.parse_args();main(a.app,a.runs,a.record,a.scratch)
