"""Stage 04 implementation tests, including adversarial input contracts."""
import csv,json,sys,subprocess,hashlib
from pathlib import Path
import numpy as np
import pytest
from brace_core.intake import parse_cohort,InputProblem
from brace_core.compatibility import evaluate_compatibility
from brace_core.cli import execute
from brace_core.reporting import generate_report

EX=Path(__file__).resolve().parents[1]/'examples'/'synthetic_valid'

def files(role):
    return [EX/f'{role}_expression.csv',EX/f'{role}_samples.csv',EX/f'{role}_manifest.json']

def cohorts():
    return parse_cohort(*files('source'),'source'),parse_cohort(*files('target'),'target')

def modify_csv(tmp_path,path,fn,name=None,sep=','):
    with path.open(newline='',encoding='utf-8') as f: rows=list(csv.reader(f,delimiter=sep))
    fn(rows)
    out=tmp_path/(name or path.name)
    with out.open('w',newline='',encoding='utf-8') as f:csv.writer(f,delimiter=sep).writerows(rows)
    return out

def modify_manifest(tmp_path,role,fn):
    m=json.loads(files(role)[2].read_text());fn(m)
    p=tmp_path/f'{role}_manifest_changed.json';p.write_text(json.dumps(m));return p

def expect_error(code,fn):
    with pytest.raises(InputProblem) as e:fn()
    assert e.value.issue.code==code

def test_valid_cohorts_are_canonical_and_immutable():
    a,b=cohorts()
    assert a.values.shape==(20,120) and b.values.shape==(14,120)
    assert list(a.sample_ids)==sorted(a.sample_ids)
    assert list(a.feature_ids)==sorted(a.feature_ids)
    assert not a.values.flags.writeable
    with pytest.raises(ValueError):a.values[0,0]=12

def test_default_mode_b_eligible_with_warnings():
    a,b=cohorts();p=evaluate_compatibility(a,b,'train_validate')
    d=p.to_dict();assert d['eligible'] and d['verdict']=='compatible_with_caveats'
    assert d['counts']['shared_features']==120
    assert {'TARGET_INDEPENDENCE_UNKNOWN','LOW_CLASS_SUPPORT'}<=set(i['code'] for i in d['issues'])

def test_mode_c_uses_no_labels_for_eligibility(tmp_path):
    a,b=cohorts()
    # Source condition can be absent in metadata under Mode C
    mm=modify_csv(tmp_path,files('source')[1],lambda rows: rows.__setitem__(0,['sample_id','patient_id','study_id']) or [row.pop(1) for row in rows[1:]])
    no_labels=parse_cohort(files('source')[0],mm,files('source')[2],'source')
    p=evaluate_compatibility(no_labels,b,'diagnose_shift',scientific_role='unlabeled_shift_only')
    assert p.eligible

def test_report_end_to_end_and_export(tmp_path):
    a,b=cohorts();p=evaluate_compatibility(a,b,'train_validate')
    rep=generate_report(p,tmp_path,export_aligned=True)
    assert (tmp_path/'compatibility_report.html').exists()
    assert (tmp_path/'source_aligned_expression.csv').exists()
    assert (tmp_path/'target_aligned_expression.csv').exists()
    assert rep['source']['input_files']['expression']['sha256']==hashlib.sha256(files('source')[0].read_bytes()).hexdigest()
    with (tmp_path/'source_aligned_expression.csv').open() as f:
        lines=list(csv.reader(f))
    assert lines[0]==['feature_id',*a.sample_ids]
    assert len(lines)==121
    assert float(lines[1][1])==a.values[0,0]
    assert 'computed' not in rep.get('note','') or 'no classifier' in rep.get('note','')

def test_output_default_does_not_duplicate_expression(tmp_path):
    p=evaluate_compatibility(*cohorts(),'diagnose_shift',scientific_role='unlabeled_shift_only')
    generate_report(p,tmp_path)
    assert not (tmp_path/'source_aligned_expression.csv').exists()

def test_feature_order_and_sample_order_do_not_change_canonical_values(tmp_path):
    a,_=cohorts()
    def rev(rows):
        rows[0]=[rows[0][0]]+rows[0][:0:-1]
        for r in rows[1:]:r[1:]=r[:0:-1]
        rows[1:]=rows[:0:-1]
    altered=modify_csv(tmp_path,files('source')[0],rev)
    a2=parse_cohort(altered,*files('source')[1:],'source')
    assert a.feature_ids==a2.feature_ids and a.sample_ids==a2.sample_ids
    np.testing.assert_array_equal(a.values,a2.values)

def test_tsv_ingestion(tmp_path):
    new=[]
    for p in files('source')[:2]:
        target=tmp_path/(p.stem+'.tsv')
        with p.open(newline='') as inf,target.open('w',newline='') as outf:
            csv.writer(outf,delimiter='\t').writerows(csv.reader(inf))
        new.append(target)
    c=parse_cohort(*new,files('source')[2],'source')
    assert c.values.shape==(20,120)

def test_duplicate_feature_rejected(tmp_path):
    m=modify_csv(tmp_path,files('source')[0],lambda r:r.__setitem__(2,[r[1][0],*r[2][1:]]))
    expect_error('DUPLICATE_FEATURE_ID',lambda:parse_cohort(m,*files('source')[1:],'source'))

def test_normalized_duplicate_feature_rejected(tmp_path):
    m=modify_csv(tmp_path,files('source')[0],lambda r:r.__setitem__(2,[' '+r[1][0]+' ',*r[2][1:]]))
    expect_error('DUPLICATE_FEATURE_ID',lambda:parse_cohort(m,*files('source')[1:],'source'))

def test_duplicate_expression_sample_rejected(tmp_path):
    m=modify_csv(tmp_path,files('source')[0],lambda r:r[0].__setitem__(2,r[0][1]))
    expect_error('DUPLICATE_SAMPLE_ID',lambda:parse_cohort(m,*files('source')[1:],'source'))

def test_duplicate_metadata_sample_rejected(tmp_path):
    m=modify_csv(tmp_path,files('source')[1],lambda r:r[2].__setitem__(0,r[1][0]))
    expect_error('DUPLICATE_SAMPLE_ID',lambda:parse_cohort(files('source')[0],m,files('source')[2],'source'))

def test_missing_metadata_sample_rejected(tmp_path):
    m=modify_csv(tmp_path,files('source')[1],lambda r:r.pop())
    expect_error('SAMPLE_SET_MISMATCH',lambda:parse_cohort(files('source')[0],m,files('source')[2],'source'))

def test_extra_metadata_sample_rejected(tmp_path):
    m=modify_csv(tmp_path,files('source')[1],lambda r:r.append(['NOT_IN_MATRIX','tumor','P888','X']))
    expect_error('SAMPLE_SET_MISMATCH',lambda:parse_cohort(files('source')[0],m,files('source')[2],'source'))

def test_bad_numeric_rejected(tmp_path):
    m=modify_csv(tmp_path,files('source')[0],lambda r:r[1].__setitem__(1,'missing'))
    expect_error('INVALID_NUMERIC_VALUE',lambda:parse_cohort(m,*files('source')[1:],'source'))

@pytest.mark.parametrize('bad',['','NaN','inf','-Infinity'])
def test_nonfinite_rejected(tmp_path,bad):
    m=modify_csv(tmp_path,files('source')[0],lambda r:r[1].__setitem__(1,bad))
    expect_error('INVALID_NUMERIC_VALUE',lambda:parse_cohort(m,*files('source')[1:],'source'))

def test_wrong_orientation_rejected(tmp_path):
    m=modify_csv(tmp_path,files('source')[0],lambda r:r[0].__setitem__(0,'sample_id'))
    expect_error('MATRIX_ORIENTATION_INVALID',lambda:parse_cohort(m,*files('source')[1:],'source'))

def test_ragged_matrix_rejected(tmp_path):
    m=modify_csv(tmp_path,files('source')[0],lambda r:r[1].pop())
    expect_error('MATRIX_INVALID',lambda:parse_cohort(m,*files('source')[1:],'source'))

def test_manifest_unknown_field_rejected(tmp_path):
    p=modify_manifest(tmp_path,'source',lambda m:m.update(arbitrary='untrusted'))
    expect_error('MANIFEST_INVALID',lambda:parse_cohort(*files('source')[:2],p,'source'))

def test_manifest_role_rejected(tmp_path):
    expect_error('ROLE_MISMATCH',lambda:parse_cohort(*files('source'),'target'))

def test_manifest_invalid_json_rejected(tmp_path):
    p=tmp_path/'bad.json';p.write_text('{invalid')
    expect_error('MANIFEST_INVALID',lambda:parse_cohort(*files('source')[:2],p,'source'))

def test_manifest_duplicate_json_key_rejected(tmp_path):
    p=tmp_path/'bad.json';p.write_text(files('source')[2].read_text().replace('"role": "source",','"role": "source", "role": "source",'))
    expect_error('MANIFEST_INVALID',lambda:parse_cohort(*files('source')[:2],p,'source'))

def test_incompatible_measurement(tmp_path):
    m=modify_manifest(tmp_path,'target',lambda x:x.update(measurement_type='rnaseq_vst'))
    a=cohorts()[0];b=parse_cohort(*files('target')[:2],m,'target')
    assert 'MEASUREMENT_INCOMPATIBLE' in {i.code for i in evaluate_compatibility(a,b,'diagnose_shift',scientific_role='unlabeled_shift_only').issues}

def test_unknown_measurement(tmp_path):
    m=modify_manifest(tmp_path,'target',lambda x:x.update(measurement_type='unknown'))
    a=cohorts()[0];b=parse_cohort(*files('target')[:2],m,'target')
    assert not evaluate_compatibility(a,b,'diagnose_shift',scientific_role='unlabeled_shift_only').eligible

def test_microarray_platform_mismatch_blocks(tmp_path):
    m=modify_manifest(tmp_path,'target',lambda x:x.update(platform='GPL999'))
    a=cohorts()[0];b=parse_cohort(*files('target')[:2],m,'target')
    assert 'PLATFORM_DIFFERENCE' in {i.code for i in evaluate_compatibility(a,b,'train_validate').issues}

def test_processing_difference_warns(tmp_path):
    m=modify_manifest(tmp_path,'target',lambda x:x.update(processing_description='Other normalization'))
    b=parse_cohort(*files('target')[:2],m,'target')
    p=evaluate_compatibility(cohorts()[0],b,'diagnose_shift',scientific_role='unlabeled_shift_only')
    assert p.eligible and 'PROCESSING_DIFFERENCE' in {i.code for i in p.issues}

def test_no_shared_features(tmp_path):
    m=modify_csv(tmp_path,files('target')[0],lambda rows:[r.__setitem__(0,'NO_OVERLAP:'+r[0]) for r in rows[1:]])
    b=parse_cohort(m,*files('target')[1:],'target');p=evaluate_compatibility(cohorts()[0],b,'diagnose_shift',scientific_role='unlabeled_shift_only')
    assert 'NO_SHARED_FEATURES' in {i.code for i in p.issues} and not p.eligible

def test_low_shared_feature_warning(tmp_path):
    m=modify_csv(tmp_path,files('target')[0],lambda rows:[r.__setitem__(0,'UNIQUE:'+r[0]) for r in rows[2:]])
    b=parse_cohort(m,*files('target')[1:],'target');p=evaluate_compatibility(cohorts()[0],b,'diagnose_shift',scientific_role='unlabeled_shift_only')
    assert p.eligible and 'LOW_FEATURE_OVERLAP' in {i.code for i in p.issues}

def test_patient_overlap_blocks_locked(tmp_path):
    def duplicate_patient(rows): rows[1][2]='SOURCEPAT0'
    m=modify_csv(tmp_path,files('target')[1],duplicate_patient)
    sm=modify_manifest(tmp_path,'source',lambda d:d.update(independence_declaration='independent_documented'))
    tm=modify_manifest(tmp_path,'target',lambda d:d.update(independence_declaration='independent_documented'))
    a=parse_cohort(*files('source')[:2],sm,'source');b=parse_cohort(files('target')[0],m,tm,'target')
    p=evaluate_compatibility(a,b,'train_validate',scientific_role='external_locked')
    assert 'PATIENT_OVERLAP' in {i.code for i in p.issues} and not p.eligible

def test_unknown_independence_blocks_locked():
    p=evaluate_compatibility(*cohorts(),'train_validate',scientific_role='external_locked')
    assert not p.eligible and 'TARGET_INDEPENDENCE_UNKNOWN' in {i.code for i in p.issues}

def test_label_outside_classes_blocks(tmp_path):
    m=modify_csv(tmp_path,files('target')[1],lambda rows:rows[2].__setitem__(1,'healthy'))
    b=parse_cohort(files('target')[0],m,files('target')[2],'target')
    p=evaluate_compatibility(cohorts()[0],b,'train_validate')
    assert not p.eligible and 'LABEL_MAPPING_INCONSISTENT' in {i.code for i in p.issues}

def test_source_class_under_five_blocks(tmp_path):
    def change(rows):
        for row in rows[1:8]:row[1]='tumor'
    m=modify_csv(tmp_path,files('source')[1],change)
    a=parse_cohort(files('source')[0],m,files('source')[2],'source')
    p=evaluate_compatibility(a,cohorts()[1],'train_validate')
    assert 'SOURCE_CV_UNSUPPORTED' in {i.code for i in p.issues} and not p.eligible

def test_absent_target_class_warns(tmp_path):
    m=modify_csv(tmp_path,files('target')[1],lambda rows:[r.__setitem__(1,'normal') for r in rows[1:]])
    b=parse_cohort(files('target')[0],m,files('target')[2],'target')
    p=evaluate_compatibility(cohorts()[0],b,'train_validate')
    assert 'LIMITED_CLASS_SUPPORT' in {i.code for i in p.issues}

def test_class_study_confounding_warns(tmp_path):
    def change(rows):
        for row in rows[1:]:row[3]='NORMAL_STUDY' if row[1]=='normal' else 'TUMOR_STUDY'
    m=modify_csv(tmp_path,files('source')[1],change)
    a=parse_cohort(files('source')[0],m,files('source')[2],'source')
    p=evaluate_compatibility(a,cohorts()[1],'train_validate')
    assert 'CLASS_STUDY_CONFOUNDING' in {i.code for i in p.issues}

def test_repeated_patient_warns(tmp_path):
    m=modify_csv(tmp_path,files('source')[1],lambda rows:rows[2].__setitem__(2,rows[1][2]))
    a=parse_cohort(files('source')[0],m,files('source')[2],'source')
    p=evaluate_compatibility(a,cohorts()[1],'train_validate')
    assert 'REPEATED_PATIENT_IDS' in {i.code for i in p.issues}

def test_very_high_values_warn(tmp_path):
    m=modify_csv(tmp_path,files('source')[0],lambda rows:[row.__setitem__(1,'2500') for row in rows[1:]])
    a=parse_cohort(m,*files('source')[1:],'source')
    assert 'SCALE_SUSPICIOUS' in {i.code for i in a.warnings}

def test_output_html_escapes_metadata(tmp_path):
    # A malicious-looking cohort label must be treated as text, not markup.
    m=modify_manifest(tmp_path,'source',lambda d:d.update(cohort_id='<script>alert(1)</script>'))
    a=parse_cohort(*files('source')[:2],m,'source')
    p=evaluate_compatibility(a,cohorts()[1],'train_validate')
    generate_report(p,tmp_path/'report')
    html=(tmp_path/'report'/'compatibility_report.html').read_text()
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html

def test_cli_blocked_run_and_no_stale_aligned_files(tmp_path):
    args=(*files('source'),*files('target'))
    rep,exitcode=execute('train_validate',*args,tmp_path,export_aligned=True)
    assert exitcode==0 and (tmp_path/'aligned_feature_ids.csv').exists()
    m=modify_csv(tmp_path,files('source')[0],lambda rows:rows[1].__setitem__(1,'bad'),name='broken.csv')
    rep,exitcode=execute('train_validate',m,*files('source')[1:],*files('target'),tmp_path)
    assert exitcode==2 and rep['verdict']=='blocked'
    assert not (tmp_path/'aligned_feature_ids.csv').exists()
    assert rep['issues'][0]['code']=='INVALID_NUMERIC_VALUE'

def test_cli_from_subprocess(tmp_path):
    args=[sys.executable,'-m','brace_core.cli','--mode','diagnose_shift',
          '--source-expression',str(files('source')[0]),'--source-metadata',str(files('source')[1]),'--source-manifest',str(files('source')[2]),
          '--target-expression',str(files('target')[0]),'--target-metadata',str(files('target')[1]),'--target-manifest',str(files('target')[2]),'--out',str(tmp_path)]
    r=subprocess.run(args,capture_output=True,text=True,cwd=EX.parents[1])
    assert r.returncode==0 and 'compatible_with_caveats' in r.stdout
    assert (tmp_path/'compatibility_report.json').exists()


def test_mode_c_excludes_outcome_label_counts(tmp_path):
    a,b=cohorts()
    p=evaluate_compatibility(a,b,'diagnose_shift',scientific_role='unlabeled_shift_only')
    d=p.to_dict()
    assert 'observed_conditions' not in d['source']
    assert 'observed_conditions' not in d['target']
    assert not any(i['code']=='CLASS_STUDY_CONFOUNDING' for i in d['issues'])

def test_manifest_enum_wrong_type_returns_structured_error(tmp_path):
    p=modify_manifest(tmp_path,'source',lambda d:d.update(measurement_type=['microarray_log2_normalized']))
    expect_error('MANIFEST_INVALID',lambda:parse_cohort(*files('source')[:2],p,'source'))
