"""Equivalent-state main/recovery static comparison using the same real backend."""
import argparse,json,mimetypes,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]


def main(url,out):
    out.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        counts={}
        for version in ('original','recovered'):
            context=browser.new_context(viewport={'width':1440,'height':1000},color_scheme='light')
            if version=='original':
                def original(route):
                    path=route.request.url.split(url.rstrip('/'),1)[-1].split('?',1)[0]
                    relative='brace_app/static/'+(path[len('/assets/'):] if path.startswith('/assets/') else 'index.html')
                    data=subprocess.check_output(['git','show','main:'+relative],cwd=ROOT)
                    mime='text/javascript' if relative.endswith('.js') else mimetypes.guess_type(relative)[0] or 'application/octet-stream'
                    route.fulfill(body=data,content_type=mime)
                context.route(url.rstrip('/')+'/',original);context.route('**/assets/**',original)
            page=context.new_page();page.goto(url)
            page.wait_for_function("document.documentElement.dataset.ready === 'true'")
            runs=page.request.get(url+'/api/runs').json()['runs'];counts[version]=len(runs)
            if runs:page.locator('#home-history').wait_for(state='visible')
            for width in (1440,390):
                page.set_viewport_size({'width':width,'height':1000})
                for theme in ('light','dark'):
                    page.locator('#theme').select_option(theme);page.mouse.move(0,0)
                    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                    page.screenshot(path=str(out/f'{version}-home-{width}-{theme}.png'),full_page=True,animations='disabled')
            context.close()
        assert counts['original']==counts['recovered'],counts
        browser.close()
    (out/'visual-comparison.json').write_text(json.dumps({'saved_run_counts':counts,'sizes':[1440,390],
        'themes':['light','dark'],'baseline':'Exact main static bytes, same live dev.2 backend; no API mocks'},indent=2),encoding='utf-8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url',required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();main(a.url,a.out)
