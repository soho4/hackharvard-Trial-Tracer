#!/usr/bin/env python3
"""Package exact core sources with a static browser interface; never rewrite rules."""
from pathlib import Path
import hashlib, json, shutil, zipfile
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'web/dist'
DEST.mkdir(parents=True,exist_ok=True)
for p in (ROOT/'web/src').iterdir():
    if p.is_file(): shutil.copy2(p,DEST/p.name)
files={}
for p in sorted((ROOT/'src/trialtrace').glob('*.py')): files['trialtrace/'+p.name]=p
files['trialtrace/evidence_bundle.schema.json']=ROOT/'contracts/evidence_bundle.schema.json'
files['candidate_rule.json']=ROOT/'rules/candidate_rule.json'
with zipfile.ZipFile(DEST/'engine.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
    for name,p in sorted(files.items()):
        item=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0)); item.compress_type=zipfile.ZIP_DEFLATED
        archive.writestr(item,p.read_bytes())
for name in ('synthetic-wide.csv','mapping.json'):
    shutil.copy2(ROOT/'examples/preparation'/name,DEST/name)
(DEST/'changed-date.csv').write_bytes((ROOT/'examples/preparation/synthetic-wide.csv').read_bytes().replace(b'2028-03-04',b'2028-03-05'))
shutil.copy2(ROOT/'rules/candidate_rule.json',DEST/'candidate_rule.json')
vendor=ROOT/'web/vendor/pyodide'
if not (vendor/'pyodide.js').is_file(): raise SystemExit('Run tools/vendor_web_runtime.py before building')
lock=json.loads((ROOT/'web/runtime-lock.json').read_bytes())
for name, expected in lock['files'].items():
    raw=(vendor/name).read_bytes()
    if len(raw)!=expected['bytes'] or hashlib.sha256(raw).hexdigest()!=expected['sha256']:
        raise SystemExit('Runtime hash mismatch: '+name)
shutil.copytree(vendor,DEST/'pyodide',dirs_exist_ok=True)
shutil.copy2(ROOT/'web/runtime-lock.json',DEST/'runtime-lock.json')
from trialtrace.exporter import code_digest
manifest={'engine_code_sha256':code_digest(),'rule_sha256':hashlib.sha256((DEST/'candidate_rule.json').read_bytes()).hexdigest(),
          'pyodide_version':'314.0.7','source_files':{name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in files.items()},
          'web_source_files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'web/src').iterdir()) if p.is_file()},
          'scope':'Browser interface to unchanged Python engine. Synthetic draft only.'}
(DEST/'build-info.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'output':str(DEST),'engine_code_sha256':manifest['engine_code_sha256']}))
