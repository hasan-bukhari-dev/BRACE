# Analyze new data

Open **Data & analysis**. Choose RACE (association testing), ACE (saved predictions or baseline training), or CE (measurement comparison).

## Public expression data

1. Choose **Discover datasets in SPACE**. Enter an accession, check files and acquire the original.
2. Choose **Prepare this dataset for analysis**. Review the organism, platform, identifiers and processing reported in the original.
3. For RACE or a baseline, choose the recorded phenotype field. Review group counts, map class names and give reasons for exclusions. CE can use unlabeled samples.
4. For a large source, choose a preparation policy and feature budget. RACE/CE can use source-only variance; baseline training uses an outcome-blind identifier panel. These computational subsets are not representative biological panels. Original numeric text is preserved.
5. Prepare the target using **Use prepared source features**. Different or missing IDs require a reviewed mapping, not guessed matches.
6. Prepared data are selected automatically. Review task checks and compute. Roles belong to the study; the same prepared dataset can serve either role in another study.

GEO characteristic fields are aligned by key across samples, even when the physical rows shift. Suggested values require review. BRACE does not normalize raw data, invent patient independence or equate different phenotype assays.

## Prediction data

Open **Import saved predictions · ACE**. Select your CSV/TSV, read its columns, and map sample ID, known class and predicted class. Review the full class universe, including classes absent from the cohort. Map every class-score column or leave all scores blank. Supply the model identity and reference-label source, then save and evaluate. No model file is executed.

## Gene measurements and function

In a RACE result, select any frozen feature to open FACE. Measurements and TRACE use that run's checked files. **Look up this gene at NCBI** sends only its identifier and namespace. Cached references work offline. Entrez, official human symbols, reviewed Ensembl cross-references and unambiguous probes in the pinned GPL570 mapping are supported. Ambiguous probes are identified explicitly; no function is guessed. Functions are reference biology, not explanations of statistical effects. Cached reference dates, source links and hashes travel with the next evidence export.

## Reuse and recovery

Use **Use as a new study** to change assignments without modifying a saved study. Swap source/target, compare saved results, or archive and restore a study. Saved preparation and study drafts restore local form values; file uploads may need reselection. A computation already accepted by the server continues if you close the browser. Review saved analyses before retrying.

Storage usage and **Create private backup** are secondary workspace controls. Backups contain original uploads; ordinary evidence ZIPs do not. Restore a private backup into a separate empty workspace, leaving the original workspace intact.
