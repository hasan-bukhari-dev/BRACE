# BRACE input examples — research data contracts

BRACE Stage 08 accepts processed bulk gene-expression CSV/TSV files and matching sample metadata and JSON manifests. **These bundled example measurements are synthetic and must not be reported as biological discoveries.**

## Mode A: evaluate a prediction table

Upload `predictions.csv` and `manifest.json` together (from `mode_a_prediction_example/`). Required columns are `sample_id`, `true_label`, `predicted_label` and, when probabilities are provided, all columns declared in the JSON class-to-probability map.

## Mode B: train on one cohort, evaluate another

Upload six files from `mode_b_or_c_cohort_example/`: source/target expression, source/target metadata, and their corresponding JSON manifests. The table is **features by samples**: column one `feature_id`; other columns are unique sample IDs. Sample metadata must match exactly. For the first baseline, source and target class labels are `normal` and `tumor`; source must have sufficient samples per class. Patient-aware cross validation is performed when patient IDs exist.

## Mode C: inspect unlabeled shift

Upload the same six files but select **Shift only**. BRACE does not consult outcome labels in this mode, even when a `condition` field exists.

### Important

- Expression matrices must already be appropriately processed; BRACE does not normalize or harmonize them automatically.
- Microarray source/target platforms and gene namespaces must match under the MVP rules.
- JSON manifest independence declarations are user assertions, not independent provenance verification.
- Arbitrary pickle, joblib, executable, or raw sequencing file uploads are unsupported.
- Maximum 25 MB per file in the Stage 08 local interface.
- If you need actual GEO example data, the Stage 03 downloader package must first fetch and verify the real matrices; they are not bundled here.
