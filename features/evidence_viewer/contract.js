// TrialTrace evidence report contract: validation, counting and filtering.
// Pure functions with no DOM access, so they run in the browser and under `node --test`.
// None of these functions modify their inputs.
(function (root) {
  "use strict";

  const SCHEMA_VERSION = "trialtrace.evidence.v1";
  const MAX_REPORT_BYTES = 2000000;
  const MAX_FINDINGS = 10000;
  const STATUSES = ["PASS", "POTENTIAL_DEVIATION", "DATA_QUERY", "NOT_EVALUABLE"];
  const UNRESOLVED = ["DATA_QUERY", "NOT_EVALUABLE"];
  const PRODUCER_KINDS = ["CONTRACT_FIXTURE", "ARITHMETIC_PROBE", "DEMO_ENGINE"];
  const REVIEW_STATUSES = ["PENDING_TEAM_SOURCE_REVIEW", "TEAM_REVIEWED_SYNTHETIC_DEMO"];
  const REPORT_FIELDS = ["schema_version", "run_id", "data_kind", "clinical_validation", "producer",
    "review_status", "source", "ruleset", "input_files", "limitations", "findings"];
  const FINDING_FIELDS = ["finding_id", "record_ordinal", "participant_id", "site_id", "visit_id",
    "visit_code", "status", "reason", "calculation", "evidence"];
  const IDENTITY_FIELDS = ["participant_id", "site_id", "visit_id", "visit_code"];
  const DATE_FIELDS = ["target", "earliest", "latest", "actual"];

  const isObject = (v) => typeof v === "object" && v !== null && !Array.isArray(v);
  const isNonEmptyString = (v) => typeof v === "string" && v.length > 0;
  const isPositiveInteger = (v) => Number.isInteger(v) && v >= 1;
  const isSha256 = (v) => typeof v === "string" && /^[0-9a-f]{64}$/.test(v);

  // A real calendar date in YYYY-MM-DD form (rejects e.g. 2026-02-30, which the schema pattern allows).
  function isCalendarDate(v) {
    if (typeof v !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(v)) return false;
    const [y, m, d] = v.split("-").map(Number);
    const date = new Date(Date.UTC(y, m - 1, d));
    return date.getUTCFullYear() === y && date.getUTCMonth() === m - 1 && date.getUTCDate() === d;
  }

  function validateBundle(bundle) {
    const errors = [];
    const err = (path, message) => errors.push(`${path}: ${message}`);

    if (!isObject(bundle)) return { ok: false, errors: ["report: must be a JSON object"] };

    // Check the version first: a report in another format would only produce misleading field errors.
    if (bundle.schema_version !== SCHEMA_VERSION) {
      return { ok: false, errors: [`schema_version: expected "${SCHEMA_VERSION}", got ${JSON.stringify(bundle.schema_version)}`] };
    }

    for (const field of REPORT_FIELDS) {
      if (!(field in bundle)) err(field, "required field is missing");
    }

    if ("run_id" in bundle && !isNonEmptyString(bundle.run_id)) err("run_id", "must be a nonempty string");
    if ("data_kind" in bundle && bundle.data_kind !== "SYNTHETIC") err("data_kind", 'only "SYNTHETIC" reports are supported');
    if ("clinical_validation" in bundle && bundle.clinical_validation !== false) err("clinical_validation", "must be exactly false");

    if ("producer" in bundle) {
      const p = bundle.producer;
      if (!isObject(p)) err("producer", "must be an object");
      else {
        if (!PRODUCER_KINDS.includes(p.kind)) err("producer.kind", `must be one of ${PRODUCER_KINDS.join(", ")}`);
        if (!isNonEmptyString(p.version)) err("producer.version", "must be a nonempty string");
      }
    }

    if ("review_status" in bundle && !REVIEW_STATUSES.includes(bundle.review_status)) {
      err("review_status", `must be one of ${REVIEW_STATUSES.join(", ")}`);
    }

    if ("source" in bundle) {
      const s = bundle.source;
      if (!isObject(s)) err("source", "must be an object");
      else {
        for (const f of ["url", "locator", "pdf_sha256", "retrieval_status"]) {
          if (!(f in s)) err(`source.${f}`, "required field is missing");
        }
        if ("url" in s && typeof s.url !== "string") err("source.url", "must be a string");
        if ("locator" in s && !isNonEmptyString(s.locator)) err("source.locator", "must be a nonempty string");
        if ("pdf_sha256" in s && s.pdf_sha256 !== null && !isSha256(s.pdf_sha256)) {
          err("source.pdf_sha256", "must be null or a 64-character lowercase hex SHA-256");
        }
        if ("retrieval_status" in s && !isNonEmptyString(s.retrieval_status)) err("source.retrieval_status", "must be a nonempty string");
      }
    }

    if ("ruleset" in bundle) {
      const r = bundle.ruleset;
      if (!isObject(r)) err("ruleset", "must be an object");
      else {
        if (!isNonEmptyString(r.id)) err("ruleset.id", "must be a nonempty string");
        if (!isNonEmptyString(r.version)) err("ruleset.version", "must be a nonempty string");
        if (!isSha256(r.sha256)) err("ruleset.sha256", "must be a 64-character lowercase hex SHA-256");
      }
    }

    // Declared hash of each input file, by name, for the evidence cross-check below.
    const fileHashes = new Map();
    if ("input_files" in bundle) {
      const files = bundle.input_files;
      if (!Array.isArray(files) || files.length === 0) err("input_files", "must be a nonempty array");
      else {
        files.forEach((f, i) => {
          const path = `input_files[${i}]`;
          if (!isObject(f)) return err(path, "must be an object");
          if (!isNonEmptyString(f.name)) err(`${path}.name`, "must be a nonempty string");
          else if (fileHashes.has(f.name)) err(`${path}.name`, `duplicate file name "${f.name}"`);
          if (!isSha256(f.sha256)) err(`${path}.sha256`, "must be a 64-character lowercase hex SHA-256");
          if (isNonEmptyString(f.name) && !fileHashes.has(f.name)) fileHashes.set(f.name, f.sha256);
        });
      }
    }

    if ("limitations" in bundle) {
      const l = bundle.limitations;
      if (!Array.isArray(l) || l.length === 0) err("limitations", "must be a nonempty array");
      else l.forEach((item, i) => { if (!isNonEmptyString(item)) err(`limitations[${i}]`, "must be a nonempty string"); });
    }

    if ("findings" in bundle) {
      const findings = bundle.findings;
      if (!Array.isArray(findings)) err("findings", "must be an array");
      else if (findings.length > MAX_FINDINGS) err("findings", `has ${findings.length} items; the maximum is ${MAX_FINDINGS}`);
      else {
        const seenIds = new Set();
        findings.forEach((f, i) => validateFinding(f, `findings[${i}]`, seenIds, fileHashes, err));
      }
    }

    return { ok: errors.length === 0, errors };
  }

  function validateFinding(f, path, seenIds, fileHashes, err) {
    if (!isObject(f)) return err(path, "must be an object");

    for (const field of FINDING_FIELDS) {
      if (!(field in f)) err(`${path}.${field}`, "required field is missing");
    }

    if ("finding_id" in f) {
      if (!isNonEmptyString(f.finding_id)) err(`${path}.finding_id`, "must be a nonempty string");
      else if (seenIds.has(f.finding_id)) err(`${path}.finding_id`, `duplicate finding_id "${f.finding_id}"`);
      else seenIds.add(f.finding_id);
    }
    if ("record_ordinal" in f && !isPositiveInteger(f.record_ordinal)) err(`${path}.record_ordinal`, "must be a positive integer");
    for (const field of IDENTITY_FIELDS) {
      if (field in f && f[field] !== null && typeof f[field] !== "string") err(`${path}.${field}`, "must be a string or null");
    }
    if ("status" in f && !STATUSES.includes(f.status)) {
      err(`${path}.status`, `${JSON.stringify(f.status)} is not one of ${STATUSES.join(", ")}`);
    }
    if ("reason" in f && !isNonEmptyString(f.reason)) err(`${path}.reason`, "must be a nonempty string");

    if ("calculation" in f) {
      const c = f.calculation;
      if (c !== null) {
        if (!isObject(c)) err(`${path}.calculation`, "must be null or an object");
        else {
          for (const d of DATE_FIELDS) {
            if (!isCalendarDate(c[d])) err(`${path}.calculation.${d}`, "must be a valid YYYY-MM-DD date");
          }
          if (!Number.isInteger(c.days_outside) || c.days_outside < 0) {
            err(`${path}.calculation.days_outside`, "must be a nonnegative integer");
          }
        }
      }
      // The outcome and the calculation must agree. We check that they agree; we never recompute the dates.
      if (f.status === "PASS" && !(isObject(c) && c.days_outside === 0)) {
        err(`${path}.calculation`, "a PASS needs a calculation with days_outside 0");
      }
      if (f.status === "POTENTIAL_DEVIATION" && !(isObject(c) && Number.isInteger(c.days_outside) && c.days_outside > 0)) {
        err(`${path}.calculation`, "a POTENTIAL_DEVIATION needs a calculation with days_outside above 0");
      }
      if (UNRESOLVED.includes(f.status) && c !== null) {
        err(`${path}.calculation`, `a ${f.status} must have a null calculation`);
      }
    }

    if ("evidence" in f) {
      const ev = f.evidence;
      if (!Array.isArray(ev) || ev.length === 0) return err(`${path}.evidence`, "must be a nonempty array");
      ev.forEach((e, j) => {
        const ep = `${path}.evidence[${j}]`;
        if (!isObject(e)) return err(ep, "must be an object");
        if (!isNonEmptyString(e.source_file)) err(`${ep}.source_file`, "must be a nonempty string");
        else if (!fileHashes.has(e.source_file)) err(`${ep}.source_file`, `"${e.source_file}" is not listed in input_files`);
        if (!isPositiveInteger(e.record_ordinal)) err(`${ep}.record_ordinal`, "must be a positive integer");
        if (!isSha256(e.sha256)) err(`${ep}.sha256`, "must be a 64-character lowercase hex SHA-256");
        else if (fileHashes.has(e.source_file) && fileHashes.get(e.source_file) !== e.sha256) {
          err(`${ep}.sha256`, `does not match the declared sha256 of input file "${e.source_file}"`);
        }
        if (!isObject(e.raw_record)) err(`${ep}.raw_record`, "must be an object");
      });
    }
  }

  // Parse the text of an uploaded file and validate it. Size is measured in UTF-8 bytes.
  function parseReportText(text) {
    const bytes = new TextEncoder().encode(text).length;
    if (bytes > MAX_REPORT_BYTES) {
      return { ok: false, bundle: null, errors: [`file: ${bytes} bytes is over the ${MAX_REPORT_BYTES}-byte limit`] };
    }
    let bundle;
    try {
      bundle = JSON.parse(text);
    } catch (e) {
      return { ok: false, bundle: null, errors: [`file: not valid JSON (${e.message})`] };
    }
    const result = validateBundle(bundle);
    return { ok: result.ok, bundle: result.ok ? bundle : null, errors: result.errors };
  }

  function summarizeFindings(findings) {
    const summary = { total: findings.length, PASS: 0, POTENTIAL_DEVIATION: 0, DATA_QUERY: 0, NOT_EVALUABLE: 0 };
    for (const f of findings) {
      if (STATUSES.includes(f.status)) summary[f.status] += 1;
    }
    return summary;
  }

  const SEARCH_FIELDS = ["finding_id", "participant_id", "site_id", "visit_id", "visit_code", "reason"];

  function filterFindings(findings, status = "ALL", query = "") {
    const q = String(query).trim().toLowerCase();
    return findings.filter((f) =>
      (status === "ALL" || f.status === status) &&
      (q === "" || SEARCH_FIELDS.some((k) => typeof f[k] === "string" && f[k].toLowerCase().includes(q))));
  }

  // Only HTTPS links without embedded user names or passwords may be clickable.
  function safeSourceURL(value) {
    if (typeof value !== "string") return null;
    let url;
    try {
      url = new URL(value);
    } catch (e) {
      return null;
    }
    if (url.protocol !== "https:" || url.username || url.password) return null;
    return url.href;
  }

  const api = {
    SCHEMA_VERSION, MAX_REPORT_BYTES, STATUSES,
    validateBundle, parseReportText, summarizeFindings, filterFindings, safeSourceURL,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.TrialTraceContract = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
