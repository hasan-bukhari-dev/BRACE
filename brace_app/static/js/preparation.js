import { $, esc } from './ui.js';

// GEO annotations are evidence to review, never inferred scientific eligibility.
export function preparationForm(host, record, preview, task, onPrepare, sourceDataset = null) {
  const metadata = preview.metadata;
  const unique = key => [...new Set((metadata[key] || []).flat().filter(Boolean))];
  const organism = unique('!Sample_organism_ch1');
  const platform = unique('!Sample_platform_id');
  const processing = unique('!Sample_data_processing').join('\n');
  const columns = [...(preview.phenotype_fields || []), ...Object.entries(metadata).flatMap(([key, rows]) =>
    /^!Sample_(title|source_name_ch1|description)$/.test(key) ? rows.filter(row => row.length === preview.sample_ids.length)
      .map((values, index) => ({name: (values[0]?.includes(':') ? values[0].split(':')[0] : key.replace('!Sample_', '')) + (rows.length > 1 ? ` · ${index + 1}` : ''), values})) : [])];
  host.innerHTML = `<h3>Prepare ${esc(record.source.accession || record.name)}</h3>
    <p>${preview.sample_ids.length} samples · ${preview.feature_count.toLocaleString()} features. BRACE will create the expression file, sample metadata and provenance record.</p>
    <form id="guided-preparation">
    <div class="cohort-grid"><div><label for="prep-role">Role in this study</label><select id="prep-role"><option value="source">Source dataset</option><option value="target">Target dataset</option></select></div>
    <div><label for="prep-organism">Organism reported by GEO</label><input id="prep-organism" required value="${esc(organism.length === 1 ? organism[0] : '')}" placeholder="Homo sapiens"></div>
    <div><label for="prep-namespace">Feature identifiers</label><select id="prep-namespace" required><option value="">Choose after reviewing identifiers</option><option value="probe_id">Platform probe IDs</option><option value="gene_symbol">Gene symbols</option><option value="ensembl_gene">Ensembl gene IDs</option><option value="entrez_gene">Entrez gene IDs</option></select><small>Examples: ${esc(preview.feature_preview.slice(0, 5).join(', '))}</small></div>
    <div><label for="prep-platform">Platform</label><input id="prep-platform" value="${esc(platform.length === 1 ? platform[0] : '')}" placeholder="e.g. GPL570"></div>
    <div><label for="prep-scale">Documented measurement scale</label><select id="prep-scale" required><option value="">Review processing below, then choose</option><option value="microarray_log2_normalized">Microarray · normalized log2</option><option value="rnaseq_log2_normalized">RNA-seq · normalized log2</option><option value="rnaseq_vst">RNA-seq · variance-stabilized</option><option value="unknown">Unknown · analysis may be blocked</option><option value="raw_counts">Raw counts · preprocessing required</option></select></div>
    <div><label for="prep-labels">Sample groups</label><select id="prep-labels"><option value="">No groups · CE does not require labels</option>${columns.map((col, i) => `<option value="${i}">${esc(col.name)}</option>`).join('')}</select></div></div>
    <p id="prep-groups" role="status"></p><div id="prep-group-mapping"></div>
    <label for="prep-processing">Processing reported in the original file · review or complete</label><textarea id="prep-processing" rows="4" required>${esc(processing)}</textarea>
    <label for="prep-independence">Patient independence</label><select id="prep-independence"><option value="unknown">Unknown · keep inference restricted</option><option value="independent_documented">Independent patients · documented in study</option><option value="not_independent">Paired, repeated or overlapping patients</option></select>
    <label for="prep-features">Feature preparation</label><select id="prep-features" required><option value="all" ${preview.feature_count > 25000 ? 'disabled' : ''}>Keep all features${preview.feature_count > 25000 ? ' · exceeds limit' : ''}</option><option value="source_variance">Source-only variance · RACE / CE</option><option value="identifier_panel">Fixed identifier panel · baseline-safe subset</option>${sourceDataset ? '<option value="source_features">Use prepared source features · target alignment</option>' : ''}</select>
    <label for="prep-cap">Source preparation feature budget</label><input id="prep-cap" type="number" min="1" max="25000" value="10000"><p class="help">This computational budget defines the screened universe, not a biological optimum. Variance ranks the original source samples without phenotype labels or target data. The retained universe is recorded. For baseline training, the fixed panel ranks only identifier hashes; expression-based selection stays inside training folds. Align the target to the source. No normalization or gene mapping is applied.</p>
    <details><summary>Original annotations and advanced preparation</summary><pre>${esc(JSON.stringify(metadata, null, 2))}</pre><p>The existing JSON editor below supports exclusions, curated feature mappings and reviewed recipes.</p></details>
    <label class="check"><input id="prep-reviewed" type="checkbox" required>I reviewed the scale, processing, identifiers and selected feature policy. BRACE does not normalize values or infer patient independence.</label>
    <p id="prep-error" role="alert"></p><button class="primary" type="submit">Prepare dataset and use in analysis</button></form>`;
  if (task !== 'diagnose_shift') $('#prep-labels').required = true;
  const draftKey='brace-preparation:'+record.id;
  const showGroups = () => {
    const col = columns[Number($('#prep-labels').value)];
    const values = $('#prep-labels').value === '' ? [] : [...new Set(col.values)];
    $('#prep-groups').textContent = values.length ? (task==='train_validate'?'Map the intended normal and tumor groups to those exact class names. Do not relabel unrelated conditions.':'Review two comparison groups. Use equivalent class names across studies; exclude other labels with a reason.') : 'All samples included without phenotype labels. CE does not evaluate prediction accuracy.';
    $('#prep-group-mapping').innerHTML=values.length?`<div class="table-scroll" tabindex="0"><table><thead><tr><th>Recorded group</th><th>Samples</th><th>Analysis class</th><th>Exclusion reason if blank</th></tr></thead><tbody>${values.map((v,i)=>`<tr><td>${esc(v)}</td><td>${col.values.filter(x=>x===v).length}</td><td><input aria-label="Class for ${esc(v)}" data-group-class="${i}" value="${esc(v.includes(':')?v.slice(v.indexOf(':')+1).trim():v)}"></td><td><input aria-label="Exclusion reason for ${esc(v)}" data-group-reason="${i}"></td></tr>`).join('')}</tbody></table></div><details><summary>Review samples</summary><div class="table-scroll" tabindex="0"><table><thead><tr><th>Sample</th><th>Recorded group</th><th>Exclude sample · optional reason</th></tr></thead><tbody>${preview.sample_ids.map((id,i)=>`<tr><td>${esc(id)}</td><td>${esc(col.values[i])}</td><td><input aria-label="Exclude ${esc(id)}" data-sample-exclude="${esc(id)}"></td></tr>`).join('')}</tbody></table></div></details>`:'';
  };
  $('#prep-labels').onchange = showGroups; showGroups();
  const roleChanged=()=>{
    const target=$('#prep-role').value==='target';
    $('#prep-features').querySelector('[value="source_variance"]').disabled=target || task==='train_validate';
    $('#prep-features').querySelector('[value="identifier_panel"]').disabled=target;

    if(target && sourceDataset)$('#prep-features').value='source_features';
    else if(!target && preview.feature_count>25000)$('#prep-features').value=task==='train_validate'?'identifier_panel':'source_variance';
  };
  $('#prep-role').onchange=roleChanged;roleChanged();
  const form=$('#guided-preparation');
  try {const draft=JSON.parse(localStorage.getItem(draftKey)||'null');if(draft){
    for(const [id,v] of Object.entries(draft.fields||{}))if(form.querySelector('#'+id))form.querySelector('#'+id).value=v;
    showGroups();roleChanged();
    for(const [selector,v] of Object.entries(draft.mappings||{})){const el=form.querySelector(selector);if(el)el.value=v}
    $('#prep-reviewed').checked=false;$('#prep-error').textContent='Saved preparation draft restored. Review before preparing.';
  }}catch{}
  form.addEventListener('input',()=>{try{
    const fields=Object.fromEntries([...form.querySelectorAll('[id]')].filter(x=>x.matches('input:not([type="checkbox"]),select,textarea')).map(x=>[x.id,x.value]));
    const mappings=Object.fromEntries([...form.querySelectorAll('[data-group-class],[data-group-reason],[data-sample-exclude]')].map(x=>[x.hasAttribute('data-group-class')?`[data-group-class="${x.dataset.groupClass}"]`:x.hasAttribute('data-group-reason')?`[data-group-reason="${x.dataset.groupReason}"]`:`[data-sample-exclude="${CSS.escape(x.dataset.sampleExclude)}"]`,x.value]));
    localStorage.setItem(draftKey,JSON.stringify({fields,mappings}));
  }catch{}});
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
      const conditions={},excluded={};
      const values=column?[...new Set(column.values)]:[];
      for(const [i,sample] of preview.sample_ids.entries()){
        const group=column?values.indexOf(column.values[i]):-1;
        const label=column?form.querySelector(`[data-group-class="${group}"]`).value.trim():'';
        const reason=column?(form.querySelector(`[data-sample-exclude="${CSS.escape(sample)}"]`).value.trim() || (!label?form.querySelector(`[data-group-reason="${group}"]`).value.trim():'')):'';
        if(column && !label && !reason)throw Error('Give each included group a class, or enter an exclusion reason.');
        if(reason)excluded[sample]=reason;else conditions[sample]=label;
      }
      await onPrepare({schema_version:'1.0.0', name:manifest.cohort_id+' · prepared',
        reviewed:true, manifest, condition_by_sample:conditions,excluded_samples:excluded,
        source_feature_cap:Number(get('cap')),feature_policy:get('features'),feature_reference_dataset:get('features')==='source_features'?sourceDataset:null});
      localStorage.removeItem(draftKey);
    } catch (error) { $('#prep-error').textContent = error.message; button.disabled = false; }
  };
}
