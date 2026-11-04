"""Exercise the original upload wizard with explicit test fixtures, no mocked APIs."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]


def main(url,out):
    out.mkdir(parents=True,exist_ok=True);expect.set_options(timeout=90000)
    results=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        for mode in ('evaluate_predictions','diagnose_shift','train_validate'):
            context=browser.new_context(viewport={'width':1440,'height':1000})
            page=context.new_page();page.set_default_timeout(90000);page.goto(url)
            page.wait_for_function("document.documentElement.dataset.ready === 'true'")
            page.locator('#own-data').click();page.locator('[data-start-task="'+mode+'"]').click()
            page.locator('#study-name').fill('Recovery '+mode)
            if mode=='evaluate_predictions':
                folder=ROOT/'examples/design3_prediction_fixtures/equipment_faults'
                page.locator('#file-predictions').set_input_files(folder/'predictions.csv')
                page.locator('#setup-next').click()
                page.locator('#file-prediction_manifest').set_input_files(folder/'manifest.json')
                page.locator('#setup-next').click()
            else:
                folder=ROOT/'examples/synthetic_valid'
                for role in ('source','target'):
                    for key,name in (('expression','expression.csv'),('metadata','samples.csv')):
                        page.locator(f'#file-{role}_{key}').set_input_files(folder/f'{role}_{name}')
                page.locator('#setup-next').click()
                for role in ('source','target'):
                    page.locator(f'#file-{role}_manifest').set_input_files(folder/f'{role}_manifest.json')
                page.locator('#setup-next').click();page.locator('#setup-next').click()
            expect(page.locator('#data-entry')).to_have_attribute('data-step','4')
            page.locator('#setup-next').click()
            expect(page.locator('#status-live')).to_contain_text('File checks passed',timeout=180000)
            page.locator('#setup-next').click()
            view='cohorts' if mode=='diagnose_shift' else 'ace'
            expect(page.locator('#view-'+view)).to_be_visible(timeout=180000)
            expect(page.locator('#status-live')).to_contain_text('saved',timeout=180000)
            page.screenshot(path=str(out/(mode+'.png')),full_page=True)
            snapshot=page.locator('#view-'+view).inner_text()
            (out/(mode+'.txt')).write_text(snapshot,encoding='utf-8')
            results.append({'mode':mode,'fixture':str(folder.relative_to(ROOT)),'status':'PASS'})
            context.close()
        browser.close()
    (out/'upload-verification.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--url',required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();main(a.url,a.out)
