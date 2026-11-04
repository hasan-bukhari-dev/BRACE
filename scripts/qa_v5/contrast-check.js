()=>{
 const ctx=document.createElement('canvas').getContext('2d',{willReadFrequently:true});
 function rgba(value){ctx.clearRect(0,0,1,1);ctx.fillStyle=value;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data].map((x,i)=>i===3?x/255:x)}
 function over(a,b){const t=a[3];return [0,1,2].map(i=>a[i]*t+b[i]*(1-t)).concat(1)}
 function background(el){const path=[];for(let e=el;e;e=e.parentElement)path.unshift(e);return path.reduce((v,e)=>over(rgba(getComputedStyle(e).backgroundColor),v),[255,255,255,1])}
 function luminance(a){return a.slice(0,3).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4}).reduce((t,x,i)=>t+x*[.2126,.7152,.0722][i],0)}
 function ratio(a,b){const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)}
 const data=[];for(const el of document.querySelectorAll('body *')){
  const s=getComputedStyle(el);if(!el.getClientRects().length||s.visibility==='hidden'||el.closest('[disabled],.sr-only,script,style'))continue;
  const direct=[...el.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim();if(!direct)continue;
  const size=parseFloat(s.fontSize),large=size>=24||(size>=18.66&&Number(s.fontWeight)>=700),fg=rgba(el instanceof SVGElement?s.fill:s.color),bg=background(el);const value=ratio(over(fg,bg),bg);
  data.push({text:direct.slice(0,160),tag:el.tagName,id:el.id,ratio:Math.round(value*100)/100,required:large?3:4.5,fg,bg,size});
 }
 const controls=[...document.querySelectorAll('button,input:not([type=range]):not([type=checkbox]),select')].filter(e=>e.getClientRects().length&&!e.disabled&&!e.closest('.wordmark')).map(el=>{const s=getComputedStyle(el),b=background(el.parentElement),r=ratio(over(rgba(s.borderTopColor),b),b);return {id:el.id,text:(el.textContent||'').trim().slice(0,60),ratio:Math.round(r*100)/100}});
 return {text:data,failures:data.filter(x=>x.ratio+.01<x.required),control_boundaries:controls,boundary_failures:controls.filter(x=>x.ratio<3)};
}