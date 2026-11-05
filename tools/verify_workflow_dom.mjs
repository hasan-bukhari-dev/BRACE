import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const {JSDOM}=await import(pathToFileURL(path.join(root,'work/dom-test/node_modules/jsdom/lib/api.js')).href);
const runtime=path.join(root,'work/dom-test/runtime');await fs.mkdir(runtime,{recursive:true});
await fs.writeFile(path.join(runtime,'package.json'),JSON.stringify({type:'module'}));
for(const name of ['datasets.js','preparation.js','workspace-tools.js','ui.js'])await fs.copyFile(path.join(root,'brace_app/static/js',name),path.join(runtime,name));
await fs.writeFile(path.join(runtime,'api.js'),'export const request=(...args)=>globalThis.mockRequest(...args);');
const dom=new JSDOM('<main><section id="workspace-datasets"></section></main>',{url:'http://localhost:8901'});
for(const key of ['window','document','localStorage','Event','CustomEvent','FormData','File','SubmitEvent'])globalThis[key]=dom.window[key];
globalThis.CSS={escape:s=>s};dom.window.HTMLElement.prototype.scrollIntoView=function(){};
const a='a'.repeat(32),b='b'.repeat(32),c='c'.repeat(32),p='d'.repeat(32);
const records=[{id:a,name:'Source original-role cohort',status:'prepared',source:{type:'test'},summary:{manifest:{role:'source'}}},
 {id:b,name:'Another original-source-role cohort',status:'prepared',source:{type:'test'},summary:{manifest:{role:'source'}}},
 {id:c,name:'Unprepared public study',status:'acquired',source:{type:'geo',accession:'GSE999'}}];
const calls=[];let prepared;
globalThis.mockRequest=async(url,options={})=>{
 calls.push([url,options]);
 if(url==='/api/datasets')return {datasets:records};
 if(url==='/api/runs')return {runs:[]};if(url==='/api/studies')return {studies:[]};
 if(url.endsWith('/inspect') && url.startsWith('/api/datasets'))return {sample_ids:['S1','S2','S3'],feature_count:30000,feature_preview:['1053_at'],phenotype_fields:[{name:'er ihc',values:['1','0','NA']}],metadata:{'!Sample_organism_ch1':[['Homo sapiens','Homo sapiens','Homo sapiens']],'!Sample_platform_id':[['GPL570','GPL570','GPL570']],'!Sample_data_processing':[['RMA log2','RMA log2','RMA log2']]}};
 if(url.endsWith('/prepare')){prepared=JSON.parse(options.body);const saved={id:'e'.repeat(32),name:'Prepared cohort',status:'prepared',source:{type:'prepared'},summary:{manifest:prepared.manifest,n_samples:2,n_features:1000}};records.push(saved);return saved}
 if(url==='/api/dataset-analysis/preflight')return {eligible:true,issues:[]};
 if(url==='/api/predictions/inspect')return {headers:['case','observed','called'],count:2,values:{case:['a','b'],observed:['alpha','beta'],called:['alpha','beta']}};
 if(url==='/api/predictions/import'){records.push({id:p,name:'Mapped table',status:'prepared',source:{type:'mapped'},summary:{kind:'saved_predictions'}});return {id:p}}
 throw Error('Unexpected request '+url);
};
const {initDatasets,refreshDatasets}=await import(pathToFileURL(path.join(runtime,'datasets.js')).href);
initDatasets({message:()=>{},isBusy:()=>false,busy:()=>{},completed:()=>{}});await refreshDatasets();
const $=s=>document.querySelector(s);
$('#registry-task').value='diagnose_shift';$('#registry-task').onchange();
assert([...$('#registry-target').options].some(o=>o.value===a && !o.disabled));
assert([...$('#registry-source').options].some(o=>o.value===b && !o.disabled));
assert([...$('#registry-source').options].some(o=>o.textContent.includes('preparation required')&&o.disabled));
$('#registry-source').value=a;$('#registry-target').value=b;$('#registry-swap').onclick();
assert.equal($('#registry-source').value,b);assert.equal($('#registry-target').value,a);
$('#registry-target').value='';
document.dispatchEvent(new CustomEvent('brace:prepare-dataset',{detail:{id:c,task:'race'}}));
await new Promise(resolve=>setTimeout(resolve,25));
assert($('#guided-preparation'));$('#prep-labels').value='0';$('#prep-labels').onchange();
assert.equal(document.querySelectorAll('[data-group-class]').length,3);
document.querySelector('[data-group-class="0"]').value='positive';document.querySelector('[data-group-class="1"]').value='negative';document.querySelector('[data-group-class="2"]').value='';document.querySelector('[data-group-reason="2"]').value='Recorded ER status unavailable';
$('#prep-role').value='source';$('#prep-role').onchange();$('#prep-namespace').value='probe_id';$('#prep-scale').value='microarray_log2_normalized';$('#prep-reviewed').checked=true;
const submit=$('#guided-preparation button[type="submit"]');await $('#guided-preparation').onsubmit(new SubmitEvent('submit',{cancelable:true,submitter:submit}));
assert.deepEqual(prepared.condition_by_sample,{S1:'positive',S2:'negative'});
assert.equal(prepared.excluded_samples.S3,'Recorded ER status unavailable');
assert.equal(prepared.feature_policy,'source_variance');
const file=new File(['case,observed,called\na,alpha,alpha\nb,beta,beta'],'new.csv',{type:'text/csv'});
Object.defineProperty($('#prediction-table'),'files',{value:[file]});await $('#prediction-preview').onclick();
for(const [key,value] of Object.entries({sample_id:'case',true_label:'observed',predicted_label:'called'}))$('#map-'+key).value=value;
$('#map-observed').onclick();$('#map-model').value='External model';$('#map-label-source').value='Recorded reference labels';
const button=$('#prediction-map-form button[type="submit"]');await $('#prediction-map-form').onsubmit(new SubmitEvent('submit',{cancelable:true,submitter:button}));
assert.equal($('#registry-task').value,'evaluate_predictions');assert.equal($('#registry-source').value,p);
const ids=[...document.querySelectorAll('[id]')].map(el=>el.id);assert.equal(new Set(ids).size,ids.length);
console.log(JSON.stringify({status:'PASS',scope:'DOM handlers, not rendered browser or human acceptance',assertions:['role-independent selection','acquired-state explanation','role swap','key-aligned phenotype mapping','explicit exclusions','source-only preparation','ACE column import and selection','unique IDs']}));
