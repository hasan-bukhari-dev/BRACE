import {files} from './state.js';
import {$,esc} from './ui.js';
// A guided declaration produces the existing JSON contract. It never infers
// acquisition, an independence claim, class universe or score mapping from data.
export function initDeclaration(invalidate){
 const details=document.createElement('details');details.id='guided-declaration';details.innerHTML=`<summary>Create the class declaration here</summary><p class="help">Use the exact class labels from your model. This setup evaluates supplied predictions as exploratory, with unknown row independence.</p><div class="cohort-grid"><div><label for="declaration-dataset">Dataset name / identifier</label><input id="declaration-dataset"><label for="declaration-model">Model name / identifier (or “not documented”)</label><input id="declaration-model"><label for="declaration-labels">How were the true labels established?</label><input id="declaration-labels"></div><div><label for="declaration-classes">Model classes · one exact label per line</label><textarea id="declaration-classes" rows="3"></textarea><label for="declaration-threshold">Reference confidence cutoff · 0 to 1</label><input type="number" id="declaration-threshold" min="0" max="1" step="any" value="0.95"></div></div><button id="declaration-mapping" type="button">Set optional score columns</button><div id="declaration-scores"></div><p class="help">Leave every score column blank for class-only evaluation. To use confidence, map a distinct column for every model class.</p><p id="declaration-error" role="alert"></p><button id="use-declaration" type="button">Use this class declaration</button>`;
 $('#file-prediction_manifest').closest('.setup-description').prepend(details);
 const wrapper=$('#file-prediction_manifest').closest('.setup-description'),upload=document.createElement('details');upload.innerHTML='<summary>Use an existing class declaration JSON instead</summary>';wrapper.append(upload);[...wrapper.children].filter(e=>e!==details&&e!==upload).forEach(e=>upload.append(e));
 const classes=()=>$('#declaration-classes').value.split(/\r?\n/).map(c=>c.trim()).filter(Boolean);
 function mapping(){const labels=classes();$('#declaration-scores').innerHTML=labels.map((label,i)=>`<label for="score-column-${i}">${esc(label)} · score column</label><input id="score-column-${i}" data-score-label="${esc(label)}" autocomplete="off">`).join('')}
 $('#declaration-mapping').onclick=mapping;
 function hydrate(file){if(!file)return;file.text().then(text=>{if(files.get('prediction_manifest')!==file)return;try{const m=JSON.parse(text);for(const [key,value] of Object.entries({dataset:m.dataset_id,model:m.model_id,labels:m.label_source_description,classes:(m.classes||[]).join('\n'),threshold:m.primary_confidence_threshold??.95}))$('#declaration-'+key).value=value||'';mapping();details.querySelectorAll('[data-score-label]').forEach(el=>el.value=m.probability_columns?.[el.dataset.scoreLabel]||'')}catch{}})}
 hydrate(files.get('prediction_manifest'));$('#file-prediction_manifest').addEventListener('change',()=>hydrate($('#file-prediction_manifest').files[0]));

 details.addEventListener('input',()=>{files.delete('prediction_manifest');$('#name-prediction_manifest').textContent='Declaration changed · save before checks';invalidate()});
 $('#use-declaration').onclick=()=>{
  try{const labels=classes(),dataset=$('#declaration-dataset').value.trim(),model=$('#declaration-model').value.trim(),source=$('#declaration-labels').value.trim(),threshold=Number($('#declaration-threshold').value);
   if(!dataset||!model||!source)throw Error('Enter the dataset, model identifier and origin of the true labels. Use “not documented” for an unknown model.');
   if(labels.length<2||new Set(labels).size!==labels.length)throw Error('Enter at least two distinct model classes, one per line.');
   if(!$('#declaration-threshold').value.trim()||!Number.isFinite(threshold)||threshold<0||threshold>1)throw Error('Reference cutoff must be between 0 and 1.');
   const fields=[...details.querySelectorAll('[data-score-label]')],filled=fields.filter(f=>f.value.trim());
   if(filled.length&&(filled.length!==labels.length||new Set(filled.map(f=>f.dataset.scoreLabel)).size!==labels.length||!labels.every(c=>filled.some(f=>f.dataset.scoreLabel===c))))throw Error('Map a score column for every current class, or leave all columns blank.');
   const probability_columns=Object.fromEntries(filled.map(f=>[f.dataset.scoreLabel,f.value.trim()]));if(new Set(Object.values(probability_columns)).size!==filled.length)throw Error('Each class needs a distinct score column.');
   const declaration={schema_version:'1.0.0',dataset_id:dataset,model_id:model,classes:labels,probability_columns,prediction_origin:'external_model',evaluation_role:'external_exploratory',independence_declaration:'unknown',label_source_description:source,primary_confidence_threshold:threshold};
   const file=new File([JSON.stringify(declaration,null,2)],'classification_declaration.json',{type:'application/json'});files.set('prediction_manifest',file);const transfer=new DataTransfer();transfer.items.add(file);$('#file-prediction_manifest').files=transfer.files;$('#name-prediction_manifest').textContent='Created from your declared settings: '+file.name;$('#declaration-error').textContent='Class declaration selected. Check files to validate labels and score vectors.';invalidate();
  }catch(error){$('#declaration-error').textContent=error.message}
 };
}
