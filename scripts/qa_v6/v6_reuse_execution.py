from pathlib import Path
import json
from playwright.sync_api import sync_playwright,expect
O=Path(__file__).resolve().parents[2]/Path('docs/v6/reuse_execution');O.mkdir(exist_ok=True);checks=[];errors=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);pg=b.new_page(viewport={'width':1280,'height':720},reduced_motion='reduce');expect.set_options(timeout=45000);pg.on('pageerror',lambda e:errors.append(str(e)))
 def check(name,ok=True):assert ok,name;checks.append(name)
 def nav(view):pg.locator('#wordmark [data-view="'+view+'"]').click()
 try:
  pg.goto('http://127.0.0.1:8787');pg.wait_for_function("document.documentElement.dataset.ready==='true'");pg.locator('#explore-public').click();expect(pg.locator('[data-signature-gene]')).to_have_count(20);nav('cohorts');pg.locator('#reuse-baseline').click();expect(pg.locator('#data-entry')).to_have_attribute('data-step','3');expect(pg.locator('#status-live')).to_have_attribute('data-state','ready');pg.locator('#setup-next').click();pg.locator('#setup-next').click();expect(pg.locator('.check-blocked')).to_be_visible();check('public_ER_baseline_explicitly_blocked');pg.screenshot(path=str(O/'baseline_blocked.png'))
  nav('study');pg.locator('#study-results').click();expect(pg.locator('[data-signature-gene]')).to_have_count(20);nav('cohorts');pg.locator('#reuse-shift').click();expect(pg.locator('#data-entry')).to_have_attribute('data-step','1');check('selected_public_files_retained',pg.evaluate("async()=>{const {files}=await import('/assets/js/state.js');return files.has('source_expression')&&files.has('target_expression')&&files.has('source_manifest')&&files.has('target_manifest')}"));pg.locator('#setup-next').click();expect(pg.locator('#source-cohort-name')).to_have_value('GSE42568_ER');check('public_JSON_visibly_hydrates_guided_form');pg.locator('#setup-next').click();pg.locator('#setup-next').click();pg.locator('#setup-next').click();expect(pg.locator('.check-ready')).to_be_visible();check('same_ER_inputs_eligible_for_distribution_checks')
  # Hold the real computation request, navigate, then release it to the actual backend.
  pending=[];pg.route('**/api/analyze',lambda r:pending.append(r));pg.locator('#setup-next').click();expect(pg.locator('#status-live')).to_have_attribute('data-state','running')
  for _ in range(100):
   if pending:break
   pg.wait_for_timeout(20)
  assert len(pending)==1
  nav('evidence');response=pending[0].fetch();pending[0].fulfill(response=response);expect(pg.locator('#status-live')).to_have_attribute('data-state','new_result');expect(pg.locator('body')).to_have_attribute('data-view','evidence');check('completion_preserves_view_after_navigating_away');pg.locator('#status-live button').click();expect(pg.locator('#projection-chart .scatterlayer')).to_be_visible();check('newly_saved_result_opens_on_explicit_action');pg.unroute('**/api/analyze')
  check('no_page_errors',not errors);(O/'receipt.json').write_text(json.dumps({'status':'PASS','checks':checks,'errors':errors,'note':'Computation request timing controlled in browser; released to actual backend without mocked result.'},indent=2))
 except Exception:
  pg.screenshot(path=str(O/'failure.png'));raise
 finally:b.close()
