"""Inspect CSV structures and relationships without evaluating a timing rule."""

import argparse
import json
from pathlib import Path

from .errors import InputError
from .importer import load_inputs
from .relationships import inspect_inputs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for role in ("anchors", "visits", "assignments"):
        ap.add_argument("--" + role, type=Path, required=True)
    args = ap.parse_args()
    try:
        tables = load_inputs({name + ".csv": getattr(args, name) for name in ("anchors", "visits", "assignments")})
        inspected = inspect_inputs(tables)
        result = {"stage": "IMPORT_ONLY_NO_TIMING", "tables": tables, "input_accounting": inspected["input_accounting"], "visit_evaluations": len(inspected["visits"])}
        print(json.dumps(result, indent=2))
        return 0
    except InputError as exc:
        print(json.dumps({"status": "FAILED", "diagnostic": exc.diagnostic()}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
