"""Read the optional public study snapshot without inventing unavailable facts.

This checks a local snapshot's shape and declared identity. It does not fetch the
registry, authenticate the response hash, or approve the protocol interpretation.
"""

from datetime import date, datetime
import json
import math
from pathlib import Path
import re

from .errors import InputError


MAX_REGISTRY_BYTES = 100_000
MAX_JSON_DEPTH = 32
NCT_ID = "NCT04470427"
API_URL = "https://clinicaltrials.gov/api/v2/studies/NCT04470427"
STUDY_URL = "https://clinicaltrials.gov/study/NCT04470427"
PROTOCOL_URL = "https://cdn.clinicaltrials.gov/large-docs/27/NCT04470427/Prot_000.pdf"


def _check_depth(text):
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise InputError("REGISTRY_DEPTH", "Public registry metadata exceeds the supported JSON depth")
        elif char in "]}":
            depth -= 1


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("REGISTRY_JSON", "Public registry metadata contains a duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(_value):
    raise InputError("REGISTRY_JSON", "Public registry metadata contains a nonfinite JSON number")


def _check_json_values(value):
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeError as exc:
            raise InputError("REGISTRY_ENCODING", "Public registry metadata contains invalid Unicode") from exc
    elif isinstance(value, float) and not math.isfinite(value):
        raise InputError("REGISTRY_JSON", "Public registry metadata contains a nonfinite JSON number")
    elif isinstance(value, dict):
        for key, child in value.items():
            _check_json_values(key)
            _check_json_values(child)
    elif isinstance(value, list):
        for child in value:
            _check_json_values(child)


def _object(value, field):
    if not isinstance(value, dict):
        raise InputError("REGISTRY_FIELDS", "Public registry metadata requires an object", field=field)
    return value


def _text(value, field, *, maximum=500):
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum or not value.isprintable():
        raise InputError("REGISTRY_FIELDS", "Public registry metadata requires nonempty printable text", field=field)
    return value


def _identity(value, expected, field):
    if value != expected or type(value) is not type(expected):
        raise InputError("REGISTRY_IDENTITY", "Public registry metadata has an unexpected identity or provenance value", field=field)


def _date(value, field):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise InputError("REGISTRY_DATE", "Public registry metadata requires a YYYY-MM-DD date", field=field)
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise InputError("REGISTRY_DATE", "Public registry metadata contains an invalid calendar date", field=field) from exc


def _validate_snapshot(snapshot):
    _object(snapshot, "snapshot")
    _identity(snapshot.get("schema_version"), "trialtrace.public_registry_snapshot.v1", "schema_version")
    _identity(snapshot.get("data_kind"), "PUBLIC_STUDY_METADATA", "data_kind")
    _identity(snapshot.get("is_participant_event_data"), False, "is_participant_event_data")
    source = _object(snapshot.get("source"), "source")
    study = _object(snapshot.get("study"), "study")
    for key, expected in {
        "provider": "ClinicalTrials.gov",
        "api_url": API_URL,
        "study_url": STUDY_URL,
        "http_status": 200,
        "content_type": "application/json",
        "transport_tls_verified": True,
        "snapshot_not_live_feed": True,
    }.items():
        _identity(source.get(key), expected, "source." + key)
    digest = source.get("response_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise InputError("REGISTRY_FIELDS", "Public registry metadata requires a full response SHA-256", field="source.response_sha256")
    size = source.get("response_byte_count")
    if type(size) is not int or size < 1:
        raise InputError("REGISTRY_FIELDS", "Public registry metadata requires a positive response byte count", field="source.response_byte_count")
    fetched = source.get("fetched_at_utc")
    if not isinstance(fetched, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|\+00:00)", fetched):
        raise InputError("REGISTRY_DATE", "Public registry metadata requires an explicit UTC retrieval timestamp", field="source.fetched_at_utc")
    try:
        datetime.fromisoformat(fetched.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InputError("REGISTRY_DATE", "Public registry metadata contains an invalid retrieval timestamp", field="source.fetched_at_utc") from exc
    _identity(study.get("nct_id"), NCT_ID, "study.nct_id")
    _identity(study.get("protocol_id"), "mRNA-1273-P301", "study.protocol_id")
    _text(study.get("overall_status"), "study.overall_status", maximum=100)
    _text(study.get("lead_sponsor"), "study.lead_sponsor")
    _date(study.get("last_update_posted"), "study.last_update_posted")
    if "protocol_document" in snapshot:
        protocol = _object(snapshot["protocol_document"], "protocol_document")
        _identity(protocol.get("url"), PROTOCOL_URL, "protocol_document.url")
        _identity(protocol.get("clinical_validation"), False, "protocol_document.clinical_validation")
        _identity(protocol.get("source_interpretation_review"), "BLOCKED_PENDING_HUMAN_REVIEW", "protocol_document.source_interpretation_review")


def load_registry_snapshot(path):
    """Return validated declared public metadata, or a structured unavailable error."""
    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(MAX_REGISTRY_BYTES + 1)
    except OSError as exc:
        raise InputError("REGISTRY_ACCESS", "Public registry metadata is missing or cannot be read") from exc
    if len(raw) > MAX_REGISTRY_BYTES:
        raise InputError("REGISTRY_SIZE_LIMIT", "Public registry metadata exceeds 100,000 bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise InputError("REGISTRY_ENCODING", "Public registry metadata is not valid UTF-8") from exc
    _check_depth(text)
    try:
        snapshot = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except InputError:
        raise
    except (ValueError, RecursionError) as exc:
        raise InputError("REGISTRY_JSON", "Public registry metadata is not valid JSON") from exc
    _check_json_values(snapshot)
    _validate_snapshot(snapshot)
    return snapshot
