# V5 current interface

Warm ivory and navy, the interlocking BRACE ribbon symbol, Manrope typography, blue/jade/iris/coral/brass tool accents. Five named letter tabs remain fixed and predictable. Independently defined dark tokens preserve scientific colour meaning; outcomes also use words, arrows or shapes.

Core source: brace_app/static/design-tokens.css and style.css. Interaction: immediate selected-gene feedback, linked measured plots, bounded file previews, four-stage setup, native dialogs, retained-input error recovery, saved analysis history. Motion respects reduced-motion; controls and forms support keyboard use. Details disclose expert statistics rather than duplicating them in the first view.

All scientific chart values come from real backend records. Plotly handles hover, zoom and PNG export; exact tables remain available. The evidence preview is the exact audited export document, so its paper-white appearance is preserved in both app themes. No account button or unsupported model execution is shown.

See docs/v5/PRODUCT_CONTRACT.md, DATA_GUIDE.md, THIRD_PARTY.md and SCREEN_REVIEW.html. Previous design system history follows.

---

**Current V4 checkpoint:** see [PRODUCT_ELEVATION_V4_REPORT.md](PRODUCT_ELEVATION_V4_REPORT.md), [current UX/visual rationale](docs/v4/UX_REVIEW.md) and [actual verification ledger](docs/v4/QA_LEDGER.md). The retained material below describes the earlier Design3/Pass7 baseline; it is not a fresh V4 acceptance claim. Human acceptance remains conditional.

# BRACE Product Design 3

The interface is a quiet entry canvas that becomes a dense evidence workbench when real data are loaded. The five colored letters are the only primary navigation. Each has a permanent plain task caption: Studies, Genes, Predictions, Datasets, Evidence. No sidebar or second tool bar competes with the wordmark.

| Element | Decision | Reason / implementation |
|---|---|---|
| Identity | B cobalt, R jade, A iris, C coral, E ochre | Five recognizable hue families, separate from scientific result colors. `design-tokens.css` contains both themes. |
| Selection | Measured suffix plate and underlined committed caption | B surrounds BRACE; R RACE; A ACE; C CE; E E. Prefix letters become neutral. `aria-current=page` and text underline give a non-color indication. |
| Type | Offline Segoe UI Variable / Segoe UI / Arial | One UI family, tabular numerals; Consolas only for hashes, code and provenance. No downloaded font. |
| Density | 15px body, 13px table/help, 27px operational heading | Tables retain scientific detail. At narrow widths, local table scrolling preserves complete columns. |
| Home | Large wordmark, one exact purpose sentence, two real actions | Public expression example or own data. Historical and artificial software examples are secondary disclosures. |
| Operational canvas | Compact sticky wordmark, slim current-analysis identity | Results lead; source/target identity and provenance remain reachable. No animated numbers. |
| Detail | Native central FACE / record dialogs | One inspector at a time; Escape, contained Tab/Shift+Tab, and return to the originating selection. Source and target measurements keep separate axes. |
| Themes | System default, Light and Dark | Synchronous head script applies saved/OS choice before CSS; preference in localStorage, run/draft state independent. |
| Controls | 42px main control height, explicit focus outline | Individual wordmark buttons remain independently accessible. Borders use a separate contrast token; quiet table dividers are not control boundaries. |
| Motion | 200ms suffix plate; 260ms home/tool continuity | Pointer preview moves only the plate/colors/purpose. Commit navigates. Motion is interruptible, absent under reduced motion. |
| Scientific colors | Supported, inconclusive, opposite, unavailable; source and target | Actual labels/counts accompany outcome colors. PCA uses source circles and target squares. Brand hue never certifies evidence. |
| Report | Result-first light document, print stylesheet | Separate from app theme; exact tables and local artifact links follow the conclusion and limitations. |

State is separated into committed route, temporary pointer/keyboard preview, draft File objects, current run, per-run selections/filters, dialog state and theme. Home, preview and theme changes do not clear an analysis. A refresh restores saved results and small UI state; browser File objects must be reselected. An interrupted request is explicitly uncertain and is never automatically submitted again.

Accessibility evidence is bounded: Chrome accessibility-tree names, keyboard/touch/focus/reduced-motion checks, rendered contrast and responsive checks are recorded. These are not full WCAG certification or a screen-reader/user study. Native desktop browser zoom and physical projector acceptance remain separate from viewport reflow and page magnification.


## V6 approved refinement
Preserve V5 typography, interlock mark, warm surfaces, instrument colors and real Plotly charts. The header now previews fixed BRACE suffixes separately from committed selection; contextual FACE/TRACE/EMBRACE/SPACE retain plain task labels. The canonical expansion is Biological Reliability Assessment across Cohorts and Experiments. A compact expandable operation receipt replaces repeated context prose. Class-only results promote supported metrics, while dense tables scroll within readable widths. See docs/v6/SCREEN_REVIEW.html for actual V5/V6 comparisons, not concept images.
