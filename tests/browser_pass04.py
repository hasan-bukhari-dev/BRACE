"""Real Chrome RACE/FACE integration. Uses the same spare-port adapter as Pass 3."""
import argparse
import csv
import json
import math
import tempfile
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'docs/pass04_screenshots'

def main(url):
    OUT.mkdir(exist_ok=True);checks=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        context=browser.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce',locale='en-US',timezone_id='America/Chicago')
        page=context.new_page();page.set_default_timeout(20000);page.on('pageerror',lambda e:errors.append(str(e)))
        def record(text):checks.append(text);print('PASS',text,flush=True)
        def nav(view):page.locator(f'nav [data-view="{view}"]').click();expect(page.locator('#view-'+view)).to_be_visible()
        def shot(name):page.screenshot(path=str(OUT/name),full_page=True,animations='disabled')
        def loaded(id):expect(page.locator('#face-title')).to_contain_text(id);expect(page.locator('#face-body .cohort-expression')).to_have_count(2)
        def overflow():assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.goto(url);page.wait_for_function("document.documentElement.dataset.ready==='true'");page.locator('#explore-public').click();page.wait_for_selector('#study-results');page.locator('#study-results').click();page.wait_for_selector('#race-table tbody tr')
        meta=page.request.get(url+'/api/race/studies/public_er_pass2/genes').json()
        expect(page.locator('#race-title')).to_have_text('Which genes hold up in another cohort?')
        expect(page.locator('#race-table tbody tr')).to_have_count(20)
        assert page.locator('.signature-summary strong').all_text_contents()==['20','20','14','5','1','0']
        for row,g in zip(page.locator('#race-table tbody tr').all(),meta['genes']):
            cells=row.locator('td').all_text_contents();assert cells[1]==g['feature_id'] and cells[2]==g['gene_symbol']
            for cell,key in [(3,'source_effect'),(4,'source_q'),(5,'effect'),(6,'q')]:assert math.isclose(float(cells[cell]),g[key],rel_tol=.006,abs_tol=.000051 if key.endswith('q') or key=='q' else .000501)
        record('All 20 visible rows match backend IDs, symbols, effects and q-values within documented rounding')
        summary=page.locator('.signature-summary').inner_text()
        for category,count in [('supported_matching_direction',14),('matching_direction_without_support',5),('opposite_direction',1),('untestable',0)]:
            page.locator('#race-filter').select_option(category);expect(page.locator('#race-table tbody tr')).to_have_count(count);assert page.locator('.signature-summary').inner_text()==summary
        page.locator('#race-filter').select_option('all')
        record('Outcome filters include negative and unavailable categories without changing summary denominators')
        for sorting,key in [('q','q'),('source_q','source_q'),('source_effect','source_effect'),('effect','effect')]:
            page.locator('#race-sort').select_option(sorting)
            actual=page.locator('#race-table tbody tr').evaluate_all('(rows)=>rows.map(r=>r.dataset.feature)')
            expected=[g['feature_id'] for g in sorted(meta['genes'],key=lambda g:(g[key] is None,g[key] or 0,g['feature_id']))]
            assert actual==expected
        record('Source/target effects and q-values sort numerically with stable feature-ID ties')
        page.locator('#race-sort').select_option('rank');page.locator('#race-search').fill('NCOA7');expect(page.locator('#race-table tbody tr')).to_have_count(1)
        page.locator('[data-select-gene="135112"]').focus();page.keyboard.press('Enter');loaded('135112')
        expected=page.request.get(url+'/api/race/studies/public_er_pass2/gene?feature_id=135112').json()
        for role in ('source','target'):
            dots=page.locator(f'[data-cohort="{role}"] circle').evaluate_all('(dots)=>dots.map(d=>({sample_id:d.dataset.sample,value:Number(d.dataset.value)}))')
            assert dots==[s for g in expected['cohorts'][role]['groups'] for s in g['samples']]
            cells=page.locator(f'[data-cohort="{role}"] .gene-statistics dd').all_text_contents()
            stats=expected['cohorts'][role]['statistics']
            for cell,key in [(0,'effect'),(1,'q'),(2,'hedges_g')]:
                assert math.isclose(float(cells[cell]),stats[key],rel_tol=.006,abs_tol=.000051 if key=='q' else .000501)
            assert all(math.isclose(float(shown),saved,abs_tol=.000501) for shown,saved in zip(cells[3].split(' to '),stats['ci95']))
        assert page.locator('.expression-plot').count()==2 and page.locator('.expression-plot circle').count()==188
        record('Keyboard selection opens FACE with all 101 source and 87 target raw observations on separate axes')
        shot('face_source_1440.png')
        page.locator('#face-inspector').evaluate('el=>{el.scrollTop=el.scrollHeight}')
        page.locator('#face-inspector').screenshot(path=str(OUT/'face_target_1440.png'),animations='disabled')
        page.locator('#trace-gene').click();expect(page.locator('#race-trace-panel')).to_contain_text('135112');expect(page.locator('#race-trace-panel')).to_contain_text(meta['hypothesis_hash'])
        shot('trace_1440.png');page.locator('#return-face').click();loaded('135112');page.locator('#close-face').click();expect(page.locator('#face-inspector')).not_to_be_visible();assert page.locator('[data-select-gene="135112"]').evaluate('el=>el===document.activeElement')
        record('Trace retains exact gene, source/target identity and frozen run hash; closing FACE restores row focus')
        page.locator('#race-search').fill('LPCAT2');page.locator('[data-select-gene="54947"]').click();loaded('54947');expect(page.locator('#face-body')).to_contain_text('Opposite-direction estimate')
        page.locator('#race-filter').select_option('supported_matching_direction');expect(page.locator('#face-inspector')).to_be_visible();expect(page.locator('#race-table')).to_contain_text('outside the current filter')
        nav('evidence');expect(page.locator('#race-trace-panel')).to_contain_text('54947');nav('race');loaded('54947');page.reload();page.wait_for_function("document.documentElement.dataset.ready==='true'");loaded('54947')
        expect(page.locator('#race-filter')).to_have_value('supported_matching_direction');expect(page.locator('#race-search')).to_have_value('LPCAT2');record('Opposite gene remains inspectable through filters, Evidence navigation and refresh')
        page.locator('#race-filter').select_option('all');page.locator('#race-search').fill('');page.locator('[data-select-gene="55816"]').click();loaded('55816');expect(page.locator('#face-body')).to_contain_text('insufficient support');shot('unsupported_1440.png')
        # Delay just one real response: the body remains actual checked backend data.
        def delay(route):
            response=route.fetch();time.sleep(.35);route.fulfill(response=response)
        page.route('**/gene?feature_id=135112',delay)
        page.locator('[data-select-gene="135112"]').click();page.locator('[data-select-gene="54947"]').click();loaded('54947');page.wait_for_load_state('networkidle');expect(page.locator('#face-title')).to_contain_text('54947');page.unroute('**/gene?feature_id=135112')
        record('Delayed older gene response cannot replace the latest selected gene')
        # Explicit UI failure injection; never counted as biological evidence.
        page.route('**/gene?feature_id=135112',lambda route:route.fulfill(status=409,content_type='application/json',body=json.dumps({'detail':{'message':'Checked input unavailable for test'}})))
        page.locator('[data-select-gene="135112"]').click();expect(page.locator('#face-body')).to_contain_text('Checked input unavailable');expect(page.locator('.expression-plot')).to_have_count(0);page.unroute('**/gene?feature_id=135112');page.locator('#retry-face').click();loaded('135112')
        record('Failed detail requests show no fabricated plot and offer a working retry')
        for width,height in [(1280,720),(390,844)]:
            page.set_viewport_size({'width':width,'height':height});overflow();page.locator('#face-title').scroll_into_view_if_needed();shot(f'face_{width}.png')
        assert page.locator('#close-face').evaluate('el=>getComputedStyle(el).transitionDuration')=='0s';page.locator('#close-face').focus();page.keyboard.press('Escape');expect(page.locator('#face-inspector')).not_to_be_visible()
        record('1280×720 and 390×844 layouts have no page overflow; reduced motion and Escape work')
        page.set_viewport_size({'width':1440,'height':900})
        # Real engine execution with one deliberately omitted target feature tests the unavailable state.
        nav('study');page.locator('#new-data').click();page.locator('#task').select_option('race')
        prepared=BASE/'examples/public_er_pair/prepared'
        with tempfile.TemporaryDirectory(prefix='brace-face-missing-') as directory:
            missing=Path(directory)/'target_expression.tsv'
            with (prepared/'target_expression.tsv').open() as source,missing.open('w') as target:
                for line in source:
                    if not line.startswith('135112\t'):target.write(line)
            for role in ('source','target'):
                for field,ext in [('expression','tsv'),('metadata','tsv'),('manifest','json')]:
                    path=missing if role=='target' and field=='expression' else prepared/f'{role}_{field}.{ext}'
                    page.locator(f'#file-{role}_{field}').set_input_files(str(path))
            for id,value in [('positive','ER_positive'),('negative','ER_negative'),('positive-definition','Clinically ER-positive primary breast tumor'),('negative-definition','Clinically ER-negative primary breast tumor')]:page.locator('#'+id).fill(value)
            page.locator('#equivalence').check();page.locator('#processing-review').check();page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Inputs checked');page.locator('#run-analysis').click();page.wait_for_function("document.querySelector('#status-live').dataset.state==='completed_with_warnings'",timeout=30000);page.wait_for_selector('[data-select-gene="135112"]');expect(page.locator('#race-filter')).to_have_value('all')
            page.locator('[data-select-gene="135112"]').click();loaded('135112');expect(page.locator('[data-cohort="target"]')).to_contain_text('Feature missing in target');expect(page.locator('[data-cohort="target"] .expression-plot')).to_have_count(0);expect(page.locator('[data-cohort="target"]')).to_contain_text('Unavailable');shot('missing_target_1440.png')
            page.locator('#face-inspector').evaluate('el=>{el.scrollTop=el.scrollHeight}')
            page.locator('#face-inspector').screenshot(path=str(OUT/'missing_target_detail.png'),animations='disabled')
        record('An actually omitted target feature produces an untestable row and no target distribution; new runs reset filters')
        # Rendering fixture only, clearly separate from numerical verification.
        page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');state.data.name='Long study name '.repeat(40);}");nav('race');overflow()
        long_id='GENE_<literal-ID>_'+('XYZ'*100)
        def long_identifier_fixture(route):
            response=route.fetch();payload=response.json();payload['genes'][0]['feature_id']=long_id;payload['genes'][0]['gene_symbol']=None;route.fulfill(response=response,json=payload)
        page.route('**/api/race/studies/*/genes',long_identifier_fixture);page.reload();page.wait_for_function("document.documentElement.dataset.ready==='true'")
        row=page.locator('#race-table tbody tr').first;expect(row.locator('[data-select-gene]')).to_have_text(long_id)
        assert row.locator('literal-ID').count()==0
        page.set_viewport_size({'width':390,'height':844});overflow()
        record('UI-only long literal feature-ID fixture is escaped and remains inside the scrollable table')
        assert not errors,errors
        (BASE/'docs/PASS04_BROWSER_RESULTS.json').write_text(json.dumps(dict(browser=browser.version,checks=checks,uncaught_errors=errors,
            screen_sizes=[[1440,900],[1280,720],[390,844]],screenshots=sorted(p.name for p in OUT.glob('*.png')),
            fixtures='Real pinned public study; actual RACE run with one target feature intentionally omitted; UI-only delayed/error response and long-label tests explicitly separated.'),indent=2)+'\n')
        browser.close()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url',default='http://127.0.0.1:8765');main(ap.parse_args().url)
