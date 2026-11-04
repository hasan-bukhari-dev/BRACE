# BRACE — Product Design 3 report

**Disposition: CONDITIONAL for the redesigned checkpoint.** Implemented software and numerical checks pass. The mandatory first-year-student, researcher and generic-prediction-user comprehension evaluations have **NOT RUN**; no human participants or acceptance outcomes are invented. This is not an unconditional design PASS or a new scientific/clinical validation. Stop after this phase.

## What changed

Versioned working copy of the completed Pass 7 archive; the original ZIP remains SHA-256 `5bb0de16f470488cf2a536fe29f86a3fd202355b200d6ae9cb5a2d44050750c3`. Native JavaScript/CSS and Python/FastAPI remain. No framework, runtime package, cloud, model execution or optional external API was added.

Five individually accessible BRACE letter buttons preview/commit measured suffix plates, with fixed glyph positions and plain task captions. Quiet home has one precise purpose sentence and two real actions. System/Light/Dark persist independently of science. RACE leads with the real family outcome, the full table and contextual FACE; ACE is neutral for classification records, with exact saved confidence points; CE owns task-specific checks and source-fitted distribution comparison; E exposes actual local history, TRACE and hash-checked exports. Home/theme/preview retain the run and selections. Interrupted requests show an uncertain outcome and are never automatically rerun.

Additive backend integration: `/api/capabilities`, `/api/runs`, task-specific preflight eligibility and retained shift compatibility counts. Existing endpoints, contracts, origin/path/export controls and limits remain. Reports are result-first and task-aware. For generic predictions, the legacy published HTML is a neutral presentation view; `HTML_PRESENTATION.json` records original-versus-published hashes. Scientific artifacts are not rewritten. Bundle version upgrades verify old evidence/receipts before regenerating a view; tampered cached ZIPs are blocked.

Exact changed/additional paths are in `docs/design3/CHANGE_LIST.json`; source hashes are in the release inventories. Actual screenshots can be browsed offline in `docs/design3/SCREENSHOT_INDEX.html`. Architecture and visual reasons are in `docs/design3/ARCHITECTURE_MAP.md`, `DESIGN_SYSTEM.md` and `VISUAL_DECISION_LEDGER.md`. Before captures: `docs/design3/before`; final captures: `docs/design3/final`; broader workflow captures: `docs/design3/after` (integration state, superseded where final counterparts exist).

## Preserved science and actual evidence

All **15 brace_core files, 96 existing example files and 25 existing test files** match the original ZIP byte for byte. The original historical CancerShift evidence and original public-data preparation/download hashes were preserved. No fresh public download or new dataset eligibility investigation was needed in this design phase.

Fresh actual browser upload of GSE42568 source → GSE20711 target: **101 (67+/34−) / 87 (42+/45−)** tumors; **10,000** source-selected Entrez representatives. Independently written `scipy.stats.ttest_ind`, gamma-based standardized effects, source ranking and a separately written reverse-rank BH calculation reproduce **1,339** source q-pass, **20** selected/frozen, **14** matching with target support, **5** matching without support, **1** opposite estimate. Four source constant-group features remain untestable in the 10,000-member correction family. Maximum absolute selected-output discrepancy was **5.33e-15**, within relative 1e-9 / absolute 1e-12 checks. CSV, JSON, ZIP CRC and published hashes reconcile. See `NUMERICAL_PRESERVATION.json`.

Fresh versus saved frozen source objects differ only in software metadata and its resulting hypothesis hash (Python 3.11.9 versus 3.11.2); source screen, chosen IDs and statistics are unchanged. No version metadata was falsified to force an equal hash.

Eligibility stays **exploratory within-cohort association and selected-gene target testing**. GC-RMA/RMA processing, EIA/IHC ER ascertainment, missing source donor IDs, unknown cross-study donor independence and confounding do not support direct absolute-scale comparison, model transfer, causality or clinical biomarker claims. The ER pair remains blocked for the existing normal/tumor baseline.

Historical CPTAC remains **668/680** correct; cutoff .95 retains **584/680**, **583** correct; .99 retains **432**, **431** correct, with the actual score .998692106 breast→ovary error still inspectable. Source baseline artificial fixture remains **13/20** source OOF and **11/14** target correct; these are separate designs, not a real ER transfer result. Mode C excludes outcome-based accuracy. Two explicitly controlled non-biological six-record fixtures each give **4/6** correct and, at .95, **1/2** retained correct; cutoff 1 retains none with undefined selective accuracy/risk. No field-data performance claim follows.

## Commands and exact outcomes

Available Windows host; standard isolated **CPython 3.11.9 x64**, NumPy 2.4.6, SciPy 1.17.1; Chrome **156.0.8078.80** through developer Playwright. Production `launch.py`, loopback **8766**, explicit external scratch run directory. Global Espressif installation was not changed. Existing pinned dependencies/wheelhouse remain compatible and unmodified.

| Check | Actual outcome |
|---|---|
| `python -m pytest tests/test_design3_integration.py tests/test_embrace.py -q` | **38 passed**, one existing Starlette/httpx deprecation warning, **24.78 s** |
| `python -m pytest -q --junitxml=docs/design3/pytest_full.xml` | **262 passed / 0 failed / 0 skipped**, same warning, **224.50 s**; all 249 prior cases retained, 13 new cases |
| Final `python -m pytest tests/test_design3_language.py -q` | **4 passed**, final source/ledger consistency and unchanged scientific bytes; final output log retained |
| `python scripts/release_smoke.py` | **PASS**, archived 680/668, full synthetic calculation and reproducibility ZIP |
| Broad real browser journey | **71 passed checks**, **103.423 s**; no page errors or unexpected HTTP errors |
| Rendered accessibility/interaction audit | **94 passed assertions**, 14 screen audits; text/control contrast, AX names, unique IDs, forward focus, themes/reload, local-only browser route, held-request interruption, page magnification/reflow |
| Final detail browser check | **22 passed checks**; suffix-plate composite contrast in both themes, CE counts/pagination/small-q, reverse dialog focus, interrupted-request cleanup, resize/animation geometry |
| Final import-purpose browser check | Receipt retained in `docs/design3/final/import_receipt.json`; **6 passed checks**; heading/focus/native-file retention and actual ER baseline rejection in both themes |
| Independent numerical/preservation audit | **PASS**, actual matrices and fresh exported rows; all original core/examples/tests preserved |

A separate mixed pointer/keyboard check also passes: keyboard preview overrides a stationary pointer and Enter commits the focused task. All JavaScript modules pass `node --check`. Final small JavaScript/copy/focus/import repairs were verified with targeted browser and language checks after the complete suite; scientific/backend code stayed unchanged. Existing old browser scripts are preserved but have obsolete selectors/copy for the intentionally replaced UI and are **not claimed as rerun acceptance**. New developer browser harnesses cover their critical workflows. Default restricted process execution stalled, so those owned attempts were stopped and the isolated tests ran through the normal reviewed execution path. No failed/stalled run is counted as PASS.

Early checks found and repaired missing-run-folder indexing, generic report biological wording, cached-bundle upgrade integrity, dialog focus escape, task-heading refresh, native retained-file display and interruption messaging. Harness-only issues (stale hidden-table selectors, resize observer timing, focus setup and controlled-request teardown) were corrected or isolated. The passing accessibility run emitted one developer Playwright cancellation diagnostic while closing its deliberately held request; the final detail run explicitly aborts/cleans that request and passes without that diagnostic. This was not an application page error or a computed-result failure.

The checkpoint build verified **529/529 source-manifest files**, **531 ZIP entries**, ZIP CRC and every manifest member SHA-256. Runtime environments, run folders, caches and the optional unchanged wheelhouse are excluded. The final ZIP hash is delivered separately in `BRACE_PRODUCT_DESIGN_V3_PACKAGE_VERIFICATION.json` beside the checkpoint; the archive cannot contain its own final hash. `python verify_release.py` passed.

## Language, accessibility and remaining gates

`UI_STRING_LEDGER.csv`: **5577** conservative source entries across **45** production files, including internal literals, dynamic JS templates, ARIA, reports, filenames and backend exception paths; **8** generated-value policies cover exact user/JSON/result fields. **27** lint matches have exact hash-keyed context decisions; no scientific vocabulary was automatically replaced. This is inspectable coverage and contextual source review, not a human comprehension study. The test rejects stale/missing entries or unreviewed new lint flags.

Real captures were inspected individually for key pages and through all 19 contact sheets (170 regions) for normal/empty/error/busy/dense/narrow/theme states. Visual changes remove the sidebar, repeated cards and undefined generalization language; preserve scientific density; add source/target shapes and exact tables. Critical text/control/plate contrast passes the recorded sampled screens, not every conceivable OS/browser combination. FACE requires internal scrolling for exact statistics/Trace at 720px height. Full-precision report cells can wrap; CSV/JSON remain exact numerical authorities.

**Not run / partial:** the three actual human comprehension evaluations; NVDA/JAWS or other real screen reader; physical touch/slow hardware/projector; clean OS/event laptop/default-port acceptance; physical Wi-Fi switch-off; narrated 150-second pitch; official competition-rule verification. 720x450 reflow and 2x browser page magnification are recorded separately, not misreported as native desktop Chrome zoom. Browser-only external-request blocking passed; it is not a new clean-machine installation study. The existing dependency warning remains. Optional external lookup APIs are **not applicable**.

The saved example took **5.047 s** and fresh public calculation **23.397 s** in this developer run; not a general performance benchmark or startup measurement. Peak memory/startup latency were not remeasured. The narrated demo remains **TARGET ONLY, ≤150 s**: B public example → RACE complete 14/5/1 family → NCOA7 FACE and separate axes → exact gene TRACE → actual evidence ZIP/report. No participant or presentation result is invented.

## Skeptical review and bounded next work

1. **“Same platform does not prove replication eligibility.”** Correct: the design preserves processing, ER-definition and donor-authentication limits; it supports exploratory within-study comparisons, not direct scales or locked transfer.
2. **“A generic prediction tool might silently retain biological assumptions.”** Actual equipment/text fixtures compute/export with neutral visible and published-report language. Their raw scientific schema stays exact; Mode C and baseline remain biological-expression contracts, not arbitrary data support.
3. **“Attractive navigation is not proven usable.”** Correct: keyboard/touch/focus/contrast/state checks and real workflow captures pass, but actual first-year-student, researcher and generic-user comprehension is still untested. Full design acceptance stays conditional.

No known critical numerical/security or primary-workflow defect remains in exercised scope. The next allowed work is the bounded human/screen-reader/hardware review and only repairs demonstrated by it. Do not start a new science engine, design phase or migration. Independent external review remains welcome; this report's internal calculations/tests are evidence, not an independent human approval.
