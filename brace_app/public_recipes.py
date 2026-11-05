"""Explicit, byte-pinned public preparation plans. Loading is not execution."""
import csv
from pathlib import Path
from collections import Counter
from brace_app import dataset_registry as registry
from brace_app.preparation import series_matrix

GSE21653_SHA256='f13e3bf972bd92a6fd53a1fbe42ad7c84caf4651df3a5e836f70dd3b22b5e76f'
SOURCE_MAPPING_SHA256='6019220d85b0b7624c3c7e7119af21e01109f624e562a03c230d8714b66861c7'

def er_21653_plan(dataset_id):
    original=registry.asset_path(dataset_id,'original')
    if registry.digest(original)!=GSE21653_SHA256:
        raise ValueError('This preparation plan requires the exact reviewed GSE21653 original. Changed or other studies require separate review.')
    parsed=series_matrix(original);meta=parsed['metadata'];ids=parsed['sample_ids']
    if len(ids)!=266 or set(meta['!Sample_platform_id'][0])!={'GPL570'} or set(meta['!Sample_data_processing'][0])!={'RMA using a quantile normalization'}:
        raise ValueError('Public platform, processing or sample count differs from the reviewed plan.')
    conditions={};excluded={}
    for i,sid in enumerate(ids):
        fields={}
        for row in meta['!Sample_characteristics_ch1']:
            if ': ' not in row[i]:continue
            key,value=row[i].split(': ',1)
            if key.casefold() in fields:raise ValueError('Repeated phenotype field requires review.')
            fields[key.casefold()]=value
        if fields.get('tissue')!='breast cancer tumor':raise ValueError('Unexpected tissue annotation; no inferred tumor label.')
        value=fields.get('er ihc')
        if value in ('0','1'):conditions[sid]='ER_positive' if value=='1' else 'ER_negative'
        elif value=='NA':excluded[sid]='Explicit ER IHC annotation is NA; no phenotype inferred.'
        else:raise ValueError('Unrecognized ER IHC annotation; no phenotype inferred.')
    if Counter(conditions.values())!={'ER_positive':150,'ER_negative':113} or len(excluded)!=3:
        raise ValueError('ER annotation counts differ from the reviewed plan.')
    mapping_path=Path(__file__).resolve().parents[1]/'examples/public_er_pair/prepared/selected_features.tsv'
    if registry.digest(mapping_path)!=SOURCE_MAPPING_SHA256:raise ValueError('Pinned source-only feature mapping changed.')
    with mapping_path.open(encoding='utf-8',newline='') as stream:
        mapping={r['probe_id']:r['feature_id'] for r in csv.DictReader(stream,delimiter='\t')}
    present=set(parsed['feature_ids']);mapping={p:g for p,g in mapping.items() if p in present}
    manifest=dict(schema_version='1.0.0',cohort_id='GSE21653_ER',role='target',organism='Homo sapiens',
        feature_namespace='entrez_gene',measurement_type='microarray_log2_normalized',platform='GPL570',
        labels='binary',independence_declaration='unknown',accession='GSE21653',study_id='GSE21653',
        processing_description='GEO deposited RMA using quantile normalization; RMA log2 convention; no BRACE normalization',
        sample_origin_notes='Explicit er ihc 1/0; three NA excluded. All tissue annotations are breast cancer tumor. Donor independence and cross-study ER ascertainment equivalence are unverified; exploratory only.')
    return {'summary':{'original_samples':266,'included':263,'excluded':3,'conditions':dict(Counter(conditions.values())),
        'retained_features':len(mapping),'original_sha256':GSE21653_SHA256,
        'limitations':'Exploratory additional cohort chosen after the original ER example was examined. No validation-cohort prespecification or authenticated donor independence. ER assay ascertainment and processing differ. RMA scale is declared from deposited processing, not reprocessed from CEL.'},
        'preparation':dict(schema_version='1.0.0',name='GSE21653 ER IHC - reviewed target',manifest=manifest,
            condition_by_sample=conditions,excluded_samples=excluded,feature_mapping=mapping,
            mapping_reference='GSE42568 source-only 10000-feature preparation; selected_features.tsv SHA256 '+SOURCE_MAPPING_SHA256+'; pinned GPL570 annotation. No target variance or labels used for feature selection.')}
