# Browser-interface review — 18 October 2026

This records actual Codex in-app-browser actions against the static application served at 127.0.0.1:8504. It does not certify all browsers, clinical correctness, representative trial exports or workflow benefit.

## Executed behavior

- The first external runtime loader failed. Its rendered error is retained in `browser/initial-runtime-failure.txt`. No result was substituted.
- Serving runtime files from the same origin exposed an unsupported classic-worker path in this browser. The original rendered message was “Classic web workers are not supported.” The saved `browser/classic-worker-failure.txt` is only a no-change AX diff, so the quoted observation here comes from the actual tool transcript, not a complete saved snapshot. The implementation now uses a module worker and the official Pyodide ES module.
- Reloading reached **Engine ready**. Loading the seven-row synthetic CSV required explicit mapping/scope confirmation before calculation.
- Actual results: 1 PASS, 1 POTENTIAL_DEVIATION, 4 DATA_QUERY, 1 NOT_EVALUABLE. The selected late record displayed the February 29–March 3 inclusive window and March 4 actual date, one day outside.
- Browser-downloaded JSON matched the existing native-Python evidence byte for byte. Every ZIP member matched its canonical counterpart. See `browser/parity-result.json`.
- Changing the input call date to March 5 and rerunning produced two days outside. The generated report and visible result are retained.
- Filtering to data queries selected the missing-vaccination-date record, explained the absent field and requested source review without an estimated date.
- A malformed actual file selection produced ROW_WIDTH, with no stale result or downloads. A 1,000,001-byte file was rejected before calculation. The oversized input was exactly that many ASCII x bytes; its generated copy stays local.
- Changing the vaccination column cleared scope confirmation and disabled Run. Restoring it required confirmation again.
- A second route used the real file chooser, selected the original CSV, manually chose all eight columns and the exact `done` completion value, then calculated. Its downloaded JSON also matched the canonical bytes.
- How it works, Evidence & scope, and brand navigation were exercised. At a 390px viewport, document/body widths were both 390px; a screenshot is retained. This is a single responsive spot check, not full mobile accessibility certification. After resetting viewport, an initial navigation click had no effect; a subsequent normal click opened the walkthrough.
- The self-contained output package was separately served on port 8505. Its actual browser calculation and JSON download matched the canonical native-Python report.
- Source strings are escaped before rendering. Invalid calendar strings are displayed literally instead of JavaScript silently normalizing them. The bridge test confirms no timing calculation for February 30.

## Deployment and access

The private deployment succeeded through Sites. The owner sign-in attempt in the in-app browser failed with an OpenAI route error (`400 Invalid content type: text/html; charset=UTF-8`), then automatic security verification appeared on retry. No authentication bypass, audience change or claim of a successful hosted calculation was made. The user explicitly requested that access remain private. The deployment receipt establishes hosting; local-browser checks establish the application behavior. These are separate claims.

## Other execution details

The first Sites packaging command failed because its subprocess could not find Node. Repeating the same helper with the bundled Node directory on PATH succeeded. No source or archive was deployed before successful packaging. An attempted CDN license URL returned HTTP403; the exact official Pyodide GitHub-tag license was fetched instead with normal TLS verification. Python and dependency notices are included in the distribution.

All 457 application tests passed (the prior 447 plus ten browser-boundary cases). Core code, rule, evidence schema and existing Streamlit application bytes remain unchanged. Command records are in `commands/`; source/runtime fingerprints are in the generated build-info and runtime-lock files.
