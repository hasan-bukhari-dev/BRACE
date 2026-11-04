# Stage 08 acceptance and delivery gate

**Build:** BRACE 0.8.0 — Unified localhost research workbench.  
**Date:** 2026-11-02

## Implemented and directly verified

| Requirement | Evidence | Status |
|---|---|---|
| Unified four-view HTML/CSS/JS interface | `brace_app/static/index.html`, `app.js`, `style.css` | Implemented; static/JS syntax verified |
| Dedicated Study, Validation, Shift, Evidence views | Four markup sections, named controls | Implemented |
| Local-only Python backend | `launch.py`, `brace_app/server.py` | FastAPI TestClient and localhost HTTP smoke tests passed |
| Existing prediction import | `POST /api/analyze`, `mode=evaluate_predictions` | Integration test passed on synthetic input files |
| Training + external evaluation | `POST /api/demo/synthetic` | New model, target evaluation, and new shift output generated; tested |
| Mode C unlabeled shift | `POST /api/analyze`, `mode=diagnose_shift` | Integration test passed; no labeled results output |
| CPTAC historical research evidence | `GET /api/example/cptac` | 680 rows, 668 correct, real archived evidence loaded; tested |
| Historical adaptation tradeoff | `GET /api/example/historical-shift` | Explicit prior-work provenance; tested |
| Evidence exports | Allowlisted run file downloads, archived CPTAC and GSE2109 CSV/JSON | Integration tests passed |
| Input examples | `/api/templates` + `templates/` | ZIP download test passed |
| Web input restrictions | No binary-model uploads, 25 MB per file, CSV/TSV/JSON only, random run IDs | Tested invalid formats and missing files |
| Cross-site write restriction | Origin and trusted-host checks | Test passed |
| Static JS validity | `node --check brace_app/static/app.js` | Passed |
| Scientific regression tests | `python -m pytest -q` | **144/144 passed** |

## External acceptance still outstanding

1. **Windows launch:** Test from a fresh unzip with Python 3.11+ and a clean dependency install; exercise all three upload modes.
2. **Browser visual testing:** Managed Chromium blocked browser automation here, including localhost and file URLs. Therefore no successfully rendered Stage 08 screenshot or browser interaction test is claimed. Manually test responsive layout at 1440×900, 1280×720, and mobile viewport; test sliders, uploads, sample and gene dialogs, keyboard, and downloads.
3. **New real public expression data:** Stage 03 GSE42568/GSE29431 expression matrices are not bundled or independently verified; the public-data live-inference demo is not yet deliverable.
4. **External researcher usability:** Have a researcher unfamiliar with BRACE attempt Mode A and Mode B and record where they get confused. Do not claim the 30-second comprehension gate is fully achieved without the test.
5. **Competition prior-work permission:** Not confirmed by published policies in the earlier audit. Organizers must confirm allowed reuse and attribution.

## What the results do NOT claim

- A running CPTAC classifier or fresh CancerShift inference: **only archived predictions are available**.
- Any scientific discovery from synthetic demonstration data.
- Causal relationship between expression shift and classifier errors.
- Statistical intervals accounting for multi-study/patient clustering unless explicitly modeled.
- Clinical validity or deployment readiness.

## Stage 08 verdict

**Integrated application and API: implemented; full inherited + HTTP tests passed.**  
**Zero-instruction judge usability and full scientific public-data demo: acceptance pending.**
