import {state,save} from './state.js';
const fields=['view','mode','entry','setupStep','ceTab','selectedGene','selectedSample','faceOpen','inspector','threshold','filter','query','currentPage','raceQuery','raceSort','raceFilter','geneQuery','shiftPage','shiftFeature','matrixFilter','distributionMode','shiftQMax','traceStep','evidenceTab'];
let active=false,restoring=false,restore,token=0;
function snapshot(){return {...Object.fromEntries(fields.map(k=>[k,state[k]??null])),runId:state.data?.id||null,scroll:scrollY}}
function key(s){return JSON.stringify([s.view,s.runId,s.entry,s.entry?s.setupStep:null,s.ceTab,s.faceOpen,s.faceOpen?s.selectedGene:null,s.inspector,s.evidenceTab])}
function url(s){const q=new URLSearchParams();if(s.runId)q.set('run',s.runId);if(s.entry){q.set('task',s.mode);q.set('step',s.setupStep||1)}if(s.faceOpen&&s.selectedGene)q.set('gene',s.selectedGene);if(s.inspector?.kind==='sample')q.set('record',s.selectedSample);return '#'+s.view+(q.size?'?'+q:'')}
export function routeFromHash(){const [view,query='']=location.hash.slice(1).split('?');const q=new URLSearchParams(query);return {view:view||'study',runId:q.get('run'),mode:q.get('task'),setupStep:Number(q.get('step'))||1,selectedGene:q.get('gene'),selectedSample:q.get('record')}}
export function recordJourney(){if(!active||restoring)return;const s=snapshot();if(key(s)!==key(history.state?.brace||{}))history.pushState({brace:s,braceIndex:(history.state?.braceIndex||0)+1},'',url(s));else history.replaceState({...history.state,brace:s},'',url(s));document.querySelector('#journey-back').disabled=!(history.state?.braceIndex>0)}
export function initJourney(fn){restore=fn;active=true;document.querySelector('#journey-back').disabled=true;history.scrollRestoration='manual';history.replaceState({brace:snapshot(),braceIndex:0},'',url(snapshot()));
 document.addEventListener('click',()=>{if(!restoring)history.replaceState({...history.state,brace:snapshot()},'',location.href)},true);
 document.addEventListener('click',()=>queueMicrotask(recordJourney));document.addEventListener('brace:step',()=>queueMicrotask(recordJourney));
 document.addEventListener('input',()=>queueMicrotask(()=>{if(active&&!restoring)history.replaceState({...history.state,brace:snapshot()},'',location.href)}));
 document.addEventListener('brace:before-context',()=>{if(active&&!restoring)history.replaceState({...history.state,brace:snapshot()},'',location.href)});
 const mo=new MutationObserver(()=>queueMicrotask(recordJourney));for(const id of ['face-inspector','sample-dialog'])mo.observe(document.getElementById(id),{attributes:true,attributeFilter:['open']});
 // A pasted/bookmarked hash has no BRACE history snapshot. Reload through the
 // checked startup resolver instead of leaving a previous run under a new URL.
 window.addEventListener('hashchange',()=>{if(!restoring&&location.hash!==url(snapshot()))location.reload()});
 window.addEventListener('popstate',async e=>{const n=++token,s=e.state?.brace;if(!s)return;restoring=true;try{await restore(s,()=>n===token);document.querySelector('#journey-back').disabled=!(e.state?.braceIndex>0);if(n===token){save();requestAnimationFrame(()=>scrollTo(0,s.scroll||0))}}finally{if(n===token)restoring=false}});
}
