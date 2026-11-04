"""Pass 5 Chrome walkthrough: real archived evidence and labeled test fixtures.

No fixture is described as new biological data. Production calculations remain
the source of truth; response injections cover UI failure/delay behavior only.
"""
import argparse
import hashlib
import json
import math
import tempfile
import time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

BASE=Path(__file__).resolve().parents[1];OUT=BASE/'docs/pass05_screenshots'
def main(url):
    OUT.mkdir(exist_ok=True);checks=[];errors=[];external=[];latencies=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        context=browser.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce',locale='en-US',timezone_id='America/Chicago',accept_downloads=True)
        page=context.new_page();page.set_default_timeout(20000);page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') and not r.url.startswith(url) else None)
        def record(text):checks.append(text);print('PASS',text.encode('ascii','backslashreplace').decode(),flush=True)
        def ready():page.wait_for_function("document.documentElement.dataset.ready==='true'")
        def nav(view):page.locator(f'nav [data-view="{view}"]').click();expect(page.locator('#view-'+view)).to_be_visible()
        def overflow():assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        def shot(name,locator=None):
            (page.locator(locator).screenshot(path=str(OUT/name),animations='disabled') if locator else page.screenshot(path=str(OUT/name),full_page=True,animations='disabled'))
        def get(path):r=page.request.get(url+path);assert r.status==200,r.text();return r.json()
        def loaded():expect(page.locator('#ace-confusion')).to_be_visible()
        def assert_metrics(selector,m):
            text=page.locator(selector+' .ace-metrics dd').all_text_contents()
            assert list(map(int,text[:3]))==[m['n'],m['n_correct'],m['n']-m['n_correct']]
            for value,key in zip(text[3:],('accuracy','balanced_accuracy_observed','supported_class_macro_f1')):
                assert math.isclose(float(value.rstrip('%'))/100,m[key],abs_tol=.000051)
        def check_point(v,threshold):
            point=next(p for p in v['threshold_curve'] if p['threshold']==threshold)
            cells=page.locator('#confidence-results dd').all_text_contents();n=v['n']
            assert int(cells[0])==point['retained'] and int(cells[1])==n-point['retained']
            assert int(cells[3])==point['correct'] and int(cells[4])==point['errors']
            for idx,key in ((2,'coverage'),(5,'selective_accuracy'),(6,'selective_risk')):
                if point[key] is None:assert cells[idx]=='Undefined'
                else:assert math.isclose(float(cells[idx].rstrip('%'))/100,point[key],abs_tol=.000051)
            expect(page.locator('#threshold-output')).to_have_text(str(threshold).removesuffix('.0'))
            marker=page.locator('#selected-operating-point')
            if point['retained']:
                assert float(marker.get_attribute('data-coverage'))==point['coverage']
                assert float(marker.get_attribute('data-accuracy'))==point['selective_accuracy']
            else:expect(marker).to_have_count(0)
        def select_threshold(v,t):
            index=next(i for i,p in enumerate(v['threshold_curve']) if p['threshold']==t)
            started=time.perf_counter();page.locator('#confidence-range').fill(str(index));check_point(v,t)
            latencies.append((time.perf_counter()-started)*1000)
        def new_upload(task):
            nav('study');page.locator('#new-data').click();page.locator('#task').select_option(task)
        def finish_upload():
            page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Inputs checked');page.locator('#run-analysis').click()
            page.wait_for_function("document.querySelector('#status-live').dataset.state==='completed_with_warnings'",timeout=30000)
        page.goto(url);ready();page.locator('#other-examples').evaluate('el=>el.open=true');page.locator('#historical-demo').click();loaded()
        info=get('/api/ace/studies/historical_cptac');v=info['validation'];m=v['metrics']
        expect(page.locator('#ace-title')).to_have_text('Does the model generalize?');assert_metrics('[data-evaluation="target"]',m)
        assert page.locator('[data-evaluation="source"]').count()==0
        expect(page.locator('#validation-content')).to_contain_text('Source CV is not recorded');expect(page.locator('#context')).to_contain_text('Archived evidence')
        record('Historical metrics show 680 evaluated, 668 correct, 12 errors, support-based balanced accuracy/F1 and no fabricated source CV')
        counts=[int(v) for v in page.locator('#ace-confusion td').all_text_contents()]
        assert counts==[v for row in m['confusion_matrix'] for v in row] and sum(counts)==680
        for row,saved in zip(page.locator('#ace-per-class tbody tr').all(),m['per_class']):
            cells=row.locator('th,td').all_text_contents();assert cells[0]==saved['class'];assert list(map(int,cells[1:4]))==[saved['support'],saved['predicted_count'],saved['tp']]
            for value,key in zip(cells[4:7],('precision','recall','f1')):
                assert value=='Undefined' if saved[key] is None else math.isclose(float(value.rstrip('%'))/100,saved[key],abs_tol=.000051)
        record('Every displayed confusion cell and per-class support/precision/recall/F1 reconciles with saved evidence; absent prostate scores remain undefined')
        check_point(v,.95);shot('ace_historical_1440.png');shot('confidence_reference.png','.confidence-panel')
        expect(page.locator('#validation-content')).to_contain_text('Adjusting the threshold does not retrain the model.')
        record('Reference 0.95 retains 584, withholds 96, keeps 583 correct and 1 error; plotted selected point matches saved coverage and accuracy')
        select_threshold(v,.99);expect(page.locator('#threshold-status')).to_contain_text('Exploratory');shot('confidence_exploratory.png','.confidence-panel')
        page.locator('#confidence-range').focus();page.keyboard.press('Home');check_point(v,0)
        page.keyboard.press('End');check_point(v,1);expect(page.locator('#confidence-results')).to_contain_text('No predictions retained');shot('confidence_empty.png','.confidence-panel')
        page.locator('#reset-range').click();check_point(v,.95);assert page.locator('#confidence-range').evaluate('el=>el===document.activeElement')
        record('Keyboard threshold edges 0 and 1, empty sets, selective risk, exploratory role and exact-reference reset work without retraining')
        row=max(v['errors'],key=lambda r:r['confidence']);button=page.get_by_role('button',name=row['sample_id'],exact=True)
        button.focus();page.keyboard.press('Enter');expect(page.locator('#trace-sample')).to_be_visible();expect(page.locator('#sample-title')).to_have_text(row['sample_id'])
        expect(page.locator('#sample-detail')).to_contain_text('0.998692106');expect(page.locator('#sample-detail')).to_contain_text('breast');expect(page.locator('#sample-detail')).to_contain_text('ovary')
        assert page.locator('#sample-detail .prob-row').count()==5;shot('historical_high_confidence_error.png','#sample-dialog')
        expect(page.locator('#sample-detail')).to_contain_text('No related expression/shift descriptors')
        page.keyboard.press('Escape');assert button.evaluate('el=>el===document.activeElement')
        button.click();expect(page.locator('#trace-sample')).to_be_visible();page.locator('#trace-sample').click();expect(page.locator('#ace-trace-panel .trace-chain>li')).to_have_count(6)
        expect(page.locator('#ace-trace-panel')).to_contain_text(row['sample_id']);expect(page.locator('[data-step="folds"]')).to_contain_text('not performed');expect(page.locator('[data-step="scoring"]')).to_contain_text('No new inference')
        page.locator('[data-step="result"] details').evaluate('el=>el.open=true');shot('trace_historical_sample.png')
        record('Actual 99.87%-score breast→ovary error opens by keyboard, restores focus, and traces its archived row without unrelated expression evidence')
        artifact=page.locator('[data-step="metrics"] a').first
        with page.expect_download() as download:artifact.click()
        saved=Path(download.value.path()).read_bytes();assert json.loads(saved)['analysis']['n']==680
        record('TRACE artifact links download the selected run’s actual full-precision evidence')
        page.locator('#return-sample').click();expect(page.locator('#sample-title')).to_have_text(row['sample_id']);expect(page.locator('#trace-sample')).to_be_visible();page.keyboard.press('Escape')
        select_threshold(v,.9);nav('evidence');expect(page.locator('#ace-trace-panel')).to_contain_text(row['sample_id']);nav('ace');loaded();check_point(v,.9);page.reload();ready();loaded();check_point(v,.9)
        record('Selected sample/run and exploratory threshold persist through TRACE, return and reload')
        # Inject a failure only for sample retrieval, then recover actual data.
        pattern='**/api/ace/studies/historical_cptac?sample_id=*'
        page.route(pattern,lambda route:route.fulfill(status=409,content_type='application/json',body=json.dumps({'detail':{'message':'Checked sample unavailable for UI test'}})))
        button=page.get_by_role('button',name=row['sample_id'],exact=True);button.click();expect(page.locator('#sample-detail')).to_contain_text('Checked sample unavailable');assert page.locator('#sample-detail .prob-row').count()==0
        page.unroute(pattern);page.locator('#retry-sample').click();expect(page.locator('#trace-sample')).to_be_visible();page.keyboard.press('Escape')
        record('Failed sample retrieval clears previous scores and retry restores checked evidence')
        # Start two real retrievals before either response is available; oldest cannot win.
        delayed=v['errors'][0]['sample_id'];latest=row['sample_id']
        def delay(route):response=route.fetch();time.sleep(.3);route.fulfill(response=response)
        page.route(pattern,delay)
        page.evaluate("async(ids)=>{const {state}=await import('/assets/js/state.js');const {openSample}=await import('/assets/js/ace.js');openSample(state.data.validation.records.find(r=>r.sample_id===ids[0]));openSample(state.data.validation.records.find(r=>r.sample_id===ids[1]));}",[delayed,latest])
        expect(page.locator('#trace-sample')).to_be_visible();page.wait_for_load_state('networkidle');expect(page.locator('#sample-title')).to_have_text(latest);page.unroute(pattern);page.keyboard.press('Escape')
        record('A delayed older sample response cannot overwrite the currently selected prediction')
        for width,height in ((1280,720),(390,844)):
            page.set_viewport_size({'width':width,'height':height});overflow();shot(f'ace_historical_{width}.png')
        assert page.locator('#reset-range').evaluate('el=>getComputedStyle(el).transitionDuration')=='0s'
        record('ACE reflows at 1280×720 and 390×844 without page overflow and respects reduced motion')
        page.set_viewport_size({'width':1440,'height':900})
        # Controlled supplied-score fixture: includes exact off-grid reference equality.
        with tempfile.TemporaryDirectory(prefix='brace-pass05-') as directory:
            temp=Path(directory);manifest=dict(schema_version='1.0.0',dataset_id='explicit_browser_fixture',model_id='supplied_test_scores',classes=['A','B','C'],probability_columns={c:'p_'+c for c in 'ABC'},prediction_origin='external_model',evaluation_role='external_exploratory',independence_declaration='unknown',label_source_description='Controlled software test fixture, not biological evidence',primary_confidence_threshold=.955)
            (temp/'manifest.json').write_text(json.dumps(manifest));(temp/'predictions.csv').write_text('sample_id,true_label,predicted_label,p_A,p_B,p_C\nequal,B,A,.955,.045,0\ncertain,A,A,1,0,0\nlower,A,A,.6,.4,0\n')
            new_upload('evaluate_predictions')
            for key,name in (('predictions','predictions.csv'),('prediction_manifest','manifest.json')):page.locator('#file-'+key).set_input_files(str(temp/name))
            finish_upload();loaded();rid=page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');return state.data.id}");fixture=get('/api/ace/studies/'+rid)['validation']
            check_point(fixture,.955);assert page.locator('#sample-table tbody tr').count()==1
            page.locator('[data-filter="retained"]').click();expect(page.locator('#sample-table tbody tr')).to_have_count(2);expect(page.locator('#sample-table')).to_contain_text('equal')
            expect(page.locator('#context')).not_to_contain_text('GSE42568');expect(page.locator('#context')).not_to_contain_text('Archived evidence')
            record('Actual imported-score run retains equality at exact 0.955; new-run context resets and does not inherit historical/public cohort identities')
            manifest['probability_columns']={};(temp/'manifest.json').write_text(json.dumps(manifest));(temp/'predictions.csv').write_text('sample_id,true_label,predicted_label\n<literal-sample>,A,B\nsecond,B,B\n')
            new_upload('evaluate_predictions')
            for key,name in (('predictions','predictions.csv'),('prediction_manifest','manifest.json')):page.locator('#file-'+key).set_input_files(str(temp/name))
            finish_upload();loaded();expect(page.locator('#confidence-range')).to_be_disabled();expect(page.locator('#confidence-results')).to_contain_text('probability vectors were not supplied')
            page.get_by_role('button',name='<literal-sample>',exact=True).click();expect(page.locator('#trace-sample')).to_be_visible();assert page.locator('literal-sample').count()==0;expect(page.locator('#sample-detail')).to_contain_text('No class probability vector');page.keyboard.press('Escape');shot('no_probabilities_fixture.png')
            record('Missing probabilities disable confidence controls; undefined classes and hostile literal sample text render honestly')
        nav('study');page.locator('#other-examples').evaluate('el=>el.open=true');page.locator('#synthetic-demo').click();loaded()
        rid=page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');return state.data.id}");computed=get('/api/ace/studies/'+rid)
        assert_metrics('[data-evaluation="source"]',computed['source_cv']['metrics']);assert_metrics('[data-evaluation="target"]',computed['validation']['metrics']);shot('ace_source_target_synthetic.png')
        sample=computed['validation']['records'][0];page.locator('[data-filter="all"]').click();page.get_by_role('button',name=sample['sample_id'],exact=True).click();expect(page.locator('#trace-sample')).to_be_visible();expect(page.locator('#sample-detail')).to_contain_text('Same-run sample shift descriptors');page.locator('#trace-sample').click();expect(page.locator('#ace-trace-panel .trace-chain>li')).to_have_count(6)
        expect(page.locator('[data-step="folds"]')).to_contain_text('computed');expect(page.locator('#ace-trace-panel')).to_contain_text(rid);shot('trace_source_model_synthetic.png')
        record('Actual synthetic Mode B shows stored source OOF and target metrics separately and traces its frozen source model with same-run sample shift data')
        new_upload('diagnose_shift');folder=BASE/'examples/synthetic_valid'
        for role in ('source','target'):
            for field,name in (('expression',f'{role}_expression.csv'),('metadata',f'{role}_samples.csv'),('manifest',f'{role}_manifest.json')):page.locator(f'#file-{role}_{field}').set_input_files(str(folder/name))
        finish_upload();expect(page.locator('#gene-table')).to_be_visible();page.locator('#show-validation').click();expect(page.locator('#shift-trace')).to_be_visible();assert page.locator('#ace-confusion').count()==0
        page.locator('#shift-trace').click();expect(page.locator('#ace-trace-panel .trace-chain>li')).to_have_count(4);expect(page.locator('#ace-trace-panel')).to_contain_text('unlabeled_shift_only');shot('trace_mode_c.png')
        record('Mode C retains source-fitted shift diagnostics and TRACE with no labeled model metrics or outcome-conditioned results')
        nav('study');page.locator('#other-public').click();page.locator('#study-results').click();page.wait_for_selector('[data-select-gene="135112"]');page.locator('[data-select-gene="135112"]').click();expect(page.locator('#trace-gene')).to_be_visible();page.locator('#trace-gene').click();expect(page.locator('#race-trace-panel .trace-chain>li')).to_have_count(6)
        expect(page.locator('#race-trace-panel')).to_contain_text('135112');expect(page.locator('[data-step="freeze"]')).to_contain_text('Frozen signature');shot('trace_race_gene.png');page.locator('#return-face').click();expect(page.locator('#face-title')).to_contain_text('135112')
        record('Real public RACE/FACE trace follows inputs→compatibility→source screen→freeze→target tests→selected gene and returns to its measured expression')
        assert not errors,errors;assert not external,external
        (BASE/'docs/PASS05_BROWSER_RESULTS.json').write_text(json.dumps(dict(browser=browser.version,checks=checks,uncaught_errors=errors,external_application_requests=external,
            sizes=[[1440,900],[1280,720],[390,844]],screenshots=sorted(p.name for p in OUT.glob('*.png')),
            threshold_interaction_observations_ms=latencies,performance_note='Developer Chrome automation round-trip observations only, not controlled hardware benchmarks or unfamiliar-user timings.',
            fixtures='Archived CPTAC is real preserved evidence. Other Mode A scores and Mode B/C expression data are explicit software fixtures. Failure/delay injection is UI-only. Public RACE measurements remain real.'),indent=2)+'\n')
        browser.close()
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8765');main(parser.parse_args().url)
