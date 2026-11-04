# PASS 03 REPORT — PASS within tested engineering scope

Rebuilt the frontend foundation on the approved Pass 2 project. The scientific engines, historical CancerShift evidence, prepared public data, numerical RACE outputs and original analysis APIs are preserved. No Pass 4 molecular plots/inspection or later-pass work was implemented. No claims of tested human usability, clinical validity or event readiness.

## Before → after

| Area | Before | After |
|---|---|---|
| Navigation | Study / Validation / Cohort shift / Evidence | Study / RACE · Genes / ACE · Models / Evidence; cohort shift inside ACE |
| First use | Crowded introduction, archive/synthetic cards and upload form; archived evidence selected automatically | One question and two primary actions; no active data until selected |
| Public example | UI said real GEO acquisition pending | Hash-checked approved ER example with actual saved computation, sources, caveats and exports |
| Input tasks | Flat mode/file list and direct execution | Task selector, source/target groups, explicit manifests, readable preflight, blockers and enabled analysis only after checks |
| Prediction-only | Two files in shared form | Two relevant inputs, no cohort or RACE fields |
| Continuity | In-memory view/result state | Shared state; tab-local run/view/filter/selection/inspector restoration; explicit file reselection after refresh |
| Layout | Oversized recurring headings and dense sections | Compact header/context, navy/teal tokens, task-specific progressive detail, focus and reduced motion |

## Exact files changed
- `brace_app/static/index.html`, `app.js`, `style.css`.
- `brace_app/server.py`: registers additive study endpoints; health now truthfully reports verified public-data availability instead of the obsolete pending-acquisition message.
- `tests/test_stage08_app.py`: one availability assertion updated from false to true because the real example is now connected. No test removed/skipped or scientific assertion relaxed in this pass.
- `README_START_HERE.md`: current workflows and verification boundaries; removed stale claims that all real expression acquisition/browser testing were unavailable.
- Release integrity manifests refreshed; preceding release CSV retained as `docs/PASS03_BASELINE_SHA256.csv`.

## Files added
- `brace_app/study_api.py`.
- `brace_app/static/js/api.js`, `state.js`, `study.js`, `ui.js`, `inspector.js`, `legacy-results.js`. The final module reuses the prior working model/shift/evidence renderers.
- `tests/test_study_api.py`, `tests/browser_pass03.py`, `tests/browser_host.py` (test-only adapter).
- `docs/PASS03_DESIGN.md`, `PASS03_PUBLIC_REFERENCE.json`, `PASS03_TEST_ENVIRONMENT.txt`, `PASS03_BROWSER_RESULTS.json`, `PASS03_CHANGE_LIST.json`, nine actual browser screenshots under `docs/pass03_screenshots/`, and this report. Change list is also machine-readable.

No runtime package or framework added. Playwright 1.64.1, Apache-2.0 per installed package metadata, was installed only in the isolated development environment; it uses installed Chrome and is not needed to run BRACE. No CDN/font/cloud dependency.

## Functional changes and preservation
The public action opens the approved GSE42568 → GSE20711 exploratory ER study. It is clearly a saved computation, not a simulated or silently rerun example. The public GET/export endpoints verify pinned original/prepared/result files and fail closed if changed. Five scientific files are downloadable. A fresh RACE run is available through the actual six-file upload path; even GEO-named uploads retain the user-supplied evidence classification.

`POST /api/preflight` reuses existing parsing, prediction intake, compatibility and RACE eligibility without fitting a model or screening genes. It returns actual sample/feature counts, group balance, processing, donor-ID availability, hashes, warnings and blockers. It does not generate invented manifest values. Manifests remain explicit advanced imports; no manifest-generation wizard was added. RACE requires explicit condition definitions/equivalence review and a processing acknowledgement when appropriate. Modifying inputs invalidates the check. Server-side scientific validation still runs again on execution.

Completed runs remain selected while drafting new data or recovering from failures. New inputs are disabled during execution while navigation remains available. Model, shift and RACE results open in their appropriate context on completion. Session storage keeps small run/view/filter/selection identifiers rather than expression tables; File objects remain memory-only. Reload fetches completed runs; inputs must be reselected and checked before another upload. Interrupted requests are not silently resubmitted. This is tab-local restoration, not a new cross-browser history/database system.

Existing prediction import, source-only logistic modeling, unlabeled shift, synthetic computation, archived CPTAC/GSE2109, templates, run retrieval, confidence exploration, sample/shift-feature inspection and exports remain operational. Health and the one matching UI contract assertion changed to reflect connected real data. No backend scientific engine or historical evidence was modified.

RACE provides the working summary, all 20 frozen outcomes, filtering/sorting/selection, methods and exports. Full FACE molecular inspection is deliberately absent; no fake plot or inert inspector button was added. Existing record inspectors use one native dialog with explicit focus cycling, Escape dismissal and focus restoration. Small q-values use scientific notation instead of appearing as rounded zero.

## Commands and actual outcomes
- `python -m pytest tests/test_study_api.py -q`: **7 passed, 1 warning in 2.53s**.
- `python -m pytest -q`: **192 passed, 1 warning in 49.51s** (185 prior tests + seven new study API checks). The warning is the existing Starlette/httpx TestClient deprecation. The suite ran against final Python/backend changes; subsequent visual-only corrections were verified by the browser suite.
- `python scripts/release_smoke.py`: **exit 0**; archived historical=680/668, synthetic full computation PASS, reproducibility ZIP PASS.
- `python tests/browser_pass03.py --url http://127.0.0.1:8766 --before http://127.0.0.1:8767`: **exit 0**, Chrome 156.0.8078.74 on Windows, 20 recorded scenario assertions. These execute real APIs and real files, including a fresh public-data RACE upload. Structured results: `docs/PASS03_BROWSER_RESULTS.json`.
- Browser scenarios cover initial state, keyboard example activation, correct views, public result consistency, methods/CSV downloads, prediction-only upload, synthetic computation, uploaded model/shift/RACE tasks, invalid files, running-state navigation, run/filter/sort/selection refresh, inspector refresh/focus/Escape, reduced motion, long hostile labels/IDs, failure preservation and actual retry.
- Actual layouts checked at 1440×900, 1280×720 and 390×844; additional 720×450 reflow check approximates the CSS viewport at 200% on a 1440-wide display. No page-level horizontal overflow. Gene tables intentionally scroll within their container on narrow displays, with a visible hint. This is not a claim of testing browser zoom with a screen reader.
- No uncaught browser errors or external application HTTP requests. The sole final console resource error is the deliberately injected HTTP 503 for unavailable-example recovery. That failure injection and the long-label rendering fixture are UI tests, not scientific evidence.
- Release/checkpoint hashes and ZIP CRC are checked after packaging; packaging receipt is appended below.

The occupied production port was left untouched. Browser testing served the identical app on 8766 through `tests/browser_host.py`, which normalizes only that test origin to the existing canonical localhost origin. The ordinary production launcher never imports the adapter; trusted-host/origin/upload/export policies remain intact and their API regression tests pass. The untouched Pass 2 app on 8767 supplied the before screenshot. Test server run folders are outside the delivered project, under the workspace scratch directory.

## Visual/accessibility findings and repairs
Inspected all nine actual screenshots: `before_1440.png`, `landing_1440.png`, `landing_1280.png`, `landing_390.png`, `race_1440.png`, `race_1280.png`, `race_390.png`, `study_inputs_1440.png`, `blocked_1440.png`.

Browser iteration found and repaired: focus escaping a single-control dialog; a completed model opening the previously selected shift subview; missing source/target identifiers in the context strip; broken mobile heading word spacing; narrow gene-ID/q-value wrapping; an overly prominent prior-run summary above a new draft; raw JSON-only preview presentation; and excessive uppercase metric labels. Final screenshots were recaptured and inspected. Early test harness failures (Playwright element-evaluation syntax and a browser Origin override that broke module loading/POSTs) were corrected in the testing setup, not by weakening production security. A final assertion was updated to check the persistent cohort strip directly rather than stale hidden study content.

No known dead primary controls or release-blocking defect remains in the exercised workflows. Explicit empty states explain which analysis has no result rather than showing invented metrics. Screen-reader software, independent unfamiliar users, projector behavior, other browser engines, clean-device cold setup and measured usability/time-saving targets remain **not verified**. No full WCAG certification or human-comprehension claim is made.

## Scientific boundaries
All approved Pass 1B/2 limitations remain: exploratory ER association, GC-RMA versus RMA, EIA versus IHC labels, incomplete donor authentication, subtype/relapse enrichment, confounding and the source-selected variable-gene universe. Public-data availability does not establish direct scale comparison or source-trained model-transfer validity. Historical evidence, synthetic results, saved public computation and uploaded computation have distinct visible labels. No clinical, causal or validated-biomarker claim added.

## Three skeptical product-judge criticisms
1. **“Your public example just opens saved numbers.”** Correct and labeled. It opens real reproducible Pass 2 output, while the browser suite also runs the supplied matrices through the live upload endpoint. No fake progress or implied fresh execution.
2. **“Six files and explicit manifests still require expertise.”** Correct. This pass groups and previews them, preserves the scientific contract and prevents invented metadata. A guided generator was optional and not substituted for reviewed declarations.
3. **“How do you know a novice understands this?”** We do not claim a human usability study. Actual keyboard, task, failure and responsive tests pass; unfamiliar-user and projector acceptance remain open.

**Decision: PASS for the implemented frontend foundation and available browser/API checks. Stop after Pass 3; no Pass 4 implementation.**

## Packaging receipt

Release verification: **195/195 files verified**. Checkpoint ZIP CRC and every recorded SHA-256 checked after creation. Cache files, virtual environments and browser-generated run folders are excluded.
