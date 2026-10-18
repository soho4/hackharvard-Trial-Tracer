# Research log

Technical observations only; no human source approval.

- 2026-10-18 UTC: Python CSV docs https://docs.python.org/3.13/library/csv.html checked for newline handling, string-preserving records, and strict errors. Use newline="" and explicit header/width checks; add quote-state scanning because strict parser alone allows stray unquoted quotes. Tests cover both.
- Python datetime docs https://docs.python.org/3.13/library/datetime.html checked for calendar date arithmetic and representable date bounds. Exact regex precedes fromisoformat; overflow becomes row query.
- jsonschema validator docs https://python-jsonschema.readthedocs.io/en/stable/validate/ checked for Draft202012Validator usage. Schema cannot enforce cross-record provenance or real dates, so explicit semantics will supplement it.
- Exact protocol acquisition and technical visual observations are in source_check/SOURCE_CHECK.md. G0 remains blocked; preserve note-number discrepancy for human review.
