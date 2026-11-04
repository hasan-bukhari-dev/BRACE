# PASS 01 REPORT — incomplete, blocked checkpoint

## Changes
Added this report only. BRACE_PASS01_v1 is a versioned copy of the supplied current 01_RUN_BRACE; no application, historical evidence, scientific rules or frontend files changed. Original ZIP unchanged. The supplied filename lacks the request's `(1)` suffix; used the explicitly attached path. Pasted roadmap treated as context, not authorization to execute later passes.

## Dataset decision and evidence
Neither cohort is approved for replication. Official GEO sample GSM1045261 (GSE42568) reports GPL570, log2 GC-RMA signals; GSM728614 (GSE29431) reports GPL570, RMA expression values and normal breast tissue from a breast-cancer patient. This is not sufficient evidence of equivalent control biology or processing. Both sample tables report 54,675 probe rows. Matching platforms alone does not establish compatibility.
Sources: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM1045261 and https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM728614 . Series URLs for GSE42568 and GSE29431 returned browser verification challenges in the web reader. No bypass attempted.

## Download and verification status
No expression matrices downloaded or prepared. No downloaded-data hashes, validated sample totals, label counts, publication verification, patient independence audit or redistribution assessment completed. No alternative pairs investigated. This is an incomplete investigation, not proof that no suitable public pair exists. No synthetic replacement supplied.

## Contracts and limitations
Input tables are features by samples, first column feature_id; internal arrays are samples by features. IDs must be unique and values finite. API limit is 25 * 1024 * 1024 bytes per file. Intake separately limits files to 100 MiB, 25,000 features and 500 samples; manifests to 1 MiB. Full GPL570 probe matrices exceed the feature cap regardless of byte size. A future approved preparation needs documented annotation and deterministic gene aggregation or a prespecified feature subset, with exclusions recorded; do not disable limits. Gene mapping has not been performed.
Compatibility checks require matching namespaces, supported measurements and matching microarray platforms. Different processing descriptions produce a warning, not a block. Scientific review must therefore remain stricter than parser eligibility. Locked external evaluation blocks unknown independence; missing patient identifiers cannot establish independence. No contracts rewritten.

## Commands and exact outcomes
From the preserved application:
- python verify_release.py: exit 0, 121/121 files verified.
- python -m pytest -q: exit 1, No module named pytest. No tests collected or passed; prior 151-test claim not independently reproduced here.
- python scripts/release_smoke.py: exit 1, ModuleNotFoundError: No module named fastapi.
Available python resolves to C:\Espressif\tools\idf-python\3.11.2\python.exe. py -0p reports no installed Pythons. Dependencies were not installed in that unrelated interpreter.

## Blockers and readiness
Pass 1 remains incomplete. Need an isolated dependency environment and successful regression/smoke checks; accessible full study metadata and processed matrices; publications, control definitions, independence and preprocessing review; then reproducible preparation, hashes, parser verification and focused integrity tests for a defensible pair. Alternative investigation remains available within the two-pair maximum.
Pass 2 is NOT ready. No RACE implementation or biological replication claims made. This checkpoint is for independent review, not acceptance of Pass 1.
