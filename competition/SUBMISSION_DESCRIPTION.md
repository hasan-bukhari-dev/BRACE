# BRACE — Biological Reliability Assessment across Cohorts and Experiments

BRACE is a local Python/FastAPI research workbench for checking whether gene-expression findings and predictive-model results remain supported across cohorts. Its promise is “Discover in one cohort. Test in another.”

The real public example compares recorded ER-positive and ER-negative breast tumors in GSE42568 and GSE20711. RACE selects genes using the source only, saves a frozen hypothesis set, then tests all selected hypotheses in the target. FACE links findings to actual measurements; TRACE exposes the evidence chain; EMBRACE exports a conventional offline HTML/CSV/JSON package with methods, hashes, warnings and full outcomes. ACE evaluates supplied predictions or a source-trained binary baseline and makes confidence/coverage tradeoffs inspectable. Unlabeled cohort shift remains a separate descriptive workflow.

CancerShift is disclosed pre-existing research motivation. Its CPTAC predictions are genuine archived records, rescored without newly executing the unavailable original classifier. The new public ER computation is distinct from that history and from clearly labeled synthetic software examples.

BRACE adds a guided, constrained cross-cohort workflow rather than a new statistical theory or a replacement for R/Bioconductor/Galaxy. Important limits include processing and ER-assay differences, incomplete donor authentication, missing-class/study confounding in historical evidence, and no causal or clinical interpretation. It runs locally without outside network access after dependencies are installed.

Development used AI assistance for code, testing and documentation. Prior code/research and subsequent pass changes are itemized in `DISCLOSURE_REGISTER.md`; official competition-window eligibility and AI/reuse permission remain to be confirmed with organizers. No clinical deployment, completed external user study or organizer permission is claimed.
