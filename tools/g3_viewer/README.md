# Isolated teammate viewer integration review

The original feature from teammate commit `1b216519e93866bca3fc36be174ec0f5bf05f793`
is preserved byte-for-byte under `native_snapshot/`. `provenance.json` identifies
all 18 files and their SHA-256 hashes. No file under `features/evidence_viewer/`
is modified by these review tools.

`candidate/` has the same feature with two focused proposed repairs:

1. `calendar_date_fix.patch`: accept calendar years 0001–0099 without JavaScript's
   `Date.UTC` remapping to 1900–1999, while rejecting year zero and impossible dates.
2. `layout_overflow_fix.patch`: wrap long engine run/finding IDs and uploaded
   filenames so they do not extend beyond a narrow screen.

`integration_fixes.patch` combines both. The integrator owns importing the feature
and applying any repair. `prepare.py` reconstructs both isolated copies from the
pinned Git commit; it overwrites only these review copies and proposal files.

## Reproduce

From the repository root with the Python development environment installed:

```sh
.venv/bin/python tools/g3_viewer/prepare.py
.venv/bin/python tools/g3_viewer/make_inputs.py
node --test tools/g3_viewer/native_snapshot/tests/contract.test.js
node --test tools/g3_viewer/candidate/tests/contract.test.js tools/g3_viewer/challenge.test.cjs
node tools/g3_viewer/browser_check.cjs
```

`make_inputs.py` creates three independent early-year CSV cases, runs the actual
CLI against each, and checks literal expected dates/statuses. It also creates
invalid browser upload files. The generated 2,000,001-byte file is ignored by Git.

The browser check requires Playwright and installed Chrome. This machine's bundled
Node modules and Chrome paths are defaults; set `PLAYWRIGHT_MODULE` and
`CHROME_EXECUTABLE` to override them. `VIEWER_PORT` defaults to 18765. It starts a
loopback HTTP server, launches a separate headless browser context, uploads actual
files through the native file input, and compares actual downloaded bytes. It
does not mock the viewer, call its internal rendering functions, or inject report
objects into the page. The server and browser close when the check finishes.

`VIEWER_CONTRACT` selects a different module for `challenge.test.cjs`; using the
unmodified native contract deliberately exposes the early-year regression. The
preserved original failing run preceded addition of the three actual CLI cases.

Recorded commands, screenshots, results, and limitations are in
`docs/trialtrace/review/g3_viewer/`. These checks cover the separate viewer; the
main Streamlit app and its embedding behavior require their own browser checks.
