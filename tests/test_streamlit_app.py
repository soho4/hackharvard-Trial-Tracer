"""Streamlit AppTest lifecycle tests. These are not browser/network tests."""

import json
import sys

import pytest
from streamlit.testing.v1 import AppTest

from conftest import ROOT


@pytest.fixture
def app(monkeypatch):
    # AppTest executes the real script in-process and inherits pytest arguments;
    # reproduce the app's own process argv instead of passing pytest flags to it.
    monkeypatch.setattr(sys, "argv", [str(ROOT / "app.py")])
    instance = AppTest.from_file(ROOT / "app.py", default_timeout=15).run()
    assert not instance.exception
    return instance


def upload_files(app, paths):
    for name, path in paths.items():
        uploader(app, name).set_value((path.name, path.read_bytes(), "text/csv"))
    app.run()
    assert not app.exception
    for name, path in paths.items():
        assert app.session_state["selected_upload_" + name] == (path.name, path.read_bytes())
        assert not [item for item in app.file_uploader if item.label == name]


def uploader(app, role):
    return next(item for item in app.file_uploader if item.label == role)


def run_button(app):
    return next(item for item in app.button if item.label == "Run timing check")


def finding_selector(app):
    return next(item for item in app.selectbox if item.label == "Select finding")


def clear_role(app, role):
    app.button(key="clear_" + role).click().run()
    assert "selected_upload_" + role not in app.session_state
    assert uploader(app, role).value is None
    assert run_button(app).disabled
    assert_no_report(app)


def run_check(app):
    app.checkbox(key="draft_confirmed").check().run()
    assert not run_button(app).disabled
    run_button(app).click().run()
    assert not app.exception


def report_downloads(app):
    return [button for button in app.download_button if button.key == "evidence_download"]


def assert_no_report(app):
    assert "result" not in app.session_state
    assert "result_bytes" not in app.session_state
    assert not report_downloads(app)
    assert not app.metric
    assert not app.exception


def test_initial_app_requires_three_files_and_synthetic_confirmation(app, records, write_inputs):
    assert len(app.file_uploader) == 3
    assert all(uploader.allowed_type == [] for uploader in app.file_uploader)
    assert run_button(app).disabled
    assert_no_report(app)
    paths = write_inputs(records)
    subset = {name: path for name, path in paths.items() if name != "assignments.csv"}
    upload_files(app, subset)
    app.checkbox(key="draft_confirmed").check().run()
    assert run_button(app).disabled
    uploader(app, "assignments.csv").set_value((paths["assignments.csv"].name, paths["assignments.csv"].read_bytes(), "text/csv")).run()
    assert not run_button(app).disabled
    app.checkbox(key="draft_confirmed").uncheck().run()
    assert run_button(app).disabled
    assert_no_report(app)


def test_actual_script_upload_compute_filter_select_and_download_state(app, records, write_inputs):
    records["visits.csv"].append(dict(records["visits.csv"][0], visit_id="app-new-late-event", actual_date="2033-01-05"))
    records["assignments.csv"][0]["mapping_note"] = 'Synthetic <script>literal text only</script>\nwith "quotes"'
    paths = write_inputs(records)
    upload_files(app, paths)
    run_check(app)
    bundle = app.session_state["result"]
    encoded = app.session_state["result_bytes"]
    assert json.loads(encoded) == bundle
    assert [item["status"] for item in bundle["findings"]] == ["PASS", "POTENTIAL_DEVIATION"]
    assert bundle["findings"][1]["calculation"]["days_outside"] == 2
    assert len(report_downloads(app)) == 1
    assert [metric.value for metric in app.metric] == ["1", "1", "0", "0"]
    app.selectbox(key="outcome_filter").select("POTENTIAL_DEVIATION").run()
    assert not app.exception
    assert len(finding_selector(app).options) == 1
    assert "app-new-late-event" in finding_selector(app).options[0]
    visible_json = [json.loads(element.value) for element in app.json]
    assert records["visits.csv"][1] in visible_json
    assert records["assignments.csv"][0] in visible_json
    assert app.session_state["result_bytes"] == encoded
    assert [metric.value for metric in app.metric] == ["1", "1", "0", "0"]
    app.text_input(key="finding_search").set_value("no-matching-person-or-event").run()
    assert any("No findings match" in info.value for info in app.info)
    assert len(report_downloads(app)) == 1
    assert app.session_state["result_bytes"] == encoded
    app.text_input(key="finding_search").set_value("").run()
    app.selectbox(key="outcome_filter").select("ALL").run()
    assert len(finding_selector(app).options) == 2
    finding_selector(app).select(bundle["findings"][0]["finding_id"]).run()
    assert records["visits.csv"][0] in [json.loads(element.value) for element in app.json]


def test_replacing_uploaded_date_invalidates_before_recomputation(app, records, write_inputs):
    paths = write_inputs(records)
    upload_files(app, paths)
    run_check(app)
    before = app.session_state["result"]
    assert before["findings"][0]["status"] == "PASS"
    clear_role(app, "visits.csv")
    records["visits.csv"][0]["actual_date"] = "2033-01-04"
    path = write_inputs(records)["visits.csv"]
    uploader(app, "visits.csv").set_value((path.name, path.read_bytes(), "text/csv")).run()
    assert_no_report(app)
    run_button(app).click().run()
    assert not app.exception
    after = app.session_state["result"]
    assert after["findings"][0]["status"] == "POTENTIAL_DEVIATION"
    assert after["findings"][0]["calculation"]["days_outside"] == 1
    assert after["run_id"] != before["run_id"]
    assert len(report_downloads(app)) == 1


def test_invalid_replacement_removes_old_findings_and_download(app, records, write_inputs):
    upload_files(app, write_inputs(records))
    run_check(app)
    assert report_downloads(app)
    clear_role(app, "visits.csv")
    uploader(app, "visits.csv").set_value(("replacement.any", b"bad,header\nwrong,row\n", "application/octet-stream")).run()
    assert_no_report(app)
    run_button(app).click().run()
    assert_no_report(app)
    assert app.session_state["check_error"]["code"] == "INVALID_HEADER"
    assert any("Input rejected" in item.value for item in app.error)
    app.run()
    assert_no_report(app)
    assert app.session_state["check_error"]["code"] == "INVALID_HEADER"


@pytest.mark.parametrize("change", ["remove_file", "withdraw_confirmation"])
def test_removal_or_withdrawn_confirmation_invalidates_current_report(app, records, write_inputs, change):
    upload_files(app, write_inputs(records))
    run_check(app)
    if change == "remove_file":
        clear_role(app, "anchors.csv")
    else:
        app.checkbox(key="draft_confirmed").uncheck().run()
    assert_no_report(app)
    assert run_button(app).disabled


def test_header_only_visits_displays_zero_without_compliance_claim(app, records, write_inputs):
    records["visits.csv"] = []
    upload_files(app, write_inputs(records))
    run_check(app)
    assert app.session_state["result"]["findings"] == []
    assert len(report_downloads(app)) == 1
    assert [metric.value for metric in app.metric] == ["0", "0", "0", "0"]
    assert any("Zero findings does not mean" in info.value for info in app.info)


def test_clear_before_oversized_replacement_removes_stale_report_and_old_bytes(app, records, write_inputs):
    paths = write_inputs(records)
    upload_files(app, paths)
    run_check(app)
    assert len(app.file_uploader) == 0
    assert app.session_state["selected_upload_visits.csv"] == (paths["visits.csv"].name, paths["visits.csv"].read_bytes())
    clear_role(app, "visits.csv")
    assert uploader(app, "visits.csv").key == "upload_visits.csv_1"
    # AppTest has no browser upload-size rejection. First verify the empty role
    # remains safe across a rerun with no accepted replacement (browser behavior).
    app.run()
    assert_no_report(app)
    assert "selected_upload_visits.csv" not in app.session_state
    assert run_button(app).disabled
    # Then exercise the server-side byte bound with a file over 1,000,000 bytes
    # but under Streamlit's 1 MiB uploader limit. This is component coverage only.
    uploader(app, "visits.csv").set_value(("oversized.csv", b"x" * 1000001, "text/csv")).run()
    assert_no_report(app)
    run_button(app).click().run()
    assert_no_report(app)
    assert app.session_state["check_error"]["code"] == "INPUT_SIZE_LIMIT"
    assert app.session_state["selected_upload_visits.csv"][0] == "oversized.csv"


def test_filtered_finding_widget_identity_label_and_evidence_remain_consistent(app, records, write_inputs):
    records["visits.csv"].append(dict(records["visits.csv"][0], visit_id="query-only-person-event", visit_status="UNKNOWN"))
    upload_files(app, write_inputs(records))
    run_check(app)
    findings = app.session_state["result"]["findings"]
    initial_key = finding_selector(app).key
    assert finding_selector(app).value == findings[0]["finding_id"]
    assert finding_selector(app).options[0].endswith("PASS")
    app.selectbox(key="outcome_filter").select("DATA_QUERY").run()
    selected = finding_selector(app)
    assert selected.key != initial_key
    assert selected.value == findings[1]["finding_id"]
    assert len(selected.options) == 1
    assert selected.options[0].endswith("DATA_QUERY")
    assert "query-only-person-event" in selected.options[0]
    assert records["visits.csv"][1] in [json.loads(element.value) for element in app.json]
    assert any(item.value.startswith("DATA_QUERY ·") for item in app.text)
    app.selectbox(key="outcome_filter").select("PASS").run()
    assert finding_selector(app).key != selected.key
    assert finding_selector(app).value == findings[0]["finding_id"]
    assert finding_selector(app).options[0].endswith("PASS")
    assert records["visits.csv"][0] in [json.loads(element.value) for element in app.json]
    clear_role(app, "visits.csv")
    assert not [item for item in app.selectbox if item.label == "Select finding"]
