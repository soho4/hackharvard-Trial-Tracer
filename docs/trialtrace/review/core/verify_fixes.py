"""Read-only regression probes; all mutable inputs/outputs are disposable copies."""
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
run_root = root / ('verification_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S'))
run_root.mkdir()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(repo / 'src'))
results = {'started_at_utc': datetime.now(timezone.utc).isoformat(), 'source_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (repo / 'src/trialtrace').glob('*.py')}, 'cases': {}}

def make_inputs(name):
    folder = run_root / name
    folder.mkdir()
    paths = {}
    for role in ['anchors', 'visits', 'assignments']:
        paths[role] = folder / (role + '.csv')
        shutil.copyfile(repo / 'fixtures/core_draft' / (role + '.csv'), paths[role])
    return folder, paths

def run(name, paths, output, extra=(), rule=None, prefix_extra=()):
    cmd = [str(repo / '.venv/bin/python'), '-m', 'trialtrace.cli', *prefix_extra]
    for role, path in paths.items():
        cmd += ['--' + role, str(path)]
    cmd += ['--rule', str(rule or repo / 'rules/candidate_rule.json'), '--draft-synthetic', '--output', str(output), *extra]
    started = datetime.now(timezone.utc).isoformat()
    r = subprocess.run(cmd, cwd=repo, env=env, capture_output=True)
    result = {'command': cmd, 'exit_code': r.returncode, 'started_at_utc': started, 'finished_at_utc': datetime.now(timezone.utc).isoformat(), 'stdout': r.stdout.decode(), 'stderr': r.stderr.decode(), 'output_exists': output.exists(), 'inputs_present': all(p.is_file() for p in paths.values())}
    results['cases'][name] = result
    return result

folder, paths = make_inputs('malformed')
out = folder / 'report.json'
assert run('malformed_baseline', paths, out)['exit_code'] == 0
old = out.read_bytes()
r = run('dangling_known_option', paths, out, extra=['--anchors'])
assert r['exit_code'] == 2 and not out.exists() and 'Traceback' not in r['stderr']
assert any(p.read_bytes() == old for p in (folder / '.previous').iterdir())

folder, paths = make_inputs('directory')
out = folder / 'report.json'
assert run('directory_baseline', paths, out)['exit_code'] == 0
old = out.read_bytes()
diag = out.with_suffix('.json.diagnostics.json'); diag.mkdir()
r = run('diagnostic_directory', paths, out)
assert r['exit_code'] == 2 and not out.exists() and diag.is_dir() and 'Traceback' not in r['stderr']
assert any(p.read_bytes() == old for p in (folder / '.previous').iterdir())

folder, paths = make_inputs('surrogate')
rule = json.loads((repo / 'rules/candidate_rule.json').read_text()); rule['interpretation_notes'] = ['\ud800']
rule_path = folder / 'rule.json'; rule_path.write_text(json.dumps(rule))
out = folder / 'report.json'
r = run('surrogate_rule', paths, out, rule=rule_path)
assert r['exit_code'] == 2 and not out.exists() and 'Traceback' not in r['stderr'] and out.with_suffix('.json.diagnostics.json').is_file()

for case in ['case_output', 'case_diagnostic']:
    folder, paths = make_inputs(case)
    if case == 'case_output':
        out = folder / 'ANCHORS.CSV'
    else:
        new_path = folder / 'REPORT.JSON.DIAGNOSTICS.JSON'
        paths['visits'].rename(new_path); paths['visits'] = new_path
        out = folder / 'report.json'
    before = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()}
    r = run(case, paths, out)
    after = {k: hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None for k, p in paths.items()}
    r.update(before_input_hashes=before, after_input_hashes=after)
    assert r['exit_code'] == 2 and json.loads(r['stderr'])['diagnostic']['code'] == 'OUTPUT_INPUT_COLLISION' and before == after
    assert not (folder / '.previous').exists()

sys.path.insert(0, str(repo / 'src'))
from trialtrace.exporter import validate_bundle
from trialtrace.errors import InputError
bundle = json.loads((run_root / 'directory/.previous').glob('*').__iter__().__next__().read_text())
for f in bundle['input_files']:
    if f['name'] == 'anchors.csv': f['name'] = 'unknown-role.csv'
for f in bundle['findings']:
    for e in f['evidence']:
        if e['source_file'] == 'anchors.csv': e['source_file'] = 'unknown-role.csv'
for table in bundle['input_accounting'].values():
    for issue in table['issues']:
        if issue['evidence']['source_file'] == 'anchors.csv': issue['evidence']['source_file'] = 'unknown-role.csv'
try:
    validate_bundle(bundle)
    raise AssertionError('unknown logical role accepted')
except InputError as exc:
    results['cases']['unknown_declared_role'] = {'diagnostic': exc.diagnostic(), 'rejected': True}

results['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
results['source_hashes_after'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (repo / 'src/trialtrace').glob('*.py')}
results['source_unchanged_during_checks'] = results['source_hashes'] == results['source_hashes_after']
results['all_assertions_passed'] = True
(root / 'fix_verification.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps({'all_assertions_passed': True, 'cases': list(results['cases']), 'source_unchanged_during_checks': results['source_unchanged_during_checks']}, indent=2))
