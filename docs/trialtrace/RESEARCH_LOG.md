# Research log

Technical observations only; no human source approval.

- 2026-10-18 UTC: Python CSV docs https://docs.python.org/3.13/library/csv.html checked for newline handling, string-preserving records, and strict errors. Use newline="" and explicit header/width checks; add quote-state scanning because strict parser alone allows stray unquoted quotes. Tests cover both.
- Python datetime docs https://docs.python.org/3.13/library/datetime.html checked for calendar date arithmetic and representable date bounds. Exact regex precedes fromisoformat; overflow becomes row query.
- jsonschema validator docs https://python-jsonschema.readthedocs.io/en/stable/validate/ checked for Draft202012Validator usage. Schema cannot enforce cross-record provenance or real dates, so explicit semantics will supplement it.
- Exact protocol acquisition and technical visual observations are in source_check/SOURCE_CHECK.md. G0 remains blocked; preserve note-number discrepancy for human review.

- Actual origin/abinet/evidence-viewer at 1b216519e93866bca3fc36be174ec0f5bf05f793: schema and six fixtures exactly match the handoff. Both isolated validators accept eight current normal-date reports. Direct probes show Date.UTC remaps years 0-99 in the teammate validator, causing 0001/0099 rejection; unchanged reference validator and core accept those valid dates. Source and probe evidence: review/core/viewer_year_results.json. Preserve teammate source; fix in G3.
- Independent technical review found duplicate-evidence amplification, 140k-cell diagnostic ambiguity, malformed CLI/stale-output errors, unpaired-surrogate configuration, abbreviated flags and case/hardlink collisions. Each received targeted regression tests or actual filesystem probes and passed recheck; see review/core/REVIEW.md. This is AI technical review, not independent human source approval.
- Fresh venv with locked dependencies and a regular wheel: imported installed package outside checkout with Python -I, verified exact schema and source digest, and reproduced current CLI output bytes. clean_install.json records versions and paths. No another-machine claim.
