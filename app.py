"""Local draft upload application. Run: streamlit run app.py."""

import argparse
import hashlib
import json
from pathlib import Path

import streamlit as st

from trialtrace.cli import load_rule
from trialtrace.errors import InputError
from trialtrace.engine import validate_rule
from trialtrace.importer import HEADERS
from trialtrace.source import hash_source_pdf
from trialtrace.workflow import check_uploads
from trialtrace.inspection import inspect_uploads, build_worklist, worklist_csv, build_input_issue_list, input_issues_csv
from trialtrace.comparison import load_report, compare_reports
from trialtrace.registry_metadata import load_registry_snapshot
from trialtrace.preparation_ui import render_preparation


ROOT = Path(__file__).resolve().parent
OUTCOMES = ("PASS", "POTENTIAL_DEVIATION", "DATA_QUERY", "NOT_EVALUABLE")


def invalidate():
    for key in ("result", "result_bytes", "result_snapshot", "check_error", "selected_finding"):
        st.session_state.pop(key, None)
    for key in list(st.session_state):
        if key.startswith("selected_finding_"):
            st.session_state.pop(key, None)


def clear_upload(role):
    """Retire results before the chooser can reject a replacement in the browser.

    Streamlit does not notify Python about client-side file-size rejections.
    A selected slot is therefore read-only until this explicit clear action.
    A fresh widget identity also removes the old bytes, including on rejection.
    """
    invalidate()
    st.session_state.pop("selected_upload_" + role, None)
    key = "revision_" + role
    st.session_state[key] = st.session_state.get(key, 0) + 1


def capture_upload(role, widget_key):
    invalidate()
    uploaded = st.session_state.get(widget_key)
    if uploaded is not None:
        st.session_state["selected_upload_" + role] = (uploaded.name, uploaded.getvalue())


def reset_check():
    for role in HEADERS:
        clear_upload(role)
    st.session_state["draft_confirmed"] = False
    st.session_state["outcome_filter"] = "ALL"
    st.session_state["finding_search"] = ""


def render_intake(uploads, rule, rule_hash):
    report = inspect_uploads(uploads, rule, rule_hash)
    st.subheader("File checks")
    if all(value is None for value in uploads.values()):
        st.caption("Select the three tables to check their format and record links before calculating dates.")
    else:
        st.dataframe([{ "Table": item["role"], "State": item["state"],
                        "Records": item.get("record_count"), "Bytes": item.get("byte_count") }
                      for item in report["files"]], hide_index=True, width="stretch")
        for item in report["files"]:
            for problem in item["problems"]:
                st.error("File rejected: " + item["role"])
                st.json(problem)
        for problem in report["configuration_problems"] + report["inspection_problems"]:
            st.error("The input check could not complete.")
            st.json(problem)
        if report["ready_for_draft_check"]:
            st.success("File formats are readable. The draft check can run.")
            st.caption("Readable files may still contain missing, conflicting or unsupported records. This does not approve data or source interpretation.")
        elif report["missing_roles"]:
            st.info("Still needed: " + ", ".join(report["missing_roles"]))
        with st.expander("Record links and input issues before calculation"):
            st.write("These checks do not calculate timing outcomes. Unused records remain accounted for.")
            if report["relationship_summary"] is None or report["input_accounting"] is None:
                st.caption("Record-link checks are unavailable until all three files have readable formats.")
            else:
                st.json(report["relationship_summary"])
                st.json(report["input_accounting"])
        st.download_button("Download input checks JSON", json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name="trialtrace-input-checks.json", mime="application/json", key="intake_download", on_click="ignore")
    return report


def render_worklist(bundle):
    rows = build_worklist(bundle)
    with st.expander(f"Findings to review · {len(rows)}", expanded=bool(rows)):
        st.caption("Potential deviations, data queries and unsupported records from the whole report. Suggestions are next checks, not clinical decisions or completed reviews.")
        if rows:
            st.dataframe([{"Outcome": row["status"], "Participant": row["participant_id"], "Visit": row["visit_id"],
                           "Reason": row["reason"], "Next check": row["suggested_action"], "Visit record": row["record_ordinal"]}
                          for row in rows], hide_index=True, width="stretch", height=280)
            st.caption("Use the outcome filter and finding selector below to open any listed record's original evidence. The CSV also includes exact run, finding and evidence references.")
        else:
            st.write("No non-PASS findings in this report. This does not establish complete records or clinical compliance.")
        st.download_button("Download review list CSV", worklist_csv(bundle), file_name="trialtrace-review-list.csv",
                           mime="text/csv", key="worklist_download", on_click="ignore")
        st.caption("CSV cells that could be read as spreadsheet formulas are escaped. The evidence JSON retains the exact original values. Display filters do not change this list.")
    input_issues = build_input_issue_list(bundle)
    with st.expander(f"Input rows to review · {len(input_issues)} issues"):
        st.caption("One row per recorded input issue, including unused anchors and assignments. A record may have several issues; this is not a count of visits or participants.")
        if input_issues:
            st.dataframe([{"Table": row["source_file"], "Record": row["record_ordinal"], "Issue": row["code"],
                           "Unused row": row["is_unreferenced"], "Participant": row["participant_id"],
                           "Next check": row["suggested_action"]} for row in input_issues], hide_index=True, width="stretch", height=280)
        else:
            st.write("No row-level input issues recorded.")
        st.download_button("Download input issues CSV", input_issues_csv(bundle), file_name="trialtrace-input-issues.csv",
                           mime="text/csv", key="input_issues_download", on_click="ignore")


def invalidate_comparison():
    for key in ("comparison_result", "comparison_error", "comparison_snapshot"):
        st.session_state.pop(key, None)
    for key in list(st.session_state):
        if key.startswith("compared_finding_"):
            st.session_state.pop(key, None)


def capture_comparison(side, widget_key):
    invalidate_comparison()
    uploaded = st.session_state.get(widget_key)
    if uploaded is not None:
        st.session_state["comparison_upload_" + side] = (uploaded.name, uploaded.getvalue())


def clear_comparison(side):
    invalidate_comparison()
    st.session_state.pop("comparison_upload_" + side, None)
    revision = "comparison_revision_" + side
    st.session_state[revision] = st.session_state.get(revision, 0) + 1


def render_comparison():
    st.subheader("Compare two saved reports")
    st.write("Choose an earlier and a later evidence JSON to inspect changed dates, outcomes and source records. Reports are read as saved; this does not rerun or approve the timing rule.")
    slots = {}
    for column, side, label in zip(st.columns(2), ("before", "after"), ("Earlier report", "Later report")):
        with column:
            selected = st.session_state.get("comparison_upload_" + side)
            if selected is None:
                key = f"comparison_{side}_{st.session_state.get('comparison_revision_' + side, 0)}"
                st.file_uploader(label, key=key, max_upload_size=2, on_change=capture_comparison, args=(side, key))
            else:
                st.text(label)
                st.text(selected[0])
                st.caption(f"{len(selected[1]):,} bytes selected")
                st.button("Clear " + label.lower(), key="clear_comparison_" + side, on_click=clear_comparison, args=(side,))
            slots[side] = selected
    snapshot = tuple((side, None if item is None else hashlib.sha256(item[1]).hexdigest()) for side, item in slots.items())
    if st.session_state.get("comparison_snapshot") != snapshot:
        invalidate_comparison()
    if st.button("Compare reports", disabled=not all(slots.values()), key="compare_reports"):
        invalidate_comparison()
        try:
            before, after = (load_report(slots[side][1]) for side in ("before", "after"))
            st.session_state["comparison_result"] = compare_reports(before, after)
        except InputError as exc:
            st.session_state["comparison_error"] = exc.diagnostic()
        st.session_state["comparison_snapshot"] = snapshot
        st.rerun()
    if "comparison_error" in st.session_state:
        st.error("Report comparison rejected. No previous comparison remains available.")
        st.json(st.session_state["comparison_error"])
    elif "comparison_result" in st.session_state:
        result = st.session_state["comparison_result"]
        st.subheader("Changes between the saved reports")
        st.caption("Records match only when study, participant, site and visit identities are complete and unique. Ambiguous records remain unpaired.")
        labels = {"matched": "Uniquely matched", "changed": "Changed values", "provenance_only": "Evidence fingerprints only",
                  "unchanged": "Unchanged", "added": "Present only in later report", "removed": "Present only in earlier report",
                  "unmatched_before": "Unpaired in earlier report", "unmatched_after": "Unpaired in later report"}
        st.dataframe([{"Comparison": label, "Records": result["summary"][key]} for key, label in labels.items()], hide_index=True, width="stretch")
        st.caption("Unpaired counts include records present on only one side and ambiguous identities. These counts do not describe missed or completed activities.")
        critical = [item for item in result["context_changes"] if item["field"] != "input_files"]
        if critical:
            st.warning("Rule, source or report context differs. Review these differences before interpreting changed outcomes.")
            st.json(critical)
        with st.expander("Input file fingerprints across reports"):
            file_changes = [item for item in result["context_changes"] if item["field"] == "input_files"]
            if file_changes:
                st.json(file_changes)
            else:
                st.write("Declared input file fingerprints are unchanged.")
        with st.expander("Matched records and field changes", expanded=True):
            include_provenance = st.checkbox("Include records whose only changes are evidence fingerprints", key="comparison_show_provenance")
            changed = [item for item in result["matched"] if any(field != "evidence_provenance" or include_provenance for field in item["changed_fields"])]
            if changed:
                selection_key = "compared_finding_" + hashlib.sha256(json.dumps([(item["before_finding_id"], item["after_finding_id"]) for item in changed]).encode()).hexdigest()
                chosen = st.selectbox("Select changed record", range(len(changed)), key=selection_key,
                                      format_func=lambda i: " · ".join(str(changed[i]["identity"].get(k) or "—") for k in ("participant_id", "site_id", "visit_id")))
                item = changed[chosen]
                values = []
                for field in ("status", "reason", "visit_code"):
                    if field in item["changes"]:
                        change = item["changes"][field]
                        values.append({"Field": field.replace("_", " ").title(), "Earlier": str(change["before"]), "Later": str(change["after"])})
                if "calculation" in item["changes"]:
                    change = item["changes"]["calculation"]
                    for field in ("actual", "target", "earliest", "latest", "days_outside"):
                        before_value = (change["before"] or {}).get(field)
                        after_value = (change["after"] or {}).get(field)
                        if before_value != after_value:
                            values.append({"Field": field.replace("_", " ").title(), "Earlier": str(before_value) if before_value is not None else "No calculation",
                                           "Later": str(after_value) if after_value is not None else "No calculation"})
                if values:
                    st.dataframe(values, hide_index=True, width="stretch")
                st.caption("Changed fields: " + ", ".join(field.replace("_", " ") for field in item["changed_fields"]))
                with st.expander("Exact comparison record and source evidence"):
                    st.json(item)
            else:
                st.write("No changed outcome, timing, reason or source-row values among the uniquely matched records.")
        with st.expander("Unpaired and ambiguous records", expanded=bool(result["unmatched_before"] or result["unmatched_after"])):
            unpaired = [{"Report": label, "Participant": (item["identity"] or {}).get("participant_id"),
                         "Visit": (item["identity"] or {}).get("visit_id"), "Record": item["record_ordinal"], "Reason": item["reason"]}
                        for label, key in (("Earlier", "unmatched_before"), ("Later", "unmatched_after")) for item in result[key]]
            if unpaired:
                st.dataframe(unpaired, hide_index=True, width="stretch")
            else:
                st.write("Every record has a unique matching identity in the other report.")
            with st.expander("Exact unpaired identities and report references"):
                st.json({key: result[key] for key in ("unmatched_before", "unmatched_after", "ambiguous_groups")})
        st.download_button("Download comparison JSON", json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name="trialtrace-comparison.json", mime="application/json", key="comparison_download", on_click="ignore")
        st.caption("This comparison is separate from both original evidence reports; neither report is changed.")
    else:
        st.info("No current comparison. Choose both saved reports, then compare.")


def render_source(rule, rule_hash, source):
    st.subheader("Public source · draft interpretation")
    st.write("NCT04470427 · Moderna mRNA-1273-P301")
    st.write("Supported check: documented OL-D8 safety phone call, anchored to an explicitly mapped actual OL-D1 vaccination.")
    earliest = rule["offset_days"] + rule["lower_days"]
    latest = rule["offset_days"] + rule["upper_days"]
    st.write(f"Candidate window: vaccination date {earliest:+d} through {latest:+d} calendar days, inclusive. Table {rule['source_locator']['table']}, amendment {rule['amendment']}, {rule['document_date']}.")
    st.link_button("Open public protocol", rule["source_url"])
    st.link_button("Open trial registry", "https://clinicaltrials.gov/study/NCT04470427")
    metadata_path = ROOT / "docs/trialtrace/review/g3_source/registry_snapshot.json"
    try:
        snapshot = load_registry_snapshot(metadata_path)
    except InputError:
        st.caption("Public registry metadata is unavailable. The pinned protocol and rule remain available below.")
    else:
        study = snapshot["study"]
        st.text(f"Registry: {study['overall_status']} · {study['lead_sponsor']}")
        st.caption(f"Public metadata fetched {snapshot['source']['fetched_at_utc'][:10]}; registry updated {study['last_update_posted']}. Snapshot, not a live feed.")
        st.caption("The registry contains aggregate results, not the participant visit dates used in this check.")
        with st.expander("Fetched public registry metadata"):
            st.json(snapshot)
    with st.expander("Rule and source provenance"):
        st.caption("Rule SHA-256")
        st.code(rule_hash, language=None)
        st.caption("Source PDF SHA-256 for this run")
        st.code(source["pdf_sha256"] if source else "Not available — source PDF bytes not supplied to this app", language=None)
        st.write("A file hash identifies bytes. It does not approve the interpretation or verify participant records.")
        st.json(rule)
    st.info("Human source review is pending. This app cannot infer eligibility, applicable amendment, missing activities, or the adequacy of a safety assessment.")


def render_report(bundle, encoded):
    st.subheader("Results from your uploaded files")
    st.caption("Draft engineering · synthetic records · source interpretation pending review")
    counts = bundle["summary"]["statuses"]
    for col, status in zip(st.columns(4), OUTCOMES):
        col.metric(status.replace("_", " ").title(), counts[status])
    st.write(f"{len(bundle['findings'])} documented visit record(s) checked. Counts always describe the whole report.")
    st.download_button("Download evidence JSON", encoded, file_name="trialtrace-evidence.json", mime="application/json", key="evidence_download", on_click="ignore")
    st.caption("The download contains the full report, including original evidence and unresolved records. Filters do not change it.")
    render_worklist(bundle)
    first, second = st.columns([1, 2])
    status = first.selectbox("Outcome filter", ("ALL", *OUTCOMES), key="outcome_filter")
    search = second.text_input("Search participant, visit, site or reason", key="finding_search").casefold().strip()
    findings = [f for f in bundle["findings"] if (status == "ALL" or f["status"] == status) and (not search or search in " ".join(str(f.get(k) or "") for k in ("participant_id", "visit_id", "site_id", "reason")).casefold())]
    st.caption(f"Showing {len(findings)} of {len(bundle['findings'])} findings")
    if findings:
        by_id = {f["finding_id"]: f for f in findings}
        # New options need a new widget identity: reusing a deleted session-state
        # key can leave Streamlit's browser label on a no-longer-listed finding.
        selection_key = "selected_finding_" + hashlib.sha256("|".join(by_id).encode()).hexdigest()
        selected = st.selectbox("Select finding", list(by_id), key=selection_key, format_func=lambda key: " · ".join(str(by_id[key].get(k) or "—") for k in ("participant_id", "visit_id", "status")))
        finding = by_id[selected]
        with st.container(border=True):
            st.subheader("Selected finding")
            st.text(f"{finding['status']} · {finding['reason']}")
            if finding["calculation"] is not None:
                st.table([{"Date": k.replace("_", " ").title(), "Value": str(v)} for k, v in finding["calculation"].items()])
            else:
                st.write("No timing conclusion. Resolve the listed evidence or applicability issues first.")
            st.caption("Original records used for this finding")
            for item in finding["evidence"]:
                with st.expander(f"{item['source_file']} · record {item['record_ordinal']}", expanded=True):
                    st.json(item["raw_record"])
                    st.caption("Exact source file SHA-256")
                    st.code(item["sha256"], language=None)
    elif not bundle["findings"]:
        st.info("No visit records were supplied. Zero findings does not mean that expected activities occurred.")
    else:
        st.info("No findings match these filters. The complete report remains available above.")
    with st.expander("Input accounting, including unused or problematic rows"):
        st.json(bundle["input_accounting"])
    with st.expander("Report identity and input fingerprints"):
        st.json({key: bundle[key] for key in ("run_id", "producer", "source", "ruleset", "input_files", "limitations")})


def main():
    st.set_page_config(page_title="TrialTrace · Timing evidence", page_icon="🔎", layout="wide")
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-pdf", type=Path)
    args = parser.parse_args()
    st.caption("TRIALTRACE / LOCAL WORKSPACE")
    st.title("TrialTrace timing checks")
    st.write("Check recorded safety-call timing against one supported draft rule. Map a spreadsheet or supply prepared tables, then inspect the evidence behind each result.")
    st.warning("DRAFT · Synthetic inputs only. Public protocol data is real; participant examples are synthetic. Source interpretation awaits human review. No clinical validation.")
    try:
        rule, rule_hash = load_rule(ROOT / "rules/candidate_rule.json")
        validate_rule(rule)
        source = hash_source_pdf(args.source_pdf) if args.source_pdf else None
    except (InputError, OSError) as exc:
        invalidate()
        st.error("The configured rule or source file is invalid or unavailable. No report is available.")
        st.text(str(exc))
        st.stop()
    with st.sidebar:
        render_source(rule, rule_hash, source)
    preparation, workspace, saved, comparison = st.tabs(["Map one spreadsheet", "Check uploaded data", "Open saved evidence report", "Compare saved reports"])
    with preparation:
        render_preparation(rule, rule_hash, source)
    with workspace:
        st.subheader("1. Supply the three source tables")
        st.caption("UTF-8 CSV · up to 1,000,000 bytes and 500 rows per table · dates YYYY-MM-DD. Files stay in this local app session; no database or model service is used.")
        st.caption("To replace or remove a selected file, clear it first. This also clears the current report before another file is chosen.")
        with st.expander("How the three tables connect"):
            st.write("Each visit names an anchor_id and assignment_id. The linked records must agree on study_id, participant_id and site_id. The anchor is the actual vaccination date; the visit is a documented completed safety phone call.")
            st.write("Keep identifiers exactly as recorded. Dates use YYYY-MM-DD. Download the header templates below; unsupported events or unresolved mappings remain visible as uncertainties.")
            st.write("This local workflow accepts synthetic draft examples only. The application cannot detect or de-identify real participant data.")
        uploads = {}
        for column, (role, headers) in zip(st.columns(3), HEADERS.items()):
            with column:
                upload_key = f"upload_{role}_{st.session_state.get('revision_' + role, 0)}"
                selected_upload = st.session_state.get("selected_upload_" + role)
                if selected_upload is None:
                    st.file_uploader(role, key=upload_key, on_change=capture_upload, args=(role, upload_key), help="Required headers: " + ", ".join(headers), max_upload_size=1)
                else:
                    st.text(role)
                    with st.container(border=True):
                        st.text(selected_upload[0])
                        st.caption(f"{len(selected_upload[1]):,} bytes selected")
                    st.button("Clear " + role, key="clear_" + role, on_click=clear_upload, args=(role,))
                uploads[role] = selected_upload
                st.download_button("Download " + role + " template", ",".join(headers) + "\n", file_name=role, mime="text/csv", key="template_" + role, on_click="ignore")
        if any(value is not None for value in uploads.values()):
            st.button("Start a new check", key="reset_check", on_click=reset_check)
        intake = render_intake(uploads, rule, rule_hash)
        confirmed = st.checkbox("These are synthetic records; run the unreviewed draft timing check.", key="draft_confirmed", on_change=invalidate)
        snapshot = tuple((role, None if value is None else (value[0], hashlib.sha256(value[1]).hexdigest())) for role, value in uploads.items()) + (("rule", rule_hash), ("source", None if source is None else source["pdf_sha256"]), ("draft", confirmed))
        if st.session_state.get("result_snapshot") != snapshot:
            invalidate()
        st.subheader("2. Run the timing check")
        ready = confirmed and intake["ready_for_draft_check"]
        if st.button("Run timing check", type="primary", disabled=not ready):
            invalidate()
            try:
                bundle, encoded = check_uploads(uploads, rule, rule_hash, draft_confirmed=confirmed, source_metadata=source)
            except InputError as exc:
                st.session_state.check_error = exc.diagnostic()
                st.session_state.result_snapshot = snapshot
            else:
                st.session_state.result = bundle
                st.session_state.result_bytes = encoded
                st.session_state.result_snapshot = snapshot
            st.rerun()
        if st.session_state.get("check_error"):
            st.error("Input rejected. No current findings or evidence download are available.")
            st.json(st.session_state.check_error)
        elif "result" in st.session_state:
            render_report(st.session_state.result, st.session_state.result_bytes)
        else:
            st.info("No current report. Upload all three tables, confirm draft mode, then run the check. Any input change clears the previous results.")
    with saved:
        st.write("The separate evidence viewer reads saved JSON reports. It does not rerun the timing engine. Use the first tab to calculate from CSV files.")
        viewer = ROOT / "features/evidence_viewer"
        if (viewer / "index.html").exists():
            html = (viewer / "index.html").read_text()
            html = html.replace('<link rel="stylesheet" href="style.css">', '<style>' + (viewer / "style.css").read_text() + '</style>')
            for asset in ("contract.js", "app.js"):
                html = html.replace(f'<script src="{asset}"></script>', '<script>' + (viewer / asset).read_text() + '</script>')
            st.iframe(html, height=1050)
        else:
            st.info("The separate viewer has not been installed in this checkout.")
    with comparison:
        render_comparison()


if __name__ == "__main__":
    main()
