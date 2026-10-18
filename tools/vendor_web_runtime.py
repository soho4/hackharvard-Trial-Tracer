#!/usr/bin/env python3
"""Fetch pinned official Pyodide assets over verified TLS; check wheel lock hashes."""
from pathlib import Path
import concurrent.futures,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'web/vendor/pyodide'; OUT.mkdir(parents=True,exist_ok=True)
BASE='https://cdn.jsdelivr.net/pyodide/v314.0.7/full/'
prior_path=ROOT/'web/runtime-lock.json'
prior=json.loads(prior_path.read_bytes()) if prior_path.is_file() else {}
if prior and prior.get('base_url')!=BASE: raise SystemExit('Runtime version changed: explicitly review and refresh the lock first')
def fetch(name, expected=None):
    expected=expected or prior.get('files',{}).get(name,{}).get('sha256')
    dest=OUT/name
    if dest.exists() and (not expected or hashlib.sha256(dest.read_bytes()).hexdigest()==expected):
        return name
    raw=subprocess.check_output(['curl','--fail','--silent','--show-error','--retry','2',BASE+name])
    if expected and hashlib.sha256(raw).hexdigest()!=expected: raise ValueError('Hash mismatch: '+name)
    dest.write_bytes(raw); return name
fetch('pyodide-lock.json')
lock=json.loads((OUT/'pyodide-lock.json').read_bytes()); packages={}
def include(name):
    key=name if name in lock['packages'] else name.replace('_','-')
    if key in packages:return
    p=lock['packages'][key];packages[key]=p
    for d in p['depends']:include(d)
include('jsonschema')
jobs=[(n,None) for n in ('pyodide.js','pyodide.mjs','pyodide.asm.mjs','pyodide.asm.wasm','python_stdlib.zip')]
jobs += [(p['file_name'],p['sha256']) for p in packages.values()]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    list(pool.map(lambda pair:fetch(*pair),jobs))
manifest={'version':'314.0.7','base_url':BASE,'info':lock['info'],'packages':{k:p['version'] for k,p in packages.items()},'files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.iterdir()) if p.is_file()}}
(ROOT/'web/runtime-lock.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'version':manifest['version'],'files':len(manifest['files']),'bytes':sum(x['bytes'] for x in manifest['files'].values())}))
