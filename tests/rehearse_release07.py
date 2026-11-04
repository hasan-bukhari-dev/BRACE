"""Ten real rendered flagship runs. Developer automation, never human-user evidence.

Run against the release launcher with tests/offline_guard on its PYTHONPATH.
Non-loopback browser HTTP requests are denied too. No mocked science or sleeps
standing in for result completion. Uses installed Chrome via developer Playwright.
"""
import argparse,csv,hashlib,io,json,math,tempfile,time,zipfile
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect
BASE=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def equal(a,b):
    if isinstance(a,float):assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12),(a,b)
    elif isinstance(a,dict):
        assert a.keys()==b.keys()
        for key in a:
            if key!='hypothesis_hash':equal(a[key],b[key])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):equal(x,y)
    else:assert a==b,(a,b)
def main(url,record,output):
    output.mkdir(parents=True,exist_ok=True);screens=output/'screenshots';screens.mkdir(exist_ok=True)
    prior=json.loads((BASE/'examples/public_er_pair/race_final/race_result.json').read_text())
    iterations=[];errors=[];denied=[];fingerprints=[];last_package=None
    with sync_playwright() as p,tempfile.TemporaryDirectory(prefix='brace-release-report-') as temporary:
        browser=p.chromium.launch(channel='chrome',headless=True)
        for number in range(1,11):
            width,height=(1280,720) if number%2 else (1440,900)
            context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce',accept_downloads=True,locale='en-US',timezone_id='America/Chicago')
            def network(route):
                request=route.request
                if request.url.startswith(('http:','https:')) and urlsplit(request.url).netloc!=urlsplit(url).netloc:
                    denied.append(request.url);route.abort()
                else:route.continue_()
            context.route('**/*',network)
            page=context.new_page();page.set_default_timeout(30000);page.on('pageerror',lambda e:errors.append(str(e)))
            start=time.perf_counter();page.goto(url);page.wait_for_function("document.documentElement.dataset.ready==='true'")
            if number==1:page.screenshot(path=str(screens/'landing_1280.png'),animations='disabled',full_page=True)
            page.locator('#explore-public').focus();page.keyboard.press('Enter');expect(page.locator('#study-results')).to_be_visible()
            saved_ready=time.perf_counter()-start;page.locator('#study-results').click();expect(page.locator('#race-table tbody tr')).to_have_count(20)
            # Fresh public measurements through the actual user intake path.
            page.locator('nav [data-view="study"]').click();page.locator('#new-data').click();page.locator('#task').select_option('race')
            prepared=BASE/'examples/public_er_pair/prepared'
            for role in ('source','target'):
                for field,extension in [('expression','tsv'),('metadata','tsv'),('manifest','json')]:
                    page.locator('#file-'+role+'_'+field).set_input_files(str(prepared/f'{role}_{field}.{extension}'))
            for key,value in [('positive','ER_positive'),('negative','ER_negative'),('positive-definition','Clinically ER-positive primary breast tumor'),('negative-definition','Clinically ER-negative primary breast tumor')]:page.locator('#'+key).fill(value)
            page.locator('#equivalence').check();page.locator('#processing-review').check();check_start=time.perf_counter()
            page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Inputs checked');preflight=time.perf_counter()-check_start
            run_start=time.perf_counter();page.locator('#run-analysis').click();page.wait_for_function("document.querySelector('#status-live').dataset.state==='completed_with_warnings'",timeout=60000)
            expect(page.locator('#race-table tbody tr')).to_have_count(20);run_seconds=time.perf_counter()-run_start
            data=page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');return state.data}")
            equal(data['race']['aggregate'],prior['aggregate']);equal(data['race']['genes'],prior['genes']);assert data['race']['counts']==prior['counts']
            fingerprint=sha(json.dumps(dict(aggregate=data['race']['aggregate'],genes=data['race']['genes']),sort_keys=True).encode());fingerprints.append(fingerprint)
            page.locator('[data-select-gene="135112"]').focus();gene_start=time.perf_counter();page.keyboard.press('Enter');expect(page.locator('#face-body .expression-plot')).to_have_count(2)
            assert page.locator('.expression-plot circle').count()==188;gene_seconds=time.perf_counter()-gene_start
            if number in (1,10):page.screenshot(path=str(screens/f'race_face_{width}.png'),animations='disabled',full_page=True)
            page.locator('#trace-gene').click();expect(page.locator('#race-trace-panel')).to_contain_text('135112');expect(page.locator('#race-trace-panel')).to_contain_text(data['race']['hypothesis_hash'])
            with page.expect_download() as download:page.locator(f'a[href="/api/embrace/{data["id"]}"]').click()
            package=Path(download.value.path()).read_bytes();z=zipfile.ZipFile(io.BytesIO(package));assert z.testzip() is None
            for row in csv.DictReader(io.StringIO(z.read('FILE_SHA256_MANIFEST.csv').decode())):assert sha(z.read(row['path']))==row['sha256']
            equal(json.loads(z.read('race/race_result.json'))['genes'],prior['genes']);last_package=package
            extracted=Path(temporary)/str(number);extracted.mkdir()
            for name in z.namelist():
                dest=(extracted/name).resolve();assert dest.is_relative_to(extracted.resolve());dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
            report=context.new_page();report.goto((extracted/'research_summary.html').as_uri());expect(report.locator('h1')).to_be_visible();assert report.locator('script').count()==0;report.close()
            page.reload();page.wait_for_function("document.documentElement.dataset.ready==='true'");expect(page.locator('#race-trace-panel')).to_contain_text('135112');assert data['id'] in page.locator('#context').inner_text()
            page.locator('nav [data-view="study"]').click();page.locator('#other-examples').evaluate('el=>el.open=true');page.locator('#historical-demo').click();expect(page.locator('#ace-confusion')).to_be_visible()
            cells=page.locator('#target-evidence .ace-metrics dd').all_text_contents() if page.locator('#target-evidence').count() else []
            # Actual saved historical rows, not the real ER specimens.
            archived=page.request.get(url+'/api/example/cptac').json()['validation'];assert archived['n']==680 and archived['metrics']['n_correct']==668
            page.locator('#confidence-range').fill('99');expect(page.locator('#confidence-results dd').first).to_have_text('432')
            page.locator('#confidence-range').fill('95');expect(page.locator('#confidence-results dd').first).to_have_text('584')
            page.locator('[data-scope="errors"]').click() if page.locator('[data-scope="errors"]').count() else None
            if number in (1,10):page.screenshot(path=str(screens/f'ace_{width}.png'),animations='disabled',full_page=True)
            total=time.perf_counter()-start;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            item=dict(iteration=number,viewport=[width,height],status='VERIFIED',run_id=data['id'],saved_example_s=saved_ready,preflight_s=preflight,fresh_race_s=run_seconds,gene_inspection_s=gene_seconds,automated_journey_s=total,scientific_fingerprint=fingerprint,frozen_hypothesis_sha256=data['race']['hypothesis_hash'],zip_sha256=sha(package),zip_bytes=len(package),reload_context_preserved=True,offline_html_opened=True)
            iterations.append(item);print(json.dumps(item),flush=True);context.close()
        assert not errors and not denied,(errors,denied);assert len(set(fingerprints))==1
        output.joinpath('BRACE_EMBRACE_PUBLIC_ER_RELEASE.zip').write_bytes(last_package)
        result=dict(status='VERIFIED',consecutive_successes=len(iterations),failures=0,browser=browser.version,iterations=iterations,uncaught_errors=errors,external_http_attempts=denied,
            scope='Ten automated developer walkthroughs, fresh real intake/RACE each time; alternating two desktop viewports. Application non-loopback sockets denied separately. No physical Wi-Fi/projector or unfamiliar-user claim.',
            prior_numerical_agreement=True,repeated_numerical_identity=True,version_note='Fresh standard Python 3.11.9 changes software provenance and frozen digest from archived Python3.11.2; numeric outputs agree. Saved historical/public evidence remains unchanged.')
        record.parent.mkdir(parents=True,exist_ok=True);record.write_text(json.dumps(result,indent=2)+'\n');browser.close()
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--url',required=True);a.add_argument('--record',type=Path,required=True);a.add_argument('--output',type=Path,required=True);v=a.parse_args();main(v.url,v.record,v.output)
