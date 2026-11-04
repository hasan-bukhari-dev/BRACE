"""V6 production-browser journeys; artificial fixtures are technical tests only."""
from pathlib import Path
import ast,json,traceback,io,zipfile,hashlib
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2];APP=ROOT;OUT=APP/'docs/v6/qa';OUT.mkdir(exist_ok=True)
receipt={'checks':[],'screenshots':[],'errors':[],'external_requests':[],'audits':[]}
contrast=(Path(__file__).resolve().parent/'contrast-check.js').read_text(encoding='utf-8')
def check(name,ok=True,details=None):
 assert ok,(name,details)
 receipt['checks'].append({'id':name,'status':'PASS','details':details});print('PASS',name,flush=True)
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);ctx=b.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce',accept_downloads=True);page=ctx.new_page();page.set_default_timeout(40000);expect.set_options(timeout=40000)
 page.on('pageerror',lambda e:receipt['errors'].append(str(e)));page.on('request',lambda r:receipt['external_requests'].append(r.url) if not r.url.startswith(('http://127.0.0.1:8787/','blob:http://127.0.0.1:8787/')) else None)
 def ready():page.wait_for_function("document.documentElement.dataset.ready==='true'")
 def nav(v):page.locator('#wordmark [data-view="'+v+'"]').click()
 def shot(n,full=False):
  page.mouse.move(3,3);page.wait_for_timeout(180);page.screenshot(path=str(OUT/(n+'.png')),full_page=full);receipt['screenshots'].append(n+'.png');receipt['audits'].append({'screen':n,**page.evaluate(contrast)})
 def choose(mode):
  nav('study');page.locator('#new-data' if page.locator('#new-data').count() else '#own-data').click();page.locator('[data-start-task="'+mode+'"]').click();expect(page.locator('#data-entry')).to_have_attribute('data-step','1')
 def next():page.locator('#setup-next').click()
 def step(n):expect(page.locator('#data-entry')).to_have_attribute('data-step',str(n))
 def preflight(allowed=True):
  next();expect(page.locator('#preflight')).to_contain_text('Ready to compute' if allowed else 'Cannot compute',timeout=60000)
 def guided_prediction(scores=False,large=False):
  choose('evaluate_predictions');data='sample_id,true_label,predicted_label'+(',p_ok,p_fault' if scores else '')+'\na,ok,ok'+(',.955,.045' if scores else '')+'\nb,ok,fault'+(',.045,.955' if scores else '')+'\nc,fault,fault'+(',.4,.6' if scores else '')+'\n'
  if large:data+=''.join('extra_'+str(i)+',ok,ok,.6,.4\n' for i in range(1500))
  page.locator('#file-predictions').set_input_files({'name':'technical_predictions.csv','mimeType':'text/csv','buffer':data.encode()});expect(page.locator('[data-preview-file="predictions"]')).to_contain_text('Local file preview');next();step(2)
  for key,value in [('dataset','Technical UI fixture'),('model','Fixture, not a research model'),('labels','Artificial test labels'),('classes','ok\nfault'),('threshold','.955')]:page.locator('#declaration-'+key).fill(value)
  if scores:
   page.locator('#declaration-mapping').click();page.locator('#score-column-0').fill('p_ok');page.locator('#score-column-1').fill('p_fault')
  page.locator('#use-declaration').click();next();step(4);preflight();next();expect(page.locator('body')).to_have_attribute('data-view','ace',timeout=60000)
 try:
  page.goto('http://127.0.0.1:8787');ready();shot('home');page.locator('#open-help').click();expect(page.locator('#help-content')).to_contain_text('Two studies');page.locator('[data-help="predictions"]').click();expect(page.locator('#help-content')).to_contain_text('Bring the predictions');page.keyboard.press('Escape');check('HELP_CLOSE_RETURNS_OPENER',page.locator('#open-help').evaluate('(e)=>e===document.activeElement'))
  page.locator('#own-data').click();page.locator('#unsupported-data').click();expect(page.locator('#task-dialog')).not_to_be_visible();expect(page.locator('#help-content')).to_contain_text('EMBRACE evidence ZIP');shot('guide_other');page.locator('#guide-public').click();expect(page.locator('[data-signature-gene]')).to_have_count(20);check('GUIDE_PUBLIC_NO_OBSCURING_MODAL',page.locator('dialog[open]').count()==0)
  metadata=page.request.get('http://127.0.0.1:8787/api/race/studies/public_er_pass2/genes').json();genes=metadata['genes'];check('RACE_ALL_20_OUTCOMES',len(genes)==20 and sum(g['classification']=='supported_matching_direction' for g in genes)==14, [g['classification'] for g in genes])
  expect(page.locator('#paired-effect-chart .scatterlayer')).to_be_visible();shot('race');
  for g in genes:
   page.locator('[data-signature-gene="'+g['feature_id']+'"]').click();page.wait_for_function('(y)=>{let e=document.querySelector("#paired-effect-chart");return e?.data?.[0]?.y?.[1]===y}',arg=g['hedges_g']);ys=page.locator('#paired-effect-chart').evaluate('e=>e.data[0].y');check('PAIRED_EFFECT_'+g['feature_id'],ys==[g['source_hedges_g'],g['hedges_g']])
  page.locator('[data-signature-gene="135112"]').click();page.locator('#preview-measurements').click();expect(page.locator('#expression-source .scatterlayer')).to_be_visible();detail=page.request.get('http://127.0.0.1:8787/api/race/studies/public_er_pass2/gene?feature_id=135112').json()
  for role,c in detail['cohorts'].items():
   marks=page.locator('#expression-'+role).evaluate('e=>e.data.filter(t=>t.type==="scatter").flatMap(t=>t.y.map((v,i)=>({id:t.customdata[i],value:v})))');expected=[{'id':s['sample_id'],'value':s['value']} for g in c['groups'] for s in g['samples']];check('FACE_'+role+'_ALL_MEASUREMENTS',marks==expected,len(marks))
  shot('face');point=page.locator('#expression-source .scatterlayer .point').first.bounding_box();page.mouse.move(point['x']+point['width']/2,point['y']+point['height']/2);expect(page.locator('#expression-source .hovertext')).to_be_visible();check('PLOT_REAL_SAMPLE_HOVER');page.locator('#expression-source .modebar-btn[data-title="Zoom in"]').click();check('PLOT_ZOOM_CHANGES_RANGE',page.locator('#expression-source').evaluate('e=>e.layout.xaxis.range[1]-e.layout.xaxis.range[0]')<2)
  with page.expect_download() as dl:page.locator('#expression-source .modebar-btn').first.click()
  dl.value.save_as(str(OUT/'actual_gene_chart.png'));check('PLOT_ACTUAL_PNG_EXPORT',(OUT/'actual_gene_chart.png').read_bytes().startswith(b'\x89PNG'))
  for key in ['Tab','Shift+Tab']:
   for _ in range(9):page.keyboard.press(key);check('FACE_CONTAINED_FOCUS_'+key,page.evaluate('document.querySelector("#face-inspector").contains(document.activeElement)'))
  page.locator('#trace-gene').click();expect(page.locator('[data-trace-step]')).to_have_count(6)
  for i in range(6):page.locator('[data-trace-step="'+str(i)+'"]').click();expect(page.locator('[data-trace-step="'+str(i)+'"]')).to_have_attribute('aria-pressed','true')
  check('ALL_SIX_TRACE_STEPS_SELECTABLE');shot('calculation');page.locator('[data-evidence-tab="report"]').click();expect(page.locator('#report-frame')).to_be_visible();shot('evidence')
  report=page.request.get('http://127.0.0.1:8787/api/embrace/public_er_pass2/report');z=zipfile.ZipFile(io.BytesIO(page.request.get('http://127.0.0.1:8787/api/embrace/public_er_pass2').body()));check('PREVIEW_EQUALS_EXPORTED_HTML',report.body()==z.read('research_summary.html'));check('REPORT_NO_SCRIPT_SANDBOX',page.locator('#report-frame').get_attribute('sandbox')=='allow-downloads')
  for row in __import__('csv').DictReader(io.StringIO(z.read('FILE_SHA256_MANIFEST.csv').decode())):check('EVIDENCE_HASH_'+row['path'],hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256'])
  nav('study');shot('workbench');page.locator('#other-examples').evaluate('e=>e.open=true');page.locator('#historical-demo').click();expect(page.locator('#confidence-chart .scatterlayer')).to_be_visible()
  for t,n,c in [('0',680,668),('0.95',584,583),('0.99',432,431),('1',0,0)]:
   page.locator('#confidence-number').fill(t);page.locator('#confidence-number').press('Tab');expect(page.locator('#confidence-results')).to_contain_text(str(n)+' of 680');marks=page.locator('[data-field-id]').evaluate_all('es=>({n:es.filter(e=>e.dataset.retained==="true").length,c:es.filter(e=>e.dataset.retained==="true"&&e.dataset.correct==="true").length})');check('ALL_680_RETENTION_'+t,marks=={'n':n,'c':c},marks)
  page.locator('#confidence-number').fill('0.95');page.locator('#confidence-number').press('Tab');shot('ace');page.locator('.ace-overview').scroll_into_view_if_needed();shot('ace_matrix');page.locator('#ace-confusion .matrix-cell').first.click();expect(page.locator('.matrix-filter-receipt')).to_be_visible();check('CONFUSION_CELL_FILTER',page.locator('#sample-table tbody tr').count()>0);page.locator('#clear-matrix-filter').click();page.locator('#overview-error').click();expect(page.locator('#sample-detail')).to_contain_text('0.998692106');shot('prediction_inspector');page.keyboard.press('Escape')
  page.keyboard.press('Control+k');page.locator('#find-query').fill('cfc121b5');expect(page.locator('[data-find-result]')).to_have_count(1);page.locator('[data-find-result]').click();expect(page.locator('#sample-dialog')).to_be_visible();check('SEARCH_RECORD_OPENS_REAL_INSPECTOR');page.keyboard.press('Escape')
  guided_prediction();expect(page.locator('#confidence-results')).to_contain_text('unavailable');check('CLASS_ONLY_UNAVAILABLE_NOT_WITHHELD',page.locator('[data-retained="unavailable"]').count()==3);shot('class_only')
  guided_prediction(True);expect(page.locator('#confidence-results')).to_contain_text('1 correct among 2 retained');check('NO_JSON_GUIDED_SCORES_EXACT_0955');shot('guided_prediction')
  guided_prediction(True,True);page.locator('#record-map').evaluate('e=>e.open=true');expect(page.locator('.score-bins>div')).to_have_count(10);check('LARGE_RECORD_BINS_EXACT','1501 records' in page.locator('.score-bins').inner_text());shot('large_record_bins')
  # Independent guided cohort descriptions; scientific fixture values unchanged.
  choose('diagnose_shift');folder=APP/'examples/synthetic_valid'
  for role in ['source','target']:
   page.locator('#file-'+role+'_expression').set_input_files(str(folder/(role+'_expression.csv')));page.locator('#file-'+role+'_metadata').set_input_files(str(folder/(role+'_samples.csv')))
  next();step(2)
  for role in ['source','target']:
   page.locator('#'+role+'-cohort-name').fill('Technical '+role);page.locator('#'+role+'-human').check();page.locator('#'+role+'-measurement').select_option('microarray_log2_normalized');page.locator('#'+role+'-namespace').select_option('entrez_gene');page.locator('#'+role+'-platform').fill('SYNTHETIC_ONLY');page.locator('#'+role+'-processing').fill('Artificial normalized values for interface verification only.');page.locator('#save-'+role+'-declaration').click()
  shot('guided_cohort_descriptions');next();step(3);next();step(4);preflight();page.locator('#edit-checked').click();step(1);check('EDIT_FILES_RETURNS_VISIBLE_INPUTS');next();step(2);page.locator('#source-processing').fill('Changed technical processing declaration');next();expect(page.locator('#setup-error')).to_contain_text('Save both');check('DESCRIPTION_EDIT_INVALIDATES');page.locator('#save-source-declaration').click();next();next();preflight();next();expect(page.locator('#projection-chart .scatterlayer')).to_be_visible(timeout=60000);shot('ce_projection')
  projection=page.locator('#projection-chart').evaluate('e=>e.data.map(t=>({x:t.x,y:t.y,ids:t.customdata}))');saved=page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');return state.data.shift.pca.samples}");check('ALL_SOURCE_FIT_PCA_POINTS_EXACT',all(projection[i]['ids']==[r['sample_id'] for r in saved if r['cohort']==role] and projection[i]['x']==[r['pc1'] for r in saved if r['cohort']==role] for i,role in enumerate(['source','target'])))
  check('MODE_C_NO_TARGET_ACCURACY','accuracy' not in page.locator('#shift-content').inner_text().lower() or 'not' in page.locator('#shift-content').inner_text().lower());page.locator('#feature-mode').click();shot('ce_features');page.locator('#shift-q').select_option('0.05');check('CE_FILTER_ACTUAL_FAMILY',page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');return [...document.querySelectorAll('#gene-table [data-gene]')].every(e=>state.data.shift.gene_shifts.find(g=>g.feature_id===e.dataset.gene).ks_bh_q_exploratory<=.05)}"));page.locator('#shift-q').select_option('');page.locator('#gene-table [data-gene]').first.click();shot('feature_inspector');page.keyboard.press('Escape')
  choose('race');[page.locator('#file-'+role+'_'+kind).set_input_files([]) for role in ['source','target'] for kind in ['expression','metadata']];next();expect(page.locator('#setup-error')).to_contain_text('Choose');check('MISSING_FILES_ACTIONABLE');shot('missing_files');page.locator('#load-public-inputs').click();step(3);expect(page.locator('#status-live')).to_have_attribute('data-state','ready');page.locator('#equivalence').check();page.locator('#processing-review').check();next();preflight();shot('checked_public');next();expect(page.locator('body')).to_have_attribute('data-view','race',timeout=60000);expect(page.locator('.result-sentence')).to_contain_text('14 / 20');check('REAL_PUBLIC_RECOMPUTE_FROM_GUIDED_FILES')
  # Reload restores the actual selected saved run and user-selected route.
  rid=page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');return state.data.id}");page.reload();ready();expect(page.locator('.result-sentence')).to_contain_text('14 / 20');check('RELOAD_RESTORES_INTEGRITY_CHECKED_RUN',page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');return state.data.id}")==rid)
  page.locator('#theme').select_option('dark');shot('race_dark');page.locator('[data-signature-gene="135112"]').click();page.locator('#preview-measurements').click();expect(page.locator('#expression-source .scatterlayer')).to_be_visible();shot('face_dark');page.keyboard.press('Escape');nav('evidence');expect(page.locator('#report-frame')).to_be_visible();shot('evidence_dark')
  check('NO_PAGE_ERRORS',not receipt['errors'],receipt['errors']);check('ALL_RUNTIME_REQUESTS_LOCAL',not receipt['external_requests'],receipt['external_requests']);receipt['status']='PASS'
 except Exception as e:receipt['status']='FAIL';receipt['failure']=str(e);receipt['traceback']=traceback.format_exc();shot('failure');raise
 finally:(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2));b.close()



