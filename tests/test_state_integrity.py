"""Execute the actual browser state module with Node and a minimal event/storage host."""
import shutil
import subprocess
from pathlib import Path

import pytest


def test_reopen_never_borrows_draft_or_previous_cohort_identity(tmp_path):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required to execute the browser state module')
    source = Path(__file__).resolve().parents[1] / 'brace_app/static/js/state.js'
    script = tmp_path / 'state-integrity.mjs'
    script.write_text('''
import fs from 'node:fs';
import assert from 'node:assert/strict';
globalThis.sessionStorage={getItem(){return null},setItem(){}};
globalThis.document={dispatchEvent(){}};
globalThis.CustomEvent=class{constructor(name){this.name=name}};
const source=fs.readFileSync(process.argv[2],'utf8');
const {state,activate}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
state.cohortIds={source:'draft-source',target:'draft-target'};
activate({id:'A',cohorts:{source:{cohort_id:'A-source'},target:{cohort_id:'A-target'}}});
assert.deepEqual(state.activeCohortIds,{source:'A-source',target:'A-target'});
state.cohortIds={source:'stale-source',target:'stale-target'};
activate({id:'B',mode:'race'});
assert.equal(state.activeCohortIds,null);
assert.equal(state.cohortIds,null);
activate({id:'C',mode:'evaluate_predictions'});
assert.equal(state.activeCohortIds,null);
console.log('Actual state module: identity isolation passed');
''', encoding='utf-8')
    result = subprocess.run([node, str(script), str(source)], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
