# Third-party software and assets

BRACE's rights-reserved notice covers only BRACE-authored material. It does not replace any third-party licence. The project reuses pre-existing research and code as described in [the disclosure register](competition/DISCLOSURE_REGISTER.md).

| Component | Notice / source |
|---|---|
| Plotly.js cartesian 3.3.0 | MIT; [included licence](brace_app/static/vendor/PLOTLY_LICENSE.txt), [original distribution](https://cdn.plot.ly/plotly-cartesian-3.3.0.min.js) |
| PapaParse 5.5.3 | MIT; [included licence](brace_app/static/vendor/PAPAPARSE_LICENSE.txt), [upstream](https://github.com/mholt/PapaParse) |
| Manrope variable font | SIL Open Font License; [included terms](brace_app/static/vendor/MANROPE_OFL.txt), [upstream](https://github.com/google/fonts/tree/main/ofl/manrope) |
| CPython and Python dependencies | Versions in `requirements-release.txt`; bundled distributions include the actual Python licence and available installed-distribution licence files under `_internal/distribution-notices/` (inside the app resources on macOS) |
| PyInstaller and its bootloader | Build tool; actual installed notices accompany binary builds. PyInstaller's licensing exception and upstream licence govern its bootloader; BRACE does not relicense it |
| Public research data, platform annotation and publication material | Separate ownership and study-specific considerations; see [DATA_SOURCES.md](DATA_SOURCES.md) and original provenance |

The binary build records `BUILD_ENVIRONMENT.json`, including dependency versions, declared licence metadata and paths to copied notices. This is an installed build-environment inventory, not a claim that every installed package is imported into the executable. Source package notices and the original vendored bytes are retained.

No inference of a blanket public-domain, CC0 or CC-BY licence is made for research data simply because it is publicly accessible. No organizer approval, complete human scientific review or unrestricted redistribution permission is invented.
