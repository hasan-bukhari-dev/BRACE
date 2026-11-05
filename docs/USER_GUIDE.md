# BRACE research workspace

BRACE tests cross-cohort associations, evaluates predictions and compares measured datasets. It runs locally. It does not establish biological mechanism or clinical validity.

## Start a study

Open **Data & analysis**, choose the scientific task, and name the study. Find public expression data in SPACE, import processed expression files, or map a prediction table for ACE. Review the data, check eligibility and compute. See [new-data instructions](NEW_DATA.md).

Prepared versions can serve either role. **Use as a new study** preserves earlier assignments; **Swap source and target** changes the new experiment. Saved runs and exact input identities remain attached to their studies. Archived studies keep their files and can be restored.

## Understand a result

- **RACE:** source-only association selection is frozen before target testing. Inspect the actual screened universe, FDR rule, selected cap and target denominator. Support means matching direction plus target BH q ≤ 0.05 under the recorded exploratory protocol, not causal or clinical confirmation. Probe features are not necessarily distinct genes.
- **ACE:** evaluates saved predictions, or trains the supported normal/tumor baseline. It never executes an uploaded model. Confidence filtering changes coverage, not the original predictions, and scores need not be calibrated.
- **CE:** describes measurement differences and source-fitted PCA. Separation is not proof of model failure. Inferential tests are withheld when processing or dependence invalidates them.
- **FACE:** opens the selected feature's actual within-cohort measurements. Axes remain separate. Gene functions come from cited reference records; ambiguous IDs stay unresolved.
- **TRACE:** records inputs, calculations and frozen choices. It does not explain biological mechanism.
- **Evidence:** exports readable results, exact tables, hashes and input requirements. Ordinary evidence ZIPs omit original uploads; private workspace backups include them.

## Try the three demonstrations

Open **Open a real-data demonstration** in the Workbench. The ER association pair, archived CancerShift predictions and public CE comparison each illustrate one task. FACE and TRACE inspect the RACE run. These capabilities also accept other supported inputs; demonstrations do not certify eligibility for an arbitrary dataset. Artificial software checks remain separate.

The ER example uses 101 source and 87 target tumors, not the full deposited study populations. CancerShift evaluates archived predictions; its original ensemble is not rerun. See the [judges' walkthrough](JUDGES_DEMO.md) for denominators and limits.

## Continue later

Saved data and completed runs persist locally. Draft fields restore in the local browser; uploads may need reselection. Use Back to return, search saved analyses, or compare recorded runs. Closing a browser does not cancel a running calculation; check history before retrying. Storage usage and private backups are secondary controls. Keep backups private unless their contents have been reviewed.
