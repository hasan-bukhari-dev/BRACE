export const $=s=>document.querySelector(s);
export const esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const fmt=(v,d=2)=>v===null||v===undefined||!Number.isFinite(Number(v))?'Undefined':Number(v).toFixed(d);
export const pct=(v,d=2)=>v===null||v===undefined||!Number.isFinite(Number(v))?'Undefined':(Number(v)*100).toFixed(d)+'%';
