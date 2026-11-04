# Public ER association case study

**Question:** Do source-selected ER-associated expression features show same-direction association with recorded clinical ER status in a second breast-tumor study?

| Item | Source GSE42568 | Target GSE20711 |
|---|---|---|
|Included tumors|101:67 ER+,34 ER−|87:42 ER+,45 ER−|
|Exclusions|17normal,3missingER from121|2normal,1missingER from90|
|Platform|GPL570|GPL570|
|Deposited processing|log2 GC-RMA|RMA/log2 as recorded|
|Clinical ER assessment|EIA threshold per source annotation|IHC0/1 per target README|
|Prepared features|10,000 source-variable Entrez representatives|Same IDs/probes selected using source only|

Full acquisition, mapping, probe selection, original SHA-256, patient/code audit, publications and redistribution considerations: `examples/public_er_pair/README.md` and its ledgers. No new license or donor verification is asserted.

Source discovery uses two-sided Welch tests, BH over all 10,000 prepared features (including four constant-group untestable features with p=1 for correction), then q≤.05, descending absolute Hedges g, exact-ID ties, maximum20. Source signature is saved/hashed before target testing. Target BH family remains all 20 frozen hypotheses, retaining unavailable hypotheses in that family. Pointwise intervals are neither simultaneous nor selection-adjusted.

Result:1,339 source q-passing,20 selected/testable,19 matching directions,14 matching+target BH support,5 matching without sufficient support,1 opposite nonsignificant estimate,0 untestable. This is exploratory support under this design, not a biomarker-validation rate. Nonsignificance does not establish absence.

Saved approved public frozen hash: `8f17b0e452532a9f0add71d4ce96986315d84a609c709d73c3e35890e04f446f`. A new standard-Python 3.11.9 run records different software provenance and therefore a different frozen digest; numerical agreement is checked separately. Do not falsify version metadata to force an old digest.

Biological and technical limits: related ER definitions do not imply identical assay ascertainment; GC-RMA/RMA scales are not interchangeable; source donor IDs are unavailable; cross-study donor linkage cannot be authenticated; target subtype/relapse enrichment and age/grade/HER2/purity/study effects can confound unadjusted association. Normal tissue is excluded. No covariate/paired inference, batch correction, causal claim, direct-scale comparison or source-trained model-transfer approval.

Clarke et al., PMID23740839, DOI10.1093/carcin/bgt208; Dedeurwaerder et al., PMID21910250, DOI10.1002/emmm.201100801. Full source publisher methods were not available during original preparation; source GEO metadata and citations, plus the target open article/README, underpin the preserved review. The rejected GSE29431 tumor/normal design remains documented, not quietly repurposed.
