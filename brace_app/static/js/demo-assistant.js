const prompts = [
 {id:'prepare-er',featured:true,label:'Prepare GSE42568 → GSE20711',text:'Get GSE42568 ready to test ER associations against GSE20711. Use the reviewed inputs and fill in the source, target and ER group labels for me.'},
 {id:'ace-error',featured:true,label:'Find CancerShift’s most confident error',text:'Check the 680 archived CancerShift predictions and take me straight to the highest-scoring mistake. I want to inspect its true label and class scores.'},
 {id:'evidence',featured:true,label:'Get the evidence I need to share this',text:'I need to share this analysis with my team. Show me its report, input provenance and evidence downloads so they can review the work.'},
 {id:'home',label:'Back to my workspace',text:'Take me back to my BRACE workspace so I can choose what to work on next.'},
 {id:'data',label:'Start with my expression data',text:'I have processed expression files and sample labels ready. Take me to the import and analysis setup.'},
 {id:'race',label:'Check ER replication across studies',text:'Show me the recorded ER replication results for GSE42568 against GSE20711, including the genes that did not meet target support.'},
 {id:'ace',label:'Review CancerShift’s 680 predictions',text:'Pull up the evaluation of CancerShift’s 680 archived predictions. I want to compare class-level errors and see what changes when I filter by score.'},
 {id:'ce',label:'Compare GSE42568 with GSE20711',text:'Compare GSE42568 with GSE20711. Show me their expression distributions and source-fitted projection before I interpret the differences.'},
 {id:'prediction-data',label:'Evaluate my saved predictions',text:'I already have model predictions and true labels. Take me to ACE import so I can evaluate them without retraining the model.'},
 {id:'baseline',label:'Set up a source-trained baseline',text:'Help me set up ACE to fit a baseline on my source expression data and evaluate it on a separate target cohort.'},
 {id:'face',label:'See the measurements behind this gene',text:'For the gene I am inspecting, show me the source and target expression measurements behind its association.'},
 {id:'trace',label:'Trace this result back to its inputs',text:'Before I use this result, show me its recorded inputs, analysis steps and calculation artifacts.'},
 {id:'evidence',label:'Find this analysis’s report and exports',text:'Bring together the report, methods and downloadable evidence for the analysis I am reviewing.'},
 {id:'space',label:'Look for another public cohort',text:'Help me look for another public breast tumor expression study. Take me to the GEO search so I can review candidates.'}
];
export function resolveAssistantIntent(text) {
 const q=text.trim().toLowerCase();
 const exact=prompts.find(p=>p.text.toLowerCase()===q);if(exact)return exact.id;
 if(/\b(prepar\w*)\b/.test(q)&&/\b(breast|er|gse42568|gse20711)\b/.test(q))return 'prepare-er';
 if(/\b(confident|highest.score|high.score)\b/.test(q)&&/\b(error|incorrect|mistake|wrong)\b/.test(q))return 'ace-error';
 if(/\b(space|geo|find.*(data|stud)|search.*(data|stud))\b/.test(q))return 'space';
 if(/\b(baseline|train|training)\b/.test(q))return 'baseline';
 if(/\b(my|own|upload|uploaded|import)\b/.test(q))return /\b(prediction|predictions|classifier)\b/.test(q)?'prediction-data':'data';
 if(/\b(trace|calculated|calculation|how.*computed)\b/.test(q))return 'trace';
 if(/\b(face|gene measurements|inspect.*gene)\b/.test(q))return 'face';
 if(/\b(embrace|evidence|export|download)\b/.test(q))return 'evidence';
 if(/\b(ace|cancershift|prediction|predictions|classifier|errors|accuracy)\b/.test(q))return 'ace';
 if(/\b(race|replicate|replication|association|associations|er genes)\b/.test(q))return 'race';
 if(/\b(ce|compare|comparison|distribution|cohorts)\b/.test(q))return 'ce';
 if(/\b(upload|own data|my data|data setup)\b/.test(q))return 'data';
 if(/\b(home|brace|workspace)\b/.test(q))return 'home';
 return null;
}
export function initDemoAssistant({actions,isBusy}) {
 if(document.querySelector('#brace-assistant'))return;
 const shell=document.createElement('aside');shell.id='brace-assistant';shell.setAttribute('aria-label','BRACE assistant');
 shell.innerHTML=`<section id="assistant-panel" class="assistant-panel" aria-labelledby="assistant-title" hidden><header class="assistant-heading"><span class="assistant-spark" aria-hidden="true">✦</span><div><h2 id="assistant-title">Ask BRACE</h2><p>Your research workspace, one message away</p></div><button type="button" class="assistant-close" aria-label="Minimize assistant">−</button></header><div class="assistant-body"><p class="assistant-intro">What are you working on?</p><p class="assistant-hint">Start with a request below, make it your own, then send.</p><div class="assistant-prompts"></div><div class="assistant-conversation" role="log" aria-live="polite" aria-relevant="additions text"></div></div><form class="assistant-compose"><label class="sr-only" for="assistant-message">Message BRACE</label><textarea id="assistant-message" rows="2" maxlength="500" placeholder="Ask about genes, predictions or evidence…"></textarea><button type="submit" class="assistant-send" aria-label="Send message">↑</button></form><p class="assistant-disclosure">Demo assistant · preset and keyword commands · uses BRACE’s real workflows, not live RAG.</p></section><button type="button" class="assistant-launcher" aria-label="Ask BRACE" aria-expanded="false" aria-controls="assistant-panel"><span aria-hidden="true">✦</span><span class="assistant-launcher-label" aria-hidden="true">Ask BRACE</span></button>`;
 document.body.append(shell);
 // Keep the assistant interactive inside native modal dialogs as well as pages.
 const placeAssistant=()=>{const dialogs=[...document.querySelectorAll('dialog[open]')].filter(d=>d.matches(':modal'));const parent=dialogs.at(-1)||document.body;if(shell.parentElement!==parent)parent.append(shell);};
 new MutationObserver(placeAssistant).observe(document.body,{attributes:true,subtree:true,attributeFilter:['open']});
 const panel=shell.querySelector('#assistant-panel'),launcher=shell.querySelector('.assistant-launcher'),input=shell.querySelector('textarea'),form=shell.querySelector('form'),log=shell.querySelector('[role="log"]'),body=shell.querySelector('.assistant-body'),send=shell.querySelector('[type="submit"]');let pending=false;
 let dismissTimer,keyboardMode=false;
 function setOpen(open,{restoreFocus=true}={}){clearTimeout(dismissTimer);panel.hidden=!open;launcher.setAttribute('aria-expanded',String(open));if(open)input.focus();else if(restoreFocus)launcher.focus();else if(shell.contains(document.activeElement))document.activeElement.blur();}
 function scheduleDismiss(){clearTimeout(dismissTimer);if(panel.hidden||!matchMedia('(hover: hover)').matches)return;dismissTimer=setTimeout(()=>{if(!shell.matches(':hover')&&!pending&&!(keyboardMode&&shell.contains(document.activeElement)))setOpen(false,{restoreFocus:false});},900);}
 shell.addEventListener('pointerenter',()=>clearTimeout(dismissTimer));
 shell.addEventListener('pointerleave',scheduleDismiss);
 shell.addEventListener('pointerdown',()=>{keyboardMode=false;});
 shell.addEventListener('keydown',()=>{keyboardMode=true;clearTimeout(dismissTimer);});
 shell.addEventListener('focusout',scheduleDismiss);
 launcher.onclick=()=>setOpen(panel.hidden);shell.querySelector('.assistant-close').onclick=()=>setOpen(false);
 shell.addEventListener('keydown',e=>{if(e.key==='Escape'){e.stopPropagation();setOpen(false)}});
 const host=shell.querySelector('.assistant-prompts');
 let featuredEnded=false;
 const storyLabel=document.createElement('span');storyLabel.className='assistant-group-label';storyLabel.textContent='SAVE A FEW STEPS';host.append(storyLabel);
 for(const prompt of prompts){if(!prompt.featured&&!featuredEnded){featuredEnded=true;const label=document.createElement('span');label.className='assistant-group-label';label.textContent='KEEP WORKING';host.append(label);}const button=document.createElement('button');if(prompt.featured)button.className='assistant-story';button.type='button';button.textContent=prompt.label;button.title=prompt.text;button.dataset.prompt=prompt.id;button.onclick=()=>{input.value=prompt.text;input.focus();send.disabled=false;};host.append(button);}
 function append(text,kind){const p=document.createElement('p');p.className='assistant-bubble assistant-'+kind;p.textContent=text;log.append(p);while(log.children.length>16)log.firstElementChild.remove();body.scrollTop=body.scrollHeight;return p;}
 input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();form.requestSubmit();}});
 form.addEventListener('submit',async e=>{
  e.preventDefault();const text=input.value.trim();if(!text||pending)return;
  if(isBusy()){append('An analysis is running. Please wait for it to finish before switching tasks.','answer');return;}
  const intent=resolveAssistantIntent(text);append(text,'question');input.value='';
  if(!intent||!actions[intent]){append('Try a suggested prompt above, or ask for RACE, ACE, CE, FACE, TRACE, evidence, public datasets or your own data. This demo recognizes preset and keyword commands.','answer');return;}
  pending=true;send.disabled=true;input.disabled=true;host.querySelectorAll('button').forEach(b=>b.disabled=true);log.setAttribute('aria-busy','true');
  const answer=append('BRACE is typing…','answer');answer.classList.add('assistant-typing');
  try{await new Promise(resolve=>setTimeout(resolve,650));answer.classList.remove('assistant-typing');if(isBusy())throw Error('An analysis started. Wait for it to finish before switching tasks.');const result=await actions[intent]();answer.textContent=result||'Opened in the main workspace. You can keep exploring or ask another question.';}
  catch(error){answer.classList.remove('assistant-typing');answer.textContent='Could not complete that request. '+(error.message||'Please try again.');}
  finally{pending=false;send.disabled=false;input.disabled=false;host.querySelectorAll('button').forEach(b=>b.disabled=false);log.setAttribute('aria-busy','false');body.scrollTop=body.scrollHeight;if(!shell.matches(':hover'))scheduleDismiss();}
 });
}
