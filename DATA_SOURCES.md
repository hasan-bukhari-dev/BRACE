# Research data and attribution

The software rights notice does not relicense data, publications, fonts or third-party software. Original records and hashes remain under `examples/`; do not remove their provenance or claim those studies as BRACE's own data collection.

## Curated public ER example

- **GSE42568**, source: Clarke et al., *Correlating transcriptional networks to breast cancer survival: a large-scale coexpression analysis*. Carcinogenesis 34:2300–2308 (2013). PMID 23740839; DOI [10.1093/carcin/bgt208](https://doi.org/10.1093/carcin/bgt208). [Official GEO record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE42568).
- **GSE20711**, target: Dedeurwaerder et al., *DNA methylation profiling reveals a predominant immune component in breast cancers*. EMBO Molecular Medicine 3:726–741 (2011). PMID 21910250; DOI [10.1002/emmm.201100801](https://doi.org/10.1002/emmm.201100801). [Official GEO record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE20711).
- Platform **GPL570**, Affymetrix Human Genome U133 Plus 2.0. The included historical annotation snapshot, source-only representative-probe selection and feature filtering are documented and hashed. Gene symbols are not independently revalidated current nomenclature.

Included analysis: 101 source and 87 target tumors; ER-positive minus ER-negative; 10,000 source-filtered features. This is exploratory gene-association replication, with GC-RMA/RMA, phenotype-assay and donor-independence limitations. Matching platform IDs do not establish direct scale or model-transfer eligibility.

See [original preparation README](examples/public_er_pair/README.md), `examples/public_er_pair/evidence/downloads.json`, `prepared/prepared_hashes.json` and the [scientific protocol](docs/SCIENTIFIC_PROTOCOL_1_0.md). The rejected GSE29431 investigation remains documented; it is not silently substituted into the runnable example.

**Reuse status:** public GEO downloads are available from the original repository. A study-specific blanket redistribution licence was not verified in the preparation checkpoint. Preserve attribution and original notices, and assess applicable study/institutional conditions for downstream uses. Included publication material retains its original copyright. This document grants no additional rights to third-party content.

## Historical and artificial examples

CancerShift historical predictions are saved research evidence, with original sources and contribution disclosures retained. Opening them does not rerun the original classifier. Synthetic fixtures and interface stress tests are explicitly artificial; their performance is not biological or clinical evidence.

## User data

Generated/private runs, uploads, caches, environment files and credentials are excluded from Git. Desktop runs are stored in the user's BRACE data folder. EMBRACE excludes raw uploads by default; users remain responsible for reviewing derived exports before sharing them.
