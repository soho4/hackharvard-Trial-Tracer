# Browser application

This is the presentation interface for the existing TrialTrace Python checker. It accepts one explicitly mapped CSV and runs the same source code inside Pyodide. The earlier Streamlit interface remains available for three-table input, saved evidence viewing and comparison; those features have not been ported into this interface.

## Rebuild and launch

From the repository root, after the normal Python development installation:

```sh
.venv/bin/python tools/vendor_web_runtime.py
.venv/bin/python tools/build_web.py
.venv/bin/python -m http.server 8504 --bind 127.0.0.1 --directory web/dist
```

Open http://127.0.0.1:8504. Loading index.html directly through file:// is unsupported because module workers need an HTTP origin. No Node build or JavaScript package installation is needed.

The initial runtime fetch uses curl with ordinary TLS verification. Generated runtime assets and dist are ignored; runtime-lock.json records the pinned assets. The build verifies their hashes. Dependency wheel hashes also match the official Pyodide lock. Redistribution notices travel with the generated site.

## Files and responsibilities

- `src/index.html`, `style.css`: semantic page shell and responsive presentation.
- `src/app.js`: explicit mapping, UI lifecycle, readable finding explanations and downloads. It never calculates a timing outcome.
- `src/engine-worker.js`: serialized module-worker requests and Python runtime loading.
- `src/bridge.py`: bounded calls into existing CSV preparation, validation, engine and exports. It returns structured failures, never sample answers.
- `runtime-lock.json`: runtime versions, sizes and SHA-256 fingerprints.
- `../tools/build_web.py`: packages the exact current Python sources, schema, fixed rule and synthetic examples; emits build-info.json.
- `../tests/test_web_bridge.py`: boundary tests against canonical outputs, changed dates, missing information and rejected requests.

## Data flow

CSV bytes + column meanings + exact completion value + explicit synthetic declaration
→ shared Python parser and preparation
→ internal anchors, visits and assignments
→ unchanged deterministic checker
→ canonical evidence and source-preserving ZIP
→ plain-language display and local downloads.

Selected CSV data stays in browser memory. Runtime assets are downloaded from the same site; fonts come from Google Fonts. No participant database, API key, runtime language model, vendor connector or server upload exists. Refreshing closes the current review session; save evidence before leaving. This is not offline-installable and mobile behavior is not a comprehensive device certification.

## Review boundaries

Synthetic data only; one draft Moderna Table 21 rule. Source interpretation is pending independent human review. The public protocol is linked, not bundled or treated as participant data. Evidence reports correctly say source PDF bytes were not supplied to the run. Site access is separate from clinical readiness. See `docs/trialtrace/HACKATHON_PRESENTER.md` and `docs/trialtrace/review/web/` for the demonstration and executed checks.
