# Original frontend recovery — 1.1.0-recovery.1

Recovery branch: `reconcile/v6-original-frontend`, based on the exact dev.2 commit
`74dba02fb153e6f883f9c1a25a4c04c60b3be2e1`. Existing branches, tags, releases and
user research data are preserved. This is an unpublished acceptance candidate.

## Source authority and preservation

GitHub refs were checked on November 4, 2026. V6 resolves to
`31e753e0149c1cc688980499a5ed1bbbe612fde9`; original main is
`871472bc6a9be8387930218b4340ba3e10b83006`; dev is `af1181677703fd4469cf1a0e914b4c844eac3ec3`.
The snapshot counts are 1,273 / 263 / 286 / 286 tracked paths respectively.

[File provenance](recovery/file-provenance.csv) records every path across the four
reference trees, its Git blob IDs, final blob ID, ownership and integration decision.
[Summary](recovery/provenance-summary.json) lists every original frontend file that
is byte-identical and every changed frontend file. No dev.2 file is deleted. No
scientific-core file is changed. The inventory is a tree comparison; shallow Git
history does not establish every file's first introduction. Historical material
remains recoverable from the V6 tag; it has not all been copied into the runtime.

## Interface reconciliation

The original homepage, logo, wordmark navigation, five-color system, fonts, ribbons,
scientific views, inspectors and interaction family remain the product authority.
The large additive registry no longer occupies the homepage. It lives inside
**CE → Study datasets · Import, prepare and analyze**, also reachable from the
small **Study datasets** toolbar action. SPACE acquisition opens that same workflow.
The original public rerun action remains in the homepage and existing analysis flows.

Changes from original main:

| Frontend file | Why it differs |
| --- | --- |
| `index.html` | Dataset entry point and disclosure in CE; retained study naming; independent startup; SPACE disabled until ready |
| `app.js` | Dev.2 registry/assay/replay/history/identity integration retained; new dataset navigation event; SPACE initialized independently |
| `js/space.js` | Dev.2 acquisition-to-registry handoff retained; opens the reconciled dataset workflow; enables its button when initialized |
| `v6.css` | Existing dev.2 registry styling and status/context fixes retained; no recovery visual redesign |
| `js/ace.js`, `js/evidence-design.js` | Dev.2 frozen replay rendering and evidence retained |
| `js/cohort-declaration.js` | Dev.2 server-provided assay catalog retained |
| `js/state.js`, `js/study.js` | Dev.2 identity, study naming and schema fixes retained |
| New `js/datasets.js`, `js/replay-view.js` | Entire dev.2 registry, preparation and frozen replay functionality retained |
| New `js/boot.js` | Independent SPACE startup and visible module-loading failure with reload recovery |

The complete byte-identical list is machine-readable in the summary, including
`style.css`, `v4.css`, design tokens, logos, `race.js`, `charts.js`, `trace.js`,
theme, navigation and wordmark modules. Only the server's static asset boundary
changes: JavaScript/CSS MIME types are deterministic and assets use `no-store`.

## Capability preservation

| Capability group | Decision and evidence |
| --- | --- |
| SQLite datasets, immutable versions, SHA-256 assets, original provenance | Preserved dev.2 implementation; dataset workflow regression suite |
| GEO metadata, bounded official acquisition, reviewed/public/general preparation, identifier exclusions and phenotype reconciliation | Preserved; live GEO source workflow exercised separately; preparation regression suite |
| Versioned/named studies, separate study/run identities, history and restart persistence | Preserved; dataset/study/state/frozen workflow tests; browser reload check |
| Task eligibility, preflight, registry-to-analysis handoff | Integrated into original CE; real public registry browser computation |
| Source-frozen RACE, saved predictions, source-only baseline, frozen replay and unlabeled prediction-only reporting | Preserved unchanged engines and dev.2 API/renderers; scientific and workflow regression suite |
| CE distributions, FACE measurements, TRACE calculations, EMBRACE lineage, atomic evidence publication and export hashes | Preserved; original views/renderers, numerical regression, export tests and real browser export |
| Input limits, security validation, Windows packaging and stable research storage | Preserved; original regression suite and separate candidate build |

No capability is intentionally removed or deferred from the implementation.
Unperformed acceptance checks are reported as unverified, not as feature removal.
Scientific interpretation remains conservative: RACE selects up to 20 source
associations after source filtering; replication is exploratory. ACE scores saved
predictions or runs the supported baseline, not arbitrary uploaded models.
Structural eligibility is not clinical validation or proof of donor independence.

## SPACE investigation

The exact published dev.2 portable ZIP was downloaded and its SHA-256 matched
GitHub's published digest:
`74b84fe1be0970b2181dfea15d42ff1149ef0686e84b867e92bbf4ae22147e1c`.
SPACE opened in that binary on this machine without console errors. Therefore the
original installed-app failure is **not reproduced**, and its exact root cause is
unresolved. An earlier local ZIP identifies itself as dev, not dev.2; it was not
used to certify the published dev.2 artifact.

A separate real-browser fault-injection test exposed an early-click failure:
while startup modules load, an enabled SPACE button can receive a click before
its handler is attached. SPACE now remains disabled until its own initialization.
It initializes independently of workbench dependencies, so an unavailable app.js
produces a visible Workbench error while SPACE remains usable. Static asset MIME
and caching hardening protect two additional failure mechanisms; these are not
claimed as the demonstrated cause of the user's installed-app defect.

Live source testing retrieved the official GSE42568 directory, acquired the
21.52 MiB original, registered it with its hash, and followed **Review preparation
in the workbench** into the reconciled CE library. The full network acquisition
path must still be repeated against the recovery binary before full release.

## Reproducible verification

Run with isolated data directories; do not point acceptance tests at existing research.

```
python -m pytest -q --junitxml=.work/recovery/verified-tests.xml
python tools/audit_ui_strings.py
python -m pytest -q tests/test_design3_language.py tests/test_recovery_assets.py
python scripts/run_public_race.py --out .work/recovery/scientific
python scripts/recovery_browser.py --url http://127.0.0.1:8911 --out .work/recovery/browser
python scripts/recovery_inputs.py --url http://127.0.0.1:8911 --out .work/recovery/uploads
python scripts/recovery_inventory.py
```

The initial full regression run produced **337 passed, 1 failed**. The failure is
the required UI source ledger becoming stale after source changes; the ledger is
regenerated and its checks rerun separately. No numerical regression failed.
The final focused audit/startup/distribution retest passed **14 tests**;
its receipt is `recovery/evidence/final-retest.xml`.
The independent public-data calculation selected 20 associations, with 19 matching
directions and 14 target-supported associations. Repeated scientific output files
were byte-identical. Vectorized SciPy reference comparisons passed the existing
`rtol=1e-10`, `atol=1e-12` tolerances. Full measurements are in
`.work/recovery/scientific/verification.json`.

The Windows recovery executable subsequently passed the actual browser public
registry → RACE → navigation → EMBRACE → reload workflow. Its original upload
wizard passed saved-prediction evaluation (explicit equipment-fault test data),
CE distribution analysis and source-only baseline training (explicit synthetic
fixtures). The separate executable verification passed process restart,
registered-data restoration, FACE/TRACE responses, all exported member hashes,
acquisition-ancestor receipts and frozen-baseline replay. Durable receipts are in
`docs/recovery/evidence`.

Browser screenshots and receipts are stored under `.work/recovery/browser`.
Original-home comparison renders exact `main` static bytes against the same real
backend; API responses are not mocked. That establishes static-interface
comparison, not execution of the original V6 binary. The injected missing-app.js
case is labeled fault injection and does not certify a live backend failure.

## Acceptance gates

Final execution results and remaining release blockers are recorded in
[the gate receipt](recovery/gates.json). A gate is never promoted based on a
historical claim. Publication and merge remain blocked until all mandatory gates
pass, including fresh Windows installation/uninstallation and the packaged
acquisition-to-analysis workflow. No existing release is replaced.

| Gate | Status | Verification / evidence | Remaining issue |
| --- | --- | --- | --- |
| 1. Provenance | PASS | Four reference trees and final source; `recovery/file-provenance.csv` | First-ever history beyond shallow boundaries is not asserted |
| 2. Original frontend | PASS | Reviewed equivalent-state 1440/390, light/dark screenshots; `recovery/screenshots` | Exhaustive pixel comparison of every state remains unperformed |
| 3. All development capabilities | BLOCKED | Regression suite and major binary workflows; `recovery/evidence/binary-uploads.json` | Complete browser preparation/reconciliation/replay acceptance |
| 4. SPACE | BLOCKED | Published binary opening, early-click fix, source live acquisition; `recovery/evidence/binary-browser.json` | Exact original installed-app cause unresolved; packaged full live flow remains |
| 5. Scientific integrity | PASS | Independent numerical comparison; `recovery/evidence/scientific.json` | None found in executed checks |
| 6. Whole product | BLOCKED | Actual binary public/prediction/CE/baseline/export/restart checks | Exhaustive control, failure, keyboard and responsive acceptance remains |
| 7. Windows distribution | BLOCKED | Executable, portable and source candidate with checksums | Inno Setup compiler absent; no new installer or fresh install/uninstall acceptance |

**Release recommendation: do not publish or merge as an accepted release.** The
frontend recovery is implemented and its main scientific workflows work in the
actual Windows candidate; the remaining strict release gates stay visible.
