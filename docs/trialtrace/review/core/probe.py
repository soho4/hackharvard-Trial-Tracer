from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
repo = root.parent / 'TrialTrace'
sys.path.insert(0, str(repo / 'src'))
from trialtrace.exporter import validate_bundle

env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(repo / 'src'))
inputs = root / 'inputs'
inputs.mkdir(exist_ok=True)
for name in ['anchors.csv', 'visits.csv', 'assignments.csv']:
    shutil.copyfile(repo / 'fixtures/core_draft' / name, inputs / name)
shutil.copyfile(repo / 'rules/candidate_rule.json', inputs / 'candidate_rule.json')

def run(label, output, extra=None, rule=None):
    cmd = [str(repo / '.venv/bin/python'), '-m', 'trialtrace.cli',
           '--anchors', str(inputs / 'anchors.csv'), '--visits', str(inputs / 'visits.csv'),
           '--assignments', str(inputs / 'assignments.csv'), '--rule', str(rule or inputs / 'candidate_rule.json'),
           '--draft-synthetic', '--output', str(output), *(extra or [])]
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(cmd, cwd=repo, env=env, capture_output=True)
    ended = datetime.now(timezone.utc).isoformat()
    (root / (label + '.stdout')).write_bytes(result.stdout)
    (root / (label + '.stderr')).write_bytes(result.stderr)
    record = {'command': cmd, 'started_at_utc': started, 'finished_at_utc': ended,
              'exit_code': result.returncode, 'stdout': result.stdout.decode(), 'stderr': result.stderr.decode(),
              'output_exists_after_run': output.exists(),
              'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest() if output.is_file() else None}
    (root / (label + '.command.json')).write_text(json.dumps(record, indent=2) + '\n')
    return record

results = {'reviewed_source_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (repo / 'src/trialtrace').glob('*.py')}}
good = root / 'good.json'
results['baseline'] = run('baseline', good)
results['dangling_option'] = run('dangling_option', good, ['--anchors'])

output = root / 'diagnostic_directory.json'
output.with_suffix(output.suffix + '.diagnostics.json').mkdir(exist_ok=True)
results['diagnostic_directory'] = run('diagnostic_directory', output)

nested = inputs / 'nested_rule.json'
nested.write_text('{"nested":' + '[' * 2000 + '0' + ']' * 2000 + '}')
results['nested_rule'] = run('nested_rule', root / 'nested_output.json', rule=nested)

bundle = json.loads(good.read_text())
for item in bundle['input_files']:
    if item['name'] == 'anchors.csv':
        item['name'] = 'arbitrary_unapproved_role.csv'
for finding in bundle['findings']:
    for item in finding['evidence']:
        if item['source_file'] == 'anchors.csv':
            item['source_file'] = 'arbitrary_unapproved_role.csv'
for table in bundle['input_accounting'].values():
    for issue in table['issues']:
        if issue['evidence']['source_file'] == 'anchors.csv':
            issue['evidence']['source_file'] = 'arbitrary_unapproved_role.csv'
try:
    validate_bundle(bundle)
    results['unknown_declared_role'] = {'validation': 'ACCEPTED', 'unexpected_role': 'arbitrary_unapproved_role.csv'}
except Exception as exc:
    results['unknown_declared_role'] = {'validation': 'REJECTED', 'type': type(exc).__name__, 'message': str(exc)}
(root / 'probe_results.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps({key: {k: v for k,v in value.items() if k in ['exit_code','output_exists_after_run','output_sha256','validation','unexpected_role']} for key, value in results.items() if key != 'reviewed_source_hashes'}, indent=2))
