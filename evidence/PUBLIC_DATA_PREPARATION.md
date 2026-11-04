# Exploratory ER association replication inputs

**Scope:** GSE42568 source and GSE20711 target; ER-positive versus ER-negative primary breast tumors. These are genuine deposited bulk microarray measurements. No RACE tests, gene discoveries, prediction results or transfer results have been calculated.

## Scientific eligibility

| Use | Decision |
|---|---|
| Within-cohort ER association | Eligible for exploratory unpaired testing, conditional on one specimen per donor; study-specific clinical ER labels retained. Confounding remains. |
| Independent gene-association replication | Eligible as an exploratory independent-study experiment, with source-only hypothesis selection and frozen target tests in Pass 2. Patient-level independence is not authenticated; do not call this locked validation. |
| Direct expression-scale comparison | Not approved: source GC-RMA and target RMA differ. Do not pool values, treat between-study mean differences as biology, or compare fold-change magnitudes as interchangeable. |
| Source-trained model transfer | Not scientifically approved by this checkpoint. Parser eligibility alone does not establish transfer validity. No model run supplied. |

The contrast is receptor status **among tumors**, not cancer versus healthy tissue. Direction is ER_positive minus ER_negative. Both cohorts use GPL570. Source GEO labels derive from enzyme immunoassay (positive >200 fmol/g protein); target README defines IHC 0=negative and 1=positive. Different assays/cutoffs can change class membership. Do not derive clinical labels from expression-based subtype assignments.

GSE42568 includes 104 pretreatment tumors and 17 normal biopsies; exclude all normal samples and three tumors with unavailable ER. GSE20711 contains 88 tumors and two normals after submitter QC; exclude both normals and one tumor with missing ER. Every downloaded matrix sample appears in `prepared/*_all_samples.tsv`, with an inclusion reason and original annotation. The study reports P_64 and normal N6 failed QC before matrix deposition; they are not additional records silently removed here. The target publication also describes specimens without expression profiling because of tissue/RNA availability; the expression matrix is not the entire methylation cohort.

Target cases were collected at Jules Bordet Institute, Belgium (main set diagnosed 1995–2003), selected partly to balance IHC subtypes and relapse outcomes. This is not population-random sampling. Source study is a separate Dublin-led acquisition; accession/sample IDs do not overlap. Source tumor specimen codes are distinct, and target patient IDs are distinct. Source donor IDs are not authenticated, and a cross-study donor linkage registry is unavailable. Consequently both manifests conservatively declare `unknown` independence; separate studies support exploratory independence but cannot prove no shared donor. No normals are used, avoiding unknown tumor/normal pairing. Do not interpret significance as causal or clinically validated. Grade, HER2, age, tumor purity, selection, treatment histories and technical batches can confound ER associations. Target metadata have age bins rather than harmonized source ages. Pass 2 should state these limits and avoid claiming adjusted effects from an unadjusted screen.

## Initial candidate decision

GSE42568/GSE29431 were downloaded and examined first. GSE29431 has 54 tumors and 12 normal tissues from breast-cancer patients; normal donor pairing is not supplied. GC-RMA/RMA differ. Its source paper additionally describes seven array exclusions not reconciled here to GEO IDs. The initial tumor/normal design is not approved for naive independent-observation testing, direct scale comparison or model transfer. A tumor-only ER contrast was considered, but QC reconciliation remains unresolved. This is a design/QC limitation, not a CAPTCHA-based rejection. Only one alternative study pair was investigated: the selected GSE42568/GSE20711 pair.

## Reproduce

From `01_RUN_BRACE` (or this versioned application directory), with Python 3.11+:

```
python examples/public_er_pair/prepare.py
python -m pytest tests/test_public_er_pair.py -q
```

Preparation uses the standard library only; tests need existing BRACE NumPy and pytest dependencies. `--download` retrieves missing pinned matrices from original HTTPS URLs; `--raw PATH --out PATH` supports a separate output directory. Hash mismatch fails closed. No global interpreter packages need alteration.

The two original `.txt.gz` matrices are bundled in `raw/`. The six downloaded GEO matrix/SOFT files are listed with full URLs, byte sizes and SHA-256 in `evidence/downloads.json`. Large family SOFT files and the rejected candidate matrix are omitted from this compact package; they can be fetched using those exact URLs and verified against those hashes. Directory listings record actual filenames. `GPL570_mapping.tsv` is extracted from the platform section of the hashed source family SOFT (annotation build 35, platform updated December 2020), with its own hash. It preserves probe ID, Entrez ID and symbol. Target uses the same GPL570 probe definitions; target labels/values never choose the map. `PMC3377115.xml` and GEO README preserve target methods; GSE29431 full matrix metadata are retained for audit.

## Deterministic feature preparation

1. Parse all 54,675 original probes; require unique IDs and finite numeric cells. Parse samples by GSM identifier, never positional label guesses.
2. Restrict source to labeled tumors. Use the supplied GPL570 annotation snapshot. Exclude controls and probes without one digits-only Entrez gene ID (including multi-gene `///` mappings); do not resolve ambiguous mappings by guessing.
3. Calculate population variance across included **source** samples without using class labels. For each Entrez ID retain the highest-variance source probe; break exact ties lexicographically by probe ID.
4. Retain 10,000 genes with largest representative-probe source variance; tie by Entrez ID string. This is a compact, variable-gene universe, not the complete transcriptome or a significance-selected signature. Later multiple-testing denominators must use this universe. No target-based feature selection or differential-expression selection occurs.
5. Use the identical selected probe for each target gene; missing target probes fail rather than impute. Preserve original decimal strings without rounding, rescaling, log transforming again, normalization, batch correction or aggregation. Gene IDs and samples are sorted lexicographically. Entire probe ledger and selected IDs are included.

This source-only representative choice reduces multiple probes per gene and satisfies the 25,000-feature and 25 MiB API limits. Probe specificity and historic annotation can remain imperfect; no claim of current universal annotation is made. Do not interpret probe selection as an experimentally validated gene assay. A second-pass method must record the source variance filter and representative-probe selection as part of the hypothesis universe.

## Integration and provenance

Upload `prepared/source_expression.tsv`, `source_metadata.tsv`, `source_manifest.json` and their target counterparts. The actual intake format is features by samples, first column `feature_id`. Use explicit classes `ER_negative`, `ER_positive` if calling compatibility code. The legacy default normal/tumor classes do not describe this study. This package does not wire a new UI example or invoke the model-training API.

`prepared/prepared_hashes.json` pins every generated artifact, including byte sizes. `integration.json` records actual parser and compatibility outcomes (generated separately from deterministic inputs). Existing compatibility emits PROCESSING_DIFFERENCE, TARGET_INDEPENDENCE_UNKNOWN and PATIENT_IDENTIFIERS_ABSENT warnings. Locked mode must block unknown independence. Exploratory parser eligibility is not permission for any of the scientific uses excluded above.

## Sources and reuse

- GSE42568: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE42568 . Clarke et al., *Correlating transcriptional networks to breast cancer survival: a large-scale coexpression analysis*. Carcinogenesis 34:2300–2308 (2013), PMID 23740839, DOI 10.1093/carcin/bgt208. GEO explicitly links this paper. Full publisher text was inaccessible (HTTP 403); GEO acquisition/processing annotations and PubMed citation were inspected, not an independently reviewed complete source paper.
- GSE20711: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE20711 . Dedeurwaerder et al., *DNA methylation profiling reveals a predominant immune component in breast cancers*. EMBO Molecular Medicine 3:726–741 (2011), PMID 21910250, DOI 10.1002/emmm.201100801, PMCID PMC3377115. Open full text inspected via Europe PMC; GEO supplementary README explicitly defines ER status.
- Rejected GSE29431 publication: Cuadros et al., *Expression profiling of breast tumors based on human epidermal growth factor receptor 2 status defines migration-related genes*. Pathobiology 80:32–40 (2013), PMID 22832278, DOI 10.1159/000339431. Identified via publication search (GEO matrix lacks a PubMed field); only abstract and indexed methods excerpt inspected, not complete publisher text.
- Official download documentation: https://www.ncbi.nlm.nih.gov/geo/info/download.html and https://www.ncbi.nlm.nih.gov/geo/info/geo_paccess.html . Retrieval used HTTPS to listed GEO FTP files, with no raw CEL reprocessing.

GEO provides public bulk downloads, which does not by itself confer a blanket CC0/CC-BY license or prove consent for every downstream purpose. No study-specific data redistribution license was verified; retain submitter attribution, citations and original provenance and review institutional/competition and downstream redistribution requirements before further publication. This package makes no invented permission statement. Source publications and platform annotations can have separate terms; a new software license does not relicense their contents. No raw CELs or controlled-access data are included.
