"""Run preserved browser assertions with an explicit large-upload deadline.

Original scripts use Playwright's five-second expect default, which can expire
while validating the real 24MB pair. Outcomes/assertions are unchanged; final
acceptance allows 30 seconds, below the 60-second real computation deadline.
"""
import argparse,importlib.util
from pathlib import Path
from playwright.sync_api import expect
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['03','04','05','06'],required=True);p.add_argument('--url',required=True);a=p.parse_args()
    expect.set_options(timeout=30000)
    spec=importlib.util.spec_from_file_location('retained_browser',Path(__file__).with_name(f'browser_pass{a.stage}.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if a.stage=='03':module.main(a.url,None)
    else:module.main(a.url)
