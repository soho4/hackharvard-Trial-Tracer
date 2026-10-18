"""UI for explicit column mapping; isolated state from the existing three-table flow."""
import json

import streamlit as st

from .errors import InputError
from .inspection import worklist_csv
from .preparation import FIELDS, inspect_spreadsheet, prepare_spreadsheet, evidence_package


def invalidate_mapping():
    for key in ("prep_prepared", "prep_result", "prep_encoded", "prep_package", "prep_error"):
        st.session_state.pop(key, None)
    st.session_state["prep_scope"] = False


def capture_sheet(widget_key):
    invalidate_mapping()
    for key in list(st.session_state):
        if key.startswith("prep_column_") or key == "prep_completed":
            st.session_state.pop(key, None)
    uploaded = st.session_state.get(widget_key)
    if uploaded is not None:
        st.session_state["prep_selected"] = (uploaded.name, uploaded.getvalue())


def clear_sheet():
    invalidate_mapping()
    st.session_state.pop("prep_selected", None)
    st.session_state["prep_revision"] = st.session_state.get("prep_revision", 0) + 1
    for key in list(st.session_state):
        if key.startswith("prep_column_") or key == "prep_completed":
            st.session_state.pop(key, None)


def retire_prepared():
    for key in ("prep_prepared", "prep_result", "prep_encoded", "prep_package", "prep_error"):
        st.session_state.pop(key, None)


def render_preparation(rule, rule_sha256, source):
    st.subheader("Check one spreadsheet")
    st.write("Use a CSV with one safety-call record per row, including its vaccination reference. Choose which columns mean what; preview the mapping before running.")
    st.caption("This is a limited import path, not a direct REDCap, OpenClinica or CDISC connector. A CSV must contain both actual dates, identifiers and call completion status. Multi-event rows, partial dates and missing columns are not inferred.")
    with st.expander("What this import can and cannot establish"):
        st.write("The selected columns must describe the actual vaccination and safety call, not consent, booking or general form-entry dates. A form marked complete is not evidence that the call occurred.")
        st.write("You declare draft Table 21 scope; this does not establish participant eligibility or amendment applicability. Repeated vaccination identifiers remain duplicate-key queries. No rows are dropped or merged.")
        st.write("All original columns stay in the downloadable source file, including columns unused by the calculation. This app cannot detect or remove patient information. Synthetic records only.")
    selected = st.session_state.get("prep_selected")
    if selected is None:
        key = f"prep_upload_{st.session_state.get('prep_revision', 0)}"
        st.file_uploader("Source spreadsheet CSV", max_upload_size=1, key=key, on_change=capture_sheet, args=(key,))
        st.info("Choose your CSV to inspect its columns. The three-table route remains available in Check uploaded data.")
        return
    st.text(selected[0])
    st.button("Clear source spreadsheet", key="prep_clear", on_click=clear_sheet)
    try:
        sheet = inspect_spreadsheet(selected[1], selected[0])
    except InputError as exc:
        retire_prepared()
        st.error("Spreadsheet rejected. No prepared result remains available.")
        st.json(exc.diagnostic())
        return
    st.caption(f"{len(sheet['records'])} logical records · {sheet['byte_count']:,} bytes · original values preserved")
    if not sheet["records"]:
        st.info("This file has headers but no records. There is nothing to map or calculate.")
        return
    with st.expander("Original source preview"):
        st.caption("First 20 records only; all records are retained and processed. Grid export is disabled; the full evidence package contains the exact source bytes.")
        st.dataframe([r["raw_record"] for r in sheet["records"][:20]], hide_index=True, width="stretch")
    st.subheader("1. Identify the source columns")
    mapping = {}
    columns = st.columns(2)
    for index, (field, label) in enumerate(FIELDS.items()):
        with columns[index % 2]:
            mapping[field] = st.selectbox(label, [None, *sheet["headers"]], format_func=lambda v: "Choose a column" if v is None else v,
                                         key="prep_column_" + field, on_change=invalidate_mapping)
    status_column = mapping["visit_status"]
    values = sorted({r["raw_record"][status_column] for r in sheet["records"] if r["raw_record"][status_column].strip()}) if status_column else []
    completed = st.selectbox("Exact value meaning the safety call was completed", [None, *values],
                             format_func=lambda v: "Choose a value" if v is None else v, key="prep_completed", on_change=invalidate_mapping)
    st.caption("Only that exact value maps to COMPLETED. All other values stay unconfirmed. Dates must already be YYYY-MM-DD; values are never silently corrected.")
    st.write("Declared context for generated records: actual OL-D1 vaccination → OL-D8 safety phone call; candidate A10_DRAFT_2 / TABLE21; synthetic draft mapping. These are declarations, not facts inferred from your CSV.")
    confirmed = st.checkbox("These are synthetic records; I confirm the column meanings and declare this batch belongs to the draft Table 21 scope.", key="prep_scope", on_change=retire_prepared)
    ready = all(mapping.values()) and completed is not None and confirmed
    if st.button("Prepare mapped records", key="prep_prepare", disabled=not ready):
        retire_prepared()
        try:
            st.session_state["prep_prepared"] = prepare_spreadsheet(selected[1], selected[0], mapping, completed, rule, rule_sha256, scope_confirmed=confirmed)
        except InputError as exc:
            st.session_state["prep_error"] = exc.diagnostic()
    if "prep_error" in st.session_state:
        st.error("Preparation or calculation rejected. No previous report is available.")
        st.json(st.session_state["prep_error"])
    prepared = st.session_state.get("prep_prepared")
    if prepared is None:
        return
    st.subheader("2. Review the mapped records")
    st.caption("First 20 of all mapped records. Duplicates, blanks and invalid dates remain for the engine to report.")
    st.dataframe([{"Source record": r["record_ordinal"], **{label: r["raw_record"][mapping[field]] for field, label in FIELDS.items()}} for r in sheet["records"][:20]], hide_index=True, width="stretch")
    st.caption("Columns not used in the calculation, but retained in source.csv: " + (", ".join(prepared["manifest"]["unmapped_columns"]) or "none"))
    with st.expander("Exact mapping, declared constants and row lineage"):
        st.json(prepared["manifest"])
    if st.button("Run mapped draft check", key="prep_run", type="primary"):
        for key in ("prep_result", "prep_encoded", "prep_package", "prep_error"):
            st.session_state.pop(key, None)
        try:
            bundle, encoded, package = evidence_package(prepared, rule, rule_sha256, source_metadata=source)
            st.session_state.update(prep_result=bundle, prep_encoded=encoded, prep_package=package)
        except InputError as exc:
            st.session_state["prep_error"] = exc.diagnostic()
        st.rerun()
    if "prep_result" not in st.session_state:
        return
    bundle = st.session_state["prep_result"]
    st.subheader("Results from the mapped spreadsheet")
    for col, (status, count) in zip(st.columns(4), bundle["summary"]["statuses"].items()):
        col.metric(status.replace("_", " ").title(), count)
    st.caption("One finding per source row. The full package includes the original CSV, exact mapping, generated tables and evidence JSON. The JSON alone describes generated tables.")
    st.download_button("Download complete evidence package", st.session_state["prep_package"], file_name="trialtrace-mapped-evidence.zip", mime="application/zip", key="prep_package_download", on_click="ignore")
    st.download_button("Download mapped evidence JSON", st.session_state["prep_encoded"], file_name="trialtrace-mapped-evidence.json", mime="application/json", key="prep_json_download", on_click="ignore")
    st.download_button("Download mapped review list CSV", worklist_csv(bundle), file_name="trialtrace-mapped-review.csv", mime="text/csv", key="prep_review_download", on_click="ignore")
    st.caption("The review CSV escapes formula-like cells. Original/generated machine-input CSV files in the package retain exact values.")
    st.dataframe([{"Source record": f["record_ordinal"], "Participant": f["participant_id"], "Outcome": f["status"], "Reason": f["reason"]} for f in bundle["findings"]], hide_index=True, width="stretch")
    chosen = st.selectbox("Inspect source row and finding", range(len(bundle["findings"])),
                          format_func=lambda i: f"Record {i+1} · {bundle['findings'][i]['participant_id']} · {bundle['findings'][i]['status']}",
                          key="prep_finding_" + bundle["run_id"])
    finding = bundle["findings"][chosen]
    st.write("Original source row, including unused columns")
    st.json(sheet["records"][chosen]["raw_record"])
    if finding["calculation"] is None:
        st.info("No timing conclusion for this record: " + finding["reason"])
    else:
        st.table([{"Calculation": k.replace("_", " "), "Value": str(v)} for k, v in finding["calculation"].items()])
    with st.expander("Generated evidence rows for this finding"):
        st.json(finding)
