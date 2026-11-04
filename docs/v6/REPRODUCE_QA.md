# Reproduce V6 verification

Runtime and pytest use the existing project `.venv`; browser QA uses a separate environment with Playwright 1.64.1 and installed Chrome (executed here with Chrome 156). Browser automation is not an application dependency. Set `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, `OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1` for comparable output. Run from the extracted application root.

1. `.venv/Scripts/python.exe -m pytest -q`
2. `.venv/Scripts/python.exe scripts/release_smoke.py` with an isolated `BRACE_RUNS_DIR`.
3. Start `launch.py` with `BRACE_PORT=8787`, `BRACE_NO_BROWSER=1` and `BRACE_RUNS_DIR=<scratch>/runs`; leave it running for browser scripts. Use an unused port or adapt script URLs consistently. Do not stop unrelated servers.
4. With the browser environment's Python, run `scripts/qa_v6/v6_journeys.py` first: it creates the actual descriptive-shift run needed by the layout script. Then run `v6_layout.py`, `v6_navigation.py`, `v6_unseen.py`, `v6_final_paths.py`, `v6_reuse_execution.py`, `v6_zoom.py`. Scripts write explicit receipts/screenshots in `docs/v6`. Navigation includes a real GEO request and may fail if the external service is unavailable; unit tests do not require NCBI.
5. `.venv/Scripts/python.exe scripts/qa_v6/v6_numerical.py` independently reconciles prepared matrices with the shipped fresh evidence ZIP and original protected-file snapshot. It does not import the RACE engine for the independent t-test/BH calculation. Browser reruns generate different run IDs; shipped `after/FRESH_RUN.json` identifies the evidence captured for this release.
6. `verify_release.py` is read-only. Regenerating QA artifacts intentionally changes release hashes; use an unmodified extraction when verifying the original release inventory.

Receipts distinguish live network checks, mocked/failure-injected UI checks and actual scientific recomputation. The 503 failure test injects only a network-error response. The delayed-completion test releases the held request to the real backend. No test receipt is a human participant study.
