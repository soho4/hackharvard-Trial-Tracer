"""AppTest is component evidence, separate from actual browser/file-transfer checks."""
import io
import json
import sys
import zipfile

import pytest
from streamlit.testing.v1 import AppTest

from conftest import ROOT


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(sys, "argv", [str(ROOT / "app.py")])
    return AppTest.from_file(ROOT / "app.py", default_timeout=15).run()


def choose_source(app, raw=None):
    raw = raw if raw is not None else (ROOT / "examples/preparation/synthetic-wide.csv").read_bytes()
    next(u for u in app.file_uploader if u.label == "Source spreadsheet CSV").set_value(("synthetic-wide.csv", raw, "text/csv")).run()
    assert not app.exception
    return raw


def choose_columns(app):
    profile = json.loads((ROOT / "examples/preparation/mapping.json").read_text())
    for field, column in profile["columns"].items():
        app.selectbox(key="prep_column_" + field).select(column).run()
    app.selectbox(key="prep_completed").select("done").run()
    app.checkbox(key="prep_scope").check().run()


def calculate(app):
    choose_source(app)
    choose_columns(app)
    app.button(key="prep_prepare").click().run()
    assert "prep_result" not in app.session_state
    app.button(key="prep_run").click().run()
    assert not app.exception


def test_explicit_choices_preview_then_actual_result_and_upstream_package(app):
    choose_source(app)
    assert app.button(key="prep_prepare").disabled
    assert all(s.value is None for s in app.selectbox if str(s.key).startswith("prep_column_"))
    choose_columns(app)
    app.button(key="prep_prepare").click().run()
    assert "prep_result" not in app.session_state
    assert len(app.session_state["prep_prepared"]["manifest"]["lineage"]) == 7
    app.button(key="prep_run").click().run()
    bundle = app.session_state["prep_result"]
    assert bundle["summary"]["statuses"] == {"PASS": 1, "POTENTIAL_DEVIATION": 1, "DATA_QUERY": 4, "NOT_EVALUABLE": 1}
    with zipfile.ZipFile(io.BytesIO(app.session_state["prep_package"])) as archive:
        assert archive.read("source.csv") == (ROOT / "examples/preparation/synthetic-wide.csv").read_bytes()
        assert json.loads(archive.read("evidence.json")) == bundle
    assert any("operator_note" in json.loads(j.value) for j in app.json if isinstance(json.loads(j.value), dict))
    assert {b.key for b in app.download_button} >= {"prep_package_download", "prep_json_download", "prep_review_download"}


def test_mapping_change_retires_confirmation_preparation_and_downloads(app):
    calculate(app)
    app.selectbox(key="prep_column_actual_date").select("dose_actual").run()
    assert not app.session_state["prep_scope"]
    assert "prep_prepared" not in app.session_state and "prep_result" not in app.session_state
    assert not any(b.key in ("prep_package_download", "prep_json_download") for b in app.download_button)
    app.checkbox(key="prep_scope").check().run()
    app.button(key="prep_prepare").click().run()
    assert app.session_state["prep_error"]["code"] == "COLUMN_REUSED"
    assert not app.exception


@pytest.mark.parametrize("replacement,code", [(b'wrong\n1,2', 'ROW_WIDTH'), (b'x'*1_000_001, 'INPUT_SIZE_LIMIT')])
def test_clear_before_bad_replacement_retires_results(app, replacement, code):
    calculate(app)
    app.button(key="prep_clear").click().run()
    assert "prep_result" not in app.session_state and "prep_package" not in app.session_state
    assert not any(b.key == "prep_package_download" for b in app.download_button)
    choose_source(app, replacement)
    assert any(json.loads(j.value).get("code") == code for j in app.json if isinstance(json.loads(j.value), dict))
    assert not app.exception


def test_unconfirm_scope_retires_report(app):
    calculate(app)
    app.checkbox(key="prep_scope").uncheck().run()
    assert "prep_result" not in app.session_state
    assert app.button(key="prep_prepare").disabled
