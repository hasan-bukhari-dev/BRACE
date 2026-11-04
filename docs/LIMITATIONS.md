# Scientific and operating limits

- BRACE is exploratory research software, not clinical validation or causal inference.
- RACE supports declared normalized log2 human microarrays and unpaired two-condition contrasts. It does not align FASTQ, preprocess CEL files, normalize arbitrary RNA-seq counts or adjust for all confounders.
- Source selection can inflate source effect estimates. Matching direction and target statistical support are separate; insufficient support does not prove no effect, and an opposite estimate does not prove biological reversal.
- The public ER pair has GC-RMA/RMA processing, ER-assay and incompletely authenticated donor-independence limitations. Direct pooled expression scales and model transfer are not approved by its exploratory association result.
- Imported predictions are scored, not executed or retrained. Confidence filtering needs valid complete class probabilities; those probabilities are not assumed calibrated. Missing classes remain unevaluated.
- The supported expression baseline is a specific source-fitted logistic-regression pipeline, not the historical CancerShift ensemble or arbitrary model execution.
- Distribution differences and source-fitted PCA do not establish target accuracy or why a model fails.
- SPACE returns candidates and bounded original downloads. Labels, preparation, reuse terms and scientific independence require review.
- API limits remain 25 MiB per file, 25,000 features, 500 expression samples per cohort and 50,000 prediction records.
- Hashes identify bytes, not patient independence or authenticated acquisition. Raw uploads are omitted from EMBRACE; exact originals are needed to recompute.
- Only Windows native downloads have been released. Source tests passed on Windows, macOS and Linux. Signing, notarization and universal hardware compatibility are not claimed.
- Human comprehension, real screen-reader and physical-device acceptance remain pending. See [the acceptance checklist](ACCEPTANCE.md).
