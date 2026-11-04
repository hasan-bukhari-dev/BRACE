# BRACE 1.0 — frozen scientific scope

This release packages the existing methods; it does not add statistical capabilities. Method-version fields retain their original identifiers even though the application release is1.0.0. Original research and newly computed evidence remain distinct.

|Capability|Implemented boundary|Authoritative protocol|
|---|---|---|
|Intake/compatibility|Unique finite aligned expression/features/samples, explicit assay/processing/phenotypes, overlap/independence/design restrictions;25MiB API/25000 features/500 samples limits|[Intake/compatibility source](../brace_core/intake.py), [API](LOCAL_API.md), preserved intake/compatibility tests|
|RACE|Exploratory unpaired processed microarray Welch/Hedges; source BH across full prepared family; source-only fixed selection; frozen-family target BH; exact untestable reasons|`RACE_METHODS_AND_API.md`, `examples/public_er_pair/README.md`, `race_config.json`|
|FACE|Saved-result linkage to exact included expression cells; separate cohort axes, actual exclusions/missingness and saved pointwise statistics|[Molecular evidence contract and tests](../tests/test_molecular_api.py)|
|Mode A/ACE|Supplied labeled predictions; observed-class supports/confusion/metrics, optional confidence; no original-model inference implied|[Prediction/evaluation contract and tests](../tests/test_evidence_api.py), Stage 05/06 tests|
|Mode B|Binary source-only logistic baseline with source-only fitting/folds and saved freeze; separate source OOF/target scoring|Preserved `baseline05.py` and Stage 05 tests; source CVseed42|
|Uncertainty/confidence|Wilson proportions, documented1000 class-stratified row-bootstrap macroF1, seed 20261101; threshold 0.01 grid plus exact declared cutoff, equality retained|`metrics06.py`, Stage 06 tests; no clinical calibration or clustering correction|
|Mode C/shift|KS/BH/median/sourceIQR; up to250 positive-variance source features; source-fit scale/PCA, target projection; descriptive distance|`shift07.py`, Stage 07 tests; no supervised outcomes without labels|
|TRACE/EMBRACE|Methods, origin/evaluation roles and integrity linkage; standard published-byte inventories and reversible safeCSV|[Evidence audit](../brace_app/evidence_audit.py), [export tests](../tests/test_embrace.py)|

The public ERpair supports within-cohort associations and exploratory source-frozen target association testing. Direct absolute-scale comparison, pooling and source-trained model transfer are not approved. Separate study acquisition does not prove donor independence. Known repeated donors/overlap, phenotype/assay incompatibility or unsupported designs must block/restrict rather than generate a misleading result.

Numerical references and leakage/adversarial tests are in the supplied full suite. Saved public artifacts retain their original Python 3.11.2 provenance; fresh standard-Python 3.11.9 acceptance runs preserve numerical results but legitimately change the software-bearing frozen digest. Full exports keep every selected hypothesis, not only positive findings. Correlated genes, selection and study/patient dependence constrain uncertainty and biological interpretation.

## Persistent integration

The integration branch preserves existing scientific engine bytes. A persistent registry and explicit preparation services connect SPACE to existing ACE/CE/RACE calculations. Frozen-model replay now has a distinct application workflow; unlabeled targets produce predictions without accuracy. [Workflow](DATASET_WORKFLOW.md) · [Architecture](ARCHITECTURE.md) · [Recorded numerical comparison](quality/INTEGRATION_REGRESSION.json).
