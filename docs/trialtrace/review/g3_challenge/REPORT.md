# Independent G3 core challenge

The actual current-source CLI passed 24 newly authored synthetic visit cases: 9 PASS, 5 POTENTIAL_DEVIATION, 7 DATA_QUERY, and 3 NOT_EVALUABLE. Expected arithmetic was written as literal calendar answers before execution, including years 0001 and 9999, nonleap centuries 1900 and 2100, leap centuries 2000 and 2400, exact endpoints, and early/late distances.

The three new CSV files use unfamiliar identifiers, Unicode identity values, reversed header order, UTF-8 BOM, CRLF, and a quoted multiline mapping note containing literal markup. Ten additional cases challenge missing/wrong-person/case-sensitive references, duplicate anchors, unknown completion, unsupported event/anchor kinds, unresolved scope, invalid dates, and derived overflow. Unreferenced invalid anchor and assignment rows remain in accounting. Every exported evidence row, ordinal, and SHA-256 was checked against these actual input files. Repeated execution produced identical bytes.

The separate challenge suite passed 8 tests, including changing one actual date and verifying only its arithmetic changes, plus six corrupt replacements: embedded NUL, incorrect delimiter, blank record, extra cell, unterminated quote, and invalid UTF-8. Each corrupt replacement returned a structured failure, removed the success target, and preserved the previous valid report separately.

Evidence:

- `actual_run/challenge_report.json` binds the result to actual input, rule, code, and output digests.
- `actual_run/inputs/` contains the three unfamiliar real CSV files.
- `actual_run/independently_authored_expected.json` is the test-only answer key; the application does not receive it.
- `actual_run/actual_bundle.json` is the actual computed export.
- `commands/20261018T082544.350665Z-independent-g3-real-file-challenge-adf53d77/` records the standalone challenge command with exit 0.
- `commands/20261018T082557.102990Z-independent-g3-challenge-pytest-4fb469ab/` records 8 passing tests with exit 0.

This is an independent AI engineering challenge of synthetic inputs. It does not establish human source approval, clinical validation, or browser/UI acceptance. The CLI uses current repository source explicitly through `PYTHONPATH`; this is not a fresh installed-wheel claim. Later production changes require rerunning affected checks.
