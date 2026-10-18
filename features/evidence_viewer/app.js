// Page logic for the evidence viewer. All report text is shown with textContent, never as HTML.
(function () {
  "use strict";

  const { parseReportText, summarizeFindings, filterFindings, safeSourceURL, MAX_REPORT_BYTES, STATUSES } =
    window.TrialTraceContract;

  const MEANINGS = {
    PASS: "This supported check passed. It does not mean the patient or trial is fully compliant or safe.",
    POTENTIAL_DEVIATION: "The supplied evidence departed from the configured rule and needs review. It is not a confirmed clinical violation.",
    DATA_QUERY: "Necessary data is missing, invalid or conflicting. It is neither a proven missed event nor a passed check.",
    NOT_EVALUABLE: "The event, scope or rule applicability is outside the supported contract. It is neither a clean result nor a deviation.",
  };

  const $ = (id) => document.getElementById(id);
  const ui = {
    fileInput: $("fileInput"), download: $("downloadButton"), print: $("printButton"),
    status: $("status"), errorBox: $("errorBox"), errorFile: $("errorFile"), errorList: $("errorList"),
    report: $("report"), runId: $("runId"), runFacts: $("runFacts"), counts: $("counts"),
    statusFilter: $("statusFilter"), search: $("searchInput"), shownLine: $("shownLine"),
    findingList: $("findingList"), detail: $("detail"),
    provenance: $("provenance"), inputFiles: $("inputFiles"), limitations: $("limitations"),
  };

  // The loaded report. `file` is the uploaded File itself, so download returns the exact original bytes.
  let current = null;
  let selectedId = null;
  let loadToken = 0;

  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  }

  const show = (value) => (value === null || value === undefined ? "Not supplied" : value);

  function addFact(list, term, value, className) {
    list.appendChild(el("dt", term));
    const dd = el("dd", value, className);
    list.appendChild(dd);
    return dd;
  }

  function clearView() {
    current = null;
    selectedId = null;
    ui.download.disabled = true;
    ui.print.disabled = true;
    ui.report.hidden = true;
    ui.errorBox.hidden = true;
    ui.errorList.replaceChildren();
    ui.runId.textContent = "";
    ui.shownLine.textContent = "";
    for (const node of [ui.runFacts, ui.counts, ui.findingList, ui.detail, ui.provenance, ui.inputFiles, ui.limitations]) {
      node.replaceChildren();
    }
    ui.statusFilter.value = "ALL";
    ui.search.value = "";
  }

  function showErrors(fileName, errors) {
    ui.status.textContent = "The selected file was rejected. Nothing from it is displayed.";
    ui.errorFile.textContent = `File: ${fileName}`;
    const shown = errors.slice(0, 25);
    for (const e of shown) ui.errorList.appendChild(el("li", e));
    if (errors.length > shown.length) ui.errorList.appendChild(el("li", `…and ${errors.length - shown.length} more errors`));
    ui.errorBox.hidden = false;
  }

  async function onFileChosen() {
    const token = ++loadToken;
    clearView();
    const file = ui.fileInput.files[0];
    if (!file) {
      ui.status.textContent = "No report loaded. Open a trialtrace.evidence.v1 JSON file.";
      return;
    }
    if (file.size > MAX_REPORT_BYTES) {
      showErrors(file.name, [`file: ${file.size} bytes is over the ${MAX_REPORT_BYTES}-byte limit`]);
      return;
    }
    ui.status.textContent = `Reading ${file.name}…`;
    let text;
    try {
      text = await file.text();
    } catch (e) {
      if (token === loadToken) showErrors(file.name, [`file: could not be read (${e.message})`]);
      return;
    }
    if (token !== loadToken) return; // a newer file was chosen while this one was being read

    const result = parseReportText(text);
    if (!result.ok) {
      showErrors(file.name, result.errors);
      return;
    }
    current = { file, bundle: result.bundle };
    renderReport();
  }

  function renderReport() {
    const b = current.bundle;
    ui.status.textContent = `Loaded ${current.file.name}.`;
    ui.runId.textContent = b.run_id;

    addFact(ui.runFacts, "Data", `${b.data_kind} (clinical validation: ${b.clinical_validation})`);
    addFact(ui.runFacts, "Producer", `${b.producer.kind}, version ${b.producer.version}`);
    addFact(ui.runFacts, "Review state", b.review_status);

    const summary = summarizeFindings(b.findings);
    const tile = (label, value) => {
      const div = el("div", null, "count");
      div.appendChild(el("span", value, "count-value"));
      div.appendChild(el("span", label, "count-label"));
      ui.counts.appendChild(div);
    };
    tile("Findings in report", summary.total);
    for (const s of STATUSES) tile(s, summary[s]);

    renderProvenance(b);
    renderList();
    ui.report.hidden = false;
    ui.download.disabled = false;
    ui.print.disabled = false;
  }

  function renderProvenance(b) {
    const linkCell = addFact(ui.provenance, "Source URL", null);
    const safe = safeSourceURL(b.source.url);
    if (safe) {
      const a = el("a", b.source.url);
      a.href = safe;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      linkCell.appendChild(a);
    } else {
      linkCell.appendChild(el("span", b.source.url || "(empty)", "mono"));
      linkCell.appendChild(el("span", " Link disabled: only HTTPS links without credentials are opened.", "warn"));
    }
    addFact(ui.provenance, "Locator", b.source.locator);
    addFact(ui.provenance, "Retrieval status", b.source.retrieval_status);
    addFact(ui.provenance, "Source PDF SHA-256", b.source.pdf_sha256 === null ? "Not available" : `${b.source.pdf_sha256} (declared, not verified)`, "mono");
    addFact(ui.provenance, "Ruleset", `${b.ruleset.id}, version ${b.ruleset.version}`);
    addFact(ui.provenance, "Ruleset SHA-256", `${b.ruleset.sha256} (declared, not verified)`, "mono");

    for (const f of b.input_files) {
      const li = el("li");
      li.appendChild(el("span", f.name));
      li.appendChild(el("span", ` ${f.sha256} (declared)`, "mono muted"));
      ui.inputFiles.appendChild(li);
    }
    for (const l of b.limitations) ui.limitations.appendChild(el("li", l));
  }

  function renderList() {
    const all = current.bundle.findings;
    const shown = filterFindings(all, ui.statusFilter.value, ui.search.value);
    ui.findingList.replaceChildren();
    ui.shownLine.textContent = `${shown.length} shown / ${all.length} findings in report`;

    if (all.length === 0) {
      ui.findingList.appendChild(el("li", "No findings supplied. This does not establish trial compliance.", "empty"));
    } else if (shown.length === 0) {
      ui.findingList.appendChild(el("li", "No findings match the filter.", "empty"));
    }

    for (const f of shown) {
      const li = el("li");
      const button = el("button", null, "finding" + (f.finding_id === selectedId ? " selected" : ""));
      button.type = "button";
      button.appendChild(el("span", f.status, `badge ${f.status}`));
      button.appendChild(el("span", f.finding_id, "mono"));
      button.appendChild(el("span", `${show(f.participant_id)} · ${show(f.visit_code)}`, "muted"));
      button.addEventListener("click", () => { selectedId = f.finding_id; renderList(); });
      li.appendChild(button);
      ui.findingList.appendChild(li);
    }

    const selected = shown.find((f) => f.finding_id === selectedId);
    if (!selected) selectedId = null;
    renderDetail(selected || null);
  }

  function renderDetail(f) {
    ui.detail.replaceChildren();
    if (!f) {
      ui.detail.appendChild(el("p", "Select a finding to see its evidence.", "muted"));
      return;
    }
    const head = el("p");
    head.appendChild(el("span", f.status, `badge ${f.status}`));
    head.appendChild(el("span", ` ${MEANINGS[f.status]}`));
    ui.detail.appendChild(head);

    const ids = el("dl", null, "facts");
    addFact(ids, "Finding ID", f.finding_id, "mono");
    addFact(ids, "Record ordinal", f.record_ordinal);
    addFact(ids, "Participant", show(f.participant_id), "mono");
    addFact(ids, "Site", show(f.site_id), "mono");
    addFact(ids, "Visit", show(f.visit_id), "mono");
    addFact(ids, "Visit code", show(f.visit_code), "mono");
    addFact(ids, "Supplied reason", f.reason);
    ui.detail.appendChild(ids);

    ui.detail.appendChild(el("h3", "Recorded calculation"));
    if (f.calculation === null) {
      ui.detail.appendChild(el("p", "No timing conclusion supplied.", "muted"));
    } else {
      const c = f.calculation;
      const calc = el("dl", null, "facts");
      addFact(calc, "Target date", c.target, "mono");
      addFact(calc, "Allowed window", `${c.earliest} to ${c.latest}`, "mono");
      addFact(calc, "Observed date", c.actual, "mono");
      addFact(calc, "Days outside window", c.days_outside, "mono");
      ui.detail.appendChild(calc);
      ui.detail.appendChild(el("p", "These values are shown as recorded in the report; the viewer does not recalculate them.", "muted"));
    }

    ui.detail.appendChild(el("h3", "Supporting records"));
    f.evidence.forEach((e) => {
      const box = el("div", null, "evidence");
      const meta = el("dl", null, "facts");
      addFact(meta, "Source file", e.source_file, "mono");
      addFact(meta, "Record ordinal", `${e.record_ordinal} (logical CSV record, not a line number)`);
      addFact(meta, "Declared SHA-256", e.sha256, "mono");
      box.appendChild(meta);
      const table = el("table", null, "raw");
      const tbody = el("tbody");
      for (const [key, value] of Object.entries(e.raw_record)) {
        const tr = el("tr");
        tr.appendChild(el("th", key, "mono"));
        tr.appendChild(el("td", typeof value === "string" ? value : JSON.stringify(value), "mono"));
        tbody.appendChild(tr);
      }
      table.appendChild(tbody);
      box.appendChild(table);
      ui.detail.appendChild(box);
    });

    const raw = el("details", null, "no-print");
    raw.appendChild(el("summary", "Raw JSON of this finding"));
    raw.appendChild(el("pre", JSON.stringify(f, null, 2), "mono"));
    ui.detail.appendChild(raw);
  }

  function downloadOriginal() {
    if (!current) return;
    const url = URL.createObjectURL(current.file);
    const a = el("a");
    a.href = url;
    a.download = current.file.name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  ui.fileInput.addEventListener("change", onFileChosen);
  ui.statusFilter.addEventListener("change", () => current && renderList());
  ui.search.addEventListener("input", () => current && renderList());
  ui.download.addEventListener("click", downloadOriginal);
  ui.print.addEventListener("click", () => window.print());
})();
