export function initTheme(){
 const root=document.documentElement,select=document.querySelector('#theme'),system=matchMedia('(prefers-color-scheme: dark)');
 select.value=root.dataset.themePreference||'system';
 function apply(){const preference=select.value;root.dataset.themePreference=preference;root.dataset.theme=preference==='system'?(system.matches?'dark':'light'):preference;try{localStorage.setItem('brace.theme',preference)}catch{}document.dispatchEvent(new CustomEvent('brace:theme'))}
 select.addEventListener('change',apply);system.addEventListener('change',()=>{if(select.value==='system')apply()});
}
