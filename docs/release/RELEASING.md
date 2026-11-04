# Build and release BRACE V6

The repository is `https://github.com/hasan-bukhari-dev/BRACE`. BRACE-authored material is rights reserved; datasets and dependencies retain their own terms. Do not label the project MIT/open source or claim blanket data redistribution permissions.

## Source checks

Use standard 64-bit CPython 3.11.9 for a matching build, in an isolated virtual environment. Run `python -m pip install -r requirements-release.txt -r requirements-build.txt`. Keep native Tk support: the minimal NuGet runtime used for earlier engine tests lacks Tk and must not be used to freeze the native launcher.

Run `python -m pytest -q`, `python scripts/release_smoke.py`, `python verify_release.py` and `python scripts/check_repository.py`. The latter checks Git's exact payload, not private untracked runs. Core hashes remain in `docs/quality/BASELINE_CODE_SHA256.json`; public-data hashes remain with the example.

## Build the actual app

`python packaging/build.py` runs pinned PyInstaller on the current OS, records available Python/dependency licences and produces a complete portable ZIP. It includes actual examples, static assets, declarations and integrity reference records. It excludes private runs, environment files, browser profiles and the developer environment.

Use `python scripts/check_distribution.py dist/BRACE/BRACE.exe` on Windows, `dist/BRACE/BRACE` on Linux, or `dist/BRACE.app/Contents/MacOS/BRACE` on macOS. This launches the actual executable from an unrelated working directory without project Python environment paths, performs a real synthetic compute and verifies the resulting evidence ZIP. It also checks the public/historical examples. It is not physical GUI or independent human scientific validation.

The controller's `--launcher-self-test` creates a real native window, waits for the server, then closes it safely and writes a receipt into `BRACE_DATA_DIR`. Use an isolated scratch folder and `BRACE_NO_BROWSER=1` in automation. `--headless` runs the same bundled server without the controller. Neither changes the computation.

On Windows, Inno Setup 6 compiles `packaging/windows.iss`. Install is per user without administrator privileges; run data are outside the installed resources and are not removed on uninstall. The release workflow tests install, the installed executable and uninstall in the build runner. Inspect the controller and installer on a real target laptop before broad distribution.

## GitHub workflow

1. Commit only the reviewed source payload. `.gitattributes` disables automatic newline conversion so pinned historical evidence retains exact bytes. Never commit `.venv`, `runs`, local credentials or build products.
2. `Verify source` runs the actual regression and smoke suite on Windows, Ubuntu and macOS. Wait for actual results; a workflow file is not evidence that its jobs passed.
3. Tag the reviewed commit `v1.0.0-v6` and push that tag.
4. Dispatch `Build release` for the tag. The default builds Windows only. The optional `all` builds each platform on its own runner and verifies the bundled backend separately. Mac/Linux are experimental until their native GUI/device acceptance is completed.
5. The workflow creates a **draft prerelease** only after its build checks pass, attaching actual binaries, receipts, checksums and the tagged source ZIP. Review the concrete result before publication. Never repoint a published tag to quietly replace a failed release.

Initial binaries are unsigned unless an actual signing process is configured and verified. Do not claim Windows code signing, Apple notarization or universal OS compatibility. A checksum detects changed bytes; it is not a vendor signature. Source/data runtime remains the preserved local Python/FastAPI workbench.

## Reproducibility and review

`python scripts/seal_source.py` regenerates the source release inventories intentionally. Run it after final documentation/evidence changes and before committing; do not regenerate an inventory to bless unexplained changed scientific files. Release verification receipts stay outside their own hash inventory to avoid circular hashes.

Dependencies are pinned by version, but binary bit-for-bit reproducibility across runners, timestamps and toolchains is not claimed. Record the exact tagged commit, package hashes, platform, Python and installed dependency licence metadata for each release.
