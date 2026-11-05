export const $=s=>document.querySelector(s);
export const esc=v=>String(v??'â€”').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const fmt=(v,d=2)=>v===null||v===undefined||!Number.isFinite(Number(v))?'Undefined':Number(v).toFixed(d);
export const pct=(v,d=2)=>v===null||v===undefined||!Number.isFinite(Number(v))?'Undefined':(Number(v)*100).toFixed(d)+'%';

export const isSoftwareFixture=r=>r.kind==='synthetic'||r.source?.type==='synthetic_example'||r.name?.startsWith('ARTIFICIAL software QA');

export const setupView=mode=>({race:"race",evaluate_predictions:"ace",train_validate:"ace",diagnose_shift:"cohorts"}[mode]||"cohorts");
