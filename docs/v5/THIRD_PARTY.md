# Local interface libraries

The interface makes no CDN requests. Pinned assets are served from `brace_app/static/vendor`; file hashes are in VENDOR_HASHES.json. Python dependencies are unchanged.

- Plotly.js cartesian 3.3.0 — https://cdn.plot.ly/plotly-cartesian-3.3.0.min.js ; MIT, local PLOTLY_LICENSE.txt. Interactive Cartesian figures only. Documentation: https://plotly.com/javascript/plotlyjs-events/ and https://plotly.com/javascript/responsive-fluid-layout/ .
- PapaParse 5.5.3 — https://raw.githubusercontent.com/mholt/PapaParse/5.5.3/papaparse.min.js ; MIT, local PAPAPARSE_LICENSE.txt. Bounded local file previews; authoritative validation remains on the server. Documentation: https://www.papaparse.com/docs .
- Manrope variable font — https://github.com/google/fonts/tree/main/ofl/manrope ; SIL Open Font License, local MANROPE_OFL.txt. Downloaded font bytes and licence are pinned by SHA-256.

Authored UI language is fully inventoried by tools/audit_ui_strings.py. Minified third-party bundle internals are excluded from that literal parser and independently inventoried here. This exclusion does not hide authored labels, error messages, calculation text or backend output.
