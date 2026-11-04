from pathlib import Path
import json
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];APP=ROOT;OUT=APP/'docs/design3/final';checks=[]
with sync_playwright() as p:
    b=p.chromium.launch(channel='chrome',headless=True);page=b.new_page(viewport={'width':1280,'height':720},reduced_motion='reduce');expect.set_options(timeout=60000);page.set_default_timeout(60000)
    page.goto('http://127.0.0.1:8766');page.wait_for_function("document.documentElement.dataset.ready==='true'");page.locator('#own-data').click();page.locator('[data-start-task="race"]').click()
    folder=APP/'examples/public_er_pair/prepared'
    for role in ('source','target'):
        for field,ext in [('expression','tsv'),('metadata','tsv'),('manifest','json')]:
            loc=page.locator('#file-'+role+'_'+field)
            if field=='manifest':loc.locator('..').evaluate('e=>e.open=true')
            loc.set_input_files(str(folder/(role+'_'+field+'.'+ext)))
    cfg=json.loads((APP/'examples/public_er_pair/race_config.json').read_text())
    for key in ('positive','negative'):page.locator('#'+key).fill(cfg[key]);page.locator('#'+key+'-definition').fill(cfg['source_conditions'][cfg[key]])
    page.locator('#equivalence').check();page.locator('#processing-review').check()
    for task,title in [('train_validate','source-only expression baseline training'),('diagnose_shift','distribution comparison'),('evaluate_predictions','saved classification prediction evaluation'),('race','gene-expression association tests')]:
        page.locator('#task').focus();page.locator('#task').select_option(task);expect(page.locator('#cohorts-title')).to_have_text('Check inputs for '+title);expect(page.locator('#run-analysis')).to_be_disabled();assert page.locator('#task').evaluate('e=>e===document.activeElement')
        if task!='evaluate_predictions':assert page.locator('#file-source_expression').evaluate('e=>e.files[0].name')=='source_expression.tsv'
        checks.append(task+' heading, check invalidation, retained native file display and focus: PASS')
    for theme in ('light','dark'):
        page.locator('#theme').select_option(theme);page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Files checked for this task');expect(page.locator('#preflight')).to_contain_text('101');expect(page.locator('#preflight')).to_contain_text('87');page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/('preflight_valid_'+theme+'.png')),full_page=True)
        page.locator('#task').select_option('train_validate');page.locator('#check-inputs').click();expect(page.locator('#preflight')).to_contain_text('Task blocked');expect(page.locator('#run-analysis')).to_be_disabled();expect(page.locator('#cohorts-title')).to_contain_text('baseline training');page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/('preflight_blocked_'+theme+'.png')),full_page=True);page.locator('#task').select_option('race')
        checks.append(theme+' actual 101/87 public preflight, purpose-specific baseline blocker: PASS')
    (OUT/'import_receipt.json').write_text(json.dumps(dict(status='PASS',checks=checks),indent=2));print(json.dumps(dict(status='PASS',checks=checks)));b.close()
