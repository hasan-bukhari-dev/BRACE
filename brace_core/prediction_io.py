"""Safe, inspectable ingestion of supplied prediction tables. Never executes model files."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv, json, math
import numpy as np
from .intake import InputProblem, _file_info, _reader
from .contracts import Issue

MANIFEST_REQUIRED = {'schema_version','dataset_id','model_id','classes','probability_columns',
    'prediction_origin','evaluation_role','independence_declaration','label_source_description'}
MANIFEST_ALLOWED = MANIFEST_REQUIRED | {'primary_confidence_threshold'}
ORIGINS = {'external_model','source_oof','historical_reference'}
ROLES = {'external_locked','external_exploratory','source_cv','historical_reference'}
INDEPENDENCE = {'independent_documented','unknown','not_independent'}

@dataclass(frozen=True)
class Predictions:
    sample_ids: tuple[str,...]
    true_labels: tuple[str,...]
    predicted_labels: tuple[str,...]
    classes: tuple[str,...]
    probabilities: np.ndarray | None
    metadata: tuple[dict[str,str],...]
    manifest: dict
    files: dict
    issues: tuple[Issue,...]
    def __post_init__(self):
        if self.probabilities is not None: self.probabilities.setflags(write=False)

def _object_unique(items):
    o={}
    for k,v in items:
        if k in o: raise ValueError('Duplicate JSON key '+k)
        o[k]=v
    return o

def load_predictions(data_path: str|Path, manifest_path: str|Path) -> Predictions:
    data_path=Path(data_path);manifest_path=Path(manifest_path)
    data_info=_file_info(data_path);manifest_info=_file_info(manifest_path,1024*1024)
    try:
        manifest=json.loads(manifest_path.read_text('utf-8-sig'),object_pairs_hook=_object_unique)
    except (UnicodeError,ValueError) as ex:
        raise InputProblem('MANIFEST_INVALID',f'Invalid prediction manifest: {ex}','Provide UTF-8 JSON with unique keys','manifest') from ex
    if not isinstance(manifest,dict) or not MANIFEST_REQUIRED<=manifest.keys() or set(manifest)-MANIFEST_ALLOWED:
        raise InputProblem('MANIFEST_INVALID','Prediction manifest has missing/unsupported fields','Use schemas/prediction_manifest.schema.json','manifest')
    if manifest['schema_version']!='1.0.0' or not all(isinstance(manifest[k],str) and manifest[k].strip() for k in ('dataset_id','model_id','label_source_description')):
        raise InputProblem('MANIFEST_INVALID','Invalid manifest version/identifiers','Use version 1.0.0 and nonblank dataset_id/model_id/label_source_description','manifest')
    if manifest['prediction_origin'] not in ORIGINS or manifest['evaluation_role'] not in ROLES or manifest['independence_declaration'] not in INDEPENDENCE:
        raise InputProblem('MANIFEST_INVALID','Unknown prediction origin, study role or independence','Choose documented manifest enum values','manifest')
    classes=manifest['classes']
    if not isinstance(classes,list) or len(classes)<2 or any(not isinstance(c,str) or not c or c!=c.strip() for c in classes) or len(set(classes))!=len(classes):
        raise InputProblem('LABEL_MAPPING_INCONSISTENT','Class universe must contain at least two unique, nonblank labels','Declare exact unique model classes','manifest.classes')
    columns=manifest['probability_columns']
    if not isinstance(columns,dict) or (columns and (set(columns)!=set(classes) or any(not isinstance(v,str) or not v for v in columns.values()) or len(set(columns.values()))!=len(classes))):
        raise InputProblem('PROBABILITY_VECTOR_INVALID','Probability mapping must cover every declared class with distinct columns, or be empty','Provide complete class-to-column mapping or {}','manifest.probability_columns')
    threshold=manifest.get('primary_confidence_threshold',0.95)
    if isinstance(threshold,bool) or not isinstance(threshold,(int,float)) or not math.isfinite(threshold) or not 0<=threshold<=1:
        raise InputProblem('MANIFEST_INVALID','Invalid predeclared confidence threshold','Declare a finite threshold between 0 and 1','manifest.primary_confidence_threshold')
    stream,reader=_reader(data_path)
    try:
        header=next(reader,None)
        if not header or len(header)!=len(set(header)) or any(not c or c!=c.strip() for c in header):
            raise InputProblem('PREDICTION_FILE_INVALID','Blank or duplicated prediction column','Correct CSV/TSV header','predictions')
        needed={'sample_id','true_label','predicted_label'}|set(columns.values())
        if not needed<=set(header):
            raise InputProblem('PREDICTION_FILE_INVALID',f'Missing prediction columns: {sorted(needed-set(header))}','Add the required columns exactly','predictions')
        rows=[];ids=set();p={};warnings=[]
        for i,row in enumerate(reader,2):
            if len(row)!=len(header):
                raise InputProblem('PREDICTION_FILE_INVALID',f'Row {i} has incorrect column count','Correct CSV/TSV quoting and width','predictions')
            r=dict(zip(header,row));sid=r['sample_id'].strip()
            if not sid:
                raise InputProblem('IDENTIFIER_MISSING',f'Empty sample_id in row {i}','Provide nonempty sample identifiers','predictions.sample_id')
            if sid in ids:
                raise InputProblem('DUPLICATE_SAMPLE_ID',f'Duplicate prediction sample_id {sid}','One prediction per sample','predictions.sample_id')
            ids.add(sid)
            if not r['true_label'] or not r['predicted_label'] or r['true_label'].strip() not in classes or r['predicted_label'].strip() not in classes:
                raise InputProblem('LABEL_MAPPING_INCONSISTENT',f'Unknown or missing class label in row {i}','Use exact labels from manifest','predictions.true_label')
            r={k:v.strip() for k,v in r.items()}
            if columns:
                try: vec=[float(r[columns[c]]) for c in classes]
                except ValueError as ex:
                    raise InputProblem('PROBABILITY_VECTOR_INVALID',f'Nonnumeric probability in row {i}','Provide finite numeric values','predictions') from ex
                if any(not math.isfinite(v) or v<0 or v>1 for v in vec) or abs(sum(vec)-1)>1e-4:
                    raise InputProblem('PROBABILITY_VECTOR_INVALID',f'Invalid probability vector in row {i}','Use [0,1] finite probabilities summing to 1 within 1e-4','predictions')
                maxv=max(vec);best=[j for j,v in enumerate(vec) if v==maxv]
                if len(best)==1 and classes[best[0]]!=r['predicted_label']:
                    raise InputProblem('PREDICTION_ARGMAX_MISMATCH',f'Predicted label disagrees with unique probability maximum in row {i}','Correct the prediction mapping or vector','predictions.predicted_label')
                if len(best)>1:
                    warnings.append(Issue('PROBABILITY_TIE','warning',f'Equal maximum probabilities for sample {sid}; predicted_label accepted as supplied','Verify model tie-breaking','predictions'))
                p[sid]=vec
            rows.append(r)
            if len(rows)>50000:
                raise InputProblem('FILE_TOO_LARGE','Prediction file exceeds 50,000 records','Split analyses or reduce input size','predictions')
        if not rows:
            raise InputProblem('PREDICTION_FILE_INVALID','Prediction file contains no rows','Provide at least one prediction record','predictions')
    except (csv.Error,UnicodeError) as ex:
        raise InputProblem('PREDICTION_FILE_INVALID',f'Invalid UTF-8 prediction file: {ex}','Export valid UTF-8 CSV/TSV','predictions') from ex
    finally:
        stream.close()
    if not columns:
        warnings.append(Issue('NO_PROBABILITIES','info','No probability columns supplied; confidence/coverage cannot be computed','Provide one probability column per class','predictions'))
    if manifest['independence_declaration']!='independent_documented':
        warnings.append(Issue('TARGET_INDEPENDENCE_UNKNOWN','warning','Independent sample acquisition is not documented by this manifest','Document provenance or retain exploratory interpretation','manifest.independence_declaration'))
    if manifest['evaluation_role']=='external_locked' and manifest['independence_declaration']!='independent_documented':
        raise InputProblem('TARGET_INDEPENDENCE_UNKNOWN','Cannot claim locked independent validation without documented independence','Use external_exploratory or provide documented independence','manifest.evaluation_role')
    rows.sort(key=lambda row:row['sample_id'])
    prob_array=np.array([p[r['sample_id']] for r in rows],dtype=float) if columns else None
    return Predictions(tuple(r['sample_id'] for r in rows),tuple(r['true_label'] for r in rows),
      tuple(r['predicted_label'] for r in rows),tuple(classes),prob_array,tuple(rows),manifest,
      {'predictions':data_info,'manifest':manifest_info},tuple(warnings))
