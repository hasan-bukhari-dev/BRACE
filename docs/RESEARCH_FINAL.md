# BRACE research reconstruction — November 4, 2026

This is the isolated working copy of local `main` at `1d31e7136636913f999faa09f7f029be6cac2818`. The original checkout was read only. Git's local clone helper was blocked by Windows; the equivalent copy contains all 286 tracked baseline files and independent copied Git objects, with no object alternates and no copied runtime state. Nothing was published, tagged, pushed or substituted from an older release.

The scientific scope remains exploratory research. Passing software tests does not establish patient independence, clinical utility, causal biology or an optimal gene signature.

## Open and demonstrate

Open **OPEN_RESEARCH_FINAL.bat** in the working-copy root. It uses the independent `.venv` and `runs` directories and loopback port **8881**. If this copy is already running, open [the local workbench](http://127.0.0.1:8881). Leave the launch window open; Ctrl+C stops a source-launched server. Other BRACE installations are left alone.

The installed environment is standard CPython **3.12.10 x64** with `requirements-release.txt`. The first environment was based on the machine's default ESP-IDF Python; BRACE's launcher correctly rejected it. That environment was moved under excluded `work/esp_idf_environment`, and the standard environment replaced it. No global Python installation was modified.

For a clean source setup, use an installed standard CPython 3.11–3.13 to create `.venv`, then run `.venv\Scripts\python.exe -m pip install -r requirements-release.txt`. The current prepared environment already has these dependencies.

The saved local demonstration portfolio includes:

| Analysis | Open |
|---|---|
| Original public ER replication | [GSE42568 → GSE20711](http://127.0.0.1:8881/#race?run=36ea07908b634e8d94c6cfc770a0ed16) |
| Additional exploratory ER cohort | [GSE42568 → GSE21653](http://127.0.0.1:8881/#race?run=b479e4ed3e0f4a5e8a618525f52de8fd) |
| CancerShift archive, evaluation only | [680 recorded predictions](http://127.0.0.1:8881/#ace?run=de8b59ca3ac041ad9914a1c773cc5e6c) |
| Descriptive cohort comparison | [CE](http://127.0.0.1:8881/#cohorts?run=7bff97a65a29485984d549f47077cb9f), then choose **Distribution comparison** |
| Artificial baseline training | [Synthetic source CV and target scoring](http://127.0.0.1:8881/#ace?run=5fb820e295234a918931398ea7e28259) |
| Application without refitting | [Synthetic frozen-baseline replay](http://127.0.0.1:8881/#ace?run=186e9286153f468bb9e0130aca6c3d65) |

These IDs are local to the delivered runtime. The scientific verification script uses a separate `work/validation_*` runtime. Re-running it does not replace the demonstration studies. Public examples and saved studies work offline; new SPACE discovery/acquisition requires a network connection.

## Major findings and implemented changes

| Severity / type | Confirmed evidence | Repair and verification |
|---|---|---|
| P0 scientific | CE produced KS p/q values despite differing declared processing or known dependence. | `brace_core/shift07.py` now withholds inferential values while retaining descriptive D, medians and source-fitted PCA. Real ER-cohort runs and exports were checked. |
| P0 scientific | A rank-one source can produce a numerical second PCA axis; dividing by an arbitrary epsilon yields extreme distances. | Rank below two now makes the two-axis projection/distance unavailable. A collinear boundary test exercises this condition. |
| P0 state integrity | Changing a saved-run hash in an already open browser tab could leave the previous analysis visible under the new URL. | `js/journey.js` now resolves external hash changes through checked startup. Normal Back/Forward snapshots retain their existing restoration path. Actual module tests and live run switching cover the repair. |
| P1 scientific clarity | Twenty was a hard-coded source-selection cap, not a display setting or demonstrated biological optimum. | `signature.py` accepts an explicit integer `selection_count`, 1–1000, default 20. The cap is recorded in the frozen rule and checked during target testing. Source testing, ranking and FDR remain unchanged. Nondefault caps identify `brace-race/0.2.0`; the historical default retains `brace-race/0.1.0`. |
| P1 workflow | General acquisition could reach the registry, but preparing the additional real cohort required composing a large JSON plan. | `public_recipes.py`, `dataset_api.py` and `js/datasets.js` provide an explicit, exact-byte-pinned GSE21653 plan. It shows labels, exclusions, mapping and limitations before the review checkbox enables preparation. Unknown/changed annotations fail closed. |
| P1 comprehension | Prepared-universe size, source eligibility, frozen cap and statistical definitions were difficult to distinguish. | RACE now shows **10,000 prepared → 1,339 source FDR passes → 20 frozen** beside the result, with concise expandable definitions. Filtering does not change the testing family. A retained selection outside the filter is explicitly identified. |
| P1 evidence | Biological context needed current, dated references independent of experimental claims. | Twenty NCBI Gene records supply dated context and links. Original platform symbols/probes retain their provenance. `BIOLOGICAL_CONTEXT.json` and the readable report carry this context in EMBRACE 0.8.1; no statistical values are rewritten. |
| P1 UX | Method panels, duplicate feature navigation and fixed decorative ribbons displaced scientific content. ACE confidence controls appeared before its overall/class summary. | Compact RACE method row; collapsed optional feature strip; denser tables; ribbons confined to the introductory area; ACE accuracy and confusion overview moved before confidence filtering. Frozen application now has its own method receipt and heading, distinct from imported evaluation and source training. Actual screenshots were reviewed. |
| P1 provenance / reliability | SPACE-derived registered data could be labeled “uploaded,” and browser assets could remain stale during local updates. | Generic registered-result labels now describe recorded dataset versions; static assets revalidate. Stored provenance remains the authority. |
| Evidence gap | Archived CancerShift scripts exist, but the referenced fitted joblib models/reference bundles were not located in the inspected archival package. | The case remains explicitly evaluation of historical predictions. No CancerShift ensemble training or new inference was claimed or executed. |

The former byte-immutability test applied to a copy-edit-only phase. It now checks explicit, hash-bound scientific changes in `quality/SCIENTIFIC_CHANGE_REGISTER.json`, while unchanged engines still have to match the original baseline hash register. The original baseline hashes were preserved. Regression tests and numerical checks accompany the two declared engine changes.

## Scientific validation

### A. Original ER association experiment

Source **GSE42568** contains 101 included tumors: 67 ER-positive and 34 ER-negative. Twenty of 121 deposited samples were excluded before the prepared input: 17 non-tumor and three missing ER annotations. Target **GSE20711** contains 87 included tumors: 42 positive and 45 negative; two non-tumor and one missing-ER sample were excluded from 90 deposited samples.

The pinned GPL570 mapping and source-only preparation contain **41,824 eligible unambiguously mapped probes representing 20,486 Entrez identifiers**. One probe per gene is chosen by source population variance, then 10,000 genes are retained by source variance rank. The original matrix contains 54,675 probe rows. The prepared 10,000-feature family is therefore a documented subset, not a complete transcriptome census. Target data do not choose the source probe or source feature rank.

Within each cohort, the sign is **ER-positive minus ER-negative** in deposited processed log-intensity units. Source two-sided Welch tests and BH correction cover all 10,000 prepared features, with conservative p=1 contributions for undefined tests. **1,339** pass source q ≤ 0.05. Qualifying features are ranked by absolute Hedges’ g, then identifier; the declared cap freezes the target family before target testing.

The historical default recomputed to **14/20 supported matching-direction associations**, **five matching without target support**, and **one opposite estimate**. Nineteen of 20 estimated directions match. The opposite LPCAT2 estimate has target q about **0.1794**; its opposite sign is not evidence of a statistically established reversal. These counts are association results, not classifier accuracy.

Independent code paths using `scipy.stats.ttest_ind`, `false_discovery_control`, direct gamma-corrected pooled effects, and Welch confidence intervals checked all 10,000 source statistics and all 20 selected target tests. Maximum absolute discrepancies were approximately **3.61e-14 for p**, **3.65e-14 for q**, and **3.64e-14 for Hedges’ g**. The reference used the same declared conservative zero-variance exclusion rule; treating those tests differently changes the BH family. This is independent numerical checking, not an independent laboratory or human peer review.

Repeated runs retained the same frozen hypothesis, selected features and numerical outputs. Saved results reopened, and CSV/JSON/ZIP counts and identities reconciled.

| Exploratory cap sensitivity | Supported matching direction | Selected |
|---|---:|---:|
| 5 | 5 | 5 |
| 20 | 14 | 20 |
| 50 | 35 | 50 |
| 100 | 67 | 100 |

These caps were compared after the target outcome was known. No cap is presented as optimal, prespecified validation or an independently confirmed winner. Ten fixed-source target-label permutations, seed **20261104**, produced supported counts **[0,0,0,0,0,0,0,0,0,0]** without changing the source freeze. Ten permutations do not establish a calibrated false-positive rate. Exploratory role reversal produced 16/20 support **within the original source-prepared 10,000-feature universe**; it was not an independently repeated, fully reversed preparation pipeline.

### B. CancerShift archive

The supplied prediction table has **680** records and **668** correct predictions: **98.2353%**. At maximum score **≥0.95**, **584/680** remain (85.8824% coverage), with **583/584** correct (99.8288%) and **96** excluded records. The original local scored TSV matched its archived provenance SHA-256, `915d3fef7eafde02cca094463baba2d0400aa5d0837e8d358af6a55624cccdd7`. The converted table matched its own recorded checksum.

| True class | Support | Recall |
|---|---:|---:|
| Breast | 133 | 98.50% |
| Colorectal | 105 | 100.00% |
| Lung | 341 | 97.65% |
| Ovary | 101 | 98.02% |
| Prostate | 0 | Undefined |

The five-class vocabulary contains prostate, but this archive has **no true prostate records**. Prostate recall/F1 and all-five-class generalization are consequently unavailable. One breast case is incorrectly labeled ovary at score **0.998692106**, and remains above 0.95. The UI exposes the exact saved vector and recorded group for this case.

The ten-bin descriptive expected calibration error is **0.0172289** in this archive. A small aggregate binning statistic does not demonstrate clinical or deployment calibration, protect rare subgroups, or remove the high-confidence error. No calibration model was fitted. Row-level intervals do not account for unverified patient/study dependence.

The actual browser confidence slider was exercised at zero (680 retained, 668 correct), one (zero retained; selective accuracy/risk undefined), and the reference 0.95. A zero-count prostate confusion cell produced an empty record selection with the full evaluated denominator retained. None of these interactions retrains a model.

### C. Additional public cohort challenge

SPACE's real GEO search returned **GSE21653**, including study identity, publication links, platform and 266 deposited samples. Its official **22,510,462-byte** compressed matrix was acquired and persisted with SHA-256 **f13e3bf972bd92a6fd53a1fbe42ad7c84caf4651df3a5e836f70dd3b22b5e76f**. The actual numeric matrix has 54,613 probe rows.

Every sample explicitly says `tissue: breast cancer tumor`; ER labels came only from explicit `er ihc: 1/0` annotations. Three `NA` ER-IHC entries were excluded. The preparation retained **150 positive and 113 negative tumors**, with **10,000 source-mapped features**. A “Normal” molecular subtype was not converted into normal tissue or used to invent a phenotype. Deposited processing says RMA with quantile normalization; the plan declares the RMA log2 convention and discloses that BRACE did not reprocess CEL files.

The complete browser journey—search, verified filename, acquisition, original inspection, pinned-plan review, preparation, registered source/target assignment, eligibility and computation—completed without reuploading. It produced **20/20 supported matching-direction associations**, retained the original source selection rule, reopened from persistence and exported consistent evidence.

This cohort was investigated after examining the original experiment. No prospective validation-cohort selection or donor-independence authentication is claimed. ER ascertainment, processing, sample size and study population differ; the 14/20 versus 20/20 outcomes do not identify which factor caused the difference.

GSE103512 and GSE65194 were also investigated. Their official matrix listings reported roughly **79M** and **73M**, respectively, above BRACE's generic 25 MiB acquisition limit. They were not silently accepted or reported as completed experiments. The exact-byte exception for the bundled GSE20711 original does not generalize to arbitrary oversized files.

### CE and the baseline

Real ER-cohort CE outputs retain observed KS D, medians, source-IQR scaling and a source-fitted PCA projection. Processing differs, so p/q values are **withheld**, and no model-error cause or biological mechanism is inferred. PCA fits source scaling and source-selected variable features; no target outcomes choose the projection. A deliberately rank-one source makes the two-axis distance unavailable.

Artificial fixtures exercise source-only logistic training, cross-validation and application of the frozen JSON model without refitting. This verifies software behavior, not biological generalization. The baseline is distinct from the original CancerShift ensemble. Source OOF performance and target evaluation remain separate. Unlabeled frozen application has no accuracy claim.

## Methods and interpretation for a skeptical reviewer

| What to ask | What this software can defend |
|---|---|
| What was measured? | Deposited processed expression signals with explicit cohort/group definitions, or saved prediction records versus supplied reference labels. |
| Why Welch? | A simple declared unpaired mean comparison allowing unequal variances. Independence remains required. It does not adjust covariates or model repeated subjects. |
| Why not automatically replace it with limma? | Limma offers variance moderation and richer designs. Swapping methods would change the experiment and needs a separately validated protocol; popularity is not a validation argument. |
| What does g mean? | A bias-corrected standardized within-cohort mean difference using pooled sample SD; descriptive under unequal variance, not accuracy or a probability. |
| What does FDR support mean? | The declared BH-adjusted family threshold and matching estimated sign. BH requires suitable dependence assumptions. A q value is not the probability that an individual biological claim is true. |
| Why 20? | Historical declared selection cap, now explicit and configurable. It is not a biological optimum. |
| What do intervals establish? | Pointwise 95% Welch intervals for a mean difference, not simultaneous or adjusted for source selection. |
| What could make this wrong? | Misdeclared scale or phenotype, cohort overlap, confounding, annotation ambiguity, platform processing differences, winner's curse, limited power or unrepresentative samples. File hashes authenticate bytes, not the scientific declarations. |
| Why does the archive matter? | It makes a high-score error, missing-class coverage and the denominator cost of confidence filtering inspectable behind a strong headline accuracy. |

## Verification and performance

The final exact automated count and check statuses are recorded in **quality/FINAL_VERIFICATION.json** and the actual JUnit output at `work/full-unslop-final-tests.xml`. The final run passed **352/352 tests**, with zero failures, errors or skips, in **217.612 seconds**. One pinned Starlette/httpx deprecation warning remains. The actual navigation/state/operation module checks independently passed 4/4. `pip check` reported no broken requirements, and the standard-Python launcher guard passed.

Agent-led browser checks covered the live SPACE acquisition and preparation flow, guided public input loading/checking/computation, persisted run restoration, opposite-estimate filtering, gene measurements and dialogs, result-specific TRACE, archived prediction counts and high-score error inspection, confidence extremes/empty selection, CE projection and withheld inference, narrow 1024×768 RACE layout, and clearly marked artificial zero-selection/untestable-target results. Those artificial boundary fixtures are software checks, not biological evidence. The default desktop capture was about 1536×633. Screenshots and captured API outputs are real application evidence.

The Chrome extension's automated file-chooser helper was blocked by its file-URL permission. No browser permission was changed. Native fallback was also unavailable because the Chrome window was minimized. The multipart file-import boundary and saved-dataset reuse were exercised through real local APIs and integration tests; **a complete direct browser file-picker upload was not verified**. No independent human usability study, screen-reader study or full WCAG conformance test was performed.

| Measured operation | Result | Scope |
|---|---:|---|
| Fresh application process to health response | 2.68 s | One run; warm filesystem caches, not a cold-disk benchmark |
| Register pinned public originals/preparation | 1.59 s | Local data, no internet transfer |
| Public pair eligibility | 1.22 s | Local HTTP path |
| Public RACE execution | 7.39, 7.61, 8.09 s | Local HTTP through saved result and persistence; 101/87 samples, 10,000 features each |
| Evidence generation/response | 0.36 s | 5,421,352-byte ZIP in the measured export version; export size changes with added context |
| Peak serving-process working set | 230.3 MiB | Across three measured public runs; Windows process counters |
| Private committed bytes after those runs | 592.4 MiB | Distinct from physical working set; not a maximum-capacity result |
| Separate official GSE21653 download | 28.55 s | One direct timed network acquisition; browser acquisition separately verified but not timed |

The 25 MiB upload, 25,000-feature, 500-sample and 50,000-prediction boundaries are implementation caps, **not demonstrated maximum-throughput benchmarks**. Computation-only cap sensitivity took approximately 4.6–5.0 s per run and is separate from HTTP workflow timing. Detailed conditions and timing arrays are in `work/benchmark.json` and `work/research_validation.json`.

## Architecture and reproducibility

The application remains FastAPI plus vanilla JavaScript, NumPy/SciPy and the existing source-fitted scikit-learn baseline. SPACE retrieves only explicit public terms from fixed official hosts. Originals, prepared immutable versions, declared study roles, preflight records and completed runs are persisted under the isolated runtime. SQLite registry records connect assets and parent lineage; computations use registered assets directly. RACE freezes the source hypothesis before target statistics. ACE evaluates recorded predictions or the explicitly supported baseline. CE describes eligible measurements with inference gates. FACE/TRACE inspect the same saved run. EMBRACE audits identities/counts and publishes readable and machine-readable evidence.

Source methods, seeds, preprocessing, exclusions, hashes, class vocabularies, denominators, undefined values and exact numerical results travel with the evidence. Original private input files are excluded from shared ZIPs; matching originals are still required for full reproduction. Derived identifiers and provenance can remain sensitive and should be reviewed before sharing. No research files were sent to an external model service.

Useful evidence:

- [Scientific checks, sensitivity and negative controls](../work/research_validation.json)
- [Additional-cohort lineage and outcome](../work/geo_challenge_validation.json)
- [Measured benchmark](../work/benchmark.json)
- [Saved demonstration inventory](../work/demo_workspace.json)
- [Before RACE](../work/screenshots/before-race.jpg), [after RACE](../work/screenshots/after-race.jpg), [1024-pixel RACE](../work/screenshots/race-1024.jpg)
- [Zero selection](../work/screenshots/race-zero-selection.jpg), [untestable target](../work/screenshots/race-untestable-target.jpg), [desktop result](../work/screenshots/race-desktop.jpg)
- [Actual gene distributions](../work/screenshots/gene-measurements.jpg), [opposite estimate](../work/screenshots/race-opposite.jpg), [TRACE](../work/screenshots/trace-evidence.jpg)
- [SPACE acquisition](../work/screenshots/space-acquired.jpg), [oversized acquisition failure](../work/screenshots/space-acquisition-blocked.jpg), [additional RACE cohort](../work/screenshots/gse21653-race.jpg)
- [ACE overview](../work/screenshots/cancershift-evaluation.jpg), [high-score error](../work/screenshots/high-confidence-error.jpg)
- [CE inference gate](../work/screenshots/ce-inference-withheld.jpg), [source-fitted projection](../work/screenshots/ce-projection.jpg), [frozen application](../work/screenshots/frozen-replay.jpg)

Reproduce the consolidated numerical checks with `.venv\Scripts\python.exe scripts\validate_research.py`. Re-run the measured local HTTP benchmark with `.venv\Scripts\python.exe scripts\benchmark_research.py`. Generated outputs remain under excluded `work/`. Run the complete suite with `.venv\Scripts\python.exe -m pytest -q`. UI inventories are generated by `tools/audit_ui_strings.py`; multiline CSV fields must retain the generator's bytes. Source sealing and final manifest verification are recorded in the final verification JSON.

## External evidence and implemented decisions

Documentation was checked during this work; these references are comparative or methodological guidance, not certification.

- [NCBI GEO2R](https://www.ncbi.nlm.nih.gov/geo/info/geo2r.html) and [GEO downloads](https://www.ncbi.nlm.nih.gov/geo/info/download.html): explicit sample groups, processed-versus-original distinctions, methods and official acquisition receipts.
- [Limma](https://bioconductor.org/packages/release/bioc/html/limma.html): variance moderation and covariate-capable modeling informed the retained limitations; no unvalidated method substitution.
- [MIAME](https://www.fged.org/projects/miame): sample relations, original/processed data, platform annotation and processing provenance informed the preparation review. Missing information remains visible.
- [TRIPOD+AI](https://www.bmj.com/content/385/bmj-2023-078378) and [PROBAST+AI](https://www.bmj.com/content/388/bmj-2024-082505): distinguish model development, evaluation, reporting and risk of bias; no claim of compliance certification or clinical validation.
- [Scikit-learn pitfalls](https://scikit-learn.org/stable/common_pitfalls.html): source-fitted preprocessing, fitting within CV folds and target isolation were inspected and retained.
- [Galaxy](https://usegalaxy.org) and [cBioPortal](https://www.cbioportal.org): study selection, inspection and history conventions informed the existing registry/workbench approach; BRACE does not clone their feature scope.
- [NCBI Gene](https://www.ncbi.nlm.nih.gov/gene/135112): dated, source-linked functional context remains separate from experimental evidence; twenty records are pinned in `brace_app/gene_context.json`.

## Full UI cleanup — November 5, 2026

The supplied Unslop 2.3.0 skill guided a source and rendered-screen review. Twelve confirmed wording defects were repaired, including slogan headings, a misleading paired-effect label and an empty-state reassurance. Formal statistical names, thresholds, numerical claims and scientific limitations were preserved. The shared BRACE rectangle and the BRACE, RACE, ACE, CE, SPACE, FACE, TRACE and EMBRACE identities remain visible.

| Surface | Completed changes and observed checks |
|---|---|
| BRACE | Compact first-use screen; direct entries for all three analytical questions; dataset/saved-analysis shortcuts; duplicate headings and saved-analysis link removed. |
| RACE | Source/target effects named accurately; FACE and TRACE actions moved above the plot. Removing sticky preview positioning fixes controls clipped below short windows; actual mouse and keyboard activation checked. |
| ACE | Accuracy and its denominator are directly readable; redundant accuracy ring removed. Confusion counts, missing-class support, confidence extremes and high-score-error access remain functional. Prediction-format help opens the correct guide. |
| Dataset library | Search by name, accession or version; original/prepared filters; empty search recovery; compact rows and collapsed technical lineage. Selecting a saved prediction study retains ACE evaluation instead of silently switching to RACE. |
| CE | Actual source/target overview for saved comparisons; the active projection or feature view uses the full width. The q filter is disabled when inference is withheld. Reusing registered cohorts opens their assigned versions without another upload; the ER example remains correctly blocked for normal/tumor baseline training. |
| SPACE | Flat candidate/result surfaces, consistent forms, preserved review requirements. Official GSE21653 search/shortlisting and invalid-accession recovery were exercised. |
| FACE / TRACE | Measured cohort distributions and references retained; readable modal typography and close controls; TRACE steps form a compact navigation list beside the selected step and its actual artifacts. |
| EMBRACE | Report, calculation and file views share consistent controls; redundant run framing removed; readable report verified visible. File links and download handlers retained. |
| Shared UI | Consistent control sizing, table typography and focus states; scrollable tables accept keyboard focus; reduced-motion and print rules; mobile captions wrap instead of colliding. |

The final full suite passed **352 tests**, with one existing Starlette/httpx deprecation warning. Eight focused language/state/dataset-routing checks also pass. Scientific engine files are unchanged in this UI pass; prior independent numerical validation remains applicable. Desktop, laptop and 390-pixel narrow layouts were inspected in light and dark themes. This remains agent-led verification, with the human and installer limits below.

The skill's strict preservation and banned-phrase checks passed for the edited labels (zero hard phrase hits). It extracted no numerical constraints from those short headings; this is not numerical validation. Its prose structure, readability and edit-percentage warnings treat unrelated UI labels as a continuous article. These were reviewed as genre mismatches in the actual screens, not presented as a universal quality score. The exact edits and tool outputs remain at `work/unslop-copy-review.json` and `work/unslop-copy-validation.json`.

[Current public workbench preview](images/workbench-current.jpg) is included in the source payload and README. Local screenshots for landing, library, setup, confidence, CE, FACE, TRACE, discovery and responsive layouts are under `work/screenshots/full-unslop-*.jpg`. Runtime datasets, archival identifiers in local screenshots and skill-tool files remain excluded from Git. No remote push or release was performed.

## Remaining limits and priority follow-up

1. Authenticate donor independence and phenotype/processing equivalence before stronger cross-study claims. Supporting a paired/covariate-adjusted or limma protocol requires a new validated method, not a warning bypass.
2. Complete a direct browser file-picker import in an appropriately configured browser and conduct an unfamiliar-researcher usability/screen-reader review. Current inspection was agent-led.
3. Validate maximum workload capacity and a locally built installer separately. PyInstaller and the Inno Setup compiler were unavailable in the isolated environment; **no new executable or installer was built or certified**. The source application was launched and exercised.
4. Fresh CancerShift ensemble inference remains unsupported without its genuine fitted models, reference bundles and compatible input/preprocessing pipeline. Raw counts/FASTQ, single-cell, arbitrary model binaries and unsupported assays remain outside the implemented analysis paths.

This copy provides working, traceable exploratory workflows within those boundaries. It does not establish clinical readiness, causal biomarkers, universally calibrated classifier scores or external independent scientific validation.

## BRACE 1.1.0 release finalization

The later release pass adds a single real-data CE preset and keeps three main demonstrations: the original public ER association pair, the archived CancerShift predictions, and descriptive comparison of the public ER cohorts. FACE and TRACE inspect the RACE example. Artificial fixtures remain explicit developer checks and are excluded from normal library/history views by default; no user records were deleted.

ACE/RACE setup now stays inside its chosen tool. Frozen-strip genes open FACE. Inspector geometry stays anchored while data load. Inspectors update their current navigation state instead of adding close/reopen Back loops; a direct analysis link has a Workbench fallback. These changes were exercised in the compiled executable, not just the source server.

The full suite passed 354 tests. Nine focused checks passed after the final Back fix. The built Windows executable recomputed real public RACE (14/20), exposed FACE/TRACE, verified every evidence ZIP member hash, preserved GEO acquisition ancestry, reopened the run after restarting, and applied its controlled frozen baseline. The native controller self-test passed on the Windows host. All 42 bundled static assets matched the final source byte-for-byte. The setup.exe compiled successfully. Earlier statements that packaging tools were unavailable describe the earlier reconstruction phase and are superseded by these actual build receipts.

The portability verifier was updated from its stale EMBRACE 0.8.0 expectation to the implemented, documented 0.8.1 format, with an additional required biological-context artifact check. The scientific algorithms did not change in this release pass.

Installer install/uninstall is checked in an isolated GitHub runner rather than replacing and removing the user's existing installation during local QA. The release workflow publishes v1.1.0 only after executable, real-data portability, native-controller and installer checks pass. Those workflow receipts, release checksums and exact tagged source are the remote acceptance evidence. No independent human usability, clinical or other-platform package validation is claimed.

Use [the judge walkthrough](JUDGES_DEMO.md). The source launcher uses port 8883 and an isolated `runs/release-demo` workspace. Published Windows users should run the installer, which bundles Python and keeps runtime data outside installed resources.
