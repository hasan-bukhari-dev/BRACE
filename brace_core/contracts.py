"""Small, framework-agnostic scientific domain structures."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import numpy as np

@dataclass(frozen=True)
class Issue:
    code: str
    severity: str  # block, warning, info
    message: str
    next_action: str
    field: str = ''
    def to_dict(self) -> dict[str, str]:
        return {k: getattr(self, k) for k in ('code','severity','field','message','next_action')}

@dataclass(frozen=True)
class Cohort:
    cohort_id: str
    role: str
    sample_ids: tuple[str, ...]          # canonical lexicographic order
    feature_ids: tuple[str, ...]         # canonical lexicographic order
    values: np.ndarray                   # [sample, feature], immutable
    metadata: dict[str, dict[str,str]]   # sample_id -> user fields
    manifest: dict[str, Any]
    input_files: dict[str, dict[str,str | int]]
    warnings: tuple[Issue, ...]
    def __post_init__(self):
        if self.values.shape != (len(self.sample_ids), len(self.feature_ids)):
            raise ValueError('Cohort matrix shape inconsistent with identifiers')
        if not np.isfinite(self.values).all():
            raise ValueError('Nonfinite cohort matrix')
        self.values.setflags(write=False)

@dataclass(frozen=True)
class Compatibility:
    source: Cohort
    target: Cohort
    mode: str
    shared_features: tuple[str, ...]
    source_indices: tuple[int, ...]
    target_indices: tuple[int, ...]
    issues: tuple[Issue, ...]
    @property
    def eligible(self) -> bool:
        return not any(issue.severity == "block" for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        src = self.source; tgt = self.target
        counts = {
            'source_samples':len(src.sample_ids),'target_samples':len(tgt.sample_ids),
            'source_features':len(src.feature_ids),'target_features':len(tgt.feature_ids),
            'shared_features':len(self.shared_features),
            'source_only_features':len(src.feature_ids)-len(self.shared_features),
            'target_only_features':len(tgt.feature_ids)-len(self.shared_features),
            'source_overlap_fraction':round(len(self.shared_features)/len(src.feature_ids),6) if src.feature_ids else 0,
            'target_overlap_fraction':round(len(self.shared_features)/len(tgt.feature_ids),6) if tgt.feature_ids else 0,
        }
        issues = [i.to_dict() for i in self.issues]
        source_summary = cohort_summary(src)
        target_summary = cohort_summary(tgt)
        if self.mode == 'diagnose_shift':
            # Unlabeled shift mode does not inspect or display biological outcome labels.
            source_summary.pop('observed_conditions', None)
            target_summary.pop('observed_conditions', None)
        blocked = any(i['severity']=='block' for i in issues)
        verdict = 'blocked' if blocked else ('compatible_with_caveats' if any(i['severity']=='warning' for i in issues) else 'compatible')
        return {
            'stage':'04','science_version':'brace-intake/0.4.0','mode':self.mode,
            'verdict':verdict,'eligible':not blocked,
            'note':'Preflight only: no classifier has been trained; no reliability, accuracy, or causal inference has been measured.',
            'counts':counts,
            'source':source_summary,'target':target_summary,
            'shared_feature_preview':list(self.shared_features[:20]),
            'issues':issues,
            'rules':{'no_automatic_normalization':True,'no_target_label_use':True,'feature_order':'lexicographic by original feature identifier','input_format':'features by samples; canonical internal array is samples by features'}
        }

def cohort_summary(c: Cohort) -> dict[str,Any]:
    labels = {}
    for id_ in c.sample_ids:
        val=c.metadata[id_].get('condition','')
        if val: labels[val]=labels.get(val,0)+1
    arr = c.values
    return {
        'cohort_id':c.cohort_id,'role':c.role,
        'n_samples':len(c.sample_ids),'n_features':len(c.feature_ids),
        'feature_namespace':c.manifest['feature_namespace'],
        'measurement_type':c.manifest['measurement_type'],
        'platform':c.manifest.get('platform'),
        'processing_description':c.manifest['processing_description'],
        'independence_declaration':c.manifest['independence_declaration'],
        'labels_declared':c.manifest['labels'],
        'observed_conditions':labels,
        'patient_ids_reported':sum(bool(c.metadata[s].get('patient_id','')) for s in c.sample_ids),
        'study_ids':sorted({c.metadata[s].get('study_id','') for s in c.sample_ids if c.metadata[s].get('study_id','')}),
        'numeric_summary':{'min':round(float(np.min(arr)),6),'median':round(float(np.median(arr)),6),'max':round(float(np.max(arr)),6),'p95':round(float(np.percentile(arr,95)),6)},
        'input_files':c.input_files,
    }
