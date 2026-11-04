from pathlib import Path
import ast,json,traceback
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2];APP=ROOT;OUT=APP/'docs/v6/screens';OUT.mkdir(exist_ok=True)
contrast=(Path(__file__).resolve().parent/'contrast-check.js').read_text(encoding='utf-8')
receipt={'screens':[],'checks':[],'errors':[]}
def check(name,ok,details=None):
 assert ok,(name,details)
 receipt['checks'].append({'id':name,'status':'PASS','details':details})
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);ctx=b.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce');page=ctx.new_page();page.set_default_timeout(30000);expect.set_options(timeout=30000);page.on('pageerror',lambda e:receipt['errors'].append(str(e)))
 def nav(v):page.locator('#wordmark [data-view="'+v+'"]').click()
 def screen(name):
  modal=bool(page.locator('dialog[open]').count())
  if not modal:page.evaluate('scrollTo(0,0)')
  for w,h in [(1440,900),(1280,720),(390,844)]:
   page.set_viewport_size({'width':w,'height':h})
   for theme in ['light','dark']:
    # Header is inert while a modal is open: choose theme through the actual module, not force-click.
    if modal:page.evaluate("t=>{document.querySelector('#theme').value=t;document.querySelector('#theme').dispatchEvent(new Event('change'))}",theme)
    else:page.locator('#theme').select_option(theme)
    page.mouse.move(2,2);page.wait_for_timeout(140);f=f'{name}_{w}_{theme}.png';page.screenshot(path=str(OUT/f));sizes=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth,over:[...document.querySelectorAll("body *")].filter(e=>{const r=e.getBoundingClientRect();return r.right>innerWidth&&r.width>0&&getComputedStyle(e).display!=="none"}).slice(0,12).map(e=>({tag:e.tagName,id:e.id,cls:String(e.className),width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right}))})');check(f+'_NO_PAGE_OVERFLOW',sizes['scroll']<=sizes['width']+1,sizes);audit=page.evaluate(contrast);receipt['screens'].append({'file':f,'state':name,'viewport':[w,h],'theme':theme,'audit':audit})
  page.set_viewport_size({'width':1440,'height':900})
 try:
  page.goto('http://127.0.0.1:8787');page.wait_for_function("document.documentElement.dataset.ready==='true'");screen('home')
  nav('race');screen('race_empty');page.locator('#wordmark [data-view="study"]').focus();page.keyboard.press('ArrowRight');check('NAV_ARROW_ROVING_FOCUS',page.locator('#wordmark [data-view="race"]').evaluate('e=>e===document.activeElement'));page.keyboard.press('Enter');check('NAV_ENTER_COMMITS',page.locator('body').get_attribute('data-view')=='race')
  nav('study');page.locator('#explore-public').click();expect(page.locator('#paired-effect-chart .scatterlayer')).to_be_visible();screen('race');page.locator('#preview-measurements').click();expect(page.locator('#expression-source .scatterlayer')).to_be_visible();screen('face');page.keyboard.press('Escape');nav('evidence');expect(page.locator('#report-frame')).to_be_visible();screen('evidence');page.locator('[data-evidence-tab="calculation"]').click();expect(page.locator('[data-trace-step]')).to_have_count(6);screen('trace');nav('study');screen('workbench')
  page.locator('#other-examples').evaluate('e=>e.open=true');page.locator('#historical-demo').click();expect(page.locator('#confidence-chart .scatterlayer')).to_be_visible();screen('ace');page.locator('#overview-error').click();screen('record');page.keyboard.press('Escape');nav('study');page.locator('#other-examples').evaluate('e=>e.open=true');page.locator('#synthetic-demo').click();expect(page.locator('#confidence-chart .scatterlayer')).to_be_visible(timeout=60000);check('BASELINE_SOURCE_CV_SEPARATE', '13 / 20' in page.locator('.source-role-note').inner_text() and '11 / 14' in page.locator('.source-role-note').inner_text());screen('baseline')
  runs=page.request.get('http://127.0.0.1:8787/api/runs').json()['runs'];rid=next(r['id'] for r in runs if r['mode']=='diagnose_shift' and r['has_result']);nav('evidence');page.locator('#run-history').evaluate('e=>e.open=true');page.locator('[data-open-run="'+rid+'"]').click();expect(page.locator('#projection-chart .scatterlayer')).to_be_visible();screen('projection');page.locator('#feature-mode').click();screen('features');page.locator('#gene-table [data-gene]').first.click();screen('feature_inspector');page.keyboard.press('Escape')
  nav('study');page.locator('#new-data').click();page.locator('[data-start-task="race"]').click();screen('setup');page.locator('#load-public-inputs').click();expect(page.locator('#data-entry')).to_have_attribute('data-step','3');expect(page.locator('#status-live')).to_have_attribute('data-state','ready');screen('contrast');page.locator('#setup-back').click();screen('descriptions');page.locator('#open-help').click();screen('guide');page.keyboard.press('Escape')
  # Forced-colour and reduced-motion are real browser media emulations.
  ctx2=b.new_context(viewport={'width':1280,'height':720},reduced_motion='reduce',forced_colors='active');pg=ctx2.new_page();pg.goto('http://127.0.0.1:8787');pg.wait_for_function("document.documentElement.dataset.ready==='true'");check('FORCED_COLOURS_ACTIVE',pg.evaluate("matchMedia('(forced-colors: active)').matches"));pg.screenshot(path=str(OUT/'home_forced_colours.png'));check('REDUCED_MOTION_ACTIVE',pg.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches"));ctx2.close()
  check('NO_PAGE_ERRORS',not receipt['errors'],receipt['errors']);receipt['status']='PASS'
 except Exception as e:receipt['status']='FAIL';receipt['failure']=str(e);receipt['traceback']=traceback.format_exc();page.screenshot(path=str(OUT/'failure.png'));raise
 finally:(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2));b.close()
