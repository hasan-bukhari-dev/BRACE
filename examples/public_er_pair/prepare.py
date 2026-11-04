"""Prepare exploratory ER association inputs. No association tests or RACE fitting.

Python standard library only; input hashes are pinned in evidence/downloads.json.
"""
import argparse
import collections
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics
import urllib.request

HERE = Path(__file__).resolve().parent
ACCESSIONS = ('GSE42568', 'GSE20711')

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def extract_mapping(soft, out):
    """Reproduce the bundled mapping from the pinned official source SOFT."""
    records=json.loads((HERE/'evidence/downloads.json').read_text())
    assert sha(soft)==next(r['sha256'] for r in records if r['file']=='GSE42568_family.soft.gz')
    with gzip.open(soft,'rt',encoding='utf-8') as stream:
        for line in stream:
            if line.startswith('!platform_table_begin'): break
        head=next(stream).rstrip('\n').split('\t')
        gi=head.index('ENTREZ_GENE_ID'); si=head.index('Gene Symbol'); rows=[]
        for line in stream:
            if line.startswith('!platform_table_end'): break
            r=line.rstrip('\n').split('\t'); rows.append([r[0],r[gi],r[si]])
    assert len(rows)==54675
    table(out,['probe_id','entrez_gene_id','gene_symbol'],rows)
    assert sha(out)==(HERE/'evidence/GPL570_mapping.sha256').read_text().strip()

def write_json(path, obj):
    # Preserve the original prepared JSON bytes on every OS, including POSIX.
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True)+'\n', encoding='utf-8', newline='\r\n')

def table(path, head, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        w.writerow(head); w.writerows(rows)

def matrix(path):
    meta = collections.defaultdict(list); rows = {}
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            if line.startswith('!series_matrix_table_begin'): break
            r = next(csv.reader([line], delimiter='\t'))
            if r: meta[r[0]].append(r[1:])
        head = next(csv.reader([next(f)], delimiter='\t'))
        assert head[0] == 'ID_REF'
        for line in f:
            if line.startswith('!series_matrix_table_end'): break
            r = next(csv.reader([line], delimiter='\t'))
            assert r[0] not in rows and len(r) == len(head)
            assert all(math.isfinite(float(v)) for v in r[1:])
            rows[r[0]] = r[1:]
    assert head[1:] == meta['!Sample_geo_accession'][0]
    assert len(set(head[1:])) == len(head)-1
    assert set(meta['!Sample_platform_id'][0]) == {'GPL570'}
    return meta, head[1:], rows

def sample_records(acc, meta, ids):
    out=[]
    for i, sid in enumerate(ids):
        chars=[r[i] for r in meta['!Sample_characteristics_ch1']]
        fields=collections.defaultdict(list)
        for c in chars:
            if ': ' in c:
                k,v=c.split(': ',1); fields[k.lower()].append(v)
        title=meta['!Sample_title'][0][i]
        origin=meta['!Sample_source_name_ch1'][0][i]
        key='er_status' if acc=='GSE42568' else 'er status'
        er=fields[key]
        assert len(er)==1
        tumor=origin == ('Breast tissue, cancer' if acc=='GSE42568' else 'Breast tumor')
        reason='included' if tumor and er[0] in ('0','1') else ('non_tumor' if not tumor else 'ER_missing')
        if acc=='GSE20711': assert fields['quality control']==['1']
        # Source title specimen codes are NOT authenticated donor identifiers.
        pid=(acc+':'+title.split('patient ')[1].split(' ')[0]) if acc=='GSE20711' and tumor else ''
        out.append(dict(sample_id=sid,condition={'0':'ER_negative','1':'ER_positive'}.get(er[0],''),
            patient_id=pid,study_id=acc,title=title,source_name=origin,er_original=er[0],
            inclusion=reason,characteristics=json.dumps(chars,ensure_ascii=True)))
    return out

def prepare(raw, out):
    out.mkdir(parents=True,exist_ok=True)
    records=json.loads((HERE/'evidence/downloads.json').read_text())
    for acc in ACCESSIONS:
        name=acc+'_series_matrix.txt.gz'
        assert sha(raw/name)==next(r['sha256'] for r in records if r['file']==name), 'Input hash mismatch'
    mapping_path=HERE/'evidence/GPL570_mapping.tsv'
    assert sha(mapping_path)==(HERE/'evidence/GPL570_mapping.sha256').read_text().strip()
    mapping=list(csv.DictReader(mapping_path.open(encoding='utf-8'),delimiter='\t'))
    source_meta, source_ids, source_rows=matrix(raw/'GSE42568_series_matrix.txt.gz')
    src=sample_records('GSE42568',source_meta,source_ids)
    idx=[source_ids.index(r['sample_id']) for r in src if r['inclusion']=='included']
    # Source-only population variance, no labels used for ranking; one probe per Entrez ID.
    candidates={}; audit=[]
    for m in mapping:
        probe=m['probe_id']; gene=m['entrez_gene_id'].strip()
        good=gene.isdigit() and not probe.startswith('AFFX') and probe in source_rows
        variance=statistics.pvariance(float(source_rows[probe][j]) for j in idx) if good else None
        audit.append([probe,gene,variance])
        if good:
            candidate=(-variance,probe)
            if gene not in candidates or candidate<candidates[gene]: candidates[gene]=candidate
    chosen=sorted(candidates,key=lambda g:(candidates[g][0],g))[:10000]
    selected={g:candidates[g][1] for g in chosen}
    assert len(selected)==10000
    table(out/'feature_selection.tsv',['probe_id','entrez_gene_id','source_population_variance','decision'],
        ([p,g,'' if v is None else repr(v),'selected' if selected.get(g)==p else
          ('unmapped_ambiguous_or_control' if v is None else 'other_probe_or_below_source_rank')]
         for p,g,v in audit))
    table(out/'selected_features.tsv',['feature_id','probe_id'],sorted(selected.items()))
    summaries={}
    for acc,role in zip(ACCESSIONS,('source','target')):
        meta,ids,rows=(source_meta,source_ids,source_rows) if role=='source' else matrix(raw/(acc+'_series_matrix.txt.gz'))
        samples=sample_records(acc,meta,ids)
        included=sorted((r for r in samples if r['inclusion']=='included'),key=lambda r:r['sample_id'])
        assert len({r['patient_id'] for r in included if r['patient_id']}) in (0,len(included))
        table(out/(role+'_all_samples.tsv'),list(samples[0]),([r[k] for k in samples[0]] for r in samples))
        table(out/(role+'_metadata.tsv'),list(samples[0]),([r[k] for k in samples[0]] for r in included))
        indices=[ids.index(r['sample_id']) for r in included]
        table(out/(role+'_expression.tsv'),['feature_id']+[r['sample_id'] for r in included],
            ([g]+[rows[selected[g]][i] for i in indices] for g in sorted(selected)))
        desc='GEO deposited log2 GC-RMA signals; no additional normalization' if role=='source' else 'GEO deposited RMA Bioconductor default parameters and log2 transformation; no additional normalization'
        write_json(out/(role+'_manifest.json'),dict(schema_version='1.0.0',cohort_id=acc+'_ER',role=role,
            organism='Homo sapiens',feature_namespace='entrez_gene',measurement_type='microarray_log2_normalized',
            processing_description=desc,labels='binary',independence_declaration='unknown',study_id=acc,
            accession=acc,platform='GPL570',sample_origin_notes='Tumors only; ER clinical annotations; exploratory independent-study comparison. See README for independence and assay limitations.'))
        summaries[acc]=dict(downloaded_samples=len(ids),included=len(included),
            labels=dict(collections.Counter(r['condition'] for r in included)),
            exclusions=dict(collections.Counter(r['inclusion'] for r in samples if r['inclusion']!='included')),
            input_features=len(rows),prepared_features=len(selected))
        # Preserve complete series/sample annotation lines, including repeated fields.
        write_json(out/(role+'_geo_metadata.json'),dict(meta))
    assert not set(source_ids)&set(ids)
    write_json(out/'summary.json',summaries)
    for p in out.glob('*_expression.tsv'): assert p.stat().st_size<=25*1024*1024
    write_json(out/'prepared_hashes.json',{p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file() and p.name!='prepared_hashes.json'})
    return summaries

def download(raw):
    raw.mkdir(parents=True,exist_ok=True)
    for r in json.loads((HERE/'evidence/downloads.json').read_text()):
        if r['file'] not in [a+'_series_matrix.txt.gz' for a in ACCESSIONS]: continue
        dest=raw/r['file']
        if not dest.exists():
            with urllib.request.urlopen(r['url'],timeout=180) as response: dest.write_bytes(response.read())
        assert sha(dest)==r['sha256'], 'Downloaded input differs from pinned version'

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--raw',type=Path,default=HERE/'raw'); ap.add_argument('--out',type=Path,default=HERE/'prepared'); ap.add_argument('--download',action='store_true')
    args=ap.parse_args()
    if args.download: download(args.raw)
    print(json.dumps(prepare(args.raw,args.out),indent=2))
