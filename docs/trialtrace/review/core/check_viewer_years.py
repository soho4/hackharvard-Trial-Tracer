"""Compare actual core exports with an inspected, unchanged teammate validator."""
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
repo = root.parent / 'TrialTrace'
ref = 'origin/abinet/evidence-viewer'
contract_path = 'features/evidence_viewer/contract.js'
git = lambda *args: subprocess.check_output(['git', *args], cwd=repo)
contract = git('show', f'{ref}:{contract_path}')
snapshot = root / 'teammate_contract.js'
snapshot.write_bytes(contract)
metadata = {'ref': ref, 'commit': git('rev-parse', ref).decode().strip(), 'path': contract_path, 'sha256': hashlib.sha256(contract).hexdigest()}
reference = root.parent / 'trialtrace_handoff/reference/v3/reference_evidence_viewer/contract.js'
sys.path.insert(0, str(repo / 'src'))
from trialtrace.importer import HEADERS, load_inputs
from trialtrace.exporter import build_bundle, serialize_bundle
raw_rule = (repo / 'rules/candidate_rule.json').read_bytes()
rule = json.loads(raw_rule)
results = {'teammate_validator': metadata, 'reference_validator': {'path': str(reference), 'sha256': hashlib.sha256(reference.read_bytes()).hexdigest()}, 'cases': []}
for year in ['0001', '0099', '0100', '2026']:
    folder = root / ('viewer_year_' + year)
    folder.mkdir(exist_ok=True)
    common = {'study_id': 'NCT04470427', 'participant_id': 'synthetic-year-review', 'site_id': 'synthetic-site'}
    rows = {
        'anchors.csv': dict(common, anchor_id='a-year', anchor_code='OL_D1', anchor_kind='ACTUAL_VACCINATION', anchor_date=year + '-01-01'),
        'visits.csv': dict(common, visit_id='v-year', visit_code='OL_D8', event_kind='SAFETY_PHONE_CALL', actual_date=year + '-01-08', visit_status='COMPLETED', anchor_id='a-year', assignment_id='s-year'),
        'assignments.csv': dict(common, assignment_id='s-year', rule_version='A10_DRAFT_2', schedule_code='TABLE21', mapping_status='DRAFT_SYNTHETIC', mapping_note='Synthetic technical date-boundary test; no source approval.'),
    }
    paths = {}
    for name, row in rows.items():
        paths[name] = folder / name
        with paths[name].open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=HEADERS[name], lineterminator='\n'); writer.writeheader(); writer.writerow(row)
    bundle = build_bundle(load_inputs(paths), rule, hashlib.sha256(raw_rule).hexdigest(), mode='DRAFT_ENGINEERING')
    output = folder / 'actual_core_bundle.json'
    output.write_bytes(serialize_bundle(bundle))
    script = 'const fs=require("fs"); const api=require(process.argv[1]); const b=JSON.parse(fs.readFileSync(process.argv[2],"utf8")); process.stdout.write(JSON.stringify(api.validateBundle(b)));'
    node = '/Users/yisak/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    result = subprocess.run([node, '-e', script, str(snapshot), str(output)], capture_output=True)
    reference_result = subprocess.run([node, '-e', script, str(reference), str(output)], capture_output=True)
    results['cases'].append({'year': year, 'core_status': bundle['findings'][0]['status'], 'calculation': bundle['findings'][0]['calculation'], 'core_code_sha256': bundle['producer']['code_sha256'], 'bundle_sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'validator_exit_code': result.returncode, 'validator': json.loads(result.stdout), 'stderr': result.stderr.decode(), 'reference_validator': json.loads(reference_result.stdout), 'reference_validator_exit_code': reference_result.returncode})
(root / 'viewer_year_results.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))
