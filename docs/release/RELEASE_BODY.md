# BRACE 1.2.2

One study workflow now connects SPACE, preparation, analysis and evidence. Prepared datasets can be reused in either role without copying their measurement files. Group review uses key-aligned GEO annotations, editable class mappings, exclusions and saved drafts. ACE accepts unfamiliar prediction-column names through a reviewed mapping form.

Large-data preparation offers source-only variance selection for RACE/CE and a fixed identifier-hash panel for baseline training. Targets align to the exact prepared source IDs. Baseline checks reject source-wide variance selection before cross-validation. Feature budgets, exclusions and original hashes remain recorded.

FACE can resolve arbitrary supported human gene identifiers using NCBI Gene, with dates, source hashes and cached function summaries. The bundled GPL570 mapping covers the whole pinned platform, not just demo genes. Ambiguous probes and unverified identifiers do not receive guessed functions. Internet is needed for uncached reference lookups; measurements and statistics remain available offline.

Studies can be reused, role-swapped, archived and restored. History is no longer silently capped at 50 runs. Local storage usage, private workspace backups (including cached gene references for offline restoration) and side-by-side recorded-run comparison are available under secondary controls.

Newly retrieved gene references refresh the cached evidence ZIP without changing scientific files. The Windows release gate exercises this cache transition, unfamiliar ACE columns, reversed-role analyses and private backups in the actual executable. Its provider fixture is labelled; the separate live reference acceptance remains recorded.

## Verification scope

Real additional-cohort RACE, FACE, TRACE, CE, baseline training, frozen replay and evidence-member hash checks passed; the receipt is in docs/quality/NON_DEMO_ACCEPTANCE.json. This is exploratory, post-hoc research evidence, not clinical or independent prospective validation. The real baseline target has only two normal samples.

**Not fully visually verified:** interactive Windows browser review was blocked by the Computer Use URL safeguard. DOM handlers are tested separately; they do not replace rendered visual or unfamiliar-user acceptance. Cross-platform source and Windows installer receipts are published as assets by the release workflow.

Close BRACE before running the Windows setup executable. The installer is unsigned; original data stay local. Ordinary evidence ZIPs reference but do not include original uploads. Private workspace backups do include original uploads and should be reviewed before sharing.
