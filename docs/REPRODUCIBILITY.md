# Reproduction and storage

Original public files, download URLs, hashes, source-only feature selection and deterministic preparation are retained under `examples/public_er_pair/`. Its README documents definitions, exclusions and scientific limits.

Run `python examples/public_er_pair/prepare.py` to prepare the public inputs, and `python -m pytest tests/test_public_er_pair.py -q` to verify them. Canonical JSON bytes are preserved on each OS; no new normalization occurs.

EMBRACE exports saved results, methods, warnings, hashes and reproduction guidance. Raw uploads are omitted. Keep matching original inputs to recompute. Extract the evidence ZIP before following its report-relative links.

Desktop storage:

- Windows: `%LOCALAPPDATA%\BRACE`
- macOS: `~/Library/Application Support/BRACE`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/BRACE`

Generated runs and logs remain outside installed resources and survive uninstall. `BRACE_DATA_DIR` changes the desktop data root; `BRACE_RUNS_DIR` explicitly selects run storage. Source `launch.py` defaults to project-local `runs/`.

Bundled examples work offline after dependencies are installed. Initial source setup and uncached SPACE queries need internet. Private files must be reselected after a full browser reload.

`packaging/source-manifest.csv` records current source integrity; `verify_release.py` checks it. Run `scripts/seal_source.py` only after reviewed changes. Git excludes environments, private runs, credentials, caches and build products.
