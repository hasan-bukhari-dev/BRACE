from pathlib import Path
import os
import json
from playwright.sync_api import sync_playwright,expect
APP=Path(os.environ.get('BRACE_QA_APP',Path(__file__).resolve().parents[2]));ROOT=APP.parent;OUT=Path(os.environ.get('BRACE_QA_OUTPUT',APP/'qa_output'))/'review';OUT.mkdir(parents=True,exist_ok=True);receipt={'checks':[],'page_errors':[]}
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page(viewport={'width':1280,'height':720},reduced_motion='reduce');page.on('pageerror',lambda e:receipt['page_errors'].append(str(e)));expect.set_options(timeout=30000);page.goto(os.environ.get('BRACE_QA_URL','http://127.0.0.1:8766'));page.wait_for_function("document.documentElement.dataset.ready==='true'")
 def open_run(rid):
  page.locator('#wordmark [data-view="evidence"]').click();page.locator('#run-history').evaluate('e=>e.open=true');page.locator('[data-open-run="'+rid+'"]').click();expect(page.locator('#ace-confusion')).to_be_visible()
 try:
  manifest=json.loads((APP/'examples/design3_prediction_fixtures/equipment_faults/manifest.json').read_text());manifest['dataset_id']='Artificial V4 class-only stress fixture';manifest['probability_columns']={}
  records='sample_id,true_label,predicted_label\n'+''.join(f'row_{i},healthy,{"fault" if i%3==0 else "healthy"}\n' for i in range(1503))
  result=page.evaluate("async ({manifest,records})=>{const f=new FormData();f.set('mode','evaluate_predictions');f.set('predictions',new File([records],'artificial_class_only.csv'));f.set('prediction_manifest',new File([JSON.stringify(manifest)],'manifest.json'));const r=await fetch('/api/analyze',{method:'POST',body:f});if(!r.ok)throw Error(await r.text());return r.json()}",{'manifest':manifest,'records':records});open_run(result['id'])
  expect(page.locator('#prediction-field-panel')).to_contain_text('Saved class-only predictions');expect(page.locator('#prediction-field-panel')).to_contain_text('1002 correct and 501 incorrect');expect(page.locator('#prediction-field-panel .score-bins')).to_have_count(0);expect(page.locator('#confidence-results')).to_contain_text('unavailable');receipt['checks'].append({'id':'LARGE_CLASS_ONLY_COUNTS_NO_FALSE_SCORE_BINS','status':'PASS'})
  page.screenshot(path=str(OUT/'large_class_only.png'))
  runs=page.request.get('http://127.0.0.1:8766/api/runs').json()['runs']
  # Current broad/focused QA creates this actual 1503-row probability fixture.
  rid=None
  for r in runs:
   if r['mode']=='evaluate_predictions' and r['id']!=result['id']:
    data=page.request.get('http://127.0.0.1:8766/api/runs/'+r['id']).json()
    if data.get('validation',{}).get('n')==1503 and data['validation']['threshold_curve']:rid=r['id'];break
  assert rid;open_run(rid);expect(page.locator('.score-bins>div')).to_have_count(10);expect(page.locator('#prediction-field-panel')).to_contain_text('Counts by score interval');assert 'Square = correct' not in page.locator('#prediction-field-panel').inner_text();receipt['checks'].append({'id':'LARGE_SCORED_COUNTS_WITH_APPROPRIATE_BIN_LEGEND','status':'PASS'});page.screenshot(path=str(OUT/'large_scored_bins.png'))
  assert not receipt['page_errors'];receipt['status']='PASS'
 except Exception as e:receipt['status']='FAIL';receipt['failure']=str(e);raise
 finally:(OUT/'bins_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');b.close()
