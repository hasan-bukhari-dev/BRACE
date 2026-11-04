# Stage 05 acceptance gate

| Requirement | Outcome |
|---|---|
| Import real existing prediction tables | PASS — original CancerShift v08 CPTAC scoring rows converted and reevaluated |
| Support CSV/TSV prediction files | PASS |
| Reject duplicate IDs, invalid labels and malformed probabilities | PASS — automated adversarial tests |
| Complete class-probability mapping, unique argmax consistency | PASS |
| Source-only logistic baseline with no external model executables | PASS — synthetic matrices |
| Source CV with pipeline contained in training folds | PASS — stratified and patient-group CV tests |
| Frozen parameters and deterministic replay | PASS — synthetic target and JSON snapshot |
| Target labels independent of model fit and target prediction | PASS — permutation test |
| Target expression not used for source fit | PASS — perturbation test |
| Repeated runs with same input and seed reproduce files | PASS — exact bytes on synthetic output |
| Full historical CancerShift inference | NOT AVAILABLE — original model/checkpoint/data missing |
| Training with verified real public GEO expression datasets | PENDING Stage 03 data acquisition |
| Native Windows GUI acceptance | PENDING; GUI implemented, Linux/headless tests only |

**Verdict:** Stage 05 implementation satisfies the deterministic, leak-resistant synthetic baseline and real historical prediction-import gates. Not a claim that Stage 03 (real expression acquisition), Stage 06 (expanded reliability statistics), or Stage 08 (complete application) are complete.
