# BRACE quick start

## First result from real public data

1. Launch BRACE. In the workspace, open **Open a real-data demonstration**.
2. Choose **Open ER association example**. This opens saved evidence, not a new computation.
3. In RACE, inspect the frozen 20-feature family and the 14 supported associations. Read the source and target denominators and processing caveats.
4. Select a feature to open FACE measurements. Use **TRACE · Trace result** for the recorded calculation.
5. Open E, **Evidence**, for reports and evidence downloads. Original uploads are not included in an ordinary evidence ZIP.

## Compute with reviewed data

1. Open **Data & analysis**. Choose **Add reviewed public ER datasets** and review the biological declarations.
2. Name your study and select **RACE · gene associations**. Select the source and target prepared versions.
3. Review group equivalence and processing. Choose **Check selected datasets**. Resolve each reported incompatibility before proceeding.
4. Choose **Compute checked analysis**. Reopen the result from **Saved analyses** later.

## Bring your own data

Use SPACE to acquire a supported GEO Series Matrix, then prepare the acquired original. Review organism, platform, normalized scale, phenotype groups and exclusions. A successful download is not yet usable input. Exact labels and comparable measurements need scientific review.

For ACE, expand **Import saved predictions · ACE**. Select the table, map its sample, truth, prediction and optional probability columns, review classes and import. Select the saved predictions in the ACE task, check and compute. This evaluates recorded predictions; it does not execute an uploaded model.

For CE select two prepared expression datasets and **CE · distribution comparison**. Inspect descriptive changes. If processing or dependence prevents inference, p/q values remain withheld.

## Keep and recover work

Use **Use as a new study** before changing a saved experiment, or **Swap source and target** for a new contrast. **Workspace storage & backup** creates a private workspace archive containing original uploads. Restore into a separate empty workspace, following the archive instructions. Browser drafts may require reselecting upload files after reload. Check saved analyses before retrying a calculation interrupted by navigation.

See [new-data instructions](NEW_DATA.md), [input formats](DATA_GUIDE.md), [scientific limitations](LIMITATIONS.md) and [user guide](USER_GUIDE.md). Gene lookups need internet unless cached and must resolve an exact supported human identifier.
