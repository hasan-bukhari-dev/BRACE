# 1.2.3 cleanup ledger

No scientific fixtures or historical result bytes have been removed.

| Candidate | Decision and dependency reason |
|---|---|
| brace_app/static/v4.css | Removed: HTML loads style.css, v6.css and workbench.css; no application, test or scientific consumer references v4.css. Packaging collected the static directory incidentally. Only regenerated string/source inventories referenced it. |
| docs/images/workbench.png | Removed: no tracked consumer except the source inventory; current README uses the authentic manual capture. No evidence artifact or offline demonstration consumes this old screenshot. |
| OPEN_RESEARCH_FINAL.bat | Retained: RESEARCH_FINAL.md explicitly references it as historical local setup |
| stage06/stage07 synthetic reports and evaluation/replay directories | Retained pending full dynamic example traversal and scientific verifier audit |
| cancershift_historical_evaluation | Retained: archived scientific provenance must not be replaced with new inference |
| UI_STRING_LEDGER.csv | Retained: generated verification contract, not ordinary prose |
| DATA_GUIDE.md opening walkthrough | Replaced obsolete button instructions with links to the quick start and new-data guide; format contract retained |
| REPRODUCIBILITY.md | Distinguished historical artifact schema from current product version |

The maintenance parity baseline is release commit 19e2aeb. Scientific changes before that commit remain documented in SCIENTIFIC_CHANGE_REGISTER.json.

DEMO.md and REPRODUCIBILITY_GUIDE.md remain compatibility pointers. Unique reproduction instructions were merged into REPRODUCIBILITY.md. Historical reports retain their original relative paths and explicit history banners. No synthetic or CancerShift evidence directory was removed: tests and runtime example dispatch depend on those preserved assets.
