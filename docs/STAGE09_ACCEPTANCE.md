# Stage 09 — Release acceptance ledger

**Release:** BRACE 0.9.0 RC1 (candidate for Hatchathon bio.exe)  
**Date:** November 2, 2026  
**Standard:** Pass core scientific regression + archived evidence + synthetic computation + complete provenance + offline runtime *after dependencies are installed*.

## Automated tests and evidence

| Check | Result | Meaning |
|---|---|---|
| Inherited Stage 04–08 tests | 144 passing | Input contracts, source-trained baseline, external reliability, shift, API/security |
| Stage 09 export and science tests | 7 passing | Bundle integrity, privacy exclusions, historical CPTAC evidence, Mode C semantics |
| **All automated pytest tests** | **151 passed** | Linux development environment, no Windows guarantee |
| New synthetic end-to-end run | Passed | Live computation on artificial measurements |
| Archived CPTAC evidence | 680 rows / 668 correct | Real historical prediction records; no original inference replay |
| Frozen 0.95 reference | 584 retained / 583 correct | Recomputed from archived evidence |
| Reproducibility manifest | Verified | Hashes, dependency versions, model parameters, warning codes |
| Research package ZIP | Verified | All allowlisted numerical artifacts; original uploaded files excluded |
| Windows setup scripts | Implemented | Actual Windows execution unverified |
| Real GEO expression demonstration | **Not passed** | Stage 03 real matrices could not be retrieved |
| Browser visual and projector acceptance | **Not passed** | Managed Chromium blocks graphical navigation |
| Organizer pre-existing-code permission | **Unconfirmed** | Requires organizer confirmation |

## Technical release verification

- Run `python -m pytest -q`, `python scripts/release_smoke.py` and `python verify_release.py` from the extracted folder.
- Stage 09 clean-extraction and localhost HTTP checks are documented in accompanying execution log (`docs/STAGE09_TEST_RESULTS.json`) once the archive is assembled.
- An installation is **not** internet-independent from a bare Windows machine unless compatible Python and dependencies or prepared wheels are available beforehand.

## Completion verdict

**Scientific reporting, packaging implementation, and automated regression: complete.**  
**Full Stage 09 clean-Windows acceptance: pending,** because no Windows machine test or verified real GEO expression example has been performed in this environment. The release must be independently operated on the actual demo laptop before calling it event-ready.
