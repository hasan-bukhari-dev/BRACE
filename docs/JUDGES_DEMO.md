# BRACE: a three-minute demonstration

BRACE tests whether a molecular finding or a model prediction remains supported, then exposes the measurements and the calculation record.

## 1. RACE: does an association carry across studies?

Open the ER association example. GSE42568 supplies 101 labeled tumors; GSE20711 supplies 87. The source-only prepared universe contains 10,000 genes. Source Welch tests and BH correction leave 1,339 eligible genes; the declared historical cap freezes 20 before target testing. Fourteen have matching direction and target BH support. Five match direction without support; one has an opposite estimate without evidence of a proven reversal.

Click a frozen gene. FACE shows the actual measurements and separate cohort axes. TRACE follows source screening, the frozen hypothesis and target tests. The data are processed microarrays, not raw reads; donor independence and processing differences limit the inference. This is association replication, not prediction accuracy or a clinically validated biomarker.

## 2. ACE: what does headline accuracy conceal?

Open CancerShift prediction reliability. BRACE evaluates 680 archived CPTAC predictions; it does not rerun the original ensemble. There are 668 correct predictions. At score cutoff 0.95, 584 remain and 583 are correct; 96 are excluded. Inspect the highest-score error: breast was predicted as ovary at approximately 0.99869. Prostate has zero true examples, so prostate recall is undefined. Confidence filtering neither proves calibration nor repairs the error.

## 3. CE: how do measurements differ?

Open the real cohort comparison. It uses the same pinned public ER studies. Scaling and PCA fit only the source. Inspect the source-fitted projection and feature distributions. Processing differs, so inferential p/q values are withheld; KS D and median differences remain descriptive. The plot does not identify a cause of model failure.

## Finish with evidence

Open Evidence to download the readable report and exact files. Dataset versions, exclusions, parameters, hashes, denominators, undefined metrics and limitations accompany the results. The main demos are bundled for offline use; SPACE can discover additional public studies when online. An accession alone does not establish eligibility.

Baseline training and frozen application are supported separately. Their controlled artificial software check is under Developer software check, outside the three real-data demonstrations. It tests implementation, not biological generalization. User datasets must meet the declared normal/tumor and compatibility rules; ER labels are correctly rejected for that baseline.

Use the top Back control to return to the previous view. Previous step moves within setup. ACE setup remains in ACE; RACE setup remains in RACE. Demonstrate the evidence, the concrete error and the limitations directly.
