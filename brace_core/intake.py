"""Strict streaming CSV/TSV input parsing with no arbitrary normalization or inference."""
from __future__ import annotations
from pathlib import Path
from collections import Counter
import csv, hashlib, json, math, re
import numpy as np
from .contracts import Cohort, Issue

MAX_FILE_BYTES=100*1024*1024
MAX_FEATURES=25_000
MAX_SAMPLES=500
MAX_METADATA_ROWS=500
MAX_JSON_BYTES=1024*1024
MANIFEST_FIELDS={
    'schema_version','cohort_id','role','organism','feature_namespace','measurement_type',
    'processing_description','labels','independence_declaration','study_id','accession','platform','sample_origin_notes'
}
REQUIRED_FIELDS={'schema_version','cohort_id','role','organism','feature_namespace','measurement_type','processing_description','labels','independence_declaration'}
ALLOWED={
 'feature_namespace':{'gene_symbol','ensembl_gene','entrez_gene','probe_id'},
 'measurement_type':{'microarray_log2_normalized','rnaseq_log2_normalized','rnaseq_vst','raw_counts','unknown'},
 'labels':{'binary','unlabeled'},
 'independence_declaration':{'independent_documented','unknown','not_independent'},
 'role':{'source','target'},
}

class InputProblem(ValueError):
    def __init__(self, code: str, message: str, next_action: str, field: str=''):
        super().__init__(message)
        self.issue=Issue(code,'block',message,next_action,field)
    def to_dict(self):
        return self.issue.to_dict()

def _file_info(path:Path, max_size=MAX_FILE_BYTES) -> dict[str,str|int]:
    if not path.is_file():
        raise InputProblem('FILE_NOT_FOUND',f'File not found: {path.name}','Select a readable local file','input')
    size=path.stat().st_size
    if size==0 or size>max_size:
        raise InputProblem('FILE_SIZE_INVALID',f'{path.name}: file is empty or exceeds the {max_size//(1024*1024)} MiB limit','Select a smaller valid file','input')
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            digest.update(chunk)
    return {'name':path.name,'bytes':size,'sha256':digest.hexdigest()}

def _read_manifest(path:Path, expected_role:str):
    info=_file_info(path,MAX_JSON_BYTES)
    try:
        # json.loads allows duplicate keys by default; explicitly reject them.
        def unique_pairs(pairs):
            d={}
            for k,v in pairs:
                if k in d: raise ValueError(f'duplicate JSON property {k!r}')
                d[k]=v
            return d
        manifest=json.loads(path.read_text(encoding='utf-8-sig'),object_pairs_hook=unique_pairs)
    except (UnicodeError,ValueError) as e:
        raise InputProblem('MANIFEST_INVALID',f'Invalid JSON manifest: {e}','Provide UTF-8 JSON conforming to Stage 02 schema','manifest') from e
    if not isinstance(manifest,dict):
        raise InputProblem('MANIFEST_INVALID','Manifest must be a JSON object','Use the Stage 02 cohort_manifest schema','manifest')
    missing=REQUIRED_FIELDS-set(manifest)
    unknown=set(manifest)-MANIFEST_FIELDS
    if missing or unknown:
        raise InputProblem('MANIFEST_INVALID',f'Manifest fields: missing={sorted(missing)}, unsupported={sorted(unknown)}','Correct required and unsupported fields','manifest')
    if manifest.get('schema_version')!='1.0.0' or manifest.get('organism')!='Homo sapiens':
        raise InputProblem('MANIFEST_INVALID','Stage 04 requires schema_version 1.0.0 and Homo sapiens','Use the Stage 02 supported schema','manifest')
    for k,values in ALLOWED.items():
        if not isinstance(manifest[k],str) or manifest[k] not in values:
            raise InputProblem('MANIFEST_INVALID',f'{k} has unsupported value {manifest[k]!r}',f'Select one of {sorted(values)}','manifest')
    if manifest['role']!=expected_role:
        raise InputProblem('ROLE_MISMATCH',f'Expected {expected_role} manifest, found {manifest["role"]}','Select the correct source or target manifest','manifest.role')
    for field in ('cohort_id','processing_description'):
        if not isinstance(manifest[field],str) or not manifest[field].strip():
            raise InputProblem('MANIFEST_INVALID',f'{field} must be nonempty text','Complete the manifest','manifest')
    for field in ('study_id','accession','platform'):
        if field in manifest and (not isinstance(manifest[field],str) or not manifest[field].strip()):
            raise InputProblem('MANIFEST_INVALID',f'{field} must be nonempty text when present','Complete or omit the optional field','manifest')
    return manifest,info

def _reader(path:Path):
    if path.suffix.lower() not in ('.csv','.tsv'):
        raise InputProblem('FILE_FORMAT_INVALID',f'{path.name} must be CSV or TSV','Select a .csv or .tsv file','file')
    stream=None
    try:
        stream=path.open('r',encoding='utf-8-sig',newline='')
        head=stream.read(16384)
        if '\x00' in head:
            stream.close(); raise InputProblem('FILE_FORMAT_INVALID','NUL bytes are not allowed','Export as UTF-8 CSV/TSV','file')
        stream.seek(0)
        dialect='\t' if path.suffix.lower()=='.tsv' else ','
        return stream,csv.reader(stream,delimiter=dialect,strict=True)
    except UnicodeError as e:
        if stream is not None:stream.close()
        raise InputProblem('FILE_ENCODING_INVALID',f'File is not UTF-8: {path.name}','Export as UTF-8','file') from e

def _id(raw:str,field:str):
    if not isinstance(raw,str) or not raw.strip():
        raise InputProblem('IDENTIFIER_MISSING',f'Empty {field}','Supply a unique, nonempty identifier',field)
    val=raw.strip()
    if any(ord(c)<32 for c in val):
        raise InputProblem('IDENTIFIER_INVALID',f'{field} contains control characters','Remove control characters',field)
    return val

def _duplicate(items:list[str],code:str,what:str):
    c=Counter(items); duplicates=[k for k,v in c.items() if v>1]
    if duplicates:
        raise InputProblem(code,f'Duplicate {what}: {duplicates[:5]}','Give each record a unique identifier; no automatic merging',what)

def _parse_metadata(path:Path):
    info=_file_info(path)
    stream,reader=_reader(path)
    try:
        head=next(reader,None)
        if not head: raise InputProblem('METADATA_INVALID','Metadata header missing','Provide sample_id and optional condition/patient_id/study_id','metadata')
        cols=[_id(x,'metadata header') for x in head]
        _duplicate(cols,'DUPLICATE_COLUMN','metadata column')
        if 'sample_id' not in cols:
            raise InputProblem('METADATA_INVALID','Metadata must have sample_id column','Rename identifier column to sample_id','metadata')
        rows={}
        saw_trimmed=cols!=head
        for n,row in enumerate(reader,2):
            if len(row)!=len(cols):
                raise InputProblem('METADATA_INVALID',f'Metadata row {n} has {len(row)} cells, expected {len(cols)}','Fix column delimiters and rows','metadata')
            r={c:val.strip() for c,val in zip(cols,row)}
            sid=_id(r['sample_id'],'sample_id')
            if sid in rows: raise InputProblem('DUPLICATE_SAMPLE_ID',f'Duplicate sample_id {sid!r} in metadata','Resolve duplicate sample IDs','metadata.sample_id')
            if any(v!=raw for v,raw in zip(r.values(),row)):
                saw_trimmed=True
            rows[sid]=r
            if len(rows)>MAX_METADATA_ROWS:
                raise InputProblem('FILE_TOO_LARGE',f'Metadata exceeds {MAX_METADATA_ROWS} records','Reduce cohort size','metadata')
        if not rows: raise InputProblem('METADATA_INVALID','Metadata has no samples','Provide sample records','metadata')
    except (csv.Error,UnicodeError) as e:
        raise InputProblem('METADATA_INVALID',f'Invalid metadata file: {e}','Repair UTF-8 CSV/TSV format','metadata') from e
    finally:
        stream.close()
    return rows,info,saw_trimmed

def _parse_matrix(path:Path):
    info=_file_info(path)
    stream,reader=_reader(path)
    try:
        head=next(reader,None)
        if not head or len(head)<3 or head[0].strip()!='feature_id':
            raise InputProblem('MATRIX_ORIENTATION_INVALID','Expected feature_id first column and at least two sample columns','Use features as rows and samples as columns','expression')
        original_ids=head[1:]
        sample_ids=[_id(s,'sample_id') for s in original_ids]
        if len(sample_ids)>MAX_SAMPLES:
            raise InputProblem('FILE_TOO_LARGE',f'Expression matrix exceeds {MAX_SAMPLES} samples','Reduce samples per cohort','expression')
        _duplicate(sample_ids,'DUPLICATE_SAMPLE_ID','expression sample_id')
        feature_ids=[]; values=[]; seen=set(); trimmed=any(a!=b for a,b in zip(sample_ids,original_ids))
        for n,row in enumerate(reader,2):
            if len(row)!=len(head):
                raise InputProblem('MATRIX_INVALID',f'Expression row {n} has {len(row)} cells, expected {len(head)}','Fix matrix row width','expression')
            fid=_id(row[0],'feature_id')
            if fid in seen:
                raise InputProblem('DUPLICATE_FEATURE_ID',f'Duplicate feature_id {fid!r}','Provide distinct gene identifiers; no silent aggregation','expression.feature_id')
            seen.add(fid);feature_ids.append(fid)
            trimmed |= (fid!=row[0])
            try:
                nums=[float(x) for x in row[1:]]
            except (ValueError,TypeError) as e:
                raise InputProblem('INVALID_NUMERIC_VALUE',f'Nonnumeric entry in row {n}, feature {fid!r}','Provide finite numeric expression values only','expression') from e
            if not all(math.isfinite(x) for x in nums):
                raise InputProblem('INVALID_NUMERIC_VALUE',f'Missing/NaN/Inf value in feature {fid!r} at row {n}','Replace invalid values using documented preprocessing outside BRACE','expression')
            values.append(nums)
            if len(feature_ids)>MAX_FEATURES:
                raise InputProblem('FILE_TOO_LARGE',f'Expression matrix exceeds {MAX_FEATURES} features','Reduce features per cohort with documented preprocessing','expression')
        if not feature_ids: raise InputProblem('MATRIX_INVALID','Expression matrix has no features','Provide expression rows','expression')
        # Deterministic order independent of upload row and column order.
        fs=sorted(range(len(feature_ids)),key=feature_ids.__getitem__)
        ss=sorted(range(len(sample_ids)),key=sample_ids.__getitem__)
        X=np.asarray(values,dtype=np.float64)[np.ix_(fs,ss)].T.copy()
        ids=[feature_ids[i] for i in fs]; samples=[sample_ids[i] for i in ss]
    except (UnicodeError,csv.Error) as e:
        raise InputProblem('MATRIX_INVALID',f'Could not parse expression matrix: {e}','Fix UTF-8 CSV/TSV data formatting','expression') from e
    finally:
        stream.close()
    return samples,ids,X,info,trimmed

def parse_cohort(expression_path:str|Path, metadata_path:str|Path, manifest_path:str|Path, expected_role:str) -> Cohort:
    """Load explicit features-by-samples CSV/TSV and metadata, canonicalize in memory."""
    if expected_role not in ('source','target'):raise ValueError('expected_role must be source/target')
    expr=Path(expression_path);meta=Path(metadata_path);mfile=Path(manifest_path)
    manifest,manifest_info=_read_manifest(mfile,expected_role)
    sample_ids,feature_ids,X,expr_info,trim_matrix=_parse_matrix(expr)
    metadata,meta_info,trim_metadata=_parse_metadata(meta)
    if set(sample_ids)!=set(metadata):
        missing=sorted(set(sample_ids)-set(metadata)); extra=sorted(set(metadata)-set(sample_ids))
        raise InputProblem('SAMPLE_SET_MISMATCH',f'Expression and metadata samples differ. Missing metadata: {missing[:5]}, extra metadata: {extra[:5]}','Make sample_id sets match exactly','metadata.sample_id')
    warnings=[]
    if trim_matrix or trim_metadata:
        warnings.append(Issue('WHITESPACE_NORMALIZED','warning','Surrounding identifier/metadata whitespace was trimmed; raw bytes and hashes retained','Review canonical IDs and original files','identifiers'))
    # Numeric flags never alter expression values
    if np.quantile(X,.95)>60:
        warnings.append(Issue('SCALE_SUSPICIOUS','warning','95th percentile expression exceeds 60, unusual for stated log2 normalized values','Verify original measurement units and processing','expression'))
    if np.any(np.ptp(X,axis=0)==0):
        count=int(np.count_nonzero(np.ptp(X,axis=0)==0))
        warnings.append(Issue('ZERO_VARIANCE_FEATURE','info',f'{count} feature(s) have zero variance across samples; future statistics may be undefined','Retain values; Stage 05/07 handle constant features explicitly','expression'))
    return Cohort(manifest['cohort_id'],expected_role,tuple(sample_ids),tuple(feature_ids),X,metadata,manifest,
        {'expression':expr_info,'metadata':meta_info,'manifest':manifest_info},tuple(warnings))
