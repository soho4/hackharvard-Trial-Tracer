"""Run one explicit draft synthetic timing check on three actual CSV files."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid

from .errors import InputError
from .exporter import build_bundle, serialize_bundle
from .importer import load_inputs


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise InputError("CLI_ARGUMENTS", message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("DUPLICATE_JSON_KEY", "Rule JSON contains a duplicate key", key=key)
        result[key] = value
    return result


def load_rule(path):
    with path.open("rb") as stream:
        raw = stream.read(65_537)
    if len(raw) > 65_536:
        raise InputError("RULE_SIZE_LIMIT", "Rule configuration exceeds 65,536 bytes")
    try:
        rule = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, InputError):
            raise
        raise InputError("RULE_JSON", "Rule is not valid UTF-8 JSON") from exc
    return rule, hashlib.sha256(raw).hexdigest()


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".trialtrace-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def preserve_previous(output):
    if output.is_symlink():
        raise InputError("OUTPUT_SYMLINK", "Output must not be a symlink")
    if output.exists():
        if not output.is_file():
            raise InputError("OUTPUT_NOT_FILE", "Output target must be a file")
        folder = output.parent / ".previous"
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        destination = folder / (output.name + "." + stamp + "." + uuid.uuid4().hex + ".json")
        output.rename(destination)
        return str(destination)
    return None


def supplied_paths(argv):
    """Recover file targets even when argparse rejects a later malformed option.

    This never authorizes evaluation; it only protects inputs and retires a stale
    output before recording the argument error. Keep every repeated input path.
    """
    flags = {"--anchors", "--visits", "--assignments", "--rule", "--source-pdf", "--output"}
    inputs, output = [], None
    for i, token in enumerate(argv):
        if token == "--":
            break
        flag, separator, value = token.partition("=")
        # Abbreviations are rejected by argparse. During failure cleanup only,
        # reserve their possible input targets so a typo cannot move an input.
        possible_input = flag.startswith("--") and any(known.startswith(flag) for known in flags - {"--output"})
        if flag not in flags and not possible_input:
            continue
        if not separator:
            value = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("--") else ""
        if not value:
            continue
        if flag == "--output":
            output = Path(value)
        else:
            inputs.append(Path(value))
    return inputs, output


def same_target(first, second):
    if first.resolve() == second.resolve():
        return True
    try:
        return first.samefile(second)
    except FileNotFoundError:
        return False


def main(argv=None):
    parser = Parser(description=__doc__, allow_abbrev=False)
    for name in ("anchors", "visits", "assignments", "rule", "output", "source-pdf"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--draft-synthetic", action="store_true", help="Opt in to synthetic engineering with unreviewed source interpretation")
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--help" in argv or "-h" in argv:
        parser.print_help()
        return 0
    output, diagnostics_path, previous = None, None, None
    try:
        inputs, output = supplied_paths(argv)
        if output is not None:
            diagnostics_path = output.with_suffix(output.suffix + ".diagnostics.json")
            if any(same_target(target, path) for target in (output, diagnostics_path) for path in inputs):
                diagnostics_path = None
                raise InputError("OUTPUT_INPUT_COLLISION", "Output and diagnostic paths must not overwrite any input or rule")
            previous = preserve_previous(output)
            if diagnostics_path.is_symlink() or (diagnostics_path.exists() and not diagnostics_path.is_file()):
                diagnostics_path = None
                raise InputError("DIAGNOSTIC_PATH", "Diagnostics target must be a regular file, not a symlink or directory")
        args, unknown = parser.parse_known_args(argv)
        if unknown:
            raise InputError("CLI_ARGUMENTS", "Unknown arguments: " + " ".join(unknown))
        if any(getattr(args, key) is None for key in ("anchors", "visits", "assignments", "rule", "output")):
            raise InputError("CLI_ARGUMENTS", "--anchors, --visits, --assignments, --rule and --output are required")
        if not args.draft_synthetic:
            raise InputError("SOURCE_REVIEW_REQUIRED", "Reviewed mode is blocked pending independent source review and integrator acceptance; use --draft-synthetic only for explicit draft engineering")
        rule, digest = load_rule(args.rule)
        tables = load_inputs({name + ".csv": getattr(args, name) for name in ("anchors", "visits", "assignments")})
        source = None
        if args.source_pdf is not None:
            with args.source_pdf.open("rb") as stream:
                prefix = stream.read(5)
                if prefix != b"%PDF-":
                    raise InputError("SOURCE_PDF", "Supplied source bytes do not have a PDF header")
                sha = hashlib.sha256(prefix)
                for block in iter(lambda: stream.read(65_536), b""):
                    sha.update(block)
            source = {"pdf_sha256": sha.hexdigest(), "retrieval_status": "LOCAL_PDF_BYTES_HASHED_IDENTITY_NOT_CHECKED_BY_RUNTIME"}
        bundle = build_bundle(tables, rule, digest, mode="DRAFT_ENGINEERING", source_metadata=source)
        encoded = serialize_bundle(bundle)
        if diagnostics_path.exists():
            diagnostics_path.unlink()
        atomic_write(output, encoded)
    except (InputError, OSError) as exc:
        diagnostic = exc.diagnostic() if isinstance(exc, InputError) else {"code": "IO_ERROR", "message": str(exc)}
        failure = {"status": "FAILED", "diagnostic": diagnostic, "previous_output": previous, "success_bundle_written": False}
        if diagnostics_path is not None:
            try:
                atomic_write(diagnostics_path, (json.dumps(failure, indent=2) + "\n").encode("utf-8"))
            except OSError as diagnostic_error:
                failure["diagnostic_write_error"] = str(diagnostic_error)
        print(json.dumps(failure), file=sys.stderr)
        return 2
    print(json.dumps({"status": "SUCCESS_DRAFT_ENGINEERING", "output": str(output), "run_id": bundle["run_id"], "summary": bundle["summary"], "previous_output": previous}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
