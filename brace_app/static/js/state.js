const key='brace.workspace.v3';
let saved={};try{saved=JSON.parse(sessionStorage.getItem(key)||'{}')}catch{}
export const state={view:'study',mode:'race',data:null,historical:null,shiftPreview:null,filter:'errors',query:'',threshold:null,currentPage:0,geneQuery:'',shiftPage:0,shiftFeature:null,raceQuery:'',raceSort:'rank',raceFilter:'all',selectedGene:null,selectedSample:null,inspector:null,ceTab:'inputs',busy:false,status:'ready',runUI:{},...saved};
state.data=null;state.busy=false;
export const files=new Map();
const keys=['filter','query','threshold','currentPage','geneQuery','shiftPage','shiftFeature','raceQuery','raceSort','raceFilter','selectedGene','selectedSample','traceGene','ceTab','matrixFilter','distributionMode','shiftQMax'];
function remember(){if(state.data?.id){state.runUI[state.data.id]=Object.fromEntries(keys.map(k=>[k,state[k]]));const ids=Object.keys(state.runUI);if(ids.length>20)delete state.runUI[ids[0]]}}
export function save(){try{remember();const {data,historical,shiftPreview,busy,...small}=state;sessionStorage.setItem(key,JSON.stringify({...small,runId:data?.id||state.runId||null,interrupted:busy}))}catch{}}
export function activate(data){document.dispatchEvent(new CustomEvent('brace:before-context'));remember();const previous=state.data?.id;state.data=data;state.runId=data.id;state.activeCohortIds=data.cohorts?{source:data.cohorts.source.cohort_id,target:data.cohorts.target.cohort_id}:data.mode==='evaluate_predictions'||data.kind==='historical'?null:state.cohortIds||null;state.status='ready';
 if(previous!==data.id){Object.assign(state,{matrixFilter:null,distributionMode:'projection',shiftQMax:null,threshold:data.validation?.threshold??null,selectedGene:null,traceGene:null,raceFilter:'all',raceQuery:'',raceSort:'rank',selectedSample:null,filter:'errors',query:'',currentPage:0,geneQuery:'',shiftPage:0,shiftFeature:null},state.runUI[data.id]||{})}
 state.faceOpen=false;state.inspector=null;save();
}
