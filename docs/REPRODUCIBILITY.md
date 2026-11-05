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

## Integration registry and evidence format

BRACE stores immutable dataset assets and a transactional SQLite registry under the runs directory. Stop the app before backing up the whole directory. Run provenance snapshots include parent acquisition URLs/hashes and transformation history. Shift-only snapshots omit phenotype values/counts recursively. The historical EMBRACE 0.8.0 artifact schema (distinct from the current product version) publishes conventional summary/results/methods/provenance/integrity sections, retaining old paths as compatibility aliases. Original uploads remain excluded; matching assets are still needed to rerun. See [dataset workflow](DATASET_WORKFLOW.md), [architecture](ARCHITECTURE.md) and [acceptance evidence](IMPLEMENTATION_REPORT.md).


## Recompute an analysis

1. Keep the original input files and compare their SHA-256 values with reproducibility_manifest.json. Ordinary EMBRACE exports contain computed outputs, not those original uploads. Private workspace backups include originals and should be kept private.
2. Use the recorded release, dependency versions, seed, model configuration, namespace and processing descriptions. Rerun the same task without changing target outcomes or selecting a favorable cutoff.
3. Compare the frozen model, predictions, metrics, warnings and per-artifact hashes. Matching-version deterministic cases are tested; equality across arbitrary toolchains and hardware is not promised.

Baseline freezes serialize JSON parameters, not executable pickle/joblib objects. CancerShift model checkpoints are not supplied; the archived CPTAC example reproduces scoring of 680 saved predictions, not original inference or expression preprocessing. GSE2109 correction experiments remain historical exploratory context.

The evidence inventory records applicable validation, shift, model, RACE and reference-context artifacts. Read REPRODUCE.md and the actual inventory in each export; historical path aliases are retained where required. Missing true classes remain unevaluated. CE has no classification accuracy. PCA distance does not identify an error cause. Post-hoc threshold selection remains exploratory, and user declarations do not authenticate patient independence.
