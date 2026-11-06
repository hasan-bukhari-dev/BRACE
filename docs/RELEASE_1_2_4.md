# BRACE 1.2.4 — Clarity & Documentation, corrected installer

This release includes the [1.2.3 documentation and usability work](RELEASE_1_2_3.md), with a packaging correction found during final asset inspection. The 1.2.3 executable was correct, but its installer retained a hard-coded 1.2.2 filename and Windows version metadata. Its published tag is preserved and the release is marked prerelease.

VERSION now supplies every installer version field. Compilation fails without it. Source CI compiles the actual Setup directives as a version-only smoke check; release CI verifies the real installer filename and PE file/product fields before install/uninstall testing. This fixes the missed packaging field rather than renaming a binary after building it.

The manual footer, source links, README and release configuration now identify 1.2.4. The interface and scientific engines are unchanged from the verified 1.2.3 source; its 25 authentic screenshots remain accurate. New PDFs are regenerated and checked. Historical screenshots, runs and method identifiers retain their recorded versions.

The documentation map, deletion rationale and scientific parity evidence remain in RELEASE_1_2_3.md and the quality records. Current PDF verification is quality/PDF_VERIFICATION_1_2_4.json. Independent human usability and screen-reader acceptance remain unmeasured. No clinical validity or WCAG compliance claim is added.
