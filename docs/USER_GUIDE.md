# BRACE — Design 3 user guide

Test gene-expression associations across studies, or evaluate saved classification predictions against known labels. Supplied manifests do not authenticate acquisition or independence. Follow README_START_HERE.md for standard 64-bit Python setup, release checks and START_BRACE_WINDOWS.bat. The installed app/data require no account, API key or outside network.

The five letters are navigation buttons: B home, R gene associations, A classification predictions, C dataset checks/distributions, E methods/history/exports. Plain task captions accompany each letter. Hover/focus previews; click/tap/Enter/Space commits. Escape cancels preview or closes an inspector. Home and theme changes retain the current analysis. System, Light and Dark are available.

## Real public example

Choose **Open a public gene-expression example**. This opens saved exploratory GSE42568→GSE20711 ER-status results, not a fresh calculation: 101/87 tumors and 10,000 prepared features. All 20 source-frozen associations remain: 14 matching with target BH support, five matching without the target threshold, one opposite estimate. Nonsupport does not establish absence; an opposite estimate does not establish reversal.

Select 135112/NCOA7 for 188 actual measurements in FACE. Source/target axes stay separate because GC-RMA/RMA absolute scales are not approved for comparison. 55816/DOK5 illustrates insufficient support; 54947/LPCAT2 an opposite estimate. Exact values, effects, q-values, pointwise intervals, mapping and exclusions are available. **Trace result** opens this exact selection's recorded methods; returning restores it. ER ascertainment, confounding and unknown donor independence remain limitations.

## Fresh expression analysis

1. **Use my data** (or **Use another dataset**) → **Test gene-expression associations**.
2. Select six files in examples/public_er_pair/prepared: source/target expression TSV, metadata TSV and manifest JSON. Assay/identifier declaration is required inside each dataset disclosure.
3. Positive label ER_positive, definition Clinically ER-positive primary breast tumor; negative ER_negative, definition Clinically ER-negative primary breast tumor.
4. Review provenance, equivalence and exploratory processing before checking their acknowledgements. **Check files for this task**, inspect counts/warnings, then **Test selected associations**.
5. Uploaded files are labeled user-supplied computation even when they match bundled public inputs; verified annotation is hash-linked. This ER pair is blocked for the normal/tumor baseline.

Changing task retains selected files within the tab, invalidates prior checking and requires a new task-specific check. Limits remain 25 MiB/file, 25,000 expression features and 500 samples/dataset. IDs must align. Resolve an input blocker and check again; no silent normalization or exclusion is added.

## Predictions and distributions

**Saved classification predictions:** choose that task, then a CSV/TSV table and JSON class/column manifest. The internal sample_id is a record key, not necessarily a biological sample. No expression or organism files are required. Maximum 50,000 records. Complete valid probability vectors are optional but required for confidence analysis. Two artificial non-biological fixtures under examples/design3_prediction_fixtures exercise format/computation; they are not real field studies.

ACE shows correct/all evaluated, true-row/predicted-column confusion, supported-class metrics and uncertainty. Confidence is maximum supplied class probability. Retention uses >= cutoff. Slider/numeric input choose saved 0.01 curve points plus the exact reference. Other cutoffs show an error without changing results. Zero retained means undefined selective accuracy/risk. Post-outcome cutoff choices are exploratory, do not retrain and do not establish calibration. Select a record for actual scores and TRACE; unrelated gene measurements are absent.

**Source baseline:** choose **Train a baseline on source expression data**, with six eligible files and normal/tumor labels. Source OOF and target scoring appear separately. The synthetic expression example verifies software without biological claims.

**Unlabeled comparison:** choose **Compare dataset measurements**. C/CE shows KS/BH, medians/source IQR and source-fitted PCA with exact tables. Labels are excluded; no accuracy or causal error explanation is produced. Existing expression/biological identifier contracts remain; arbitrary numeric tables are not silently accepted. Same-run diagnostics are available only when actually computed.

**Historical predictions:** B → **Historical research and software examples** → **Open historical predictions**. CPTAC: 668/680 correct; at .95, 583/584 retained correct; at .99, 431/432, still one error. Search cfc121b5 to inspect the actual breast→ovary error with maximum score 0.998692106. Original weights are unavailable; no new original-classifier inference is claimed. GSE2109 is a separately labeled recorded method table.

## Evidence and recovery

E → **Export evidence ZIP**. Extract and open research_summary.html for the result-first report, limits, full tables, methods, local links and hashes. Derived identifiers/scores can be sensitive. Original uploads are excluded: reproduction needs matching hashed originals and software. Hashes do not authenticate acquisition, consent or redistribution rights. Spreadsheet-safe CSV has a reversible encoding ledger; JSON retains exact IDs.

**Saved local analyses** lists up to 50 actual generated folders, with integrity checked when opened. Small per-run filters/selections restore after refresh; File objects do not. Reselect and check before another upload. Interrupted requests are never automatically rerun; check saved analyses because their outcome may be uncertain. If integrity fails, restore matching originals/results; do not edit hashes to bypass rejection.

Actual screen-reader use, unfamiliar-user comprehension, physical touch/projector and narrated demo acceptance remain untested. Current verification is in PRODUCT_DESIGN_V3_REPORT.md; earlier pass documents are historical snapshots.
