# Research log

Technical observations only; no human source approval.

- 2026-10-18 UTC: Python CSV docs https://docs.python.org/3.13/library/csv.html checked for newline handling, string-preserving records, and strict errors. Use newline="" and explicit header/width checks; add quote-state scanning because strict parser alone allows stray unquoted quotes. Tests cover both.
- Python datetime docs https://docs.python.org/3.13/library/datetime.html checked for calendar date arithmetic and representable date bounds. Exact regex precedes fromisoformat; overflow becomes row query.
- jsonschema validator docs https://python-jsonschema.readthedocs.io/en/stable/validate/ checked for Draft202012Validator usage. Schema cannot enforce cross-record provenance or real dates, so explicit semantics will supplement it.
- Exact protocol acquisition and technical visual observations are in source_check/SOURCE_CHECK.md. G0 remains blocked; preserve note-number discrepancy for human review.

- Actual origin/abinet/evidence-viewer at 1b216519e93866bca3fc36be174ec0f5bf05f793: schema and six fixtures exactly match the handoff. Both isolated validators accept eight current normal-date reports. Direct probes show Date.UTC remaps years 0-99 in the teammate validator, causing 0001/0099 rejection; unchanged reference validator and core accept those valid dates. Source and probe evidence: review/core/viewer_year_results.json. Preserve teammate source; fix in G3.
- Independent technical review found duplicate-evidence amplification, 140k-cell diagnostic ambiguity, malformed CLI/stale-output errors, unpaired-surrogate configuration, abbreviated flags and case/hardlink collisions. Each received targeted regression tests or actual filesystem probes and passed recheck; see review/core/REVIEW.md. This is AI technical review, not independent human source approval.
- Fresh venv with locked dependencies and a regular wheel: imported installed package outside checkout with Python -I, verified exact schema and source digest, and reproduced current CLI output bytes. clean_install.json records versions and paths. No another-machine claim.

## G3 continuation, 18 October 2026

- Actual official registry API https://clinicaltrials.gov/api/v2/studies/NCT04470427
  returned HTTP 200 with TLS verification. Its protocol identity/date/size agree
  with the candidate and previously acquired PDF. The fetched metadata and hash
  are in review/g3_source/registry_snapshot.json; raw response stays local. The
  registry provides aggregate results and no matching individual visit/assignment
  records. The app displays a dated source card, never a fabricated patient feed.
- Official Streamlit file-uploader documentation
  https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader and
  installed 1.66.0 signatures were checked for upload bytes, callbacks and limits.
  Actual browser testing showed that an oversized replacement is rejected before
  the Python callback. The selected-file/explicit-Clear design follows that observed
  lifecycle rather than assuming every attempted replacement reaches Python.
- Official iframe documentation https://docs.streamlit.io/develop/api-reference/layout/st.iframe
  and installed API were checked for inline trusted viewer HTML. Replacing the
  deprecated components.html call removed its warning; fresh AppTest and actual
  served Chrome checks passed for the final app fingerprint.
- JavaScript early-year validation was checked with literal years 0001, 0004 and
  0099. setUTCFullYear avoids Date.UTC's 0–99 remapping. Year 0000 remains invalid;
  schema and the candidate window are unchanged. Fifty-eight viewer tests passed.
- Actual standard Chrome captured the embedded viewer Blob download and verified
  exact original bytes. The same capture did not succeed in the in-app browser;
  the cause is unverified. Print CSS was exercised, but no OS print/PDF-pagination
  claim is made. See review/g3_viewer/embedded_REVIEW.md.
- The final app was verified against the installed CLI and a fresh Python -I wheel
  installation. New evidence lives under review/g3_clean_install; the earlier
  clean_install.json is retained as its original core-only checkpoint.
