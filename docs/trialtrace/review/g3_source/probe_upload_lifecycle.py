"""Focused read-only component probes, not a served-browser test."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[3]
REPO = BASE / 'work/TrialTrace'
sys.path.insert(0, str(REPO / 'src'))
sys.argv = [str(REPO / 'app.py')]
from streamlit.testing.v1 import AppTest
from trialtrace.importer import HEADERS, parse_table

FILES = ('app.py','src/trialtrace/importer.py','src/trialtrace/workflow.py','src/trialtrace/source.py','src/trialtrace/cli.py')
def fingerprints():
    return {n:hashlib.sha256((REPO/n).read_bytes()).hexdigest() for n in FILES}

def current_download(app):
    return any(b.key == 'evidence_download' for b in app.download_button)

def no_report(app):
    assert not app.exception
    assert 'result' not in app.session_state
    assert 'result_bytes' not in app.session_state
    assert not current_download(app)
    assert not app.metric

result={'kind':'READ_ONLY_COMPONENT_AND_DIRECT_API_PROBE_NOT_BROWSER_E2E','started_at_utc':datetime.now(timezone.utc).isoformat(),'files_start':fingerprints(),'checks':[]}
app=AppTest.from_file(REPO/'app.py',default_timeout=15).run()
assert not app.exception
for role in HEADERS:
    raw=(','.join(HEADERS[role])+'\n').encode()
    next(u for u in app.file_uploader if u.label==role).set_value((role,raw,'text/csv'))
app.run()
assert len(app.file_uploader)==0
assert len([b for b in app.button if b.label.startswith('Clear ')])==3
assert all(app.session_state['selected_upload_'+role][1] == (','.join(HEADERS[role])+'\n').encode() for role in HEADERS)
app.checkbox(key='draft_confirmed').check().run()
next(b for b in app.button if b.label=='Run timing check').click().run()
assert current_download(app)
assert json.loads(app.session_state['result_bytes']) == app.session_state['result']
result['checks'].append({'check':'first uploads persist; explicit run publishes original computed bytes','outcome':'PASS'})
app.button(key='clear_visits.csv').click().run()
no_report(app)
assert len(app.file_uploader)==1
assert app.file_uploader[0].key=='upload_visits.csv_1'
assert next(b for b in app.button if b.label=='Run timing check').disabled
result['checks'].append({'check':'clear removes report and download before a replacement chooser exists','outcome':'PASS'})
for index,(raw,code) in enumerate([(b'\xff','INVALID_UTF8'),(b'x'*1000001,'INPUT_SIZE_LIMIT')]):
    app.file_uploader[0].set_value(('replacement.csv',raw,'text/csv')).run()
    no_report(app)
    next(b for b in app.button if b.label=='Run timing check').click().run()
    no_report(app)
    assert app.session_state['check_error']['code']==code
    app.run()
    no_report(app)
    assert app.session_state['check_error']['code']==code
    result['checks'].append({'check':code+' replacement; persistent error without old report or download','outcome':'PASS','bytes':len(raw)})
    app.button(key='clear_visits.csv').click().run()
    no_report(app)
role='anchors.csv'
name='../../<script>alert(1)</script>\\fake\x00\n\r\u202e.csv'
parsed=parse_table((','.join(HEADERS[role])+'\n').encode(),role,name)
assert parsed['name']==role
assert parsed['display_name']=='../../<script>alert(1)</script>\\fake.csv'
assert len(parsed['display_name'])<=200
result['checks'].append({'check':'untrusted display filename remains metadata only, canonical evidence role retained, controls removed','outcome':'PASS','display_name':parsed['display_name']})
result['files_end']=fingerprints()
assert result['files_start']==result['files_end']
result['finished_at_utc']=datetime.now(timezone.utc).isoformat()
print(json.dumps(result,indent=2))
