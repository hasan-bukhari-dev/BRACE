# Persistent dataset workflow

Open Workbench and use **Study datasets**. Acquired originals, prepared versions, studies and analysis runs have different identities. Display names are human-readable; immutable IDs and SHA-256 hashes identify records and bytes.

## Reviewed public example

1. Open SPACE, search `GSE42568` and `GSE20711`, verify their official matrix filenames, and acquire the originals. Each acquisition is automatically registered. These originals are not yet analysis-ready.
2. Return to Workbench and choose **Add reviewed public ER datasets**. The app checks pinned original/prepared hashes, registers both cohorts, and records recipe/mapping hashes and original parents. The same workflow works offline from bundled originals. No new normalization occurs.
3. Review ER-positive/ER-negative definitions, source/target roles and processing caveats. Name the study, acknowledge review and choose **Check selected datasets**.
4. For RACE, compute after checks pass. The supported demonstration selects 20 associations and reports 14 with matching direction and target support. Inspect measurements in FACE, calculations in TRACE, and export EMBRACE from Evidence.
5. Choose ACE baseline for the same pair to see its blocker: ER labels do not satisfy the normal/tumor baseline contract. CE has its own structural/processing checks and descriptive interpretation.

Reviewed preparation reuses byte-pinned outputs of `examples/public_er_pair/prepare.py`. That recipe selects features from source variance without consulting target outcomes. Regression tests regenerate preparation and check pinned outputs. This is not general automatic GEO normalization.

## Other acquired GEO matrices

Choose **Inspect & prepare** on an acquired record. The bounded parser supports a UTF-8 numeric GEO Series Matrix with `ID_REF`, unique IDs, complete finite cells and a complete gzip stream. It consumes the stream to verify CRC. Generic acquisition is limited to 25 MiB. The reviewed GSE20711 original alone has an exact 26,895,121-byte exception, accepted only if its pinned SHA-256 also matches; no other limit is raised. Parsing limits are 128 MiB expanded input, 1 MiB per line, 500 samples and 100,000 original features. Prepared inputs remain limited to 25,000 features and 25 MiB per asset.

The editor exposes original annotations and a JSON template. Supply:

- A BRACE cohort manifest with the actual organism, namespace, supported measurement state, processing description, role and independence declaration.
- Every included sample in `condition_by_sample`; empty conditions are allowed only for declared unlabeled data. Every omitted sample needs a reason in `excluded_samples`.
- Where conversion/subsetting is needed, an explicit one-to-one `feature_mapping` and `mapping_reference` identifying the reviewed reference/version. Ambiguous many-to-one mappings are blocked. Unmapped features are listed in the saved report. No mapping preserves original IDs.

Retained numeric text is preserved. Missing/nonfinite values, unsupported declarations, unresolved samples, ambiguous mappings and resource violations block preparation/analysis with a reason. The original remains available. Supply documented processed expression, metadata and a manifest when the format is unsupported.

For different phenotype vocabularies, inspect a prepared record and create a reviewed phenotype/role version. Map every observed condition to the shared contrast and provide definitions. This creates a new ID, preserving the original, expression hash and parent link. Role changes also create a version; assigning the same cohort twice does not establish independence.

## Researcher-provided inputs and studies

Use **Import a prepared expression dataset**, or the existing guided upload setup. Successful analyses register exact inputs automatically. Saved classification predictions remain a separate ACE workflow and can describe nonbiological classes. Evaluated prediction tables become reusable registered prediction datasets.

Choose an existing study in the library to compute another run on its fixed dataset versions. Choose **New study** for a different question/pair. Each run retains its name, study ID, dataset IDs, timestamp, provenance snapshot and results. History lists the newest 50 by recorded creation time; legacy entries use the run configuration file timestamp and identify that fallback.

## Frozen baselines

After an eligible source-baseline run, expand **Apply a previously frozen BRACE baseline**. Select the original verified training run and a prepared target. The app accepts only a safe BRACE JSON freeze, aligns required features and reuses source parameters. It does not deserialize executable models.

Labeled targets receive existing evaluation calculations. Unlabeled targets receive prediction rows and predicted-class composition, with no accuracy, error-rate or AUROC claim. TRACE records the original freeze identity, target version, parameters and whether metrics were computable. Both paths export audited evidence.

## Storage and reproduction

The registry is `BRACE_RUNS_DIR/_workspace/registry.sqlite3`, alongside immutable per-dataset asset directories. SQLite transactions publish complete records; copies are staged before publication. Run inputs/results live in separate 32-character directories. Stop the app and back up the whole runs directory. Copying only the database is insufficient.

Assets are hash-checked before task handoff. Display-name edits do not mutate saved run provenance. Pair-specific preflight receipts at `/api/datasets/{id}/checks` retain exact task, IDs, contrast and decision.

EMBRACE contains `summary/`, `results/`, `methods/`, `provenance/` and `integrity/`. Existing paths remain compatibility aliases. Original uploads are excluded; derived identifiers, declared metadata, predictions and provenance remain. Reproduction needs matching input assets/manifests identified by export hashes. Review derived metadata before sharing.

Processed proteomics, metabolomics, methylation/epigenomics, single-cell inference and raw FASTQ/count preprocessing remain unimplemented.
