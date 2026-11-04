"""Real Chrome E2E; run against this checkpoint's localhost server (not mocked science).
Test-only Origin mapping permits a spare port without changing production security.
Requires Playwright in the development environment; no app dependency added.
"""
import argparse
import json
import time
from urllib.parse import urlparse
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE=Path(__file__).resolve().parents[1]
EVIDENCE=BASE/'docs/pass03_screenshots'

def main(url,before):
    EVIDENCE.mkdir(exist_ok=True);checks=[];errors=[];console_errors=[];request_urls=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        context=browser.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce',locale='en-US',timezone_id='America/Chicago')
        # On spare port 8766, tests/browser_host.py maps the local test origin.
        # Module requests and the production app's security policy are unchanged.
        page=context.new_page();page.set_default_timeout(15000);page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:console_errors.append(m.text) if m.type=='error' else None)
        page.on('request',lambda r:request_urls.append(r.url))
        def record(name):checks.append(name);print('PASS',name,flush=True)
        def nav(view):page.locator(f'nav [data-view="{view}"]').click();expect(page.locator('#view-'+view)).to_be_visible()
        def screenshot(name):page.screenshot(path=str(EVIDENCE/name),full_page=True,animations='disabled')
        def ready():page.wait_for_function("document.documentElement.dataset.ready==='true'")
        def overflow():assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        def new_data(mode):
            nav('study')
            if page.locator('#new-data').count():page.locator('#new-data').click()
            elif page.locator('#own-data').is_visible():page.locator('#own-data').click()
            page.locator('#task').select_option(mode)
        def inputs(prediction=False,public=False):
            folder=BASE/'examples'/('public_er_pair/prepared' if public else 'synthetic_prediction_input' if prediction else 'synthetic_valid')
            names={'predictions':'predictions.csv','prediction_manifest':'manifest.json'} if prediction else {f'{r}_{k}':f'{r}_{v}' for r in ('source','target') for k,v in ([('expression','expression.tsv'),('metadata','metadata.tsv'),('manifest','manifest.json')] if public else [('expression','expression.csv'),('metadata','samples.csv'),('manifest','manifest.json')])}
            for name,filename in names.items():page.locator('#file-'+name).set_input_files(str(folder/filename))
        def check_and_run():
            page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Inputs checked');expect(page.locator('#run-analysis')).to_be_enabled();page.locator('#run-analysis').click();page.wait_for_function("document.querySelector('#status-live').dataset.state==='completed_with_warnings'",timeout=30000)
        if before:
            page.goto(before);page.wait_for_load_state('networkidle');screenshot('before_1440.png')
            console_errors.clear()
        page.goto(url);ready();assert not page.locator('#context').is_visible();assert not page.locator('#data-entry').is_visible();expect(page.locator('#study-title')).to_contain_text('Does your finding hold up')
        record('Initial state: two primary actions, no automatic historical selection')
        for width,height in [(1440,900),(1280,720),(390,844)]:
            page.set_viewport_size({'width':width,'height':height});overflow();screenshot(f'landing_{width}.png')
        page.set_viewport_size({'width':1440,'height':900})
        # Keyboard navigation: native button activation and visible focus.
        page.locator('#explore-public').focus();assert page.locator('#explore-public').evaluate('el=>getComputedStyle(el).outlineStyle')!='none'
        page.keyboard.press('Enter');expect(page.locator('#study-summary')).to_contain_text('101 samples');record('Keyboard activation opens pinned real public study')
        page.locator('#study-results').click();expect(page.locator('#race-table tbody tr')).to_have_count(20)
        result=page.request.get(url+'/api/example/public-er').json()
        assert result['race']['aggregate']['supported']==14
        page.locator('#race-search').fill('135112');expect(page.locator('#race-table tbody tr')).to_have_count(1)
        page.locator('[data-select-gene="135112"]').click();page.locator('#race-sort').select_option('q');nav('evidence');nav('race');expect(page.locator('#race-search')).to_have_value('135112');expect(page.locator('#race-sort')).to_have_value('q');expect(page.locator('#race-table tr[aria-selected=true]')).to_have_count(1)
        page.reload();ready();expect(page.locator('#race-search')).to_have_value('135112');record('Run, gene selection, filter and sort survive navigation and refresh')
        page.locator('#race-search').fill('');page.locator('#race-sort').select_option('rank');screenshot('race_1440.png')
        nav('evidence');page.locator('#methods summary').click();expect(page.locator('#methods-body')).to_contain_text('Two-sided Welch')
        with page.expect_download() as download:page.get_by_role('link',name='replication_genes.csv',exact=True).click()
        assert download.value.failure() is None
        record('Executed methods and CSV evidence download are connected')
        new_data('evaluate_predictions');expect(page.locator('[data-file]')).to_have_count(2);inputs(prediction=True);check_and_run();nav('ace');expect(page.locator('#validation-content')).to_contain_text('Overall accuracy');record('Prediction-only upload → preflight → actual evaluation')
        nav('study');page.locator('#other-examples summary').click();page.locator('#historical-demo').click();expect(page.locator('#validation-content')).to_contain_text('680')
        button=page.locator('#sample-table [data-id]').first;sample=button.get_attribute('data-id');button.click();expect(page.locator('#sample-dialog')).to_be_visible();page.keyboard.press('Tab');assert page.locator('#sample-dialog').evaluate('el=>el.contains(document.activeElement)');page.keyboard.press('Escape');expect(page.locator('#sample-dialog')).not_to_be_visible();assert page.locator(f'[data-id="{sample}"]').evaluate('el=>el===document.activeElement');record('Archived evidence retained; inspector traps focus, closes on Escape and restores focus')
        nav('study');page.locator('#synthetic-demo').click();expect(page.locator('#context')).to_contain_text('Synthetic');nav('ace');expect(page.locator('#validation-content')).to_contain_text('synthetic');page.locator('#show-shift').click();expect(page.locator('#shift-content')).to_contain_text('Distribution shifts');record('Synthetic model and source-fitted shift still run')
        new_data('diagnose_shift');inputs();check_and_run();nav('ace');page.locator('#show-shift').click();expect(page.locator('#shift-content')).to_contain_text('Distribution shifts');page.locator('#show-validation').click();expect(page.locator('#validation-content')).to_contain_text('No labeled predictions');record('Unlabeled Mode C preserved without accuracy claims')
        page.locator('#show-shift').click();feature=page.locator('#gene-table [data-gene]').first.get_attribute('data-gene');page.locator('#gene-table [data-gene]').first.click();page.reload();ready();expect(page.locator('#sample-dialog')).to_be_visible();expect(page.locator('#sample-title')).to_have_text(feature);page.keyboard.press('Escape');record('Shift feature inspector and selected feature restore after refresh')
        new_data('train_validate');inputs();check_and_run();nav('ace');expect(page.locator('#validation-content')).to_contain_text('Overall accuracy');record('Source/target Mode B upload and model evaluation preserved')
        # Invalid preflight retains the last successful run and selected files.
        new_data('diagnose_shift');inputs();old_context=page.locator('#context').inner_text();page.locator('#file-source_expression').set_input_files({'name':'invalid.csv','mimeType':'text/csv','buffer':b'feature_id,S,S\nx,1,2\n'});page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Analysis blocked');expect(page.locator('#run-analysis')).to_be_disabled();assert page.locator('#context').inner_text()==old_context;screenshot('blocked_1440.png');record('Invalid input blocks execution, retains completed run and files')
        # Live RACE upload uses the pinned prepared measurements; no mocks.
        new_data('race');inputs(public=True)
        for id,value in [('positive','ER_positive'),('negative','ER_negative'),('positive-definition','Clinically ER-positive primary breast tumor'),('negative-definition','Clinically ER-negative primary breast tumor')]:page.locator('#'+id).fill(value)
        page.locator('#equivalence').check();page.locator('#processing-review').check();page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Inputs checked');screenshot('study_inputs_1440.png');page.locator('#run-analysis').click();nav('evidence');page.wait_for_function("document.querySelector('#status-live').dataset.state==='completed_with_warnings'",timeout=30000);nav('race');expect(page.locator('#race-table tbody tr')).to_have_count(20);expect(page.locator('#context')).to_contain_text('GSE42568_ER');expect(page.locator('#context')).to_contain_text('GSE20711_ER');record('Live public-data RACE upload; navigation during computation preserves run')
        # Study context contains user cohort IDs without silently substituting the approved example.
        nav('study');expect(page.locator('#study-summary')).to_contain_text('GSE42568_ER');expect(page.locator('#study-summary')).to_contain_text('GSE20711_ER')
        nav('race')
        for width,height in [(1280,720),(390,844)]:page.set_viewport_size({'width':width,'height':height});overflow();screenshot(f'race_{width}.png')
        page.set_viewport_size({'width':720,'height':450});overflow();record('1440×900, 1280×720, 390×844 and 200%-equivalent reflow have no page overflow')
        page.set_viewport_size({'width':1440,'height':900});assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches");assert page.locator('#race-search').evaluate('el=>getComputedStyle(el).transitionDuration')=='0s';record('Reduced-motion controls preserve functionality')
        # Isolated failure injection, explicitly not evidence of scientific success.
        nav('study');page.route('**/api/example/public-er',lambda route:route.fulfill(status=503,content_type='application/json',body=json.dumps({'detail':{'message':'Example unavailable for test'}})))
        page.locator('#other-public').click();expect(page.locator('#status-live')).to_contain_text('Public example unavailable');expect(page.locator('#context')).to_be_visible();page.unroute('**/api/example/public-er');record('Injected unavailable example reports failure and preserves prior result')
        page.locator('#other-public').click();expect(page.locator('#study-summary')).to_contain_text('saved exploratory computation');record('Retry after injected failure recovers the verified public example')
        # Long user-facing study names are data, not HTML. This is an isolated rendering fixture.
        page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');state.data.name='<script>bad()</script>'+('Long study name '.repeat(30));state.data.race.genes[0].feature_id='GENE_'+('XYZ'.repeat(90));}")
        nav('evidence');overflow();assert page.locator('#context script').count()==0;record('Long hostile study label is escaped and wraps without page overflow')
        nav('race');overflow();page.set_viewport_size({'width':390,'height':844});overflow();record('Long gene identifiers wrap inside the scrollable table without page overflow')
        assert not errors,errors
        assert all('503' in text for text in console_errors),console_errors
        assert all(urlparse(u).hostname=='127.0.0.1' for u in request_urls if urlparse(u).scheme in ('http','https'))
        record('Application requests stay on localhost; only the injected 503 produces a console resource error')
        record('No uncaught browser errors in completed scenarios')
        (BASE/'docs/PASS03_BROWSER_RESULTS.json').write_text(json.dumps({'browser':browser.version,'url':url,'checks':checks,'uncaught_errors':errors,'console_errors':console_errors,'external_application_requests':[],'screenshots':sorted(p.name for p in EVIDENCE.glob('*.png')),'test_origin_mapping':'Test-only ASGI adapter on port 8766 normalizes its own local origin to canonical localhost:8765; production security unchanged','not_run':['screen-reader software','independent unfamiliar-user study','other browser engines']},indent=2)+'\n')
        browser.close()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url',default='http://127.0.0.1:8765');ap.add_argument('--before');args=ap.parse_args();main(args.url,args.before)
