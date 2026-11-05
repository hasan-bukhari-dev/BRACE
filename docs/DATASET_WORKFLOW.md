# Data and studies

Use [the new-data guide](NEW_DATA.md) for the ordinary workflow.

A dataset contains immutable measurements and metadata. A prepared version records processing, exclusions and identifier decisions. A study assigns dataset versions to source/target or prediction roles. An analysis run records one execution. Evidence belongs to that run.

The import manifest retains its original role field for file compatibility. That field no longer restricts reuse: a study binds the execution role in its own manifest without changing the original assets. Original and execution hashes can therefore differ for the manifest only; both identities and the assigned role remain in provenance.

Common GEO preparation uses reviewed fields and class tables. Technical preparation is automatic; scale, biology, exclusions and independence remain scientific declarations. Characteristic fields align by key across samples. Advanced JSON supports curated feature mappings or recipes; ordinary supported paths do not require handwriting it.

RACE/CE may use source-only variance preparation. Baseline training requires all features or an identifier-hash panel so expression-based selection stays in training folds. Targets align to the prepared source IDs. A panel or budget defines the tested feature universe; neither represents the whole transcriptome by default. No normalization, uncertain gene mapping or label guessing occurs silently.

To reuse data, select a saved study and choose Use as a new study. Change roles or task, review its assumptions, check eligibility and compute. A different biological class mapping is a new prepared version; a different experimental role alone is not.

Prediction import maps arbitrary CSV/TSV column names to the required sample, true-class and predicted-class fields. The class universe and optional complete score vector require review. No model is executed. Frozen BRACE baseline replay reuses an existing freeze without fitting on the new target; the original training dataset cannot be passed off as a transfer target.

Search covers all saved runs. Archiving hides a study but deletes no data. Private backups contain a consistent registry snapshot, immutable original assets and completed runs with hashes and restoration instructions. Restore into a separate empty workspace; preserve the current one until restored results open correctly.
