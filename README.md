# BRACE

**Biological Reliability Assessment across Cohorts and Experiments**

A local research workbench for cross-cohort gene associations, saved-prediction evaluation and reproducible evidence.

[Download Windows app](https://github.com/hasan-bukhari-dev/BRACE/releases/tag/v1.0.0-v6) · [User guide](docs/USER_GUIDE.md) · [Input formats](docs/DATA_GUIDE.md)

![BRACE workbench](docs/images/workbench.png)

## Start

Windows: download the installer, or extract the entire portable ZIP and open `BRACE.exe`. Python is bundled. Keep the controller open while working; **Stop & close** stops its local server.

From source, use standard 64-bit Python 3.11–3.13:

- Windows: `SETUP_BRACE_WINDOWS.bat`, then `START_BRACE_WINDOWS.bat`.
- macOS/Linux: `sh SETUP_BRACE.sh`, then `sh START_BRACE.sh`.

Start with **Open saved public result** to inspect evidence, **Run the public example again** to compute, or **Use my data** for guided inputs.

## Tools

| Tool | Purpose |
|---|---|
| RACE | Select source gene associations, freeze them, then test the same contrast in another study |
| ACE | Evaluate saved predictions or fit the supported source-only baseline |
| FACE / TRACE | Inspect measurements and the recorded calculation |
| Dataset checks | Check task eligibility and describe distribution differences |
| EMBRACE | Export reports, results, methods and hashes |
| SPACE | Find official GEO candidates and verify files; scientific preparation still requires review |

The included GSE42568 → GSE20711 example has 101 / 87 tumors and 20 source-frozen associations. Fourteen have matching direction and target statistical support. It remains exploratory, with processing, phenotype and independence limitations. [Methods](docs/SCIENTIFIC_PROTOCOL_1_0.md) · [Data sources](docs/DATA_SOURCES.md) · [Limits](docs/LIMITATIONS.md).

## Privacy and checks

Computation runs locally on `127.0.0.1`. Bundled examples work offline after installation. Only explicitly submitted public SPACE fields go to NCBI. Private uploads, runs and credentials are excluded from Git. [Storage and reproduction](docs/REPRODUCIBILITY.md).

```sh
python verify_release.py
python -m pytest -q
python scripts/release_smoke.py
```

Windows install, computation, export and uninstall checks passed. Source tests passed on Windows, macOS and Linux; macOS/Linux native installers are not released. This is an unsigned research preview. [Build guide](docs/release/RELEASING.md) · [Remaining acceptance](docs/ACCEPTANCE.md).

## Rights

BRACE-authored material is **rights reserved**. [License](LICENSE) · [Third-party notices](docs/THIRD_PARTY_NOTICES.md) · [Attribution](docs/ATTRIBUTION.md) · [Contributing](.github/CONTRIBUTING.md) · [Security](.github/SECURITY.md).
