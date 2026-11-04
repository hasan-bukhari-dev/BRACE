# BRACE 1.1.0-dev implementation and acceptance report

November 4, 2026. Working branch: `release/brace-integration`. Base commit: `871472bc6a9be8387930218b4340ba3e10b83006`.

The core dataset-to-analysis integration is implemented and verified. This is an unsigned development preview, with release acceptance still conditional on the explicitly untested items below. No existing GitHub branch, tag or published release was overwritten.

## Baseline and confirmed defects

The uploaded ZIP and checkout contained the same 263 files, with no differences. The original public recipe, scientific examples and original scientific engine bytes are preserved. The original audit was also read from the earlier project conversation. Its two diagram images were not accessible as image contents in this session; the new architecture diagram reflects the actual inspected code.

Confirmed in code and/or actual execution:

- Submitted study names were replaced by fixed names; RACE responses also used a generic title.
- Reopening a run without cohort identities could borrow draft identities from another study.
- Run history selected filesystem iteration entries and folder modification times, which change during export.
- SPACE acquisition ended without persistent preparation/analysis handoff.
- The reviewed GSE20711 original is 26,895,121 bytes, exceeding the generic 25 MiB acquisition limit. The live workflow reproduced this blocker.
- The scientific protocol referenced five absent internal documents.

The first complete baseline run reported **316 passed, 1 failed in 158.96 seconds**. The failure was the launcher correctly rejecting the default ESP-IDF Python installation used to create that first environment. The project environment was recreated using the installed standard Python 3.12.10 and pinned release dependencies; the launcher test now passes. A separate interrupted run failed because the system disk filled. Only this session's disposable environments and confirmed test-output folders were cleaned; original source, private data and the ESP-IDF installation were preserved. The optional `--brace-clean-temp` test flag bounds retained verification outputs.

## Before and after

| Area | Before | Implemented behavior |
|---|---|---|
| Public discovery | Search/download receipt followed by manual file juggling | Acquisitions register automatically; reviewed or explicit general preparation creates reusable dataset versions |
| Reviewed target download | GSE20711 blocked at 25 MiB | Exact 26,895,121-byte exception for one official URL, requiring its pinned SHA-256; generic limits stay unchanged |
| Dataset identity | Browser-local `File` map | Transactional SQLite registry, immutable hashed assets, transformation versions and complete ancestor snapshots |
| Analysis handoff | Upload the same data again | Registered IDs resolve to verified assets server-side and delegate to existing ACE/CE/RACE execution paths |
| Task decisions | Detached from discovery | Pair/task/contrast-specific preflight receipts, visible blockers and retained unsupported originals |
| Study/run context | Generic names and possible stale cohort fallback | Named studies, fixed version assignments, separate run IDs, authoritative timestamps and run-specific identities |
| Frozen models | CLI capability without a corresponding workbench flow | Verified source freeze applied to registered targets; labeled evaluation or honest prediction-only output |
| Evidence | Strong scientific artifacts with disconnected preparation context | Original acquisition URLs/hashes, preparation/mapping versions, exclusions, parent records and exact run identities in TRACE/EMBRACE |
| Interface | Separate discovery and file setup | Persistent workbench library, existing-study selection, labeled public-contrast review, contextual results and exports |
| Export publication | Separate writers and partially written output risk | Shared atomic publisher; verified deterministic ZIP, controlled aliases and a manifest committed after the package |

## Implementation checklist and final acceptance matrix

“Fixed and tested” means the cited execution path ran. “Partial” and “deferred” are not release-completion claims.

| Requirement / audit issue | Status | Main implementation and evidence |
|---|---|---|
| P0 baseline and regression fixtures | Fixed and tested | Original suite, independent public SciPy comparison and `quality/INTEGRATION_REGRESSION.json` |
| P0 submitted study names | Fixed and tested | `server.py`, `persistence.py`, `study.js`, reports/manifests; Unicode name round trips in `test_dataset_workflow.py` |
| P0 stale cohort identities | Fixed and tested | `state.js`, run-specific manifests and reload activation; actual Node module test plus browser reload |
| P0 canonical persistent dataset/study/run identity | Fixed and tested | `dataset_registry.py`, transactional records, exact role assignments and immutable assets; restart/reopen tests |
| P0 SPACE acquisition registration | Fixed and tested | `discovery.py`, `dataset_api.py`; live discovery of both accessions and real original downloads |
| P0 reviewed preparation → analysis | Fixed and tested | Pinned public recipe outputs, hashes and parent records; real API, browser and bundled-app RACE runs |
| P0 general supported matrix preparation | Fixed and tested | Bounded gzip parser, explicit labels/exclusions, finite cells and reviewed mapping; general-format fixture reaches real CE and RACE |
| P0 unsupported GEO handling | Fixed and tested | Specific parser/format/resource blockers; original remains downloadable; malformed/truncated/NA fixtures |
| P0 ACE/CE/RACE task routing | Fixed and tested | Existing core gates remain authoritative; public ER baseline blocked; registry references passed server-side |
| P0 exact evidence and lineage | Fixed and tested | `evidence_api.py`, `molecular_api.py`, `embrace.py`; ancestor acquisition receipts, same-run FACE/TRACE, ZIP hash checks |
| SPACE supplementary/SOFT acquisition | Partial | Official study links and matrix acquisition are available; a general supplementary/SOFT importer is not implemented. The parser explains the supported format and preserves other acquired evidence |
| P0 schema versions and boundary validation | Fixed and tested | Versioned request models, rejected unknown versions/extra fields/duplicate JSON/nonfinite JSON, bounded JSON body |
| ACE generic binary/multiclass predictions | Preserved and tested | Existing equipment/text-category and prediction suites; names, persistence and exports are task-neutral |
| ACE source-only baseline | Preserved and tested | Original source-only training/CV and target scoring; synthetic application/bundle tests |
| ACE frozen replay, including unlabeled targets | Fixed and tested | `frozen_workflow.py`; safe existing JSON freezes only, exact feature contract, no target refit, no unlabeled accuracy |
| CE structural compatibility versus shift | Preserved and tested | Existing checks and descriptive source-fitted projection; no biological/clinical causation claim |
| RACE source freeze and independent target testing | Preserved and tested | All original engine bytes unchanged; numerical fields exactly match the baseline |
| FACE actual measurements | Preserved and tested | API and browser inspection of NCOA7, exact group sizes and separate expression axes |
| TRACE saved-prediction scope | Preserved and tested | Records BRACE evaluation, not the unknown external model's internal reasoning |
| Unlabeled TRACE/evidence excludes phenotype results | Fixed and tested | Recursive structural provenance sanitization; existing leakage test caught and verified the correction |
| P1 study-centered workspace | Implemented and browser-tested | Registry, existing-study selection, source/target choices, labeled contrast review and direct compute; independent-user acceptance pending |
| P1 brand/family preservation | Preserved and inspected | Existing BRACE assets and navigation retained; FACE/TRACE remain contextual; EMBRACE remains the result completion path |
| P1 extensible assay metadata | Implemented and tested | `assays.py`, `/api/assays`, shared interface catalog; original scientific acceptance stays conservative |
| P1 identifier interoperability | Implemented for reviewed/manual mappings | Lexical hints require review; deterministic one-to-one mappings and loss reports; no live universal annotation resolver |
| P1 phenotype interoperability | Fixed and tested | Reviewed complete condition mapping, biological definitions, role-version changes and preserved expression hash |
| P1 history organization and ordering | Fixed and tested | Newest 50 by recorded creation time; explicit legacy fallback; study/dataset/run separation and export-touch regression |
| P1 naming and filenames | Fixed and tested | Human titles preserved; immutable IDs; original filenames retained in provenance and controlled internal asset names |
| P1 module boundaries and code consolidation | Implemented in changed paths | Registry, preparation, application API, replay, persistence and evidence publication have separate ownership; numerical engines reused |
| P1 legacy CSS/result consolidation | Deferred deliberately | These layers still implement active chart/setup/result behavior. Removing them without equivalent visual coverage would risk existing workflows |
| P1 type safety/static checks | Improved; partial whole-codebase coverage | Pydantic request contracts, Python hints, Node syntax checks and executed state tests; no claim of full mypy/TypeScript conversion |
| P1 resource limits and failure safety | Tested within supported bounds | Streaming gzip limits, 2 MiB JSON, original upload limits, staged/transactional records, atomic exports and integrity rejection |
| P1 security | Tested for changed boundaries | Controlled paths, no arbitrary URLs/model binaries, foreign-origin rejection, original input exclusion, safe CSV encoding and corruption tests |
| P1 performance | Bounded changes; no large-scale claim | Deduplication avoids recopying existing versions; parser retains only requested prepared features; no arbitrary general limit increase |
| P1 documentation/API/architecture | Fixed and checked | `DATASET_WORKFLOW.md`, `ARCHITECTURE.md`, generated `API_SCHEMA.json`, expanded API guide and repaired protocol links |
| P1 Windows packaging | Built and tested as portable | Actual bundled runtime: public analysis, FACE/TRACE, export hashes, original receipts, restart/reopen and frozen demo |
| P1 installer install/uninstall | Not run for this version | Existing released installer remains V6; this deliverable is a separate portable development preview |
| P1 macOS/Linux source/native verification | Not run in this session | Preserved source/build configuration; no new cross-platform acceptance claim |
| P1 accessibility and human usability | Partial | Keyboard compute path, visible focus, 390 px layout, no duplicate IDs/unlabeled visible inputs in inspected view; screen-reader, unfamiliar-user and physical-device tests pending |
| Additional processed proteomics/tabular assays | Deferred with scientific justification | No validated modality-specific fixtures/protocol supplied; widening numerical acceptance would undermine preserved scope |
| Metabolomics/methylation/single-cell/raw preprocessing | Scientific capability limitation | Explicitly unimplemented; requires distinct representation, processing and statistical validation |
| P2 additional comparison dashboards | Deferred | Core integration and evidence integrity took priority; no decorative or fabricated analytics added |

## Verification receipts

- Complete final suite: **336 passed, 1 warning**. The recorded final run took **526.31 seconds** while other verification/build work also ran. The warning is the existing Starlette/httpx test-client deprecation; no test was skipped or disabled to obtain a pass.
- All **27 application JavaScript modules** passed Node syntax checking. The final interface-language/state checks passed **5 tests** after the labeled contrast refinement.
- Public scientific regression: source 101 samples / target 87; 10,000 screened features; 20 selected; 19 matching directions; 14 matching-direction target supports. Every scientific field in the result, signature and methods matches the captured baseline exactly after excluding software metadata and its dependent digests. Original run hashes remain untouched. Independent SciPy checks passed at `rtol=1e-10`, `atol=1e-12`, with maximum observed discrepancy below `7e-14`.
- Baseline/after engine timings were 6.18/5.08 seconds; these are individual observations on different Python runtimes, not a general speedup claim.
- Existing offline smoke: archived predictions **680 records / 668 correct**, full synthetic computation and reproducibility ZIP passed.
- Live browser: discovered both official studies, acquired both originals, reused registered preparation, reviewed contrast/processing, computed RACE by keyboard, inspected FACE and TRACE, downloaded a real evidence ZIP, and verified all **31 inventoried members** against SHA-256.
- Responsive inspection: 390 px viewport, no horizontal document overflow; no duplicate IDs or unlabeled visible form inputs in the inspected view. This is not full WCAG conformance or a screen-reader acceptance test.
- Windows portable: bundled Python ran the public workflow, checked every exported member, preserved original acquisition ancestry, reopened the exact result after process restart, and retained synthetic provenance during frozen replay. See `quality/PORTABLE_VERIFICATION.json`.

Repeat the principal checks from the repository root:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
.\.venv\Scripts\python.exe -m pytest -q --brace-clean-temp
.\.venv\Scripts\python.exe scripts\run_public_race.py --out work\public-check
.\.venv\Scripts\python.exe scripts\release_smoke.py
.\.venv\Scripts\python.exe verify_release.py
.\.venv\Scripts\python.exe scripts\verify_portable.py --app dist\BRACE\BRACE.exe --out work\new-portable-check
```

Use a new empty output directory for each scientific/portable verification. The portable check terminates only the app process it launches and leaves its isolated evidence available for inspection.

## Launch and remaining acceptance

Windows portable: extract the **entire** `BRACE-1.1.0-dev-windows-x64-portable.zip`, then open `BRACE.exe`. Keep the controller open while working; Stop & close stops its local server. Python is bundled. This is unsigned development software, not the previously published installer.

Source: use a standard 64-bit Python 3.11–3.13 installation, run `SETUP_BRACE_WINDOWS.bat`, then `START_BRACE_WINDOWS.bat`. Standard Python 3.12.10 with `requirements-release.txt` was exercised here. The launcher intentionally rejects ESP-IDF Python. Generic macOS/Linux source instructions remain in README, without a new platform-verification claim.

Use **Add reviewed public ER datasets → review → check → compute** for the complete public demonstration. Private input and other supported GEO preparation directions are in [DATASET_WORKFLOW.md](DATASET_WORKFLOW.md).

Scientific limitations remain: declared rather than authenticated independence, exploratory unadjusted RACE, processing/phenotype differences, no clinical validity claim, independent-row uncertainty assumptions and supported-assay restrictions. Engineering acceptance still outstanding: unfamiliar-user/screen-reader tests, this version's installer lifecycle, macOS/Linux execution, broader resource profiling and incremental replacement of active legacy UI layers. These are explicit release limitations, not claims of completed verification.
