"""Streamlit AppTest lifecycle tests. These are not browser/network tests."""

from copy import deepcopy
import io
import json
from pathlib import Path
import sys

import pytest
from streamlit.testing.v1 import AppTest

from conftest import HEADERS, ROOT
from trialtrace.exporter import serialize_bundle


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


def role_uploaders(app):
    return [item for item in app.file_uploader if item.label in HEADERS]


def visible_json(app):
    return [json.loads(item.value) for item in app.json]


def diagnostics(app):
    return [item for item in visible_json(app) if isinstance(item, dict) and "code" in item]


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
    assert not [item for item in app.download_button if item.key in ("worklist_download", "input_issues_download")]
    assert not app.metric
    assert not app.exception


def test_multiple_rejected_uploads_show_diagnostics_without_null_json_components(app, records, write_inputs):
    paths = write_inputs(records)
    uploader(app, "anchors.csv").set_value(("invalid-anchors.csv", b"incorrect,header\nwrong,row\n", "text/csv"))
    uploader(app, "visits.csv").set_value(("invalid-visits.csv", b"\xff", "text/csv"))
    uploader(app, "assignments.csv").set_value((paths["assignments.csv"].name, paths["assignments.csv"].read_bytes(), "text/csv"))
    app.run()
    app.checkbox(key="draft_confirmed").check().run()
    assert_no_report(app)
    assert run_button(app).disabled
    assert {item["code"] for item in diagnostics(app)} >= {"INVALID_HEADER", "INVALID_UTF8"}
    assert any("File rejected: anchors.csv" in item.value for item in app.error)
    assert any("File rejected: visits.csv" in item.value for item in app.error)
    assert all(json.loads(item.value) is not None for item in app.json), "st.json(None) creates an invalid react-json-view source"
    messages = [item.value.lower() for category in (app.markdown, app.caption, app.info, app.text) for item in category]
    assert any(("relationship" in message or "record-link" in message) and "unavailable" in message for message in messages)
    assert any(item.key == "intake_download" for item in app.download_button)
    app.run()
    assert_no_report(app)
    assert run_button(app).disabled
    assert all(json.loads(item.value) is not None for item in app.json)
    assert {item["code"] for item in diagnostics(app)} >= {"INVALID_HEADER", "INVALID_UTF8"}


def test_initial_app_requires_three_files_and_synthetic_confirmation(app, records, write_inputs):
    assert len(role_uploaders(app)) == 3
    assert all(uploader.allowed_type == [] for uploader in role_uploaders(app))
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
    assert run_button(app).disabled
    assert any(item["code"] == "INVALID_HEADER" and item["file"] == "visits.csv" for item in diagnostics(app))
    assert any("File rejected: visits.csv" in item.value for item in app.error)
    app.run()
    assert_no_report(app)
    assert run_button(app).disabled
    assert any(item["code"] == "INVALID_HEADER" for item in diagnostics(app))


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
    assert len(role_uploaders(app)) == 0
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
    assert run_button(app).disabled
    assert any(item["code"] == "INPUT_SIZE_LIMIT" and item["file"] == "visits.csv" for item in diagnostics(app))
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


def test_preflight_reports_multiple_rejected_roles_and_recovers_one_at_a_time(app, records, write_inputs):
    paths = write_inputs(records)
    uploader(app, "anchors.csv").set_value(("bad-encoding.csv", b"\xff", "text/csv"))
    uploader(app, "visits.csv").set_value(("bad-headers.csv", b"bad,header\n", "text/csv"))
    uploader(app, "assignments.csv").set_value((paths["assignments.csv"].name, paths["assignments.csv"].read_bytes(), "text/csv"))
    app.run()
    assert_no_report(app)
    assert {(item["file"], item["code"]) for item in diagnostics(app)} == {("anchors.csv", "INVALID_UTF8"), ("visits.csv", "INVALID_HEADER")}
    table = app.dataframe[0].value.set_index("Table")
    assert table.loc["assignments.csv", "State"] == "PARSED"
    assert table.loc["assignments.csv", "Records"] == 1
    app.checkbox(key="draft_confirmed").check().run()
    assert run_button(app).disabled
    clear_role(app, "anchors.csv")
    uploader(app, "anchors.csv").set_value((paths["anchors.csv"].name, paths["anchors.csv"].read_bytes(), "text/csv")).run()
    assert {item["code"] for item in diagnostics(app)} == {"INVALID_HEADER"}
    assert run_button(app).disabled
    clear_role(app, "visits.csv")
    uploader(app, "visits.csv").set_value((paths["visits.csv"].name, paths["visits.csv"].read_bytes(), "text/csv")).run()
    assert not diagnostics(app)
    assert not run_button(app).disabled
    assert_no_report(app)
    run_button(app).click().run()
    assert app.session_state["result"]["findings"][0]["status"] == "PASS"


def test_preflight_counts_logical_multiline_records_without_timing_evaluation(app, records, write_inputs):
    records["assignments.csv"][0]["mapping_note"] = 'Synthetic note\r\nsecond line, "quoted"'
    paths = write_inputs(records, bom=True, newline="\r\n")
    upload_files(app, paths)
    assert_no_report(app)
    table = app.dataframe[0].value.set_index("Table")
    assert set(table["State"]) == {"PARSED"}
    assert list(table["Records"]) == [1, 1, 1]
    assert {role: table.loc[role, "Bytes"] for role in HEADERS} == {role: len(path.read_bytes()) for role, path in paths.items()}
    relationship = next(item for item in visible_json(app) if isinstance(item, dict) and "visits_with_issues" in item)
    assert relationship["visit_records"] == 1
    assert relationship["visits_with_issues"] == 0
    assert "timing was not evaluated" in relationship["note"]
    assert app.download_button(key="intake_download")
    assert run_button(app).disabled  # Structural readability does not opt into draft execution.


def test_worklists_show_unreferenced_input_issues_and_ignore_display_filters(app, records, write_inputs):
    records["visits.csv"].append(dict(records["visits.csv"][0], visit_id="late-for-worklist", actual_date="2033-01-04"))
    records["anchors.csv"].append(dict(records["anchors.csv"][0], anchor_id="unused-invalid-anchor", anchor_date="2033-02-29"))
    upload_files(app, write_inputs(records))
    run_check(app)
    finding_rows = next(frame.value for frame in app.dataframe if "Next check" in frame.value.columns and "Visit" in frame.value.columns)
    assert list(finding_rows.columns) == ["Outcome", "Participant", "Visit", "Reason", "Next check", "Visit record"]
    assert list(finding_rows["Visit"]) == ["late-for-worklist"]
    assert list(finding_rows["Outcome"]) == ["POTENTIAL_DEVIATION"]
    assert finding_rows.iloc[0]["Participant"] == records["visits.csv"][1]["participant_id"]
    assert finding_rows.iloc[0]["Visit record"] == 2
    assert finding_rows.iloc[0]["Reason"]
    assert finding_rows.iloc[0]["Next check"]
    issue_rows = next(frame.value for frame in app.dataframe if "Unused row" in frame.value.columns)
    assert list(issue_rows.columns) == ["Table", "Record", "Issue", "Unused row", "Participant", "Next check"]
    assert len(issue_rows) == 1
    assert issue_rows.iloc[0]["Table"] == "anchors.csv"
    assert issue_rows.iloc[0]["Record"] == 2
    assert issue_rows.iloc[0]["Participant"] == records["anchors.csv"][1]["participant_id"]
    assert issue_rows.iloc[0]["Issue"] == "INVALID_DATE"
    assert bool(issue_rows.iloc[0]["Unused row"])
    assert issue_rows.iloc[0]["Next check"]
    assert app.download_button(key="worklist_download")
    assert app.download_button(key="input_issues_download")
    encoded = app.session_state["result_bytes"]
    worklist_url = app.download_button(key="worklist_download").proto.url
    issues_url = app.download_button(key="input_issues_download").proto.url
    app.selectbox(key="outcome_filter").select("PASS").run()
    assert finding_selector(app).options[0].endswith("PASS")
    filtered_rows = next(frame.value for frame in app.dataframe if "Next check" in frame.value.columns and "Visit" in frame.value.columns)
    assert filtered_rows.equals(finding_rows)
    # AppTest checks the component's media references, not a browser download.
    assert app.download_button(key="worklist_download").proto.url == worklist_url
    assert app.download_button(key="input_issues_download").proto.url == issues_url
    assert app.session_state["result_bytes"] == encoded
    clear_role(app, "visits.csv")
    assert_no_report(app)


def select_saved_reports(app, before, after):
    for label, raw in (("Earlier report", before), ("Later report", after)):
        uploader(app, label).set_value((label.replace(" ", "-") + ".json", raw, "application/json"))
    app.run()
    assert not app.exception
    assert not app.button(key="compare_reports").disabled
    app.button(key="compare_reports").click().run()
    assert not app.exception


def assert_no_comparison(app):
    assert "comparison_result" not in app.session_state
    assert not [button for button in app.download_button if button.key == "comparison_download"]
    assert not [item for item in app.selectbox if item.label == "Select changed record"]
    assert not app.exception


def test_saved_report_comparison_is_read_only_and_exposes_changed_calculation(app, records, make_bundle, monkeypatch):
    before = make_bundle(records)
    records["visits.csv"][0]["actual_date"] = "2033-01-04"
    after = make_bundle(records)
    before_raw, after_raw = serialize_bundle(before), serialize_bundle(after)
    originals = deepcopy((before, after))
    def forbidden_calculation(*_args, **_kwargs):
        raise AssertionError("Saved-report comparison must not rerun the timing engine")
    monkeypatch.setattr("trialtrace.engine.calculate", forbidden_calculation)
    select_saved_reports(app, before_raw, after_raw)
    comparison = app.session_state["comparison_result"]
    assert comparison["summary"]["matched"] == 1
    assert comparison["summary"]["changed"] == 1
    assert comparison["matched"][0]["changes"]["calculation"]["before"]["days_outside"] == 0
    assert comparison["matched"][0]["changes"]["calculation"]["after"]["days_outside"] == 1
    assert comparison["matched"][0] in visible_json(app)
    assert app.download_button(key="comparison_download")
    assert app.session_state["comparison_upload_before"][1] == before_raw
    assert app.session_state["comparison_upload_after"][1] == after_raw
    assert (before, after) == originals
    assert app.checkbox(key="draft_confirmed").value is False
    assert_no_report(app)


@pytest.mark.parametrize("replacement,code", [(b"{", "REPORT_JSON"), (b"x" * 2000001, "REPORT_SIZE_LIMIT")])
def test_invalid_comparison_replacement_retires_previous_diff_and_preserves_main_report(app, records, write_inputs, replacement, code):
    upload_files(app, write_inputs(records))
    run_check(app)
    raw = app.session_state["result_bytes"]
    select_saved_reports(app, raw, raw)
    assert app.session_state["comparison_result"]["summary"]["unchanged"] == 1
    app.button(key="clear_comparison_after").click().run()
    assert_no_comparison(app)
    assert app.button(key="compare_reports").disabled
    assert uploader(app, "Later report").value is None
    assert app.session_state["result_bytes"] == raw
    uploader(app, "Later report").set_value(("replacement.json", replacement, "application/json")).run()
    assert_no_comparison(app)
    app.button(key="compare_reports").click().run()
    assert_no_comparison(app)
    assert app.session_state["comparison_error"]["code"] == code
    app.run()
    assert_no_comparison(app)
    assert app.session_state["comparison_error"]["code"] == code
    assert app.session_state["result_bytes"] == raw
    assert report_downloads(app)


def test_context_change_is_visible_without_relabeling_same_outcomes(app, records, make_bundle):
    before = make_bundle(records)
    after = deepcopy(before)
    after["producer"]["code_sha256"] = "f" * 64
    after["ruleset"]["sha256"] = "e" * 64
    select_saved_reports(app, serialize_bundle(before), serialize_bundle(after))
    result = app.session_state["comparison_result"]
    assert {change["field"] for change in result["context_changes"]} == {"producer", "ruleset"}
    assert result["summary"]["unchanged"] == 1
    assert result["summary"]["changed"] == 0
    assert any("report context differs" in item.value.casefold() for item in app.warning)
    assert result["context_changes"] in visible_json(app)


def test_start_new_check_clears_current_inputs_filters_and_exports_but_preserves_saved_comparison(app, records, write_inputs):
    paths = write_inputs(records)
    upload_files(app, paths)
    run_check(app)
    raw = app.session_state["result_bytes"]
    select_saved_reports(app, raw, raw)
    comparison = deepcopy(app.session_state["comparison_result"])
    app.selectbox(key="outcome_filter").select("DATA_QUERY").run()
    app.text_input(key="finding_search").set_value("obsolete search").run()
    app.button(key="reset_check").click().run()
    assert_no_report(app)
    assert len(role_uploaders(app)) == 3
    assert all(u.value is None for u in role_uploaders(app))
    assert app.checkbox(key="draft_confirmed").value is False
    assert run_button(app).disabled
    assert not [button for button in app.download_button if button.key == "intake_download"]
    assert app.session_state["comparison_result"] == comparison
    assert app.download_button(key="comparison_download")
    upload_files(app, paths)
    run_check(app)
    assert app.selectbox(key="outcome_filter").value == "ALL"
    assert app.text_input(key="finding_search").value == ""
    assert app.session_state["result_bytes"] == raw


def test_corrupt_optional_registry_snapshot_does_not_block_pinned_rule_or_draft_run(monkeypatch, records, write_inputs):
    metadata = ROOT / "docs/trialtrace/review/g3_source/registry_snapshot.json"
    original_open = Path.open
    original_bytes = metadata.read_bytes()
    def injected_open(path, *args, **kwargs):
        if path == metadata:
            return io.BytesIO(b"{")
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(sys, "argv", [str(ROOT / "app.py")])
    with monkeypatch.context() as context:
        context.setattr(Path, "open", injected_open)
        app = AppTest.from_file(ROOT / "app.py", default_timeout=15).run()
        assert not app.exception
        assert any("Public registry metadata is unavailable" in item.value for item in app.caption)
        assert any("Human source review is pending" in item.value for item in app.info)
        assert len(role_uploaders(app)) == 3
        upload_files(app, write_inputs(records))
        run_check(app)
        assert app.session_state["result"]["findings"][0]["status"] == "PASS"
        assert app.session_state["result"]["clinical_validation"] is False
        assert app.session_state["result"]["review_status"] == "PENDING_TEAM_SOURCE_REVIEW"
    assert metadata.read_bytes() == original_bytes
