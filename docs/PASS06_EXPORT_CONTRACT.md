# EMBRACE export contract — Pass 6

EMBRACE is standard HTML/CSV/JSON inside a ZIP, version `brace-embrace/0.6.0`. It packages saved evidence without fitting a model or rerunning hypothesis tests. `GET /api/embrace/{study_id}` accepts the verified examples `public_er_pass2`, `historical_cptac`, or an existing validated user run ID. Existing bundle and individual-download routes remain available. Analysis/preflight work uses the existing worker pool so a heavy operation does not monopolize the async request loop.

## Reader journey

Open the public ER study, inspect RACE/FACE and Evidence, then choose **Export EMBRACE evidence ZIP**. The archived CPTAC study also exposes this action. A real preparing state ends only after a valid ZIP response; errors preserve the selected run/gene/sample and offer Retry. Open `research_summary.html` after extracting the ZIP. Relative links point to local evidence. The report has no executable script or external network dependency. Exact floating-point tables scroll horizontally when needed.

## Applicable contents

All packages carry a readable report, methods/software versions, input/output hashes, provenance declarations, compatibility, warnings/exclusions, reproduction/privacy instructions and the CSV text-encoding ledger. RACE adds the frozen source signature, selection configuration, full source screen and complete target family. ACE adds available scored samples, per-class metrics, confusion matrix, confidence/coverage and source OOF/model artifacts where actually computed. Mode C includes shift/PCA evidence and excludes supervised metrics. Absent artifacts are not invented. Archived predictions are explicitly historical and are never described as fresh inference.

The separately delivered real public example contains these 18 files:

- `CSV_TEXT_ENCODING.json`
- `FILE_SHA256_MANIFEST.csv`
- `PRIVACY.md`
- `PUBLIC_DATA_PREPARATION.md`
- `REPRODUCE.md`
- `analysis_methods.json`
- `compatibility_summary.json`
- `consistency_audit.json`
- `race/FILE_SHA256_MANIFEST.csv`
- `race/race_methods.json`
- `race/race_result.json`
- `race/replication_genes.csv`
- `race/selected_signature.json`
- `race/source_gene_screen.csv`
- `race_config.json`
- `reproducibility_manifest.json`
- `research_summary.html`
- `warning_exclusion_records.json`

## Byte and identity contract

Internal scientific files remain exact. The internal manifest retains their hashes for TRACE and analysis readers. Published CSV views prefix potentially formula-active **text** cells with an apostrophe; control/whitespace-prefixed formulas are covered. Negative numeric effects/coordinates/signs stay numeric. `CSV_TEXT_ENCODING.json` records reversible row/column text changes. JSON retains authoritative exact identifiers. Consumers requiring exact original text must use the JSON/ledger rather than treating the spreadsheet-safe apostrophe as part of an identifier.

The ZIP's `artifact_sha256` hashes its published bytes; separate scientific-source hashes describe internal originals. Download metadata distinguishes them. Top-level `FILE_SHA256_MANIFEST.csv` covers every member except itself. JSON inventories do not self-hash. Package receipt hashes cover the complete ZIP. Cached exports verify input files, saved scientific artifacts, run configuration, published artifacts and ZIP bytes before reuse; mismatches return 409 and do not silently repair or bless altered evidence. A lock serializes same-run exports. Temporary staging and ZIP paths reject paths/junctions escaping the run root.

ZIP entries are sorted, use fixed 1980 timestamps and have relative safe names. Repeating unchanged export produces identical bytes. Different analysis run IDs are legitimate provenance differences even when numerical results match. Hashes detect changes relative to saved receipts; they are not signatures or independent authentication of biology. A local actor who can replace every receipt and the application is outside this integrity boundary.

## Scientific interpretation and reproduction

Source-screened associations and independently target-tested hypotheses have separate tables, denominators and correction families. Untestable source features remain in the prespecified screening family with p=1 for correction, while displayed undefined values remain null. Source OOF estimates are distinct from external scored records. Confidence intervals are pointwise and inherit patient/study dependence and selection limitations; neither confidence nor a same-direction effect certifies biological validity. Missing true classes are explicit, and shift alone cannot diagnose prediction failure.

Raw uploaded matrices/metadata, environment files, arbitrary files, local absolute input paths and executable model binaries are excluded. Derived IDs, predictions and scores can still be sensitive: review before sharing. Input hashes alone cannot reproduce a private run; obtain the matching original inputs and application/dependency versions, then follow the included instructions. The complete checkpoint retains the approved public preparation scripts and hashed data. `PUBLIC_DATA_PREPARATION.md` records original accessions, citations, download URLs, deterministic filtering and redistribution considerations; no blanket permission or new license is asserted. The GC-RMA/RMA ER example remains exploratory, with donor independence unverified and no direct-scale or source-model-transfer approval.
