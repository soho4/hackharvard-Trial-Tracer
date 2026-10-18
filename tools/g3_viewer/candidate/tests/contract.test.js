// Run: node --test features/evidence_viewer/tests/contract.test.js
// Expected values are written by hand from the fixtures, never computed by the functions under test.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {
  validateBundle, parseReportText, summarizeFindings, filterFindings, safeSourceURL, MAX_REPORT_BYTES,
} = require("../contract.js");

const FIXTURES = path.join(__dirname, "..", "fixtures");
const readText = (name) => fs.readFileSync(path.join(FIXTURES, name), "utf8");
const load = (name) => JSON.parse(readText(name));

function deepFreeze(obj) {
  for (const value of Object.values(obj)) {
    if (typeof value === "object" && value !== null) deepFreeze(value);
  }
  return Object.freeze(obj);
}

function rejectedWith(bundle, fragment) {
  const result = validateBundle(bundle);
  assert.equal(result.ok, false, "expected the report to be rejected");
  assert.ok(result.errors.some((e) => e.includes(fragment)),
    `expected an error containing "${fragment}", got:\n${result.errors.join("\n")}`);
}

// Supplied fixtures

test("mixed.json is valid and has one finding of each outcome", () => {
  const bundle = load("mixed.json");
  assert.deepEqual(validateBundle(bundle), { ok: true, errors: [] });
  assert.deepEqual(summarizeFindings(bundle.findings),
    { total: 4, PASS: 1, POTENTIAL_DEVIATION: 1, DATA_QUERY: 1, NOT_EVALUABLE: 1 });
});

test("empty.json is valid with zero counts", () => {
  const bundle = load("empty.json");
  assert.deepEqual(validateBundle(bundle), { ok: true, errors: [] });
  assert.deepEqual(summarizeFindings(bundle.findings),
    { total: 0, PASS: 0, POTENTIAL_DEVIATION: 0, DATA_QUERY: 0, NOT_EVALUABLE: 0 });
});

test("invalid_status.json is rejected for CONFIRMED_SAFE", () => {
  rejectedWith(load("invalid_status.json"), "findings[0].status");
  rejectedWith(load("invalid_status.json"), "CONFIRMED_SAFE");
});

test("invalid_duplicate_id.json is rejected for the repeated finding_id", () => {
  rejectedWith(load("invalid_duplicate_id.json"), 'duplicate finding_id "fixture-f-1"');
});

test("invalid_evidence_hash.json is rejected for mismatched declared provenance", () => {
  rejectedWith(load("invalid_evidence_hash.json"), "findings[0].evidence[0].sha256: does not match");
});

test("markup.json is a valid report whose source link is unsafe", () => {
  const bundle = load("markup.json");
  assert.deepEqual(validateBundle(bundle), { ok: true, errors: [] });
  assert.equal(safeSourceURL(bundle.source.url), null);
  assert.equal(bundle.findings[0].participant_id, "<script>window.__unexpected_script_ran=true</script>");
});

test("a null source PDF hash is valid", () => {
  assert.equal(load("mixed.json").source.pdf_sha256, null);
  assert.equal(validateBundle(load("mixed.json")).ok, true);
});

// Our own cases, built by changing one thing in mixed.json

test("adding a fifth PASS finding gives total 5 and PASS 2", () => {
  const bundle = load("mixed.json");
  const extra = structuredClone(bundle.findings[0]);
  extra.finding_id = "abinet-test-f-5";
  extra.participant_id = "DEMO-P005";
  bundle.run_id = "abinet-test-run-005";
  bundle.findings.push(extra);
  assert.equal(validateBundle(bundle).ok, true);
  assert.deepEqual(summarizeFindings(bundle.findings),
    { total: 5, PASS: 2, POTENTIAL_DEVIATION: 1, DATA_QUERY: 1, NOT_EVALUABLE: 1 });
});

test("a missing required report field is rejected", () => {
  const bundle = load("mixed.json");
  delete bundle.run_id;
  rejectedWith(bundle, "run_id: required field is missing");
});

test("a missing required finding field is rejected (null is allowed, absent is not)", () => {
  const bundle = load("mixed.json");
  delete bundle.findings[2].calculation;
  rejectedWith(bundle, "findings[2].calculation: required field is missing");
});

test("an unknown schema version is rejected", () => {
  const bundle = load("mixed.json");
  bundle.schema_version = "trialtrace.evidence.v2";
  rejectedWith(bundle, "schema_version");
});

test("non-synthetic data and clinical-validation claims are rejected", () => {
  const a = load("mixed.json"); a.data_kind = "REAL";
  rejectedWith(a, "data_kind");
  const b = load("mixed.json"); b.clinical_validation = true;
  rejectedWith(b, "clinical_validation");
  const c = load("mixed.json"); c.clinical_validation = "false";
  rejectedWith(c, "clinical_validation");
});

test("an impossible calendar date is rejected", () => {
  const bundle = load("mixed.json");
  bundle.findings[0].calculation.actual = "2026-02-30";
  rejectedWith(bundle, "findings[0].calculation.actual");
});

test("an outcome that disagrees with its calculation is rejected", () => {
  const passLate = load("mixed.json");
  passLate.findings[0].calculation.days_outside = 1;
  rejectedWith(passLate, "a PASS needs a calculation with days_outside 0");

  const deviationOnTime = load("mixed.json");
  deviationOnTime.findings[1].calculation.days_outside = 0;
  rejectedWith(deviationOnTime, "a POTENTIAL_DEVIATION needs");

  const queryWithDates = load("mixed.json");
  queryWithDates.findings[2].calculation = structuredClone(queryWithDates.findings[0].calculation);
  rejectedWith(queryWithDates, "a DATA_QUERY must have a null calculation");

  const passWithoutDates = load("mixed.json");
  passWithoutDates.findings[0].calculation = null;
  rejectedWith(passWithoutDates, "a PASS needs");
});

test("evidence from a file not listed in input_files is rejected", () => {
  const bundle = load("mixed.json");
  bundle.findings[1].evidence[0].source_file = "other.csv";
  rejectedWith(bundle, '"other.csv" is not listed in input_files');
});

test("duplicate input file names are rejected", () => {
  const bundle = load("mixed.json");
  bundle.input_files.push(structuredClone(bundle.input_files[0]));
  rejectedWith(bundle, "duplicate file name");
});

test("a malformed hash is rejected", () => {
  const bundle = load("mixed.json");
  bundle.source.pdf_sha256 = "ABC";
  rejectedWith(bundle, "source.pdf_sha256");
});

test("non-object input is rejected", () => {
  for (const value of [null, [], "report", 42]) {
    assert.equal(validateBundle(value).ok, false);
  }
});

test("more than 10,000 findings is rejected", () => {
  const bundle = load("mixed.json");
  bundle.findings = Array.from({ length: 10001 }, (_, i) => ({ ...bundle.findings[0], finding_id: `f-${i}` }));
  rejectedWith(bundle, "the maximum is 10000");
});

// Parsing the uploaded text

test("broken JSON is rejected", () => {
  const result = parseReportText('{"schema_version": ');
  assert.equal(result.ok, false);
  assert.match(result.errors[0], /not valid JSON/);
});

test("a file over 2,000,000 bytes is rejected before parsing", () => {
  const result = parseReportText(" ".repeat(MAX_REPORT_BYTES + 1));
  assert.equal(result.ok, false);
  assert.match(result.errors[0], /over the 2000000-byte limit/);
});

test("parsing the mixed fixture text succeeds", () => {
  const result = parseReportText(readText("mixed.json"));
  assert.equal(result.ok, true);
  assert.equal(result.bundle.run_id, "fixture-mixed-001");
});

// Filtering

test("filtering to DATA_QUERY lists one finding, fixture-f-3", () => {
  const findings = load("mixed.json").findings;
  assert.deepEqual(filterFindings(findings, "DATA_QUERY").map((f) => f.finding_id), ["fixture-f-3"]);
});

test("searching demo-p002 finds fixture-f-2, case-insensitively", () => {
  const findings = load("mixed.json").findings;
  assert.deepEqual(filterFindings(findings, "ALL", "demo-p002").map((f) => f.finding_id), ["fixture-f-2"]);
  assert.deepEqual(filterFindings(findings, "ALL", "  DEMO-P002 ").map((f) => f.finding_id), ["fixture-f-2"]);
});

test("search also matches reason text, and status and search combine", () => {
  const findings = load("mixed.json").findings;
  assert.deepEqual(filterFindings(findings, "ALL", "anchor date").map((f) => f.finding_id), ["fixture-f-3"]);
  assert.deepEqual(filterFindings(findings, "PASS", "demo-p002"), []);
  assert.equal(filterFindings(findings).length, 4);
});

// Links

test("safeSourceURL allows only plain HTTPS", () => {
  assert.equal(safeSourceURL("https://cdn.clinicaltrials.gov/a.pdf"), "https://cdn.clinicaltrials.gov/a.pdf");
  assert.equal(safeSourceURL("http://cdn.clinicaltrials.gov/a.pdf"), null);
  assert.equal(safeSourceURL("javascript:window.__unexpected_script_ran=true"), null);
  assert.equal(safeSourceURL("https://user:pass@example.com/"), null);
  assert.equal(safeSourceURL("not a url"), null);
  assert.equal(safeSourceURL(null), null);
});

// Read-only

test("no function modifies its input", () => {
  const bundle = deepFreeze(load("mixed.json"));
  const before = JSON.stringify(bundle);
  validateBundle(bundle);
  summarizeFindings(bundle.findings);
  filterFindings(bundle.findings, "PASS", "demo");
  safeSourceURL(bundle.source.url);
  assert.equal(JSON.stringify(bundle), before);
});
