"""Real-browser recovery acceptance; requests use a real isolated BRACE server.

Usage: python scripts/recovery_browser.py --url http://127.0.0.1:8911 --out .work/recovery/browser
Only original static assets are intercepted for the baseline comparison. No API is mocked.
"""
import argparse
import hashlib
import json
import mimetypes
from pathlib import Path
import subprocess
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]


def main(url, out):
    out.mkdir(parents=True, exist_ok=True)
    expect.set_options(timeout=90000)
    results=[]; errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context(viewport={'width':1440,'height':1000},color_scheme='light')
        page=context.new_page();page.set_default_timeout(90000)
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(url);page.wait_for_function("document.documentElement.dataset.ready === 'true'")
        expect(page.locator('#landing')).to_be_visible()
        expect(page.locator('#workspace-datasets')).not_to_be_visible()
        for width in (1440,390):
            page.set_viewport_size({'width':width,'height':1000})
            for theme in ('light','dark'):
                page.locator('#theme').select_option(theme)
                page.mouse.move(0,0)
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                page.screenshot(path=str(out/f'recovered-home-{width}-{theme}.png'),full_page=True,animations='disabled')
        page.set_viewport_size({'width':1440,'height':1000});page.locator('#theme').select_option('light')
        page.locator('#open-space').click();expect(page.locator('#space-dialog')).to_be_visible()
        expect(page.locator('#space-question')).to_be_focused()
        page.screenshot(path=str(out/'space-open.png'),full_page=True)
        page.locator('#space-question').fill('GSE42568')
        page.locator('#space-question').press('Escape')
        expect(page.locator('#space-dialog')).not_to_be_visible()
        expect(page.locator('#open-space')).to_be_focused()
        results.append('SPACE toolbar click, initial focus, Escape and focus restoration')
        page.locator('#open-datasets').click();expect(page.locator('#workspace-datasets')).to_be_visible()
        page.locator('#registry-space').click();expect(page.locator('#space-dialog')).to_be_visible()
        page.locator('#close-space').click()
        with page.expect_response(lambda r:'/api/datasets/reviewed-public' in r.url,timeout=180000) as prepared:
            page.locator('#registry-public').click()
        assert prepared.value.ok,prepared.value.text()
        expect(page.locator('#registry-source')).not_to_have_value('')
        page.locator('#registry-name').fill('Recovery browser public ER')
        page.locator('#registry-processing-review').check();page.locator('#registry-review').check()
        page.locator('#registry-check').click();expect(page.locator('#registry-run')).to_be_enabled(timeout=180000)
        with page.expect_response(lambda r:'/api/dataset-analysis/run' in r.url,timeout=240000) as computed:
            page.locator('#registry-run').click()
        run=computed.value.json();assert computed.value.ok,run
        expect(page.locator('#view-race')).to_be_visible()
        assert run['race']['aggregate']['selected']==20,run['race']['aggregate']
        (out/'computed-run.json').write_text(json.dumps(run,indent=2),encoding='utf-8')
        page.screenshot(path=str(out/'race-result.png'),full_page=True)
        results.append('Reviewed public registry → declared contrast → eligibility → real RACE computation')
        for view in ('ace','cohorts','evidence','study','race'):
            page.locator(f'#wordmark button[data-view="{view}"]').click()
            expect(page.locator(f'#view-{view}')).to_be_visible()
            page.screenshot(path=str(out/f'view-{view}.png'),full_page=True)
        page.locator('#wordmark button[data-view="evidence"]').click()
        export=page.locator('a[href="/api/embrace/'+run['id']+'"]')
        assert export.count()>0
        with page.expect_download(timeout=180000) as downloaded:export.first.click()
        downloaded.value.save_as(out/'EMBRACE.zip')
        results.append('Original navigation and real EMBRACE export')
        page.reload();page.wait_for_function("document.documentElement.dataset.ready === 'true'")
        expect(page.locator('#status-live')).not_to_contain_text('could not be restored')
        results.append('Saved result restoration after reload')
        # A genuinely missing workbench module must not make SPACE inert.
        isolated=browser.new_context(viewport={'width':1440,'height':1000})
        isolated.route('**/assets/app.js',lambda route:route.abort())
        failure=isolated.new_page();failure.goto(url)
        failure.locator('#open-space').click();expect(failure.locator('#space-dialog')).to_be_visible()
        expect(failure.get_by_role('alert')).to_contain_text('Workbench could not start')
        failure.screenshot(path=str(out/'space-with-workbench-load-failure.png'))
        results.append('Injected missing app.js: SPACE still opens; startup failure visible')
        isolated.close()
        # Render exact original main static bytes against the same real backend.
        baseline=browser.new_context(viewport={'width':1440,'height':1000},color_scheme='light')
        def original(route):
            path=route.request.url.split(url.rstrip('/'),1)[-1].split('?',1)[0]
            relative='brace_app/static/'+(path[len('/assets/'):] if path.startswith('/assets/') else 'index.html')
            data=subprocess.check_output(['git','show','main:'+relative],cwd=ROOT)
            mime='text/javascript' if relative.endswith('.js') else mimetypes.guess_type(relative)[0] or 'application/octet-stream'
            route.fulfill(body=data,content_type=mime)
        baseline.route(url.rstrip('/')+'/',original);baseline.route('**/assets/**',original)
        old=baseline.new_page();old.goto(url);old.wait_for_function("document.documentElement.dataset.ready === 'true'")
        for width in (1440,390):
            old.set_viewport_size({'width':width,'height':1000})
            for theme in ('light','dark'):
                old.locator('#theme').select_option(theme)
                old.mouse.move(0,0)
                old.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                old.screenshot(path=str(out/f'original-home-{width}-{theme}.png'),full_page=True,animations='disabled')
        assert not errors,errors
        browser.close()
    (out/'browser-verification.json').write_text(json.dumps({'url':url,'passed':results,'page_errors':errors,
        'scope':'Real backend; baseline swaps only exact main static assets. Live GEO and installer acceptance are separate.'},indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();main(args.url,args.out)
