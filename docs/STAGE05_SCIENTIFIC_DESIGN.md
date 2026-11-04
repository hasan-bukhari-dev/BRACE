# Stage 05 — Scientific method and provenance

## Mode A: supplied prediction evidence

- The unit of analysis is one `sample_id`; rows sorted lexicographically by sample ID to avoid accidental positional joins.
- `prediction_manifest.json` defines exact class labels, probabilities per class and source/target role; confidence calculations require a complete finite vector, values in [0,1], and row sum within 1e-4 of 1.
- All metrics are computed directly from supplied reference labels and predictions. A manifest's statement about provenance or independent evaluation is **an assertion by the submitting researcher**.
- Accuracy = correct / total; per-class precision = TP/(TP+FP) when predictions exist; recall = TP/(TP+FN) when true support exists; F1 = 2TP/(2TP+FP+FN) for true-supported classes with positive denominator, otherwise 0 when a true class was fully missed. Absent true classes have recall/F1 null with reasons. Macro F1 averages **true-supported** classes only; denominator and missing true classes reported. Balanced accuracy averages recalls over observed true classes only.
- Retained sample policy: max modeled class probability >= predeclared threshold. Coverage = retained / total; accuracy among retained = retained correct / retained when any retained, else null/EMPTY_RETAINED_SET. A score of 0.99 is a model output, **not calibrated 99% clinical certainty**.
- A posthoc threshold curve is left to Stage 06; altering the frozen threshold after consulting target labels would be exploratory, not independent confirmation.

## Mode B: source-only baseline

- Stage 04 preflight validates assay units, matching feature identifiers, patient overlap, source and target class vocabulary, sample counts, recorded processing, and declared study roles. It may inspect **target class-support metadata for eligibility**, but no target labels enter model hyperparameter selection, source CV, preprocessing, or target prediction generation.
- Shared feature intersection is determined by identifier *presence*, sorted once before training; target *values* do not influence any fitted step. Feature coverage can be the only feature-selection information obtained from the target.
- Source CV: deterministic seed=42; 5 stratified folds for independent source samples with >=5 per class. If actual repeated patient IDs occur, stratified grouped folds are attempted with k=5, then 4, then 3 only when both classes occur in each test and train split. If all fail, training is blocked. Unknown patient identity remains a provenance caveat.
- Pipeline trained freshly inside each fold: `VarianceThreshold(0)` -> `StandardScaler` -> `LogisticRegression(C=1.0, L2 default, class_weight='balanced', max_iter=2000, random_state=42)`. Internal source predictions are out-of-fold, not in-sample.
- A final pipeline is fit on all source samples, then saved as `frozen_model.json`, containing exact feature order, selected variable columns, scale mean and divisor, numeric logistic coefficients, intercept, classes, configuration and hashes. The frozen numerical transform and coefficients are used for target predictions.
- Default target evaluation threshold is 0.95 on max class probability; class predictions themselves use the logistic model's argmax. `true_label` is joined only **after** frozen target prediction generation for result metrics and CSV.
- Two tests deliberately scramble target labels and alter target values. In the first case, model and predictions are unchanged. In the second, source model and CV are unchanged but target predictions respond. These tests enforce the key source-only contract.

## Frozen replay contract

- Never load `.pkl`, `.joblib`, or arbitrary code. Parse only a BRACE JSON freeze artifact and verify its content hash before using coefficients.
- Require identical gene namespace, compatible processed assay type and same microarray platform where applicable; all required frozen features must be present in target input. Unlabeled replay returns predictions but no performance statistics.
- Difference in preprocessing descriptions is explicitly warned; BRACE does not apply transformations beyond the *source-fitted* scaler already part of the frozen model.
- This integrity digest detects unintended changes, not cryptographic provenance authentication; a hostile editor who recomputes all hashes cannot be excluded by SHA alone.

## Historical reference

The `CANCERSHIFT.zip` source's `evidence/v08/scoring/scored_predictions.tsv` was converted without redoing inference, and preserves original ensemble probability values. The one-shot evaluation contains 680 rows. New BRACE metrics are recomputed from those historical prediction records; these are **not** new predictions produced by the Stage 05 baseline. The package records the original evidence file's SHA-256 for traceability.

## Known limitations / next stage

- Stage 03 public GEO matrices remain absent from the current workbench: no real external-training cohort has been fitted here.
- No uncertainty intervals, per-study inferential summaries, calibration plots, or exhaustive confidence-risk curves (Stage 06).
- CLI, unit and smoke tests verified on Linux/Python 3.13. A Windows native GUI run has not been verified.
- This is strictly a research tool and not a diagnostic or clinical decision system.
