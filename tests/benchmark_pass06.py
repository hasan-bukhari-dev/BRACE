"""Reproducible local benchmark; actual public RACE and archived-score ACE.

No user input code is executed. Numerical routines are only timed, not modified.
Run with --work a new scratch folder and --record a JSON destination.
"""
import argparse,ctypes,hashlib,json,os,platform,shutil,sys,time,uuid
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))

def peak_memory():
    if os.name!='nt':return dict(available=False,reason='This benchmark implements Windows process peak working set only.')
    from ctypes import wintypes as w
    class Counters(ctypes.Structure):
        _fields_=[('cb',w.DWORD),('PageFaultCount',w.DWORD),('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),
            ('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t)]
    c=Counters();c.cb=ctypes.sizeof(c);kernel=ctypes.WinDLL('kernel32',use_last_error=True);psapi=ctypes.WinDLL('psapi',use_last_error=True)
    kernel.GetCurrentProcess.restype=w.HANDLE
    psapi.GetProcessMemoryInfo.argtypes=[w.HANDLE,ctypes.POINTER(Counters),w.DWORD]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(c),c.cb):return dict(available=False,reason=str(ctypes.WinError(ctypes.get_last_error())))
    return dict(available=True,peak_working_set_bytes=c.PeakWorkingSetSize,scope='Peak resident working set for this complete benchmark worker, including imports, both RACE repeats, exports and ACE rescoring; not phase-specific allocation.')

def main(work,record_path,example):
    work=work.resolve();work.mkdir(parents=True,exist_ok=False);os.environ['BRACE_RUNS_DIR']=str(work)
    from brace_core import signature,stage06_cli
    from brace_core.intake import parse_cohort
    from brace_app.embrace import finalize
    from brace_app.release09 import package_versions
    pair=BASE/'examples/public_er_pair';cfg=json.loads((pair/'race_config.json').read_text());runs=[]
    for _ in range(2):
        start=time.perf_counter();cpu=time.process_time();rid=uuid.uuid4().hex;root=work/rid
        source,target=[parse_cohort(*(pair/f'prepared/{r}_{field}.{ext}' for field,ext in [('expression','tsv'),('metadata','tsv'),('manifest','json')]),r) for r in ('source','target')]
        loading=time.perf_counter()-start;phase={};original={name:getattr(signature,name) for name in ('eligibility','discover','replicate')}
        def timed(name,fn):
            def call(*args,**kwargs):
                t=time.perf_counter();value=fn(*args,**kwargs);phase[name]=phase.get(name,0)+time.perf_counter()-t;return value
            return call
        for name,fn in original.items():setattr(signature,name,timed(name,fn))
        try:
            t=time.perf_counter();result=signature.run(source,target,cfg,root/'race');race_total=time.perf_counter()-t
        finally:
            for name,fn in original.items():setattr(signature,name,fn)
        config=dict(id=rid,kind='public_computed',name='Verified public ER association',mode='race',input_hashes=result['input_files'],
            data_label='New local computation from verified public GSE42568 → GSE20711 ER-association inputs; exploratory, not clinical or locked validation.',
            public_preparation=json.loads((pair/'prepared/summary.json').read_text()),public_data_document=(pair/'README.md').read_text(encoding='utf-8'))
        (root/'run.json').write_text(json.dumps(config));t=time.perf_counter();path=finalize(root);export=time.perf_counter()-t
        numerical={name:hashlib.sha256((root/'race'/name).read_bytes()).hexdigest() for name in signature.FILES}
        elapsed=time.perf_counter()-start;cpu_elapsed=time.process_time()-cpu;t=time.perf_counter();again=finalize(root);cached=time.perf_counter()-t
        assert path.read_bytes()==again.read_bytes()
        runs.append(dict(run_id=rid,samples={'source':len(source.sample_ids),'target':len(target.sample_ids)},features=10000,
            loading_and_intake_s=loading,eligibility_s=phase['eligibility'],source_screen_and_freeze_s=phase['discover'],target_testing_s=phase['replicate'],
            race_total_s=race_total,race_write_and_coordination_s=race_total-sum(phase.values()),evidence_export_s=export,cached_export_validation_s=cached,
            overall_s=elapsed,process_cpu_s=cpu_elapsed,aggregate=result['aggregate'],numerical_sha256=numerical,bundle_bytes=path.stat().st_size))
        if len(runs)==1:shutil.copyfile(path,example)
    assert runs[0]['numerical_sha256']==runs[1]['numerical_sha256'],'Scientific numerical reruns diverged'
    prior={name:hashlib.sha256((pair/'race_final'/name).read_bytes()).hexdigest() for name in signature.FILES}
    assert runs[0]['numerical_sha256']==prior,'Prior approved scientific artifacts changed'
    archive=BASE/'examples/cancershift_historical_cptac';t=time.perf_counter()
    ace=stage06_cli.evaluate_existing(archive/'predictions.tsv',archive/'manifest.json',work/'archived_score_rescore');ace_time=time.perf_counter()-t
    assert ace['n']==680 and ace['metrics']['n_correct']==668 and ace['frozen_threshold_result']['retained']==584 and ace['frozen_threshold_result']['correct']==583
    result=dict(environment=dict(os=platform.platform(),processor=platform.processor(),logical_cpus=os.cpu_count(),software=package_versions()),
        public_data_runs=runs,repeated_numerical_artifacts_identical=True,approved_prior_artifacts_identical=True,zip_times='Fixed 1980 entry timestamps; different run IDs are provenance differences, not numerical differences.',
        ace=dict(kind='Historical real prediction rescoring only; original CancerShift inference is not run.',seconds=ace_time,n=ace['n'],correct=ace['metrics']['n_correct']),
        public_pair_ace_model_transfer=dict(seconds=None,reason='This exploratory GC-RMA/RMA ER pair is not approved for source-trained model transfer; no forced public model benchmark.'),
        memory=peak_memory(),measurement_scope='Single developer machine; two actual local RACE runs. Times exclude interpreter/import startup, include data loading, checks, numerical outputs and audited export. No population benchmark or human task timing claim.')
    record_path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(overall_s=[r['overall_s'] for r in runs],race_s=[r['race_total_s'] for r in runs],export_s=[r['evidence_export_s'] for r in runs],memory=result['memory'],ace_rescore_s=ace_time,numerical_repeat='PASS'),indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--record',type=Path,required=True);p.add_argument('--example',type=Path,required=True);args=p.parse_args();main(args.work,args.record,args.example)
