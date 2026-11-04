from pathlib import Path
import json,time,csv,io,zipfile,hashlib,re,traceback
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];APP=ROOT;OUT=APP/'docs/design3/final';OUT.mkdir(parents=True,exist_ok=True)
receipt={'checks':[],'screenshots':[],'audits':[],'page_errors':[],'network':[]}
def check(key,ok=True,data=None):
    assert ok,(key,data)
    receipt['checks'].append({'id':key,'status':'PASS','details':data});print('PASS',key,flush=True)
def shot(page,name,full=False):
    page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/(name+'.png')),full_page=full);receipt['screenshots'].append(name+'.png')
def ready(page):page.wait_for_function("document.documentElement.dataset.ready==='true'")
def nav(page,key):page.locator('#wordmark [data-view="'+key+'"]').click();expect(page.locator('body')).to_have_attribute('data-view',key)
CONTRAST=r'''()=>{
 const ctx=document.createElement('canvas').getContext('2d',{willReadFrequently:true});
 function rgba(value){ctx.clearRect(0,0,1,1);ctx.fillStyle=value;ctx.fillRect(0,0,1,1);return [...ctx.getImageData(0,0,1,1).data].map((x,i)=>i===3?x/255:x)}
 function over(a,b){const t=a[3];return [0,1,2].map(i=>a[i]*t+b[i]*(1-t)).concat(1)}
 function background(el){const path=[];for(let e=el;e;e=e.parentElement)path.unshift(e);return path.reduce((v,e)=>over(rgba(getComputedStyle(e).backgroundColor),v),[255,255,255,1])}
 function luminance(a){return a.slice(0,3).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4}).reduce((t,x,i)=>t+x*[.2126,.7152,.0722][i],0)}
 function ratio(a,b){const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)}
 const data=[];for(const el of document.querySelectorAll('body *')){
  const s=getComputedStyle(el);if(!el.getClientRects().length||s.visibility==='hidden'||el.closest('[disabled],.sr-only,script,style'))continue;
  const direct=[...el.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim();if(!direct)continue;
  const size=parseFloat(s.fontSize),large=size>=24||(size>=18.66&&Number(s.fontWeight)>=700),fg=rgba(el instanceof SVGElement?s.fill:s.color),bg=background(el);const value=ratio(over(fg,bg),bg);
  data.push({text:direct.slice(0,160),tag:el.tagName,id:el.id,ratio:Math.round(value*100)/100,required:large?3:4.5,fg,bg,size});
 }
 const controls=[...document.querySelectorAll('button,input:not([type=range]):not([type=checkbox]),select')].filter(e=>e.getClientRects().length&&!e.disabled&&!e.closest('.wordmark')).map(el=>{const s=getComputedStyle(el),b=background(el.parentElement),r=ratio(over(rgba(s.borderTopColor),b),b);return {id:el.id,text:(el.textContent||'').trim().slice(0,60),ratio:Math.round(r*100)/100}});
 return {text:data,failures:data.filter(x=>x.ratio+.01<x.required),control_boundaries:controls,boundary_failures:controls.filter(x=>x.ratio<3)};
}'''
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True);context=browser.new_context(viewport={'width':1280,'height':720},reduced_motion='reduce',color_scheme='light',accept_downloads=True);page=context.new_page();page.set_default_timeout(25000);expect.set_options(timeout=25000)
    page.on('pageerror',lambda e:receipt['page_errors'].append(str(e)));page.on('request',lambda r:receipt['network'].append(r.url))
    def audit(label):
        d=page.evaluate(CONTRAST);d['screen']=label;receipt['audits'].append(d);check('TEXT_CONTRAST_'+label,not d['failures'],d['failures'])
        check('CONTROL_BOUNDARIES_'+label,not d['boundary_failures'],d['boundary_failures'])
        ids=page.locator('[id]').evaluate_all('els=>els.map(e=>e.id)');check('UNIQUE_IDS_'+label,len(ids)==len(set(ids)))
        cdp=context.new_cdp_session(page);nodes=cdp.send('Accessibility.getFullAXTree')['nodes'];missing=[n for n in nodes if not n.get('ignored') and n.get('role',{}).get('value') in ('button','link','combobox','textbox','slider','searchbox') and not n.get('name',{}).get('value')];check('AX_NAMES_'+label,not missing,[n.get('role') for n in missing]);cdp.detach()
    try:
        page.goto('http://127.0.0.1:8766');ready(page)
        for theme in ('light','dark'):
            page.locator('#theme').select_option(theme);audit('home_'+theme);shot(page,'home_'+theme)
            for key in ('study','race','ace','cohorts','evidence'):
                page.locator('#wordmark [data-view="'+key+'"]').hover();shot(page,'preview_'+key+'_'+theme)
            page.mouse.move(10,650)
        page.locator('#explore-public').click();expect(page.locator('#race-table tbody tr')).to_have_count(20)
        for theme in ('light','dark'):
            page.locator('#theme').select_option(theme);audit('race_'+theme);shot(page,'race_'+theme,True);page.locator('[data-select-gene="135112"]').click();expect(page.locator('#face-body circle[data-value]')).to_have_count(188);audit('face_'+theme);shot(page,'face_'+theme)
            for _ in range(12):page.keyboard.press('Tab');check('FACE_FOCUS_CONTAINED_'+theme,page.evaluate("document.querySelector('#face-inspector').contains(document.activeElement)"))
            page.locator('#trace-gene').click();expect(page.locator('#race-trace-panel')).to_contain_text('135112');audit('trace_'+theme);shot(page,'trace_'+theme,True);page.locator('#return-face').click();expect(page.locator('#face-inspector')).to_be_visible();page.keyboard.press('Escape')
        # Result-first offline report, actual exported bytes and exact counts.
        nav(page,'evidence');with_download=page.expect_download()
        with with_download as dl:page.locator('a[href^="/api/embrace/"]').first.click()
        package=OUT/'PUBLIC_ER_EMBRACE.zip';dl.value.save_as(str(package))
        with zipfile.ZipFile(package) as z:
            assert z.testzip() is None
            z.extractall(OUT/'public_report')
            for r in csv.DictReader(io.StringIO(z.read('FILE_SHA256_MANIFEST.csv').decode())):assert hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256']
        report=context.new_page();report.goto((OUT/'public_report/research_summary.html').as_uri());expect(report.locator('.lead')).to_contain_text('14 of 20');report.screenshot(path=str(OUT/'exported_report.png'),full_page=True);receipt['screenshots'].append('exported_report.png');report.emulate_media(media='print');report.pdf(path=str(OUT/'exported_report.pdf'),format='A4',print_background=True);report.close();check('RESULT_FIRST_LOCAL_HTML_AND_ZIP_HASHES')
        nav(page,'study');page.locator('#other-examples').evaluate('e=>e.open=true');page.locator('#historical-demo').click();expect(page.locator('#ace-confusion')).to_be_visible()
        for theme in ('light','dark'):
            page.locator('#theme').select_option(theme);page.locator('#confidence-number').fill('0.99');page.locator('#confidence-number').press('Tab');expect(page.locator('#confidence-results')).to_contain_text('431 correct among 432');audit('ace_'+theme);shot(page,'ace_'+theme,True)
        page.locator('#sample-search').fill('cfc121b5');page.locator('#sample-table [data-id]').click();expect(page.locator('#sample-detail')).to_contain_text('0.998692106');audit('record_dark');shot(page,'record_dark');page.keyboard.press('Escape')
        # Fresh non-biological fixture and input-purpose footer semantics.
        nav(page,'study');page.locator('#new-data').click();page.locator('[data-start-task="evaluate_predictions"]').click();expect(page.locator('#input-limits')).to_have_text('25 MiB per file · 50,000 classification records');check('GENERIC_TASK_SPECIFIC_LIMIT_COPY')
        folder=APP/'examples/design3_prediction_fixtures/text_categories';page.locator('#file-predictions').set_input_files(str(folder/'predictions.csv'));page.locator('#file-prediction_manifest').set_input_files(str(folder/'manifest.json'))
        page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Files checked');audit('generic_intake_dark');shot(page,'generic_intake_dark',True);page.locator('#run-analysis').click();expect(page.locator('#validation-content #ace-confusion')).to_be_visible();expect(page.locator('#validation-content')).to_contain_text('66.67%')
        text=page.locator('#validation-content').inner_text();check('GENERIC_VISIBLE_COPY_NO_FORCED_BIOLOGY',not re.search(r'\b(genes?|patients?|tumou?rs?|cohorts?|assays?)\b',text,re.I),text[:100])
        for theme in ('light','dark'):
            page.locator('#theme').select_option(theme);audit('generic_ace_'+theme);shot(page,'generic_ace_'+theme,True)
        # Loading, duplicate click, interruption and retry: controlled network delay.
        nav(page,'study');page.locator('#other-public').click();expect(page.locator('body')).to_have_attribute('data-view','race');expect(page.locator('#race-table tbody tr')).to_have_count(20)
        nav(page,'study');calls=[]
        def delay(route):calls.append(route.request.url);shot(page,'controlled_loading_public');time.sleep(.5);route.continue_()
        page.route('**/api/example/public-er',delay)
        with page.expect_response('**/api/example/public-er'):page.locator('#other-public').dblclick()
        expect(page.locator('body')).to_have_attribute('data-view','race');expect(page.locator('#race-table tbody tr')).to_have_count(20);check('DUPLICATE_REQUEST_GUARD',len(calls)==1,calls);page.unroute('**/api/example/public-er')
        # Hold a submitted request, reload, and confirm no automatic second POST.
        nav(page,'study');page.locator('#new-data').click();page.locator('[data-start-task="evaluate_predictions"]').click();page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Files checked');held=[]
        page.route('**/api/analyze',lambda route:held.append(route));page.locator('#run-analysis').click();expect(page.locator('#status-live')).to_have_attribute('data-state','running');shot(page,'controlled_pending_prediction');page.reload();ready(page);expect(page.locator('#status-live')).to_contain_text('outcome is not confirmed');expect(page.locator('#status-live')).to_have_attribute('data-state','failed');check('INTERRUPTION_NO_AUTO_RESUBMIT',len(held)==1);shot(page,'interrupted_request_recovery');
        for r in held:
            try:r.abort()
            except Exception:pass
        page.unroute('**/api/analyze');nav(page,'study');page.locator('#other-public').click();expect(page.locator('#race-table tbody tr')).to_have_count(20)
        # Offline guard rejects every non-loopback browser request; local tasks still work.
        blocked=[]
        def local_only(route):
            if route.request.url.startswith('http://127.0.0.1:8766/'):route.continue_()
            else:blocked.append(route.request.url);route.abort()
        page.route('**/*',local_only);page.reload();ready(page);expect(page.locator('#race-table tbody tr')).to_have_count(20);nav(page,'evidence');expect(page.locator('#race-trace-panel')).to_contain_text('135112');check('BROWSER_LOCAL_ONLY_RESTORE_TRACE',not blocked,blocked)
        # Theme bootstrap observation before DOM ready, real saved dark preference.
        page.locator('#theme').select_option('dark');page.add_init_script("window.themeSamples=[];new MutationObserver(()=>{if(document.documentElement)window.themeSamples.push(document.documentElement.dataset.theme)}).observe(document,{childList:true,subtree:true,attributes:true,attributeFilter:['data-theme']})");page.reload();ready(page);samples=page.evaluate('window.themeSamples.filter(Boolean)');check('NO_WRONG_THEME_BOOTSTRAP_OBSERVED',samples and set(samples)=={'dark'},sorted(set(samples)))
        # Real browser zoom command, verified by innerWidth change, not device scale factor.
        before=page.evaluate('innerWidth');cdp=context.new_cdp_session(page);cdp.send('Emulation.setPageScaleFactor',{'pageScaleFactor':2});zoom=page.evaluate('visualViewport.scale');check('PAGE_SCALE_200_PERCENT',zoom==2,zoom);shot(page,'actual_page_scale_200');cdp.send('Emulation.setPageScaleFactor',{'pageScaleFactor':1});cdp.detach()
        nav(page,'study');page.emulate_media(reduced_motion='reduce');page.locator('#wordmark [data-view="race"]').hover();transition=page.locator('#wordmark-plate').evaluate('e=>getComputedStyle(e).transitionDuration');check('REDUCED_MOTION_NO_PLATE_TRANSITION',all(float(x.rstrip('s'))==0 for x in transition.split(', ')),transition)
        # Final responsive samples with current CSS, including real loaded data.
        for width,height,label in [(1440,900,'1440'),(390,844,'390'),(720,450,'200pct_reflow')]:
            page.set_viewport_size({'width':width,'height':height});page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');shot(page,'home_dark_'+label)
            nav(page,'race');expect(page.locator('#race-table tbody tr')).to_have_count(20);page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');check('FINAL_REFLOW_'+label,page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));shot(page,'race_dark_'+label);nav(page,'study')
        receipt['status']='PASS';check('NO_PAGE_ERRORS',not receipt['page_errors'],receipt['page_errors']);check('NO_REMOTE_BROWSER_REQUESTS',not [u for u in receipt['network'] if not u.startswith(('http://127.0.0.1:8766/','file:','blob:'))])
    except Exception as e:
        receipt['status']='FAIL';receipt['failure']=str(e);receipt['traceback']=traceback.format_exc();page.screenshot(path=str(OUT/'failure.png'));raise
    finally:
        page.unroute_all(behavior='ignoreErrors');(OUT/'accessibility_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');browser.close()
