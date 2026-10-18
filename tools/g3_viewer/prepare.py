#!/usr/bin/env python3
"""Export the teammate feature without altering it; prepare a focused date fix."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
DEST = Path(__file__).resolve().parent
REF = "1b216519e93866bca3fc36be174ec0f5bf05f793"
PREFIX = "features/evidence_viewer/"
files = subprocess.check_output(
    ["git", "ls-tree", "-r", "--name-only", REF, PREFIX], cwd=ROOT, text=True
).splitlines()
manifest = {}
for name in files:
    raw = subprocess.check_output(["git", "show", f"{REF}:{name}"], cwd=ROOT)
    relative = name.removeprefix(PREFIX)
    manifest[relative] = hashlib.sha256(raw).hexdigest()
    for tree in ("native_snapshot", "candidate"):
        output = DEST / tree / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(raw)

native = (DEST / "native_snapshot/contract.js").read_text()
old = "    const date = new Date(Date.UTC(y, m - 1, d));\n"
replacement = (
    "    if (y < 1) return false;\n"
    "    // Date.UTC maps years 0..99 to 1900..1999; setUTCFullYear preserves the supplied year.\n"
    "    const date = new Date(0);\n"
    "    date.setUTCFullYear(y, m - 1, d);\n"
)
assert native.count(old) == 1
candidate = native.replace(old, replacement)
(DEST / "candidate/contract.js").write_text(candidate)
patch = "".join(difflib.unified_diff(
    native.splitlines(keepends=True), candidate.splitlines(keepends=True),
    fromfile="a/features/evidence_viewer/contract.js", tofile="b/features/evidence_viewer/contract.js"
))
(DEST / "calendar_date_fix.patch").write_text(patch)
native_style = (DEST / "native_snapshot/style.css").read_text()
style_anchor = '.finding.selected { border-color: var(--accent); box-shadow: inset 3px 0 0 var(--accent); }\n'
assert native_style.count(style_anchor) == 1
candidate_style = native_style.replace(style_anchor, style_anchor + '#runId, .finding > span, .status, #errorFile { overflow-wrap: anywhere; min-width: 0; }\n')
(DEST / 'candidate/style.css').write_text(candidate_style)
style_patch = ''.join(difflib.unified_diff(
    native_style.splitlines(keepends=True), candidate_style.splitlines(keepends=True),
    fromfile='a/features/evidence_viewer/style.css', tofile='b/features/evidence_viewer/style.css'
))
(DEST / 'layout_overflow_fix.patch').write_text(style_patch)
(DEST / 'integration_fixes.patch').write_text(patch + style_patch)
result = {
    "upstream_commit": REF,
    "upstream_path": PREFIX,
    "native_files_sha256": manifest,
    "candidate_changes": ["contract.js:isCalendarDate only", "style.css:wrap long run/finding IDs and filenames"],
    "candidate_contract_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
    "patch_sha256": hashlib.sha256(patch.encode()).hexdigest(),
    "candidate_style_sha256": hashlib.sha256(candidate_style.encode()).hexdigest(),
    "layout_patch_sha256": hashlib.sha256(style_patch.encode()).hexdigest(),
    "scope": "Isolated review copies; no teammate file was modified by prepare.py.",
}
(DEST / "provenance.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"copied_files": len(files), "upstream": REF, "candidate_changes": result["candidate_changes"]}))
