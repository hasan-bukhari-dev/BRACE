# Pass 4: RACE → FACE → selected-gene trace

## Reproduce the public-data walkthrough

1. Extract the checkpoint, install the existing `requirements.txt`, and start `launch.py` (or the supplied Windows launcher). Open the loopback address shown by the launcher.
2. Choose **Explore a public example**, then the study's results action. The saved Pass 2 computation opens under **RACE · Genes**. This action reads saved evidence; it does not launch another analysis.
3. Read **Which genes hold up in another cohort?** Source is GSE42568_ER, target GSE20711_ER. The contrast is clinically ER-positive minus clinically ER-negative primary breast tumor.
4. All 20 selected genes are initially shown. Search `NCOA7` or exact Entrez ID `135112`, then activate its feature-ID button. FACE opens beside the table (above it on narrow layouts). Scroll within the desktop inspector to the target panel.
5. Inspect source 101 samples (34 negative, 67 positive) and target 87 (45 negative, 42 positive), separate dot plots, saved estimates and support. Expand measured values for sample IDs and exact original values. Source and target axes are deliberately independent.
6. Choose **Trace result**. The gene ID, study/run `public_er_pass2`, frozen hypothesis hash, source-only selection, input hashes and executed methods stay linked. **Return to gene measurements** restores FACE.
7. Search `DOK5` / `55816` to inspect matching direction without sufficient target support. Search `LPCAT2` / `54947` for the opposite-direction estimate; this estimate is not a statistically supported reversal. Filters retain the selected inspector even when its row is outside the filter. Close or Escape restores focus to its row, or the outcome filter if the row is hidden.
8. The existing Evidence downloads retain full precision. A fresh user analysis still uses **Analyze my data**, the six prepared files and explicit condition/processing review described in the public-pair README. Inspection never reruns RACE.

## Read-only endpoints

Both endpoints accept `study_id=public_er_pass2`, or an existing 32-character hexadecimal local run ID produced by BRACE. They do not create runs, execute uploaded code, fit models, normalize values or run association tests. A selected family is capped at 20 by the existing engine; the complete family is returned without pagination.

### `GET /api/race/studies/{study_id}/genes`

| Field | Contract and authoritative origin |
|---|---|
| `study_id`, `hypothesis_hash` | Exact requested run and saved `race_result.json` identity, checked against the frozen signature and methods. |
| `aggregate`, `positive`, `negative`, `feature_coverage`, `warnings`, `evaluation_role` | Unchanged saved RACE result fields. |
| `genes[]` | Complete saved result rows in frozen source selection order: `feature_id`, `selection_rank`, `source_effect`, `source_q`, target `effect`, `q`, `p`, `hedges_g`, `ci95`, `n_positive`, `n_negative`, `direction_agreement`, `classification`, `reason`, and the other saved fields. No recalculation. |
| Enriched source statistics | `source_p`, `source_hedges_g`, `source_ci95`, `source_n_positive`, `source_n_negative` from the corresponding frozen source record. |
| Enriched annotation | `gene_symbol`, `probe_id`, `annotation_note`, `feature_namespace`. Symbols/probes are supplied only from pinned public platform annotations when all six input hashes equal the approved pair. Otherwise symbol/probe are null and the exact feature ID remains authoritative. |
| `condition_definitions` | Frozen common definitions, keyed by the exact positive/negative labels. |
| `cohorts.source`, `cohorts.target` | Hash-checked parsed input context: cohort/study/accession, sample count, per-condition count/proportion, feature count, namespace, platform, measurement type, processing description, independence declaration, notes. `preparation` is the pinned public inclusion/exclusion summary when inputs exactly match; otherwise null and `original_exclusions_known=false`. |
| `shift_available`, `shift_note` | False for this RACE computation, with an explanation. Existing ACE shift/PCA outputs remain accessible; none are invented for RACE. |

### `GET /api/race/studies/{study_id}/gene?feature_id={exact_id}`

| Field | Contract and authoritative origin |
|---|---|
| `feature` | The selected saved target result row plus the same verified annotations. Only frozen selected features are accepted. |
| `cohorts.{role}.statistics` | Entire source frozen record or entire target saved result record, including signed mean difference, BH q, Hedges' g and pointwise interval. Source q controls the 10,000-feature source screen; target q controls the complete frozen selected family. |
| `cohorts.{role}.groups[]` | Negative group first, then positive. Exact condition, included `n`, measured `observed_n`, and ordered `samples: [{sample_id, value}]` from the uploaded/prepared matrix aligned with parsed metadata. Saved group sizes must match. |
| `available`, `unavailable_reason`, `missing_values` | A present feature has all finite values under existing intake and zero missing included cells. A missing target feature has no observations, `available=false`, reason `missing_target_feature`, `missing_values=null`; saved null statistics remain null. No zeros or distributions are substituted. Other undefined-test reasons are retained even when measurements exist. |
| `trace` | Exact study/gene/hash, frozen selection rule, source and target testing-family sizes, six input records with hashes, method version, software, test/effect/CI/multiplicity descriptions, `no_statistical_rerun=true`. |
| `measurement_comparison`, `warnings` | Separate-cohort scale statement and unchanged run warnings. |

Before serving either response, the server verifies the public pinned evidence, or each user's five scientific artifacts against its saved reproducibility manifest; checks canonical frozen hash/family ordering; validates allowlisted saved input filenames; checks all six input hashes and parses them using actual intake. Parsed cohorts are cached with a four-entry limit keyed by paths, hashes and role. Hash checks occur on every request. No new persistent data store is introduced.

Unknown/unsafe run IDs and non-selected features return 404. Missing or mismatched saved user evidence/input returns 409 `MOLECULAR_EVIDENCE_UNAVAILABLE`, with restoration guidance. Unavailable or changed pinned public evidence retains the existing public-example verifier's 503 response and restoration message. The client clears old measurements while loading, shows failure/retry, and never substitutes a different gene. Generation tokens and current run/gene checks reject late responses.

## Presentation, state and scientific boundaries

The six summary counts use the complete frozen family regardless of table filters. The default is all outcomes. Numeric columns sort using underlying numbers, nulls last, exact feature-ID tie breaks. Tables use bounded vertical and horizontal scrolling. Search is literal case-insensitive feature/symbol text. Absent annotation/statistics display **Unavailable**. Zero direction remains indeterminate rather than agreement.

Signed effects, Hedges' g and interval endpoints display three decimals (absolute rounding error at most 0.0005). q values display four decimals (at most 0.00005), or three significant scientific digits below 0.0001. Group proportions display one percent decimal. Counts and IDs are exact; raw-value tables retain numeric values. Full-precision saved JSON/CSV remains authoritative. JavaScript computes plot coordinates/jitter and presentation counts only; it does not compute statistical estimates or support.

Each plot's y range comes only from that cohort's observed values, with padding, ticks and normalized log-intensity units. Dots are measured observations; horizontal jitter separates overlaps without changing y values. Hover identifies the sample; expandable tables provide keyboard-readable exact observations. No line or shared axis claims comparable absolute source/target intensity.

Session state retains selected run, feature, filters, sort and inspector through relevant navigation/refresh. Starting another run clears gene-specific state and restores all outcomes. FACE is a nonmodal contextual aside: the rest of RACE stays usable. It closes with its button or Escape and restores focus. Reduced motion remains respected.

The public pair supports exploratory within-cohort association and cross-study gene-direction/support inspection. GC-RMA versus RMA, EIA versus IHC ER assessment, unverified cross-study donor independence, selection bias and observational confounding remain. CIs are pointwise, not selection-adjusted simultaneous intervals. Matching estimates without support do not establish absence; an opposite sign does not establish significant reversal. This pass adds no clinical, causal, source-model-transfer or direct-scale validation claim.

## Review evidence

`PASS04_BROWSER_RESULTS.json` records 11 actual Chrome scenarios. `PASS04_LEGACY_BROWSER_RESULTS.json` records 20 previous-pass browser scenarios rerun on Pass 4. Original Pass 3 receipts/screenshots are retained under their original names.

`pass04_screenshots/face_source_1440.png`, `face_target_1440.png` (inspector crop), `face_1280.png`, `face_390.png`, `unsupported_1440.png`, and `trace_1440.png` show real pinned public evidence. `missing_target_1440.png` and `missing_target_detail.png` show an explicitly controlled test: a real engine run using public measurements with target feature 135112 deliberately omitted. That test is not a new biological finding. Delay/failure/long-label fixtures exist only in browser tests and are not used as public scientific screenshots.

To rerun browser checks on a spare local port while preserving production origin restrictions, install Playwright as a developer test dependency and use installed Chrome. The already supplied `tests/browser_host.py` maps only its own test-port origin; it is not used by the production launcher:

```powershell
$env:BRACE_RUNS_DIR='C:\path\to\temporary-runs'
python -m uvicorn browser_host:app --app-dir tests --host 127.0.0.1 --port 8766
# In another terminal in the project folder:
python tests\browser_pass04.py --url http://127.0.0.1:8766
python tests\browser_pass03.py --url http://127.0.0.1:8766
```

The older browser script writes its original receipt/screenshot names; archive those before rerunning if preserving historical review evidence. There are no new application runtime dependencies.
