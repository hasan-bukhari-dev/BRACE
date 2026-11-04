"""Offline real-data preparation and integration checks; no biological results."""
from pathlib import Path
import sys
import csv
import json
import numpy as np
import pytest
from brace_core.intake import parse_cohort
from brace_core.compatibility import evaluate_compatibility

ROOT=Path(__file__).resolve().parents[1]/'examples/public_er_pair'
sys.path.insert(0,str(ROOT))
import prepare

@pytest.fixture(scope='module')
def cohorts():
    p=ROOT/'prepared'
    return tuple(parse_cohort(p/f'{r}_expression.tsv',p/f'{r}_metadata.tsv',p/f'{r}_manifest.json',r) for r in ('source','target'))

def test_alignment_labels_and_limits(cohorts):
    for c,n,counts in zip(cohorts,(101,87),({'ER_positive':67,'ER_negative':34},{'ER_positive':42,'ER_negative':45})):
        assert c.values.shape==(n,10000)
        assert len(set(c.sample_ids))==n
        assert np.isfinite(c.values).all()
        assert set(c.metadata)==set(c.sample_ids)
        assert {label:sum(c.metadata[s]['condition']==label for s in c.sample_ids) for label in counts}==counts
        for file in c.input_files.values(): assert file['bytes']<=25*1024*1024
    assert cohorts[0].feature_ids==cohorts[1].feature_ids
    assert not set(cohorts[0].sample_ids)&set(cohorts[1].sample_ids)
    pids=[r['patient_id'] for r in cohorts[1].metadata.values()]
    assert all(pids) and len(set(pids))==87

def test_compatibility_warnings_and_locked_block(cohorts):
    comp=evaluate_compatibility(*cohorts,'train_validate',classes=('ER_negative','ER_positive'))
    assert comp.eligible
    assert {'PROCESSING_DIFFERENCE','TARGET_INDEPENDENCE_UNKNOWN','PATIENT_IDENTIFIERS_ABSENT'} <= {i.code for i in comp.issues}
    locked=evaluate_compatibility(*cohorts,'train_validate',classes=('ER_negative','ER_positive'),scientific_role='external_locked')
    assert not locked.eligible
    assert any(i.code=='TARGET_INDEPENDENCE_UNKNOWN' and i.severity=='block' for i in locked.issues)

def test_original_values_and_mapping(cohorts):
    selected=dict(csv.reader((ROOT/'prepared/selected_features.tsv').read_text().splitlines()[1:],delimiter='\t'))
    assert len(selected)==10000 and len(set(selected.values()))==10000
    for acc,c in zip(prepare.ACCESSIONS,cohorts):
        _,ids,rows=prepare.matrix(ROOT/'raw'/f'{acc}_series_matrix.txt.gz')
        # Full cell-by-cell check against original deposited decimal values.
        expected=np.array([[float(rows[selected[g]][ids.index(s)]) for g in c.feature_ids] for s in c.sample_ids])
        np.testing.assert_array_equal(c.values,expected)

def test_reproducible_preparation(tmp_path):
    prepare.prepare(ROOT/'raw',tmp_path)
    expected=json.loads((ROOT/'prepared/prepared_hashes.json').read_text())
    assert json.loads((tmp_path/'prepared_hashes.json').read_text())==expected
    for name,entry in expected.items(): assert prepare.sha(tmp_path/name)==entry['sha256']

def test_complete_inclusion_ledger():
    for role,total,included in [('source',121,101),('target',90,87)]:
        records=list(csv.DictReader((ROOT/f'prepared/{role}_all_samples.tsv').open(encoding='utf-8'),delimiter='\t'))
        assert len(records)==total
        assert sum(r['inclusion']=='included' for r in records)==included
        assert all(r['inclusion'] in ('included','non_tumor','ER_missing') for r in records)
