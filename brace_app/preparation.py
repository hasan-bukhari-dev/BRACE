"""Bounded GEO Series Matrix parsing and explicit, reviewed transformations."""
from __future__ import annotations

import csv
import gzip
import io
import json
import math
import hashlib
import numpy as np
from pathlib import Path

from brace_core.intake import InputProblem, MAX_FEATURES, MAX_SAMPLES

MAX_EXPANDED = 128 * 1024 * 1024
MAX_ORIGINAL_FEATURES = 100_000


def series_matrix(path: Path, include_values: bool = False, selected_features: set | None = None) -> dict:
    metadata: dict[str, list] = {}
    samples = []
    values = {}
    features = []
    row_bytes = []
    variances = []
    expanded = 0
    in_table = False
    ended = False
    seen = set()
    try:
        with gzip.open(path, 'rb') as stream:
            while True:
                line = stream.readline(1024 * 1024 + 1)
                if not line:
                    break
                expanded += len(line)
                if len(line) > 1024 * 1024 or expanded > MAX_EXPANDED:
                    raise ValueError('Expanded GEO matrix exceeds the bounded 128 MiB / 1 MiB per-line limit.')
                text = line.decode('utf-8').rstrip('\r\n')
                if ended:
                    continue  # consume to verify the gzip CRC, including concatenated members
                if text == '!series_matrix_table_begin':
                    in_table = True
                    continue
                if text == '!series_matrix_table_end':
                    ended = True
                    continue
                row = next(csv.reader([text], delimiter='\t', strict=True), [])
                if not in_table:
                    if row and row[0].startswith(('!Sample_', '!Series_')):
                        metadata.setdefault(row[0], []).append(row[1:])
                    continue
                if not samples:
                    if not row or row[0] != 'ID_REF' or not 2 <= len(row) - 1 <= MAX_SAMPLES:
                        raise ValueError('Expected ID_REF and 2–500 sample columns in a GEO Series Matrix table.')
                    samples = row[1:]
                    if len(set(samples)) != len(samples) or any(not sample.strip() for sample in samples):
                        raise ValueError('GEO sample identifiers must be unique and nonempty.')
                    continue
                if len(row) != len(samples) + 1 or not row[0] or row[0] in seen:
                    raise ValueError('GEO matrix contains a duplicate feature or an inconsistent row width.')
                numbers = [float(value) for value in row[1:]]
                if not all(math.isfinite(number) for number in numbers):
                    raise ValueError('GEO matrix contains missing or nonfinite values. Supply documented preprocessing.')
                seen.add(row[0])
                features.append(row[0])
                row_bytes.append(len(line))
                variances.append(float(np.var(numbers)))
                if include_values and (selected_features is None or row[0] in selected_features):
                    values[row[0]] = row[1:]  # preserve numeric text; no normalization or rounding
                    if len(values) > MAX_FEATURES:
                        raise ValueError('More than 25,000 prepared features. Supply an explicit reviewed feature mapping/subset.')
                if len(features) > MAX_ORIGINAL_FEATURES:
                    raise ValueError('GEO matrix exceeds 100,000 original features. Supply a documented prepared subset.')
        if not ended or not features:
            raise ValueError('No complete supported numeric GEO Series Matrix table was found.')
        declared = metadata.get('!Sample_geo_accession', [])
        if declared and (len(declared) != 1 or declared[0] != samples):
            raise ValueError('GEO table sample identifiers differ from the declared sample accessions.')
        return dict(sample_ids=samples, feature_ids=features, values=values,
                    metadata=metadata, expanded_bytes=expanded, feature_row_bytes=row_bytes, feature_variances=variances)
    except (OSError, EOFError, UnicodeError, csv.Error, ValueError) as exc:
        raise InputProblem('GEO_PREPARATION_BLOCKED', str(exc),
            'Preserve the acquired original. Supply finite processed expression, sample metadata and a BRACE manifest if this matrix is unsupported.') from exc


def prepare_general(original: Path, directory: Path, *, manifest: dict,
                    condition_by_sample: dict[str, str], feature_mapping: dict[str, str],
                    mapping_reference: str, excluded_samples: dict[str, str],
                    feature_policy: str = 'all', reference_ids: list[str] | None = None,
                    source_feature_cap: int = 10000) -> tuple[dict, dict]:
    if feature_policy not in ('all', 'bounded_original_order', 'source_variance', 'source_features', 'identifier_panel'):
        raise ValueError('Unsupported feature policy.')
    if feature_policy != 'all':
        if feature_mapping:
            raise ValueError('Choose a feature mapping or an original-order subset, not both.')
        preview = series_matrix(original)
        retained_ids = []
        # Original numeric text is preserved. Original TSV row lengths are a
        # conservative bound for output rows; reserve a full MiB for headers.
        budget = 24 * 1024 * 1024
        order = list(range(len(preview['feature_ids'])))
        limit = MAX_FEATURES
        if feature_policy in ('source_variance','identifier_panel'):
            if manifest.get('role') != 'source':
                raise ValueError('Variance selection is source-only. Align the target to a prepared source.')
            if feature_policy == 'source_variance':
                order.sort(key=lambda i: (-preview['feature_variances'][i], preview['feature_ids'][i]))
            else:
                order.sort(key=lambda i: (hashlib.sha256(preview['feature_ids'][i].encode()).hexdigest(),preview['feature_ids'][i]))
            if isinstance(source_feature_cap,bool) or not 1 <= source_feature_cap <= 25000:
                raise ValueError('Source feature budget must be 1–25,000.')
            limit = min(MAX_FEATURES, source_feature_cap)
        elif feature_policy == 'source_features':
            if not reference_ids:
                raise ValueError('No source feature reference was supplied.')
            wanted = set(reference_ids)
            order = [i for i in order if preview['feature_ids'][i] in wanted]
            if len(order) != len(wanted):
                raise ValueError('The target lacks source feature IDs. Review the platform/namespace or supply a curated common-ID mapping.')
        for i in order:
            feature, size = preview['feature_ids'][i], preview['feature_row_bytes'][i]
            if len(retained_ids) == limit:
                break
            if size > budget:
                if feature_policy in ('source_features','identifier_panel') and size > budget:
                    raise ValueError('The complete source feature set exceeds target preparation limits. Prepare a smaller source set before alignment.')
                break
            retained_ids.append(feature)
            budget -= size
        if not retained_ids:
            raise ValueError('No original feature fits the bounded preparation limit.')
        feature_mapping = {feature: feature for feature in retained_ids}
        mapping_reference = 'Original-order prefix within 25,000 features and 24 MiB row-text budget; no outcome-based selection or gene mapping'
        if feature_policy == 'source_variance':
            mapping_reference = f'Source-only population variance across original source samples, descending; identifier breaks ties; cap {limit} features and 24 MiB. No phenotype labels or target values used.'
        elif feature_policy == 'source_features':
            mapping_reference = 'Exact prepared source identifiers; target values and phenotype labels do not select features. Original numeric text preserved.'
        elif feature_policy == 'identifier_panel':
            mapping_reference = f'Fixed identifier panel: smallest SHA-256(identifier) values, cap {limit}. No expression values, labels or target data rank features. Computational subset, not a representative biological panel.'
    parsed = series_matrix(original, include_values=True, selected_features=set(feature_mapping) if feature_mapping else None)
    samples = parsed['sample_ids']
    if set(condition_by_sample) | set(excluded_samples) != set(samples) or set(condition_by_sample) & set(excluded_samples):
        raise ValueError('Review every sample: map it to a condition (empty only for unlabeled inputs), or supply an exclusion reason.')
    if any(not reason.strip() for reason in excluded_samples.values()):
        raise ValueError('Each excluded sample needs a nonempty scientific reason.')
    included = [sample for sample in samples if sample not in excluded_samples]
    if len(included) < 2:
        raise ValueError('At least two included samples are required.')
    if manifest.get('labels') == 'binary' and any(not condition_by_sample[sample].strip() for sample in included):
        raise ValueError('Labeled preparations require an explicit condition for every included sample.')
    if manifest.get('labels') == 'unlabeled' and any(condition_by_sample.values()):
        raise ValueError('Unlabeled preparation must use empty conditions; do not store unreviewed labels.')
    original_features = parsed['feature_ids']
    if feature_mapping:
        if not mapping_reference.strip() or set(feature_mapping) - set(original_features):
            raise ValueError('Mapping needs a reference/version and must refer only to original features.')
        if len(set(feature_mapping.values())) != len(feature_mapping) or any(not value.strip() for value in feature_mapping.values()):
            raise ValueError('Feature mapping must be one-to-one and unambiguous. Resolve duplicate gene mappings explicitly.')
    indices = [samples.index(sample) for sample in included]
    retained = [(feature_mapping.get(feature) if feature_mapping else feature, row)
                for feature, row in parsed['values'].items()]
    if not 1 <= len(retained) <= MAX_FEATURES:
        raise ValueError('Prepared inputs require 1–25,000 features. Supply an explicit, scientifically justified mapping/subset.')
    paths = {kind: directory / (kind + suffix) for kind, suffix in
             (('expression', '.tsv'), ('metadata', '.tsv'), ('manifest', '.json'))}
    with paths['expression'].open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        writer.writerow(['feature_id', *included])
        for feature, values in retained:
            writer.writerow([feature, *(values[index] for index in indices)])
    with paths['metadata'].open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        writer.writerow(['sample_id', 'condition', 'study_id'])
        writer.writerows((sample, condition_by_sample[sample], manifest.get('study_id', '')) for sample in included)
    paths['manifest'].write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    report = dict(operation='reviewed_geo_series_matrix', automatic_normalization=False,
        feature_policy=feature_policy, selection_uses_labels=False,
        phenotype_mapping=condition_by_sample, excluded_samples=excluded_samples,
        original_features=len(original_features), retained_features=len(retained),
        unmapped_features=[feature for feature in original_features if feature_mapping and feature not in feature_mapping],
        feature_mapping=feature_mapping, mapping_reference=mapping_reference or 'Original identifiers preserved',
        processing_declaration=manifest.get('processing_description'),
        limitations=['Phenotypes, feature mapping and measurement scale are user-reviewed declarations, not independently authenticated.',
                    'No donor identities are inferred from sample names.'])
    return paths, report
