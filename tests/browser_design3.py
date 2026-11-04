"""Real Chrome + production launch.py. Controlled failures are explicitly labeled."""
from pathlib import Path
import csv,hashlib,io,json,time,zipfile,re,traceback
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];APP=ROOT;OUT=APP/'docs/design3/after';OUT.mkdir(parents=True,exist_ok=True)
receipt={'checks':[],'screenshots':[],'page_errors':[],'unexpected_http_errors':[],'environment':{},'controlled_failure_requests':[]};started=time.perf_counter()
def check(name,condition=True,details=None):
    assert condition,(name,details)
    receipt['checks'].append({'id':name,'status':'PASS','details':details});print('PASS',name,flush=True)
def shot(page,name,full=False):
    if not page.locator('dialog[open]').count():page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path=str(OUT/(name+'.png')),full_page=full);receipt['screenshots'].append(name+'.png')
def nav(page,key):page.locator('#wordmark [data-view="'+key+'"]').click();expect(page.locator('body')).to_have_attribute('data-view',key)
def ready(page):page.wait_for_function("document.documentElement.dataset.ready==='true'")
def choose(page,task):
    nav(page,'study')
    button=page.locator('#new-data') if page.locator('#new-data').count() else page.locator('#own-data')
    button.click();expect(page.locator('#task-dialog')).to_be_visible();page.locator('[data-start-task="'+task+'"]').click()
def upload_pair(page,folder,public=False):
    for role in ('source','target'):
        for field,file in [('expression',role+('_expression.tsv' if public else '_expression.csv')),('metadata',role+('_metadata.tsv' if public else '_samples.csv')),('manifest',role+'_manifest.json')]:
            loc=page.locator('#file-'+role+'_'+field)
            if field=='manifest':loc.locator('..').evaluate('e=>e.open=true')
            loc.set_input_files(str(folder/file))
def preflight(page,allowed=True):
    page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Files checked for this task' if allowed else 'Task blocked',timeout=60000)
    if allowed:expect(page.locator('#run-analysis')).to_be_enabled()
def compute(page,route):
    page.locator('#run-analysis').click();expect(page.locator('body')).to_have_attribute('data-view',route,timeout=60000)
    if route=='race':expect(page.locator('#race-table tbody tr')).to_have_count(20,timeout=60000)
    if route=='ace':expect(page.locator('#ace-confusion')).to_be_visible(timeout=60000)
def assert_no_overflow(page,tag):
    page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
    sizes=page.evaluate('({w:innerWidth,scroll:document.documentElement.scrollWidth})');check(tag,sizes['scroll']<=sizes['w']+1,sizes)
def export(page,name):
    with page.expect_download() as event:page.locator('a[href^="/api/embrace/"]').first.click()
    path=OUT/(name+'.zip');event.value.save_as(str(path))
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        for row in csv.DictReader(io.StringIO(z.read('FILE_SHA256_MANIFEST.csv').decode())):assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
        (OUT/(name+'.html')).write_bytes(z.read('research_summary.html'))
    return path
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    context=browser.new_context(viewport={'width':1280,'height':720},reduced_motion='reduce',color_scheme='light',accept_downloads=True)
    page=context.new_page();page.set_default_timeout(20000);expect.set_options(timeout=20000)
    receipt['environment']={'browser':browser.version,'viewport':[1280,720],'runtime':'actual production launch.py at 127.0.0.1:8766','started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    page.on('pageerror',lambda e:receipt['page_errors'].append(str(e)))
    def response(r):
        if r.status>=400 and not receipt.get('expect_failure'):receipt['unexpected_http_errors'].append({'url':r.url,'status':r.status})
    page.on('response',response)
    try:
        page.goto('http://127.0.0.1:8766');ready(page)
        expect(page.locator('#landing .home-actions>button')).to_have_count(2);check('HOME_TWO_ACTIONS_NO_SIDEBAR',not page.locator('aside').count())
        for theme in ('light','dark'):
            page.locator('#theme').select_option(theme);shot(page,'home_'+theme)
            original=page.locator('.glyph').evaluate_all('els=>els.map(e=>({x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,width:e.getBoundingClientRect().width}))')
            for key in ('study','race','ace','cohorts','evidence'):
                page.locator('#wordmark [data-view="'+key+'"]').hover();expect(page.locator('#wordmark')).to_have_attribute('data-preview',key)
                current=page.locator('.glyph').evaluate_all('els=>els.map(e=>({x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,width:e.getBoundingClientRect().width}))')
                check('NAV_FIXED_GLYPHS_'+theme+'_'+key,all(abs(a['x']-b['x'])<.2 and abs(a['y']-b['y'])<.2 for a,b in zip(original,current)))
                plate=page.evaluate("""()=>{const n=document.querySelector('#wordmark'),k=n.dataset.preview,b=n.querySelector('[data-view="'+k+'"] .glyph').getBoundingClientRect(),z=n.querySelector('[data-view="evidence"] .glyph').getBoundingClientRect(),p=document.querySelector('#wordmark-plate').getBoundingClientRect(),pad=Number(getComputedStyle(n).getPropertyValue('--plate-pad'));return {left:p.left-b.left+pad,right:p.right-z.right-pad,top:p.top-b.top+pad,bottom:p.bottom-b.bottom-pad}}""")
                check('NAV_SUFFIX_GEOMETRY_'+theme+'_'+key,max(abs(v) for v in plate.values())<1,plate)
                shot(page,'preview_'+key+'_'+theme)
            page.mouse.move(15,600);expect(page.locator('#wordmark')).to_have_attribute('data-preview','study');check('PREVIEW_CANCEL_'+theme)
        page.locator('#wordmark [data-view="race"]').focus();page.keyboard.press('ArrowRight');expect(page.locator('#wordmark [data-view="ace"]')).to_be_focused();expect(page.locator('body')).to_have_attribute('data-view','study');page.keyboard.press('Escape');expect(page.locator('#wordmark')).to_have_attribute('data-preview','study');page.keyboard.press('Home');page.keyboard.press('End');expect(page.locator('#wordmark [data-view="evidence"]')).to_be_focused();page.keyboard.press('Enter');expect(page.locator('body')).to_have_attribute('data-view','evidence');check('KEYBOARD_ARROWS_HOME_END_ESCAPE_ENTER')
        for key in ('race','ace','cohorts','evidence'):
            nav(page,key);shot(page,'empty_'+key+'_dark')
        nav(page,'study');page.locator('#own-data').click();expect(page.locator('#task-dialog')).to_be_visible();page.keyboard.press('Escape');expect(page.locator('#own-data')).to_be_focused();check('TASK_DIALOG_ESCAPE_RETURN')
        for width,height,label in [(1440,900,'1440'),(390,844,'390'),(720,450,'200pct_equivalent')]:
            page.set_viewport_size({'width':width,'height':height});assert_no_overflow(page,'HOME_REFLOW_'+label);shot(page,'home_dark_'+label)
        page.set_viewport_size({'width':1280,'height':720});page.locator('#theme').select_option('light')
        t=time.perf_counter();page.locator('#explore-public').click();expect(page.locator('#race-table tbody tr')).to_have_count(20);receipt['saved_example_seconds']=round(time.perf_counter()-t,3)
        expect(page.locator('.result-sentence')).to_contain_text('14 of 20');check('PUBLIC_SAVED_FULL_FAMILY_AND_DENOMINATORS')
        for theme in ('light','dark'):
            page.locator('#theme').select_option(theme);shot(page,'race_'+theme,True)
            page.locator('[data-select-gene="135112"]').click();expect(page.locator('#face-body .expression-plot')).to_have_count(2);expect(page.locator('#face-body circle[data-sample]')).to_have_count(188);shot(page,'face_supported_'+theme);page.locator('#face-inspector').evaluate('e=>e.scrollTop=e.scrollHeight');shot(page,'face_statistics_'+theme);page.keyboard.press('Escape');expect(page.locator('[data-select-gene="135112"]')).to_be_focused()
        check('FACE_REAL_188_MEASUREMENTS_SEPARATE_AXES_AND_FOCUS')
        for fid,status in [('55816','insufficient support'),('54947','Opposite-direction estimate')]:
            page.locator('[data-select-gene="'+fid+'"]').click();expect(page.locator('#face-body')).to_contain_text(status);shot(page,'face_'+fid+'_dark');page.keyboard.press('Escape')
        check('FACE_INCONCLUSIVE_AND_OPPOSITE_EXPLICIT')
        page.locator('#race-filter').select_option('matching_direction_without_support');expect(page.locator('#race-table tbody tr')).to_have_count(5);nav(page,'study');nav(page,'race');expect(page.locator('#race-filter')).to_have_value('matching_direction_without_support');check('HOME_PRESERVES_RUN_FILTER_SELECTION')
        page.locator('#race-filter').select_option('all');page.locator('[data-select-gene="135112"]').click();page.locator('#trace-gene').click();expect(page.locator('#race-trace-panel')).to_contain_text('135112');expect(page.locator('.trace-chain li')).to_have_count(6);shot(page,'trace_race_dark',True)
        path=export(page,'public_saved_evidence');check('PUBLIC_EXPORT_ZIP_CRC_AND_ALL_HASHES',True,path.name)
        page.locator('#return-face').click();expect(page.locator('#face-inspector')).to_be_visible();expect(page.locator('#face-title')).to_contain_text('135112');page.keyboard.press('Escape');check('TRACE_RETURN_EXACT_GENE')
        # Browser failures are controlled fault-injection tests, never claimed as scientific output.
        page.route('**/api/race/studies/*/gene?*',lambda route:route.fulfill(status=503,content_type='application/json',body='{"detail":"Controlled browser-test outage. Retry this record."}'))
        receipt['expect_failure']=True;page.locator('[data-select-gene="55816"]').click();expect(page.locator('#retry-face')).to_be_visible();shot(page,'controlled_face_error_dark');page.unroute('**/api/race/studies/*/gene?*');receipt['expect_failure']=False;page.locator('#retry-face').click();expect(page.locator('#face-body .expression-plot')).to_have_count(2);page.keyboard.press('Escape');check('FACE_ERROR_RETRY_PRESERVES_SELECTED_GENE')
        # Fresh real public uploads through CE and existing RACE endpoint.
        choose(page,'race');upload_pair(page,APP/'examples/public_er_pair/prepared',True);config=json.loads((APP/'examples/public_er_pair/race_config.json').read_text())
        for key in ('positive','negative'):
            page.locator('#'+key).fill(config[key]);page.locator('#'+key+'-definition').fill(config['source_conditions'][config[key]])
        page.locator('#equivalence').check();page.locator('#processing-review').check();preflight(page)
        expect(page.locator('#preflight')).to_contain_text('101');expect(page.locator('#preflight')).to_contain_text('87');expect(page.locator('[data-status="blocked"]')).to_contain_text('baseline');shot(page,'public_preflight_valid_dark',True)
        page.locator('#task').select_option('train_validate');expect(page.locator('#run-analysis')).to_be_disabled();preflight(page,False);shot(page,'public_preflight_baseline_blocked_dark',True);check('PURPOSE_CHANGE_REUSES_FILES_BUT_RECHECKS_AND_BLOCKS_ER_BASELINE')
        page.locator('#task').select_option('race');preflight(page);t=time.perf_counter();compute(page,'race');receipt['fresh_public_computation_seconds']=round(time.perf_counter()-t,3)
        expect(page.locator('.result-sentence')).to_contain_text('14 of 20');check('FRESH_REAL_PUBLIC_UI_INTAKE_AND_RACE')
        nav(page,'evidence');expect(page.locator('#race-trace-panel')).to_contain_text('calculation');export(page,'public_fresh_evidence');check('FRESH_PUBLIC_RESULT_EXPORT')
        # Neutral non-biological controlled fixtures, actual existing prediction intake.
        for name in ('equipment_faults','text_categories'):
            choose(page,'evaluate_predictions');folder=APP/'examples/design3_prediction_fixtures'/name
            page.locator('#file-predictions').set_input_files(str(folder/'predictions.csv'));page.locator('#file-prediction_manifest').set_input_files(str(folder/'manifest.json'));expect(page.locator('#cohort-fields input[type=file]')).to_have_count(2)
            preflight(page);compute(page,'ace');expect(page.locator('#validation-content .ace-metric-panel .ace-metrics')).to_contain_text('66.67%');shot(page,name+'_light' if page.locator('#theme').input_value()=='light' else name+'_dark',True)
            for t,retained,correct in [('0',6,4),('0.95',2,1),('1',0,None)]:
                page.locator('#confidence-number').fill(t);page.locator('#confidence-number').press('Tab');expect(page.locator('#confidence-results')).to_contain_text(str(retained)+' of 6')
                if correct is not None:expect(page.locator('#confidence-results')).to_contain_text(str(correct)+' correct among '+str(retained))
                else:expect(page.locator('#confidence-results')).to_contain_text('undefined')
            page.locator('#confidence-number').fill('0.955');page.locator('#confidence-number').press('Tab');expect(page.locator('#threshold-input-error')).to_contain_text('has not changed');expect(page.locator('#confidence-results')).to_contain_text('0 of 6');check('NEUTRAL_'+name+'_THRESHOLDS_EQUALITY_EMPTY_INVALID')
            page.locator('#reset-range').click();page.locator('#sample-table [data-id]').first.click();expect(page.locator('#sample-detail')).to_contain_text('Supplied prediction record');page.locator('#trace-sample').click();expect(page.locator('.trace-chain')).to_contain_text('Supplied prediction origin');shot(page,'trace_'+name+'_dark',True);export(page,name+'_evidence');check('NEUTRAL_'+name+'_RECORD_TRACE_EXPORT')
        # Invalid input error preserves selected files; correction uses retained manifest.
        choose(page,'evaluate_predictions');folder=APP/'examples/design3_prediction_fixtures/equipment_faults';page.locator('#file-prediction_manifest').set_input_files(str(folder/'manifest.json'));lines=(folder/'predictions.csv').read_bytes().splitlines();page.locator('#file-predictions').set_input_files({'name':'duplicate.csv','mimeType':'text/csv','buffer':b'\n'.join([lines[0],lines[1],lines[1]])+b'\n'});receipt['expect_failure']=True;page.locator('#check-inputs').click();expect(page.locator('#status-live')).to_have_attribute('data-state','blocked');expect(page.locator('#preflight')).to_contain_text(re.compile('duplicate',re.I));shot(page,'invalid_input_dark');receipt['expect_failure']=False;page.locator('#file-predictions').set_input_files(str(folder/'predictions.csv'));preflight(page);compute(page,'ace');check('DUPLICATE_INPUT_ERROR_RETAINED_MANIFEST_AND_RECOVERY')
        # Existing baseline and unlabeled comparison remain executable from the same selected files.
        choose(page,'train_validate');upload_pair(page,APP/'examples/synthetic_valid');preflight(page);compute(page,'ace');expect(page.locator('[data-evaluation="source"]')).to_contain_text('Source out-of-fold');expect(page.locator('[data-evaluation="target"]')).to_contain_text('11');shot(page,'baseline_source_target_dark',True);check('MODE_B_SOURCE_OOF_SEPARATE_FROM_TARGET')
        nav(page,'cohorts');page.locator('#show-shift').click();expect(page.locator('#shift-content svg.chart-svg')).to_be_visible();shot(page,'ce_shift_dark',True);page.locator('#gene-table [data-gene]').first.click();expect(page.locator('#sample-dialog')).to_be_visible();shot(page,'ce_feature_dark');page.keyboard.press('Escape');check('SAME_RUN_CE_SOURCE_FITTED_COORDINATES_AND_FEATURE_INSPECTOR')
        nav(page,'study');page.locator('#new-data').click();page.locator('[data-start-task="diagnose_shift"]').click();preflight(page);compute(page,'cohorts');expect(page.locator('#shift-content')).to_contain_text('no accuracy or error association');check('MODE_C_UNLABELED_NO_INVENTED_ACCURACY')
        for theme in ('light','dark'):
            page.locator('#theme').select_option(theme);shot(page,'ce_unlabeled_'+theme,True);nav(page,'evidence');shot(page,'evidence_shift_'+theme,True);nav(page,'cohorts')
        # Historical confidence challenge preserves original saved evidence.
        nav(page,'study');page.locator('#other-examples').evaluate('e=>e.open=true');page.locator('#historical-demo').click();expect(page.locator('#ace-confusion')).to_be_visible();expect(page.locator('#confidence-results')).to_contain_text('583 correct among 584')
        for theme in ('light','dark'):
            page.locator('#theme').select_option(theme);page.locator('#confidence-number').fill('0.99');page.locator('#confidence-number').press('Tab');expect(page.locator('#confidence-results')).to_contain_text('431 correct among 432');shot(page,'ace_historical_'+theme,True)
        page.locator('#sample-search').fill('cfc121b5');expect(page.locator('#sample-table [data-id]')).to_have_count(1);page.locator('#sample-table [data-id]').click();expect(page.locator('#sample-detail')).to_contain_text('0.998692106');expect(page.locator('#sample-detail')).to_contain_text('Incorrect prediction');shot(page,'historical_high_confidence_error_dark');page.locator('#trace-sample').click();expect(page.locator('#ace-trace-panel')).to_contain_text('cfc121b5');check('HISTORICAL_680_668_THRESHOLDS_AND_EXACT_WRONG_RECORD_TRACE')
        # Actual local history and view state restoration.
        page.locator('#run-history').evaluate('e=>e.open=true');expect(page.locator('[data-open-run]')).not_to_have_count(0);shot(page,'history_dark',True)
        page.locator('[data-open-run]').first.click();page.wait_for_function("document.querySelector('#status-live').dataset.state==='ready'");check('LOCAL_HISTORY_OPENS_INTEGRITY_CHECKED_REAL_RUN')
        run_before=page.locator('#context').inner_text();page.locator('#theme').select_option('light');page.reload();ready(page);expect(page.locator('#theme')).to_have_value('light');expect(page.locator('#context')).to_contain_text(run_before.split('\n')[0]);check('THEME_AND_RUN_PERSIST_AFTER_RELOAD')
        page.emulate_media(color_scheme='dark');page.locator('#theme').select_option('system');expect(page.locator('html')).to_have_attribute('data-theme','dark');page.emulate_media(color_scheme='light');expect(page.locator('html')).to_have_attribute('data-theme','light');check('SYSTEM_THEME_FOLLOWS_OS')
        for width,height,label in [(1280,720,'1280'),(1440,900,'1440'),(390,844,'390'),(720,450,'200pct_equivalent')]:
            page.set_viewport_size({'width':width,'height':height})
            for key in ('race','ace','cohorts','evidence'):
                nav(page,key);assert_no_overflow(page,'OPERATIONAL_REFLOW_'+label+'_'+key)
                if label in ('390','200pct_equivalent'):shot(page,key+'_light_'+label)
        page.set_viewport_size({'width':1280,'height':720});nav(page,'study');page.emulate_media(forced_colors='active');shot(page,'forced_colors_home');page.locator('#wordmark [data-view="race"]').focus();page.keyboard.press('Space');expect(page.locator('body')).to_have_attribute('data-view','race');check('FORCED_COLORS_AND_SPACE_COMMIT');page.emulate_media(forced_colors='none')
        # Real animated pointer interruptions and CPU throttling, route must stay committed.
        nav(page,'study');page.emulate_media(reduced_motion='no-preference');cdp=context.new_cdp_session(page);cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
        for i in range(25):page.locator('#wordmark [data-view="'+['race','ace','cohorts','evidence','study'][i%5]+'"]').hover(force=True)
        page.mouse.move(12,610);page.wait_for_timeout(250);expect(page.locator('#wordmark')).to_have_attribute('data-preview','study');expect(page.locator('body')).to_have_attribute('data-view','study');check('INTERRUPTED_25_PREVIEWS_CPU_4X_NO_ROUTE_MUTATION');cdp.send('Emulation.setCPUThrottlingRate',{'rate':1});page.emulate_media(reduced_motion='reduce')
        # Touch has no preview-only dead end.
        touch=browser.new_context(is_mobile=True,has_touch=True,viewport={'width':390,'height':844},reduced_motion='reduce');tp=touch.new_page();tp.goto('http://127.0.0.1:8766');ready(tp);tp.locator('#wordmark [data-view="cohorts"]').tap();expect(tp.locator('body')).to_have_attribute('data-view','cohorts');check('TOUCH_COMMITS_CE');touch.close()
        check('NO_PAGE_ERRORS',not receipt['page_errors'],receipt['page_errors']);check('NO_UNEXPECTED_HTTP_ERRORS',not receipt['unexpected_http_errors'],receipt['unexpected_http_errors']);receipt['status']='PASS'
    except Exception as exc:
        receipt['status']='FAIL';receipt['failure']=str(exc);receipt['traceback']=traceback.format_exc();page.screenshot(path=str(OUT/'failure.png'));raise
    finally:
        receipt['duration_seconds']=round(time.perf_counter()-started,3);(OUT/'browser_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');browser.close()
