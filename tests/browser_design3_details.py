from pathlib import Path
import ast,json,time
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];APP=ROOT;OUT=APP/'docs/design3/final';receipt={'checks':[],'audits':[],'screenshots':[]}
tree=ast.parse((ROOT/'tests/browser_design3_accessibility.py').read_text());contrast=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CONTRAST' for t in n.targets))
# Include the actual suffix-plate sibling behind glyphs, not just ancestor fills.
contrast=contrast.replace('bg=background(el);const value=',"bg0=background(el);let bg=bg0;if(el.classList.contains('glyph')){const p=document.querySelector('#wordmark-plate'),b=p.getBoundingClientRect(),a=el.getBoundingClientRect();if(a.left+a.width/2>=b.left&&a.left+a.width/2<=b.right)bg=over(rgba(getComputedStyle(p).backgroundColor),bg)}const value=")
def check(name,condition=True,details=None):
    assert condition,(name,details)
    receipt['checks'].append(dict(id=name,status='PASS',details=details));print('PASS',name,flush=True)
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True);ctx=browser.new_context(viewport={'width':1280,'height':720},reduced_motion='reduce');page=ctx.new_page();page.set_default_timeout(30000);expect.set_options(timeout=30000)
    def ready():page.wait_for_function("document.documentElement.dataset.ready==='true'")
    def nav(key):page.locator('#wordmark [data-view="'+key+'"]').click();expect(page.locator('body')).to_have_attribute('data-view',key)
    def shot(name,full=False):page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/(name+'.png')),full_page=full);receipt['screenshots'].append(name+'.png')
    def audit(name):
        d=page.evaluate(contrast);d['screen']=name;receipt['audits'].append(d);check('CONTRAST_'+name,not d['failures'] and not d['boundary_failures'],d['failures']+d['boundary_failures'])
    try:
        page.goto('http://127.0.0.1:8766');ready()
        for theme in ('light','dark'):
            page.locator('#theme').select_option(theme)
            for key in ('study','race','ace','cohorts','evidence'):
                page.locator('#wordmark [data-view="'+key+'"]').hover();audit('glyph_plate_'+theme+'_'+key)
        runs=page.request.get('http://127.0.0.1:8766/api/runs').json()['runs'];rid=next(r['id'] for r in reversed(runs) if r['mode']=='diagnose_shift' and r['has_result']);nav('evidence');page.locator('#run-history').evaluate('e=>e.open=true');page.locator('[data-open-run="'+rid+'"]').click();expect(page.locator('body')).to_have_attribute('data-view','cohorts');page.locator('#show-shift').click();expect(page.locator('#gene-table tbody tr')).to_have_count(20);check('CE_TWENTY_ROWS_AND_EXACT_COUNTS','20 samples · 120 features' in page.locator('#shift-content').inner_text() and '14 samples · 120 features' in page.locator('#shift-content').inner_text())
        for theme in ('light','dark'):
            page.locator('#theme').select_option(theme);audit('ce_'+theme);shot('ce_'+theme,True);page.locator('#gene-table [data-gene]').first.click();audit('ce_feature_'+theme);shot('ce_feature_'+theme);page.keyboard.press('Escape')
        page.locator('#shift-next').click();expect(page.locator('#gene-table .table-foot')).to_contain_text('21–40');page.locator('#shift-prev').click();expect(page.locator('#gene-table .table-foot')).to_contain_text('1–20');check('CE_PAGINATION_NO_FEATURE_LOSS')
        # Small-q display boundary is an explicitly labeled UI-only fixture.
        page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');state.data.shift.gene_shifts[0].ks_bh_q_exploratory=1e-9;const {renderShift}=await import('/assets/js/legacy-results.js');renderShift()}");check('SMALL_Q_DISPLAY_ONLY_BOUNDARY','e-9' in page.locator('#gene-table tbody tr').first.inner_text())
        # Real local template download and direct output route remain available.
        response=page.request.get('http://127.0.0.1:8766/api/templates');check('INPUT_TEMPLATE_DOWNLOAD',response.status==200 and response.body()[:2]==b'PK')
        # Plain current task heading and interruption cleanup on final app.
        nav('study');page.locator('#new-data').click();page.locator('[data-start-task="evaluate_predictions"]').click();expect(page.locator('#cohorts-title')).to_have_text('Check inputs for saved classification prediction evaluation')
        folder=APP/'examples/design3_prediction_fixtures/equipment_faults';page.locator('#file-predictions').set_input_files(str(folder/'predictions.csv'));page.locator('#file-prediction_manifest').set_input_files(str(folder/'manifest.json'));page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Files checked');held=[];page.route('**/api/analyze',lambda r:held.append(r));page.locator('#run-analysis').click();expect(page.locator('#status-live')).to_have_attribute('data-state','running');page.reload();ready();expect(page.locator('#status-live')).to_contain_text('outcome is not confirmed');check('FINAL_INTERRUPTION_NO_RESUBMIT',len(held)==1)
        for route in held:
            try:route.abort()
            except Exception:pass
        page.unroute_all(behavior='ignoreErrors');shot('interrupted_request_final');check('DRIVER_CONTROLLED_REQUEST_CLEANUP')
        # FACE forward and reverse focus containment on final module.
        nav('study');page.locator('#other-public').click();expect(page.locator('body')).to_have_attribute('data-view','race');page.locator('[data-select-gene="135112"]').click();expect(page.locator('#trace-gene')).to_be_visible();page.locator('#close-face').focus();page.keyboard.press('Shift+Tab');expect(page.locator('#trace-gene')).to_be_focused();page.keyboard.press('Tab');expect(page.locator('#close-face')).to_be_focused();page.keyboard.press('Escape');expect(page.locator('[data-select-gene="135112"]')).to_be_focused();check('FINAL_FACE_REVERSE_FORWARD_ESCAPE_FOCUS')
        # Selected operational preview is measured after an interrupted real transition.
        page.emulate_media(reduced_motion='no-preference');nav('study');nav('race');page.set_viewport_size({'width':1440,'height':900});page.wait_for_timeout(300);page.locator('#wordmark [data-view="cohorts"]').hover();page.wait_for_timeout(220);d=page.evaluate("()=>{const p=document.querySelector('#wordmark-plate').getBoundingClientRect(),a=document.querySelector('[data-view=cohorts] .glyph').getBoundingClientRect(),z=document.querySelector('[data-view=evidence] .glyph').getBoundingClientRect();return {l:p.left-a.left+7,r:p.right-z.right-7}}")
        check('RESIZE_NAV_ANIMATION_FINAL_GEOMETRY',max(abs(v) for v in d.values())<1,d);receipt['status']='PASS'
    except Exception as exc:receipt['status']='FAIL';receipt['failure']=str(exc);raise
    finally:
        page.unroute_all(behavior='ignoreErrors');(OUT/'details_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');browser.close()
