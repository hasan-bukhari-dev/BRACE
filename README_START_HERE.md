# BRACE 1.0 — V6 workflow refinement

**Biological Reliability Assessment across Cohorts and Experiments.** A local research workbench for comparing gene-expression associations between studies and evaluating saved classification predictions against known labels.

This is the approved V5 visual design with the V6 navigation, interpretation, adaptive-input and public-discovery improvements. The existing working directory is updated in place; its legacy folder name may still contain V5. Current evidence: [V6 report](PRODUCT_REFINEMENT_V6_REPORT.md), [actual V5/V6 screenshots](docs/v6/SCREEN_REVIEW.html), [quick task guide](docs/v6/USER_TASKS.md), [demo card](docs/v6/DEMO_CARD.md). Earlier pass/design reports are historical checkpoints.

## Start on Windows

1. Extract the complete ZIP to a writable directory. Keep the relative folders together.
2. Install standard 64-bit CPython 3.11–3.13 if needed. This release was executed using **3.11.9 x64**; a fresh 3.13 installation has not been retested. Do not use the unrelated Espressif interpreter.
3. Run **SETUP_BRACE_WINDOWS.bat** while online. Project dependencies go in `.venv`; global packages are unchanged. Python and offline wheels are not bundled.
4. Run **RUN_RELEASE_CHECKS_WINDOWS.bat** to verify file hashes, pytest and the scientific smoke check.
5. Run **START_BRACE_WINDOWS.bat** and open the exact address it prints. Keep its terminal open; Ctrl+C stops the server.

The default is `http://127.0.0.1:8765`. If occupied, the launcher reserves another loopback port through 8785 and prints that address. It leaves other services running. You can explicitly set `BRACE_PORT` to an unused local port. If an explicit port is occupied, launch stops with recovery instructions instead of opening a misleading page.

If the Python launcher selects a vendor interpreter, set `BRACE_PYTHON_EXE` to the full path to standard Python before setup. Once `.venv` exists, launch and checks use it. `BRACE_NONINTERACTIVE=1` suppresses pauses; `BRACE_NO_BROWSER=1` suppresses opening the browser. Neither changes scientific computation.

## Your first result

- **Open saved public result** reads the included GSE42568 → GSE20711 exploratory ER-association evidence. No new statistical test is performed by opening it.
- **Run the public example again** loads the exact verified files into guided setup. Review the biological contrast and processing disclosures, check inputs, then compute. The complete ready-to-use input bundle can also be downloaded.
- **Use my data** explains which supported task fits expression studies or saved predictions. Guided declarations avoid mandatory manual JSON editing; existing JSON remains supported.
- **SPACE · Find public datasets** searches official GEO metadata, verifies actual Series Matrix filenames and can acquire a bounded original gzip with a hash receipt. Candidates are not automatically prepared or scientifically approved inputs. [Discovery contract](docs/v6/SPACE_CONTRACT.md).

The prepared public example includes 101 source tumors (67 ER-positive / 34 ER-negative) and 87 target tumors (42 / 45), with 10,000 source-filtered features and 20 source-frozen associations. Fourteen have target BH support in the matching direction, five match without support and one has an opposite estimate. Original downloaded matrix totals are 121 and 90; exclusions are inspectable. GC-RMA/RMA, ER-assay and donor-independence limitations remain. This does not approve pooled absolute expression scales, clinical validation or model transfer.

Historical CancerShift demonstrations use saved predictions (668/680 correct); they do not rerun the original classifier. The synthetic expression baseline is explicitly artificial. Every operation has a compact **Method & steps** receipt. FACE shows actual measurements, TRACE explains the recorded calculation, and EMBRACE packages the evidence.

## Offline use and reproduction

After dependencies are installed, bundled data, computations, fonts and charts run locally without an account, CDN or external API. Uncached SPACE requests need internet. Offline runtime is different from offline first installation: prepare a matching wheelhouse with `PREPARE_OFFLINE_WHEELS_WINDOWS.bat`, transfer its complete `wheelhouse/` folder, then use `INSTALL_OFFLINE_DEPS_WINDOWS.bat`. No wheelhouse is included in this complete source/data ZIP. Rehearse on the actual destination machine.

EMBRACE includes reports, machine-readable results, settings, warnings, hashes and reproduction guidance. Raw uploaded inputs are omitted; reacquire matching originals to recompute. Extract the ZIP before following report-relative artifact links. Public symbol annotations are a provenance-pinned presentation legend, not a new nomenclature validation.

## Verification and boundaries

V6: **309 pytest tests passed**, the offline scientific smoke passed, and browser checks covered public recomputation, historical evaluation, synthetic baseline, unfamiliar prediction inputs, exports, navigation, both themes, narrow viewports and native 200% Chrome zoom. See the current report for exact counts and commands. Scientific engines, bundled datasets and all original regression test files are preserved byte-for-byte.

The API limits remain 25 MiB per file, 25,000 features, 500 samples per cohort and 50,000 prediction records. Supported RACE inputs are declared normalized log2 human microarrays; raw sequencing, automatic normalization and arbitrary model execution are outside scope. [Scientific protocol](docs/SCIENTIFIC_PROTOCOL_1_0.md), [known limitations](KNOWN_LIMITATIONS.md).

Human student/researcher comprehension, physical touch/projector testing, actual screen-reader operation and a fresh target-laptop Python 3.13 installation remain **NOT RUN**. [Pending task checklist](docs/v6/HUMAN_ACCEPTANCE_PENDING.md). No claim of universal usability, clinical validation or completed human tests is made.

`FILE_SHA256_MANIFEST.csv`, `CHECKPOINT_SHA256.json` and `verify_release.py` identify the release payload. `.venv`, runtime `runs/`, caches, scratch work and browser profiles are excluded. Automated test receipts and before/after screenshots are included for independent review. Preserve the original CancerShift records and disclosure documents when sharing the work.
