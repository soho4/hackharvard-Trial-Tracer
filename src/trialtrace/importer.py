"""Bounded, non-coercing CSV ingestion retaining logical-record evidence."""

import csv
import hashlib
import io
from pathlib import Path

from .errors import InputError

HEADERS = {
    "anchors.csv": "study_id,participant_id,site_id,anchor_id,anchor_code,anchor_kind,anchor_date".split(","),
    "visits.csv": "study_id,participant_id,site_id,visit_id,visit_code,event_kind,actual_date,visit_status,anchor_id,assignment_id".split(","),
    "assignments.csv": "assignment_id,study_id,participant_id,site_id,rule_version,schedule_code,mapping_status,mapping_note".split(","),
}
MAX_BYTES = 1_000_000
MAX_RECORDS = 500
MAX_CELL = 10_000


def _logical_records(text, name):
    """Enforce CSV quote placement (csv.reader(strict=True) alone allows stray quotes)."""
    start, i, state, cell_chars = 0, 0, "start", 0
    while i < len(text):
        c = text[i]
        if c == "\r" and (i + 1 == len(text) or text[i + 1] != "\n"):
            raise InputError("CSV_NEWLINE", "Only LF or CRLF line endings are supported", file=name)
        if state == "quoted":
            if c == '"':
                if i + 1 < len(text) and text[i + 1] == '"':
                    cell_chars += 1
                    if cell_chars > MAX_CELL:
                        raise InputError("CELL_SIZE_LIMIT", "Cell exceeds 10,000 characters", file=name)
                    i += 2
                    continue
                state = "closed"
            else:
                cell_chars += 1
        elif c in "\r\n":
            end = i + (2 if c == "\r" else 1)
            yield text[start:end]
            start, i, state, cell_chars = end, end, "start", 0
            continue
        elif c == ",":
            state, cell_chars = "start", 0
        elif c == '"':
            if state != "start":
                raise InputError("CSV_QUOTING", "Quote inside an unquoted field", file=name)
            state = "quoted"
        elif state == "closed":
            raise InputError("CSV_QUOTING", "Characters after a closing quote", file=name)
        else:
            state = "unquoted"
            cell_chars += 1
        if cell_chars > MAX_CELL:
            raise InputError("CELL_SIZE_LIMIT", "Cell exceeds 10,000 characters", file=name)
        i += 1
    if state == "quoted":
        raise InputError("CSV_QUOTING", "Unclosed quoted field", file=name)
    if start < len(text):
        yield text[start:]


def load_table(path, name):
    path = Path(path)
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
    except OSError as exc:
        raise InputError("FILE_ACCESS", f"Cannot read {name}: {exc.strerror}", file=name) from exc
    if len(raw) > MAX_BYTES:
        raise InputError("INPUT_SIZE_LIMIT", "Input exceeds 1,000,000 bytes", file=name)
    if b"\x00" in raw:
        raise InputError("NUL_BYTE", "NUL bytes are not accepted", file=name)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InputError("INVALID_UTF8", "Input is not UTF-8", file=name) from exc
    if not text.strip():
        raise InputError("EMPTY_FILE", "Empty or whitespace-only table", file=name)
    header, records = None, []
    for ordinal, raw_csv in enumerate(_logical_records(text, name)):
        try:
            values = next(csv.reader(io.StringIO(raw_csv, newline=""), strict=True))
        except (csv.Error, StopIteration) as exc:
            raise InputError("CSV_PARSE", "Malformed CSV record", file=name, record_ordinal=ordinal) from exc
        if any(len(cell) > MAX_CELL for cell in values):
            raise InputError("CELL_SIZE_LIMIT", "Cell exceeds 10,000 characters", file=name, record_ordinal=ordinal)
        if header is None:
            if len(values) != len(HEADERS[name]) or set(values) != set(HEADERS[name]):
                raise InputError("INVALID_HEADER", "Headers must contain each required name exactly once", file=name)
            header = values
            continue
        if ordinal > MAX_RECORDS:
            raise InputError("RECORD_LIMIT", "Table exceeds 500 data records", file=name)
        if len(values) != len(header):
            raise InputError("ROW_WIDTH", "Row width does not match header", file=name, record_ordinal=ordinal)
        records.append({"record_ordinal": ordinal, "raw_record": dict(zip(header, values)), "raw_csv": raw_csv})
    return {
        "name": name,
        "display_name": "".join(c for c in path.name if c.isprintable())[:200] or name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bom": raw.startswith(b"\xef\xbb\xbf"),
        "byte_count": len(raw),
        "records": records,
    }


def load_inputs(paths):
    if set(paths) != set(HEADERS):
        raise InputError("INPUT_ROLES", "Exactly anchors.csv, visits.csv and assignments.csv roles are required")
    return {name: load_table(paths[name], name) for name in HEADERS}
