# BRACE — PASS 05 REPORT

**2026-11-03 · Decision: PASS for the tested Pass 5 acceptance scope.** A judge can inspect a real saved prediction error, explore confidence/coverage, and trace the selected result to checked evidence. No subsequent pass has started.

## Delivered and preserved

The working project was extracted from the approved Pass 4 checkpoint into `BRACE_PASS05_v1`. The previous checkpoint and original supplied archive are unchanged. Hash comparison confirms **no changes to `brace_core/`, `examples/`, or any existing test**. All historical predictions, public measurements, preparation records and frozen RACE results remain intact. Original prior-pass review receipts/screenshots are retained; new regression receipts are named separately.

ACE now asks **Does the model generalize?** It shows total/correct/incorrect counts, overall accuracy, support-based balanced accuracy and macro-F1, exact class support/confusion counts, saved uncertainty and evaluation roles. Source OOF and target results appear side by side only when recorded; imported/archived scores have an explicit unavailable source-CV comparison. No performance-difference headline is invented.

Confidence Challenge reads the existing saved curve, displays every required retained/withheld/coverage/correct/error/accuracy/risk value, and marks the selected operating point. Its indexed slider represents the 0.01 grid plus the **exact** declared reference, including off-grid cutoffs. Equality is retained. Threshold 1 with an empty set shows undefined selective accuracy/risk. Missing probability vectors disable the interaction. The visible explanation is: **“Adjusting the threshold does not retrain the model.”** Other cutoffs remain exploratory; historical references are not newly blinded evaluations.

Sample inspection shows actual labels, complete supplied scores, raw maximum score and reference-cutoff membership. Same-run shift descriptors appear only for the matching evaluated target sample. TRACE preserves the run and selected sample/gene, with recorded/computed/declared/not-performed steps, methods, hashes, warnings and artifact links. RACE/FACE retain their measured-expression workflow and now use the complete six-step contextual trace. Mode C has a separate unlabeled chain and no outcome-conditioned findings.

Python/FastAPI, native JavaScript/CSS, production dependencies, loopback/origin restrictions, intake limits and existing scientific engines are preserved. The generated Stage 05 `run_result.json`, already present in scientific bundles, is now also allowlisted for read-only download so source CV/freeze evidence can be inspected. Raw uploads remain excluded from exports.

## Actual historical evidence

| Quantity | Verified saved value |
|---|---|
| Evaluation | 680 scored predictions; 668 correct; 12 incorrect |
| Overall accuracy | 668/680 = 98.24% displayed |
| Balanced accuracy / supported macro-F1 | 98.54% / 98.27% displayed; 4 supported true classes of 5 declared |
| True support | breast 133; colorectal 105; lung 341; ovary 101; prostate 0 |
| Archived reference cutoff 0.95 | 584 retained; 96 withheld; 583 retained correct; 1 retained error |
| Reference coverage / selective accuracy / risk | 85.88% / 99.83% / 0.17% displayed |
| Exploratory cutoff 0.99 | 432 retained; 248 withheld; 431 retained correct; still 1 error |

The verified high-confidence error is sample `breast_cptac_gdc::cfc121b5-9562-4a6d-b792-3cd6d5`: true **breast**, predicted **ovary**, maximum score **0.998692106** (99.87% rounded). Its actual saved vector is available in the inspector and trace snapshot. It remains retained at both 0.95 and 0.99. This is archived CancerShift evidence, not new five-class inference or evidence about the curated RACE specimens.

The real public RACE trace uses GSE42568 → GSE20711, ER association, exact Entrez ID 135112 and the unchanged frozen hypothesis. The independently audited Pass 2/4 result remains 20 selected/testable, 14 matching with target support, 5 matching without sufficient support and 1 opposite estimate. No new gene or clinical result is claimed.

Mode B was also actually computed on the bundled **synthetic** expression fixture: source OOF 13/20 correct, target 11/14 correct. Their metrics/folds/frozen model and same-run sample shift linkage were checked. These artificial data verify software only. Controlled imported-score fixtures test exact 0.955 equality, missing classes/probabilities and undefined denominators. Mode C was run with the synthetic expression inputs while excluding their outcome labels from analysis output.

## Reproduce and inspect

Launch the extracted project using the existing launcher → **Study → Other examples & archived research → Open archived predictions**. Read ACE → move Confidence Challenge → reset to 0.95 → select the breast→ovary error in **Errors** → **Trace result** → inspect/download its recorded evidence → **Return to sample prediction**.

For RACE: **Explore a public example → study results → feature 135112 → Trace result → Return to gene measurements**. The active study does not change.

`docs/PASS05_DATA_CONTRACT.md` supplies the full click path and exact new GET contracts:

- `/api/ace/studies/{study_id}?sample_id=...`: checked saved metrics/source CV, exact selected row and same-run shift descriptors.
- `/api/trace/studies/{study_id}?feature_id=...` or `?sample_id=...`: six recorded RACE/ACE steps; four unlabeled Mode C steps.

Neither endpoint fits, scores a model, recomputes statistics or optimizes thresholds. Hash/canonical model checks fail closed when evidence mismatches; declarations are explicitly unauthenticated. The browser caches the latest checked summary for navigation; fresh sample/TRACE requests and reloads check evidence again. This is not a live filesystem monitor or cryptographic acquisition attestation.

Thirteen screenshots are in `docs/pass05_screenshots/`. Four actual TRACE JSON snapshots and two engine-generated synthetic/shift research bundles are in `docs/pass05_evidence/`, with an `INDEX.json` hash inventory. Random test-run URLs in those snapshots refer to developer runs; the files are review evidence, not installed runtime history. The stable historical/public examples work directly in the app. Fixture filenames and the contract document identify artificial data explicitly.

## Files changed or added

Changed: `README_START_HERE.md`; `brace_app/server.py`; `brace_app/static/app.js`, `index.html`, `style.css`; `brace_app/static/js/inspector.js`, `legacy-results.js`, `race.js`, `state.js`; both checkpoint hash inventories.

Added implementation: `brace_app/evidence_api.py`, `brace_app/static/js/ace.js`, `trace.js`. Added tests: `tests/test_evidence_api.py`, `tests/browser_pass05.py`.

Added review material: this report; `docs/PASS05_DATA_CONTRACT.md`, `PASS05_VERIFICATION_LEDGER.md`, `PASS05_VERIFICATION.json`, `PASS05_CHANGE_LIST.json`, `PASS05_ARCHIVED_REFERENCE.json`, `PASS05_BASELINE_SHA256.csv`, `PASS05_BROWSER_RESULTS.json`, `PASS05_LEGACY_BROWSER_RESULTS.json`, `PASS05_RACE_BROWSER_RESULTS.json`; the screenshot/evidence files above. The machine-readable change list enumerates every path. No files were removed. No new application runtime package or chart library was introduced.

## Commands run and exact outcomes

Commands used the existing isolated workspace virtual environment; the Espressif installation was not modified. Python tests ran from the checkpoint folder. Browser scripts used the existing test-only origin adapter on local port 8766; production security and the unrelated app on 8765 were untouched.

| Command | Actual final outcome |
|---|---|
| `python -m compileall -q brace_app` | Exit 0 |
| `python -m pytest tests/test_evidence_api.py -q` | **12 passed**, 1 warning, **6.29 s** |
| `python -m pytest -q` | **211 passed**, 1 warning, **63.78 s**; 199 retained + 12 new |
| `python tests/browser_pass05.py --url http://127.0.0.1:8766` | Exit 0; **15/15 scenarios**, zero uncaught errors/external application requests |
| `python tests/browser_pass04.py --url http://127.0.0.1:8766` | Exit 0; **11/11 RACE/FACE scenarios** |
| `python tests/browser_pass03.py --url http://127.0.0.1:8766` | Exit 0; **20/20 preserved scenarios**, zero uncaught errors/external requests; expected injected 503 resource error only |
| `python scripts/release_smoke.py` | Exit 0; historical 680/668, synthetic full computation PASS, reproducibility ZIP PASS |
| Nested review ZIP manifests, CRC and snapshot hashes | All verified |
| `python verify_release.py`; checkpoint ZIP CRC/SHA inspection | Exact packaging receipt below |

The full Python suite ran once after the final backend change. Later browser-driven refinements were JavaScript/CSS and console/test-capture changes, verified in the final browser walks. The warning is the existing Starlette/httpx TestClient deprecation. Older browser-script Unicode output required `PYTHONIOENCODING=utf-8` in Windows; assertions were retained.

Tests independently reconcile every historical confusion cell, class support/metrics and saved threshold point against sample rows; check the actual high-confidence error and artifact hashes; check source OOF/freeze linkage without rerunning training; reject altered inputs/artifacts; and confirm that Mode C excludes labels even when input metadata contains them. Existing invalid-probability, undefined-denominator, missing-class, leakage and historical-invariant tests remain in the full suite.

Browser coverage includes exact table/metric agreement, retained equality and endpoints, empty sets, selected plot marker, disabled probabilities, support/reasons, errors and same-run shift linkage, contextual RACE/ACE TRACE, real downloads, filtering/persistence, keyboard/focus, failure/retry, stale asynchronous responses, escaped identifiers and responsive layouts. Chrome **156.0.8078.74**, developer Playwright **1.64.1**, Windows; 1440×900, 1280×720 and 390×844, plus legacy reflow coverage. Screenshots were opened and visually inspected against the retained prior-pass evidence.

## Discrepancies and repairs

No Stage 06 numerical or export discrepancy was found; no scientific metric implementation changed. Percentages display two decimals, while counts, IDs and threshold values remain exact; full-precision JSON/CSV is authoritative. The old nearest-grid/rounded threshold presentation was replaced by selection among exact saved points, verified with a 0.955 reference.

Development tests found and repaired: the generated source-CV JSON was bundled but not downloadable; sample inspection replaced its opener row and lost return focus; TRACE introduced ambiguous duplicate download names; active old-study result buttons could be clicked while a public example was loading. The fixes add one generated JSON download filename, preserve the original row/dialog opener, give contextual accessible link names, and disable stale study actions during loading. Legacy wording distinguishing **Overall accuracy** from selective accuracy and the unlabeled explanation was retained. Initial failing checks were rerun successfully; no old assertion was removed.

Two final automated threshold-action observations were **19.68 ms** and **17.61 ms**, including browser-automation round trips. These are developer observations, not controlled hardware benchmarks, human task timings or performance guarantees. Startup, peak memory, unfamiliar-user timing and projector targets were not measured.

## Biomedical ML reviewer critique / known limits

The interface now exposes conditional evidence more faithfully; it does not improve the underlying model or authenticate its cohort. CPTAC's absent prostate true class, study/class confounding and unverified acquisition independence prevent a full five-class transportability claim. Row-level Wilson/bootstrap intervals do not resolve patient/study clustering. A higher confidence cutoff can retain a very confident wrong prediction; post-hoc exploration cannot establish a safe prospective abstention rule. Source OOF and target evaluations have distinct sampling/designs and are not a paired performance comparison.

The public RACE pair retains GC-RMA/RMA, ER-assay and donor-independence limitations; it is not model-transfer evidence. Biological provenance, manifest roles and predeclaration are recorded declarations. Original CancerShift model weights/training history are not recovered. Source OOF intervals were not saved; exploratory-cutoff intervals are not invented. Narrow charts/tables require local scrolling. A screen-reader-software audit, other browser engines, clean-device installation, actual unfamiliar-user testing and projector operation remain unverified. Competition authorization/disclosure uncertainties from earlier passes remain recorded. No known failing primary workflow remains in the tested scope.

Three skeptical judge questions:

1. **“Does 99.83% selective accuracy establish clinical reliability?”** No: it describes 583 correct among 584 retained archived rows, at 85.88% coverage, under limited class support and unresolved independence/calibration assumptions.
2. **“Did moving the slider retrain the model or validate a better policy?”** No: it selects a saved point computed from the same records. The exact reference and post-hoc alternatives remain visibly distinct; the confident error still survives 0.99.
3. **“Can the gene result or prediction error be traced to invented steps or unrelated specimens?”** TRACE lists recorded inputs, methods, hashes and actual artifact links for the selected run. Unperformed training/inference is explicit for supplied predictions. Archived errors receive no unrelated RACE expression data; same-run shift linkage is conditional and noncausal.

**Stop point:** Pass 5 is delivered for independent review. Pass 6 has not started.

## Packaging receipt

Release verification: **249/249 files verified**. Checkpoint ZIP CRC and every recorded SHA-256/byte count were checked after creation. The ZIP contains 251 files, including both inventories. Virtual environments, caches and runtime run folders are excluded. Prior release hashes are preserved in `docs/PASS05_BASELINE_SHA256.csv`. The six review evidence files also passed their hash checks; both nested research ZIPs passed CRC and every scientific-artifact manifest hash.
