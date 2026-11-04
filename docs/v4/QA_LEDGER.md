# V4 verification ledger

Decision: **CONDITIONAL** for product acceptance. Engineering checks below passed; no human acceptance was fabricated.

| Actual check | Outcome | Evidence |
|---|---|---|
| Final full pytest in clean delivery folder |265 passed,0 failed,0 skipped;1 existing Starlette/httpx deprecation warning;136.66s | `final_pytest.txt`, `final_pytest.xml` |
| Initial implementation pytest |265 passed;1 same warning;105.13s | `pytest.txt`, `pytest.xml` |
| Final source-language/preservation gate after refinements |4 passed,0 failed;1.01s | `language_tests.txt` |
| Scientific release smoke |historical680/668; new synthetic computation and reproducibility ZIP PASS | `release_smoke.txt` |
| Independent public numerical reconciliation |101/87 tumors;10,000 source-screened;20 frozen;14/5/1. Maximum difference5.33e-15 | `NUMERICAL_PRESERVATION.json` |
| Baseline preservation |All protected engine/example/original test files byte-identical; complete hashes recorded | `BASELINE_PROTECTED_FILES.json` |
| Rendered text and necessary control contrast |26 populated/empty/dialog states, both themes;5912 text instances; no measured text failures | `review/focused_receipt.json` |
| Browser accessibility tree |Names for visible controls; no duplicateIDs in audited states | same receipt |
| Native200% Chrome zoom |9 screen states × both themes, actual devicePixelRatio2, visualViewport.scale1, layout width711 vs outer1440; no page overflow | `review/native_zoom_receipt.json` |
| Reduced motion, keyboard, forced colors, 390px touch emulation, 4×CPU previews |PASS for enumerated scenarios | browser receipts |
| Two unfamiliar users, no coaching |**NOT RUN** | No participants or answers invented |
| Native screen reader, physical touch, projector/event machine |**NOT RUN** | Automation is not those checks |

The contrast audit measures rendered text against composited ancestor fills, including the actual wordmark plate. Required normal/large-text ratios 4.5/3 were met in measured states. It initially flagged low-contrast decorative row dividers on the exact home-task, gene-row and TRACE-step patterns. They are identified by text, underline/arrow, selected state and keyboard focus; their separators are not necessary control boundaries. Each exception remains recorded as `reviewed_decorative_rules`, rather than claiming every decorative line meets3:1. Necessary input/button boundaries were checked separately. This is not a full WCAG certification.

Browser receipts (assertion counts are local checks, not a usability score):

| Receipt | Passed assertions | Status |
|---|---:|---|
| `docs/v4/after/browser_receipt.json` | 72 | PASS |
| `docs/v4/review/focused_receipt.json` | 98 | PASS |
| `docs/v4/review/last_receipt.json` | 40 | PASS |
| `docs/v4/review/native_zoom_receipt.json` | 20 | PASS |
| `docs/v4/review/bins_receipt.json` | 2 | PASS |

Captured screenshots: {"before": 28, "comparison": 28, "after": 60, "review": 112}. `before/` is the unchanged verified baseline; `comparison/` repeats the same7 primary scenarios at1280×720 and1440×900 in both themes. ACE comparison uses the historical reference .95 in both versions. Public RACE/FACE uses the same saved study and gene135112. CE comparison uses the same artificial demonstration. `after/` contains broad workflow captures and controlled errors; `review/` includes further refinements, guided imports, true zoom and narrow states. Use the gallery and inspect original images at full size; screenshots alone do not prove numerical correctness. Automated tests checked chart values separately.

Commands executed from the app/workspace with isolated interpreters:

```
python -m pytest -q --junitxml=docs/v4/pytest.xml
python scripts/release_smoke.py
python -m pytest -q tests/test_design3_language.py
python work/v4_acceptance.py
python work/v4_focused.py
python work/v4_last_checks.py
python work/v4_zoom.py
python work/v4_bins_check.py
python work/v4_numerical.py
```

Python 3.11.9x64 (NumPy 2.4.6, SciPy 1.17.1); actual production `launch.py` at127.0.0.1:8766; baseline at8767. Playwright 1.64.1 and Chrome 156.0.8078.80 in a separate developer environment. `BRACE_RUNS_DIR` isolated QA output. Original raw GEO inputs and all prepared matrices were present for the 265-test run. The last4-test gate covers source changes after the full run; later large-input legend checks are in `bins_receipt.json`. No unrelated Python installation changed. Reproduction harnesses are in `scripts/qa_v4/`, with their environment instructions.

Known operational limits:25 MiB per API file,25,000 features,500 samples/cohort,50,000 prediction rows remain unchanged. Saved-run index exposes at most50 generated runs. Browser reload during a request reports unknown outcome and does not automatically resubmit; it does not cancel an already-running server calculation. File selection must be restored after reload. Other operating systems/browser engines and a new clean machine were not tested this pass.

The included portable acceptance harness was also executed from the clean delivery folder:72 assertions passed, no page errors or unexpected HTTP errors. Its receipt is `portable_harness_check.json`; its duplicate captures remain in the isolated test workspace. The final full pytest run above includes every current source change.

Final geometry gate: all 40 public paired-effect marks align with their numerical axis in 8 theme/viewport combinations (maximum screen-coordinate discrepancy 1.14e-13 pixels). Both end labels are centered on their coordinates; source and target SVGs share the axis viewport height. The empty selected-gene trace recovery action was also exercised: 9 checks passed in `review/geometry_receipt.json`. The final 265-test delivery run was repeated after this repair and passed in 136.66s. Offline gallery: all 228 screenshot links load and its comparison filter works (`gallery_check.json`).
