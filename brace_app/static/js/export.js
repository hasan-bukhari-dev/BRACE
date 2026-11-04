import {esc} from './ui.js';
let exporting=false;
export function initExports(){
 document.addEventListener('click',async event=>{
  const link=event.target.closest('a[href]');if(!link)return;
  const url=new URL(link.href,location.href);if(url.origin!==location.origin||!/^\/api\/embrace\/[^/]+$/.test(url.pathname))return;
  event.preventDefault();if(exporting)return;exporting=true;link.setAttribute('aria-disabled','true');
  let host=link.parentElement.parentElement.querySelector('.embrace-export-status');
  if(!host){host=document.createElement('div');host.className='embrace-export-status';host.setAttribute('aria-live','polite');link.parentElement.after(host)}
  host.setAttribute('role','status');host.textContent='Checking and preparing the evidence ZIP…';
  try{
   const response=await fetch(url.pathname,{credentials:'same-origin'});
   if(!response.ok){let message='Export request failed ('+response.status+').';try{const body=await response.json();message=body.detail?.message||body.detail||message}catch{}throw new Error(String(message))}
   if(!response.headers.get('content-type')?.includes('application/zip'))throw new Error('The server did not return an evidence ZIP. Retry after checking the saved run.');
   const blob=await response.blob(),signature=new Uint8Array(await blob.slice(0,4).arrayBuffer());
   if(signature[0]!==80||signature[1]!==75)throw new Error('The evidence download is not a valid ZIP response. Retry the export.');
   const objectURL=URL.createObjectURL(blob),download=document.createElement('a');download.href=objectURL;download.download='BRACE_EMBRACE_'+url.pathname.split('/').at(-1)+'.zip';download.hidden=true;document.body.append(download);download.click();download.remove();setTimeout(()=>URL.revokeObjectURL(objectURL),1000);
   if(host.isConnected)host.textContent='Evidence ZIP prepared; download started. Derived identifiers and scores are included. Raw uploads are excluded; review the package before sharing.';
  }catch(error){if(host.isConnected){host.setAttribute('role','alert');host.innerHTML=`<p>${esc(error.message)}</p><button type="button">Retry evidence export</button>`;host.querySelector('button').onclick=()=>link.click()}}
  finally{exporting=false;link.removeAttribute('aria-disabled')}
 });
}
