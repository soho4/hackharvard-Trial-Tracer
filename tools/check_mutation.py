"""Make a real arithmetic error in an isolated copy and require assertion failure."""

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

from record_command import run_record


def main():
    repo = Path(__file__).resolve().parents[1]
    evidence = repo / "docs/trialtrace/mutation"
    evidence.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="trialtrace-mutation-") as directory:
        copy = Path(directory)
        for name in ("src", "tests", "rules", "fixtures", "contracts"):
            shutil.copytree(repo / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        shutil.copyfile(repo / "pyproject.toml", copy / "pyproject.toml")
        engine = copy / "src/trialtrace/engine.py"
        original = engine.read_bytes()
        before = b"latest = target + timedelta(days=upper_days)"
        after = b"latest = target + timedelta(days=upper_days + 1)"
        assert original.count(before) == 1, "Mutation target must be unique"
        engine.write_bytes(original.replace(before, after))
        record, folder = run_record([sys.executable, "-m", "pytest", "tests/test_engine.py", "-k", "inclusive_boundaries_and_outside_distance", "-q"], copy, repo / "docs/trialtrace/commands", "g2-arithmetic-mutation")
        stdout = (folder / "stdout.log").read_text()
        detected = record["exit_code"] == 1 and "AssertionError" in stdout and "5 failed" in stdout and "ImportError" not in stdout and "SyntaxError" not in stdout
        result = {"status": "MUTATION_DETECTED_BY_ASSERTIONS" if detected else "FAIL", "mutation": {"from": before.decode(), "to": after.decode()}, "original_engine_sha256": hashlib.sha256(original).hexdigest(), "mutant_engine_sha256": hashlib.sha256(engine.read_bytes()).hexdigest(), "command_record": str(folder / "record.json"), "exit_code": record["exit_code"], "expected": "Five boundary calculation assertions fail, exit 1; no syntax/import failure", "observed_assertion_failure": detected, "implementation_unchanged": (repo / "src/trialtrace/engine.py").read_bytes() == original}
        (evidence / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return 0 if detected and result["implementation_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
