# PASS 01B REPORT

**Decision:** ready for independent review and Pass 2 development of an **exploratory ER gene-association replication** experiment, subject to retaining the scientific restrictions below. No Pass 2 implementation or biological test results supplied. Locked external validation, direct scale comparison and model transfer are not approved.

## Files added and baseline preservation
No existing application, test, frontend, engine, API, limit, historical artifact or release-manifest file changed. Added `tests/test_public_er_pair.py` and `examples/public_er_pair/` containing pinned raw matrices, deterministic `prepare.py`, curated inputs, all-sample ledgers, complete probe selection ledger, mapping snapshot, README, download evidence and actual integration results. Original supplied archives remain unchanged. Existing 121-file manifest continues to cover the frozen baseline; added files are covered by CHECKPOINT_SHA256.json.

User reports independent baseline verification: 121/121 release files, 151/151 tests and scientific smoke passed. Accepted as externally reported, not rerun or claimed as newly verified here. A byte comparison to the Pass 01 application found zero changed baseline files.

## Retrieval and dataset decision
Official GEO download documentation was consulted. Default restricted-shell retrieval initially failed DNS resolution (`getaddrinfo failed`, 11001); enabling network access resolved it. Official HTTPS directory listings verified actual filenames before retrieval. Both matrix and family SOFT downloads succeeded for GSE42568 and GSE29431, then for one alternative target GSE20711. No raw CEL reprocessing and no second alternative pair.

Initial GSE42568/GSE29431 tumor/normal proposal was not approved: GC-RMA/RMA differences; cancer-patient normal controls with unresolved donor pairing; GSE29431 paper reports seven rejected arrays not reconciled here to GEO IDs. It was not rejected because of CAPTCHA. Its 66 sample annotations are retained. Source publications identified: Clarke et al. PMID 23740839 / DOI 10.1093/carcin/bgt208; Cuadros et al. PMID 22832278 / DOI 10.1159/000339431. Publisher full texts returned HTTP 403; source GEO full annotations and PubMed citations were inspected; GSE29431 QC methods were available as an indexed paper excerpt, not full-paper review.

Selected alternative: GSE42568 source → GSE20711 target, tumors only, ER_positive versus ER_negative. Target source: Dedeurwaerder et al., EMBO Mol Med 2011;3:726–741, PMID 21910250, DOI 10.1002/emmm.201100801. Its open full text and official GEO README were inspected. Both use GPL570; full deposited annotations reviewed. Counts below are calculated from actual files, not inferred from publication abstracts.

| Cohort | Original samples | Included | ER+ | ER− | Excluded |
|---|---:|---:|---:|---:|---|
| GSE42568 | 121 | 101 | 67 | 34 | 17 normals, 3 missing ER |
| GSE20711 | 90 | 87 | 42 | 45 | 2 normals, 1 missing ER |

Both original matrices have 54,675 probes. Both prepared matrices have 10,000 identical Entrez gene IDs, represented by identical GPL570 probes. Select one unambiguous probe per gene by highest population variance in included source tumors; then top 10,000 genes by source variance. Lexicographic ties are explicit. No target values/outcomes choose probes/features. Full selection audit is supplied. Values preserve deposited decimal strings without added normalization or rounding. This limits the inferential universe to 10,000 source-variable genes.

## Scientific eligibility and limits
- Within-cohort association: exploratory eligible, conditional on one independent tumor specimen per donor, using the recorded clinical ER labels; associations are not causal.
- Independent gene replication: exploratory eligible across separate acquisitions, with source-only hypothesis selection and frozen target tests to be implemented in Pass 2. This is not a claim of replicated findings.
- Direct scale comparison: not approved; log2 GC-RMA versus deposited RMA/log2 processing differs. No pooling or silent correction.
- Model transfer: not approved; legacy exploratory compatibility is preflight syntax/metadata acceptance only.

Source clinical ER comes from EIA (>200 fmol/g protein); target ER is IHC 0/1, as documented in its README. These are related biological contrasts with different assay definitions. Target is a Jules Bordet main-set expression subset, selected to balance subtype and relapse status; nonrandom sampling, HER2/grade/purity/age and technical confounding remain. Normals are excluded to avoid uncertain pairing. Target patient codes are unique; source specimen codes are not authenticated patient IDs. No overlapping GSM IDs or exact whole expression vectors were found, but donor linkage across studies cannot be authenticated. Manifests deliberately declare unknown independence; locked mode is blocked. Source full publisher methods remain inaccessible, so source acquisition evidence is limited to GEO and linked citation. No blanket data license or consent authorization is invented: public GEO availability is documented; study-specific redistribution terms remain unverified. See preparation README for citations, exact rules and downstream reuse limitations.

## Actual verification and commands
An isolated workspace virtual environment was created with `python -m venv work/venv`; NumPy 2.4.6 and pytest 9.2.0 were installed into it, without altering Espressif packages.

- `python work/build.py` invoked the delivered `prepare.prepare(raw, out)` function: completed; hashes checked, matrices and sample/feature ledgers generated. The README supplies the equivalent standalone CLI command.
- From application directory: isolated Python `-m pytest tests/test_public_er_pair.py -q`: **5 passed in 25.85s**; final rerun after the mapping-extraction helper addition: **5 passed in 24.34s**.
- Tests check full sample/metadata alignment, label counts, feature identity, API byte limits, finite values, every prepared expression cell against original values, unique target patients, complete exclusion ledger and byte-identical regenerated outputs.
- Actual `parse_cohort` and `evaluate_compatibility` calls: `compatible_with_caveats`, with PROCESSING_DIFFERENCE, TARGET_INDEPENDENCE_UNKNOWN, PATIENT_IDENTIFIERS_ABSENT. `external_locked`: ineligible. Exact-vector duplicate count: 0 across 188 included samples. Full machine-readable result: `examples/public_er_pair/integration.json`.
- A first pytest invocation from the parent workspace failed collection (`No module named brace_core`); rerunning from application directory resolved it. A scratch integration invocation initially hit a local `inspect.py` name collision; renamed that scratch file, then integration succeeded. Neither failure indicates a baseline regression.

Preparation hashes in `prepared/prepared_hashes.json` include exact byte sizes: source expression 12,069,487 bytes and target expression 10,402,456 bytes, each below 26,214,400 bytes (25 MiB). Feature cap unchanged at 25,000. The original target gzip is 26,895,121 bytes and is an acquisition artifact, not an API upload; prepared TSVs meet the limit. No limit was relaxed.

## Download records
All files below were actually downloaded and hashed. The compact package bundles both approved original matrix gzip files, the extracted pinned mapping, target full-text XML, target README, original directory listings and rejected-candidate metadata. Large family SOFT files and rejected matrix are omitted from the ZIP but reproducible from recorded URLs/hashes; local acquisition copies were retained during this pass.

- `GSE42568_series_matrix.txt.gz` — 22,565,943 bytes; SHA-256 `43b93f72f1d81838dcd2a5b6ccc3bc1875e46230dad0d7346236773a99e32b76`; [original download](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE42nnn/GSE42568/matrix/GSE42568_series_matrix.txt.gz).
- `GSE42568_family.soft.gz` — 59,874,216 bytes; SHA-256 `e7692c6f8b78ed4a46f3a574de79fb120a2f59960406cba7b896efdb90f55679`; [original download](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE42nnn/GSE42568/soft/GSE42568_family.soft.gz).
- `GSE29431_series_matrix.txt.gz` — 8,181,340 bytes; SHA-256 `9ad76f66469ae1fc44381af277662ad9beaa0bebd806279d98b33a7bdb301fa6`; [original download](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE29nnn/GSE29431/matrix/GSE29431_series_matrix.txt.gz).
- `GSE29431_family.soft.gz` — 30,131,956 bytes; SHA-256 `7814b76c17740bec30034388a59c8a9b894cd100e3e58395e3316b7648c1fd0e`; [original download](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE29nnn/GSE29431/soft/GSE29431_family.soft.gz).
- `GSE20711_series_matrix.txt.gz` — 26,895,121 bytes; SHA-256 `14d4f4ae57234d1e8deaeed9131d40b98664866f462eaab2b0309a9f96e107c1`; [original download](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE20nnn/GSE20711/matrix/GSE20711_series_matrix.txt.gz).
- `GSE20711_family.soft.gz` — 53,610,604 bytes; SHA-256 `e19a891cc7fb738cca420b55012e70d427fbd175a97f917cc4f34f8d09ddc380`; [original download](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE20nnn/GSE20711/soft/GSE20711_family.soft.gz).
- `PMC3377115.xml` — 135,045 bytes; SHA-256 `630a2e1d8d3af5bc5b373b31d417f27e5caa79a84c2d393ee81d0c1847921a92`; [original download](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3377115/fullTextXML).
- `GSE20711_README.txt` — 2,552 bytes; SHA-256 `5be4b3f411866bde789220fda1fccde46ddebb741f9ce077399cadb59cd26643`; [original download](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE20nnn/GSE20711/suppl/GSE20711_README.txt).

## Remaining boundaries and Pass 2
No engineering blocker remains for the supplied exploratory data workflow. Patient-authenticated independence, harmonized ER measurement and comparable absolute expression scales are not established. Future locked or clinical claims require additional evidence/design work. Pass 2 may begin **only with exploratory status and these restrictions carried forward**, after independent review; no subsequent pass was started. No new UI behavior or direct model-transfer readiness is implied.
