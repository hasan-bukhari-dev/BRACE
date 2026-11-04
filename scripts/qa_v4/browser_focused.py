"""Additional real-browser checks. Artificial inputs are explicitly technical fixtures."""
from pathlib import Path
import os
import ast,csv,io,json,re,time,traceback
from playwright.sync_api import sync_playwright,expect
APP=Path(os.environ.get('BRACE_QA_APP',Path(__file__).resolve().parents[2]));ROOT=APP.parent;OUT=Path(os.environ.get('BRACE_QA_OUTPUT',APP/'qa_output'))/'review';OUT.mkdir(parents=True,exist_ok=True)
receipt={'checks':[],'audits':[],'screenshots':[],'page_errors':[],'network':[]}
contrast="()=>{\n const ctx=document.createElement('canvas').getContext('2d',{willReadFrequently:true});\n function rgba(value){ctx.clearRect(0,0,1,1);ctx.fillStyle=value;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data].map((x,i)=>i===3?x/255:x)}\n function over(a,b){const t=a[3];return [0,1,2].map(i=>a[i]*t+b[i]*(1-t)).concat(1)}\n function background(el){const path=[];for(let e=el;e;e=e.parentElement)path.unshift(e);return path.reduce((v,e)=>over(rgba(getComputedStyle(e).backgroundColor),v),[255,255,255,1])}\n function luminance(a){return a.slice(0,3).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4}).reduce((t,x,i)=>t+x*[.2126,.7152,.0722][i],0)}\n function ratio(a,b){const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)}\n const data=[];for(const el of document.querySelectorAll('body *')){\n  const s=getComputedStyle(el);if(!el.getClientRects().length||s.visibility==='hidden'||el.closest('[disabled],.sr-only,script,style'))continue;\n  const direct=[...el.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim();if(!direct)continue;\n  const size=parseFloat(s.fontSize),large=size>=24||(size>=18.66&&Number(s.fontWeight)>=700),fg=rgba(el instanceof SVGElement?s.fill:s.color),bg=background(el);const value=ratio(over(fg,bg),bg);\n  data.push({text:direct.slice(0,160),tag:el.tagName,id:el.id,ratio:Math.round(value*100)/100,required:large?3:4.5,fg,bg,size});\n }\n const controls=[...document.querySelectorAll('button,input:not([type=range]):not([type=checkbox]),select')].filter(e=>e.getClientRects().length&&!e.disabled&&!e.closest('.wordmark')).map(el=>{const s=getComputedStyle(el),b=background(el.parentElement),r=ratio(over(rgba(s.borderTopColor),b),b);return {id:el.id,text:(el.textContent||'').trim().slice(0,60),ratio:Math.round(r*100)/100}});\n return {text:data,failures:data.filter(x=>x.ratio+.01<x.required),control_boundaries:controls,boundary_failures:controls.filter(x=>x.ratio<3)};\n}"
contrast=contrast.replace('bg=background(el);const value=',"bg0=background(el);let bg=bg0;if(el.classList.contains('glyph')){const p=document.querySelector('#wordmark-plate'),b=p.getBoundingClientRect(),a=el.getBoundingClientRect();if(a.left+a.width/2>=b.left&&a.left+a.width/2<=b.right)bg=over(rgba(getComputedStyle(p).backgroundColor),bg)}const value=")
def check(name,ok=True,data=None):
 assert ok,(name,data)
 receipt['checks'].append(dict(id=name,status='PASS',details=data));print('PASS',name,flush=True)
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True);ctx=browser.new_context(viewport={'width':1280,'height':720},reduced_motion='reduce',accept_downloads=True);page=ctx.new_page();page.set_default_timeout(30000);expect.set_options(timeout=30000)
 page.on('pageerror',lambda e:receipt['page_errors'].append(str(e)));page.on('request',lambda r:receipt['network'].append(r.url))
 def ready():page.wait_for_function("document.documentElement.dataset.ready==='true'")
 def nav(key):page.locator('#wordmark [data-view="'+key+'"]').click();expect(page.locator('body')).to_have_attribute('data-view',key)
 def shot(name,full=False):
  if not page.locator('dialog[open]').count():page.evaluate('scrollTo(0,0)')
  page.screenshot(path=str(OUT/(name+'.png')),full_page=full);receipt['screenshots'].append(name+'.png')
 def audit(label):
  d=page.evaluate(contrast);d['screen']=label
  # The three exact text-action patterns use words, underlines/arrows and focus;
  # their thin separators are decorative, not the sole identifying boundary.
  decorative=page.locator('.task-entry,.effect-row,.trace-thread button').evaluate_all('els=>els.map(e=>(e.textContent||"").trim().slice(0,60))')
  d['reviewed_decorative_rules']=[r for r in d['boundary_failures'] if r['text'] in decorative]
  d['boundary_failures']=[r for r in d['boundary_failures'] if r['text'] not in decorative]
  receipt['audits'].append(d)
  ids=page.locator('[id]').evaluate_all('els=>els.map(e=>e.id)');check('UNIQUE_IDS_'+label,len(ids)==len(set(ids)))
  cdp=ctx.new_cdp_session(page);nodes=cdp.send('Accessibility.getFullAXTree')['nodes'];missing=[n for n in nodes if not n.get('ignored') and n.get('role',{}).get('value') in ('button','link','combobox','textbox','slider','searchbox') and not n.get('name',{}).get('value')];check('ACCESSIBLE_NAMES_'+label,not missing,[n.get('role') for n in missing]);cdp.detach()
 def gallery(name):
  for theme in ('light','dark'):
   page.locator('#theme').select_option(theme);audit(name+'_'+theme)
   for w,h in ((1280,720),(1440,900)):
    page.set_viewport_size({'width':w,'height':h});shot(name+'_'+theme+'_'+str(w))
   page.set_viewport_size({'width':1280,'height':720})
 def choose(task):
  nav('study');page.locator('#new-data' if page.locator('#new-data').count() else '#own-data').click();page.locator('[data-start-task="'+task+'"]').click()
 def preflight():
  page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Inputs meet this task’s checks',timeout=60000)
 def compute():
  page.locator('#compute-checked').click();expect(page.locator('body')).to_have_attribute('data-view','ace',timeout=60000);expect(page.locator('#ace-confusion')).to_be_visible()
 def guided(scores=False,large=False):
  choose('evaluate_predictions');page.locator('#guided-declaration').evaluate('e=>e.open=true')
  page.locator('#declaration-dataset').fill('Artificial V4 integration fixture');page.locator('#declaration-model').fill('not documented');page.locator('#declaration-labels').fill('Artificial labels for browser verification only');page.locator('#declaration-classes').fill('healthy\nfault');page.locator('#declaration-threshold').fill('0.955')
  if scores:
   page.locator('#declaration-mapping').click();page.locator('#score-column-0').fill('prob_healthy');page.locator('#score-column-1').fill('prob_fault')
  page.locator('#use-declaration').click();expect(page.locator('#name-prediction_manifest')).to_contain_text('Created from your declared settings')
  text='sample_id,true_label,predicted_label'+(',prob_healthy,prob_fault' if scores else '')+'\n'
  if scores:
   # Exact .955 equality: one correct .955, one incorrect .99, and a withheld .8.
   text+='E1,healthy,healthy,0.955,0.045\nE2,fault,healthy,0.99,0.01\nE3,healthy,healthy,0.8,0.2\n'
   if large:text+=''.join(f'B{i},healthy,healthy,0.8,0.2\n' for i in range(1500))
  else:text+='E1,healthy,healthy\nE2,fault,healthy\nE3,fault,fault\n'
  page.locator('#file-predictions').set_input_files({'name':'artificial_v4_fixture.csv','mimeType':'text/csv','buffer':text.encode()});preflight();compute()
 try:
  page.goto(os.environ.get('BRACE_QA_URL','http://127.0.0.1:8766'));ready();gallery('home')
  page.locator('#home-genes').click();expect(page.locator('.empty-flow')).to_be_visible();gallery('race_empty');check('HOME_GENES_HAS_EXAMPLE_AND_UPLOAD_PATH')
  nav('study');page.locator('#explore-public').click();expect(page.locator('[data-effect-gene]')).to_have_count(20);gallery('race')
  page.locator('[data-effect-gene="135112"]').click();expect(page.locator('#face-body circle[data-value]')).to_have_count(188);gallery('face')
  marks=page.locator('#face-body [data-cohort]').evaluate_all('els=>Object.fromEntries(els.map(e=>[e.dataset.cohort,[...e.querySelectorAll("circle[data-sample]")].map(c=>({id:c.dataset.sample,value:Number(c.dataset.value)}))]))')
  detail=page.request.get('http://127.0.0.1:8766/api/race/studies/public_er_pass2/gene?feature_id=135112').json()
  check('ALL_188_DOTS_EQUAL_SAVED_VALUES',all(marks[k]==[{'id':s['sample_id'],'value':s['value']} for g in c['groups'] for s in g['samples']] for k,c in detail['cohorts'].items()))
  fit=page.locator('#face-inspector').evaluate('e=>({client:e.clientHeight,scroll:e.scrollHeight,trace:document.querySelector("#trace-gene").getBoundingClientRect().bottom,bottom:e.getBoundingClientRect().bottom})');check('FACE_720_BOTH_PLOTS_STATS_TRACE_FIT',fit['client']>=fit['scroll'] and fit['trace']<fit['bottom'],fit)
  for key in ('Tab','Shift+Tab'):
   for _ in range(12):page.keyboard.press(key);check('FACE_FOCUS_CONTAINED_'+key,page.evaluate('document.querySelector("#face-inspector").contains(document.activeElement)'))
  page.locator('#trace-gene').click();expect(page.locator('[data-trace-step]')).to_have_count(6);gallery('evidence')
  for i in range(6):
   page.locator('[data-trace-step="'+str(i)+'"]').click();expect(page.locator('[data-trace-step="'+str(i)+'"]')).to_have_attribute('aria-pressed','true');check('TRACE_SELECT_STEP_'+str(i),bool(page.locator('#trace-step-detail').inner_text()))
  page.locator('#return-face').click();page.keyboard.press('Escape')
  # Historical values and all 680 individual marks, independently recounted.
  nav('study');page.locator('#other-examples').evaluate('e=>e.open=true');page.locator('#historical-demo').click();expect(page.locator('[data-field-id]')).to_have_count(680)
  for t,n,c in [('0',680,668),('0.95',584,583),('0.99',432,431),('1',0,0)]:
   page.locator('#confidence-number').fill(t);page.locator('#confidence-number').press('Tab');expect(page.locator('#confidence-results')).to_contain_text(str(n)+' of 680');data=page.locator('[data-field-id]').evaluate_all('els=>({retained:els.filter(e=>e.dataset.retained==="true").length,correct:els.filter(e=>e.dataset.retained==="true"&&e.dataset.correct==="true").length})');check('ALL_680_MARK_RETENTION_'+t,data=={'retained':n,'correct':c},data)
  page.locator('#confidence-number').fill('0.99');page.locator('#confidence-number').press('Tab');gallery('ace')
  page.locator('#inspect-score-error').click();expect(page.locator('#sample-detail')).to_contain_text('0.998692106');expect(page.locator('#sample-title')).to_contain_text('cfc121b5');gallery('incorrect_record');page.keyboard.press('Escape')
  # Guided declaration produces the unchanged API contract from real form inputs.
  guided();expect(page.locator('#confidence-results')).to_contain_text('unavailable');check('CLASS_ONLY_NOT_FALSE_WITHHELD',page.locator('[data-retained="unavailable"]').count()==3 and page.locator('.prediction-mark.withheld').count()==0);gallery('class_only')
  guided(True);expect(page.locator('#confidence-results')).to_contain_text('1 correct among 2 retained');check('GUIDED_DECLARATION_EXACT_0955_EQUALITY',page.locator('[data-retained="true"]').count()==2);gallery('guided_scores_result')
  guided(True,True);expect(page.locator('.score-bins>div')).to_have_count(10);check('LARGE_FIELD_ACTUAL_BIN_COUNTS','1501 records' in page.locator('.score-bins').inner_text() and '2 of 1503' in page.locator('#confidence-results').inner_text());shot('large_fixture_real_bins',True)
  # Use a real saved unlabeled run from the broad browser test.
  runs=page.request.get('http://127.0.0.1:8766/api/runs').json()['runs'];rid=next(r['id'] for r in runs if r['mode']=='diagnose_shift' and r['has_result'])
  nav('evidence');page.locator('#run-history').evaluate('e=>e.open=true');page.locator('#history-search').fill(rid);check('HISTORY_SEARCH_ACTUAL_RUN',page.locator('[data-open-run]:visible').count()==1);page.locator('[data-open-run="'+rid+'"]').click();nav('cohorts');page.locator('#show-shift').click();expect(page.locator('#shift-content svg')).to_be_visible();page.locator('#projection-mode').click();gallery('ce_projection')
  page.locator('#feature-mode').click();gallery('ce_features');page.locator('#shift-q').select_option('0.05');data=page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');return {ids:state.data.shift.gene_shifts.filter(g=>g.ks_bh_q_exploratory!=null&&g.ks_bh_q_exploratory<=.05).map(g=>g.feature_id),table:[...document.querySelectorAll('#gene-table [data-gene]')].map(e=>e.dataset.gene)}}");check('CE_Q_FILTER_FROM_SAVED_FAMILY',data['table']==data['ids'][:20],{'matched':len(data['ids'])});shot('ce_q_filtered',True)
  page.locator('#shift-q').select_option('');page.locator('#gene-table [data-gene]').first.click();gallery('ce_feature_inspector');page.keyboard.press('Escape')
  choose('evaluate_predictions');gallery('ce_input');page.locator('#guided-declaration').evaluate('e=>e.open=true');shot('guided_declaration',True)
  # Browser-held request interruption: no automatic duplicate computation after reload.
  folder=APP/'examples/design3_prediction_fixtures/equipment_faults';page.locator('#file-predictions').set_input_files(str(folder/'predictions.csv'));page.locator('#file-prediction_manifest').set_input_files(str(folder/'manifest.json'));preflight()
  with page.expect_download() as dl:page.locator('#download-checks').click()
  target=OUT/'actual_input_check_report.json';dl.value.save_as(str(target));report=json.loads(target.read_text(encoding='utf-8'));check('DOWNLOAD_CHECKS_REAL_BACKEND_RECEIPT',report['eligible'] and report['preview']['prediction_rows']==6 and report['task']=='evaluate_predictions')
  held=[];page.route('**/api/analyze',lambda r:held.append(r));page.locator('#compute-checked').click();expect(page.locator('#status-live')).to_have_attribute('data-state','running');shot('controlled_waiting');page.reload();ready();expect(page.locator('#status-live')).to_contain_text('outcome is not confirmed');check('INTERRUPTION_NO_FALSE_SUCCESS_NO_AUTO_RESUBMIT',len(held)==1);shot('controlled_interruption')
  for route in held:
   try:route.abort()
   except Exception:pass
  page.wait_for_timeout(100);page.unroute_all(behavior='ignoreErrors')
  check('NO_PAGE_ERRORS',not receipt['page_errors'],receipt['page_errors']);check('ALL_RUNTIME_REQUESTS_LOCAL',not [url for url in receipt['network'] if not url.startswith('http://127.0.0.1:8766/')])
  failures=[{'screen':a['screen'],'text':a['failures'],'controls':a['boundary_failures']} for a in receipt['audits'] if a['failures'] or a['boundary_failures']];receipt['contrast_findings']=failures;receipt['status']='PASS' if not failures else 'CONTRAST_REPAIR_REQUIRED';print('CONTRAST FINDINGS',json.dumps(failures),flush=True)
 except Exception as exc:
  receipt['status']='FAIL';receipt['failure']=str(exc);receipt['traceback']=traceback.format_exc();shot('failure');raise
 finally:
  page.unroute_all(behavior='ignoreErrors');(OUT/'focused_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');browser.close()
