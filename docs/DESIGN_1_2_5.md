# BRACE 1.2.5 interface contract

Baseline: 59326ae, with the approved assistant and its CancerShift fix retained.

The interface is precise, approachable and restrained. The core task is to prepare compatible inputs, compute or open a recorded analysis, inspect the result and export its evidence. Newcomers get task descriptions and full tool names; experienced users retain dense tables, parameters, saved work and direct links.

Use the existing Manrope font, semantic color tokens, numerical formatting, theme preferences and local assets. Do not recolor scientific outcomes to match navigation. Preserve all existing controls and backend routes. No framework or runtime dependency is added.

The shared navigation is defined in navigation.css. It follows the header, has a 900px maximum width, and uses five equal destinations. Workbench letters are 52px on desktop; analysis letters are 32px. At narrow widths, captions wrap and the full-name region grows to fit EMBRACE. The rectangle previews tool suffixes; an independent underline marks the committed page. Preview does not navigate or trigger live-region chatter. The only navigation motion is the existing short rectangle transition, disabled by reduced-motion preference. Whole-module page-transition scaling is removed.

The logo and question-card monograms are enlarged in place. RACE, ACE and CE replace the question cards' single-letter monograms. Other controls, scientific content and the assistant retain their approved behavior.

The four historical stylesheet layers remain for unchanged scientific views. Header, navigation and monogram refinements have one narrowly scoped owner in navigation.css, loaded last. A broad rewrite of those layers is outside this patch.

Acceptance includes desktop and narrow rendered checks, light/dark themes, full-name preview and selected-state separation, keyboard navigation, deep-link/history preservation, unchanged scientific-engine hashes, and existing workflow tests. Automated checks are not a substitute for human usability or screen-reader acceptance.
