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


## Persistent integration API (schema 1.0.0)

`GET /api/schema` returns the current OpenAPI document, including multipart and JSON request models. `API_SCHEMA.json` is the generated source snapshot. New JSON request models reject extra fields and unknown schema versions. Original multipart clients may omit `schema_version`, which defaults to `1.0.0`. Named analysis/preflight requests accept `name` (at most 200 characters; no controls).

| Endpoint | Contract |
|---|---|
| `GET /api/assays` | Existing processed-measurement adapters, operations, limitations and unimplemented modalities |
| `GET /api/datasets` | Persistent acquired/prepared versions with immutable IDs |
| `GET /api/datasets/{id}` | Exact record and transformation lineage |
| `PATCH /api/datasets/{id}` | `{name}` changes display name without changing version/assets |
| `GET /api/datasets/{id}/assets/{kind}` | Hash-verified local asset; controlled paths only |
| `POST /api/datasets/import` | Multipart `name`, `expression`, `metadata`, `manifest`; validates canonical intake |
| `POST /api/datasets/reviewed-public` | `{reviewed:true}` registers verified bundled originals and pinned ER preparation |
| `GET /api/datasets/{id}/inspect` | Bounded numeric GEO parsing; annotations, lexical identifier hints and review requirements, never eligibility |
| `POST /api/datasets/{id}/prepare` | `name`, `reviewed:true`, `manifest`, complete `condition_by_sample`, optional reasoned `excluded_samples`, one-to-one `feature_mapping` and `mapping_reference` |
| `POST /api/datasets/{id}/transform` | `name`, `reviewed:true`, `role`, complete `condition_mapping` and `biological_definitions`; creates a separate version |
| `GET /api/datasets/{id}/checks` | Saved pair/task/contrast-specific preflight receipts |
| `GET/POST /api/studies` | List/create named studies with exact role-to-dataset ID assignments |
| `GET /api/studies/{id}` | Named study and immutable dataset-version assignments |
| `POST /api/dataset-analysis/preflight` | `{name,mode,datasets:{source:id,target:id},race_config:{...},study_id:null}`; prediction mode instead uses `{predictions:id}` |
| `POST /api/dataset-analysis/run` | Same contract; copies verified assets server-side and delegates to the existing scientific route |
| `POST /api/dataset-analysis/replay` | `{name,frozen_run_id,target_dataset_id}`; only verified existing BRACE source-baseline freezes |
| `GET /api/runs` | Newest 50 by `created_utc`; legacy timestamp source is explicit |
| `GET /api/runs/{id}` | Verifies and reopens exact run; includes study, dataset and cohort identities |

Preparation/dataset JSON requests are bounded to 2 MiB. Uploads and generic acquisitions remain limited to 25 MiB. The reviewed GSE20711 original alone may be exactly 26,895,121 bytes and must match its pinned SHA-256; this is not a configurable general size increase. Foreign-origin writes are rejected. SPACE sends only explicitly submitted public search fields to approved NCBI endpoints. No model binaries or arbitrary remote URLs are accepted.

Errors retain HTTP status and a code/message where applicable: 413 resource violation; 422 invalid/unsupported input or scientific blocker; 409 missing/changed evidence or incompatible saved identity; 404 unavailable record; existing 429/502/503 discovery responses distinguish remote failure. A blocked preparation preserves its original acquisition. Schema/version errors do not silently upgrade a dataset.

The registry record schema includes `schema_version`, immutable `id`, editable `name`, `source`, hashed `assets`, `status`, validated `summary`, preprocessing history, parents and timestamps. Studies have immutable IDs, names, timestamps and role assignments. Runs snapshot study/dataset IDs, original filenames/hashes, parameters and provenance in atomic `run.json` records. Exact scientific contracts remain in the preserved core models. See [dataset workflow](DATASET_WORKFLOW.md).
