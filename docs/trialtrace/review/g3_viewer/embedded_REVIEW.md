# Embedded viewer browser verification — 18 October 2026

The final main app and embedded viewer work together in standard Chrome. A fresh
isolated browser session uploaded the three independently authored 24-record
CSV files, computed 9 PASS / 5 POTENTIAL_DEVIATION / 7 DATA_QUERY / 3 NOT_EVALUABLE,
downloaded the actual main-app report, reopened those downloaded bytes through
the iframe's native file input, and downloaded the original report again.
All operational records were synthetic. “Real” in execution records means actual
file processing and browser actions, not patient records.

Both immediately preserved downloads matched a newly executed installed CLI
byte-for-byte: **77,329 bytes**, SHA-256
`133c65689a864a9c7f9971cee38f096ac4e7117075aba2de1a19bdaafc002acd`.
The browser captured both the main HTTP media download and the iframe Blob
download. The iframe sandbox includes `allow-downloads` and `allow-modals`.

Eight checks passed in Chrome 155.0.8059.80 with no page exceptions or console
errors. The iframe showed all 24 findings and the selected early-year evidence.
At a 390-pixel main viewport, the iframe viewport and content width were both
358 pixels. Print media hid controls and applied one column. Invalid status,
duplicate-ID, and mismatched-evidence-hash replacements each removed the old
report, IDs/counts, and enabled download. Wide and narrow screenshots were
visually inspected.

The native/OS print dialog was not tested. Print CSS was exercised in the real
embedded frame; complete PDF pagination of the parent app is not established.

## IAB observation versus standard Chrome

The root agent separately reported that the Codex in-app browser did not expose
a captured download event after clicking the iframe's original-report download.
This isolated standard Chrome run reproduces the same served app path and
successfully captures and verifies the actual bytes. Therefore the observed IAB
event limitation was **not reproduced in standard Chrome**. This does not prove
why IAB failed to report an event, or claim that IAB's download behavior was fixed.
It does establish that the app's native iframe Blob download works in the tested
Chrome configuration. No alternate download endpoint or fabricated response was
injected to produce the passing result.

## Exact evidence

- Latest result: `embedded_result.json`
- Final run artifacts: `embedded_runs/2026-10-18T08-48-02.492Z-aa79f368/`
- Actual main download: `main-downloaded.json` in that run
- Actual iframe download: `iframe-downloaded.json` in that run
- Actual CLI result and command: `cli-generated.json`, `cli.command.json`
- Successful final command: `embedded_commands/20261018T084802.317580Z-actual-main-embedded-stable-mobile-00fc5d27/record.json`
- App SHA-256: `6ab33e3e3f7253b16e2226ab4037fba904e958b9f2ced15de18d34cb9f092a9e`
- Viewer asset hashes are recorded in `embedded_result.json`.

The first attempt is preserved under
`embedded_runs/2026-10-18T08-43-18.430Z-38a3f27e/`. Its Playwright `checkbox.check`
targeted the styled checkbox's covered native input and timed out. The test was
corrected to click the actual visible label and assert the checked state; no
forced click, DOM mutation, or application change was used. The uploaded files
were already visible in the failed screenshot. The subsequent run completed the
entire flow from a new browser context.

The intermediate passing run remains preserved under
`embedded_runs/2026-10-18T08-44-16.110Z-feef39a7/`. Its narrow screenshot retained
an open Streamlit sidebar drawer over the page. The final harness closes that
drawer through its actual UI control before narrowing and waits for its closing
animation to finish, then repeats all eight checks. The first close-control run
captured the animation mid-transition and remains preserved as well. The final
narrow screenshot was visually inspected with the viewer visible; iframe content
width remains equal to its viewport.

## Reproduce

Start the final app locally using its installed dependencies, for example from
the repository root:

```sh
.venv/bin/streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

If supplying the public source PDF bytes to that app, append
`-- --source-pdf /path/to/Prot_000.pdf` and set `SOURCE_PDF` to that same path when
running the browser check. The default is the original local source-check PDF.
No source approval is inferred from supplying the file.

Then run:

```sh
node tools/g3_viewer/embedded_check.cjs
```

The script uses the installed Chrome executable and bundled Playwright path on
this machine; `CHROME_EXECUTABLE` and `PLAYWRIGHT_MODULE` override them.
`TRIALTRACE_URL` defaults to `http://127.0.0.1:8501/`. The test starts its own
headless browser context, not a user browser profile, and leaves the served app
running. It uses actual browser file inputs and immediately saves downloads.
Each run creates a unique evidence directory, preserving failures. It does not
inject app functions, preloaded reports, network responses, or source records.

The fresh-environment installed AppTest probe was also rerun after the final
iframe API change and passed at this same app hash. Those records are separate
under `../g3_clean_install/`; AppTest does not substitute for this browser run.
