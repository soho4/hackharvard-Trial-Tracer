import hashlib

import pytest

from conftest import HEADERS
from trialtrace.errors import InputError
from trialtrace.importer import load_inputs


def assert_structural_error(paths):
    with pytest.raises(InputError) as error:
        load_inputs(paths)
    assert error.value.code


def test_real_files_preserve_values_raw_bytes_and_logical_roles(records, write_inputs):
    paths = write_inputs(records)
    tables = load_inputs(paths)
    assert set(tables) == set(HEADERS)
    for name, table in tables.items():
        assert table["name"] == name
        assert table["display_name"] == paths[name].name
        assert table["sha256"] == hashlib.sha256(paths[name].read_bytes()).hexdigest()
        assert table["bom"] is False
        assert len(table["records"]) == 1
        row = table["records"][0]
        assert row["record_ordinal"] == 1
        assert row["raw_record"] == records[name][0]
        assert row["raw_csv"] == paths[name].read_text().splitlines(keepends=True)[1]


def test_header_order_is_not_positional(records, write_inputs):
    paths = write_inputs(records, headers={name: list(reversed(fields)) for name, fields in HEADERS.items()})
    tables = load_inputs(paths)
    for name in HEADERS:
        assert tables[name]["records"][0]["raw_record"] == records[name][0]


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_quoted_comma_newline_and_quote_are_one_record(records, write_inputs, newline):
    note = 'Synthetic note, with "quoted" text\nsecond logical line'
    records["assignments.csv"][0]["mapping_note"] = note
    records["assignments.csv"].append(dict(records["assignments.csv"][0], assignment_id="another-assignment"))
    paths = write_inputs(records, newline=newline)
    rows = load_inputs(paths)["assignments.csv"]["records"]
    assert [row["record_ordinal"] for row in rows] == [1, 2]
    assert [row["raw_record"]["mapping_note"] for row in rows] == [note, note]
    assert '""quoted""' in rows[0]["raw_csv"]
    assert rows[0]["raw_csv"].endswith(newline)
    assert "second logical line" in rows[0]["raw_csv"]


def test_bom_is_accepted_recorded_and_hashed(records, write_inputs):
    paths = write_inputs(records, bom=True)
    tables = load_inputs(paths)
    for name in HEADERS:
        assert tables[name]["bom"] is True
        assert tables[name]["records"][0]["raw_record"] == records[name][0]
        assert tables[name]["sha256"] == hashlib.sha256(paths[name].read_bytes()).hexdigest()


@pytest.mark.parametrize("change", ["missing", "extra", "duplicate", "empty", "space", "semicolon"])
def test_bad_headers_fail_the_table(records, write_inputs, change):
    paths = write_inputs(records)
    raw = paths["visits.csv"].read_bytes()
    header, rows = raw.split(b"\n", 1)
    fields = header.split(b",")
    if change == "missing":
        fields.pop()
    elif change == "extra":
        fields.append(b"extra")
    elif change == "duplicate":
        fields[1] = fields[0]
    elif change == "empty":
        fields[1] = b""
    elif change == "space":
        fields[1] = b" participant_id"
    delimiter = b";" if change == "semicolon" else b","
    paths["visits.csv"].write_bytes(delimiter.join(fields) + b"\n" + rows)
    assert_structural_error(paths)


@pytest.mark.parametrize("bad_body", [
    b"\xff\n", b"bad\x00record\n", b'"unterminated\n',
    b'"closed"garbage,other\n', b'a"illegal,b\n', b"too,few\n",
    b"1,2,3,4,5,6,7,8,9,10,11\n",
])
def test_invalid_encoding_nul_quoting_or_row_width_blocks(records, write_inputs, bad_body):
    paths = write_inputs(records)
    header = paths["visits.csv"].read_bytes().split(b"\n", 1)[0]
    paths["visits.csv"].write_bytes(header + b"\n" + bad_body)
    assert_structural_error(paths)


@pytest.mark.parametrize("raw", [b"", b" ", b"\r\n\t\n", b"\xef\xbb\xbf"])
def test_empty_or_whitespace_only_files_are_structural_failures(records, write_inputs, raw):
    paths = write_inputs(records)
    paths["visits.csv"].write_bytes(raw)
    assert_structural_error(paths)


def test_header_only_tables_are_valid(records, write_inputs):
    paths = write_inputs({name: [] for name in HEADERS})
    tables = load_inputs(paths)
    assert all(table["records"] == [] for table in tables.values())


def test_roles_allow_same_external_filename(records, write_inputs, tmp_path):
    original = write_inputs(records)
    paths = {}
    for index, name in enumerate(HEADERS):
        target = tmp_path / str(index) / "upload.csv"
        target.parent.mkdir()
        target.write_bytes(original[name].read_bytes())
        paths[name] = target
    tables = load_inputs(paths)
    assert set(tables) == set(HEADERS)
    assert all(table["display_name"] == "upload.csv" for table in tables.values())
    assert len({table["sha256"] for table in tables.values()}) == 3


def test_missing_role_is_not_silently_an_empty_table(records, write_inputs):
    paths = write_inputs(records)
    paths.pop("anchors.csv")
    assert_structural_error(paths)


def test_extra_role_fails_closed(records, write_inputs):
    paths = write_inputs(records)
    paths["unexpected.csv"] = paths["anchors.csv"]
    assert_structural_error(paths)


def test_missing_file_is_a_structured_failure(records, write_inputs):
    paths = write_inputs(records)
    paths["anchors.csv"].unlink()
    assert_structural_error(paths)


def test_raw_line_ending_changes_hash_but_not_values(records, write_inputs, tmp_path):
    first = load_inputs(write_inputs(records, newline="\n", directory=tmp_path / "lf"))
    second = load_inputs(write_inputs(records, newline="\r\n", directory=tmp_path / "crlf"))
    for name in HEADERS:
        assert first[name]["sha256"] != second[name]["sha256"]
        assert first[name]["records"][0]["raw_record"] == second[name]["records"][0]["raw_record"]


def test_cell_at_limit_and_one_over(records, write_inputs):
    records["assignments.csv"][0]["mapping_note"] = "x" * 10000
    tables = load_inputs(write_inputs(records))
    assert len(tables["assignments.csv"]["records"][0]["raw_record"]["mapping_note"]) == 10000
    records["assignments.csv"][0]["mapping_note"] += "x"
    assert_structural_error(write_inputs(records))


def test_record_limit_at_500_then_501(records, write_inputs):
    records["anchors.csv"] = [dict(records["anchors.csv"][0], anchor_id=f"a-{index}") for index in range(500)]
    assert len(load_inputs(write_inputs(records))["anchors.csv"]["records"]) == 500
    records["anchors.csv"].append(dict(records["anchors.csv"][0], anchor_id="a-500"))
    assert_structural_error(write_inputs(records))


def test_file_at_exact_byte_limit_then_one_over(records, write_inputs):
    row = records["assignments.csv"][0]
    records["assignments.csv"] = [dict(row, assignment_id=f"s-{index}", mapping_note="x" * 9800) for index in range(100)]
    paths = write_inputs(records)
    remaining = 1000000 - paths["assignments.csv"].stat().st_size
    # Spread padding across cells while keeping every cell within its own bound.
    for current in records["assignments.csv"]:
        extra = min(200, remaining)
        current["mapping_note"] += "x" * extra
        remaining -= extra
    assert remaining == 0
    paths = write_inputs(records)
    assert paths["assignments.csv"].stat().st_size == 1000000
    assert len(load_inputs(paths)["assignments.csv"]["records"]) == 100
    paths["assignments.csv"].write_bytes(paths["assignments.csv"].read_bytes() + b"\n")
    assert paths["assignments.csv"].stat().st_size == 1000001
    assert_structural_error(paths)
