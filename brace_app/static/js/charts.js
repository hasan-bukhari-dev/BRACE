import {esc} from './ui.js';
const observed=new WeakSet();
export const ink=name=>getComputedStyle(document.documentElement).getPropertyValue('--'+name).trim();
export async function draw(host,data,layout={}){
 if(!host||!host.isConnected)return;
 if(!window.Plotly){host.innerHTML='<p role="alert">The local chart library could not load. Exact values remain in the tables. Refresh BRACE to retry.</p>';return}
 const base={paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',font:{family:'Manrope, Segoe UI, sans-serif',size:11,color:ink('muted')},margin:{l:52,r:20,t:18,b:48},hoverlabel:{font:{family:'Manrope, Segoe UI, sans-serif',size:12},bgcolor:ink('surface'),font_color:ink('text'),bordercolor:ink('line')},showlegend:false,dragmode:'zoom',uirevision:host.id,autosize:true};
 const axis={gridcolor:ink('plot-grid'),zerolinecolor:ink('control-line'),linecolor:ink('control-line'),automargin:true,tickfont:{size:10},title:{font:{size:11}},fixedrange:false};
 await Plotly.react(host,data,{...base,...layout,xaxis:{...axis,...layout.xaxis},yaxis:{...axis,...layout.yaxis}},{responsive:true,displaylogo:false,displayModeBar:'hover',scrollZoom:false,modeBarButtonsToRemove:['select2d','lasso2d','autoScale2d'],toImageButtonOptions:{format:'png',filename:'BRACE_'+(host.id||'chart'),scale:2}});
 if(!observed.has(host)){observed.add(host);const ro=new ResizeObserver(()=>{if(host.isConnected&&host.clientWidth)Plotly.Plots.resize(host)});ro.observe(host);host._braceObserver=ro}
}
document.addEventListener('brace:theme',()=>{
 document.querySelectorAll('.js-plotly-plot').forEach(host=>{if(!host.isConnected)return;const redraw=host._braceRedraw;if(redraw)redraw();else Plotly.relayout(host,{'font.color':ink('muted'),'xaxis.gridcolor':ink('plot-grid'),'yaxis.gridcolor':ink('plot-grid'),'xaxis.linecolor':ink('control-line'),'yaxis.linecolor':ink('control-line'),'yaxis.zerolinecolor':ink('control-line')})});
});
export function effectsChart(host,gene){
 const render=()=>{const ys=[gene.source_hedges_g,gene.hedges_g],valid=ys.filter(v=>v!=null),lo=Math.min(0,...valid),hi=Math.max(0,...valid),pad=Math.max(.2,(hi-lo)*.18);draw(host,[{type:'scatter',mode:'markers+text',x:[0,1],y:ys,text:ys.map(v=>v==null?'':v.toFixed(3)),textposition:'top center',textfont:{size:13,color:ink('text')},marker:{size:13,color:[ink('source'),ink('target')],symbol:['circle','square'],line:{color:ink('surface'),width:2}},customdata:['Source','Target'],hovertemplate:'%{customdata}<br>Hedges’ g %{y:.4f}<extra></extra>'}],{height:240,xaxis:{range:[-.5,1.5],tickvals:[0,1],ticktext:['Source','Target'],showgrid:false},yaxis:{range:[lo-pad,hi+pad],title:{text:'Hedges’ g',font:{size:11}},zeroline:true,zerolinewidth:1},shapes:[{type:'line',x0:-.5,x1:1.5,y0:0,y1:0,line:{color:ink('control-line'),width:1,dash:'dot'}}]})};host._braceRedraw=render;render();
}
export function expressionChart(host,cohort){
 const render=()=>{
  const traces=[];
  cohort.groups.forEach((group,j)=>{
   const color=ink(j?'positive':'negative'),samples=group.samples;
   traces.push({type:'box',name:group.condition,x:samples.map(()=>j),y:samples.map(s=>s.value),boxpoints:false,width:.3,fillcolor:color+'25',line:{color,width:1.5},quartilemethod:'linear',hoverinfo:'skip',showlegend:false});
   traces.push({type:'scatter',mode:'markers',name:group.condition,x:samples.map((s,i)=>j+((i*7)%19-9)*.013),y:samples.map(s=>s.value),customdata:samples.map(s=>s.sample_id),marker:{size:5,color,opacity:.72},hovertemplate:'%{customdata}<br>'+esc(group.condition)+'<br>Expression %{y:.6f}<extra></extra>'});
  });
  draw(host,traces,{height:240,margin:{l:46,r:10,t:10,b:50},xaxis:{range:[-.5,1.5],tickvals:[0,1],ticktext:cohort.groups.map(g=>g.condition.replaceAll('_',' ')+'<br>(n='+g.observed_n+')'),showgrid:false},yaxis:{title:{text:'Normalized log intensity',font:{size:10}},zeroline:false}});
 };host._braceRedraw=render;render();
}
export function confidenceChart(host,v,selected,onSelect){
 const render=()=>{const points=v.threshold_curve.filter(p=>p.selective_accuracy!=null);draw(host,[{type:'scatter',mode:'lines+markers',x:points.map(p=>p.coverage),y:points.map(p=>p.selective_accuracy),customdata:points.map(p=>[p.threshold,p.retained,p.correct]),line:{color:ink('brand-2'),width:2.5},marker:{size:4,color:ink('brand-2')},hovertemplate:'Cutoff %{customdata[0]}<br>%{customdata[1]} retained · %{customdata[2]} correct<br>Coverage %{x:.1%} · accuracy %{y:.1%}<extra></extra>'},...(selected?.selective_accuracy==null?[]:[{type:'scatter',mode:'markers',x:[selected.coverage],y:[selected.selective_accuracy],marker:{size:12,color:ink('target'),line:{color:ink('text'),width:1.5}},hoverinfo:'skip'}])],{height:225,margin:{l:49,r:15,t:18,b:45},xaxis:{range:[0,1],tickformat:'.0%',title:{text:'Coverage · retained / all',font:{size:11}}},yaxis:{range:[0,1.03],tickformat:'.0%',title:{text:'Accuracy among retained',font:{size:10}}}}).then(()=>{host.removeAllListeners?.('plotly_click');host.on('plotly_click',e=>{const t=e.points[0]?.customdata?.[0];if(t!=null)onSelect(t)})})};host._braceRedraw=render;render();
}
export function projectionChart(host,pca){
 const render=()=>{const data=['source','target'].map((role,i)=>{const points=pca.samples.filter(p=>p.cohort===role);return {type:'scatter',mode:'markers',name:role==='source'?'Source':'Target',x:points.map(p=>p.pc1),y:points.map(p=>p.pc2),customdata:points.map(p=>p.sample_id),marker:{color:ink(role),size:i?8:7,symbol:i?'square':'circle',opacity:.8},hovertemplate:'%{customdata}<br>PC1 %{x:.5f}<br>PC2 %{y:.5f}<extra>'+role+'</extra>'}});draw(host,data,{height:350,showlegend:true,legend:{orientation:'h',x:0,y:1.15,font:{size:11}},margin:{l:58,r:25,t:30,b:50},xaxis:{title:{text:'Source PC1 · '+(pca.explained_variance_ratio_source[0]*100).toFixed(1)+'% variance',font:{size:11}}},yaxis:{title:{text:'Source PC2 · '+(pca.explained_variance_ratio_source[1]*100).toFixed(1)+'% variance',font:{size:11}}}})};host._braceRedraw=render;render();
}
