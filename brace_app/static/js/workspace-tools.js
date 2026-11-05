import { $, esc } from './ui.js';
import { request } from './api.js';

export function initWorkspaceTools(host, refresh, message) {
  host.insertAdjacentHTML('beforeend', `<details id="prediction-import"><summary>Import saved predictions · ACE</summary><p>Map your CSV/TSV columns. BRACE evaluates recorded predictions; it does not execute the model.</p><label for="prediction-table">Prediction table</label><input id="prediction-table" type="file" accept=".csv,.tsv"><button id="prediction-preview" type="button">Read columns</button><div id="prediction-mapping"></div><p id="prediction-import-status" role="status"></p></details>
    <details><summary>Compare saved analyses</summary><div class="cohort-grid"><div><label for="compare-left">First analysis</label><select id="compare-left"></select></div><div><label for="compare-right">Second analysis</label><select id="compare-right"></select></div></div><button type="button" id="compare-analyses">Compare recorded results</button><div id="comparison-result" role="status"></div></details>
    <details><summary>Workspace storage & backup</summary><button type="button" id="storage-check">Show storage usage</button><div id="storage-usage" role="status"></div><p>Private backups include original uploads. Keep them local or share only after reviewing their contents. Existing data are never deleted here.</p><button type="button" id="workspace-backup">Create private backup</button><div id="backup-status" role="status"></div></details>`);
  $('#prediction-preview').onclick=async()=>{
    const file=$('#prediction-table').files[0],out=$('#prediction-import-status');
    if(!file){out.textContent='Choose a CSV or TSV prediction table.';return}
    const data=new FormData();data.set('table',file);out.textContent='Reading columns and class values…';
    try {
      const preview=await request('/api/predictions/inspect',{method:'POST',body:data});
      const options=preview.headers.map(h=>`<option>${esc(h)}</option>`).join('');
      $('#prediction-mapping').innerHTML=`<p>${preview.count.toLocaleString()} records.</p><form id="prediction-map-form"><div class="cohort-grid">${[['sample_id','Sample ID'],['true_label','Known class'],['predicted_label','Predicted class']].map(([id,label])=>`<div><label for="map-${id}">${label}</label><select required id="map-${id}">${options}</select></div>`).join('')}</div><label for="map-classes">Model classes · one per line</label><textarea id="map-classes" rows="4" required></textarea><button type="button" id="map-observed">Use observed class names</button><p class="help">Add model classes absent from this cohort. Scores are optional; map a complete class vector or leave all score columns blank.</p><div id="map-scores"></div><label for="map-name">Dataset name</label><input id="map-name" required value="${esc(file.name)}"><label for="map-model">Model name or version</label><input id="map-model" required><label for="map-label-source">How were the known labels established?</label><input id="map-label-source" required><label class="check"><input type="checkbox" required>I reviewed the classes and columns. Patient independence remains unknown.</label><button type="submit">Save predictions for ACE</button></form>`;
      for(const key of ['sample_id','true_label','predicted_label'])if(preview.headers.includes(key))$('#map-'+key).value=key;
      const scores=()=>{
        const classes=$('#map-classes').value.split('\n').map(s=>s.trim()).filter(Boolean);
        $('#map-scores').innerHTML=classes.map((label,i)=>`<label for="map-score-${i}">Score column for ${esc(label)}</label><select id="map-score-${i}"><option value="">No score column</option>${options}</select>`).join('');
      };
      $('#map-observed').onclick=()=>{$('#map-classes').value=[...new Set(['true_label','predicted_label'].flatMap(key=>preview.values[$('#map-'+key).value]||[]))].filter(Boolean).join('\n');scores()};
      $('#map-classes').onchange=scores;
      $('#prediction-map-form').onsubmit=async event=>{
        event.preventDefault();const button=event.submitter;button.disabled=true;
        try{
          const classes=$('#map-classes').value.split('\n').map(s=>s.trim()).filter(Boolean),probability_columns=Object.create(null);
          classes.forEach((label,i)=>{const column=$('#map-score-'+i)?.value;if(column)probability_columns[label]=column});
          const mapping={name:$('#map-name').value,model_id:$('#map-model').value,label_source_description:$('#map-label-source').value,classes,probability_columns,reviewed:true};
          for(const key of ['sample_id','true_label','predicted_label'])mapping[key]=$('#map-'+key).value;
          const body=new FormData();body.set('table',file);body.set('mapping',JSON.stringify(mapping));
          const saved=await request('/api/predictions/import',{method:'POST',body});await refresh();
          $('#registry-task').value='evaluate_predictions';$('#registry-task').dispatchEvent(new Event('change'));$('#registry-source').value=saved.id;
          $('#registry-name').value=mapping.name+' · prediction evaluation';$('#registry-analysis').requestSubmit($('#registry-check'));
          out.textContent='Predictions saved and selected. Review ACE checks, then compute.';$('#registry-analysis').scrollIntoView({block:'start'});
        }catch(error){out.textContent=error.message}finally{button.disabled=false}
      };
      out.textContent='Choose the exact columns and review the class universe.';
    }catch(error){out.textContent=error.message}
  };
  $('#storage-check').onclick=async()=>{try{const s=await request('/api/workspace/storage');$('#storage-usage').textContent=`${(s.bytes/1048576).toFixed(1)} MiB · ${s.datasets} dataset versions · ${s.studies} studies. `+Object.entries(s.categories).map(([k,v])=>`${k}: ${(v/1048576).toFixed(1)} MiB`).join(' · ')}catch(e){$('#storage-usage').textContent=e.message}};
  $('#workspace-backup').onclick=async()=>{const b=$('#workspace-backup'),out=$('#backup-status');b.disabled=true;out.textContent='Creating a registry snapshot and copying immutable files…';try{const r=await request('/api/workspace/backup',{method:'POST'});out.innerHTML=`<a href="${esc(r.url)}" download>Download private backup · ${(r.bytes/1048576).toFixed(1)} MiB</a><p>Restore instructions and file hashes are inside the ZIP. Restore into a separate empty workspace.</p>`}catch(e){out.textContent=e.message}finally{b.disabled=false}};
  $('#compare-analyses').onclick=async()=>{
    const out=$('#comparison-result'),ids=[$('#compare-left').value,$('#compare-right').value];
    if(ids.some(id=>!id)||ids[0]===ids[1]){out.textContent='Choose two different saved analyses.';return}
    try{const results=await Promise.all(ids.map(id=>request('/api/runs/'+encodeURIComponent(id))));
      if(results[0].mode!==results[1].mode){out.textContent='These analyses use different tasks. Compare runs of the same task; no combined statistic is computed.';return}
      out.innerHTML=`<p>Recorded results side by side. Differences in datasets, feature universes or thresholds can change these results; this is not a statistical test between runs.</p><div class="cohort-grid">${results.map(r=>{const a=r.race?.aggregate,v=r.validation?.metrics;return `<section><h4>${esc(r.name)}</h4><p>${esc(r.mode)}</p>${a?`<p>${a.supported}/${a.selected} target-supported associations · ${a.source_features_screened} source-screened features</p>`:''}${r.validation?`<p>${r.validation.records?.length??'See report'} evaluated records</p>`:''}${r.shift?`<p>${r.shift.feature_coverage?.shared??'See report'} shared features</p>`:''}<a href="#${r.mode==='race'?'race':r.mode==='diagnose_shift'?'cohorts':'ace'}?run=${esc(r.id)}">Open this analysis</a></section>`}).join('')}</div>`;
    }catch(e){out.textContent=e.message}
  };
}
