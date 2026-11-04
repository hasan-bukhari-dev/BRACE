# Prior work and contribution register

**Project:** BRACE — Biological Reliability Assessment across Cohorts and Experiments.

## Prior to the Stage 08 application build

- **CancerShift v1.0.0:** original five-class tissue-of-origin research, TCGA source, GSE2109 exploratory adaptation, GSE103512 and CPTAC-GDC one-shot evaluations. This pre-existing scientific research is **not** hackathon-built.
- **CancerShift research viewer v0.1.0:** prior web-based interactive *historical evidence* viewer. Its visual design motivated BRACE's dark navy/blue/orange palette; the Stage 08 interface is newly implemented rather than copied verbatim from the viewer.
- **BRACE Stage 04–07:** pre-existing tested scientific pipelines for ingestion, source-only baseline fitting, selective metrics, shift analysis. Stage 08 integrates them; do not present their scientific internals as newly invented in Stage 08.

## New in Stage 08

- Unified 4-view user workflow and new frontend implementation.
- Local FastAPI interface delegating to validated scientific engines.
- Guided file import with file-type/size restrictions, clear error messages and starter templates.
- One-click synthetic end-to-end run and integrated historical real-evidence inspection.
- Searchable sample and gene inspection, dynamic confidence thresholds, visual cohort projection and dataset/role distinction.
- Allowlisted provenance exports, random per-run storage, localhost-only launcher, cross-origin write rejection, UI/API integration tests.

## Missing/unevaluated

- Original serialized CancerShift model weights and raw expression matrices were not in the recovered archive.
- Real GEO expression matrices GSE42568/GSE29431 await execution of Stage 03 downloader and numerical verification.
- Public competition rules on prior-work reuse remain unconfirmed. Seek approval and attribute the prior research and software accurately.

This file is a change register, **not** a claim about the organizers' approval or legal ownership of third-party public datasets.
