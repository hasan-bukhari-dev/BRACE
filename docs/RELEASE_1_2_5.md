# BRACE 1.2.5 source candidate — verification and release handoff

Date: 2026-11-08. Baseline: 59326ae. Branch: feat/workbench-1.2.5.

Decision: CONDITIONAL. The source and interface are prepared for review. This is not a published or fully verified binary release. Main, release tags and published GitHub assets have not been changed.

## Implemented

- Centered B R A C E navigation below the header, enlarged on the workbench and compact on analysis pages.
- Official full names beneath pointer/keyboard previews; committed-page underline remains independent of preview.
- Larger BRACE logo; RACE, ACE and CE question-card monograms.
- Short captions at 320px, wrapping descriptions, keyboard focus and reduced-motion/forced-color styles.
- Existing controls, local routes, saved work, statistical methods and the approved assistant preserved.
- VERSION, README source version and release workflow default advanced to 1.2.5.
- Navigation regression check added to source CI; string inventory and source integrity manifest refreshed.

## Evidence ledger

Environment: Windows, Python 3.12.14 local virtual environment; Node 24.22.1; jsdom 31.0.0. Matching-release Python 3.11.9 and other operating systems remain CI gates.

| Check | Result | Evidence and limit |
|---|---|---|
| Full Python suite | FAIL / environment limitation | 369 passed, 2 failed, 1 dependency deprecation warning; 446.14 seconds. Both failed tests cannot create Windows directory-junction fixtures: New-Item returns Access is denied, before application assertions. Tests were not weakened or skipped. |
| Junction containment checks | BLOCKED | tests/test_embrace.py::test_windows_junction_run_cannot_escape_run_root and ::test_published_directory_junction_cannot_redirect_export require a Windows runner that permits junction creation. |
| Workflow DOM | PASS | node tools/verify_workflow_dom.mjs: preparation mappings/exclusions, independent roles, swap, ACE import and unique IDs. |
| Navigation DOM | PASS | node tools/verify_navigation_dom.mjs: official expansions, preview does not navigate, selection, arrows/End/Escape, retained focus and question labels. |
| Scientific smoke | PASS | scripts/release_smoke.py: historical 680/668, fresh synthetic full computation and reproducibility ZIP verification. |
| Scientific engine preservation | PASS | git diff origin/main -- brace_core is empty; existing scientific-hash regression passed. |
| Assistant preservation | PASS | No changes to demo-assistant.js or assistant.css relative to 59326ae. Rendered shortcut opened breast-to-ovary error, maximum archived score 0.998692106. |
| Rendered interface | PASS | Desktop 1440x1000, narrow 390x844 and 320x800 inspected through the browser. Full EMBRACE expansion wraps. Short 320px captions fit. Light and dark RACE views inspected. No captured browser errors. These are observations, not committed pixel-diff baselines. |
| Keyboard smoke | PASS | Arrow-key focus previews ACE without navigation; End previews EMBRACE; selected-page mark remains distinct. Escape restores selected description. |
| Saved scientific result | PASS | Real RACE example still shows 14/20 target-supported associations. Evidence page retains archived CancerShift 668/680 and report/export links. |
| Final UI / identity regression | PASS | 8 tests passed after the last label changes; 1 dependency deprecation warning. |
| UI wording inventory | PASS | 9,690 inventoried rows across 78 source files; 40 context-reviewed lint findings. Official scientific terminology is retained. |
| Attached Unslop audit | PASS / advisory | Release-body phrase scan: zero hard/soft phrase violations. Structure scanner reports a soft sentence-length-uniformity flag; formal release-note wording retained. Other audit outputs remain in local work/release-125. |
| Source manifest / payload / local links | PASS | 359/359 sealed files verified; 360-file Git payload passed; 104 local references across 35 Markdown sources passed. |
| Actual browser zoom | NOT VERIFIED | Browser shortcut did not change reported scale. 320px reflow is verified; this does not establish 200% zoom acceptance. |
| Screen reader, physical touch, full WCAG | NOT RUN | Keyboard and semantic checks do not establish assistive-technology or full WCAG acceptance. |
| Windows executable, installer, native lifecycle | NOT RUN | Exact-tag CI must build and verify on the specified Python 3.11.9 toolchain before publication. No binary readiness claim. |
| Illustrated manual | Previous edition retained | Existing 1.2.4 illustrated manual is retained with the explicit NAVIGATION_1_2_5 supplement. Screenshots/PDF have not been regenerated for 1.2.5. |

## Merge and publication sequence

1. Publish this branch from an authenticated GitHub session and open a pull request targeting main. The portable Git bundle can transfer the branch to another clone containing origin/main at 7b01ca2.
2. Review the source, interface and explicit test limitations. Require Verify source CI on Windows, Linux and macOS; in particular, both junction tests must pass on a capable runner. Investigate any additional failure before merge.
3. Merge the reviewed branch. Only then create v1.2.5 on the reviewed main commit; do not move an existing tag.
4. Dispatch Build release with tag v1.2.5. Publish only if the workflow's executable, portable/native lifecycle, installer version and install/uninstall gates pass.
5. Regenerate/review the illustrated manual if publishing documentation as a current-interface edition. Until then identify it as the previous edition and include the supplement.

GitHub credential lookup in this session found no usable credential. No branch push, pull request, main merge, tag or release publication was attempted through an unauthenticated write path.

## Authorized merge/release follow-through

The user subsequently authorized merge and release. The version-specific release handoff workflow waits for successful main source CI, verifies the same source commit, creates v1.2.5 only if absent, and dispatches the existing verified Windows release workflow. Its Actions and contents write permissions are limited to that job. The approved interface, assistant and scientific engines are unchanged. Final remote outcomes are reported in the pull request and Actions runs; the local historical evidence above remains the record of pre-publication checks.
