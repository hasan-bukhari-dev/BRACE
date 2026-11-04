# Implemented task boundaries

The executable source of task descriptions is `brace_app/task_capabilities.json`, exposed read-only at `/api/capabilities`. This describes the existing engines; it does not broaden their intake contracts.

| Task | Required files / labels | Eligible work | Explicit limits |
|---|---|---|---|
| RACE | Six source/target expression, sample metadata and manifest files; explicit equivalent positive/negative biological definitions | Source-only Welch/BH screen, frozen selected family, target tests; contextual measured FACE | Exploratory unpaired processed microarrays with supported biological identifiers. No raw counts, paired/repeated-subject or covariate-adjusted inference. Independence declarations are not authentication. |
| Mode A / ACE | Prediction CSV/TSV plus JSON class/column manifest; known and predicted classes | Classification confusion, supported-class metrics, uncertainty and supplied probability filtering; generic records supported | Optional probabilities must form complete valid vectors for confidence metrics. No organism or expression files required. No regression, raw text/images/audio, executable model or model endpoint. `sample_id` is the internal record key. |
| Mode B / ACE | Six supported expression/metadata/manifest files with normal/tumor classes | Existing source-only binary logistic baseline; source OOF and target scores shown separately | ER_positive/ER_negative public pair is blocked for this baseline. No new original CancerShift training or generic arbitrary classifier fitting. |
| Mode C / CE | Six compatible declared expression/metadata/manifest files | KS/BH, medians/source IQR, source-fitted PCA and target projection | Labels excluded. No phantom target accuracy or causal error explanation. Existing expression/biological identifier contract remains; arbitrary numeric tables are not silently accepted. |
| Historical records | Preserved local CPTAC / GSE2109 artifacts | Read and inspect archived predictions/adaptation comparisons | No new original-classifier inference. No matching GEO expression invented for an archived prediction. |

All API uploads remain limited to **25 MiB per file**. Expression intake remains at **25,000 features and 500 samples per cohort**. Prediction intake remains at **50,000 records**. UI text shows the limits for the selected task.

CE checks eligibility by task rather than assigning unconditional comparability. An ER RACE preflight can pass with caveats while the baseline is blocked. Mode C does not read labels to infer supervised eligibility. Changing task retains selected File objects within the tab, invalidates prior checking, and requires a new check.

Public example eligibility: GSE42568 (101 tumors, 67 ER-positive / 34 negative) → GSE20711 (87 tumors, 42 positive / 45 negative), 10,000 source-selected Entrez representatives. Exploratory within-cohort associations and selected-gene target tests are permitted with limits. Direct absolute expression-scale comparison, source-trained model transfer, authenticated donor independence and clinical validation are **not established**. GC-RMA/RMA, EIA/IHC ER ascertainment and confounding remain documented. Original acquisition, mapping and exclusion records remain in `examples/public_er_pair` without changed bytes.

Two controlled software fixtures, equipment fault classification and text category classification, exercise actual Mode A intake/computation/export. Both have six records, four correct predictions, and two retained at the declared 0.95 cutoff with one correct. They are artificial technical tests, not real field evaluations or biological data.


## V6 task access
Every operation remains accessible through Use my data. Prediction setup has three visible stages; expression has four. Current expression files can be rechecked for RACE, descriptive shifts or baseline eligibility without pretending all tasks are interchangeable: the public ER pair remains blocked for the normal/tumor baseline. SPACE adds official GEO metadata discovery and bounded original-file acquisition only; it neither curates labels nor grants scientific eligibility. Existing API feature/file limits and all engine scopes remain in force. See docs/v6/USER_TASKS.md.
