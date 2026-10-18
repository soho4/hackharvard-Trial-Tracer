"""Browser boundary to the unchanged TrialTrace Python core. Inputs are data only."""
import base64
import hashlib
import json
from pathlib import Path
from trialtrace.cli import load_rule
from trialtrace.errors import InputError
from trialtrace.exporter import code_digest
from trialtrace.inspection import build_worklist, worklist_csv, build_input_issue_list
from trialtrace.preparation import FIELDS, inspect_spreadsheet, prepare_spreadsheet, evidence_package

RULE_PATH = Path('/trialtrace-runtime/candidate_rule.json')


def handle(payload, rule_path=None):
    try:
        raw = base64.b64decode(payload['bytes'], validate=True)
        name = payload.get('name', 'source.csv')
        sheet = inspect_spreadsheet(raw, name)
        if payload['action'] == 'inspect':
            return {'headers': sheet['headers'], 'records': sheet['records'], 'byte_count': len(raw),
                    'sha256': sheet['sha256'], 'fields': FIELDS}
        if payload['action'] != 'run':
            raise InputError('ACTION', 'Unsupported action')
        rule, rule_hash = load_rule(rule_path or RULE_PATH)
        prepared = prepare_spreadsheet(raw, name, payload['mapping'], payload['completed_value'],
                                       rule, rule_hash, scope_confirmed=payload.get('confirmed') is True)
        bundle, encoded, package = evidence_package(prepared, rule, rule_hash)
        return {'bundle': bundle, 'manifest': prepared['manifest'], 'original': sheet['records'],
                'worklist': build_worklist(bundle, include_pass=True),
                'input_issues': build_input_issue_list(bundle),
                'downloads': {'json': base64.b64encode(encoded).decode(),
                              'zip': base64.b64encode(package).decode(),
                              'csv': base64.b64encode(worklist_csv(bundle)).decode()},
                'code_sha256': code_digest(), 'report_sha256': hashlib.sha256(encoded).hexdigest()}
    except InputError as exc:
        return {'error': exc.diagnostic()}
    except (KeyError, ValueError, TypeError) as exc:
        return {'error': {'code': 'REQUEST_FORMAT', 'message': 'The supplied file or mapping request is incomplete or invalid.'}}


def handle_json(payload_json):
    return json.dumps(handle(json.loads(payload_json)), ensure_ascii=False)
