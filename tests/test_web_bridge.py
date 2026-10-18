"""Exercise the browser boundary against canonical evidence and adversarial input."""
import base64
import importlib.util
import io
import json
from pathlib import Path
import zipfile
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('web_bridge', ROOT/'web/src/bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
RULE = ROOT/'rules/candidate_rule.json'
RAW = (ROOT/'examples/preparation/synthetic-wide.csv').read_bytes()
PROFILE = json.loads((ROOT/'examples/preparation/mapping.json').read_bytes())

def request(raw=RAW, **changes):
    payload = {'action':'run','name':'synthetic-wide.csv','bytes':base64.b64encode(raw).decode(),
               'mapping':PROFILE['columns'].copy(),'completed_value':PROFILE['completed_value'],'confirmed':True}
    payload.update(changes)
    return bridge.handle(payload, RULE)

def test_exact_canonical_evidence_and_source_preservation():
    result=request()
    encoded=base64.b64decode(result['downloads']['json'])
    assert encoded==(ROOT/'docs/trialtrace/review/preparation/actual_run/evidence.json').read_bytes()
    assert result['bundle']['summary']['statuses']=={'PASS':1,'POTENTIAL_DEVIATION':1,'DATA_QUERY':4,'NOT_EVALUABLE':1}
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(result['downloads']['zip']))) as actual, zipfile.ZipFile(ROOT/'docs/trialtrace/review/preparation/actual_run/evidence-package.zip') as expected:
        assert sorted(actual.namelist())==sorted(expected.namelist())
        for name in actual.namelist(): assert actual.read(name)==expected.read(name)

def test_changed_input_recalculates_and_changes_evidence_identity():
    original=request(); changed=request(RAW.replace(b'2028-03-04',b'2028-03-05'))
    assert original['bundle']['findings'][1]['calculation']['days_outside']==1
    assert changed['bundle']['findings'][1]['calculation']['days_outside']==2
    assert original['report_sha256']!=changed['report_sha256']

@pytest.mark.parametrize('confirmed',[False,None,1,'true'])
def test_scope_requires_true_boolean(confirmed):
    result=request(confirmed=confirmed)
    assert result['error']['code']=='PREPARATION_SCOPE'
    assert 'bundle' not in result

def test_missing_date_and_conflicts_never_receive_calculations():
    result=request()
    for i in (2,3,5,6):
        assert result['bundle']['findings'][i]['status']=='DATA_QUERY'
        assert result['bundle']['findings'][i]['calculation'] is None

def test_invalid_calendar_date_preserved_without_calculation():
    result=request(RAW.replace(b'2028-03-04',b'2028-02-30'))
    assert result['original'][1]['raw_record']['phone_actual']=='2028-02-30'
    assert result['bundle']['findings'][1]['status']=='DATA_QUERY'
    assert result['bundle']['findings'][1]['calculation'] is None

def test_invalid_base64_and_incomplete_mapping_no_fallback():
    assert request(bytes='!!!!')['error']['code']=='REQUEST_FORMAT'
    assert request(mapping={})['error']['code']=='COLUMN_MAPPING'

def test_inspection_preserves_literal_formula_like_identifier():
    result=request(action='inspect')
    assert result['records'][0]['raw_record']['subject_ref']=='=SYNTH-PREP-01'
    assert 'bundle' not in result
