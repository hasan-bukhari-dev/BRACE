"""Stage 04 command line entrypoint, used by the optional desktop picker."""
import argparse,json,sys
from pathlib import Path
from .intake import parse_cohort,InputProblem
from .compatibility import evaluate_compatibility
from .reporting import generate_report

def execute(mode,source_expr,source_meta,source_manifest,target_expr,target_meta,target_manifest,out,classes=('normal','tumor'),scientific_role=None,export_aligned=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    try:
        file_paths=[Path(p) for p in (source_expr,source_meta,source_manifest,target_expr,target_meta,target_manifest)]
        if all(p.is_file() for p in file_paths) and sum(p.stat().st_size for p in file_paths)>300*1024*1024:
            raise InputProblem('RUN_TOO_LARGE','Combined input files exceed 300 MiB','Reduce the size of the study inputs','run')
        s=parse_cohort(source_expr,source_meta,source_manifest,'source')
        t=parse_cohort(target_expr,target_meta,target_manifest,'target')
        role=scientific_role or ('unlabeled_shift_only' if mode=='diagnose_shift' else 'external_exploratory')
        result=evaluate_compatibility(s,t,mode,tuple(classes),role)
        report=generate_report(result,out,export_aligned=export_aligned)
        return report, (0 if result.eligible else 2)
    except InputProblem as e:
        report={'stage':'04','verdict':'blocked','eligible':False,'issues':[e.to_dict()],
                'note':'Preflight blocked before matrices could be compared. No analysis was performed.'}
        (out/'compatibility_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        # No stale artifacts may survive an invalid run in reused output dirs.
        for name in ('compatibility_report.html','aligned_feature_ids.csv','source_aligned_expression.csv','target_aligned_expression.csv'):
            (out/name).unlink(missing_ok=True)
        return report,2

def main(argv=None):
    parser=argparse.ArgumentParser(description='BRACE Stage 04: validate cohorts, generate compatibility report')
    parser.add_argument('--mode',required=True,choices=['train_validate','diagnose_shift'])
    parser.add_argument('--source-expression',required=True,type=Path)
    parser.add_argument('--source-metadata',required=True,type=Path)
    parser.add_argument('--source-manifest',required=True,type=Path)
    parser.add_argument('--target-expression',required=True,type=Path)
    parser.add_argument('--target-metadata',required=True,type=Path)
    parser.add_argument('--target-manifest',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--classes',nargs=2,default=['normal','tumor'])
    parser.add_argument('--scientific-role',choices=['external_exploratory','external_locked','unlabeled_shift_only'])
    parser.add_argument('--export-aligned',action='store_true',help='Explicitly export gene-aligned original numeric values without normalization')
    p=parser.parse_args(argv)
    try:
        report,exitcode=execute(p.mode,p.source_expression,p.source_metadata,p.source_manifest,p.target_expression,p.target_metadata,p.target_manifest,p.out,p.classes,p.scientific_role,p.export_aligned)
    except Exception as exc:
        # CLI reports operational failures explicitly, does not turn them into scientific blocks.
        print(f'BRACE operational failure ({type(exc).__name__}): {exc}',file=sys.stderr)
        return 1
    print(json.dumps({'verdict':report['verdict'],'eligible':report['eligible'],'issues':report['issues'],'report_file':str(p.out/'compatibility_report.json')},indent=2))
    return exitcode

if __name__=='__main__':raise SystemExit(main())
