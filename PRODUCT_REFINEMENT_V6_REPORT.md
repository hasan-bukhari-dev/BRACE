# BRACE V6 — implemented workflow refinement

**2026-11-04. Engineering verification: PASS on the tested Windows environment. Human/device acceptance: NOT RUN.** This implements the approved V5 audit scope while preserving the approved appearance and scientific engines. It is an exploratory local research workbench, not a claim of clinical validity or universal usability.

The existing application was updated in place at the sole working application directory, whose legacy name remains `BRACE_V5_v1`. The complete delivery ZIP uses `BRACE_V6/` as its root. Original downloads and historical CancerShift research were not edited. Supporting historical specifications informed the work; obsolete pass instructions and illustrative reference-image numbers were not executed or copied into scientific results.

## Changes against the approved 20-item scope

| # | Implemented behavior | Verification / boundary |
|---|---|---|
| 1 | Full canonical name: **Biological Reliability Assessment across Cohorts and Experiments** on the current home and biological reports | Generic prediction reports remain domain-neutral; historical artifacts retain their original wording |
| 2 | Committed browser history, Back/Forward, route/run restoration and a visible Back control | Tested tool roundtrips, deep-link reload and selected-gene/record restoration; no claim of every possible browser history permutation |
| 3 | Explicit FACE/TRACE returns and saved-result routes | Same-gene FACE → TRACE → FACE, prediction TRACE return, dataset editing and saved-run reopen exercised |
| 4 | Stationary BRACE letters with moving suffix preview, subdued prefix and separate committed state | Thirty pointer previews, pointer-leave restoration and arrow/Enter activation; touch does not require hover |
| 5 | Contextual FACE, TRACE, EMBRACE and SPACE family treatment with plain task labels | Native actionable controls remain; no extra competing global tabs |
| 6 | Concrete opening explanation and separate expression/prediction routes | Current home and file help inspected at desktop and narrow widths |
| 7 | Compact operation receipt before and after execution | Identifies input origin, exact operation, meaningful method sequence and recorded run; saved opening, filtering, fitting and computing are distinguished |
| 8 | Expandable actual RACE, prediction, baseline and shift methods | Welch/BH/freeze; source-fitted logistic pipeline/CV; source-fitted PCA/KS are disclosed; explanations do not execute calculations |
| 9 | Public origin separated from fresh/saved status | Exact six input hashes required to recognize the bundled public inputs; fresh public preparation/provenance persists into EMBRACE |
| 10 | **Open saved public result** and **Run the public example again** | Actual public rerun verified; six exact inputs/config/README download; historical classifier is never promised as rerunnable |
| 11 | Reuse selected files, visible JSON-to-form hydration, retained task drafts and invalidated checks | Public ER data reuse succeeds for shifts and is explicitly blocked for the normal/tumor baseline; full reload still requires reselecting original private files |
| 12 | Class-only ACE leads with supported accuracy/confusion/class results | No large disabled confidence instrument; valid scored inputs keep confidence/coverage behavior; invalid vectors remain rejected |
| 13 | Compact scrolling ID/class tables, exact-ID copy and keyboard matrix navigation | New artificial 2/3/10/30-class inputs, long Unicode IDs, absent classes and no probabilities; 900-cell matrix avoids 900 Tab stops |
| 14 | RACE separates matching direction from target support and inconclusive/opposite estimates | Actual 14/5/1 result retained; no effect/reversal/clinical claim invented |
| 15 | FACE keeps actual cohort/group measurements, stable IDs and separate expression scales | All 188 included sample points and all 20 feature values checked through the broad browser journey |
| 16 | TRACE explains each recorded step before raw artifacts | Actual 10,000 source features, 20 frozen features and 20 target tests displayed; selected object and explicit return preserved |
| 17 | Evidence leads with result, origin and limitations; biological report includes a pinned feature-symbol/probe legend | Original numeric artifacts retained; audited HTML route equals ZIP member; preview artifact-link download verified byte-for-byte against the ZIP |
| 18 | Source/freeze/target and source-CV/target diagrams, inclusion/exclusion rails and brief continuity motion | Original sample exclusions inspectable/downloadable; reduced-motion/forced-color and native zoom checks; no fabricated progress stages, number countups or significance celebration |
| 19 | **SPACE · Find public datasets** searches official GEO, shortlists two candidates, verifies actual matrix names, acquires a bounded original gzip and exports receipts | Live search/listing/acquisition succeeded. Metadata and an original download remain explicitly unprepared and scientifically unapproved; manual scientific curation is required |
| 20 | Regression, numerical, new-input, navigation, export, responsive and visual review | Executed automated checks below; unfamiliar student/researcher, real screen-reader and physical device acceptance remain explicitly pending |

## Files changed or added

The exact inventory is [FILE_CHANGES.json](docs/v6/FILE_CHANGES.json); final source/data byte hashes are in `FILE_SHA256_MANIFEST.csv` and `CHECKPOINT_SHA256.json`.

- New frontend modules: `js/journey.js`, `js/operation.js`, `js/family.js`, `js/space.js`, plus `v6.css`. Updated current index/app/state/wordmark, guided setup/declarations, RACE/FACE, ACE, inspector, TRACE and Evidence rendering under `brace_app/static/`.
- New backend: `brace_app/discovery.py` and `provenance_origin.py`; bounded additive routes/provenance in `server.py`; presentation/export improvements in `embrace.py` (presentation generator `brace-embrace/0.7.3-v6`). Stable scientific APIs are preserved.
- New focused tests: `tests/test_v6_discovery.py` (28 executed parametrized cases). New portable browser/numerical scripts in `scripts/qa_v6/`.
- Current README, design/motion/capability/decision/limitation notes updated. New V6 task guide, SPACE contract, demo card, pending human checklist, reproduction guidance, actual screen gallery, verification receipts and fresh evidence ZIP under `docs/v6/`. Language inventory regenerated with explicit reviews of the 30 flagged contexts.

No new runtime package, frontend framework, cloud service, LLM, arbitrary model execution or scientific engine replacement was introduced. Existing vendored Plotly, PapaParse and fonts remain local and preserved.

## Scientific and data preservation

Start-of-pass hash reconciliation confirms **15 scientific core files, 101 example/data files and all 34 original test files unchanged**. The complete new suite adds tests without weakening those originals. Existing historical prediction evidence and saved original research artifacts remain intact.

The actual public prepared pair remains **GSE42568 → GSE20711**, GPL570, exploratory ER-positive minus ER-negative tumors:

| Cohort | Downloaded matrix samples | Included | ER-positive / ER-negative | Excluded |
|---|---:|---:|---:|---|
| Source GSE42568 | 121 | 101 | 67 / 34 | 17 non-tumor, 3 missing ER |
| Target GSE20711 | 90 | 87 | 42 / 45 | 2 non-tumor, 1 missing ER |

The target total is **90 in the verified preparation**, not the 88 illustrated in an earlier concept reference. Ten thousand source-filtered features are preserved. Independent calculations from those matrices reproduce 1,339 source-q-passing features, four untestable source features, 20 frozen selections and the 14 supported / 5 same-direction without support / 1 opposite-estimate outcomes. Maximum absolute checked numerical discrepancy is below `6e-15`; tolerance was relative `1e-9`, absolute `1e-12`. Original and fresh Python patch versions differ (3.11.2 vs 3.11.9), so recorded software metadata and the frozen-record hash differ; numerical outcomes agree. See [NUMERICAL_PRESERVATION.json](docs/v6/NUMERICAL_PRESERVATION.json).

GC-RMA vs RMA, ER assay differences, selected-source effect inflation, unadjusted covariates and unauthenticated patient overlap still limit interpretation. This release does not add another biological validation cohort, establish absolute scale equivalence, authenticate independent donors or approve source-trained model transfer for the ER pair. Artificial stress inputs verify software behavior only.

The API still enforces **25 MiB per file, 25,000 features, 500 samples per expression cohort and 50,000 prediction records**. No limit was silently increased. The legacy CLI's separate existing limits were not rewritten.

## Actual new external retrieval

Official GEO ESearch/ESummary and the actual GSE42568 matrix directory returned HTTP 200. A genuine original file was acquired:

- URL: `https://ftp.ncbi.nlm.nih.gov/geo/series/GSE42nnn/GSE42568/matrix/GSE42568_series_matrix.txt.gz`
- Size: **22,565,943 bytes** (compressed), within the 25 MiB acquisition bound.
- SHA-256: **`43b93f72f1d81838dcd2a5b6ccc3bc1875e46230dad0d7346236773a99e32b76`**.
- Status: original file acquired and hashed; **not automatically curated, normalized or approved**. The extra acquisition cache is not duplicated in the release ZIP. Bundled approved inputs remain included unchanged.

[Live metadata receipt](docs/v6/LIVE_DISCOVERY.json), [acquisition receipt](docs/v6/LIVE_ACQUISITION.json) and [SPACE boundaries/reference links](docs/v6/SPACE_CONTRACT.md) record retrieval times, URLs and stage distinctions. Only explicit public query fields go to NCBI; uploaded data are not used. Metadata refresh/cache behavior, endpoint restrictions, bounds and review requirements are documented. A controlled 503 test verifies recovery wording separately from the successful live check.

## Commands and actual outcomes

Executed on Windows with standard **CPython 3.11.9 x64**, project-isolated dependencies; browser QA used separate Playwright **1.64.1**, installed **Chrome 156**. Test servers used isolated run storage and port 8787. See [reproduction instructions](docs/v6/REPRODUCE_QA.md).

| Command / check | Exact outcome | Evidence |
|---|---|---|
| `.venv/Scripts/python.exe -m pytest -q` | **309 passed, 1 warning, 99.89 s** | `docs/v6/pytest_final.txt`; existing Starlette/httpx deprecation warning |
| `.venv/Scripts/python.exe scripts/release_smoke.py` | Historical 680/668; full synthetic computation PASS; reproducibility ZIP PASS | `docs/v6/release_smoke.txt` |
| `v6_journeys.py` | **86 recorded checks PASS**; real public rerun, exact dots/genes/metrics, input recovery, exported artifacts, no page errors or nonlocal browser runtime requests | `docs/v6/qa/receipt.json` |
| `v6_navigation.py` | **38 checks PASS**; previews, committed Back/Forward, same gene, reload, live discovery and three-stage predictions | `docs/v6/navigation/receipt.json` |
| `v6_layout.py` | **108 checks PASS**, 102 screen-matrix captures plus forced-color capture; 1440×900, 1280×720, 390×844, both themes | `docs/v6/screens/receipt.json`; zero flagged text/control-boundary contrast failures in its scan |
| `v6_unseen.py` | **24 checks PASS**, new artificial 2/3/10/30-class inputs with Unicode IDs, exact metrics, missing-class scope and no probabilities | `docs/v6/unseen/receipt.json` |
| `v6_final_paths.py` | **7 checks PASS**, plus explicitly injected 503 recovery | Public exclusion downloads, exact report-frame artifact download, actual TRACE family counts and correct historical operation label |
| `v6_reuse_execution.py` | **7 checks PASS** | ER baseline block, real shift eligibility, form hydration, selected inputs retained and late real completion preserving current view |
| `v6_zoom.py` | **16 checks / 16 captures PASS** | Native Chrome 200% zoom; DPR 2, pinch scale 1; both themes, eight states |
| `v6_numerical.py` | **PASS** | Independent t-test/BH reconciliation, preserved core/data/tests and original/fresh distinction |
| `tools/audit_ui_strings.py` generation | 7,138 rows, 60 source files, 30 reviewed lint contexts | Language ledger/review; regression suite verifies exact coverage |

These are **286 recorded browser checks across the seven receipts**, not 286 human tasks. The contrast scanner is bounded and does not establish WCAG conformance. Screens were reviewed as contact sheets plus representative full-resolution home, RACE, ACE, FACE/setup, methods, new-input and discovery states; they were compared against retained actual V5 screenshots. The [before/after gallery](docs/v6/SCREEN_REVIEW.html) keeps the source screenshots accessible.

Visual critique caught a wrong historical method label and insufficient dark navigation contrast; both were repaired before the final passing run. Regression review caught biological branding leaking into generic prediction reports; domain-neutral behavior was restored without changing original tests. Test harness timing/selector failures were corrected and rerun; only completed passing receipts are counted.

The ZIP's CRC, complete manifest/hash verification and extracted-copy launch are recorded in the separate delivery verification receipt beside the release ZIP. No fabricated fresh installation is implied: extraction/startup reuses the already isolated dependency environment. Python itself and a wheelhouse are not bundled.

## Unresolved issues and explicit limits

1. **Human/device acceptance NOT RUN.** Unfamiliar student/researcher comprehension, actual screen reader, physical touch, projector, target-laptop launch and clean Python 3.13 installation require the [pending checklist](docs/v6/HUMAN_ACCEPTANCE_PENDING.md). Automated checks do not prove universal intuitiveness.
2. **SPACE is discovery plus bounded original acquisition.** Automated scientific curation/preparation, broad crawling, automatic normalization and authenticated patient independence are not implemented or promised. Remote availability/rate limits can change; the curated local example remains usable.
3. **Execution granularity is request-level.** Real start/completion/error and safe navigation are implemented; method diagrams explain the algorithm. No fine-grained backend event stream or cancellation is claimed.
4. **Browser file permissions remain real.** In-session files/drafts can be reused; after reload private files must be reselected for another computation. Saved evidence remains available. EMBRACE omits raw private uploads.
5. **Scientific scope remains exploratory.** No new clinical, causal, performance benchmark or independent human scientific-review claim is made. Pinned gene-symbol annotations are presentation aids, not newly revalidated nomenclature.

The engineering changes are complete for independent review on the tested environment. No further scientific engine or frontend redesign pass was started.
