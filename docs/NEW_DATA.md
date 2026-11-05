# Run CE on public data

1. Open **Data & analysis** and choose **CE · distribution comparison**.
2. Select **Discover datasets in SPACE**. Enter a GSE accession and check its files.
3. Acquire the matrix, then choose **Prepare this dataset for analysis**.
4. Review the ordinary preparation fields. Organism, platform and processing text come from the file. Confirm the documented measurement scale and identifiers. CE does not need phenotype groups.
5. Choose an explicit subset policy if the original exceeds the feature or file limits. The original-order subset is exploratory; omitted IDs remain in the record. No values are normalized or rounded.
6. Prepare the dataset. It is selected automatically. Repeat for the target cohort; review the target role.
7. Once both are selected, CE checks the pair. Review warnings and choose **Compute checked analysis**. Results and provenance are saved.

GSE42568 and GSE20711 were exercised through this general workflow. The complete original populations and probe subsets differ from the curated ER demonstration. Do not equate their results.

For RACE or baseline training, choose the relevant task and a reviewed phenotype annotation during preparation. Two biologically suitable classes are required; BRACE does not invent normal/tumor labels. Advanced preparation supports exclusions and feature mappings. A GEO accession alone never guarantees task eligibility. Raw read processing and arbitrary model training are outside the supported workflow.
