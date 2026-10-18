#!/usr/bin/env python3
"""Record an actual subprocess and preserve failures; not a gate, sandbox or secret scrubber.

Example: python tools/record_command.py --label importer-tests --out .local-evidence \
  --cwd . -- python -m pytest tests/test_importer.py -q
Do not put credentials in commands or log secret-producing operations.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid


def run_record(command: list[str], cwd: Path, out: Path, label: str, timeout: float = 300) -> tuple[dict, Path]:
    if not command:
        raise ValueError('A real command is required.')
    if timeout <= 0:
        raise ValueError('Timeout must be positive.')
    cwd = cwd.resolve()
    if not cwd.is_dir():
        raise ValueError('Working directory does not exist.')
    safe_label = re.sub(r'[^A-Za-z0-9_.-]+', '-', label).strip('.-') or 'command'
    started = datetime.now(timezone.utc)
    folder = out.resolve() / (started.strftime('%Y%m%dT%H%M%S.%fZ') + '-' + safe_label[:60] + '-' + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    stdout_path, stderr_path = folder/'stdout.log', folder/'stderr.log'
    status, exit_code = 'EXECUTED', None
    with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
        try:
            result = subprocess.run(command, cwd=cwd, stdout=stdout, stderr=stderr, timeout=timeout, check=False)
            exit_code = result.returncode
            status = 'EXIT_ZERO' if exit_code == 0 else 'EXIT_NONZERO'
        except subprocess.TimeoutExpired:
            status, exit_code = 'TIMEOUT', 124
            stderr.write(b'\nRecorder timeout: the direct subprocess was terminated. Inspect any child processes separately.\n')
        except OSError as exc:
            status, exit_code = 'COULD_NOT_START', 127
            stderr.write((type(exc).__name__ + ': ' + str(exc) + '\n').encode())
    record = {
        'label':label, 'command':command, 'cwd':str(cwd), 'started_at':started.isoformat(),
        'finished_at':datetime.now(timezone.utc).isoformat(), 'elapsed_seconds':round(time.monotonic()-start,6),
        'status':status, 'exit_code':exit_code,
        'stdout_path':str(stdout_path), 'stderr_path':str(stderr_path),
        'stdout_sha256':hashlib.sha256(stdout_path.read_bytes()).hexdigest(),
        'stderr_sha256':hashlib.sha256(stderr_path.read_bytes()).hexdigest(),
        'gate_acceptance': 'NOT_DETERMINED_BY_COMMAND_RECORDER',
        'warning':'Logs are not tamper-proof; this does not establish test assertions, source review, or clinical validity.'}
    (folder/'record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    return record, folder


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--label',required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--cwd',type=Path,default=Path.cwd())
    ap.add_argument('--timeout',type=float,default=300)
    ap.add_argument('command',nargs=argparse.REMAINDER)
    args=ap.parse_args()
    cmd=args.command[1:] if args.command[:1]==['--'] else args.command
    try:
        record, folder=run_record(cmd,args.cwd,args.out,args.label,args.timeout)
    except (ValueError,OSError) as exc:
        print(json.dumps({'status':'RECORDER_ERROR','error':str(exc)}),file=sys.stderr)
        return 2
    print(json.dumps({'record':str(folder/'record.json'),'status':record['status'],'exit_code':record['exit_code']}))
    code=int(record['exit_code'])
    return code if 0<=code<=255 else 1

if __name__=='__main__':
    raise SystemExit(main())
