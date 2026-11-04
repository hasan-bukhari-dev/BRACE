# Start with the files you have

**Learn the workflow:** start BRACE and choose **Explore the public study**. This opens saved exploratory ER-association evidence from real GEO measurements; it does not launch a fresh test. Select a gene tile, inspect its measured values, then open Evidence for the report and downloads.

**Recompute the real example:** Use my data → Expression + sample labels → Load example files. Review the two group definitions and processing differences, confirm the review checkboxes, then Check inputs → Test selected associations. Back revisits the actual dataset descriptions. Checks do not authenticate donor independence.

**Use two expression studies:** provide four UTF-8 CSV/TSV files: source expression, source sample metadata, target expression and target sample metadata. Matrix rows are features; columns are samples; first header is feature_id. Metadata has sample_id and, for gene testing or training, condition. Within each study, sample IDs must match the matrix exactly. Feature IDs must be unique, declared in the same namespace, and meaningful across both studies. Do not rename unrelated probes to manufacture overlap.

In step 2, describe each dataset: its name, human bulk origin, normalized measurement, identifiers, microarray platform and processing. A saved description produces the existing BRACE declaration JSON without manual editing. You can choose existing JSON declarations instead. Step 3 defines the biological contrast. Review eligibility and limits before calculating. RACE currently supports unpaired normalized log2 microarrays. The source-only baseline requires normal/tumor labels. Distribution comparison supports the existing declared measurement types and does not use target labels.

**Use saved predictions:** provide a table with sample_id, true_label and predicted_label. Declare the exact model classes and how reference labels were obtained. Class-only tables are supported. Confidence filtering additionally requires a mapped probability column for every declared class, finite 0–1 values and a row sum of 1. Incomplete probability vectors are rejected. A maximum class score is not assumed calibrated confidence. BRACE does not execute your uploaded model.

**Other files:** an EMBRACE ZIP is a report output. Extract it and open research_summary.html; to recompute, use original inputs. FASTQ/CEL and raw counts need scientifically appropriate preprocessing elsewhere. Export an Excel sheet as UTF-8 CSV/TSV. An unlabeled target belongs in distribution comparison.

**Limits:** 25 MiB per API-uploaded file, 25,000 features, 500 samples per expression study; 50,000 prediction records. No limit was relaxed. Prepare a documented deterministic smaller input rather than silently truncating biology or selecting features with target outcomes.

Uploaded files are sent to the local BRACE server and remain on this computer. Generated analyses are saved locally; choose Open a saved analysis to find them. Reloading cannot restore browser file permissions, so new uploads require reselecting files. Evidence ZIPs omit raw uploaded input tables; keep original inputs and protect sensitive exported record IDs.
