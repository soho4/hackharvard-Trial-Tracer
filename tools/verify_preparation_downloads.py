#!/usr/bin/env python3
"""Verify artifacts actually downloaded by browser; does not simulate UI actions."""
import hashlib
import json
from pathlib import Path
import zipfile
from trialtrace.exporter import code_digest
from trialtrace.inspection import worklist_csv

ROOT = Path(__file__).resolve().parents[1]
review = ROOT / 'docs/trialtrace/review/preparation'
browser, actual = review/'browser', review/'actual_run'
source = (ROOT/'examples/preparation/synthetic-wide.csv').read_bytes()
evidence = (browser/'browser-evidence.json').read_bytes()
bundle = json.loads(evidence)
assert evidence == (actual/'evidence.json').read_bytes()
assert (browser/'browser-package.zip').read_bytes() == (actual/'evidence-package.zip').read_bytes()
assert (browser/'browser-review.csv').read_bytes() == worklist_csv(bundle)
with zipfile.ZipFile(browser/'browser-package.zip') as archive:
    assert archive.testzip() is None
    assert archive.read('source.csv') == source
    assert archive.read('evidence.json') == evidence
    manifest = json.loads(archive.read('preparation.json'))
    assert manifest['source_record_count'] == 7
    assert manifest['unmapped_columns'] == ['operator_note']
    assert manifest['report_sha256'] == hashlib.sha256(evidence).hexdigest()
    for name, description in manifest['generated_files'].items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == description['sha256']
expected = json.loads((ROOT/'examples/preparation/expected.json').read_bytes())
assert [f['status'] for f in bundle['findings']] == expected['statuses']
assert bundle['findings'][1]['calculation'] == expected['second_calculation']
assert bundle['producer']['code_sha256'] == code_digest()
clean = json.loads((review/'clean_install/result.json').read_bytes())
assert clean['status'] == 'PASS'
assert clean['code_sha256'] == code_digest()
assert clean['app_sha256'] == hashlib.sha256((ROOT/'app.py').read_bytes()).hexdigest()
assert clean['spreadsheet_preparation']['evidence_sha256'] == hashlib.sha256(evidence).hexdigest()
result = {'status':'PASS_ARTIFACT_PARITY', 'code_sha256':code_digest(), 'app_sha256':clean['app_sha256'],
          'browser_report_matches_installed_cli_bytes':True, 'browser_package_matches_actual_file_bytes':True,
          'browser_review_matches_full_derived_csv_bytes':True, 'original_source_bytes_preserved':True,
          'fresh_environment_matches_report':True, 'counts':expected['counts'],
          'download_sha256':{name:hashlib.sha256((browser/name).read_bytes()).hexdigest()
                             for name in ('browser-evidence.json','browser-package.zip','browser-review.csv')},
          'limitations':['Actual UI actions and upload failures are separately recorded in events.json and console.json.',
                         'Synthetic example, no actual vendor-export or participant-data validation.']}
(browser/'result.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
