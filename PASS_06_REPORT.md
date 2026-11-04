# BRACE — PASS 06 REPORT

Date: 2026-11-03. Baseline: approved `BRACE_PASS05_checkpoint.zip`, SHA-256 `032a721e3d6392c24a151fe42a25ae5f083a9e2f0ad4178ae23b0609357f3dd3`.

**Pass 6 is complete for the supported local research workflow.** EMBRACE now exports inspectable standalone scientific evidence. All 240 collected Python cases passed, with zero failures/skips; 53 final browser scenarios passed. No known critical or major defect remains in that supported scope. This is not clinical validation or clean-device certification. Pass 7 has not begun.

## Changes and preservation

The complete working checkpoint builds on Pass 5. It preserves Python/FastAPI, existing API contracts, scientific engines, the 25 MiB upload limit, 25,000-feature limit, public preparation data and original CancerShift evidence. No runtime dependency was added. All previous test files and historical example files remain byte-identical. The only core-file change is closing an intake stream after an early UTF-8 failure; numerical algorithms are unchanged.

Production additions: `brace_app/embrace.py` (standard export/report), `evidence_audit.py` (pre-export arithmetic consistency), `export_safety.py` (safe published CSV/path handling), and `static/js/export.js` (observed preparing/error/retry/download states). Integration changes: `release09.py`, `server.py`, `study_api.py`, `evidence_api.py`, `static/app.js`, `static/js/legacy-results.js`, and `brace_core/intake.py`. Tests/diagnostics added: `tests/test_embrace.py`, `browser_pass06.py`, `benchmark_pass06.py`, `audit_outputs_pass06.py`. Documentation, receipts and seven reviewed screenshots are under `docs/`. The machine-readable `docs/PASS06_CHANGE_LIST.json` lists every changed/added file and confirms no removals; the baseline release hash inventory is preserved separately.

## Critical and major findings

Severity describes the potential impact in BRACE's local research setting; these are not claims of proven remote exploitation.

| Severity | Finding and repair | Verification |
|---|---|---|
| Critical integrity | Cached exports could be returned without rechecking current scientific files or complete ZIP bytes. Export now checks original scientific artifacts, inputs, saved run configuration, published artifacts and ZIP receipts; altered evidence returns 409, without repairing scientific records. | Mutated result, sample CSV, input, configuration and ZIP tests; repeat and concurrent export tests. |
| Critical security | Arbitrary imported text could become a spreadsheet formula in downloaded CSV. Publication-only apostrophe encoding now covers formula/control-prefixed text with a reversible cell ledger. Internal science/JSON IDs and numeric negatives stay exact. | Hostile real API imports, browser HTML inspection, decoded CSV comparisons, download hashes and numeric-sign tests. |
| Major | RACE export lacked a complete standalone scientific report/context and the public RACE evidence screen lacked a complete-package action. | Unified finalizer and real ZIP action; public, archived ACE, computed synthetic Mode B and unlabeled Mode C exports exercised offline. |
| Major security | Run/export file operations could follow Windows directory junctions outside their intended root. All generated/exported path components now reject escapes. | Actual root and nested junctions tested on Windows; outside sentinel untouched. Attack requires local filesystem access. |
| Major | Malformed intake used nonexistent `InputProblem.code`, producing an actual 500. Early UTF-8 failure also left an open stream by inspection, risking Windows cleanup. | Structured 422 response and stream closure; renamed-binary CSV rejected and temporary uploads cleaned. |
| Major responsiveness | Concurrent browser walks exposed heavy synchronous computation inside async request handlers. Parsing, preflight and numerical work now use the existing worker pool. No mathematical routine changed. | Three controlled concurrent-request gates prove health requests remain serviceable during Mode A, RACE and preflight work; complete suite rerun. |

The final small error-handling change also makes missing/changed saved evidence return structured 409 on run inspection. Focused tests passed after that change. Browser download failures preserve selection and offer Retry; a non-ZIP error response is never presented as a successful archive.

## Scientific validation and unchanged findings

The actual public example remains **GSE42568 → GSE20711**, tumor-only ER association: source 101 samples (67 positive/34 negative), target 87 (42 positive/45 negative), 10,000 identical retained features. Original public downloads, hashes, citations, deterministic source-only filtering and inclusion/exclusion records remain in `examples/public_er_pair/`. This pass made no new external download or licensing claim. The initial GSE29431 investigation and prior dataset decision remain documented in the preserved preparation evidence.

An independent vectorized SciPy Welch reference and separate Hedges ranking/BH implementation reproduce the source screen and all selected target tests. Four source features have a constant group and are untestable under the existing BRACE policy: displayed p/q remain null, and p=1 retains those hypotheses in the prespecified 10,000-feature correction family. A naive reference that tests variable-versus-constant groups initially disagreed; aligning the reference with that documented policy resolved the difference without changing the engine.

Unchanged result: 1,339 source q-passing features; 20 source-selected and frozen; 20 target-testable; 19 direction-matching; 14 matching with target BH support; five matching with insufficient target support; one opposite estimate without statistical support; zero untestable. The six without target support include that opposite estimate. Frozen hypothesis SHA-256 remains `8f17b0e452532a9f0add71d4ce96986315d84a609c709d73c3e35890e04f446f`. All five numerical files are byte-identical across the two measured repeats and to the approved prior evidence.

GC-RMA versus RMA, different ER ascertainment, unavailable patient identifiers and unverified donor independence restrict this to exploratory cross-study association support. It does not approve direct expression-scale comparison, source-trained model transfer, causality, biomarker certification or locked clinical validation. Source selection affects interpretation of source intervals; pointwise uncertainty does not solve patient/study dependence.

Archived CPTAC remains **680 evaluated/668 correct**; threshold .95 retains **584/583 correct**. Prostate has no true support. The real breast→ovary error at confidence approximately .998692106 survives both .95 and .99. These are rescored archived predictions, without new inference or invented source CV. Synthetic Mode B checks separately identify source OOF and target scoring. Mode C reports measured shift/PCA only.

`docs/PASS06_OUTPUT_AUDIT.json` records an additional independent output audit of nine exported ACE runs, including the real 680-row archive and explicit software fixtures. Sample counts, confusion/per-class metrics, every available threshold point, calibration and study summaries reconcile. Independent NumPy/SciPy calculations match 840 fixture shift rows; 238 PCA identities/coordinates agree between saved JSON and CSV. The PCA check is reconciliation, not a separately refitted projection. `PASS06_AUDIT_MATRIX.md` maps all scientific adversarial and security cases to executed checks or explicit inspection.

## Package and security contract

`BRACE_EMBRACE_PUBLIC_ER_PASS06.zip` contains **18 standard files, 2,708,610 bytes**. SHA-256: `3363616fd6d7b4db6531853850a3e59f30f602ccd184f0f2ba7946080b518c88`.

It includes offline HTML, full source/target gene tables, frozen signature/configuration, methods, compatibility, warnings/exclusions, provenance, software/input hashes, reproduction/privacy instructions, original preparation README, text-encoding ledger and output inventories. `docs/PASS06_EXAMPLE_INVENTORY.json` lists every member and hash. ZIP CRC, recorded bytes and all listed hashes were verified. The report links locally to machine-readable evidence and labels unsupported/untestable outcomes and historical versus newly computed evidence.

Published CSV hash values describe published safe bytes; original scientific hashes are separately identified. Internal records stay unchanged. Raw uploaded matrices/metadata, arbitrary files, environment secrets, local absolute input paths and executable model binaries are excluded. Derived identifiers/scores still require sharing review. Hashes detect changes against receipts; they do not authenticate acquisition, patient independence or an attacker who replaces every local receipt. Reproduction of private runs requires original hashed inputs. No uploaded ZIP extraction or untrusted-model execution was introduced.

Actual size enforcement (25 MiB+1 → 413), hostile host/origin rejection, traversal, duplicate metadata/features, nonfinite/malformed input, .pkl/.joblib/.exe rejection, HTML escaping, formula safety, cleanup and canary-secret exclusion passed. Limits were not relaxed.

## Commands and exact outcomes

Commands use the isolated `work/venv/Scripts/python.exe`; project commands run with the checkpoint as working directory unless shown otherwise. The unrelated global Espressif installation was not modified.

| Command | Actual final outcome |
|---|---|
| `python -m pytest -q` | **240 passed, 0 failed, 0 skipped, 1 warning, 76.52 s**. All 211 retained cases plus29 new cases executed. |
| `python -m pytest tests/test_embrace.py -q` | **29 passed, 0 failed, 0 skipped, 1 warning, 21.02 s**, after final GET409 error translation. |
| `python scripts/release_smoke.py` | Exit0; historical680/668, synthetic full computation PASS, reproducibility ZIP PASS. |
| `python tests/browser_pass06.py --url http://127.0.0.1:8766` |7 checks passed, no uncaught errors. |
| `python tests/browser_pass03.py --url http://127.0.0.1:8766` |20 checks passed, no uncaught errors. |
| `python tests/browser_pass04.py --url http://127.0.0.1:8766` |11 checks passed in final isolated run, no uncaught errors. |
| `python tests/browser_pass05.py --url http://127.0.0.1:8766` |15 checks passed, no uncaught errors. |
| `python tests/benchmark_pass06.py --work <new-scratch-dir> --record docs/PASS06_BENCHMARK.json --example <example-ZIP>` | Two actual public runs; repeated and approved-prior numerical identity PASS. See exact receipt. |
| `python tests/audit_outputs_pass06.py --runs <browser-scratch-runs> --record docs/PASS06_OUTPUT_AUDIT.json` | PASS; independent saved-output calculations described above. |

The one pytest warning is the existing Starlette/httpx deprecation. Earlier focused work had two failures (reference-policy mismatch and malformed-input bug), both resolved. A preliminary full237-case run passed before the responsiveness repair; the final240-case full rerun supersedes it.

## Performance and browser acceptance

Windows build26300, Intel64 Family6 Model140 Stepping1, eight logical CPUs; isolated Python3.11.2, NumPy2.4.6, SciPy1.17.1, scikit-learn1.9.1. Exact versions are recorded. These are two measured local runs, excluding interpreter/import startup, not population performance estimates.

| Measured phase | Run1 seconds | Run2 seconds |
|---|---:|---:|
| Load/intake validation |1.5692|1.7878|
| Eligibility |.0242|.0381|
| Source screening/freeze |3.0854|5.4551|
| Target tests |.2360|.3159|
| RACE total including write/coordination |4.2306|6.7954|
| Evidence export |2.0236|1.4657|
| Overall |7.8496|10.0695|
| Cached export validation |.2383|.2423|

Peak resident working set: **225,128,448 bytes (214.70 MiB)** for the complete benchmark worker, including imports, both repeats, exports and archived ACE rescoring; not phase-specific allocation. Real archived-score ACE recalculation took **2.5004 s**, not classifier inference. Public-pair source-model transfer is ineligible and was not benchmarked. Source screening was the largest measured computation; no numerical optimization/replacement was introduced. The final example's export-only layout refresh took1.4452s using unchanged numerical files.

Chromium156.0.8078.80:53 final browser checks passed. Seven new screenshots were visually reviewed alongside prior walkthrough evidence. Tests cover primary/error/retry, keyboard selection, narrow390px/desktop layouts, reduced motion and18 computed-color samples (minimum7.695:1). This is not a complete WCAG or screen-reader certification. Recorded Playwright observations: saved-example opening2,278ms; three gene selections847–878ms; threshold changes16.4–17.2ms. They include automation round trips, not unfamiliar-human timings.

Concurrency caveat: initial simultaneous walks exposed request-loop blocking, now fixed. Under heavy concurrent walks/tests the unchanged legacy RACE harness still exceeded its five-second deadline during a large upload/preflight, with a Windows temporary-file cleanup failure. The final unchanged script passed all11 checks alone. The three request-responsiveness gates pass, but stress-load latency certification remains unverified. Full-precision HTML tables require horizontal scrolling; this is a minor readability limitation.

## Remaining limits and skeptical review

No known critical/major release blocker remains for a single local research workflow. Fresh-device startup/installation, other browser engines/devices, screen-reader software, projector use and independent-human testing were not performed. Original historical classifier weights/training evidence are not newly reconstructed. Public donor independence remains unverified. No scientific claim is upgraded by these export or QA repairs.

1. **Does14/20 mean clinical replication?** No. It is prespecified target-family statistical support within an exploratory ER association example, constrained by processing/assay differences and unknown independence.
2. **Can a spreadsheet or changed cached ZIP silently change the evidence?** Published text is reversibly encoded; exact JSON/scientific hashes are separately preserved. Mutated saved evidence/ZIP/configuration fails409. Local all-receipt replacement and authenticated biology are outside hash guarantees.
3. **Do fast runs and a confident prediction establish reliable deployment?** No. Timings are two developer-machine observations; archived high-confidence errors remain. Stress concurrency, cold installs, human use and clinical utility are unverified.

The checkpoint is ready for independent Pass6 review. Approval to work autonomously has been respected; no subsequent pass was started.

## Packaging receipt

Release verification: **278/278 files verified**. The complete checkpoint ZIP contains 280 files including both inventories. ZIP CRC and every recorded SHA-256/byte count were checked after creation. Virtual environments, caches and runtime runs are excluded. All existing tests, historical examples and prior-pass review evidence remain byte-identical; the only core edit is intake stream cleanup. There are 9 changed and 29 added files relative to Pass5, including inventories/review material; no files removed. `docs/PASS06_CHANGE_LIST.json` is the exact list. The separately delivered real EMBRACE example also passed CRC and every inventory hash.
