# Stage 09 — Scientific quality and risk review

## Scope of the release

This is an engineering validation and reproducibility packaging increment on Stage 08. It does not retrain CancerShift, obtain new GEO gene-expression matrices, change the fixed historical thresholds, or create a clinical model.

## Methodology and verification matrix

| Area | Implemented check | Scientific guardrail |
|---|---|---|
| Prediction input integrity | Stage 05/06 probability vectors, class/ID checks | Invalid labels and impossible probabilities are blocked |
| Source model | Stage 05 logistic regression + source-only CV | Preprocessing and feature filtering occur within source folds; target labels do not influence fitting |
| Frozen external evaluation | Stage 05 JSON freeze + Stage 06 independent scoring | Historical saved predictions are not new inference; use labels for evaluation only |
| Classification | Stage 06 confusion matrix and class metrics | Absent true classes and undefined denominators reported rather than silently imputed |
| Confidence and coverage | Stage 06 threshold curves and calibration bins | Only declared reference threshold considered frozen; other cutoffs exploratory |
| Intervals | Wilson 95% approximations, class-stratified row bootstrap | Independent-observation assumptions stated; no patient/study cluster correction |
| Dataset comparability | Stage 04 manifest and measurement metadata checks | Unsupported cross-platform / processing combinations not silently transformed |
| Expression shift | Stage 07 KS, FDR, median shifts and source-fitted PCA | Differences are observational, not evidence of a causal mechanism |
| Reliability associations | Stage 07 error-by-source-PCA-distance summaries | Error associations are descriptive, not calibrated predictors of individual failure |
| Reproducibility | Stage 09 hashes, engine versions, study declarations, saved numerical evidence | Local uploaded raw files excluded from export; independence declarations not authenticated |
| Historical consistency | Stage 06 real archived CPTAC 680 total, 668 correct, frozen 0.95 retained 584, 583 correct | Missing prostate reference class and study-class confounding disclosed |

## Dataset identity and provenance

- The **GSE42568/GSE29431** primary public expression demonstration remains unverified because official expression matrices could not be retrieved in this environment. Stage 03's downloader and metadata are separate. Thus Stage 09 cannot certify a live, real-GEO-expression demonstration.
- The **680 CPTAC-GDC prediction records** are original CancerShift *archived* research evidence. They do not substitute for accessible trained models or expression matrices.
- The **synthetic examples** are artificial input files used to test algorithms, interfaces and packaging only. Never interpret as disease discoveries.
- On third-party input, BRACE can verify local syntax, hashes and declared metadata. It cannot independently establish cohort sampling, patient identity, consent, independent acquisition, assay validity, or leakage outside its own model-training implementation.

## Error and adversarial cases

The inherited Stage 04–08 tests cover malformed CSV, missing fields, duplicate samples and features, invalid numbers, inconsistent labels, source/target incompatibility, label leakage assertions, class-support edge cases, empty confidence-retained sets, and invalid probability vectors. Stage 09 adds package integrity, no raw input inclusion, reproducible repeated exports, archived-evidence integrity, and shift-only output semantics.

## Unsupported claims

Neither a high held-out score nor a cohort shift chart establishes deployment reliability, biomedical causality, clinical accuracy, or a drug/biomarker discovery. The archived CPTAC results cannot be extrapolated to unobserved reference classes.

## Blockers retained as blockers

1. Real GEO expression acquisition and numerical validation are not done.
2. Windows/browser/projector clean-machine acceptance is not done.
3. No blinded independent usability experiment has been completed.
4. Reuse eligibility with competition organizers is unconfirmed.
5. Python dependencies are not fully bundled as Windows wheels; a prepared wheelhouse or preinstalled dependencies are needed for fully offline cold setup.

**Stage 09 verdict:** Engine scientific regression and export packaging are verifiable. Full clean Windows and public-expression demonstration gates are **pending**.
