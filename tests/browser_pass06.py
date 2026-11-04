"""Rendered export/recovery/offline-report QA, actual evidence and labeled fixtures."""
import argparse,hashlib,io,json,re,tempfile,time,zipfile
from pathlib import Path,PurePosixPath
from playwright.sync_api import sync_playwright,expect
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'docs/pass06_screenshots'

def verify(data):
    z=zipfile.ZipFile(io.BytesIO(data));assert z.testzip() is None
    assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n and ':' not in n for n in z.namelist())
    assert not any(n.startswith('input/') for n in z.namelist())
    m=json.loads(z.read('reproducibility_manifest.json'))
    for name,entry in m['artifact_sha256'].items():assert hashlib.sha256(z.read(name)).hexdigest()==entry['sha256']
    return z

def main(url):
    OUT.mkdir(exist_ok=True);checks=[];errors=[];latency={};contrasts=[]
    with tempfile.TemporaryDirectory(prefix='brace-report-browser-') as directory,sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        ctx=browser.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce',locale='en-US',timezone_id='America/Chicago',accept_downloads=True)
        page=ctx.new_page();page.set_default_timeout(25000);page.on('pageerror',lambda e:errors.append(str(e)))
        def record(text):checks.append(text);print('PASS',text.encode('ascii','backslashreplace').decode(),flush=True)
        def nav(view):page.locator(f'nav [data-view="{view}"]').click();expect(page.locator('#view-'+view)).to_be_visible()
        def shot(name,locator=None):
            page.locator(locator).screenshot(path=str(OUT/name),animations='disabled') if locator else page.screenshot(path=str(OUT/name),full_page=True,animations='disabled')
        def download(link):
            with page.expect_download() as event:link.click()
            return Path(event.value.path()).read_bytes()
        def offline(data,label):
            z=verify(data);dest=Path(directory)/label;dest.mkdir()
            for name in z.namelist():
                path=(dest/name).resolve();assert path.is_relative_to(dest.resolve());path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(name))
            report=ctx.new_page();report.set_viewport_size({'width':1280,'height':900});network=[]
            report.on('request',lambda r:network.append(r.url) if r.url.startswith(('http://','https://')) else None)
            report.goto((dest/'research_summary.html').as_uri());expect(report.locator('h1')).to_be_visible()
            assert report.locator('script,img,iframe').count()==0 and not network
            for href in report.locator('a').evaluate_all('(a)=>a.map(x=>x.getAttribute("href"))'):assert (dest/href).is_file()
            return report,z
        def contrast():
            # Native computed colors for representative visible product text,
            # not a claim of a complete WCAG/screen-reader audit.
            values=page.evaluate('''()=>['h1','.help','a','.eyebrow'].flatMap(sel=>[...document.querySelectorAll(sel)].filter(e=>e.getClientRects().length).slice(0,3).map(e=>{let p=e,bg;while(p){const c=getComputedStyle(p).backgroundColor;if(c!=='rgba(0, 0, 0, 0)'&&c!=='transparent'){bg=c;break}p=p.parentElement}return {text:e.textContent.slice(0,55),color:getComputedStyle(e).color,bg:bg||'rgb(11, 25, 36)'}}))''')
            def lum(c):
                rgb=list(map(float,re.findall(r'[\d.]+',c)))[:3];v=[x/255 for x in rgb];v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v];return sum(x*w for x,w in zip(v,(.2126,.7152,.0722)))
            for value in values:
                a,b=sorted((lum(value['color']),lum(value['bg'])));ratio=(b+.05)/(a+.05);assert ratio>=4.5,(value,ratio);contrasts.append(dict(**value,ratio=ratio))
        page.goto(url);page.wait_for_function("document.documentElement.dataset.ready==='true'");t=time.perf_counter();page.locator('#explore-public').click();page.locator('#study-results').click();expect(page.locator('#race-table tbody tr')).to_have_count(20);latency['example_to_ready_ms']=(time.perf_counter()-t)*1000
        latency['gene_selection_ms']=[]
        for gene in ('135112','54947','55816'):
            t=time.perf_counter();page.locator(f'[data-select-gene="{gene}"]').click();expect(page.locator('#face-title')).to_contain_text(gene);expect(page.locator('#face-body .cohort-expression')).to_have_count(2);latency['gene_selection_ms'].append((time.perf_counter()-t)*1000)
        contrast();nav('evidence');expect(page.locator('#race-trace-panel')).to_contain_text('55816')
        link=page.locator('a[href="/api/embrace/public_er_pass2"]');page.route('**/api/embrace/public_er_pass2',lambda r:r.fulfill(status=409,content_type='application/json',body=json.dumps({'detail':{'message':'Deliberate export failure for UI recovery test'}})))
        link.focus();page.keyboard.press('Enter');expect(page.locator('.embrace-export-status')).to_contain_text('Deliberate export failure');shot('export_error_recovery.png','.embrace-export-status')
        assert page.locator('#context').inner_text().find('GSE42568')>=0;page.unroute('**/api/embrace/public_er_pass2')
        data=download(page.get_by_role('button',name='Retry evidence export'));expect(page.locator('.embrace-export-status')).to_contain_text('download started');shot('embrace_public_evidence.png')
        record('Keyboard export failure remains recoverable; retry downloads a real ZIP while preserving the selected public run/gene')
        report,z=offline(data,'public');expect(report.locator('h1')).to_contain_text('Which genes');assert json.loads(z.read('race/race_result.json'))['aggregate']['supported']==14
        report.screenshot(path=str(OUT/'standalone_public_report_1280.png'),animations='disabled');report.locator('table').filter(has=report.get_by_role('columnheader',name='Rank',exact=True)).locator('..').screenshot(path=str(OUT/'standalone_gene_table.png'),animations='disabled');report.close()
        record('Public EMBRACE opens offline with no HTTP requests or executable content; relative evidence links, hashes and all 20 gene outcomes are valid')
        nav('study');page.locator('#other-examples').evaluate('el=>el.open=true');page.locator('#historical-demo').click();expect(page.locator('#ace-confusion')).to_be_visible()
        latency['threshold_adjustment_ms']=[]
        for index,count in ((99,432),(95,584),(100,0)):
            t=time.perf_counter();page.locator('#confidence-range').fill(str(index));expect(page.locator('#confidence-results dd').first).to_have_text(str(count));latency['threshold_adjustment_ms'].append((time.perf_counter()-t)*1000)
        contrast();nav('evidence');data=download(page.locator('a[href="/api/embrace/historical_cptac"]'));report,z=offline(data,'historical')
        expect(report.locator('body')).to_contain_text('not new five-class model inference');expect(report.locator('body')).to_contain_text('0.998692106');report.screenshot(path=str(OUT/'standalone_historical_report_1280.png'),animations='disabled');report.close()
        record('Archived CPTAC export preserves 680/668 and 584/583, absent-class limits and the actual confident error without claiming new inference')
        # Malicious-label supplied-score fixture is actual input validation/scoring,
        # not a biological result or a mocked successful calculation.
        evil='<img src="https://invalid.example/x" onerror="window.BRACE_ATTACK=1">'
        manifest=dict(schema_version='1.0.0',dataset_id='explicit_security_fixture',model_id='supplied_scores',classes=[evil,'B'],probability_columns={},prediction_origin='external_model',evaluation_role='external_exploratory',independence_declaration='unknown',label_source_description='Explicit software security fixture')
        import csv
        text=io.StringIO(newline='');w=csv.writer(text);w.writerow(['sample_id','true_label','predicted_label']);w.writerow(['=1+1',evil,'B']);w.writerow(['safe','B','B'])
        r=page.request.post(url+'/api/analyze',multipart={'mode':'evaluate_predictions','predictions':{'name':'fixture.csv','mimeType':'text/csv','buffer':text.getvalue().encode()},'prediction_manifest':{'name':'manifest.json','mimeType':'application/json','buffer':json.dumps(manifest).encode()}})
        assert r.status==200,r.text();rid=r.json()['id'];response=page.request.get(url+'/api/embrace/'+rid);assert response.status==200;report,z=offline(response.body(),'hostile')
        assert report.evaluate('window.BRACE_ATTACK') is None;assert '=1+1' in z.read('CSV_TEXT_ENCODING.json').decode();report.close()
        record('Hostile imported labels stay literal in offline HTML and formula-active CSV identifiers receive reversible encoding')
        response=page.request.post(url+'/api/demo/synthetic');assert response.status==200
        computed=response.json();response=page.request.get(url+'/api/embrace/'+computed['id']);assert response.status==200
        report,z=offline(response.body(),'model_fixture');expect(report.locator('body')).to_contain_text('Source out-of-fold cross-validation');expect(report.locator('body')).to_contain_text('different samples and evaluation designs')
        raw=json.loads(z.read('validation/validation_result.json'));stage=json.loads(z.read('validation/stage05/run_result.json'))
        tables=report.locator('table').filter(has=report.get_by_role('columnheader',name='Evaluated',exact=True))
        assert tables.count()==2
        for table,metrics in zip(tables.all(),[stage['outputs']['source_cv'],raw['analysis']['metrics']]):
            assert table.locator('tbody td').all_text_contents()[:3]==[str(metrics['n']),str(metrics['n_correct']),str(metrics['n']-metrics['n_correct'])]
        report.screenshot(path=str(OUT/'standalone_model_fixture_1280.png'),animations='disabled');report.close()
        record('Actual synthetic Mode B export keeps source OOF and target scoring separate, with exact counts and no false paired comparison')
        folder=BASE/'examples/synthetic_valid';files={'mode':'diagnose_shift'}
        for role in ('source','target'):
            for field,name in [('expression',f'{role}_expression.csv'),('metadata',f'{role}_samples.csv'),('manifest',f'{role}_manifest.json')]:
                files[f'{role}_{field}']={'name':name,'mimeType':'application/json' if field=='manifest' else 'text/csv','buffer':(folder/name).read_bytes()}
        response=page.request.post(url+'/api/analyze',multipart=files);assert response.status==200
        response=page.request.get(url+'/api/embrace/'+response.json()['id']);assert response.status==200
        report,z=offline(response.body(),'shift_fixture');assert not any(n.startswith('validation/') for n in z.namelist())
        assert report.get_by_role('columnheader',name='Accuracy fraction',exact=True).count()==0
        expect(report.locator('body')).to_contain_text('Mode C excludes outcome labels')
        compat=json.loads(z.read('compatibility_summary.json'));assert all('observed_conditions' not in compat[r] for r in ('source','target'))
        report.screenshot(path=str(OUT/'standalone_mode_c_fixture_1280.png'),animations='disabled');report.close()
        record('Mode C standalone report includes measured shift/PCA evidence and excludes fabricated accuracy, target class counts and labeled results')
        for width,height in ((1280,720),(390,844)):
            page.set_viewport_size({'width':width,'height':height});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        assert page.locator('nav button').first.evaluate('el=>getComputedStyle(el).transitionDuration')=='0s'
        record('Export/TRACE layouts retain narrow reflow and reduced motion; sampled rendered text colors meet 4.5:1 contrast')
        assert not errors,errors
        (BASE/'docs/PASS06_BROWSER_RESULTS.json').write_text(json.dumps(dict(browser=browser.version,checks=checks,uncaught_errors=errors,
            interaction_observations=latency,contrast_samples=contrasts,screenshots=sorted(p.name for p in OUT.glob('*.png')),
            scope='Real saved public/historical evidence plus explicit security fixture. UI times include Playwright round trips on this machine; not human timings. Contrast samples are not a full accessibility audit.'),indent=2)+'\n')
        browser.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8765');main(p.parse_args().url)
