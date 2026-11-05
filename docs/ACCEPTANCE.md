# Acceptance scope

Current release: 1.2.2. See [consolidation record](RELEASE_1_2.md) and [new-data receipt](quality/NON_DEMO_ACCEPTANCE.json).

Automated release gates cover exact source bytes, the full Python suite, actual DOM handlers, bundled executable calculations, saved-result restart, the native launcher, installation, installed execution and uninstall. The tagged release publishes their actual receipts and the full Windows JUnit report. Passing these gates does not establish human usability or clinical validity.

Interactive Windows visual review is **BLOCKED**: Computer Use could not verify the browser URL and stopped control. It was not bypassed. The release is not fully visually verified. Unfamiliar-user testing, screen-reader review and full WCAG assessment are NOT RUN.

Research scope remains limited to supported processed matrices and prediction tables. Gene lookup is reference information; it neither validates a statistical result nor explains a biological mechanism. Additional cohorts were investigated post-hoc. The real baseline target has only two normal samples; its accuracy is not a clinical performance estimate.

A researcher and a technical user should each attempt an unfamiliar supported dataset without coaching before any claim of independently validated usability. Record wrong turns, task completion and interpretation. No such observations are fabricated here.
