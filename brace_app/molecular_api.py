"""Read-only linkage of frozen RACE statistics to hash-checked molecular inputs.

No testing, fitting, normalization or annotation guessing occurs on this path.
"""
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from collections import Counter
from fastapi import APIRouter, HTTPException
from brace_core.intake import parse_cohort
from brace_core.signature import FILES, digest
from brace_app.study_api import public_paths

router=APIRouter()

def obj(path):return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

@lru_cache(maxsize=4)
def parsed(paths,hashes,role):
    # Cache immutable numerical arrays only after content checks on every request.
    return parse_cohort(*paths,role)

def context(study_id):
    from brace_app import server
    public=study_id=='public_er_pass2'
    try:
        if public:
            pair=public_paths();folder=pair/'race_final';inputs=pair/'prepared'
        else:
            root=server.safe_run_dir(study_id);folder=root/'race';inputs=root/'input'
            if not (folder/'race_result.json').is_file():raise HTTPException(404,'No RACE evidence for this run')
            records=obj(root/'reproducibility_manifest.json')['artifacts']
            for name in FILES:
                if sha(folder/name)!=records[name]['sha256']:raise ValueError('Scientific artifact hash mismatch')
        result=obj(folder/'race_result.json');methods=obj(folder/'race_methods.json');frozen=obj(folder/'selected_signature.json')
        claimed=frozen['hypothesis_hash']
        if digest({k:v for k,v in frozen.items() if k!='hypothesis_hash'})!=claimed or result['hypothesis_hash']!=claimed or methods['source_hypothesis_hash']!=claimed:
            raise ValueError('Frozen result identity mismatch')
        if [g['feature_id'] for g in result['genes']]!=[g['feature_id'] for g in frozen['selected']]:raise ValueError('Frozen gene family mismatch')
        cohorts={}
        for role in ('source','target'):
            paths=[];hashes=[]
            for field in ('expression','metadata','manifest'):
                record=methods['input_files'][role][field];name=record['name']
                allowed={f'{role}_{field}.json'} if field=='manifest' else {f'{role}_{field}.csv',f'{role}_{field}.tsv'}
                if name not in allowed:raise ValueError('Unexpected saved input filename')
                path=inputs/name
                if sha(path)!=record['sha256']:raise ValueError('Input hash mismatch')
                paths.append(str(path));hashes.append(record['sha256'])
            cohorts[role]=parsed(tuple(paths),tuple(hashes),role)
        annotations={}
        # Only use pinned platform annotations when all six inputs equal the approved pair.
        from brace_app import server
        pair=server.BASE/'examples/public_er_pair'
        try:
            reference=obj(pair/'race_final/race_methods.json')['input_files']
            matches=all(methods['input_files'][r][k]['sha256']==reference[r][k]['sha256'] for r in ('source','target') for k in ('expression','metadata','manifest'))
        except (OSError,ValueError,KeyError):matches=False
        preparation=None
        if public or matches:
            try:
                pair=public_paths()
                annotations={a['feature_id']:a for a in obj(pair/'race_final/gene_annotations.json')}
                preparation=obj(pair/'prepared/summary.json')
            except HTTPException:
                if public:raise
        return result,methods,frozen,cohorts,annotations,preparation
    except HTTPException:raise
    except (OSError,ValueError,KeyError,TypeError) as exc:
        raise HTTPException(409,{'code':'MOLECULAR_EVIDENCE_UNAVAILABLE','message':'Gene measurements cannot be linked to the saved result: '+str(exc)+'. Restore matching inputs and evidence; no replacement values were generated.'}) from exc

def cohort_context(c,result,role,preparation):
    counts=Counter(c.metadata[s].get('condition','') for s in c.sample_ids)
    original=preparation.get(c.manifest.get('accession','')) if preparation else None
    return dict(cohort_id=c.cohort_id,study_id=c.manifest.get('study_id'),accession=c.manifest.get('accession'),
        n_samples=len(c.sample_ids),conditions={label:dict(n=n,proportion=n/len(c.sample_ids)) for label,n in counts.items()},
        feature_count=len(c.feature_ids),platform=c.manifest.get('platform'),feature_namespace=c.manifest['feature_namespace'],
        measurement_type=c.manifest['measurement_type'],processing_description=c.manifest['processing_description'],
        independence_declaration=c.manifest['independence_declaration'],preparation=original,
        original_exclusions_known=original is not None,notes=c.manifest.get('sample_origin_notes'))

def annotated(row,annotations,namespace):
    a=annotations.get(row['feature_id'],{})
    return {**row,'gene_symbol':a.get('gene_symbol'),'probe_id':a.get('probe_id'),
            'feature_namespace':namespace,'annotation_note':a.get('annotation_source','No verified symbol annotation supplied; exact feature identifier retained.')}

@router.get('/api/race/studies/{study_id}/genes')
def genes(study_id:str):
    result,methods,frozen,cohorts,annotations,preparation=context(study_id)
    source={r['feature_id']:r for r in frozen['selected']}
    rows=[annotated({**r,'source_p':source[r['feature_id']]['p'],'source_hedges_g':source[r['feature_id']]['hedges_g'],
        'source_ci95':source[r['feature_id']]['ci95'],'source_n_positive':source[r['feature_id']]['n_positive'],
        'source_n_negative':source[r['feature_id']]['n_negative']},annotations,cohorts['source'].manifest['feature_namespace']) for r in result['genes']]
    return dict(study_id=study_id,hypothesis_hash=result['hypothesis_hash'],aggregate=result['aggregate'],genes=rows,
        positive=result['positive'],negative=result['negative'],condition_definitions=frozen['condition_definitions'],
        cohorts={r:cohort_context(c,result,r,preparation) for r,c in cohorts.items()},feature_coverage=result['feature_coverage'],
        warnings=result['warnings'],evaluation_role=result['evaluation_role'],
        shift_available=False,shift_note='This RACE run does not compute PCA or distribution shift. Existing shift results remain available in ACE for runs that computed them.')

@router.get('/api/race/studies/{study_id}/gene')
def gene(study_id:str,feature_id:str):
    result,methods,frozen,cohorts,annotations,preparation=context(study_id)
    selected=next((r for r in result['genes'] if r['feature_id']==feature_id),None)
    if selected is None:raise HTTPException(404,'Feature is not in this frozen signature')
    src=next(r for r in frozen['selected'] if r['feature_id']==feature_id)
    details={}
    for role,c in cohorts.items():
        statistic=src if role=='source' else selected
        available=feature_id in c.feature_ids
        groups=[]
        for label in (result['negative'],result['positive']):
            ids=[(i,s) for i,s in enumerate(c.sample_ids) if c.metadata[s].get('condition')==label]
            j=c.feature_ids.index(feature_id) if available else None
            samples=[dict(sample_id=s,value=float(c.values[i,j])) for i,s in ids] if available else []
            key='n_positive' if label==result['positive'] else 'n_negative'
            if statistic[key]!=len(ids):raise HTTPException(409,'Saved group sizes and checked input labels disagree')
            groups.append(dict(condition=label,n=len(ids),observed_n=len(samples),samples=samples))
        details[role]=dict(**cohort_context(c,result,role,preparation),groups=groups,statistics=statistic,
            available=available,unavailable_reason=None if available else 'missing_target_feature',missing_values=0 if available else None,
            missingness_note='BRACE intake requires complete finite cells; no imputation. Unavailable features have no distribution.')
    trace=dict(study_id=study_id,feature_id=feature_id,hypothesis_hash=result['hypothesis_hash'],
        source_selection_rule=frozen['selection_rule'],source_family_size=methods['source_family_size'],target_family_size=methods['target_family_size'],
        input_files=methods['input_files'],method_version=methods['version'],software=methods['software'],
        method_descriptions={k:methods[k] for k in ('test','effect','standardized','ci','multiplicity')},
        no_statistical_rerun=True)
    return dict(study_id=study_id,feature=annotated(selected,annotations,cohorts['source'].manifest['feature_namespace']),
        positive=result['positive'],negative=result['negative'],condition_definitions=frozen['condition_definitions'],
        cohorts=details,warnings=result['warnings'],trace=trace,
        measurement_comparison='Separate within-cohort distributions and axes. Absolute source and target intensities are not assumed comparable.')
