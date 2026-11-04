**Current V4 checkpoint:** see [PRODUCT_ELEVATION_V4_REPORT.md](PRODUCT_ELEVATION_V4_REPORT.md), [current UX/visual rationale](docs/v4/UX_REVIEW.md) and [actual verification ledger](docs/v4/QA_LEDGER.md). The retained material below describes the earlier Design3/Pass7 baseline; it is not a fresh V4 acceptance claim. Human acceptance remains conditional.

# Motion and interaction evidence

Implementation: `wordmark.js` separates committed route from pointer/keyboard preview. Plate geometry is measured from actual glyphs and updated by ResizeObserver, font readiness, resize and theme events. Glyphs do not change position during preview. Current caption has an underline and `aria-current`; prefix muting is supplementary.

| Behavior | Actual verification | Evidence / scope |
|---|---|---|
| Five suffixes, both themes | PASS | Browser measured left/right/top/bottom plate edges against actual suffix glyph bounds; all within one CSS pixel under reduced motion. Glyph x/y did not move during preview. |
| Pointer cancel | PASS | Leaving each theme's home preview restores committed BRACE. No route computation is triggered. |
| Keyboard | PASS | Arrow keys, Home/End, Escape cancel, Enter and Space commit. Native buttons remain in Tab order. |
| Touch | PASS | Emulated touch at 390px commits CE directly; no hover-only dead end. Physical touch device not tested. |
| Interruptions / slower CPU | PASS | 25 rapid previews with Chrome CPU throttled 4x; restored committed route, no page error or numeric animation. This is not a physical low-end-device benchmark. |
| Reduced motion | PASS | Media preference removes plate transitions and home/tool animation; function remains usable. |
| Responsive geometry | PASS | 1280x720, 1440x900, 390x844 and 720x450 reflow checks; allow two animation frames for the measured plate observer after a programmatic viewport change. |
| Theme and state | PASS | System follows emulated OS, explicit preference persists across reload, active result/filter/selection retained. Bootstrap mutation observations check saved dark preference before readiness. |
| Dialogs | PASS | FACE and record inspectors close/return focus; FACE now wraps Tab/Shift+Tab explicitly after audit caught a native-dialog focus escape. |
| Duplicate / interrupted requests | PASS | Duplicate requests guarded by actual busy state. Controlled held request plus reload verifies uncertain outcome, retained previous result and no automatic POST. Controlled delay is not a runtime performance measurement. |

The completed broad browser run is `docs/design3/after/browser_receipt.json`. Final targeted checks and current screenshots are `docs/design3/final/accessibility_receipt.json`. Developer harnesses are included under `tests/` and require a separately installed Playwright/Chrome; these are not application dependencies. Every numerical result in normal tests uses the real local backend. Only error/delay/interruption scenarios intercept requests, explicitly labeled controlled fixtures.

Unverified: real screen-reader announcements, physical touch/low-end device, projector, narrated demo timing and the three human comprehension tests. No full accessibility or human-usability PASS is implied.


## V6 continuity and evidence
Wordmark preview, keyboard focus and committed routes have distinct state. Pointer leave restores the selected suffix. Workspaces and inspectors use short interruptible reveals; scientific numbers and axes do not count up or celebrate significance. Reduced-motion preserves all information. Method sequences are explanatory diagrams, not timed claims about backend progress. Real requests determine busy/completed/failed state. Navigation and native 200% zoom receipts are in docs/v6/. Physical touch and real screen-reader tests remain NOT RUN.
