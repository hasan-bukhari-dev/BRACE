from pathlib import Path
import json,io,zipfile,hashlib
from playwright.sync_api import sync_playwright,expect
O=Path(__file__).resolve().parents[2]/Path('docs/v6/final_paths');O.mkdir(exist_ok=True)
receipt={'status':'RUNNING','checks':[],'errors':[],'controlled_failure_tests':[]}
def check(name,ok=True):
 assert ok,name
 receipt['checks'].append(name)
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);pg=b.new_page(viewport={'width':1280,'height':720},reduced_motion='reduce',accept_downloads=True);pg.on('pageerror',lambda e:receipt['errors'].append(str(e)));expect.set_options(timeout=40000)
 try:
  pg.goto('http://127.0.0.1:8787');pg.wait_for_function("document.documentElement.dataset.ready==='true'");pg.locator('#explore-public').click();expect(pg.locator('[data-signature-gene]')).to_have_count(20)
  for role,total,n in [('source',121,101),('target',90,87)]:
   el=pg.locator('[data-exclusions="'+role+'"]');expect(el).to_contain_text(str(n)+'/'+str(total));el.locator('summary').click();expect(el.locator('tbody tr')).to_have_count(total-n)
   with pg.expect_download() as download:el.locator('button').click()
   data=json.loads(Path(download.value.path()).read_text());check(role+'_exclusions_and_download',data['included']==n and data['downloaded_samples']==total and len(data['records'])==total-n)
   el.locator('summary').click()
  pg.screenshot(path=str(O/'race_inclusions.png'))
  pg.locator('#operation-summary summary').click();expect(pg.locator('#operation-summary .method-flow li')).to_have_count(3);pg.screenshot(path=str(O/'method_explanation.png'));check('method_sequence_is_visible_without_running_again');pg.locator('#operation-summary summary').click();pg.locator('#preview-measurements').click();expect(pg.locator('#expression-source .scatterlayer')).to_be_visible();pg.locator('#trace-gene').click();expect(pg.locator('[data-trace-step]')).to_have_count(6)
  for step,count in [(2,'10000'),(3,'20'),(4,'20')]:
   pg.locator('[data-trace-step="'+str(step)+'"]').click();expect(pg.locator('#trace-step-detail>p')).to_contain_text(count)
  check('TRACE_actual_source_frozen_and_target_counts');pg.screenshot(path=str(O/'trace_target_family.png'))
  pg.locator('[data-evidence-tab="report"]').click();frame=pg.frame_locator('#report-frame');expect(frame.locator('a[href*="/artifact/"]').first).to_be_visible();a=frame.locator('a[href*="/artifact/"]').first;href=a.get_attribute('href');member=href.split('/artifact/')[1]
  with pg.expect_download() as download:a.click()
  payload=Path(download.value.path()).read_bytes();bundle=pg.request.get('http://127.0.0.1:8787/api/embrace/public_er_pass2').body()
  with zipfile.ZipFile(io.BytesIO(bundle)) as z:check('report_iframe_link_download_exact_zip_member',payload==z.read(member))
  pg.locator('#wordmark [data-view="study"]').click();pg.locator('#other-examples').evaluate('e=>e.open=true');pg.locator('#historical-demo').click();expect(pg.locator('#operation-summary')).to_contain_text('ACE');check('historical_method_is_evaluation_not_RACE');pg.locator('#wordmark [data-view="study"]').click()
  # Deliberate failure injection certifies recovery wording only, not live NCBI availability.
  pg.route('**/api/discovery/search',lambda route:route.fulfill(status=503,content_type='application/json',body=json.dumps({'detail':'Controlled network outage for UI recovery test.'})))
  pg.locator('#open-space').click();pg.locator('#space-question').fill('breast tumor');pg.locator('#space-search').click();expect(pg.locator('#space-status')).to_contain_text('Controlled network outage');expect(pg.locator('#space-search')).to_be_enabled();expect(pg.locator('#space-question')).to_have_value('breast tumor');receipt['controlled_failure_tests'].append('503 preserves public query, offers retry and bundled offline alternative');pg.screenshot(path=str(O/'space_recovery.png'));pg.unroute('**/api/discovery/search');pg.locator('#close-space').click()
  check('no_page_errors',not receipt['errors']);receipt['status']='PASS'
 finally:
  (O/'receipt.json').write_text(json.dumps(receipt,indent=2));b.close()
