"""In-memory upload adapter: same parser, evaluator and export used by the CLI."""

from .errors import InputError
from .exporter import build_bundle, serialize_bundle
from .importer import HEADERS, parse_table


def check_uploads(uploads, rule, rule_sha256, *, draft_confirmed=False, source_metadata=None):
    """Uploads map each logical role to (display filename, exact bytes)."""
    if not draft_confirmed:
        raise InputError("SOURCE_REVIEW_REQUIRED", "Confirm synthetic draft engineering before running")
    if set(uploads) != set(HEADERS) or any(value is None for value in uploads.values()):
        raise InputError("INPUT_ROLES", "Upload all three required tables")
    tables = {name: parse_table(raw, name, display) for name, (display, raw) in uploads.items()}
    bundle = build_bundle(tables, rule, rule_sha256, mode="DRAFT_ENGINEERING", source_metadata=source_metadata)
    return bundle, serialize_bundle(bundle)
