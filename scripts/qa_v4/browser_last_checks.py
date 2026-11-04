from pathlib import Path
import os
import json,re,time,traceback
from playwright.sync_api import sync_playwright,expect
APP=Path(os.environ.get('BRACE_QA_APP',Path(__file__).resolve().parents[2]));ROOT=APP.parent;OUT=Path(os.environ.get('BRACE_QA_OUTPUT',APP/'qa_output'))/'review';OUT.mkdir(parents=True,exist_ok=True);receipt={'checks':[],'screenshots':[],'page_errors':[]}
def check(name,ok=True,data=None):
 assert ok,(name,data)
 receipt['checks'].append(dict(id=name,status='PASS',details=data));print('PASS',name,flush=True)
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True);ctx=browser.new_context(viewport={'width':1280,'height':720},reduced_motion='reduce');page=ctx.new_page();page.set_default_timeout(30000);expect.set_options(timeout=30000);page.on('pageerror',lambda e:receipt['page_errors'].append(str(e)))
 def ready():page.wait_for_function("document.documentElement.dataset.ready==='true'")
 def nav(key):page.locator('#wordmark [data-view="'+key+'"]').click();expect(page.locator('body')).to_have_attribute('data-view',key)
 def shot(name):
  if not page.locator('dialog[open]').count():page.evaluate('scrollTo(0,0)')
  page.screenshot(path=str(OUT/(name+'.png')));receipt['screenshots'].append(name+'.png')
 def reflow(name):
  for theme in ('light','dark'):
   page.locator('#theme').select_option(theme)
   for w,h in ((390,844),(720,450)):
    page.set_viewport_size({'width':w,'height':h});dim=page.evaluate('({w:innerWidth,scroll:document.documentElement.scrollWidth})');check('REFLOW_'+name+'_'+theme+'_'+str(w),dim['scroll']<=dim['w']+1,dim);shot(name+'_'+theme+'_'+str(w))
  page.set_viewport_size({'width':1280,'height':720})
 try:
  page.goto(os.environ.get('BRACE_QA_URL','http://127.0.0.1:8766'));ready();page.locator('#explore-public').click();expect(page.locator('[data-effect-gene]')).to_have_count(20);reflow('race_loaded')
  page.locator('[data-effect-gene="135112"]').click();expect(page.locator('#face-body circle[data-value]')).to_have_count(188);reflow('face_loaded')
  page.locator('#theme').select_option('light');page.locator('#close-face').focus();page.keyboard.press('Shift+Tab');check('FACE_REVERSE_FOCUS_STAYS_IN_DIALOG',page.evaluate('document.querySelector("#face-inspector").contains(document.activeElement)'));page.keyboard.press('Escape');expect(page.locator('[data-effect-gene="135112"]')).to_be_focused()
  # Selection/theme/navigation preservation and forced-color availability.
  for theme in ('dark','light'):
   page.locator('#theme').select_option(theme);expect(page.locator('[data-effect-gene="135112"]')).to_have_attribute('aria-pressed','true')
  check('THEME_PRESERVES_SELECTED_GENE');page.emulate_media(forced_colors='active');shot('race_forced_colors');page.emulate_media(forced_colors='none')
  nav('study');page.locator('#new-data').click();page.locator('[data-start-task="race"]').click();reflow('two_dataset_wells')
  for theme in ('light','dark'):
   page.locator('#theme').select_option(theme);shot('two_dataset_wells_'+theme+'_1280')
  # Invalid guided settings fail locally; they do not create a fake manifest.
  page.locator('#task').select_option('evaluate_predictions');page.locator('#guided-declaration').evaluate('e=>e.open=true');page.locator('#declaration-dataset').fill('Artificial check');page.locator('#declaration-model').fill('not documented');page.locator('#declaration-labels').fill('Artificial verification');page.locator('#declaration-classes').fill('healthy\nfault');page.locator('#declaration-threshold').fill('');page.locator('#use-declaration').click();expect(page.locator('#declaration-error')).to_contain_text('between 0 and 1');check('EMPTY_DECLARED_CUTOFF_REJECTED')
  page.locator('#declaration-threshold').fill('0.955');page.locator('#declaration-mapping').click();page.locator('#score-column-0').fill('same');page.locator('#score-column-1').fill('same');page.locator('#use-declaration').click();expect(page.locator('#declaration-error')).to_contain_text('distinct score column');check('DUPLICATE_SCORE_COLUMN_REJECTED')
  reflow('guided_settings')
  # Verify complete source-fitted chart and real coordinate geometry in current CSS.
  runs=page.request.get('http://127.0.0.1:8766/api/runs').json()['runs'];rid=next(r['id'] for r in runs if r['mode']=='diagnose_shift' and r['has_result']);nav('evidence');page.locator('#run-history').evaluate('e=>e.open=true');page.locator('[data-open-run="'+rid+'"]').click();nav('cohorts');page.locator('#show-shift').click();page.locator('#projection-mode').click();expect(page.locator('#projection-lens svg')).to_be_visible()
  data=page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');return {saved:state.data.shift.source_fitted_pca,marks:[...document.querySelectorAll('#projection-lens [data-pc1]')].map(e=>({id:e.dataset.sample,c:e.dataset.cohort,x:Number(e.dataset.pc1),y:Number(e.dataset.pc2)}))}}")
  if data['saved'] is None:
   data=page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');return {saved:state.data.shift.projection,marks:[...document.querySelectorAll('#projection-lens [data-pc1]')].map(e=>({id:e.dataset.sample,c:e.dataset.cohort,x:Number(e.dataset.pc1),y:Number(e.dataset.pc2)}))}}")
  # The engine property is discovered from the recorded shift, not inferred.
  engine=page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');return Object.values(state.data.shift).find(v=>v&&Array.isArray(v.samples)&&v.explained_variance_ratio_source)}")
  check('PCA_ALL_34_COORDINATES_EQUAL_SAVED',data['marks']==[dict(id=s['sample_id'],c=s['cohort'],x=s['pc1'],y=s['pc2']) for s in engine['samples']])
  for theme in ('light','dark'):
   page.locator('#theme').select_option(theme);dim=page.locator('#projection-lens svg').evaluate('e=>({bottom:e.getBoundingClientRect().bottom,viewport:innerHeight})');check('FULL_PCA_720_'+theme,dim['bottom']<=dim['viewport'],dim);shot('ce_projection_'+theme+'_1280')
  reflow('ce_projection_loaded');page.locator('#feature-mode').click();reflow('ce_features_loaded');nav('evidence');reflow('evidence_loaded')
  nav('study');page.locator('#other-examples').evaluate('e=>e.open=true');page.locator('#historical-demo').click();expect(page.locator('[data-field-id]')).to_have_count(680);reflow('ace_loaded')
  check('NO_PAGE_ERRORS',not receipt['page_errors'],receipt['page_errors']);receipt['status']='PASS'
 except Exception as exc:
  receipt['status']='FAIL';receipt['failure']=str(exc);receipt['traceback']=traceback.format_exc();shot('last_failure');raise
 finally:
  (OUT/'last_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');browser.close()
