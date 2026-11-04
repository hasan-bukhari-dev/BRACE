"""True Chrome page zoom, using only an isolated test profile's zoom preference."""
from pathlib import Path
import os
import json,math,time,traceback,base64
from playwright.sync_api import sync_playwright,expect
APP=Path(os.environ.get('BRACE_QA_APP',Path(__file__).resolve().parents[2]));OUT=Path(os.environ.get('BRACE_QA_OUTPUT',APP/'qa_output'))/'review';OUT.mkdir(parents=True,exist_ok=True);profile=OUT/'isolated_zoom_profile/Default';profile.mkdir(parents=True,exist_ok=True)
(profile/'Preferences').write_text(json.dumps({'partition':{'default_zoom_level':{'x':math.log(2)/math.log(1.2)}}}),encoding='utf-8')
receipt={'checks':[],'screenshots':[],'page_errors':[],'method':'Chrome native default page zoom in isolated profile; not CSS zoom, device emulation or pinch zoom. Chromium ChromeZoomLevelPrefs storage-partition dictionary x.','capture':'Direct Chrome Page.captureScreenshot, fromSurface=true, captureBeyondViewport=false. Playwright default clip mis-scales native-zoom screenshots; discarded those captures after visual inspection.', 'method_source':'https://raw.githubusercontent.com/chromium/chromium/main/chrome/browser/ui/zoom/chrome_zoom_level_prefs.cc'}
def check(name,ok=True,data=None):
 assert ok,(name,data)
 receipt['checks'].append(dict(id=name,status='PASS',details=data));print('PASS',name,flush=True)
with sync_playwright() as p:
 ctx=p.chromium.launch_persistent_context(str(profile.parent),channel='chrome',headless=True,no_viewport=True,reduced_motion='reduce',args=['--window-size=1440,1000']);page=ctx.pages[0];page.set_default_timeout(30000);expect.set_options(timeout=30000);page.on('pageerror',lambda e:receipt['page_errors'].append(str(e)))
 def nav(k):page.locator('#wordmark [data-view="'+k+'"]').click();expect(page.locator('body')).to_have_attribute('data-view',k)
 def screen(name):
  for theme in ('light','dark'):
   page.locator('#theme').select_option(theme)
   if not page.locator('dialog[open]').count():page.evaluate('scrollTo(0,0)')
   sizes=page.evaluate('({width:innerWidth,outer:outerWidth,scroll:document.documentElement.scrollWidth,dpr:devicePixelRatio,pinch:visualViewport.scale})');check(name+'_'+theme+'_NATIVE_200_PERCENT',sizes['dpr']==2 and sizes['pinch']==1 and sizes['width']<sizes['outer']*.51 and sizes['scroll']<=sizes['width']+1,sizes)
   filename=name+'_native200_'+theme+'.png';cdp=ctx.new_cdp_session(page);capture=cdp.send('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False,'fromSurface':True});(OUT/filename).write_bytes(base64.b64decode(capture['data']));cdp.detach();receipt['screenshots'].append(filename)
 try:
  page.goto(os.environ.get('BRACE_QA_URL','http://127.0.0.1:8766'));page.wait_for_function("document.documentElement.dataset.ready==='true'");screen('home')
  page.locator('#explore-public').click();expect(page.locator('[data-effect-gene]')).to_have_count(20);screen('race')
  page.locator('[data-effect-gene="135112"]').click();expect(page.locator('#face-body circle[data-value]')).to_have_count(188);screen('face');geometry=page.locator('#face-inspector').evaluate('e=>{const r=e.getBoundingClientRect();return {top:r.top,bottom:r.bottom,height:innerHeight,hit:e.contains(document.elementFromPoint(r.left+30,r.top+30))}}');check('ZOOM_DIALOG_ACTUALLY_IN_VIEW_AND_HIT_TESTS',geometry['hit'] and geometry['top']>=0 and geometry['bottom']<=geometry['height'],geometry);page.locator('#trace-gene').click();expect(page.locator('[data-trace-step]')).to_have_count(6);screen('evidence')
  nav('study');page.locator('#other-examples').evaluate('e=>e.open=true');page.locator('#historical-demo').click();expect(page.locator('[data-field-id]')).to_have_count(680);screen('ace')
  nav('study');page.locator('#new-data').click();page.locator('[data-start-task="evaluate_predictions"]').click();screen('input')
  page.locator('#task').select_option('race');screen('two_dataset_input')
  runs=page.request.get('http://127.0.0.1:8766/api/runs').json()['runs'];rid=next(r['id'] for r in runs if r['mode']=='diagnose_shift' and r['has_result']);nav('evidence');page.locator('#run-history').evaluate('e=>e.open=true');page.locator('[data-open-run="'+rid+'"]').click();nav('cohorts');page.locator('#show-shift').click();page.locator('#projection-mode').click();screen('ce');page.locator('#feature-mode').click();screen('ce_features')
  check('NO_PAGE_ERRORS',not receipt['page_errors'],receipt['page_errors']);receipt['status']='PASS'
 except Exception as e:receipt['status']='FAIL';receipt['failure']=str(e);receipt['traceback']=traceback.format_exc();raise
 finally:(OUT/'native_zoom_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');ctx.close()
