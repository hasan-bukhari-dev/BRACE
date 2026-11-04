"""Independent published-output audit; does not generate or repair results."""
import argparse,csv,io,json,math,sys
from collections import Counter
from pathlib import Path
import numpy as np
from scipy import stats
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
from brace_core.intake import parse_cohort

def close(a,b):
    if a is None or b is None:assert a is b,(a,b)
    else:assert math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-12),(a,b)
def cells(folder,name):
    raw=list(csv.reader(io.StringIO((folder/name).read_text(encoding='utf-8'))))
    ledger=json.loads((folder/'CSV_TEXT_ENCODING.json').read_text())['changed_cells'].get(name,[])
    for change in ledger:raw[change['row']-1][change['column']-1]=change['original']
    return [dict(zip(raw[0],row)) for row in raw[1:]]
def scalar(value):return float(value) if value!='' else None
def evaluate(group,classes):
    truth=Counter(r['true_label'] for r in group);pred=Counter(r['predicted_label'] for r in group)
    tp=Counter(r['true_label'] for r in group if r['correct']);f1=[2*tp[c]/(truth[c]+pred[c]) for c in classes if truth[c]]
    return truth,pred,tp,sum(f1)/len(f1)

def main(runs,record):
    checked=[];ks_features=0;pca_points=0
    inputs=BASE/'examples/synthetic_valid'
    src,tgt=[parse_cohort(inputs/f'{r}_expression.csv',inputs/f'{r}_samples.csv',inputs/f'{r}_manifest.json',r) for r in ('source','target')]
    for configfile in sorted(runs.glob('*/run.json')):
        root=configfile.parent;published=root/'embrace'
        if not published.is_dir():continue
        val=published/'validation/validation_result.json';shift=published/'shift/shift_result.json'
        if val.is_file():
            a=json.loads(val.read_text())['analysis'];records=a['records'];classes=a['class_order'];truth,pred,tp,macro=evaluate(records,classes)
            per=cells(published,'validation/per_class.csv');assert len(per)==len(classes)
            for row in per:
                c=row['class'];assert (int(row['support']),int(row['predicted_count']),int(row['tp']))==(truth[c],pred[c],tp[c])
                close(scalar(row['precision']),tp[c]/pred[c] if pred[c] else None)
                close(scalar(row['recall']),tp[c]/truth[c] if truth[c] else None)
                close(scalar(row['f1']),2*tp[c]/(truth[c]+pred[c]) if truth[c] else None)
            close(a['metrics']['supported_class_macro_f1'],macro)
            curve=cells(published,'validation/threshold_curve.csv')
            for point in curve:
                t=float(point['threshold']);kept=[r for r in records if r['confidence'] is not None and r['confidence']>=t];right=sum(r['correct'] for r in kept)
                assert (int(point['retained']),int(point['correct']),int(point['errors']))==(len(kept),right,len(kept)-right)
                close(scalar(point['coverage']),len(kept)/len(records));close(scalar(point['selective_accuracy']),right/len(kept) if kept else None);close(scalar(point['selective_risk']),(len(kept)-right)/len(kept) if kept else None)
            bins=cells(published,'validation/confidence_bins.csv');weighted=0
            for b in bins:
                lo,hi=float(b['lower']),float(b['upper']);group=[r for r in records if r['confidence'] is not None and r['confidence']>=lo and (r['confidence']<hi or hi==1 and r['confidence']<=1)]
                assert int(b['count'])==len(group)
                mean=sum(r['confidence'] for r in group)/len(group) if group else None;accuracy=sum(r['correct'] for r in group)/len(group) if group else None
                close(scalar(b['mean_confidence']),mean);close(scalar(b['accuracy']),accuracy)
                if group:weighted+=len(group)/len(records)*abs(mean-accuracy)
            close(a['expected_calibration_error_10bin'],weighted if bins else None)
            studies=cells(published,'validation/study_summary.csv')
            assert len(studies)==len({r['study_id'] for r in records if r['study_id']})
            for row in studies:
                group=[r for r in records if r['study_id']==row['study_id']];supports,_,_,f1=evaluate(group,classes)
                assert int(row['n'])==len(group) and json.loads(row['class_support_json'])=={c:supports[c] for c in classes}
                close(row['accuracy'],sum(r['correct'] for r in group)/len(group));close(row['observed_class_macro_f1'],f1)
            checked.append(dict(run_id=json.loads(configfile.read_text())['id'],evaluation_rows=len(records),per_class_rows=len(per),threshold_points=len(curve),confidence_bins=len(bins),study_rows=len(studies)))
        if shift.is_file():
            doc=json.loads(shift.read_text());genes=cells(published,'shift/gene_shifts.csv');assert len(genes)==doc['feature_coverage']['shared']
            pvalues=[]
            for row,g in zip(genes,doc['gene_shifts']):
                assert row['feature_id']==g['feature_id'];i=src.feature_ids.index(g['feature_id']);j=tgt.feature_ids.index(g['feature_id']);s=src.values[:,i];t=tgt.values[:,j]
                ref=stats.ks_2samp(s,t,method='auto');pvalues.append(ref.pvalue)
                close(row['ks_d'],ref.statistic);close(row['ks_p_exploratory'],ref.pvalue)
                close(row['source_mean'],np.mean(s));close(row['target_mean'],np.mean(t));close(row['source_median'],np.median(s));close(row['target_median'],np.median(t))
                iqr=np.percentile(s,75)-np.percentile(s,25);close(row['source_iqr'],iqr)
                close(row['median_difference_target_minus_source'],np.median(t)-np.median(s));close(scalar(row['median_shift_per_source_iqr']),(np.median(t)-np.median(s))/iqr if iqr else None)
            q=stats.false_discovery_control(pvalues)
            for row,expected in zip(genes,q):close(row['ks_bh_q_exploratory'],expected)
            pts=cells(published,'shift/pca_samples.csv');assert {(r['cohort'],r['sample_id']) for r in pts}=={('source',s) for s in src.sample_ids}|{('target',s) for s in tgt.sample_ids}
            for row,saved in zip(pts,doc['pca']['samples']):
                assert row['sample_id']==saved['sample_id'];close(row['pc1'],saved['pc1']);close(row['pc2'],saved['pc2']);close(row['source_scaled_pc_distance'],saved['source_scaled_pc_distance'])
            pca_points+=len(pts);ks_features+=len(genes)
    assert checked and ks_features and pca_points
    value=dict(status='PASS',published_ace_runs=checked,independently_referenced_shift_features=ks_features,pca_csv_json_points_reconciled=pca_points,
        note='Independent Python counts/formulas for class support, confidence, calibration and study summaries; SciPy KS/BH and NumPy moment references on the actual known synthetic shift fixtures. PCA CSV coordinates/identities reconciled to saved calculations. No result modification or clinical claim.')
    record.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(status='PASS',ace_runs=len(checked),ks_features=ks_features,pca_points=pca_points)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--runs',type=Path,required=True);p.add_argument('--record',type=Path,required=True);a=p.parse_args();main(a.runs,a.record)
