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
    if metadata_path.exists():
        snapshot = json.loads(metadata_path.read_text())
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
    st.write("Upload three tables, check the supported timing rule, and inspect every result against the original records.")
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
    workspace, saved = st.tabs(["Check uploaded data", "Open saved evidence report"])
    with workspace:
        st.subheader("1. Supply the three source tables")
        st.caption("UTF-8 CSV · up to 1,000,000 bytes and 500 rows per table · dates YYYY-MM-DD. Files stay in this local app session; no database or model service is used.")
        st.caption("To replace or remove a selected file, clear it first. This also clears the current report before another file is chosen.")
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
        confirmed = st.checkbox("These are synthetic records; run the unreviewed draft timing check.", key="draft_confirmed", on_change=invalidate)
        snapshot = tuple((role, None if value is None else (value[0], hashlib.sha256(value[1]).hexdigest())) for role, value in uploads.items()) + (("rule", rule_hash), ("source", None if source is None else source["pdf_sha256"]), ("draft", confirmed))
        if st.session_state.get("result_snapshot") != snapshot:
            invalidate()
        st.subheader("2. Run the timing check")
        ready = confirmed and all(value is not None for value in uploads.values())
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


if __name__ == "__main__":
    main()
