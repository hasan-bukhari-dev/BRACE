# BRACE — PASS 04 REPORT

**Decision: PASS for the tested Pass 4 acceptance scope.** A real saved RACE result now opens FACE measurements and a gene-specific trace without rerunning the statistical engine. Delivery stops at Pass 4.

## Scope and preserved baseline

Working project: `BRACE_PASS04_v1`, copied from the approved `BRACE_PASS03_v1`. Previous checkpoints and original supplied archive are unchanged. No `brace_core/` or `examples/` file differs from Pass 3, including public downloads, prepared data, frozen RACE artifacts and historical CancerShift prediction evidence. Existing tests are retained without edits. Python/FastAPI, production dependencies, API protections, 25 MiB file limit and 25,000-feature intake limit remain unchanged.

The user authorized continuation without repeated checkpoint approval questions. This delivery implements the attached Pass 4 brief; it does not begin subsequent passes or treat incidental document content as a separate user request.

## Delivered behavior and public-data click path

Start the existing local launcher → **Explore a public example** → study results → **RACE · Genes**. The question is **Which genes hold up in another cohort?** The full selected family is the default. Search `NCOA7` / `135112`, activate the feature ID, and inspect FACE beside the table. Scroll its desktop panel to the target cohort. Expand measured values, missingness and exclusions. **Trace result** opens Evidence with that exact gene/run/hash; **Return to gene measurements** restores context.

Search `DOK5` / `55816` for matching direction with insufficient target support, or `LPCAT2` / `54947` for an opposite-direction estimate. All remain inspectable. Filtering never changes summary denominators or silently replaces a selected gene. Starting another analysis resets gene-specific state and shows all outcomes. Numeric sorting uses original numbers; missing values appear as **Unavailable**. The table scrolls within bounded space, and the nonmodal inspector moves above it on narrow screens. Keyboard activation, Escape/focus restoration, loading/retry and late-response protection are functional.

The public example reads the validated Pass 2 artifacts. For fresh computation, the existing six-file upload and compatibility-review workflow remains available. Full instructions and exact field-level API contracts are in `docs/PASS04_DATA_CONTRACT.md`.

## Real evidence and scientific interpretation

| Item | Source | Target |
|---|---|---|
| Study | GSE42568_ER / GEO GSE42568 | GSE20711_ER / GEO GSE20711 |
| Included tumors | 101: 67 ER-positive, 34 ER-negative | 87: 42 ER-positive, 45 ER-negative |
| Original sample exclusions | 17 non-tumor, 3 ER missing, from 121 | 2 non-tumor, 1 ER missing, from 90 |
| Platform / deposited processing | GPL570 / log2 GC-RMA | GPL570 / RMA plus log2 transformation |
| Prepared features | 10,000 source-selected Entrez representatives | Same 10,000 identifiers |

The contrast is clinically ER-positive minus clinically ER-negative primary breast tumor. Existing source-only probe/gene filtering and all provenance/citations/hashes remain in the public-pair README and preparation records; no new external dataset or annotation was downloaded for this pass. Symbols are read only from verified pinned platform annotations when all six input hashes match. Generic uploads retain exact IDs without invented symbols or prior-exclusion counts.

The unchanged frozen result screened 10,000 source hypotheses; 1,339 passed source BH q≤0.05. It selected 20 genes before target testing. **20 are testable, 14 have matching direction plus target BH support, 5 match without sufficient support, 1 has an opposite-direction estimate, and 0 are untestable.** The opposite estimate is not a statistically supported reversal. The six summary counts are overlapping concepts (selected/testable versus outcome categories), not a universal pass/fail score.

FACE uses actual matrix cells, exact included sample IDs and saved group statistics. Each cohort has its own labeled intensity axis; no shared-axis scale equivalence is claimed. Positive-minus-negative mean differences are not relabeled as log2 fold change. Pointwise Welch intervals and Hedges' g come from saved Python outputs. The browser performs presentation formatting and plot positioning only.

This is exploratory association evidence. GC-RMA/RMA processing, EIA/IHC ER assessment, unknown cross-study donor independence, study composition and unadjusted observational confounding remain material limits. Matching without support does not establish no effect. Source-selected pointwise intervals are not selection-adjusted simultaneous intervals. This work establishes neither causal/clinical biomarkers, source-trained model transfer nor direct comparison of absolute cohort expression scales. Existing source-fitted PCA and shift results remain in ACE for studies that computed them; none are manufactured for this RACE result.

## Files changed or added

Changed implementation/documentation files:

- `brace_app/server.py`: registers the minimal read-only molecular router.
- `brace_app/static/app.js`: connects RACE rendering and selected-gene Evidence trace.
- `brace_app/static/index.html`: primary RACE question.
- `brace_app/static/js/state.js`: resets gene/filter state when a new run starts.
- `brace_app/static/style.css`: RACE table, summary, FACE plots and responsive inspector layout.
- `README_START_HERE.md`: current molecular workflow and verification boundaries.

Added:

- `brace_app/molecular_api.py`: checked result-to-input linkage; selected-family metadata and per-gene measurements. No engine rerun.
- `brace_app/static/js/race.js`: complete searchable/sortable family, categories, measured distributions, contextual inspector and trace.
- `tests/test_molecular_api.py` (7 collected tests); `tests/browser_pass04.py` (11 scenario checks).
- `docs/PASS04_DATA_CONTRACT.md`, `PASS04_BROWSER_RESULTS.json`, `PASS04_LEGACY_BROWSER_RESULTS.json`, `PASS04_VERIFICATION.json`, `PASS04_CHANGE_LIST.json`, `PASS04_BASELINE_SHA256.csv`.
- Eight actual screenshots in `docs/pass04_screenshots/`; this report. The machine-readable change list enumerates each path.
- Refreshed `FILE_SHA256_MANIFEST.csv` and `CHECKPOINT_SHA256.json` for this checkpoint.

No files were removed. Original Pass 3 screenshots/receipt are preserved; the rerun's receipt is stored separately under Pass 4. No new runtime packages, chart library, model service, cloud or telemetry were added. The existing developer-only Playwright installation drives installed Chrome; it is not a runtime dependency or bundled browser.

## Data linkage and numerical audit

`GET /api/race/studies/{study_id}/genes` returns the complete selected family plus verified annotation and cohort context. `GET /api/race/studies/{study_id}/gene?feature_id=...` returns exact saved source/target statistics, observed groups/sample values, availability, limitations and trace. IDs are the existing safe local run ID or pinned `public_er_pass2`. Existing authoritative export files remain unchanged.

Every request checks input hashes; scientific artifacts and the frozen family/hash are checked before serving measurements. Only allowlisted saved input names are read. The existing intake parser supplies aligned measurements; a four-entry parsed-cohort cache avoids reparsing unchanged files. Invalid IDs/nonselected genes return 404; corrupt or mismatched saved user evidence fails closed with 409 (the existing pinned public verifier retains its 503 unavailable response). Missing features return empty observations and null saved statistics, never a fake zero distribution. Details are in the contract document.

The API test independently reads the prepared TSVs with `csv.reader` and checks every observation for all 20 selected genes, every source frozen record and target result record, group sizes and trace hashes. It prevents calls to the RACE engine/test function during retrieval. Browser tests verify all 20 table rows, numeric order, actual dot values and displayed FACE estimates/q/intervals against API values. Existing engine/export consistency tests remain in the full suite.

No calculation/export discrepancies were found. Display differences are documented rounding: effects/g/interval endpoints to three decimals; q to four decimals or three significant scientific digits below 0.0001. Full-precision exports remain authoritative. Development testing found and repaired a context bug where a previously traced gene could remain in Evidence after selecting a different gene; a regression assertion now checks the latest selection. A target screenshot initially captured the inspector's source scroll position; the harness now captures a separate target crop. Neither repair changed scientific values.

## Commands executed and actual outcomes

Commands below used the isolated workspace `work/venv/Scripts/python.exe`; the global Espressif Python installation was not modified. Working folder was the checkpoint for pytest, or the workspace with the checkpoint path supplied for scripts.

| Command | Observed outcome |
|---|---|
| `python -m pytest tests/test_molecular_api.py -q` | **7 passed**, 1 warning, 14.68 s. |
| `python -m pytest -q` | **199 passed**, 1 warning, 77.83 s (192 retained + 7 new). Full suite run once; subsequent frontend/context and screenshot-test refinements were verified through Chrome. |
| `python tests/browser_pass04.py --url http://127.0.0.1:8766` | Final run exit 0; **11/11 scenario checks passed**, zero uncaught browser errors; 8 screenshots. |
| `python tests/browser_pass03.py --url http://127.0.0.1:8766` | Exit 0; **20/20 existing scenario checks passed**, zero uncaught errors, zero external application requests. One expected resource error came from the deliberately injected 503 failure test. |
| `python scripts/release_smoke.py` | Exit 0; `historical=680/668; synthetic full compute=PASS; reproducibility ZIP=PASS`. |
| `python verify_release.py` and ZIP integrity/hash inspection | Exact packaging receipt below. |

The one pytest/smoke warning is the existing Starlette TestClient/httpx deprecation, not a failed check. Socket/browser checks ran with the necessary host permissions because the restricted Windows environment hangs on asyncio socket setup. Production origin checks were unchanged; browser verification used the existing test-only spare-port adapter. The unrelated app occupying port 8765 was left alone.

Browser: installed **Chrome 156.0.8078.74**, developer Playwright 1.64.1, Windows, 1440×900 / 1280×720 / 390×844, reduced motion enabled. Coverage includes unsupported/opposite/untestable outcomes, fixed denominators, numeric sorting, keyboard activation, closing/focus, navigation/refresh, rapid delayed selection, fetch failure/retry, escaped long identifiers and actual uploaded RACE execution. The legacy suite also exercised supplied-prediction Mode A, source-trained Mode B, unlabeled Mode C, historical/synthetic examples, shift inspection, downloads, blocked input and persistence.

The missing-target case is an explicit controlled fixture: original public measurements with target row 135112 omitted, followed by real RACE computation. It is not presented as the approved cohort result. Delay/error/long-label injections are UI tests only. Public screenshots use actual pinned evidence; the two `missing_target*` images are labeled fixture evidence in the contract document. Screenshots were opened and visually inspected, including separate source/target plots, unsupported results, trace, responsive layouts and missing-target text.

## Internal comprehension review and limitations

Internal heuristic review, **not a real human-user test**:

1. Biological question: the RACE title and explicit ER contrast identify what was tested.
2. Discovery cohort: “Discovered in source” and GSE42568_ER appear above the results and inside FACE.
3. Testing cohort: “Tested in target” and GSE20711_ER appear with counts and assay details.
4. Support meaning: summary definitions distinguish BH support, insufficient support, opposite estimates and untestable cases; all selected genes remain available.
5. Measurement origin: sample-value tables, original probe/annotation provenance, checked input hashes and exact selected-run trace identify where the observations came from.

Known limits: the desktop table requires horizontal scrolling with FACE open; target measurements require scrolling within the inspector. Narrow layouts place the inspector above the table. These behaviors have visible cues and were tested, but unfamiliar-user task times, projector operation, screen-reader software, other browser engines and clean-device installation remain unverified. No latency/memory benchmark or product timing target is claimed. Historical platform symbols may differ from current nomenclature; exact Entrez/probe IDs and annotation provenance remain available. Independent confirmation of patient independence and competition permission/disclosure requirements remains outstanding from earlier passes.

No known failing primary workflow or scientific value discrepancy remains in the tested scope. Limitations above constrain interpretation; they are not concealed as successful external validation.

## Three skeptical biology-judge questions

1. **“Does 14 supported genes mean you validated a biomarker?”** No. It means matching-direction target BH support in an exploratory frozen family under this unadjusted association design. Processing, phenotype and donor limitations preclude a locked or clinical claim.
2. **“How do I know these plots are the observations used for this result?”** The endpoint checks the saved scientific artifacts, frozen family/hash and all six input hashes, then returns exact matrix cells aligned through actual intake. Tests compare every selected gene against independently read TSV cells. Trace exposes those identities and methods.
3. **“Are the less successful genes hidden or the target used to improve selection?”** All 20 source-frozen hypotheses appear by default; 5 matching-but-insufficient and 1 opposite estimate stay inspectable. Target testing does not change source selection. Absent genes retain their testing-family place and show unavailable evidence. Source-only selection/leakage protections remain in the unchanged engine regression suite.

## Stop point

Pass 4's result → measurements → exact-run trace workflow is delivered for independent review. No Pass 5 functionality or speculative frontend design has been started.

## Packaging receipt

Release verification: **214/214 files verified**. ZIP CRC and every recorded SHA-256 were checked after creation. The ZIP contains 216 files, including both inventory files. Cache files, virtual environments and generated run folders are excluded. `docs/PASS04_BASELINE_SHA256.csv` retains the prior release inventory; the new inventories describe Pass 4.
