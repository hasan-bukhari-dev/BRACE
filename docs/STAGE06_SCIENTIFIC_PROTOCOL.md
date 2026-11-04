# Stage 06 — Scientific protocol

## Unit, labels, and evidence boundary

- Unit of evaluation: exactly one prediction per unique sample ID. Stage 05 prediction import sorts samples deterministically and rejects duplicate IDs or unmapped class names.
- Declared class universe comes from a manifest or frozen model. Confusion matrix rows = **true labels**, columns = **predicted labels**, both in the declared order.
- **Mode A:** imported predictions and reference labels are scored; this is not model inference. Model probabilities are optional, but when supplied must be complete, finite, [0,1], sum to 1 within 1e-4, and agree with unique argmax.
- **Mode B:** Stage 05 trains only from source values/labels (using fold-contained preprocessing), freezes coefficients/scaler in JSON, and scores target predictions afterward. Target feature *presence* establishes shared features, but target *values or labels* never tune the model. Stage 06 computes post hoc metrics from the frozen predictions.
- **Replay:** applies existing, verified JSON coefficients without deserialization or refitting; if target truth is unavailable, reports no accuracy or uncertainty.

## Metrics and mathematical definitions

Let `C` denote the declared class list and `C_obs` those with positive true support in this evaluation.

- `accuracy` = correctly classified / all samples, defined for positive sample count.
- `precision[c]` = TP / (TP + FP) when that class has predicted samples, otherwise **null / NO_PREDICTIONS**.
- `recall[c]` = TP / (TP + FN) when that class has true support, otherwise **null / NO_TRUE_SUPPORT**.
- `F1[c]` = 2TP / (2TP + FP + FN) for a true-supported class; **0** for a fully missed but present class, **null / NO_TRUE_SUPPORT** if true class is absent.
- `supported_class_macro_f1` = mean F1 across `C_obs`; exposes its denominator and absence list; never treated as full-universe score when `C_obs != C`.
- `balanced_accuracy_observed` = arithmetic mean of recall over `C_obs`; unobserved classes excluded and flagged.
- `confidence` = maximum class probability; no calibration guarantee.
- At predeclared threshold `t`: retained iff `confidence >= t`, including equality. `coverage` = retained / all, `selective_accuracy` = retained correct / retained if retained > 0 else null; `selective_risk` = retained errors / retained if retained > 0 else null.
- `threshold_curve.csv` enumerates thresholds 0–1 every 0.01 plus the exact predeclared t. **Only** t is labeled `predeclared_reference`; all other grid points are exploratory. Displaying a curve does *not* preserve the blindness of a threshold chosen after inspecting target labels.
- `confidence_bins`: ten equal-width bins over [0,1], with final bin including 1. Mean model confidence and observed correctness per nonempty bin.
- `expected_calibration_error_10bin` = sum per bin `count/N * abs(bin_accuracy - bin_mean_confidence)`. This is descriptive, binning-dependent, and **not proof of calibration**.

## Uncertainty

- `accuracy_wilson_95`: Wilson-score 95% interval for correct/N; per-class recall and precision intervals use respective supports/denominators; retained coverage and retained accuracy have analogous Wilson bounds.
- For undefined denominator, interval bounds are **null with ZERO_DENOMINATOR**, never zeroes. Small N (<30) generates a warning; imprecision should be interpreted accordingly.
- `macro_f1_bootstrap_95`: 1,000 class-stratified row-bootstrap samples with seed `20261101`, using a 2.5–97.5 percentile interval of supported-class macro F1. Require total N >= 30 and at least 5 observations in each *observed* true class. Otherwise return null and a reason. Stratification preserves observed class counts, but **is not a cluster bootstrap**.
- All intervals presume independent observations; their assumptions are documented in JSON. Study/patient correlation, incomplete patient identifiers, class/study confounding and cohort selection can invalidate population-level interpretations. Treat them as descriptive intervals, not evidence of clinical validation.

## Warnings

| Code | Trigger / meaning |
|---|---|
| `LIMITED_CLASS_SUPPORT` | One or more declared true classes absent; no full-universe macro estimate |
| `INDEPENDENCE_NOT_ESTABLISHED` | Manifest does not document independence; intervals have potential pseudoreplication |
| `STUDY_CLASS_CONFOUNDING` | Every recorded study contains only one observed true class (when >1 study); no causal isolation of study versus class |
| `SMALL_EVALUATION_SET` | Fewer than 30 evaluated records |
| `MACRO_F1_INTERVAL_UNAVAILABLE` | Insufficient total/class support for planned bootstrap |
| `NOT_LOCKED_INDEPENDENT_VALIDATION` | Exploratory/source-CV/historical roles cannot be called newly independent locked testing |
| `UNCALIBRATED_MODEL_CONFIDENCE` | Scores do not establish calibration or safety |
| `NO_PROBABILITIES` | Confidence, bins, coverage curves unavailable |
| `EMPTY_RETAINED_SET` | No examples survive the frozen cutoff |

Warnings inherited from Stage 05 input parsing and Stage 04 compatibility remain present. Stage 06 does not claim that a statistical association between cohort shift and errors is a causal mechanism (Stage 07).

## Reproducibility

- Fixed seeds: Stage 05 CV=42; Stage 06 bootstrap=20261101.
- The historical CPTAC case is converted from preserved labeled prediction rows and re-evaluated, not retrained. Its provenance and source hashes live in `examples/cancershift_historical_cptac/PROVENANCE.json`.
- Outputs include stable row ordering, explicit class ordering, JSON report, CSV tables and SHA-256 manifest. Stage 05 non-executable JSON model freeze is retained under `stage05/` for training runs.
- The binary model is a transparent regularized logistic regression, not a reimplementation of CancerShift's original five-class ensemble.
