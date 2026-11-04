# Pass 5 — ACE and contextual TRACE

## Reproduce the real archived-evidence path

Start the existing local launcher. In **Study → Other examples & archived research → CancerShift · CPTAC**, choose **Open archived predictions**. ACE asks **Does the model generalize?** This is archived research evidence, not new CancerShift inference or authenticated independent acquisition.

Read the full-evaluation counts (680 evaluated, 668 correct, 12 incorrect), supported-class metrics, absent true prostate class and uncertainty disclosures. Source CV is unavailable for these records; the interface does not invent a source–target comparison.

In **Confidence Challenge**, the reference threshold is exactly 0.95: 584 retained, 96 withheld, 583 retained correct and 1 retained error. Select 0.99: 432 retained, 248 withheld, 431 correct, still 1 error. This is a descriptive cutoff exploration, not a validated improved policy. Threshold 1 retains none in this archive, so selective accuracy/risk are undefined. **Reset to reference** returns exactly to the original saved point. Keyboard Home/End choose the endpoints; arrow keys move among saved thresholds. Adjusting the threshold does not retrain the model.

In **Errors**, select:

`breast_cptac_gdc::cfc121b5-9562-4a6d-b792-3cd6d5`

The actual row is true **breast**, predicted **ovary**, maximum score **0.998692106** (99.87% displayed). Its five saved class scores are available, with exact values under disclosure. No expression/shift descriptors are attributed to this archived sample. **Trace result** opens that exact sample in run `historical_cptac`; preprocessing/folds and new model inference are explicitly “not performed.” Expand a step to inspect its stored data/configuration/hashes, or download its supporting artifact. **Return to sample prediction** preserves the selection.

For a computed model example, choose **Run synthetic demo**. Source OOF and target results are actual computations on explicitly artificial expression data. They illustrate software behavior, not new biology. ACE shows both evaluation roles, distinct denominators, fold method/seed and the limitation on comparing them. Same-run target sample/PCA descriptors appear only where the saved shift result contains the matching prediction row.

For real RACE evidence, choose the approved public example, select Entrez `135112` in RACE/FACE, then **Trace result**. The six recorded steps follow input cohorts → compatibility → source screen → frozen signature → target tests → the selected gene. Existing expression plots and frozen hypothesis identity are preserved.

## New read-only API contracts

Existing analysis and example API responses remain compatible. Two additive GET endpoints compose saved evidence. No statistical engine is rerun by either endpoint.

### `GET /api/ace/studies/{study_id}?sample_id={optional_exact_id}`

`study_id` is `historical_cptac` or an existing strict 32-character hexadecimal local ACE/shift run ID.

| Field | Recorded origin / behavior |
|---|---|
| `study_id`, `kind`, `mode` | Selected completed run identity and origin category; historical, synthetic and user-supplied evidence remain distinct. |
| `validation` | Existing `mini_validation` contract from checked Stage 06 output: metrics, declared classes/role/independence, records/errors, exact reference threshold, full saved curve, confidence bins, study composition, warnings and interpretations. Null for Mode C. |
| `source_cv` | For Mode B only: `role=source_cv`, exact Stage 05 `outputs.source_cv` metrics, saved fold method/count, seed 42 and explicit unavailable source-interval note. Null for imported/archived scores and Mode C. No new source uncertainty calculation. |
| `source_target_comparison` | Explicit difference in evaluation designs/samples, or unavailable comparison. No performance-difference headline or paired test is manufactured. |
| `frozen_model_hash` | Canonical saved model identity for Mode B, otherwise null. |
| `expected_calibration_error_10bin` | Exact saved Stage 06 descriptive value, otherwise null. |
| `selection` | Null when no sample was requested. Otherwise `{record, related_shift, provenance_note}` for that exact evaluated sample. An ID from another run returns 404. |
| `selection.record` | Saved sample ID, study ID, true/predicted labels, correctness, maximum score, full class score vector and membership at the saved reference cutoff. Missing probabilities remain null. |
| `selection.related_shift` | Only a matching target row from this same checked run's `error_association.samples`, with matching labels/correctness and its target PCA point if recorded. Null for archived/unrelated/missing shift evidence. Descriptive, not a causal explanation. |
| `artifacts` | Checked, allowlisted supporting outputs: path, byte count, SHA-256 and existing local download URL. |
| `scientific_role`, `methods`, `provenance_authenticated` | Saved evaluation role/method/version/interpretation; authentication flag is always false. Declarations are not independent authentication. |

### `GET /api/trace/studies/{study_id}?feature_id={exact_id}`
### `GET /api/trace/studies/{study_id}?sample_id={optional_exact_id}`

Gene mode accepts the same public or user RACE run IDs as Pass 4. It accepts only a gene in the frozen family. Sample mode uses the ACE contract above. Supplying both selection types returns 422. Mode C accepts no sample result selection.

Response fields: `study_id`, `analysis` (`race` or `ace`), exact `selection`, `evaluation_role`, `steps[]`, verified `artifacts`, warnings, software information and `provenance_authenticated=false`. ACE also supplies recorded `kind` and `mode`; RACE supplies the frozen `hypothesis_hash`.

Every step has `key`, `title`, `status`, `data`, and `artifacts`. Status means **computed in saved evidence**, **recorded**, **declared**, or **not_performed**. It never implies the endpoint just performed the step.

| Analysis | Recorded chain |
|---|---|
| RACE | Six steps: methods/input hashes/manifests; saved eligibility/counts/warnings; source-family size/rule/selected source record; frozen hash/IDs; target-family size/methods/selected target record; gene classification/result. |
| Mode A / archived ACE | Six steps: input score provenance; source preprocessing/folds not performed by BRACE; supplied prediction origin declared; new inference not performed; saved metrics/reference/uncertainty; exact sample or aggregate result. Original model/training history is unavailable or declared only. |
| Mode B ACE | Six steps: recorded input hashes; source preprocessing/fold configuration and OOF metrics; canonical frozen model/config hashes, aligned/retained feature counts and preview (complete IDs in model artifact); frozen target scoring; saved Stage 06 metrics/uncertainty; selected sample and same-run descriptors where available. |
| Mode C | Four steps: input hashes; saved unlabeled compatibility; source-fitted projection/feature diagnostics; unlabeled result. No target class counts, accuracy, label-conditioned tests or outcome rows are exposed. |

For historical evidence, `PASS05_ARCHIVED_REFERENCE.json` pins the original scores/manifest and supporting saved report files. For user/synthetic runs, the existing reproducibility inventory verifies artifact bytes/hashes; saved input hashes are checked; safe generated filenames are used; canonical model/config hashes and the Stage 05 freeze identity must agree. RACE uses the existing Pass 4 checked linkage. Unknown IDs return 404. Missing/mismatched ACE evidence returns 409 with restoration guidance. The existing pinned public RACE verifier retains its 503 unavailable response.

These checks detect mismatched files; they are not signatures, acquisition audits or a continuous filesystem monitor. The browser caches the latest checked ACE summary for navigation. Fresh sample and TRACE requests recheck backend evidence; reloading also refetches the summary.

The only additional allowlisted download filename is generated `run_result.json`, already present in scientific bundles, needed to audit source OOF metrics and freeze configuration. Existing path/group restrictions remain. Uploaded raw files and executable models are not made downloadable by this addition.

## Exact metrics and confidence interaction

Stage 06 is unchanged. Accuracy = correct / evaluated. Precision = TP / predicted count; recall = TP / true support. An observed-class F1 = 2TP / (2TP + FP + FN). Balanced accuracy and macro-F1 average only true-supported classes; absent true classes are listed and excluded from those averages. Undefined precision/recall/F1 remain undefined with saved reasons. Confusion rows are true classes; columns are predictions. Exact support, predicted count and TP accompany the rates.

Wilson intervals, class-stratified macro-F1 bootstrap (1,000 replicates, seed 20261101), unavailable reasons and independence/clustering assumptions are displayed from saved results. Bootstrap/intervals are not invented when unavailable. Source Stage 05 OOF intervals were not saved, so the interface states that limitation.

The slider indexes the saved curve entries, which contain the 0.01 grid from 0 to 1 **plus the exact declared reference**, including off-grid values such as 0.955. Its visible output and accessible value text state the actual threshold; it never snaps to a nearby point while showing another threshold. Reference reset selects that exact entry. All other cutoffs remain exploratory. Imported reference declarations and historical references do not acquire a new locked-validation interpretation.

Retained = confidence ≥ threshold, including equality. Counts, coverage, retained correct/errors, selective accuracy and selective risk come directly from the saved point. Withheld = total minus retained. Record filters use the same exact cutoff. Empty retained sets show **No predictions retained**, undefined accuracy/risk, and no selected plot marker. When probability vectors are absent, confidence controls/retained filters are disabled with an explanation. Invalid vectors remain blocked by existing intake.

The plot has full 0–100% axes, labels and a selected operating point; no arbitrary performance magnification. Small layouts permit chart/table scrolling for readable labels. Percentages display two decimals, with at most 0.005 percentage-point rounding error. Counts/IDs/reference thresholds are exact. ECE displays four decimals; raw class scores and full-precision JSON/CSV remain authoritative. No metric/uncertainty calculations are duplicated in JavaScript.

## Verification and review artifacts

`PASS05_BROWSER_RESULTS.json` records 15 final Chrome scenarios and 13 screenshots. `PASS05_LEGACY_BROWSER_RESULTS.json` and `PASS05_RACE_BROWSER_RESULTS.json` retain the rerun receipts for the 20 prior workflows and 11 RACE/FACE scenarios. Original receipts and screenshots are preserved under their historical names.

`pass05_evidence/` contains four actual checked TRACE JSON snapshots: historical error, real public gene 135112, synthetic model sample, and unlabeled software fixture. The two accompanying ZIPs are existing engine-generated research bundles for the synthetic model and unlabeled fixture. `INDEX.json` records hashes and scope. These are inspectable review evidence; random developer-run URLs are not installed runtime history. The stable historical/public examples work directly in the runnable app, and fixture computations can be reproduced from bundled inputs/tests.

Screenshots named `ace_historical*`, `confidence_*`, `historical_high_confidence_error` and `trace_historical_sample` use real archived records. `trace_race_gene` uses real public GEO computation. `*_synthetic`, `trace_mode_c` and `no_probabilities_fixture` are explicitly software evidence. No screenshot is used to claim a new independently validated model or human usability test.

Browser tests use the existing `tests/browser_host.py` spare-port adapter and installed Chrome through developer-only Playwright. Production origins/security are unchanged. See the Pass 4 contract for launching port 8766; execute `python tests/browser_pass05.py --url http://127.0.0.1:8766`. For older scripts on Windows, use `PYTHONIOENCODING=utf-8` to print their existing Unicode test messages. No new runtime dependency was added.
