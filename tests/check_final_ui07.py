"""Final rendered Unicode, small-q and narrow-view acceptance; no new science."""
import argparse,json,math
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
BASE=Path(__file__).resolve().parents[1]
def main(url,record,screens):
    screens.mkdir(exist_ok=True,parents=True);checks=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True);ctx=browser.new_context(viewport={'width':1280,'height':720},reduced_motion='reduce');page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.set_default_timeout(30000);expect.set_options(timeout=30000)
        page.goto(url);page.wait_for_function("document.documentElement.dataset.ready==='true'");body=page.locator('body').inner_text();assert 'Â·' not in body and 'Ã' not in body;expect(page.locator('.landing .eyebrow')).to_have_text('Discover in one cohort. Test in another.');page.locator('#explore-public').focus();assert page.locator('#explore-public').evaluate('e=>getComputedStyle(e).outlineStyle')!='none'
        page.screenshot(path=str(screens/'landing_focus_1280.png'),animations='disabled',full_page=True);checks.append('Final Unicode and research wording render correctly; keyboard focus visible')
        page.locator('#other-examples').evaluate('e=>e.open=true');page.locator('#synthetic-demo').click();expect(page.locator('#ace-confusion')).to_be_visible();page.locator('#show-shift').click();expect(page.locator('#gene-table tbody tr')).not_to_have_count(0)
        value=page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');return state.data}");rows=value['shift']['gene_shifts'];tiny=[r for r in rows if r['ks_bh_q_exploratory'] is not None and 0<r['ks_bh_q_exploratory']<.001]
        kind='actual synthetic fixture calculation'
        if tiny:row=tiny[0]
        else:
            # Explicit display-only boundary fixture, never treated as biology.
            page.evaluate("async()=>{const {state}=await import('/assets/js/state.js');state.data.shift.gene_shifts[0].ks_bh_q_exploratory=1e-9;const {renderShift}=await import('/assets/js/legacy-results.js');renderShift()}");row=dict(rows[0],ks_bh_q_exploratory=1e-9);kind='explicit display-only small-q boundary fixture'
        page.locator('#gene-search').fill(row['feature_id']);text=page.locator('#gene-table tbody tr').first.locator('td').last.inner_text();assert 'e-' in text and math.isclose(float(text),row['ks_bh_q_exploratory'],rel_tol=.006)
        page.screenshot(path=str(screens/'small_q_shift_1280.png'),animations='disabled',full_page=True);checks.append('Positive tiny q-values remain nonzero scientific notation in table: '+kind)
        page.locator('#gene-table [data-gene]').first.click();expect(page.locator('#sample-detail')).to_contain_text(text);page.locator('#close-dialog').click()
        for width,height in [(1440,900),(1280,720),(390,844),(720,450)]:
            page.set_viewport_size({'width':width,'height':height});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.screenshot(path=str(screens/'shift_narrow_720.png'),animations='disabled',full_page=True);checks.append('Final shift layout and inspector retain data/focus and reflow at desktop/narrow and approximate200%CSS viewport')
        assert not errors;record.write_text(json.dumps(dict(status='VERIFIED',browser=browser.version,checks=checks,uncaught_errors=errors,q_example=dict(feature_id=row['feature_id'],raw=row['ks_bh_q_exploratory'],display=text,kind=kind),scope='Developer rendered checks; not a human-user or screen-reader study'),indent=2)+'\n');browser.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--record',type=Path,required=True);p.add_argument('--screens',type=Path,required=True);a=p.parse_args();main(a.url,a.record,a.screens)
