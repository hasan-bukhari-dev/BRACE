# Reproducing this evidence

Evidence format: brace-embrace/0.7.1-design3. Extract the ZIP and open research_summary.html without
a server or network. Input hashes, methods and output tables are enclosed.
Original uploaded files are excluded. Obtain the matching originals separately
and verify their SHA-256; this package alone cannot recreate private inputs.
Use the matching BRACE source and dependency versions in analysis_methods.json.
CSV_TEXT_ENCODING.json records reversible spreadsheet-safe text encoding.
Run configuration and declared evaluation role must match; declarations do not
authenticate acquisition or observation independence.

Parse the six source/target expression, metadata and manifest files with
brace_core.intake.parse_cohort, then call brace_core.signature.run(source, target,
the JSON race_config.json contents, a new output directory). The source-only rule
screens the full family and freezes selected IDs before target testing.
Never select features or alter the rule from target outcomes. For the public ER
example, use the checkpoint's actual preparation README, hashes and exclusions.
Source/target processing and phenotype differences remain exploratory limits.

Where computed, uncertainty uses saved Wilson intervals and a1000-replicate
class-stratified row bootstrap, seed20261101. These assume independent rows and
do not correct unknown group/batch dependence. Confidence>=cutoff retains equal
values; a nonreference cutoff viewed after outcomes is exploratory.
Compare numerical artifacts. Software-version changes and random run IDs can
change provenance hashes without changing numerical results. Repeated export of
an unchanged run/version is byte-stable. Verify FILE_SHA256_MANIFEST.csv and
the published-byte hashes, separate from original scientific-source hashes.
