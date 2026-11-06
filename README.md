# BRACE

**Biological Reliability Assessment across Cohorts and Experiments**

A local research workbench for testing cross-cohort associations, evaluating saved predictions and inspecting reproducible evidence.

A finding in one study may not hold in another. BRACE freezes source choices, tests compatible target data and records what was calculated. It serves researchers and students working with processed human bulk-expression data and classification predictions; it does not establish mechanism or clinical validity.

![Current BRACE workspace](docs/manual/screenshots/01-workspace.jpg)

## Choose your question

| Tool | Official name | Use it to |
|---|---|---|
| BRACE | Biological Reliability Assessment across Cohorts and Experiments | Organize studies and saved work |
| RACE | Replication Assessment of Cohort Effects | Test frozen source associations in a target cohort |
| ACE | Algorithmic Classifier Evaluation | Evaluate saved predictions, train the supported baseline or replay it |
| CE | Cohort Evaluation | Compare measurements and distributions |
| EMBRACE | Evidence Management, Bundling, Reproducibility, Audit & Controlled Exports | Inspect and export evidence; the E navigation destination |
| SPACE | Study Provenance, Acquisition & Cohort Exploration | Find and acquire official public studies |
| FACE | Feature Analysis of Cohort Expression | Inspect measurements and dated gene-reference context |
| TRACE | Transparent Record of Analysis, Computation & Evidence | Inspect recorded methods and calculations |

## Start

[Latest verified Windows release](https://github.com/hasan-bukhari-dev/BRACE/releases/latest) · [Quick start](docs/QUICK_START.md) · [Illustrated PDF manual](docs/USER_MANUAL.pdf) · [Editable manual](docs/manual/USER_MANUAL.md)

Download the Windows x64 setup executable and close BRACE before installing. Alternatively, extract the **entire** portable ZIP and open `BRACE.exe`. Python is bundled. Keep the controller open while working; **Stop & close** stops its server. Binaries are unsigned research software.

For source installation, use standard 64-bit CPython 3.11–3.13, not an embedded toolchain interpreter. On Windows run `SETUP_BRACE_WINDOWS.bat`, then `START_BRACE_WINDOWS.bat`. On macOS/Linux run `sh SETUP_BRACE.sh`, then `sh START_BRACE.sh`. For a matching release build use pinned CPython 3.11.9 and [release instructions](docs/release/RELEASING.md).

The connected path is **Question → Data → Preparation → Eligibility → Analysis → Inspection → Evidence**. Open **Data & analysis**, choose a task, add files or acquire a study in SPACE, review the scientific declarations, check eligibility and compute. Downloaded data require preparation. Prepared versions can be reused in either role; completed analyses retain exact identities.

## Inputs and examples

RACE supports unpaired normalized log2 human microarrays with reviewed equivalent groups. CE supports its declared normalized expression types, including supported RNA-seq measurement declarations. The normal/tumor baseline requires the exact supported labels and source-only fitting. ACE also accepts reviewed saved-prediction tables with optional complete probability vectors. [Input formats](docs/DATA_GUIDE.md) · [New data](docs/NEW_DATA.md).

Raw FASTQ/CEL, arbitrary model files, raw counts and arbitrary assays are not accepted as analysis-ready inputs. Limits and rejection reasons are explicit; identifier mapping does not manufacture biological equivalence.

Three real demonstrations cover ER associations (GSE42568 → GSE20711), archived CancerShift predictions and cohort measurement comparison. The historical ER configuration has **14/20** supported associations from 101 source and 87 target tumors. CancerShift evaluates **680 archived predictions**, with 668 correct; its original model is not rerun. Additional GSE21653 preparation and analysis are recorded separately. These are exploratory examples, not prospective or clinical validation. [Walkthrough](docs/JUDGES_DEMO.md) · [Sources](docs/DATA_SOURCES.md).

## Interpretation and privacy

Matching direction plus target BH q ≤ 0.05 defines operational RACE support. Multiple probes may represent one gene. Confidence filtering changes coverage; scores need not be calibrated. PCA separation does not prove model failure. CE withholds unsupported inference. Reference summaries describe known gene functions, not mechanisms established by the experiment. [Methods](docs/SCIENTIFIC_PROTOCOL_1_0.md) · [Limitations](docs/LIMITATIONS.md).

Processing runs locally on `127.0.0.1`. Uploaded measurements remain local. Explicit SPACE queries and uncached gene-identifier lookups contact NCBI; cached demonstrations and local statistics work offline. Saved data, runs and browser drafts persist locally. Ordinary evidence exports omit original uploads; private workspace backups include them and cached references. [Storage and reproducibility](docs/REPRODUCIBILITY.md).

## Verify and maintain

Use `python verify_release.py`, `python -m pytest -q`, `python scripts/release_smoke.py` and `python scripts/check_repository.py` in the isolated environment. Evidence exports record hashes, methods and input lineage. Source sealing verifies recorded bytes; checksums are not digital signatures or guarantees of clinical validity. [Architecture](docs/ARCHITECTURE.md) · [API](docs/LOCAL_API.md) · [Verification](docs/RELEASE_1_2_4.md).

The source product version is **1.2.4**. Download links resolve to the latest actually verified release. Automated source, DOM, binary and installer evidence does not establish unfamiliar-user usability or WCAG compliance.

## Rights and references

BRACE-authored material is **rights reserved**, not MIT-licensed open source. Data and bundled dependencies retain their own terms. [License](LICENSE) · [Notices](docs/THIRD_PARTY_NOTICES.md) · [Attribution](docs/ATTRIBUTION.md) · [Scientific references](docs/RESEARCH_FINAL.md) · [Security](.github/SECURITY.md).
