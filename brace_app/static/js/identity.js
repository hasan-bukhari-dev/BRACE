// Product vocabulary is separate from frozen scientific method identifiers.
export const identities = Object.freeze({
 BRACE:'Biological Reliability Assessment across Cohorts and Experiments',
 RACE:'Replication Assessment of Cohort Effects',
 ACE:'Algorithmic Classifier Evaluation',
 CE:'Cohort Evaluation',
 EMBRACE:'Evidence Management, Bundling, Reproducibility, Audit & Controlled Exports',
 SPACE:'Study Provenance, Acquisition & Cohort Exploration',
 FACE:'Feature Analysis of Cohort Expression',
 TRACE:'Transparent Record of Analysis, Computation & Evidence'
});
export function describeIdentity(element, name) {
 if (identities[name]) element.title = `${name} — ${identities[name]}`;
}
export function evaluationTitle(count, sourceFitted=false) {
 return sourceFitted ? `Evaluate source-trained baseline on ${count.toLocaleString()} target samples` : `Evaluate ${count.toLocaleString()} saved predictions`;
}
export function initIdentity() {
 const navNames=['BRACE','RACE','ACE','CE','EMBRACE'];
 document.querySelectorAll('#wordmark [data-view]').forEach((el,i)=>describeIdentity(el,navNames[i]));
 const glossary=document.createElement('details');
 glossary.id='product-identities';
 const summary=document.createElement('summary');summary.textContent='BRACE tool names';glossary.append(summary);
 const list=document.createElement('dl');
 for(const [name,meaning] of Object.entries(identities)) {
  const term=document.createElement('dt'),definition=document.createElement('dd');
  term.textContent=name;definition.textContent=meaning;list.append(term,definition);
 }
 glossary.append(list);document.querySelector('#help-dialog').append(glossary);
}
