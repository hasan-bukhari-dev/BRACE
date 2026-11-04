"""Measurement adapters describe validated operations, never infer readiness."""
from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True)
class AssayAdapter:
    id: str
    label: str
    modality: str
    data_state: str
    feature_namespaces: tuple[str, ...]
    operations: tuple[str, ...]
    requires_platform: bool
    limitations: str


GENE_NAMESPACES = ('gene_symbol', 'ensembl_gene', 'entrez_gene', 'probe_id')
ADAPTERS = {
    'microarray_log2_normalized': AssayAdapter('microarray_log2_normalized', 'Microarray · normalized log2',
        'bulk_transcriptomics', 'normalized_log2', GENE_NAMESPACES,
        ('race', 'train_validate', 'diagnose_shift', 'replay_frozen'), True,
        'Matching platforms and reviewed processing required. RACE is exploratory and unpaired.'),
    'rnaseq_log2_normalized': AssayAdapter('rnaseq_log2_normalized', 'RNA-seq · normalized log2',
        'bulk_transcriptomics', 'normalized_log2', GENE_NAMESPACES,
        ('train_validate', 'diagnose_shift', 'replay_frozen'), False,
        'Already processed matrices only; no raw reads/count normalization and no RACE support.'),
    'rnaseq_vst': AssayAdapter('rnaseq_vst', 'RNA-seq · variance-stabilized',
        'bulk_transcriptomics', 'variance_stabilized', GENE_NAMESPACES,
        ('train_validate', 'diagnose_shift', 'replay_frozen'), False,
        'Transformation must be documented and compatible. No raw preprocessing and no RACE support.')}


def catalog() -> dict:
    return {'schema_version': '1.0.0', 'adapters': [asdict(adapter) for adapter in ADAPTERS.values()],
        'saved_predictions': {'modality': 'structured_classification', 'operations': ['evaluate_predictions'],
                              'labels_required_for_accuracy': True, 'multiclass': True},
        'not_implemented': ['Processed proteomics', 'Metabolomics', 'Methylation/epigenomics',
                            'Single-cell inference', 'Raw FASTQ/count preprocessing'],
        'note': 'Adapter presence describes accepted representations, not dataset-pair eligibility.'}


def identifier_hints(feature_ids) -> dict:
    """Lexical hints for explicit review; never a gene mapping or namespace claim."""
    identifiers = list(feature_ids)
    candidates = []
    if identifiers and all(re.fullmatch(r'ENSG[0-9]+(?:\.[0-9]+)?', value) for value in identifiers):
        candidates.append('ensembl_gene')
    if identifiers and all(value.isdigit() for value in identifiers):
        candidates.extend(['entrez_gene', 'numeric_probe_or_other'])
    if identifiers and all(re.fullmatch(r'[0-9]+(?:_[asx])?_at', value) for value in identifiers):
        candidates.append('probe_id')
    if not candidates and identifiers and all(re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]*', value) for value in identifiers):
        candidates.extend(['gene_symbol', 'other_text_identifier'])
    return {'candidates': candidates, 'requires_review': True,
            'note': 'Lexical patterns only. Numeric and text identifiers may be probes or other namespaces. '
                    'Verify the actual annotation reference; no IDs or Ensembl versions were changed.'}
