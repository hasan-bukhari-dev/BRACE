# SPACE — public discovery boundaries

**Purpose:** help a researcher find and document candidate studies, then inspect actual processed-file availability. SPACE does not turn arbitrary public matrices into automatically approved BRACE inputs.

Stages are **metadata found → filenames verified → original file acquired → manual labels/processing/independence review → deterministic preparation frozen → task-specific intake**. Only the first three are automated here. A two-candidate shortlist exports unresolved scientific checks with `eligible:false`; it never ranks favorable target outcomes.

## Actual connections and files

The search uses official NCBI ESearch/ESummary, database `gds`, GEO Series filter, user-selected organism and assay, and up to six candidates. Human and mouse search are available; current RACE eligibility still requires supported human normalized log2 microarrays. Intended task is recorded for review, not used as a false automatic eligibility verdict.

The matrix directory is actually fetched from `https://ftp.ncbi.nlm.nih.gov/geo/series/.../GSE.../matrix/`. Available names are parsed from that directory. Acquisition accepts only an exact listed Series Matrix gzip name, never an arbitrary URL or filesystem path. An empty listing means no supported matrix was listed; it is not a scientific rejection of that study.

Original-file acquisition is bounded to **25 MiB compressed bytes**. The gzip signature and downloaded SHA-256 are checked; no decompression, full gzip-content validation, phenotype guessing or normalization occurs. Prepared/decompressed inputs must separately meet all intake limits. Reuse and redistribution terms need study/publication review. Public hosting alone is not a licence grant.

## Bounds and privacy

- Only explicit public search fields are transmitted. No access to uploaded matrices, patient metadata or private record labels is part of discovery.
- HTTPS endpoint hosts are restricted to `eutils.ncbi.nlm.nih.gov` and `ftp.ncbi.nlm.nih.gov`; redirects, credentials and custom ports are rejected. Outbound metadata is bounded to 2 MiB, directory responses to 1 MiB, acquired files to 25 MiB, with 12-second connection/read timeout and spacing of at least 0.36 seconds between request starts within one app process.
- Metadata cache: 24 hours, integrity envelope and atomic replacement. The refresh option bypasses it. Acquired original files have a separate local hash-addressed cache. Cache files live under the configured `BRACE_RUNS_DIR/_discovery/`; the release does not ship the extra original acquisition cache.
- Malformed official responses, oversized responses, rate limiting and unavailable network receive distinct failures. Candidate eligibility remains unknown. Closing the dialog does not claim to cancel an already submitted request.

## Verified live evidence

On 2026-11-04 UTC, official search for GSE42568, its actual matrix-directory listing and acquisition returned HTTP 200. The acquired file was `GSE42568_series_matrix.txt.gz`, 22,565,943 bytes, SHA-256 `43b93f72f1d81838dcd2a5b6ccc3bc1875e46230dad0d7346236773a99e32b76`. See [live metadata receipt](integrity/geo-search.json) and [acquisition receipt](integrity/geo-acquisition.json) for original URLs and retrieval times. This is a real original download, not a newly curated cohort or replication result. Unit/failure-injection tests are separate from this live check.

Official reference links: [GEO download guidance](https://www.ncbi.nlm.nih.gov/geo/info/download.html), [E-utilities introduction](https://www.ncbi.nlm.nih.gov/books/NBK25497/), [NCBI policies](https://www.ncbi.nlm.nih.gov/home/about/policies/), [GEO2R guidance and interpretation limits](https://www.ncbi.nlm.nih.gov/geo/info/geo2r.html). Access and remote availability may change; offline examples remain the dependable demonstration path.
