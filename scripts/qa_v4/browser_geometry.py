from pathlib import Path
import json
from playwright.sync_api import sync_playwright,expect
APP=Path(__file__).resolve().parents[2];ROOT=APP.parent;OUT=APP/'qa_output/review';OUT.mkdir(parents=True,exist_ok=True);receipt={'checks':[],'maximum_pixel_discrepancy':0,'page_errors':[]}
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page(viewport={'width':1280,'height':720},reduced_motion='reduce');page.on('pageerror',lambda e:receipt['page_errors'].append(str(e)));expect.set_options(timeout=30000)
 try:
  page.goto('http://127.0.0.1:8766');page.wait_for_function("document.documentElement.dataset.ready==='true'");page.locator('#explore-public').click();expect(page.locator('[data-effect-gene]')).to_have_count(20)
  for theme in ('light','dark'):
   page.locator('#theme').select_option(theme)
   for w,h in ((1280,720),(1440,900),(390,844),(720,450)):
    page.set_viewport_size({'width':w,'height':h});d=page.evaluate('''()=>{
      const axis=document.querySelector('.effect-axis svg'),labels=[...axis.querySelectorAll('text')],left=Number(labels[0].getAttribute('x')),right=Number(labels[2].getAttribute('x')),lo=Number(labels[0].textContent),hi=Number(labels[2].textContent),ctm=axis.getScreenCTM();
      const point=(x,m)=>new DOMPoint(x,12).matrixTransform(m).x;
      const errors=[...document.querySelectorAll('[data-source-g],[data-target-g]')].map(mark=>{const value=Number(mark.dataset.sourceG??mark.dataset.targetG),x=Number(mark.getAttribute(mark.tagName==='circle'?'cx':'x'))+(mark.tagName==='circle'?0:4),actual=point(x,mark.ownerSVGElement.getScreenCTM()),expected=point(left+(value-lo)/(hi-lo)*(right-left),ctm);return Math.abs(actual-expected)});
      return {marks:errors.length,max:Math.max(...errors),anchors:labels.every(e=>e.getAttribute('text-anchor')==='middle')}
    }''');assert d['marks']==40 and d['max']<.01 and d['anchors'],d;receipt['maximum_pixel_discrepancy']=max(receipt['maximum_pixel_discrepancy'],d['max']);receipt['checks'].append({'id':f'ALL40_EFFECT_POSITIONS_ALIGN_TO_ACTUAL_AXIS_{theme}_{w}','status':'PASS','details':d})
  # Unselected trace guard has a direct, working return to the real gene list.
  page.set_viewport_size({'width':1280,'height':720});page.locator('#wordmark [data-view="evidence"]').click();expect(page.locator('#trace-choose-gene')).to_be_visible();page.locator('#trace-choose-gene').click();expect(page.locator('[data-effect-gene]')).to_have_count(20);receipt['checks'].append({'id':'UNSELECTED_TRACE_DIRECT_GENE_RECOVERY','status':'PASS'})
  assert not receipt['page_errors'];receipt['status']='PASS'
 except Exception as e:receipt['status']='FAIL';receipt['failure']=str(e);raise
 finally:(OUT/'geometry_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');b.close()
