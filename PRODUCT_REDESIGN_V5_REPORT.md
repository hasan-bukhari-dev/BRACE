# BRACE V5 — visual and workflow redesign

**Delivered:** the real local Python/FastAPI workbench, redesigned across home, workbench, RACE, FACE, ACE, Cohort Explorer, TRACE, evidence, intake, help and record inspectors. Engineering verification passes. Human usability acceptance remains **NOT RUN**.

## What changed

- A coherent interlock identity, fixed named BRACE tabs, warm light surfaces, independent dark colours, local Manrope typography and responsive layouts.
- Four-stage setup: files → dataset/class descriptions → contrast/review → validation and computation. Local CSV/TSV previews, exact-label suggestions, form-generated declarations and retained-input recovery remove the need to hand-edit JSON for common cases.
- A ready-to-use real public study, plus an explicit file guide distinguishing expression matrices, prediction tables, raw assays, models and evidence ZIPs.
- Linked frozen-gene tiles, a readable results table and actual paired standardized effects. FACE plots contain all measured samples, boxes, exact hover values, zoom and PNG download. Source and target expression axes stay separate.
- Actual confidence/coverage curves, overall accuracy, clickable multiclass confusion cells and exact saved-record inspection. Class-only confidence remains unavailable. Source cross-validation stays separate from target evaluation.
- Actual source-fitted PCA, feature comparisons, six selectable recorded calculation steps, a sandboxed preview of the exact exported HTML, real downloads and provenance fingerprints.

Implementation: brace_app/static/index.html, style.css, design-tokens.css, app.js and the JS modules; new charts.js, setup.js, cohort-declaration.js, guide.js, ace-design.js and evidence-design.js. Two additive read-only routes in study_api.py and embrace.py; existing API responses and scientific exports preserved. Focused route tests added in tests/test_v5_readonly_routes.py. Full path inventory: docs/v5/CHANGED_FILES.json. Libraries/licences/hashes: docs/v5/THIRD_PARTY.md and VENDOR_HASHES.json. No new Python package.

## Baseline and scientific preservation

Baseline: exact workspace BRACE_V4_COMPLETE.zip, SHA-256 `724a40f662d66dffad123fee205683ac7a4c6bba23948913972aaae8da0006bb`. Newly named Downloads copies were unavailable; the existing verified workspace archive supplied the runnable application. Supplied images informed visual design; their illustrative scientific values were not imported.

All 15 brace_core files, 101 original example/evidence files and 33 original test files are byte-identical to V4. The archive is unchanged. No CancerShift predictions or biological engines were rewritten. Existing 25 MiB API / 25,000-feature limits remain.

A fresh public recomputation used GSE42568 source **101 tumors** (67 ER+, 34 ER−) and GSE20711 target **87 tumors** (42 ER+, 45 ER−), with 10,000 source-filtered features. Independent SciPy/Welch and BH calculations reproduced all 20 frozen selections and the **14 supported / 5 matching without support / 1 opposite estimate** outcome. Maximum numerical discrepancy <6×10⁻¹⁵. Fresh freeze software metadata/hash differ from the saved reference because Python 3.11.9 replaces 3.11.2; numeric results agree. Actual fresh evidence and receipt: docs/v5/after/.

This remains exploratory ER-association testing: GC-RMA versus RMA, ER assay differences and incomplete donor authentication preclude claims of equal expression scales, locked validation, clinical utility or ER model transfer. No new biological claim is made by the redesign.

## Actual verification

- `python -m pytest -q`: **281 passed, 0 failed, 0 skipped**, 87.52 s; one existing Starlette/httpx deprecation warning. Includes all 265 prior tests plus 16 new route/integrity cases.
- `python scripts/release_smoke.py`: **PASS** — historical 680/668, synthetic full computation and reproducibility ZIP.
- Chrome production-browser journeys: **85 assertions passed**. Guided expression/prediction uploads, class-only and mapped-score cases, large-record bins, all 188 gene values, all 20 paired effects, 680-record cutoff counts, PCA coordinates, real recomputation/reload, report/ZIP equality, artifact hashes and error recovery.
- Responsive review: **108 assertions**, **102 screenshots**, 1440×900 / 1280×720 / 390×844, both themes. No page overflow, sampled text contrast failures or sampled control-boundary contrast failures. Actual forced-colour and reduced-motion checks passed.
- Native Chrome 200% zoom: **16 checks and 16 viewport screenshots**, both themes. Not CSS or device scaling. No runtime page errors or external runtime requests in final browser checks; generated local image blobs are local.
- Independent numerical reconciliation and baseline byte preservation: **PASS**. UI ledger: 6,440 entries across 53 authored source files; 29 explicit context reviews. Third-party bundle internals are separately hashed.

Receipts, screenshots, source checks and developer QA scripts accompany the package. SCREEN_REVIEW.html shows actual V4/V5 screenshots at matched viewports; it is a review artifact, not the application. Verification is automated engineering evidence, not completed human research or user testing.

## Critique, fixes and unresolved work

Visual inspection led to a simpler five-column gene table, separate measurements inspector, sticky setup actions, stronger contrast and narrower layouts. Browser testing caught and repaired stale help focus, an obscuring task dialog, an endless loader message, hidden edit controls, stale Back-button state, missing microarray platform guidance, matrix overflow, clipped-heading overflow and saved distribution-run navigation.

No known task-blocking engineering issue remains in the exercised flows. Unfamiliar-user task success, human screen-reader acceptance, physical touch devices, projector/display scaling and a fresh Python 3.13 installation were not tested. Chart hover/precision gestures are pointer interactions; exact tables and ordinary controls provide keyboard alternatives. The unchanged published report remains paper-white in dark mode. Python and an offline wheelhouse are not bundled: initial dependency setup needs a prepared wheelhouse or network, then the interface runs locally without CDN access. Use standard x64 Python; project packages stay in .venv.

## Start

Extract the complete ZIP to a writable folder. Run SETUP_BRACE_WINDOWS.bat, then START_BRACE_WINDOWS.bat. Use the printed local address; default-port conflicts automatically choose a free loopback port. Choose **Explore the public study**, or follow docs/v5/DATA_GUIDE.md for your files. Read README_START_HERE.md for dependency setup and release checks.
