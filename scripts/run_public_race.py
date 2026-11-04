"""Run pinned public ER example, repeat it, and compare with independent SciPy references."""
import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np
from scipy import stats

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from brace_core.intake import parse_cohort
from brace_core.signature import run, FILES, write_json

def main(out):
    pair=ROOT/'examples/public_er_pair';prepared=pair/'prepared'
    hashes=json.loads((prepared/'prepared_hashes.json').read_text())
    for name,entry in hashes.items():
        assert hashlib.sha256((prepared/name).read_bytes()).hexdigest()==entry['sha256']
    downloads=json.loads((pair/'evidence/downloads.json').read_text())
    for acc in ('GSE42568','GSE20711'):
        name=acc+'_series_matrix.txt.gz'
        assert hashlib.sha256((pair/'raw'/name).read_bytes()).hexdigest()==next(r['sha256'] for r in downloads if r['file']==name)
    cohorts=[parse_cohort(prepared/f'{r}_expression.tsv',prepared/f'{r}_metadata.tsv',prepared/f'{r}_manifest.json',r) for r in ('source','target')]
    config=json.loads((pair/'race_config.json').read_text())
    started=time.perf_counter();result=run(*cohorts,config,out);elapsed=time.perf_counter()-started
    again=out.parent/(out.name+'_repeat');run(*cohorts,config,again)
    for name in FILES:assert (out/name).read_bytes()==(again/name).read_bytes(),name
    # Separate vectorized SciPy implementation, with independent selection reconstruction.
    source,target=cohorts
    def reference(c,features):
        a=[i for i,s in enumerate(c.sample_ids) if c.metadata[s]['condition']=='ER_positive']
        b=[i for i,s in enumerate(c.sample_ids) if c.metadata[s]['condition']=='ER_negative']
        ix=[c.feature_ids.index(f) for f in features]
        x=c.values[np.ix_(a,ix)];y=c.values[np.ix_(b,ix)]
        test=stats.ttest_ind(x,y,axis=0,equal_var=False)
        delta=x.mean(axis=0)-y.mean(axis=0)
        n,m=len(a),len(b);df=n+m-2
        # scipy.stats.t has no Hedges helper; gamma correction via math.lgamma, independently scalar.
        import math
        j=math.exp(math.lgamma(df/2)-.5*math.log(df/2)-math.lgamma((df-1)/2))
        g=j*delta/np.sqrt(((n-1)*x.var(axis=0,ddof=1)+(m-1)*y.var(axis=0,ddof=1))/df)
        valid=(np.ptp(x,axis=0)>0)&(np.ptp(y,axis=0)>0)
        p=np.where(valid,test.pvalue,1.0)
        return test,delta,g,stats.false_discovery_control(p),valid
    rows=result['source_screen'];ref,effect,g,q,valid=reference(source,[r['feature_id'] for r in rows])
    discrepancies={}
    for key,expected in [('p',ref.pvalue),('t',ref.statistic),('effect',effect),('hedges_g',g),('q',q)]:
        actual=np.array([r[key] for i,r in enumerate(rows) if valid[i]],dtype=float);expected=expected[valid]
        np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-12)
        discrepancies['source_'+key]=float(np.max(np.abs(actual-expected)))
    assert all((r['p'] is not None)==bool(valid[i]) for i,r in enumerate(rows))
    independently_selected=sorted([i for i in range(len(rows)) if valid[i] and q[i]<=.05],key=lambda i:(-abs(g[i]),rows[i]['feature_id']))[:20]
    selected=[rows[i]['feature_id'] for i in independently_selected]
    assert selected==[r['feature_id'] for r in result['genes']]
    ref,effect,g,q,valid=reference(target,selected)
    assert valid.all()
    for key,expected in [('p',ref.pvalue),('t',ref.statistic),('effect',effect),('hedges_g',g),('q',q)]:
        actual=np.array([r[key] for r in result['genes']]);np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-12)
        discrepancies['target_'+key]=float(np.max(np.abs(actual-expected)))
    # Annotation joins use the exact source-selected probe, not all symbol aliases for an Entrez gene.
    probes=dict(csv.reader((prepared/'selected_features.tsv').read_text().splitlines()[1:],delimiter='\t'))
    mapping={r['probe_id']:r for r in csv.DictReader((pair/'evidence/GPL570_mapping.tsv').open(encoding='utf-8'),delimiter='\t')}
    annotation=[]
    for gene in selected:
        row=mapping[probes[gene]];assert row['entrez_gene_id']==gene
        symbol=row['gene_symbol'];annotation.append(dict(feature_id=gene,probe_id=probes[gene],gene_symbol=symbol if symbol and '///' not in symbol else None,annotation_source='Pinned GPL570 platform snapshot; not independently validated current nomenclature'))
    write_json(out/'gene_annotations.json',annotation)
    write_json(out/'verification.json',dict(evidence_origin='new_public_cohort_computation',runtime_seconds_engine_and_exports=elapsed,
        repeated_scientific_files_byte_identical=True,reference_tolerance=dict(rtol=1e-10,atol=1e-12),maximum_absolute_discrepancies=discrepancies,
        aggregate=result['aggregate'],source_sample_counts=result['counts']['source'],target_sample_counts=result['counts']['target'],
        preparation_hash_manifest_sha256=hashlib.sha256((prepared/'prepared_hashes.json').read_bytes()).hexdigest(),
        original_download_records=downloads,reference='Vectorized scipy.stats.ttest_ind(equal_var=False), scipy.stats.false_discovery_control; independent source selection reconstruction'))
    print(json.dumps(dict(runtime_seconds=elapsed,aggregate=result['aggregate'],selected=annotation,reference_max_discrepancies=discrepancies),indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);main(ap.parse_args().out)
