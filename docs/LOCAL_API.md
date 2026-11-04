# Local API reference (Stage 08)

BRACE runs on **127.0.0.1:8765**. The server allows only localhost Host values and blocks foreign-browser write origins. It has no external account or cloud connection.

## Read-only endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | Application interface |
| `GET /api/health` | Version, scope and real-data availability flag |
| `GET /api/example/cptac` | Real archived CPTAC predictions and calculated reliability summary |
| `GET /api/example/historical-shift` | Historical GSE2109 adaptation comparison |
| `GET /api/example/synthetic` | Precomputed clearly synthetic source-fitted shift preview |
| `GET /api/templates` | ZIP of test input formats, **synthetic** |
| `GET /api/runs/<run_id>` | Reopen a completed local analysis |
| `GET /api/runs/<run_id>/export/<validation|shift|model>/<allowed_filename>` | Export this run's verified numerical output files |
| `GET /api/example/export/<cptac|shift|historical>/<allowed_filename>` | Export a packaged example file |

## POST analyses

- `POST /api/demo/synthetic` — no body; recomputes a complete synthetic model + external validation + shift example. Results generated under a new `runs/<id>/` folder.
- `POST /api/analyze` — multipart/form-data body, `mode` and required named uploaded files:
  - `mode=evaluate_predictions`: `predictions`, `prediction_manifest`
  - `mode=train_validate`: `source_expression`, `source_metadata`, `source_manifest`, `target_expression`, `target_metadata`, `target_manifest`
  - `mode=diagnose_shift`: same six fields; no outcome labels interpreted.

Upload extensions: `.csv`/`.tsv` for tables; `.json` for manifests; **25 MB per file**. Inputs undergo Stage 04/05 parsing, compatibility and model-data checks before calculation. Rejected input returns HTTP 422 with a specific issue and suggested next action. Endpoints do not accept executable serialized model files.

## Output shape

Runs return `id`, `kind` (`historical`, `synthetic`, or `user_computed`), `name`, `data_label`, `validation` (object or null), `shift` (object or null), `exports`, `notes` and `provenance`.

Provenance declarations are user supplied unless expressly identified as reviewed historical artifacts. Scientific warnings and intervals must be inspected before drawing conclusions. Input files and generated outputs remain locally in `runs/<id>` and are not accessible through arbitrary API filesystem paths.
