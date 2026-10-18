"""Run with a separate environment's Python -I, outside the source checkout."""

import argparse
import hashlib
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import platform
import subprocess
import sys

import trialtrace
from trialtrace.exporter import code_digest


ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--repo", type=Path, required=True)
ap.add_argument("--source-pdf", type=Path, required=True)
args = ap.parse_args()
repo = args.repo.resolve()
assert not Path(trialtrace.__file__).resolve().is_relative_to(repo), "Must exercise installed package outside checkout"
schema = importlib.resources.files("trialtrace").joinpath("evidence_bundle.schema.json").read_bytes()
assert schema == (repo / "contracts/evidence_bundle.schema.json").read_bytes()
source = hashlib.sha256()
for path in sorted((repo / "src/trialtrace").glob("*.py")):
    source.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
source.update(schema)
assert source.hexdigest() == code_digest(), "Installed Python/schema bytes differ from current source"
folder = repo / "examples/execution/before"
output = repo / "examples/execution/clean_install_bundle.json"
command = [sys.executable, "-I", "-m", "trialtrace.cli", "--draft-synthetic"]
for name in ("anchors", "visits", "assignments"):
    command += ["--" + name, str(folder / (name + ".csv"))]
command += ["--rule", str(repo / "rules/candidate_rule.json"), "--source-pdf", str(args.source_pdf.resolve()), "--output", str(output)]
result = subprocess.run(command, cwd=Path.cwd(), text=True, capture_output=True, timeout=30)
print(result.stdout, end="")
print(result.stderr, end="", file=sys.stderr)
assert result.returncode == 0, result.returncode
assert output.read_bytes() == (folder / "bundle.json").read_bytes(), "Clean installed CLI changed the exact report bytes"
record = {"status": "PASS", "scope": "Fresh venv and wheel on this machine; no claim of another-machine or browser validation", "python": sys.version,
          "platform": platform.platform(), "executable": sys.executable, "imported_module": trialtrace.__file__, "isolated": sys.flags.isolated,
          "code_sha256": code_digest(), "schema_sha256": hashlib.sha256(schema).hexdigest(), "byte_identical_cli_output": True,
          "cli_exit_code": result.returncode, "command": command,
          "dependencies": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}}
(repo / "docs/trialtrace/clean_install.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
