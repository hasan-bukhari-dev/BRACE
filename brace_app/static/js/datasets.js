import { $, esc, isSoftwareFixture } from "./ui.js";
import { request } from "./api.js";
let hooks,
  records = [],
  studies = [],
  checked = null,
  revision = 0;
const jsonOptions = (value) => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(value),
});
const label = {
  race: "RACE · gene associations",
  diagnose_shift: "CE · distribution comparison",
  train_validate: "ACE · source baseline",
  evaluate_predictions: "ACE · saved predictions",
};
const issueHTML = (result) =>
  `<p><strong>${result.eligible ? "Task checks passed" : "Analysis blocked"}</strong> · ${esc(result.note || "Review the reasons below.")}</p><ul>${(result.issues || []).map((issue) => `<li><strong>${esc(issue.code)}</strong>: ${esc(issue.message)} ${esc(issue.next_action || "")}</li>`).join("")}</ul><details><summary>Exact input summaries and task decisions</summary><pre>${esc(JSON.stringify(result, null, 2))}</pre></details>`;
function invalidate() {
  revision++;
  checked = null;
  $("#registry-run").disabled = true;
  $("#registry-checks").replaceChildren();
}
function payload() {
  const mode = $("#registry-task").value,
    source = $("#registry-source").value,
    target = $("#registry-target").value,
    name = $("#registry-name").value.trim();
  if (!name) throw Error("Enter a study name.");
  const datasets =
    mode === "evaluate_predictions"
      ? { predictions: source }
      : { source, target };
  if (Object.values(datasets).some((id) => !id))
    throw Error("Select the required prepared datasets.");
  let race_config = {};
  if (mode === "race") {
    const positive = $("#registry-positive").value.trim(),
      negative = $("#registry-negative").value.trim();
    const positiveDefinition = $("#registry-positive-definition").value.trim(),
      negativeDefinition = $("#registry-negative-definition").value.trim();
    if (!positive || !negative || !positiveDefinition || !negativeDefinition)
      throw Error("Complete both biological class labels and definitions.");
    const definitions = {
      [positive]: positiveDefinition,
      [negative]: negativeDefinition,
    };
    race_config = {
      selection_count: Number($("#registry-selection-count").value),
      positive,
      negative,
      source_conditions: definitions,
      target_conditions: definitions,
      allow_processing_difference: $("#registry-processing-review").checked,
      evaluation_role: "exploratory",
      design: "unpaired",
      covariates: [],
    };
    if (!$("#registry-review").checked)
      throw Error(
        "Review both biological definitions and the processing limitations before checking RACE.",
      );
  }
  return {
    schema_version: "1.0.0",
    mode,
    name,
    datasets,
    race_config,
    study_id: $("#registry-study").value || null,
  };
}
function taskChanged() {
  invalidate();
  const prediction = $("#registry-task").value === "evaluate_predictions";
  $("#registry-target-field").hidden = prediction;
  $("#registry-race").hidden = $("#registry-task").value !== "race";
  for (const [role, select] of [
    ["source", $("#registry-source")],
    ["target", $("#registry-target")],
  ]) {
    const previous = select.value;
    select.innerHTML =
      '<option value="">Choose a prepared dataset</option>' +
      records
        .filter(
          (record) =>
            record.status === "prepared" && (!isSoftwareFixture(record) || $("#registry-fixtures").checked) &&
            (prediction
              ? record.summary?.kind === "saved_predictions"
              : record.summary?.manifest?.role === role),
        )
        .map(
          (record) =>
            `<option value="${record.id}">${esc(record.name)}</option>`,
        )
        .join("");
    if ([...select.options].some((option) => option.value === previous))
      select.value = previous;
  }
}
export async function refreshDatasets() {
  const [result, history, savedStudies] = await Promise.all([
    request("/api/datasets"),
    request("/api/runs"),
    request("/api/studies"),
  ]);
  records = result.datasets;
  studies = savedStudies.studies;
  const studySelect = $("#registry-study");
  const selectedStudy = studySelect?.value;
  if (studySelect) {
    studySelect.innerHTML =
      '<option value="">New study</option>' +
      studies
        .map(
          (study) => `<option value="${study.id}">${esc(study.name)}</option>`,
        )
        .join("");
    if (studies.some((study) => study.id === selectedStudy))
      studySelect.value = selectedStudy;
  }
  const frozen = $("#registry-freeze");
  if (frozen)
    frozen.innerHTML =
      '<option value="">Choose a saved source-trained baseline</option>' +
      history.runs
        .filter((run) => run.mode === "train_validate")
        .map((run) => `<option value="${run.id}">${esc(run.name)}</option>`)
        .join("");
  const replayTarget = $("#registry-replay-target");
  if (replayTarget)
    replayTarget.innerHTML =
      '<option value="">Choose a prepared target</option>' +
      records
        .filter((record) => record.summary?.manifest?.role === "target" && (!isSoftwareFixture(record) || $("#registry-fixtures").checked))
        .map(
          (record) =>
            `<option value="${record.id}">${esc(record.name)}</option>`,
        )
        .join("");
  const host = $("#registry-list");
  host.innerHTML = records.length
    ? `<div class="table-scroll" tabindex="0" role="group" aria-label="Scrollable data table"><table><thead><tr><th>Dataset version</th><th>Preparation</th><th>Evidence</th><th>Actions</th></tr></thead><tbody>${records.map((record) => `<tr data-dataset-id="${esc(record.id)}"><th scope="row">${esc(record.name)}</th><td>${record.status === "prepared" ? "Prepared · task checks required" : "Original acquired · preparation required"}${record.summary?.n_samples ? `<br>${record.summary.n_samples} samples · ${record.summary.n_features.toLocaleString()} features` : ""}</td><td>${esc(record.source.accession || record.source.type.replaceAll("_", " "))}${record.summary?.measurement_type ? "<br>" + esc(record.summary.measurement_type.replaceAll("_", " ")) : ""}</td><td><button type="button" data-inspect-dataset="${record.id}">Inspect ${record.status === "acquired" ? "& prepare" : "record"}</button><button type="button" data-rename-dataset="${record.id}">Rename</button></td></tr>`).join("")}</tbody></table></div>`
    : "<p>No datasets registered yet. Add the reviewed example, acquire a public original in SPACE, or import prepared files.</p>";
  host
    .querySelectorAll("[data-inspect-dataset]")
    .forEach(
      (button) =>
        (button.onclick = () => inspect(button.dataset.inspectDataset)),
    );
  host
    .querySelectorAll("[data-rename-dataset]")
    .forEach(
      (button) => (button.onclick = () => rename(button.dataset.renameDataset)),
    );
  filterDatasetRows();
  taskChanged();
}
function filterDatasetRows() {
  const query = $("#registry-search").value.trim().toLowerCase(), status = $("#registry-status").value;
  let count = 0;
  document.querySelectorAll("#registry-list [data-dataset-id]").forEach(row => {
    const record = records.find(item => item.id === row.dataset.datasetId);
    const match = (!isSoftwareFixture(record) || $("#registry-fixtures").checked) && (!status || record.status === status) && (row.textContent + " " + record.id).toLowerCase().includes(query);
    row.hidden = !match; if (match) count++;
  });
  $("#registry-count").textContent = count + " / " + records.length + " dataset versions";
  $("#registry-no-match").hidden = count > 0 || records.length === 0;
}
async function rename(id) {
  const record = records.find((row) => row.id === id),
    host = $("#registry-detail");
  host.innerHTML = `<form id="registry-rename"><label for="registry-new-name">Dataset display name</label><input id="registry-new-name" required maxlength="200" value="${esc(record.name)}"><button>Save display name</button></form>`;
  $("#registry-rename").onsubmit = async (event) => {
    event.preventDefault();
    try {
      await request("/api/datasets/" + id, {
        ...jsonOptions({ name: $("#registry-new-name").value }),
        method: "PATCH",
      });
      await refreshDatasets();
      host.textContent =
        "Display name saved. Dataset version and input hashes are unchanged.";
    } catch (error) {
      hooks.message(error.message, "failed");
    }
  };
  $("#registry-new-name").focus();
}
async function inspect(id) {
  const record = records.find((row) => row.id === id),
    host = $("#registry-detail");
  host.innerHTML = `<h3>${esc(record.name)}</h3><p class="help">${record.status === "prepared" ? "Prepared version · task checks required" : "Acquired original · preparation required"}${record.summary?.n_samples ? " · " + record.summary.n_samples + " samples · " + record.summary.n_features.toLocaleString() + " features" : ""}</p><details><summary>Dataset identity, assets and preparation lineage</summary><pre>${esc(JSON.stringify(record, null, 2))}</pre></details>`;
  if (record.status !== "acquired") {
    request("/api/datasets/" + id + "/checks")
      .then((checks) => {
        if (host.querySelector("h3")?.textContent === record.name)
          host.insertAdjacentHTML(
            "beforeend",
            "<details><summary>Saved task checks for this version</summary><pre>" +
              esc(JSON.stringify(checks, null, 2)) +
              "</pre></details>",
          );
      })
      .catch((error) => hooks.message(error.message, "failed"));
    if (record.summary?.manifest) {
      host.insertAdjacentHTML(
        "beforeend",
        '<details><summary>Create a reviewed phenotype or role version</summary><p>Map every observed condition to your shared biological contrast and supply definitions. Changing a source/target role also creates a new immutable version. Expression values are preserved.</p><form id="registry-transform"><label for="registry-transform-json">Transformation JSON</label><textarea id="registry-transform-json" rows="12"></textarea><label class="check"><input id="registry-transform-review" type="checkbox" required>I reviewed these role and biological class definitions.</label><button>Create transformed dataset version</button></form></details>',
      );
      $("#registry-transform-json").value = JSON.stringify(
        {
          name: record.name + " · reviewed version",
          role: record.summary.manifest.role,
          condition_mapping: {},
          biological_definitions: {},
        },
        null,
        2,
      );
      $("#registry-transform").onsubmit = async (event) => {
        event.preventDefault();
        if (hooks.isBusy()) return;
        hooks.busy(
          true,
          "Saving the reviewed phenotype and role transformation…",
        );
        try {
          const value = JSON.parse($("#registry-transform-json").value);
          value.reviewed = $("#registry-transform-review").checked;
          await request(
            "/api/datasets/" + id + "/transform",
            jsonOptions(value),
          );
          await refreshDatasets();
          host.textContent =
            "Transformed version saved with its parent identity. Select this version and run task checks.";
        } catch (error) {
          hooks.message(error.message, "blocked");
        } finally {
          hooks.busy(false);
        }
      };
    }
    return;
  }
  host.insertAdjacentHTML(
    "beforeend",
    '<p role="status">Checking the compressed matrix, numeric rows and sample annotations…</p>',
  );
  try {
    const preview = await request("/api/datasets/" + id + "/inspect");
    host.innerHTML = `<h3>Review preparation · ${esc(record.name)}</h3><p>${preview.sample_ids.length} original samples · ${preview.feature_count.toLocaleString()} original features. ${esc(preview.note)}</p><details><summary>Original sample annotations and feature identifiers</summary><pre>${esc(JSON.stringify(preview, null, 2))}</pre></details><p>Complete the manifest and explicitly map each sample to a condition, or list an exclusion reason. Empty conditions are allowed only for declared unlabeled data. Feature mapping must be one-to-one, versioned and reviewed; omitted features are recorded. No mapping preserves original identifiers. No normalization is performed.</p><form id="registry-prepare"><label for="registry-preparation">Reviewed preparation JSON</label><textarea id="registry-preparation" rows="16" spellcheck="false"></textarea><label class="check"><input type="checkbox" id="registry-prepare-review" required>I reviewed the biological labels, identifiers, measurement scale and processing declaration.</label><button type="submit">Prepare and register a new version</button></form>`;
    $("#registry-preparation").value = JSON.stringify(
      {
        schema_version: "1.0.0",
        name: record.source.accession + " · reviewed preparation",
        manifest: {
          schema_version: "1.0.0",
          cohort_id: record.source.accession,
          role: "source",
          organism: "",
          feature_namespace: "",
          measurement_type: "",
          processing_description: "",
          labels: "",
          independence_declaration: "unknown",
          accession: record.source.accession,
        },
        condition_by_sample: Object.fromEntries(
          preview.sample_ids.map((sample) => [sample, ""]),
        ),
        excluded_samples: {},
        feature_mapping: {},
        mapping_reference: "",
      },
      null,
      2,
    );
    if(record.source.accession === "GSE21653") {
      $("#registry-prepare").insertAdjacentHTML("beforebegin", '<button type="button" id="load-reviewed-er-plan">Review the pinned GSE21653 ER preparation plan</button><div id="reviewed-er-plan-summary"></div>');
      $("#load-reviewed-er-plan").onclick=async()=>{
        try {
          const plan=await request("/api/datasets/"+id+"/reviewed-er-plan");
          $("#registry-preparation").value=JSON.stringify(plan.preparation,null,2);
          $("#registry-prepare-review").checked=false;
          const s=plan.summary;
          $("#reviewed-er-plan-summary").innerHTML=`<p><strong>${s.included}/${s.original_samples} tumors included:</strong> ${s.conditions.ER_positive} ER-positive and ${s.conditions.ER_negative} ER-negative; ${s.excluded} explicit ER-IHC NA exclusions. ${s.retained_features.toLocaleString()} source-mapped features retained.</p><p>${esc(s.limitations)}</p><p>Read the exact labels, exclusions and mapping below, then confirm the review to prepare. Loading this plan has not changed or analyzed the original.</p>`;
        } catch(error) {hooks.message(error.message,"blocked")}
      };
    }
    $("#registry-prepare").onsubmit = async (event) => {
      event.preventDefault();
      if (hooks.isBusy()) return;
      hooks.busy(true, "Preparing the reviewed public matrix…");
      try {
        const value = JSON.parse($("#registry-preparation").value);
        value.reviewed = $("#registry-prepare-review").checked;
        await request("/api/datasets/" + id + "/prepare", jsonOptions(value));
        await refreshDatasets();
        host.textContent =
          "Prepared dataset registered. Select its role and run the task checks before analysis.";
        hooks.message(
          "Prepared version saved with original-file and transformation lineage.",
          "ready",
        );
      } catch (error) {
        hooks.message(error.message, "blocked");
      } finally {
        hooks.busy(false);
      }
    };
  } catch (error) {
    host.insertAdjacentHTML(
      "beforeend",
      `<p role="alert">${esc(error.message)} The original acquisition is retained. Import a documented processed expression matrix, metadata and manifest if this format is unsupported.</p>`,
    );
  }
}
export function initDatasets(callbacks) {
  hooks = callbacks;
  const host = $("#workspace-datasets");
  host.innerHTML = `<h2>Dataset library</h2><p>Dataset versions and study results are saved locally. Task eligibility is checked against the selected pair and contrast.</p><div class="actions"><button id="registry-public">Add reviewed public ER datasets</button><button id="registry-space">Discover datasets in SPACE ↗</button></div><p class="help">Reviewed example: GSE42568 → GSE20711, ER-positive versus ER-negative tumors. Processing and ER assays differ; donor independence remains unknown. Suitable for exploratory association testing, not normal/tumor baseline training.</p><div class="registry-filters"><label for="registry-search">Find a dataset<input id="registry-search" type="search" placeholder="Name, accession or version ID"></label><label for="registry-status">Preparation<select id="registry-status"><option value="">All versions</option><option value="prepared">Prepared</option><option value="acquired">Acquired originals</option></select></label><label class="check"><input id="registry-fixtures" type="checkbox">Include software checks</label><p id="registry-count" role="status"></p></div><div id="registry-list"></div><p id="registry-no-match" hidden>No dataset versions match. Clear the search or change the preparation filter.</p><div id="registry-detail"></div><details><summary>Import a prepared expression dataset</summary><form id="registry-import"><label for="registry-import-name">Dataset display name</label><input id="registry-import-name" required maxlength="200"><label for="registry-expression">Processed expression (CSV/TSV)</label><input id="registry-expression" type="file" accept=".csv,.tsv" required><label for="registry-metadata">Sample metadata (CSV/TSV)</label><input id="registry-metadata" type="file" accept=".csv,.tsv" required><label for="registry-manifest">BRACE dataset manifest (JSON)</label><input id="registry-manifest" type="file" accept=".json" required><button>Validate and register dataset</button></form></details><form id="registry-analysis"><h3>Analyze registered datasets</h3><label for="registry-study">Study</label><select id="registry-study"><option value="">New study</option></select><label for="registry-name">Study name</label><input id="registry-name" required maxlength="200" placeholder="Name this research question"><label for="registry-task">Scientific task</label><select id="registry-task">${Object.entries(
    label,
  )
    .map(([key, text]) => `<option value="${key}">${text}</option>`)
    .join(
      "",
    )}</select><div class="cohort-grid"><div><label for="registry-source">Source / prediction dataset</label><select id="registry-source"></select></div><div id="registry-target-field"><label for="registry-target">Target dataset</label><select id="registry-target"></select></div></div><details id="registry-race"><summary>Review biological contrast and exploratory processing policy</summary><p>Use exact prepared metadata labels for the same biological contrast in both studies. Create a reviewed phenotype version first if the vocabularies differ.</p><div class="cohort-grid"><div><label for="registry-positive">Positive-group label</label><input id="registry-positive"><label for="registry-positive-definition">Positive-group biological definition</label><input id="registry-positive-definition"></div><div><label for="registry-negative">Negative-group label</label><input id="registry-negative"><label for="registry-negative-definition">Negative-group biological definition</label><input id="registry-negative-definition"></div></div><label class="check"><input id="registry-processing-review" type="checkbox">I accept exploratory within-study effect comparisons despite declared processing differences.</label><label for="registry-selection-count">Source selection cap</label><input id="registry-selection-count" type="number" min="1" max="1000" step="1" value="20"><p class="help">Freeze up to this many source features with BH q ≤ 0.05, ranked by absolute Hedges’ g. 20 preserves the historical example. Choose before inspecting the target; the 1–1000 range is a software limit, not a biological optimum.</p><label class="check"><input id="registry-review" type="checkbox">I reviewed the source and target biological group definitions and processing limitations.</label></details><div class="actions"><button id="registry-check" type="submit">Check selected datasets</button><button id="registry-run" type="button" class="primary" disabled>Compute checked analysis</button></div></form><div id="registry-checks" aria-live="polite"></div><details><summary>Apply a previously frozen BRACE baseline</summary><p>Reuses an existing source-trained JSON freeze. No fitting on the new target. Unlabeled targets produce predictions with no accuracy metrics.</p><form id="registry-replay"><label for="registry-replay-name">Replay study name</label><input id="registry-replay-name" required maxlength="200"><label for="registry-freeze">Original source-trained run</label><select id="registry-freeze" required></select><label for="registry-replay-target">Target dataset version</label><select id="registry-replay-target" required></select><button>Apply frozen baseline</button></form></details>`;
  $("#registry-search").oninput = filterDatasetRows;
  $("#registry-status").onchange = filterDatasetRows;
  $("#registry-fixtures").onchange = () => refreshDatasets().catch(error => hooks.message(error.message, "failed"));
  $("#registry-analysis").addEventListener("input", invalidate);
  $("#registry-task").onchange = taskChanged;
  $("#registry-study").onchange = () => {
    invalidate();
    const study = studies.find((row) => row.id === $("#registry-study").value);
    $("#registry-name").readOnly = !!study;
    if (study) {
      $("#registry-name").value = study.name;
      const currentTask = $("#registry-task").value;
      $("#registry-task").value = taskForStudy(study, currentTask);
      taskChanged();
      $("#registry-source").value =
        study.datasets.source || study.datasets.predictions || "";
      $("#registry-target").value = study.datasets.target || "";
    }
    for (const role of ["source", "target"])
      $("#registry-" + role).disabled = !!study;
  };
  $("#registry-space").onclick = () => $("#open-space").click();
  $("#registry-public").onclick = async () => {
    if (hooks.isBusy()) return;
    hooks.busy(
      true,
      "Verifying the reviewed public preparation and original-file hashes…",
    );
    try {
      const result = await request(
        "/api/datasets/reviewed-public",
        jsonOptions({ reviewed: true }),
      );
      await refreshDatasets();
      $("#registry-study").value = "";
      $("#registry-name").readOnly = false;
      $("#registry-source").disabled = false;
      $("#registry-target").disabled = false;
      $("#registry-task").value = "race";
      taskChanged();
      for (const role of ["source", "target"])
        $("#registry-" + role).value = result.datasets[role].id;
      for (const condition of ["positive", "negative"]) {
        $("#registry-" + condition).value = result.race_config[condition];
        $("#registry-" + condition + "-definition").value =
          result.race_config.source_conditions[result.race_config[condition]];
      }
      $("#registry-processing-review").checked = false;
      $("#registry-name").value = "Breast tumor · ER association";
      $("#registry-review").checked = false;
      $("#registry-race").open = true;
      hooks.message(
        "Reviewed public versions registered. Review the contrast and limitations, then check this task.",
        "ready",
      );
    } catch (error) {
      hooks.message(error.message, "failed");
    } finally {
      hooks.busy(false);
    }
  };
  $("#registry-import").onsubmit = async (event) => {
    event.preventDefault();
    if (hooks.isBusy()) return;
    hooks.busy(true, "Validating and registering the prepared dataset…");
    try {
      const body = new FormData();
      body.set("name", $("#registry-import-name").value);
      for (const kind of ["expression", "metadata", "manifest"])
        body.set(kind, $("#registry-" + kind).files[0]);
      await request("/api/datasets/import", { method: "POST", body });
      await refreshDatasets();
      hooks.message(
        "Prepared dataset saved. Task eligibility is checked when a pair is selected.",
        "ready",
      );
    } catch (error) {
      hooks.message(error.message, "blocked");
    } finally {
      hooks.busy(false);
    }
  };
  $("#registry-analysis").onsubmit = async (event) => {
    event.preventDefault();
    if (hooks.isBusy()) return;
    let value;
    try {
      value = payload();
    } catch (error) {
      hooks.message(error.message, "blocked");
      return;
    }
    const token = revision;
    hooks.busy(true, "Checking selected dataset versions and task rules…");
    try {
      const result = await request(
        "/api/dataset-analysis/preflight",
        jsonOptions(value),
      );
      if (token !== revision) return;
      $("#registry-checks").innerHTML = issueHTML(result);
      checked = result.eligible ? value : null;
      $("#registry-run").disabled = !checked;
      hooks.message(
        result.eligible
          ? "Task checks passed. Review the warnings before computing."
          : "The selected task is blocked; review the specific reasons.",
        result.eligible ? "ready" : "blocked",
      );
    } catch (error) {
      hooks.message(error.message, "blocked");
    } finally {
      hooks.busy(false);
    }
  };
  $("#registry-run").onclick = async () => {
    if (!checked || hooks.isBusy()) return;
    const value = checked;
    hooks.busy(true, "Computing from the exact checked dataset versions…");
    try {
      hooks.completed(
        await request("/api/dataset-analysis/run", jsonOptions(value)),
      );
      await refreshDatasets();
    } catch (error) {
      hooks.message(error.message, "failed");
    } finally {
      hooks.busy(false);
    }
  };
  $("#registry-replay").onsubmit = async (event) => {
    event.preventDefault();
    if (hooks.isBusy()) return;
    hooks.busy(
      true,
      "Verifying the original source freeze and applying it to the target…",
    );
    try {
      hooks.completed(
        await request(
          "/api/dataset-analysis/replay",
          jsonOptions({
            name: $("#registry-replay-name").value,
            frozen_run_id: $("#registry-freeze").value,
            target_dataset_id: $("#registry-replay-target").value,
          }),
        ),
      );
      await refreshDatasets();
    } catch (error) {
      hooks.message(error.message, "blocked");
    } finally {
      hooks.busy(false);
    }
  };
  document.addEventListener("brace:datasets-changed", () =>
    refreshDatasets().catch((error) => hooks.message(error.message, "failed")),
  );
  refreshDatasets().catch((error) => hooks.message(error.message, "failed"));
}

export function taskForStudy(study, currentTask) {
  if (study.datasets.predictions) return "evaluate_predictions";
  return currentTask === "evaluate_predictions" ? "race" : currentTask;
}
