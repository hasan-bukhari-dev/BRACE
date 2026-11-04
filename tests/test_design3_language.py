"""Requested copy coverage gate, without replacing scientific vocabulary."""
import csv,hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ui_audit',ROOT/'tools/audit_ui_strings.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
def test_source_ledger_has_full_current_inventory_and_required_columns():
    with (ROOT/'docs/quality/UI_STRING_LEDGER.csv').open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f);assert reader.fieldnames==audit.FIELDS;actual=list(reader)
    expected,coverage=audit.inventory();assert actual==expected
    assert json.loads((ROOT/'docs/quality/STRING_SOURCE_COVERAGE.json').read_text())==coverage
    assert all(all(r.get(k) for k in audit.FIELDS) for r in actual)
    assert sum(r['semantic_category']=='generated_value_policy' for r in actual)==8
def test_every_language_lint_flag_has_an_exact_context_review():
    rows,_=audit.inventory();flags=audit.findings(rows)
    reviews=json.loads((ROOT/'docs/quality/UI_LANGUAGE_REVIEW.json').read_text())
    keys={(r['source_file'],r['literal_sha256']) for r in reviews}
    assert keys=={(f['source'].split(':')[0],hashlib.sha256(f['literal_or_template'].encode()).hexdigest()) for f in flags}
    assert all(r['decision']=='keep_with_context' and len(r['reason'])>30 for r in reviews)
def test_nested_javascript_template_labels_are_not_lost():
    result=audit.js_literals('const x=`Result ${ok ? `Count ${n}` : "Unavailable"}`; const error="Retry files";')
    values=[v for _,v,_ in result]
    assert 'Unavailable' in values and 'Retry files' in values and 'Count ${n}' in values
    assert any(v.startswith('Result ${') for v in values)
    regex=audit.js_literals('const x=value.replace(/[&<>"\']/g, c=>"escaped"); const y="Undefined";')
    assert [v for _,v,_ in regex]==['escaped','Undefined']
def test_scientific_engine_source_bytes_are_unchanged():
    hashes=json.loads((ROOT/'docs/quality/BASELINE_CODE_SHA256.json').read_text())
    for name,sha in hashes.items():
        if name.startswith('brace_core/'):assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
