# V4 browser and scientific review

Optional developer checks; Playwright is NOT a BRACE runtime dependency. The recorded run used Playwright 1.64.1 with installed Chrome 156.0.8078.80 on Windows. Do not install these tools into global Python.

Start production `launch.py` from the app root with `BRACE_PORT=8766`, `BRACE_NO_BROWSER=1` and an isolated `BRACE_RUNS_DIR`. Use a separate developer environment with Playwright and installed Chrome. From the app root run, in order:

```
python scripts/qa_v4/browser_acceptance.py
python scripts/qa_v4/browser_focused.py
python scripts/qa_v4/browser_last_checks.py
python scripts/qa_v4/browser_zoom.py
python scripts/qa_v4/browser_bins_check.py
python scripts/qa_v4/browser_geometry.py
```

These checks create genuine local runs (including clearly artificial technical fixtures), not production research evidence. `qa_output/` contains the new receipts and captures. Some later checks require runs made by earlier checks. Port 8766 is embedded in verification endpoint URLs; keep that test port. `BRACE_QA_APP` may select another extracted copy and `BRACE_QA_OUTPUT` another output root. Do not point the harness at a user's live research workspace. The zoom harness writes only its isolated output profile, never the user's Chrome profile.

The numerical check uses the actual fresh export in `docs/v4/after/public_fresh_evidence.zip`, prepared matrices, separately written Welch/BH/effect calculations, and `BASELINE_PROTECTED_FILES.json`. Run it with project scientific dependencies:

```
.venv\Scripts\python.exe scripts/qa_v4/numerical_preservation.py
```

Default release checks remain `RUN_RELEASE_CHECKS_WINDOWS.bat`. Browser/AX measurements are not unfamiliar-user tests or a screen-reader certification.
