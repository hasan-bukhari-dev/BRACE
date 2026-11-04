# Verification ledger — BRACE Pass 5

**Project/revision:** BRACE_PASS05_v1, based on approved Pass 4. 2026-11-03.

**Environment:** Windows; isolated Python 3.11 environment; Chrome 156.0.8078.74; developer-only Playwright 1.64.1; native FastAPI/JavaScript application.

**Review scope:** ACE model/score results, exact confidence exploration, contextual RACE/ACE TRACE, preserved Mode A/B/C and RACE/FACE.

**Critical user task:** inspect an actual archived error → explore a cutoff → trace that same selected result to stored scientific evidence.

**Authoritative evidence:** unchanged Stage 05/06/07 outputs and actual prediction rows; pinned historical/public files; checked completed-run artifact inventories.

| Check | Executed command / action | Observed outcome / evidence | Status | Next action |
|---|---|---|---|---|
| Build/launch | Python compile; uvicorn on spare loopback port | Successful imports/launch and real Chrome application loading | PASS | None for this scope |
| Primary journey | `tests/browser_pass05.py` | 15 scenarios; `PASS05_BROWSER_RESULTS.json`; real archived error/threshold/TRACE | PASS | Independent review |
| Failure/retry | Injected sample fetch error, retry; delayed competing selections | Old scores cleared; checked recovery; newest selection retained | PASS | None |
| Export/persistence/provenance | Download artifact; navigation/reload; API hash checks | Exact selected run/sample retained; downloaded JSON matches; actual snapshots in `pass05_evidence/` | PASS | None |
| Keyboard/focus | Enter, Escape, Tab, slider Home/End/reset; reduced motion | Focus returns to selected row; modal focus retained; operating-point values update | PASS | None |
| Assistive-technology software | Screen reader | Not performed | NOT RUN | Test on target accessibility setup |
| Visual normal/empty/dense | Opened real screenshots; reviewed against retained baseline | 13 screenshots include reference/exploratory/empty confidence, error, source/target and trace | PASS | Independent visual review |
| Viewports/theme/reflow | Dark theme at 1440×900,1280×720,390×844; legacy reflow | No page overflow; local table/chart scrolling where required | PASS | Projector and other engines unverified |
| Scientific regression/leakage | `python -m pytest -q` | 211 passed, 1 existing deprecation warning, 63.78 s | PASS | None |
| Focused linkage | `tests/test_evidence_api.py` | 12 passed; exact row/curve/support reconciliation; corrupt evidence blocked; Mode C labels excluded | PASS | None |
| Prior workflows | Browser Pass 3 + Pass 4 scripts | 20 + 11 scenarios passed; preserved receipts named under Pass 5 | PASS | None |
| Scientific smoke | `scripts/release_smoke.py` | Historical680/668; actual synthetic model/shift and research ZIP passed | PASS | None |
| Performance observations | Two automated threshold fill/check actions | 19.68 and17.61ms round trips; raw values in browser receipt | PASS for observations only | No benchmark/general usability claim |
| Startup/memory/unfamiliar users | Controlled measurements | Not performed | NOT RUN | Measure on demo hardware later |
| Clean-device release path | Cold install/offline/projector | Not performed; existing launch scripts retained | NOT RUN | Target-device verification later |
| Packaging | Release SHA inventory; ZIP CRC; every recorded SHA; nested evidence manifests | Exact count in report packaging receipt | PASS | Independent extraction/review |

**Unresolved blockers/majors:** None known for the tested Pass 5 workflow. Scientific interpretation is limited as stated in the report; acquisition/independence, clinical calibration and prospective policy validation are not established.

**Snapshot changes reviewed by:** Codex internal rendered-image review. No human participant or unfamiliar-user test is claimed. Prior-pass images/receipts are preserved rather than overwritten as new historical evidence.

**Release disposition:** PASS for implemented/tested scope, with explicit unverified device/accessibility/user-study boundaries. No production-readiness or clinical-validation claim.
