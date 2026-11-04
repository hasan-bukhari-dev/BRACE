# Stage 06 — Delivery and acceptance gate

## Verification conducted in the project runtime

- 102 automated tests passed, comprising **77 inherited Stage 04/05 regression tests** and **25 new Stage 06 tests** (pytest parameterization expands several cases; total test cases = 102).
- Both historical real prediction and synthetic training/replay CLI paths completed. Mode A uses preserved CancerShift CPTAC records; Mode B training remains **synthetic only**, because Stage 03 expression matrices are not yet available in this environment.
- Repeated evaluation of the same evidence produced identical JSON/CSV/HTML files.
- Error cases include duplicate sample IDs, malformed probability arrays, argmax mismatch, unsupported class and absent class, empty retained set, missing probabilities, precision undefined, insufficient bootstrap support, and study/class confounding.
- Stage 05 leakage protections remain in regression suite: target labels leave the frozen source model/predictions unchanged; target expression changes cannot refit source model.

## Historical CPTAC-GDC numerical audit

| Metric | Value | Scope |
|---|---:|---|
| Sample rows | 680 | Archived scored predictions |
| Correct | 668 | 12 errors |
| Accuracy | 98.2353% | Observed historical reference |
| Wilson 95% accuracy interval | 96.94%–98.99% | Approximate, row independence unverified |
| True supported classes | 4 of 5 | Prostate absent |
| Supported-class macro F1 | 0.982665 | Four observed classes only |
| Reference cutoff | 0.95 | Source manuscript reference cutoff |
| Retained | 584 / 680 | 85.8824% coverage |
| Retained correct | 583 / 584 | 99.8288% selective accuracy; one retained error |
| Study/class confounding | Detected | Studies largely indicate true class |

The historical CPTAC study is **not** a new blind evaluation. Its high confidence errors illustrate why confidence should not be equated with clinical safety. Confidence curves other than the reference threshold are post hoc explorations of the same data.

## Completion verdict

**PASS (Stage 06 core scientific evaluation engine and inspectable reports).** The Stage 06 requirements are satisfied for existing labeled prediction evidence, with a synthetic baseline/replay integration demonstration. Native Windows GUI startup has **not** been independently exercised, Stage 03 public GEO expression matrices remain **pending**, and no prospective clinical or patient-level independent validation is claimed.

Next: Stage 07, shift-forensics linking compatible expression cohort differences to model error profiles, without implying causal attribution.
