# BRACE 0.9.0 RC1 — Changes from v0.8.0

- Added `brace_app/release09.py`: human-readable cross-mode scientific report and reproducibility manifest.
- Added allowlisted `RESEARCH_PACKAGE.zip` for each successful analysis, with artifact SHA-256, software versions, model settings, study declarations, and warnings; raw user uploads intentionally omitted.
- Added read-only endpoints `/api/runs/{id}/bundle` and `/api/example/bundle/cptac`; separate report downloads added.
- Added archived CPTAC evidence ZIP with explicit historical provenance and file hashes.
- Added 'Complete research evidence ZIP' link in Evidence UI.
- Added Windows online setup, offline wheelhouse preparation/installation, and non-network-surprise launcher.
- Added a release smoke test reproducing CPTAC evidence and generating a new synthetic run.
- Added seven Stage 09 automated tests: packaging integrity, mode semantics, historical data, and export privacy.
- Kept Stage 04–07 scientific algorithm code unchanged. The real GEO expression dataset remains pending.
