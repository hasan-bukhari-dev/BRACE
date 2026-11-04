# Stage 07 — Delivery and scientific gate

## Implemented and tested

- [x] Cohort compatibility reuses strict Stage 04 checks.
- [x] Real computation of gene distribution changes from user-provided matrices (with explicitly synthetic examples).
- [x] Source-fitted PCA uses no target expression values to fit scalers or components.
- [x] Feature overlap, sample counts, declared assay/processing differences and warnings survive in results.
- [x] Labeled Mode B class-conditioned summary, strictly descriptive and separate from source-fit preprocessing.
- [x] Optional Stage 05/06 prediction import with sample/label matching; quartile-level error and confidence tables.
- [x] Mode C excludes class distributions and prediction/error metrics.
- [x] Historical CancerShift adaptation comparison preserved with input source SHA and distinct historical label.
- [x] Offline HTML, inspectable CSV/JSON, SHA-256 run manifest, CLI and Windows file-picker implementation.
- [x] All inherited Stage 04/05/06 tests remain in the archive.

## Outstanding external verification

- [ ] Stage 03 real GSE42568/GSE29431 expression matrices have not been acquired in this environment, so no new biological expression-shift finding is certified.
- [ ] Windows desktop GUI has not been exercised on an actual Windows host.
- [ ] Original historical CancerShift raw expression matrices and serialized models are still missing. GSE2109 adaptation metrics are archival, not recomputed; the CPTAC model errors cannot be directly linked to new gene-level shift values without sample-aligned expression features.
- [ ] Competition policy for reuse of original research and pre-existing UI is not independently verified.

## Scientific definitions

KS p-values and BH q-values are exploratory and rely on valid independence assumptions. The source PCA variance-based gene choice and projection use only source expression; target expression is merely transformed. Relative distance is not a calibrated individual reliability score. Target phenotype labels, when present in Mode B, are used only for post-hoc descriptive summaries. No causality or generalization beyond the evaluated samples is asserted. Data and declarations are provided by the user and not certified by BRACE.

## Release verification

Run `py -3 -m pytest tests -q` and `py -3 tools/verify_release.py` after extracting the ZIP. The verifier checks `FILE_SHA256_MANIFEST.csv` against extracted file contents. The ZIP itself can be independently checked using your archive application's CRC test.
