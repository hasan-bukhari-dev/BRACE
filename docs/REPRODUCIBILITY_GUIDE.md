# Reproducibility and evidence contracts

## What a completed new run produces

From Study, conduct a live Mode A, B or C run. Evidence offers:

- `research_summary.html`: human-readable summary of calculated results, warning codes and declared source hashes.
- `reproducibility_manifest.json`: release/version information, exact input SHA-256 hashes, allowlisted study metadata, analysis parameters, observed class universe, method versions, every exported artifact SHA-256, and science caveats.
- `validation/`: per-sample predictions, class metrics, reference threshold curve, confidence bins, error table, HTML/JSON source results where available.
- `shift/`: PCA coordinates, gene shift statistics and errors-by-shift summaries where calculated.
- `validation/stage05/`: source out-of-fold predictions, frozen JSON parameters, new target predictions, and original Stage 05 execution result when Mode B applies.

Download a single `RESEARCH_PACKAGE.zip` from Evidence. The zip stores **only computed scientific outputs**; it does not contain the uploaded raw input files, user-provided patient metadata, or full uploaded manifests. If the user keeps source files with the exported hashes, the identity of those inputs can later be checked.

## Reproducing Mode B from identical inputs

1. Use exactly the original six source/target cohort files. Confirm their SHA-256 hashes against `reproducibility_manifest.json`.
2. Use the same BRACE release, same dependency versions, recorded random seed, model config, feature namespace and measurement/processing descriptions.
3. Run a fresh Mode B analysis. Compare exported `frozen_model.json` and predictions to the prior result. Deterministic predictions are tested for matching versions and supported data conditions; numerical equality across arbitrary hardware/software builds is not guaranteed.
4. Compare test metrics and warnings. Changing target labels cannot be part of model selection under a frozen evaluation. Post-hoc adjustment invalidates the original independent role.

The source-trained baseline serializes JSON parameters, not a code-executing pickle or joblib object. The original CancerShift model checkpoints were not present in the supplied research archive.

## Historical data disclosure

The real CPTAC archived example has its own `BRACE_CPTAC_ARCHIVED_EVIDENCE.zip` and `HISTORICAL_EVIDENCE_PROVENANCE.json`. It is a reproducible *re-scoring* of saved predictions, not reproduction of the original inference or expression processing. A previously exploratory GSE2109 correction study is provided as historical context, never as a new blind experiment.

## Human interpretation rules

- Mode C has no evaluation accuracy; report shift only.
- Missing true classes lead to restricted observed-class summaries.
- A source-fitted PCA distance measures a position in feature space, not the cause of an error.
- Confidence threshold adjustment after reviewing errors is exploratory. A high confidence number is not calibrated clinical certainty.
- User-declared independence is not proof of independent patients or institutions.
