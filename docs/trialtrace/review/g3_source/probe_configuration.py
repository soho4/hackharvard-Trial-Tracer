"""Read-only AppTest probes; rule mutations are in-memory mocks, never production writes."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[3]
REPO = BASE / 'work/TrialTrace'
sys.path.insert(0, str(REPO / 'src'))
from streamlit.testing.v1 import AppTest
from trialtrace.cli import load_rule
from trialtrace.engine import validate_rule
from trialtrace.workflow import check_uploads

sys.argv = [str(REPO / 'app.py')]
rule, original_hash = load_rule(REPO / 'rules/candidate_rule.json')
uploads = {
    'anchors.csv': ('synthetic-anchors.csv', b'study_id,participant_id,site_id,anchor_id,anchor_code,anchor_kind,anchor_date\nNCT04470427,synthetic-review-1,synthetic-site,A,OL_D1,ACTUAL_VACCINATION,2026-11-01\n'),
    'visits.csv': ('synthetic-visits.csv', b'study_id,participant_id,site_id,visit_id,visit_code,event_kind,actual_date,visit_status,anchor_id,assignment_id\nNCT04470427,synthetic-review-1,synthetic-site,V,OL_D8,SAFETY_PHONE_CALL,2026-11-10,COMPLETED,A,M\n'),
    'assignments.csv': ('synthetic-assignments.csv', b'assignment_id,study_id,participant_id,site_id,rule_version,schedule_code,mapping_status,mapping_note\nM,NCT04470427,synthetic-review-1,synthetic-site,A10_DRAFT_2,TABLE21,DRAFT_SYNTHETIC,Independent synthetic configuration probe\n'),
}
result = {'started_at_utc': datetime.now(timezone.utc).isoformat(), 'kind': 'READ_ONLY_COMPONENT_PROBE_NOT_BROWSER_E2E', 'source_files_at_start': {name: hashlib.sha256((REPO/name).read_bytes()).hexdigest() for name in ('app.py','src/trialtrace/engine.py','src/trialtrace/workflow.py')}}
with patch('trialtrace.cli.load_rule', return_value=({}, '0'*64)):
    app = AppTest.from_file(REPO / 'app.py', default_timeout=15).run()
    result['missing_fields'] = {'exceptions': [str(e.message) for e in app.exception], 'errors':[e.value for e in app.error], 'has_result': 'result' in app.session_state}
changed = copy.deepcopy(rule)
changed['offset_days'], changed['lower_days'], changed['upper_days'] = 0,0,0
changed_hash = hashlib.sha256(json.dumps(changed).encode()).hexdigest()
validate_rule(changed)
with patch('trialtrace.cli.load_rule', return_value=(changed, changed_hash)):
    app = AppTest.from_file(REPO / 'app.py', default_timeout=15).run()
    for role,(name,raw) in uploads.items():
        next(u for u in app.file_uploader if u.label == role).set_value((name,raw,'text/csv'))
    app.run()
    app.checkbox(key='draft_confirmed').check().run()
    next(b for b in app.button if b.label == 'Run timing check').click().run()
    result['accepted_changed_offsets'] = {'exceptions': [str(e.message) for e in app.exception], 'window_text':[m.value for m in app.markdown if 'Candidate window' in m.value], 'calculation':app.session_state['result']['findings'][0]['calculation'],'status':app.session_state['result']['findings'][0]['status']}
result['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
result['source_files_at_end'] = {name: hashlib.sha256((REPO/name).read_bytes()).hexdigest() for name in result['source_files_at_start']}
result['source_changed_during_probe'] = result['source_files_at_start'] != result['source_files_at_end']
assert not result['missing_fields']['exceptions']
assert result['missing_fields']['errors']
assert not result['missing_fields']['has_result']
assert not result['accepted_changed_offsets']['exceptions']
assert any('+0 through +0' in text for text in result['accepted_changed_offsets']['window_text'])
assert result['accepted_changed_offsets']['calculation']['days_outside'] == 9
assert not result['source_changed_during_probe']
print(json.dumps(result, indent=2))
