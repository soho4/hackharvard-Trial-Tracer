#!/usr/bin/env python3
"""Installed G3 probe: run fresh-environment Python -I from outside this checkout.

This executes real installed package functions, subprocess CLI, and AppTest.
AppTest is an in-process script test, not a browser or network test.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.resources
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--source-pdf', type=Path)
    parser.add_argument('--out', type=Path, help='Evidence directory; defaults to the original G3 review folder')
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.out.resolve() if args.out else repo/'docs/trialtrace/review/g3_clean_install'
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ') + '-' + uuid.uuid4().hex[:8]
    run = output/'runs'/run_id
    run.mkdir(parents=True, exist_ok=False)
    assert sys.flags.isolated == 1, 'Must run Python -I'
    assert not Path.cwd().resolve().is_relative_to(repo), 'Run outside the checkout'
    assert str(repo/'src') not in sys.path, 'Source checkout must not be on sys.path'
    app_path = repo/'app.py'
    app_sha = sha(app_path.read_bytes())
    lock_path = repo/'requirements-ui.lock'
    lock_sha = sha(lock_path.read_bytes())

    import trialtrace
    from trialtrace.cli import load_rule
    from trialtrace.errors import InputError
    from trialtrace.exporter import code_digest
    from trialtrace.source import hash_source_pdf
    from trialtrace.workflow import check_uploads
    from trialtrace.comparison import load_report, compare_reports
    from trialtrace.inspection import inspect_uploads, build_worklist, build_input_issue_list

    installed_path = Path(trialtrace.__file__).resolve()
    environment = Path(sys.prefix).resolve()
    assert installed_path.is_relative_to(environment), installed_path
    assert not installed_path.is_relative_to(repo), installed_path
    schema = importlib.resources.files('trialtrace').joinpath('evidence_bundle.schema.json').read_bytes()
    assert schema == (repo/'contracts/evidence_bundle.schema.json').read_bytes()
    source_digest = hashlib.sha256()
    source_hashes = {}
    for path in sorted((repo/'src/trialtrace').glob('*.py')):
        raw = path.read_bytes()
        source_digest.update(path.name.encode() + b'\0' + raw + b'\0')
        source_hashes[path.name] = sha(raw)
        assert (installed_path.parent/path.name).read_bytes() == raw, path.name
    source_digest.update(schema)
    assert source_digest.hexdigest() == code_digest(), 'Installed core differs from current source'
    dependencies = {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}
    for line in lock_path.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        name, version = line.split('==', 1)
        assert importlib.metadata.version(name) == version, (name, version)

    source = hash_source_pdf(args.source_pdf) if args.source_pdf else None
    rule, rule_sha = load_rule(repo/'rules/candidate_rule.json')
    cases = []
    outputs = {}
    for name, status, outside, actual in [
        ('boundary', 'PASS', 0, '2040-03-03'),
        ('outside', 'POTENTIAL_DEVIATION', 1, '2040-03-04'),
        ('missing_anchor', 'DATA_QUERY', None, None),
    ]:
        folder = repo/'examples/browser'/name
        paths = {role: folder/role for role in ('anchors.csv', 'visits.csv', 'assignments.csv')}
        uploads = {role: (path.name, path.read_bytes()) for role, path in paths.items()}
        intake = inspect_uploads(uploads, rule, rule_sha)
        assert intake['ready_for_draft_check'] and intake['timing_evaluated'] is False
        assert [item['record_count'] for item in intake['files']] == ([0, 1, 1] if name == 'missing_anchor' else [1, 1, 1])
        bundle, encoded = check_uploads(uploads, rule, rule_sha, draft_confirmed=True, source_metadata=source)
        assert len(bundle['findings']) == 1
        finding = bundle['findings'][0]
        assert finding['status'] == status, finding
        expected_calc = None if actual is None else {
            'target': '2040-02-29', 'earliest': '2040-02-29', 'latest': '2040-03-03',
            'actual': actual, 'days_outside': outside,
        }
        assert finding['calculation'] == expected_calc, finding
        command = [sys.executable, '-I', '-m', 'trialtrace.cli', '--draft-synthetic']
        for role, path in paths.items():
            command += ['--'+role.removesuffix('.csv'), str(path)]
        target = run/(name+'-cli.json')
        command += ['--rule', str(repo/'rules/candidate_rule.json'), '--output', str(target)]
        if args.source_pdf:
            command += ['--source-pdf', str(args.source_pdf.resolve())]
        completed = subprocess.run(command, cwd=Path.cwd(), capture_output=True, timeout=30)
        (run/(name+'-cli.stdout.log')).write_bytes(completed.stdout)
        (run/(name+'-cli.stderr.log')).write_bytes(completed.stderr)
        command_result = {'command': command, 'cwd': str(Path.cwd()), 'exit_code': completed.returncode,
                          'stdout_sha256': sha(completed.stdout), 'stderr_sha256': sha(completed.stderr)}
        (run/(name+'-cli.command.json')).write_text(json.dumps(command_result, indent=2)+'\n')
        assert completed.returncode == 0, completed.stderr.decode()
        assert target.read_bytes() == encoded, name+' CLI/upload adapter bytes differ'
        assert json.loads(encoded) == bundle
        assert bundle['review_status'] == 'PENDING_TEAM_SOURCE_REVIEW'
        assert bundle['clinical_validation'] is False
        assert bundle['producer']['code_sha256'] == code_digest()
        assert load_report(encoded) == bundle
        review_rows = build_worklist(bundle)
        assert len(review_rows) == (0 if status == 'PASS' else 1)
        input_issues = build_input_issue_list(bundle)
        assert len(input_issues) == (1 if name == 'missing_anchor' else 0)
        if input_issues:
            assert input_issues[0]['code'] == 'MISSING_ANCHOR_ID'
        outputs[name] = encoded
        cases.append({'case': name, 'status': status, 'calculation': expected_calc,
                      'cli_exit_code': completed.returncode, 'cli_adapter_bytes_identical': True,
                      'intake_ready_without_timing': True, 'review_findings': len(review_rows), 'input_issues': len(input_issues),
                      'output_sha256': sha(encoded), 'input_sha256': {role: sha(path.read_bytes()) for role,path in paths.items()},
                      'command_record': str(run/(name+'-cli.command.json'))})

    comparison = compare_reports(load_report(outputs['boundary']), load_report(outputs['outside']))
    assert comparison['summary']['matched'] == comparison['summary']['changed'] == 1
    assert comparison['summary']['unmatched_before'] == comparison['summary']['unmatched_after'] == 0
    assert comparison['matched'][0]['changes']['status'] == {'before': 'PASS', 'after': 'POTENTIAL_DEVIATION'}

    # Confirm malformed bytes reach the installed parser, not a successful fixture fallback.
    folder = repo/'examples/browser/corrupt'
    uploads = {role: (role, (folder/role).read_bytes()) for role in ('anchors.csv','visits.csv','assignments.csv')}
    try:
        check_uploads(uploads, rule, rule_sha, draft_confirmed=True, source_metadata=source)
    except InputError as error:
        malformed_code = error.code
        assert malformed_code == 'INVALID_HEADER', error.diagnostic()
    else:
        raise AssertionError('Malformed replacement was accepted')

    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    from streamlit.testing.v1 import AppTest
    original_argv = sys.argv[:]
    try:
        sys.argv = [str(app_path)]
        if args.source_pdf:
            sys.argv += ['--source-pdf', str(args.source_pdf.resolve())]
        app = AppTest.from_file(app_path, default_timeout=30).run()
        assert not app.exception, [item.message for item in app.exception]
        assert len(app.file_uploader) == 5
        csv_uploaders = [uploader for uploader in app.file_uploader if uploader.label in ('anchors.csv', 'visits.csv', 'assignments.csv')]
        assert len(csv_uploaders) == 3
        assert {uploader.label for uploader in app.file_uploader} == {'anchors.csv', 'visits.csv', 'assignments.csv', 'Earlier report', 'Later report'}
        assert 'result' not in app.session_state
        assert next(button for button in app.button if button.label == 'Run timing check').disabled
        for uploader in csv_uploaders:
            role = uploader.label
            path = repo/'examples/browser/boundary'/role
            uploader.set_value((path.name, path.read_bytes(), 'text/csv'))
        app.run()
        assert not app.exception, [item.message for item in app.exception]
        app.checkbox(key='draft_confirmed').check().run()
        button = next(button for button in app.button if button.label == 'Run timing check')
        assert not button.disabled
        button.click().run()
        assert not app.exception, [item.message for item in app.exception]
        assert app.session_state['result_bytes'] == outputs['boundary'], 'App script bytes differ from installed CLI'
        assert [metric.value for metric in app.metric] == ['1','0','0','0']
        assert len([button for button in app.download_button if button.key == 'evidence_download']) == 1
        assert {button.key for button in app.download_button} >= {'intake_download', 'worklist_download', 'input_issues_download'}
        assert app.session_state['result']['findings'][0]['calculation']['target'] == '2040-02-29'
        # The real UI's explicit clear action retires stale results before replacement.
        next(button for button in app.button if button.label == 'Clear visits.csv').click().run()
        assert not app.exception, [item.message for item in app.exception]
        assert 'result' not in app.session_state and 'result_bytes' not in app.session_state
        assert not [button for button in app.download_button if button.key == 'evidence_download']
        assert next(button for button in app.button if button.label == 'Run timing check').disabled
    finally:
        sys.argv = original_argv

    assert sha(app_path.read_bytes()) == app_sha, 'App changed during this probe; rerun'
    assert sha(lock_path.read_bytes()) == lock_sha, 'Dependency lock changed during this probe; rerun'
    assert code_digest() == source_digest.hexdigest()
    imported_modules = {name: module.__file__ for name,module in sys.modules.items()
                        if name.startswith('trialtrace') and getattr(module, '__file__', None)}
    assert all(Path(path).resolve().is_relative_to(environment) for path in imported_modules.values()), imported_modules
    assert str(repo/'src') not in sys.path
    result = {
        'status': 'PASS', 'run_id': run_id,
        'scope': 'Fresh venv and regular installed wheel on this same machine. AppTest is not a browser/network test.',
        'python': sys.version, 'platform': platform.platform(), 'executable': sys.executable,
        'cwd': str(Path.cwd()), 'isolated': sys.flags.isolated, 'installed_module': str(installed_path),
        'installed_modules': imported_modules, 'code_sha256': code_digest(), 'source_files_sha256': source_hashes,
        'schema_sha256': sha(schema), 'app_sha256': app_sha, 'requirements_ui_lock_sha256': lock_sha,
        'rule_sha256': rule_sha, 'source_metadata': source, 'dependencies': dependencies,
        'cases': cases, 'malformed_upload_rejection': malformed_code,
        'comparison': comparison['summary'],
        'app_test': {'actual_script': str(app_path), 'uploads': 3, 'draft_confirmed': True,
                     'initial_upload_slots': 5, 'csv_slots_selected_by_role': True,
                     'findings_status': 'PASS', 'metrics': ['1','0','0','0'], 'bytes_match_cli': True,
                     'clear_retires_report_and_download': True, 'app_exceptions': 0,
                     'classification': 'IN_PROCESS_APPTEST_NOT_BROWSER'},
        'limitations': ['Not a second-machine reproduction.', 'No human source review or clinical validation.',
                        'Main browser/server checks are recorded separately.'],
    }
    text = json.dumps(result, indent=2)+'\n'
    (run/'result.json').write_text(text)
    (output/'result.json').write_text(text)
    print(text, end='')


if __name__ == '__main__':
    main()
