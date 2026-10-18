// The contract under review is selected with VIEWER_CONTRACT; no application mocks.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const contractPath = path.resolve(process.env.VIEWER_CONTRACT || path.join(__dirname, 'candidate/contract.js'));
const {validateBundle, parseReportText, summarizeFindings, safeSourceURL} = require(contractPath);
const load = (name='mixed.json') => JSON.parse(fs.readFileSync(path.join(__dirname, 'native_snapshot/fixtures', name), 'utf8'));

for (const date of ['0001-01-08', '0004-02-29', '0099-12-31', '0100-03-01', '0400-02-29', '2000-02-29', '9999-12-31']) {
  test(`accepts Gregorian date ${date} without 1900 remapping`, () => {
    const b = load();
    for (const field of ['target', 'earliest', 'latest', 'actual']) b.findings[0].calculation[field] = date;
    assert.deepEqual(validateBundle(b), {ok: true, errors: []});
  });
}
for (const date of ['0000-01-01', '0001-02-29', '0100-02-29', '1900-02-29', '2100-02-29', '2026-04-31', '2026-00-01', '2026-13-01', '2026-01-00', '2026-01-32']) {
  test(`rejects impossible date ${date}`, () => {
    const b = load(); b.findings[0].calculation.actual = date;
    const r = validateBundle(b);
    assert.equal(r.ok, false);
    assert.ok(r.errors.some(e => e.startsWith('findings[0].calculation.actual:')));
  });
}
test('unknown version is rejected before treating findings as v1', () => {
  const b = load(); b.schema_version='trialtrace.evidence.future'; b.findings=[];
  assert.equal(validateBundle(b).ok, false);
});
test('unknown clinical conclusion cannot be counted as a valid finding', () => {
  const b = load(); b.findings[0].status='CLINICALLY_CLEARED';
  assert.equal(validateBundle(b).ok, false);
});
test('internal evidence provenance rejects a changed hash and unknown source role', () => {
  const wrongHash=load(); wrongHash.findings[0].evidence[0].sha256='1'.repeat(64);
  const unknown=load(); unknown.findings[0].evidence[0].source_file='invented.csv';
  assert.equal(validateBundle(wrongHash).ok, false);
  assert.equal(validateBundle(unknown).ok, false);
});
test('markup fixture parses unchanged but javascript source is not a link', () => {
  const raw=fs.readFileSync(path.join(__dirname,'native_snapshot/fixtures/markup.json'),'utf8');
  const r=parseReportText(raw);
  assert.equal(r.ok,true);
  assert.equal(r.bundle.findings[0].participant_id,'<script>window.__unexpected_script_ran=true</script>');
  assert.equal(safeSourceURL(r.bundle.source.url),null);
});
for (const name of ['before','after','missing_anchor','wrong_person','unresolved','unknown_event','empty_visits']) {
  test(`actual CLI export ${name} passes this viewer`, () => {
    const raw=fs.readFileSync(path.join(__dirname,'../../examples/execution',name,'bundle.json'),'utf8');
    const r=parseReportText(raw);
    assert.equal(r.ok,true,JSON.stringify(r.errors));
    assert.equal(r.bundle.producer.kind,'DEMO_ENGINE');
    assert.equal(r.bundle.review_status,'PENDING_TEAM_SOURCE_REVIEW');
    assert.equal(summarizeFindings(r.bundle.findings).total,r.bundle.findings.length);
  });
}
for (const name of ['early0001','leap0004','early0099']) {
  test(`new actual CLI early-year export ${name} passes this viewer`, () => {
    const raw=fs.readFileSync(path.join(__dirname,'../../docs/trialtrace/review/g3_viewer/inputs',name,'bundle.json'),'utf8');
    const r=parseReportText(raw);
    assert.equal(r.ok,true,JSON.stringify(r.errors));
    assert.equal(r.bundle.producer.kind,'DEMO_ENGINE');
    assert.equal(r.bundle.review_status,'PENDING_TEAM_SOURCE_REVIEW');
  });
}
