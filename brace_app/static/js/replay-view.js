import { esc, pct } from "./ui.js";
export function renderReplay(host, data) {
  const replay = data.replay,
    classes = Object.keys(replay.records[0] || {}).filter((key) =>
      key.startsWith("prob_"),
    ),
    counts = new Map();
  for (const record of replay.records)
    counts.set(
      record.predicted_label,
      (counts.get(record.predicted_label) || 0) + 1,
    );
  host.innerHTML = `<h2>Frozen baseline · ${esc(data.name)}</h2><p>${replay.n} target predictions generated using the original source parameters. No model fitting or feature selection occurred on this target.</p>${replay.evaluation_possible ? `<p><strong>${replay.metrics.n_correct} / ${replay.metrics.n} correct</strong> (${pct(replay.metrics.accuracy)}). Known target labels were used only for evaluation.</p><details><summary>Evaluation metrics, class counts and uncertainty</summary><pre>${esc(JSON.stringify(data.validation, null, 2))}</pre></details>` : '<p class="scope-note">Prediction-only result. Target reference labels are absent; accuracy, AUROC and classification error rates are unavailable.</p>'}<dl><dt>Original source run</dt><dd class="mono">${esc(replay.frozen_run_id)}</dd><dt>Frozen model SHA-256</dt><dd class="mono">${esc(replay.model_sha256)}</dd></dl><h3>Predicted class distribution</h3><p>${[...counts].map(([label, n]) => esc(label) + ": " + n + " / " + replay.n).join(" · ")}. Predicted composition is not ground truth.</p><h3>Target prediction records</h3><div class="table-scroll replay-records" tabindex="0" aria-label="Frozen baseline prediction records"><table><thead><tr><th>Sample</th><th>Predicted class</th>${classes.map((key) => "<th>" + esc(key) + "</th>").join("")}</tr></thead><tbody>${replay.records.map((record) => `<tr><td>${esc(record.sample_id)}</td><td>${esc(record.predicted_label)}</td>${classes.map((key) => "<td>" + Number(record[key]).toFixed(4) + "</td>").join("")}</tr>`).join("")}</tbody></table></div><p>Probabilities are model outputs; calibration and independent acquisition are not established by this replay.</p><button id="replay-evidence">Inspect TRACE and export EMBRACE evidence</button>`;
  host.querySelector("#replay-evidence").onclick = () =>
    document.dispatchEvent(
      new CustomEvent("brace:navigate", { detail: "evidence" }),
    );
}
