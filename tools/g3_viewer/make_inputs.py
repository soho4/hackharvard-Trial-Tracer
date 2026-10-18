#!/usr/bin/env python3
"""Make independent early-year CSVs, then execute the real CLI and assert literal results."""
from pathlib import Path
import csv
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/trialtrace/review/g3_viewer/inputs'
sys.path.insert(0, str(ROOT / 'tools'))
from record_command import run_record

cases = [
    ('early0001', '0001-01-01', '0001-01-11', '0001-01-08', '0001-01-11', 'PASS', 0),
    ('leap0004', '0004-02-19', '0004-02-29', '0004-02-26', '0004-02-29', 'PASS', 0),
    ('early0099', '0099-12-20', '0099-12-31', '0099-12-27', '0099-12-30', 'POTENTIAL_DEVIATION', 1),
]
results = []
for case, anchor, actual, target, latest, status, outside in cases:
    directory = OUT / case
    directory.mkdir(parents=True, exist_ok=True)
    for role in ('anchors', 'visits', 'assignments'):
        with (ROOT / 'examples/execution/before' / f'{role}.csv').open(newline='') as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            rows = list(reader)
        for row in rows:
            for key, value in row.items():
                if value.startswith('SYNTH-'):
                    row[key] = value + '-' + case
            if role == 'anchors': row['anchor_date'] = anchor
            if role == 'visits': row['actual_date'] = actual
        with (directory / f'{role}.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    command = [sys.executable, '-m', 'trialtrace.cli']
    for role in ('anchors', 'visits', 'assignments'):
        command += ['--' + role, str(directory / f'{role}.csv')]
    command += ['--rule', str(ROOT / 'rules/candidate_rule.json'), '--draft-synthetic', '--output', str(directory / 'bundle.json')]
    # Use the current source deliberately; the command log records this choice.
    command = ['env', 'PYTHONPATH=' + str(ROOT / 'src')] + command
    record, log = run_record(command, ROOT, ROOT/'docs/trialtrace/review/g3_viewer/commands', case)
    assert record['exit_code'] == 0, record
    bundle = json.loads((directory/'bundle.json').read_text())
    assert len(bundle['findings']) == 1
    finding = bundle['findings'][0]
    expected = {'target': target, 'earliest': target, 'latest': latest, 'actual': actual, 'days_outside': outside}
    assert finding['status'] == status, finding
    assert finding['calculation'] == expected, finding
    results.append({'case': case, 'expected_status': status, 'actual_status': finding['status'], 'expected_calculation': expected, 'actual_calculation': finding['calculation'], 'command_record': str(log.relative_to(ROOT)/'record.json')})

OUT.mkdir(parents=True, exist_ok=True)
mixed = json.loads((ROOT/'tools/g3_viewer/native_snapshot/fixtures/mixed.json').read_text())
mixed['schema_version'] = 'trialtrace.evidence.future'
(OUT/'unknown_schema.json').write_text(json.dumps(mixed)+'\n')
(OUT/'oversized.json').write_bytes(b' ' * 2_000_001)
(OUT/'broken.json').write_text('{"schema_version":')
(OUT/'engine_results.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps({'real_cli_cases': len(results), 'assertions': 'passed', 'results': results}))
