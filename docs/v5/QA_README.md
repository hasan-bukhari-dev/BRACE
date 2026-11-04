# Re-running developer checks

Application checks: from the app folder with its .venv, run `python -m pytest -q` and `python scripts/release_smoke.py`. `python verify_release.py` checks the shipped manifest. No browser-test package is required to run BRACE.

Browser QA uses a separate environment with Playwright 1.64.1 and installed Chrome 156.0.8078.80. Start launch.py on loopback port 8766 with BRACE_RUNS_DIR pointing to a scratch folder. qa_v5 scripts are developer reference harnesses; the scripts default to local port 8766 and write QA captures under docs/v5. Keep the isolated browser profile under work/. The numerical check additionally needs BRACE_QA_BASELINE set to the exact V4 baseline ZIP for byte-preservation assertions and a freshly exported public evidence ZIP. It independently recalculates Welch tests/BH from the prepared matrices.

Final receipts: qa/receipt.json (85 checks), screens/receipt.json (108 checks), zoom/receipt.json (16 checks), NUMERICAL_PRESERVATION.json. Screens were visually reviewed as full images and contact sheets. The sampled computed-contrast audit is a useful engineering check, not a universal accessibility certification. Native zoom uses an isolated Chrome profile and CDP viewport screenshots because ordinary Playwright clipping mis-scales native zoom.

No actual human unfamiliar-user, screen-reader or physical touch acceptance is claimed. Earlier V4/design3 evidence in this package is historical, not counted as new V5 testing.
