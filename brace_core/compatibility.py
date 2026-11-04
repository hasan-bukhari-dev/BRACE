"""Explicit scientific eligibility checks; does not train models or correct assays."""
from __future__ import annotations
from collections import Counter,defaultdict
from .contracts import Cohort,Compatibility,Issue

VALID_MEASUREMENTS={'microarray_log2_normalized','rnaseq_log2_normalized','rnaseq_vst'}

def _issue(code,severity,message,action,field=''):
    return Issue(code,severity,message,action,field)

def evaluate_compatibility(source:Cohort,target:Cohort,mode:str,classes:tuple[str,...]=('normal','tumor'),scientific_role:str='external_exploratory')->Compatibility:
    if mode not in ('train_validate','diagnose_shift'):
        raise ValueError('Stage 04 supports train_validate or diagnose_shift')
    if scientific_role not in ('external_exploratory','external_locked','unlabeled_shift_only'):
        raise ValueError('Invalid scientific_role')
    if mode=='train_validate' and scientific_role=='unlabeled_shift_only':
        raise ValueError('train_validate cannot claim unlabeled_shift_only')
    if mode=='diagnose_shift' and scientific_role!='unlabeled_shift_only':
        raise ValueError('diagnose_shift requires unlabeled_shift_only role')
    issues=list(source.warnings)+list(target.warnings)
    if source.cohort_id==target.cohort_id:
        issues.append(_issue('DUPLICATE_COHORT_ID','block','Source and target have the same cohort_id','Assign distinct cohort identities','manifest.cohort_id'))
    if source.manifest['feature_namespace']!=target.manifest['feature_namespace']:
        issues.append(_issue('FEATURE_NAMESPACE_MISMATCH','block','Gene identifier namespaces differ between cohorts','Use a documented deterministic common feature namespace','manifest.feature_namespace'))
    s_meas=source.manifest['measurement_type']; t_meas=target.manifest['measurement_type']
    if s_meas!=t_meas or s_meas not in VALID_MEASUREMENTS:
        issues.append(_issue('MEASUREMENT_INCOMPATIBLE','block',f'Unsupported measurement comparison: {s_meas} vs {t_meas}','Use the same supported processed measurement type; no automatic normalization','manifest.measurement_type'))
    if s_meas=='microarray_log2_normalized' and t_meas=='microarray_log2_normalized':
        ps=source.manifest.get('platform','');pt=target.manifest.get('platform','')
        if not ps or not pt:
            issues.append(_issue('PLATFORM_UNVERIFIED','block','Microarray platform is missing in at least one manifest','Declare the platform (e.g. GPL570) in both manifests','manifest.platform'))
        elif ps!=pt:
            issues.append(_issue('PLATFORM_DIFFERENCE','block',f'Microarray platforms differ: {ps} vs {pt}','Provide a reviewed cross-platform protocol; MVP supports matching microarray platforms only','manifest.platform'))
    if source.manifest['processing_description'].strip().casefold()!=target.manifest['processing_description'].strip().casefold():
        issues.append(_issue('PROCESSING_DIFFERENCE','warning','The cohorts declare different processing methods; shared measurement types do not guarantee directly comparable scales','Inspect processing provenance and interpret shifts cautiously; no correction applied','manifest.processing_description'))
    srcmap={k:i for i,k in enumerate(source.feature_ids)}
    tgtmap={k:i for i,k in enumerate(target.feature_ids)}
    shared=tuple(sorted(set(srcmap)&set(tgtmap)))
    if not shared:
        issues.append(_issue('NO_SHARED_FEATURES','block','No shared feature IDs were found','Verify feature namespaces, annotations and identifier versions','expression.feature_id'))
    elif len(shared)<100 or min(len(shared)/len(source.feature_ids),len(shared)/len(target.feature_ids))<.5:
        issues.append(_issue('LOW_FEATURE_OVERLAP','warning',f'Only {len(shared)} features overlap; limited gene coverage may affect comparisons','Review the gene mapping and excluded feature sets','expression.feature_id'))
    # Patient collisions matter even when sample IDs themselves differ.
    source_patients={source.metadata[s].get('patient_id','') for s in source.sample_ids};source_patients.discard('')
    target_patients={target.metadata[s].get('patient_id','') for s in target.sample_ids};target_patients.discard('')
    overlap=source_patients & target_patients
    if overlap:
        severity='block' if scientific_role=='external_locked' else 'warning'
        issues.append(_issue('PATIENT_OVERLAP',severity,f'{len(overlap)} patient identifiers occur in both cohorts; independent evaluation is not established','Resolve identities and remove overlapping patients or classify the analysis as exploratory','metadata.patient_id'))
    if source.manifest['independence_declaration']!='independent_documented' or target.manifest['independence_declaration']!='independent_documented':
        severity='block' if scientific_role=='external_locked' else 'warning'
        issues.append(_issue('TARGET_INDEPENDENCE_UNKNOWN',severity,'Independent cohort acquisition is not documented for both cohorts','Document non-overlapping study/patient provenance or retain exploratory reporting','manifest.independence_declaration'))
    if source.manifest['independence_declaration']=='not_independent' or target.manifest['independence_declaration']=='not_independent':
        if scientific_role=='external_locked':
            issues.append(_issue('KNOWN_NONINDEPENDENCE','block','A manifest explicitly declares non-independence','Use exploratory study role and disclose overlap','manifest.independence_declaration'))
        else:
            issues.append(_issue('KNOWN_NONINDEPENDENCE','warning','A manifest explicitly declares non-independence; cannot label this independent validation','Disclose non-independence in report','manifest.independence_declaration'))
    if not source_patients or not target_patients:
        issues.append(_issue('PATIENT_IDENTIFIERS_ABSENT','warning','Patient IDs are absent in one or both cohorts; cannot rule out overlapping subjects using identifiers alone','Provide patient-level provenance or maintain unverified independence statement','metadata.patient_id'))
    if mode=='train_validate':
        if len(classes)!=2 or any(not x or not x.strip() for x in classes) or len(set(classes))!=2:
            issues.append(_issue('LABEL_MAPPING_INCONSISTENT','block','Binary baseline requires exactly two distinct nonempty declared classes','Declare an explicit pair of class labels','classes'))
        if source.manifest['labels']!='binary' or target.manifest['labels']!='binary':
            issues.append(_issue('LABEL_MAPPING_INCONSISTENT','block','Supervised Mode B requires binary condition labels in both cohort manifests','Provide correctly labeled sample metadata and manifests','manifest.labels'))
        for cohort in (source,target):
            labs=[cohort.metadata[s].get('condition','') for s in cohort.sample_ids]
            bad=sorted(set(labs)-set(classes))
            if bad:
                issues.append(_issue('LABEL_MAPPING_INCONSISTENT','block',f'{cohort.role} labels are missing or outside the declared classes: {bad[:5]}','Supply exact condition names or explicit documented remapping','metadata.condition'))
            counts=Counter(labs)
            if cohort.role=='source':
                sparse=[x for x in classes if counts[x]<5]
                if sparse:
                    issues.append(_issue('SOURCE_CV_UNSUPPORTED','block',f'Source has fewer than 5 samples in class(es): {sparse}; 5-fold benchmark not eligible','Add independent source examples before supervised training','metadata.condition'))
            else:
                if len(cohort.sample_ids)<2:
                    issues.append(_issue('TARGET_TOO_SMALL','block','Target has fewer than two samples','Provide at least two target samples','metadata'))
                absent=[x for x in classes if counts[x]==0]
                if absent:
                    issues.append(_issue('LIMITED_CLASS_SUPPORT','warning',f'Target does not contain true class(es): {absent}; full binary-class generalization cannot be assessed','Interpret target metrics only for observed classes','metadata.condition'))
            if any(0<counts[x]<10 for x in classes):
                issues.append(_issue('LOW_CLASS_SUPPORT','warning',f'{cohort.role} class counts below 10: {dict(counts)}','Use cautious interpretation and report exact denominators','metadata.condition'))
            patient_to_class=defaultdict(set)
            for sid in cohort.sample_ids:
                pid=cohort.metadata[sid].get('patient_id','')
                if pid:patient_to_class[pid].add(cohort.metadata[sid].get('condition',''))
            if any(len(v)>1 for v in patient_to_class.values()):
                issues.append(_issue('PATIENT_LABEL_CONFLICT','warning',f'{cohort.role} has repeated patient IDs with different condition labels','Audit repeated measures; ensure patient-aware split','metadata.patient_id'))
            if len(patient_to_class)<len([cohort.metadata[s].get('patient_id','') for s in cohort.sample_ids if cohort.metadata[s].get('patient_id','')]):
                issues.append(_issue('REPEATED_PATIENT_IDS','warning',f'{cohort.role} contains repeated patient identifiers; future CV must use group-aware splitting','Use StratifiedGroupKFold or block unsupported training in Stage 05','metadata.patient_id'))
            bystudy=defaultdict(set)
            study_values=[]
            for sid in cohort.sample_ids:
                study=cohort.metadata[sid].get('study_id','')
                if study:
                    bystudy[study].add(cohort.metadata[sid].get('condition',''))
                    study_values.append(study)
            if len(bystudy)>1 and len(study_values)==len(cohort.sample_ids) and all(len(v)==1 for v in bystudy.values()) and len(set().union(*bystudy.values()))>1:
                issues.append(_issue('CLASS_STUDY_CONFOUNDING','warning',f'{cohort.role} class label is perfectly separated by recorded study_id; effects cannot be disentangled','Use a design with multiple biological classes per study where possible','metadata.study_id'))
    else:
        # Labels are not consulted for Mode C inference; no label statistics interpreted.
        pass
    return Compatibility(source,target,mode,shared,tuple(srcmap[k] for k in shared),tuple(tgtmap[k] for k in shared),tuple(issues))
