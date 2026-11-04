# BRACE V6 — start with your question

BRACE means **Biological Reliability Assessment across Cohorts and Experiments**. It is a local research workbench. It does not discover a disease mechanism or establish clinical validity.

## Try the real public example

1. Start `START_BRACE_WINDOWS.bat`; use the address printed in its window.
2. **Open saved public result** reads the included exploratory GSE42568 → GSE20711 evidence. It does not run a new experiment.
3. Select a gene in the signature or table. **FACE · Gene measurements** shows the included measurements by condition in each study. The cohorts have separate expression axes.
4. **TRACE · Trace result** explains the source test, frozen selection and target test. **Return to gene measurements** restores the same gene. Browser Back/Forward and the workbench Back control preserve context.
5. **E · Evidence** opens the readable report, calculation record and exact downloads. HTML links work beside the files in the extracted EMBRACE ZIP. Download the ZIP when sharing the complete record.

To compute again, use **Run the public example again**. Review the loaded files, ER definitions and processing differences; confirm the scientific declarations, check inputs, then compute. The origin remains verified public data, while execution is recorded as fresh. Download the complete input bundle if you want to inspect or reproduce the files independently.

The example tests ER-positive minus ER-negative tumors: source 101 tumors (67/34), target 87 (42/45), 10,000 source-filtered features. The verified preparation starts from 121 and 90 matrix samples respectively; excluded sample IDs and reasons are available from each cohort's inclusion summary. Original study totals are not analysis denominators.

## Choose the route that matches your files

| What you have | Choose | What happens |
|---|---|---|
| Two processed expression matrices and sample annotations, with equivalent supported conditions | Test gene-expression associations / RACE | Source-only selection, frozen gene list, independent-study target association testing |
| Saved predictions and known reference labels | Evaluate saved predictions / ACE | Scores your supplied predictions; does not execute or retrain your model |
| Supported normal/tumor expression cohorts | Train and evaluate a baseline / ACE | Fits the specific source-only logistic-regression pipeline; separates source CV from target evaluation |
| Compatible expression cohorts, possibly without target labels | Compare distributions / CE | Descriptive feature differences and source-fitted PCA; no target prediction accuracy |
| Only a public research question | SPACE · Find public datasets | Searches official GEO metadata, checks actual matrix filenames and can acquire bounded original gzip files; preparation remains a separate scientific task |

Expression intake needs one genes-by-samples CSV/TSV matrix and one sample metadata table per cohort, plus dataset declarations. Guided forms can create declarations; existing JSON can also be loaded. Prediction intake needs `sample_id`, `true_label`, `predicted_label` and the model's declared class list. Probability columns are optional, but if present must be complete and valid. **? · Help** contains small format examples. See the preserved [data guide](../v5/DATA_GUIDE.md) for exact schemas.

The API limits remain 25 MiB per input, 25,000 features, 500 samples per cohort and 50,000 prediction records. BRACE expects appropriately processed expression data. It is not a FASTQ/CEL preprocessing or general RNA-seq differential-expression tool.

## Read results without overclaiming

- **Matching direction + target support** requires both the same estimated sign and the configured target BH threshold. The public example has 14/20 such associations.
- Five matching estimates lack target statistical support; that is inconclusive, not proof of no effect. The opposite estimate is not a demonstrated biological reversal.
- Source effects are selected and may be inflated. Differences in GC-RMA/RMA processing, ER assays and unauthenticated donor independence limit the public experiment. Do not pool absolute expression scales or call it locked clinical validation/model-transfer evidence.
- Prediction accuracy always needs its denominator. Confidence filtering changes retained records and coverage; it does not retrain a model or establish calibrated probabilities. Unsupported classes remain unevaluated.
- Historical CancerShift predictions are archived evidence. The synthetic baseline is artificial software demonstration data. Neither is a fresh execution of the historical classifier.

## Recovery and privacy

Return to dataset descriptions to correct declarations; unaffected selected files remain in the current page session. Editing invalidates earlier checks. After a full reload, browsers cannot silently restore local file permissions: reselect original uploads when needed. Saved results remain reopenable from Evidence.

If you leave a view during computation, BRACE keeps the current view and offers the newly completed result. The method diagram explains the algorithm; it is not a live step-by-step progress monitor. A request's busy state lasts until a real response/error; there is no invented percentage or cancel promise.

Local computation and bundled examples do not need external network access after dependencies are installed. SPACE sends only the public search fields you explicitly submit to NCBI; matrices, private labels and uploaded records are not included. Its cache is local. A network failure does not disable the bundled example.
