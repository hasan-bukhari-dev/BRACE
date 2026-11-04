# PASS 02 REPORT — PASS (exploratory research scope)

Implemented the RACE backend and additive API on the approved Pass 1B checkpoint. No frontend redesign or Pass 3 work. The approved data were present, hashed, parsed and eligible for the explicitly exploratory ER contrast. Original CancerShift evidence and Stage 05–09 scientific engines remain unchanged.

## Files changed or added
- Added `brace_core/signature.py`: eligibility, source-only screen, immutable frozen signature, target testing, aggregate metrics and five scientific exports; standalone CLI.
- Changed `brace_app/server.py`: additive POST `/api/race`, RACE run reload, allowlisted exports and conventional evidence ZIP. Existing analyze modes retained; report generator and frontend unchanged.
- Added `tests/test_race.py` (29 tests), `scripts/run_public_race.py`, `docs/RACE_METHODS_AND_API.md`, `docs/PASS02_ENVIRONMENT.txt`, preserved baseline hash manifest `docs/PASS02_BASELINE_SHA256.csv`.
- Added `examples/public_er_pair/race_config.json` and `race_final/` real outputs, verification and probe/symbol annotations. All Pass 1B original matrices, prepared data, maps and exclusion ledgers retained.
- Corrected one assertion in `tests/test_stage05.py`: archived cross-OS probabilities compared at absolute tolerance 1e-15 (zero relative tolerance), while row count, fields, sample IDs and labels remain exact. The unchanged Pass 1B test reproduced the identical ~1e-17 textual discrepancy in this environment. No expected values, model coefficients or saved research evidence were changed.
- Refreshed `FILE_SHA256_MANIFEST.csv` and `CHECKPOINT_SHA256.json` for this release. Previous manifest retained for independent baseline comparison. This report is supplied both inside and beside the ZIP.

## Exact methods and equations
Positive = ER_positive; negative = ER_negative. Effects are within-cohort mean differences in deposited normalized log-intensity units, never asserted to be directly comparable log2 fold changes across studies.

For group sizes n,m and sample variances sa²,sb²: Δ=mean(a)−mean(b); SE²=sa²/n+sb²/m; t=Δ/SE; ν=SE⁴/[(sa²/n)²/(n−1)+(sb²/m)²/(m−1)]. Two-sided Student-t p; pointwise 95% Welch CI Δ±tν,.975 SE. Minimum two rows/group; either constant group is untestable. Hedges g=J(n+m−2) Δ/sp, pooled sp²=[(n−1)sa²+(m−1)sb²]/(n+m−2), exact J(d)=Γ(d/2)/[sqrt(d/2)Γ((d−1)/2)]. Standardized effects are descriptive under unequal variances; CIs are not simultaneous or selection-adjusted.

BH over all 10,000 source hypotheses; undefined tests enter correction as p=1 but remain null/untestable in output. Select q≤0.05, descending |g| then feature ID, cap 20. Snapshot includes source inputs/hashes, manifest, conditions, full screening family, selected signs, selection rule and software versions. Source discovery accepts no target argument. Source snapshot is persisted before target statistics are computed. Target features and labels do not choose source genes. Entire frozen set is the target BH family, including unavailable tests as p=1; no outcome-based reduction. BH relies on independent or suitable positively dependent tests, not arbitrary dependence. No combined replication score.

Unsupported assays/designs, repeated known donors, sample/patient overlap, conflicting condition definitions, perfect study/class confounding and ambiguous mappings block. Unknown independence remains a warning and exploratory only, even if a user declares documented independence. Different processing needs explicit acknowledgement. Raw counts, paired/covariate inference and locked claims are rejected. Neither missing significance nor an opposite-sign estimate without support establishes biological absence/reversal. Exact classifications, counts and reasons are exported.

## Actual biological run
GSE42568 source: 101 tumors, 67 ER+, 34 ER−. GSE20711 target: 87 tumors, 42 ER+, 45 ER−. Shared input universe: 10,000 Entrez features selected in Pass 1B using source-only variance and representative-probe rules; source/target coverage 10,000/10,000 each. Original data and preparation hashes are carried forward and checked by the public runner. No cohort changed after inspecting findings.

- 10,000 source hypotheses screened; 4 conservatively untestable for constant within-group expression (retained in correction family).
- 1,339 source genes met q≤0.05; 20 frozen under the declared ranking rule.
- 20/20 target-testable; 19/20 matching effect directions (95%).
- 14 matching-direction genes had target BH q≤0.05.
- 5 matching-direction genes lacked sufficient target statistical support.
- 1 opposite-direction estimate, without target FDR support.
- 6/20 overall lacked target statistical support; none unavailable or indeterminate.

All 20 selected features (rank, Entrez ID, platform symbol):

1. 135112 — NCOA7
2. 7091 — TLE4
3. 29968 — PSAT1
4. 56935 — SMCO4
5. 10477 — UBE2E3
6. 140885 — SIRPA
7. 5336 — PLCG2
8. 5621 — PRNP
9. 84441 — MAML2
10. 55816 — DOK5
11. 5997 — RGS2
12. 4067 — LYN
13. 10402 — ST3GAL6
14. 54947 — LPCAT2
15. 157506 — RDH10
16. 51191 — HERC5
17. 834 — CASP1
18. 29015 — SLC43A3
19. 5918 — RARRES1
20. 8424 — BBOX1

Full effects, statistics, intervals, q-values and classifications are in `race_final/replication_genes.csv` and `race_result.json`; full source screen is supplied, not only successful genes. Symbols come from the pinned historic platform mapping; exact selected probes are recorded, and current nomenclature is not independently certified.

Frozen hypothesis SHA-256: `8f17b0e452532a9f0add71d4ce96986315d84a609c709d73c3e35890e04f446f`.

Measured engine-plus-export runtime: **2.947421 seconds**, excluding intake, initial imports and independent reference checking, in this Windows Python 3.11.2 environment. No peak-memory, browser latency, startup, clean-device or human-test measurements claimed.

## Verification, commands and exact outcomes
- Existing requirements installed in workspace `work/venv`; Espressif installation untouched. Actual versions saved in `docs/PASS02_ENVIRONMENT.txt` (NumPy 2.4.6, SciPy 1.17.1, scikit-learn 1.9.1, pytest 9.2.0).
- Initial focused `python -m pytest tests/test_race.py -q -k 'not api'`: 27 passed, 1 deselected in 1.64s before the additional partial-family test.
- Restricted API attempts stalled in Windows asyncio socketpair creation; diagnostic stack identified the execution-environment boundary. Processes were interrupted. Running the local API checks with access enabled resolved it. First API fixture then correctly failed because legacy fictional GENE IDs declared Entrez. The API-test copy now declares its fictional identifiers as gene symbols; original fixture and parser unchanged. Corrected API check: 1 passed, 27 deselected in 2.55s.
- `python scripts/run_public_race.py --out examples/public_er_pair/race_final`: exit 0; two runs produced byte-identical five scientific files. Independent vectorized `scipy.stats.ttest_ind(equal_var=False)`, `false_discovery_control`, scalar gamma correction and separately reconstructed selection agree. Maximum absolute discrepancy across checked statistics/effects/q-values: 6.573e-14; tolerances rtol=1e-10, atol=1e-12. Four constant genes explicitly reconciled, not hidden. SciPy reference emitted a precision-loss warning on constant rows, which are excluded from inference by the documented rule. Initial reference attempt failed on undefined source values; reference masking/correction-family handling was corrected before the final verification.
- First full `python -m pytest -q`: **183 passed, 1 failed**, 50.32s; failure was the archived text-equality probability comparison.
- Unchanged approved Pass 1B targeted replay test: **1 failed**, 2.11s with the identical discrepancy, confirming a pre-existing portability issue.
- After the narrow assertion correction and extra partial-family/file-limit checks, full `python -m pytest -q`: **185 passed, 1 warning in 40.91s**. This comprises original 151 tests, five Pass 1B tests and 29 RACE tests; no test removed or skipped.
- `python scripts/release_smoke.py`: exit 0; historical 680/668, synthetic full computation PASS, reproducibility ZIP PASS.
- Release hash manifest: 169/169 files checked. Checkpoint ZIP CRC and all artifact SHA-256 hashes verified after packaging.

The one suite warning is Starlette's httpx TestClient deprecation. No new package was added to avoid that warning. Existing supported requirements were used.

## Scientific limitations and unresolved issues
This is exploratory independent-study replication, not patient-authenticated locked external validation. Source EIA and target IHC ER thresholds differ. GC-RMA and RMA differ. Different acquisitions support exploratory independence, but missing source donor identifiers prevent full linkage verification. No direct scale comparison, model-transfer readiness, causal mechanism or clinical biomarker claim is supported. Target subtype/relapse enrichment and age/grade/HER2/purity/batch confounding remain. Public runner verifies declared/pinned files, not original acquisition or consent. Historical annotation and source-only variable-gene selection limit the inference universe. Source full publisher methods and study-specific redistribution licensing remain as documented in Pass 1B. No formal statistical adjustment for covariates or gene-selection uncertainty is implemented. See `RACE_METHODS_AND_API.md` and Pass 1B README.

## Ready for subsequent frontend work
The additive upload endpoint, JSON result schema, full source and target tables, immutable source evidence, pointwise intervals, scientific warnings, exact denominators, run reload and safe evidence exports are executable and tested. Public results and annotated IDs are supplied. No navigation, chart or frontend has been redesigned; visual/browser acceptance remains unverified. Legacy health/UI example messaging is unchanged in this backend pass. No subsequent pass begins without review and approval.

## Three skeptical judge objections
1. **“Are these truly independent, clinically equivalent cohorts?”** Separate study acquisition and distinct samples support exploratory use; donor linkage and ER assay equivalence are not fully authenticated. The engine prohibits a locked claim and exposes those limits.
2. **“Did you choose genes or cohorts to make the target succeed?”** Dataset choice and source-only feature preparation predate this run. Discovery has no target argument, source signature is hashed/saved first, target-label attacks leave it unchanged, and all 20 outcomes including nonsupport are retained.
3. **“Does 14/20 mean validated biomarkers?”** No. It is matching-direction statistical support under this exploratory two-cohort contrast and declared testing family. Selection, dependence, sampling and technical confounding remain; there is no clinical validation or causal experiment.

**Decision: PASS within the approved exploratory scope, ready for independent review. Stop after Pass 2.**
