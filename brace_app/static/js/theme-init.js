/* Runs before styles: a stored preference never flashes the opposite theme. */
(()=>{
 let preference='system';try{const saved=localStorage.getItem('brace.theme');if(['light','dark','system'].includes(saved))preference=saved}catch{}
 document.documentElement.dataset.themePreference=preference;
 document.documentElement.dataset.theme=preference==='system'?(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):preference;
})();
