import { $, esc } from './ui.js';

// GEO annotations are evidence to review, never inferred scientific eligibility.
export function preparationForm(host, record, preview, task, onPrepare) {
  const metadata = preview.metadata;
  const unique = key => [...new Set((metadata[key] || []).flat().filter(Boolean))];
  const organism = unique('!Sample_organism_ch1');
  const platform = unique('!Sample_platform_id');
  const processing = unique('!Sample_data_processing').join('\n');
  const columns = Object.entries(metadata).flatMap(([key, rows]) =>
    /^!Sample_(title|source_name_ch1|characteristics_ch1|description)$/.test(key) ? rows.filter(row => row.length === preview.sample_ids.length)
      .map((values, index) => ({name: key.replace('!Sample_', '') + (rows.length > 1 ? ` · ${index + 1}` : ''), values})) : []);
  host.innerHTML = `<h3>Prepare ${esc(record.source.accession || record.name)}</h3>
    <p>${preview.sample_ids.length} samples · ${preview.feature_count.toLocaleString()} features. BRACE will create the expression file, sample metadata and provenance record.</p>
    <form id="guided-preparation">
    <div class="cohort-grid"><div><label for="prep-role">Use as</label><select id="prep-role"><option value="source">Source dataset</option><option value="target">Target dataset</option></select></div>
    <div><label for="prep-organism">Organism reported by GEO</label><input id="prep-organism" required value="${esc(organism.length === 1 ? organism[0] : '')}" placeholder="Homo sapiens"></div>
    <div><label for="prep-namespace">Feature identifiers</label><select id="prep-namespace" required><option value="">Choose after reviewing identifiers</option><option value="probe_id">Platform probe IDs</option><option value="gene_symbol">Gene symbols</option><option value="ensembl_gene">Ensembl gene IDs</option><option value="entrez_gene">Entrez gene IDs</option></select><small>Examples: ${esc(preview.feature_preview.slice(0, 5).join(', '))}</small></div>
    <div><label for="prep-platform">Platform</label><input id="prep-platform" value="${esc(platform.length === 1 ? platform[0] : '')}" placeholder="e.g. GPL570"></div>
    <div><label for="prep-scale">Documented measurement scale</label><select id="prep-scale" required><option value="">Review processing below, then choose</option><option value="microarray_log2_normalized">Microarray · normalized log2</option><option value="rnaseq_log2_normalized">RNA-seq · normalized log2</option><option value="rnaseq_vst">RNA-seq · variance-stabilized</option><option value="unknown">Unknown · analysis may be blocked</option><option value="raw_counts">Raw counts · preprocessing required</option></select></div>
    <div><label for="prep-labels">Sample groups</label><select id="prep-labels"><option value="">No groups · CE does not require labels</option>${columns.map((col, i) => `<option value="${i}">${esc(col.name)}</option>`).join('')}</select></div></div>
    <p id="prep-groups" role="status"></p>
    <label for="prep-processing">Processing reported in the original file · review or complete</label><textarea id="prep-processing" rows="4" required>${esc(processing)}</textarea>
    <label for="prep-independence">Patient independence</label><select id="prep-independence"><option value="unknown">Unknown · keep inference restricted</option><option value="independent_documented">Independent patients · documented in study</option><option value="not_independent">Paired, repeated or overlapping patients</option></select>
    <label for="prep-features">Features to retain</label><select id="prep-features" required><option value="all" ${preview.feature_count > 25000 ? 'disabled' : ''}>All original features${preview.feature_count > 25000 ? ' · exceeds 25,000 limit' : ''}</option>${preview.feature_count > 25000 ? '<option value="">Choose a subset policy</option>' : ''}<option value="bounded_original_order">Original-order subset · fits feature and file limits</option></select>
    ${preview.feature_count > 25000 ? '<p>Keeps the largest original-order prefix within 25,000 features and a 24 MiB row-text budget; remaining IDs are recorded as omitted. It is not a representative gene panel. Both cohorts must share IDs; different file orders can reduce overlap. Use advanced preparation for a curated mapping.</p>' : ''}
    <details><summary>Original annotations and advanced preparation</summary><pre>${esc(JSON.stringify(metadata, null, 2))}</pre><p>The existing JSON editor below supports exclusions, curated feature mappings and reviewed recipes.</p></details>
    <label class="check"><input id="prep-reviewed" type="checkbox" required>I reviewed the scale, processing, identifiers and selected feature policy. BRACE does not normalize values or infer patient independence.</label>
    <p id="prep-error" role="alert"></p><button class="primary" type="submit">Prepare dataset and use in analysis</button></form>`;
  if (task !== 'diagnose_shift') $('#prep-labels').required = true;
  const showGroups = () => {
    const col = columns[Number($('#prep-labels').value)];
    const values = $('#prep-labels').value === '' ? [] : [...new Set(col.values)];
    $('#prep-groups').textContent = values.length ? `${values.length} recorded groups: ${values.slice(0, 12).join('; ')}. Values will be preserved exactly; RACE and baseline training need two reviewed classes.` : 'All samples included without phenotype labels. No accuracy or association testing from unlabeled inputs.';
  };
  $('#prep-labels').onchange = showGroups; showGroups();
  $('#guided-preparation').onsubmit = async event => {
    event.preventDefault();
    const button = event.submitter;
    button.disabled = true;
    $('#prep-error').textContent = 'Preparing files and validating the dataset…';
    const get = id => $('#prep-' + id).value.trim();
    const column = get('labels') === '' ? null : columns[Number(get('labels'))];
    const manifest = {schema_version:'1.0.0', cohort_id:record.source.accession || record.name,
      role:get('role'), organism:get('organism'), feature_namespace:get('namespace'),
      measurement_type:get('scale'), processing_description:get('processing'),
      independence_declaration:get('independence'), labels:column ? 'binary' : 'unlabeled'};
    if (get('platform')) manifest.platform = get('platform');
    if (record.source.accession) manifest.accession = record.source.accession;
    try {
      await onPrepare({schema_version:'1.0.0', name:`${manifest.cohort_id} · ${manifest.role}`,
        reviewed:true, manifest, condition_by_sample:Object.fromEntries(preview.sample_ids.map((sample, i) => [sample, column ? column.values[i] : ''])),
        feature_policy:get('features')});
    } catch (error) { $('#prep-error').textContent = error.message; button.disabled = false; }
  };
}
