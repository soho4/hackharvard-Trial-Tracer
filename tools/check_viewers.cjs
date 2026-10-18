// Validate actual computed JSON against immutable, isolated viewer validators.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const contracts = {
  handoff_reference: require('./viewer_reference/handoff_contract.cjs'),
  teammate_branch_snapshot: require('./viewer_reference/teammate_contract.cjs'),
};
const repo = path.resolve(__dirname, '..');
const names = ['before/bundle.json', 'after/bundle.json', 'missing_anchor/bundle.json',
  'wrong_person/bundle.json', 'unresolved/bundle.json', 'unknown_event/bundle.json',
  'empty_visits/bundle.json', 'frozen_bundle.json'];
const results = [];
for (const name of names) {
  const file = path.join(repo, 'examples/execution', name);
  const raw = fs.readFileSync(file);
  assert.ok(raw.length <= 2000000);
  const bundle = JSON.parse(raw);
  const checks = {};
  for (const [label, contract] of Object.entries(contracts)) {
    const checked = contract.validateBundle(bundle);
    assert.equal(checked.ok, true, `${label} ${name}: ${checked.errors.join('; ')}`);
    if (contract.parseReportText) assert.equal(contract.parseReportText(raw.toString('utf8')).ok, true);
    checks[label] = checked;
    if (bundle.findings.length) {
      const duplicate = JSON.parse(raw);
      duplicate.findings.push(duplicate.findings[0]);
      assert.equal(contract.validateBundle(duplicate).ok, false, 'Duplicate-ID control must fail');
      const mismatch = JSON.parse(raw);
      mismatch.findings[0].evidence[0].sha256 = '0'.repeat(64);
      assert.equal(contract.validateBundle(mismatch).ok, false, 'Hash mismatch control must fail');
    }
  }
  results.push({file: name, bytes: raw.length, sha256: crypto.createHash('sha256').update(raw).digest('hex'), checks});
}
const result = {status: 'PASS_FOR_EIGHT_ACTUAL_CORE_REPORTS', node: process.version, results,
  limitations: ['Contract checks only, no browser/UI integration.', 'Separate teammate validator has a recorded 0001–0099 year limitation; see review/core/viewer_year_results.json.']};
fs.writeFileSync(path.join(repo, 'docs/trialtrace/viewer_compatibility.json'), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
