# Portability fixes found by the real GitHub runners

The initial Windows build and installer checks passed. Running the unmodified suite on Ubuntu and macOS exposed genuine portability defects before publication:

1. Preparation used the operating system's default JSON newline. The shipped reference JSON uses CRLF; POSIX regenerated LF and therefore different byte hashes despite identical values. `prepare.write_json` now explicitly uses CRLF on every OS. No existing prepared matrix, metadata, mapping, selected feature, saved result or original test file was rewritten. The original deterministic-preparation regression remains the acceptance check.
2. The launcher recognized Windows/Linux address-in-use numbers, but macOS returns `errno.EADDRINUSE` as 48. It now uses the standard platform constant. The same original occupied-port tests run on macOS, without skipping or weakening them.

`PORTABILITY_PATCH.json` retains both the old and reviewed new hash for the one changed preparation source file. Of the 150 protected baseline core/example/original-test files, 149 remain byte-identical and that one code-only patch is explicitly accounted for. All 15 scientific core files, actual prepared data and all original regression test files remain unchanged. Source/frozen selection, matrices and numerical results are preserved. The independent numerical checker validates this exact declared exception rather than silently replacing the baseline snapshot.

These fixes are packaging/reproducibility maintenance, not a new scientific method or additional biological validation. Current-platform CI and attached release receipts determine support. Native macOS/Linux device acceptance remains separate from source tests and Windows verification.
