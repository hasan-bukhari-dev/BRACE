# BRACE 1.2: consolidation and verification

## Product contract

One study owns the question, selected datasets, assigned roles and runs. Prepared measurement assets stay immutable and reusable. The main path is question → data → review → check → analyze → evidence. Scientific choices remain explicit; mechanical file generation and compatibility checks are automated.

## Audit resolution

| Audit area | Implemented behavior | Evidence |
|---|---|---|
| SPACE handoff | Exact acquired ID and selected task continue into guided preparation | DOM workflow checks; API tests |
| Manual JSON | Common GEO paths use fields, group counts, class mappings and exclusions | Key-aligned phenotype tests and DOM handlers |
| Empty selectors | Acquired entries are visible with a preparation reason and action; prediction imports have their own action | DOM assertions |
| Rigid roles | Runtime manifests bind study roles while preserving original asset bytes and IDs | Reversed-role computation and export test |
| Resource limits | Explicit source-only variance or outcome-blind identifier panel; exact target alignment | Selection-independence, file-limit and alignment tests |
| Task readiness | Preflight remains task-specific; baseline rejects outside-fold variance prefilters | API leakage-guard tests |
| Scattered setup | New-study and question actions select the same registry workflow; file upload is a subordinate import step | Actual modules executed in DOM harness |
| Interpretation | Existing denominators, q-family definitions, processing and independence limits retained; RACE links directly to CE reuse | Existing scientific regressions; source review |
| Gene context | Whole pinned GPL570 mapping plus optional exact human NCBI lookup; ambiguous identities stay unresolved | Live ESR1 lookup in an additional-cohort run; cached/ambiguous tests |
| Repeat work | Reuse, role swap, new-study creation, archiving/restoration, saved drafts and side-by-side run summaries | API and DOM checks |
| History | All saved analyses returned; searchable names and study IDs retained | More-than-50 history regression |
| Storage | Usage and checksum-bearing private backups; no destructive cleanup | Windows backup test with original bytes and SQLite snapshot |
| Reporting | Original-input requirements and private/public export distinction remain explicit | Real-data evidence hash checks |

## Non-demo acceptance

The general preparation API processed the actual GSE21653 original, aligned phenotype fields by key, and created a 5,000-feature source-only variance universe. GSE20711 was aligned to those source IDs. RACE used 263 source and 87 target samples, yielding 20 target-supported matching-direction features from 20 frozen hypotheses. FACE returned measurements for all 20; TRACE and evidence hashes agreed. ESR1 was resolved from probe 205225_at using the whole platform mapping, then NCBI supplied its functional summary. No statistical result depends on this lookup.

CE on those registered inputs retained descriptive measurements and withheld inferential p/q values for different processing. A separate real normal/tumor baseline used GSE42568 and GSE20711 with a 1,000-feature identifier-hash panel; expression values and labels did not select that panel. Frozen application and the resulting exports were exercised. Exact counts, metrics, run IDs and limitations are in quality/NON_DEMO_ACCEPTANCE.json. Cohort choice was post-hoc and target normal support is only two samples; these checks establish execution, not clinical validity or prospective replication.

Reproduce these specific checks from their original gzip files with `python scripts/accept_non_demo.py --er-source GSE21653_series_matrix.txt.gz --normal-source GSE42568_series_matrix.txt.gz --target GSE20711_series_matrix.txt.gz --out NEW_EMPTY_DIRECTORY`. The script verifies the pinned original bytes, uses the general preparation API, and records its actual outcomes. The application itself does not require these accessions.

## Verification limits

The interactive Windows browser check was BLOCKED: Computer Use could not establish the active URL and stopped further UI control. It was not bypassed. DOM checks execute the actual interface modules but do not establish pixel layout, screen-reader support or independent human usability. This release is **not fully visually verified**. Native launcher and installer lifecycle checks are separate automated gates; their actual receipts accompany the GitHub release.

Prepared drafts are saved in local browser storage. Registered data and completed runs persist in the local workspace. Closing a browser does not cancel a computation already accepted by the server; review saved analyses before retrying. No progress percentages or cancellation promises are invented.

No universal assay support, raw-read preprocessing, arbitrary uploaded-model execution or biological mechanism claim is added. Offline statistics work on local inputs; uncached public discovery and gene annotation require internet. Unknown platform probes require a reviewed mapping. Archive hides studies without reclaiming disk space; private backup restore uses a separate empty workspace, preserving the existing one.
