"""Execute the actual browser state module with Node and a minimal event/storage host."""
import shutil
import subprocess
from pathlib import Path

import pytest


def test_setup_remains_in_selected_tool_and_fixtures_are_explicit(tmp_path):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required for UI routing checks')
    source = Path(__file__).resolve().parents[1] / 'brace_app/static/js/ui.js'
    script = tmp_path / 'setup-routing.mjs'
    script.write_text('''
import fs from 'node:fs';import assert from 'node:assert/strict';
const {setupView,isSoftwareFixture}=await import('data:text/javascript;base64,'+Buffer.from(fs.readFileSync(process.argv[2],'utf8')).toString('base64'));
assert.equal(setupView('evaluate_predictions'),'ace');assert.equal(setupView('train_validate'),'ace');
assert.equal(setupView('race'),'race');assert.equal(setupView('diagnose_shift'),'cohorts');
assert.equal(isSoftwareFixture({kind:'synthetic'}),true);
assert.equal(isSoftwareFixture({source:{type:'synthetic_example'}}),true);
assert.equal(isSoftwareFixture({name:'ARTIFICIAL software QA - boundary'}),true);
assert.equal(!!isSoftwareFixture({kind:'historical',name:'CancerShift archive'}),false);
assert.equal(!!isSoftwareFixture({name:'Artificial intelligence classifier',source:{type:'imported_file'}}),false);
''', encoding='utf-8')
    result = subprocess.run([node, str(script), str(source)], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr


def test_external_run_link_never_leaves_old_result_under_new_url(tmp_path):
    node=shutil.which('node')
    if not node:pytest.skip('Node is required to execute the browser navigation module')
    source=Path(__file__).resolve().parents[1]/'brace_app/static/js/journey.js'
    script=tmp_path/'journey-integrity.mjs'
    script.write_text('''
import fs from 'node:fs';
import assert from 'node:assert/strict';
const events={};let reloads=0,pushes=0;
globalThis.testState={view:'race',data:{id:'old-run'},entry:false,runUI:{}};
globalThis.window={addEventListener(name,fn){events[name]=fn}};
globalThis.location={hash:'#race?run=old-run',href:'http://localhost/#race?run=old-run',reload(){reloads++}};
globalThis.history={state:null,replaceState(s,title,url){this.state=s;if(url?.startsWith('#'))location.hash=url},pushState(s,title,url){pushes++;this.state=s;if(url?.startsWith('#'))location.hash=url}};
const backButton={};globalThis.document={querySelector(){return backButton},getElementById(){return {}},addEventListener(){}};
globalThis.MutationObserver=class{observe(){}};
globalThis.scrollY=0;globalThis.requestAnimationFrame=fn=>fn();globalThis.scrollTo=()=>{};
let code=fs.readFileSync(process.argv[2],'utf8').replace("import {state,save} from './state.js';","const state=globalThis.testState;const save=()=>{};");
const {initJourney,recordJourney}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
let release;initJourney(()=>new Promise(resolve=>{release=resolve}));
assert.equal(backButton.disabled,false);assert.match(backButton.textContent,/Workbench/);testState.faceOpen=true;testState.selectedGene='2099';recordJourney();testState.faceOpen=false;recordJourney();assert.equal(pushes,0,'inspectors must not add a close/reopen Back loop');events.hashchange();assert.equal(reloads,0);
location.hash='#ace?run=new-run';history.state=null;events.hashchange();assert.equal(reloads,1);
// A normal Back/Forward restore keeps the existing in-memory input files.
const restoring=events.popstate({state:{brace:{view:'ace',runId:'new-run'},braceIndex:1}});
events.hashchange();assert.equal(reloads,1);release();await restoring;
console.log('Actual navigation module: external run link and history isolation passed');
''',encoding='utf-8')
    result=subprocess.run([node,str(script),str(source)],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr


def test_operation_receipt_distinguishes_training_evaluation_and_replay(tmp_path):
    node=shutil.which('node')
    if not node:pytest.skip('Node is required to execute the operation module')
    source=Path(__file__).resolve().parents[1]/'brace_app/static/js/operation.js'
    script=tmp_path/'operation-integrity.mjs'
    script.write_text('''
import fs from 'node:fs';import assert from 'node:assert/strict';
globalThis.testState={view:'ace',entry:false,operationExpanded:false};
let code=fs.readFileSync(process.argv[2],'utf8').replace("import {state} from './state.js';","const state=globalThis.testState;").replace("import {esc} from './ui.js';","const esc=String;");
const {operationSummary}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const host={firstElementChild:{}};
testState.data={id:'evaluation',validation:{},mode:'evaluate_predictions'};operationSummary(host);assert.match(host.innerHTML,/Saved prediction evaluation/);
testState.data={id:'training',validation:{},mode:'train_validate'};operationSummary(host);assert.match(host.innerHTML,/Source-trained expression baseline/);
testState.data={id:'replay',validation:{},replay:{},mode:'replay_frozen'};operationSummary(host);assert.match(host.innerHTML,/Frozen baseline application/);assert.doesNotMatch(host.innerHTML,/Saved prediction evaluation/);
testState.data={id:'race',race:{}};operationSummary(host);assert.match(host.innerHTML,/Saved prediction evaluation/);assert.doesNotMatch(host.innerHTML,/RACE/);
testState.view='cohorts';testState.ceTab='inputs';operationSummary(host);assert.match(host.innerHTML,/Dataset checks/);assert.doesNotMatch(host.innerHTML,/Gene-association testing/);
testState.ceTab='shift';operationSummary(host);assert.match(host.innerHTML,/Distribution comparison/);
testState.view='evidence';testState.data=null;operationSummary(host);assert.match(host.innerHTML,/EMBRACE/);
testState.view='cohorts';testState.entry=true;testState.mode='train_validate';operationSummary(host);assert.match(host.innerHTML,/Source-trained expression baseline/);
console.log('Actual operation module: three scientific operations remain distinct');
''',encoding='utf-8')
    result=subprocess.run([node,str(script),str(source)],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr


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


def test_saved_dataset_study_retains_its_task_kind(tmp_path):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required to execute the dataset module')
    source = Path(__file__).resolve().parents[1] / 'brace_app/static/js/datasets.js'
    script = tmp_path / 'dataset-task-integrity.mjs'
    script.write_text('''
import fs from 'node:fs';import assert from 'node:assert/strict';
let code=fs.readFileSync(process.argv[2],'utf8')
 .replace('import { $, esc, isSoftwareFixture } from "./ui.js";', 'const $=()=>{},esc=String,isSoftwareFixture=()=>false;')
 .replace('import { request } from "./api.js";', 'const request=()=>{};');
const {taskForStudy}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const predictions={datasets:{predictions:'saved-prediction-version'}};
for(const task of ['race','diagnose_shift','train_validate','evaluate_predictions'])
 assert.equal(taskForStudy(predictions,task),'evaluate_predictions');
const expression={datasets:{source:'source-version',target:'target-version'}};
for(const task of ['race','diagnose_shift','train_validate'])assert.equal(taskForStudy(expression,task),task);
assert.equal(taskForStudy(expression,'evaluate_predictions'),'race');
''', encoding='utf-8')
    result = subprocess.run([node, str(script), str(source)], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
