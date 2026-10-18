# Main app: actual served browser review

The primary agent launched `app.py` with Streamlit on `http://127.0.0.1:8501`,
confirmed the health endpoint returned `ok`, and navigated the Codex in-app browser
to the served page. Files were selected through the real browser file chooser.
No app HTML, network response, session state, or computed answer was injected.
These observations are distinct from Streamlit AppTest component checks.

The local run used the previously retrieved public protocol PDF via `--source-pdf`.
Its bytes were hashed, not approved by a human. The real registry snapshot appears
in the source sidebar; every uploaded operational record is explicitly synthetic.

## Executed behavior

| Case | Observed result |
|---|---|
| New leap-year files in `examples/browser/boundary` | Vaccination 2040-02-22; target/earliest 2040-02-29; latest/actual 2040-03-03; PASS, 0 days outside |
| Change only visit date to 2040-03-04 | Prior report cleared; recomputation POTENTIAL_DEVIATION, 1 day outside |
| Header-only anchors | DATA_QUERY / MISSING_ANCHOR_ID; no timing conclusion |
| Malformed visits | Visible INVALID_HEADER rejection; no current result/download |
| Clear a selected input | Its bytes and current report removed before the next chooser; Run disabled |
| 1.1 MB replacement after repair | Browser shows size rejection; missing role remains empty, Run disabled, no result/download |
| Independent 24-visit dataset | 9 PASS, 5 POTENTIAL_DEVIATION, 7 DATA_QUERY, 3 NOT_EVALUABLE |
| Filter DATA_QUERY, search uppercase WRONG-PERSON | One of 24 displayed, full counts retained; selected label and raw evidence identify the wrong-person query |
| Original markup-like mapping note | Appears as literal JSON text, not executable markup |
| Actual JSON download while filtered | Full 24-findings report, byte-identical to real installed CLI; 77,329 bytes |
| Final unfiltered download | Identical to filtered download and CLI |
| Main app at 390 px and 1280 px | No page-width overflow; calendar dates readable; screenshots retained |
| Integrated saved-report viewer | Loads the actual downloaded report including year 0001; shows full 24/9/5/7/3 counts and pending-source labels |

`export_comparison.json` records the final app and core fingerprints and exact
download hash. `final-dom.txt`, failure/fix DOM records, and screenshots contain
observed page state. `session-events.json` preserves the initial event record.
Later observations were recorded from tool results and saved artifacts; exact
individual timestamps were not retained across a browser-tool session reset.

## Real failures found and repaired

1. **Oversized replacement left stale success visible.** Streamlit rejects files
   above its widget limit in the client without invoking Python `on_change`.
   Merely invalidating in that callback was insufficient. The revised UI stores
   accepted bytes in a read-only selected slot and requires Clear before opening
   another chooser. Clear removes the result and selected bytes immediately.
   The first attempted repair using `disabled=True` discarded initial uploads;
   independent component review found that regression and the selected-slot
   implementation replaced it. Red and green evidence are preserved.
2. **Filter label could disagree with selected evidence.** Deleting a selectbox
   session-state key while reusing its widget identity left an old label in the
   browser. The selection key now depends on the filtered finding IDs. Actual
   browser retesting verified the wrong-person DATA_QUERY label and evidence match.
3. The separate viewer's early-year validation and long-ID layout issues were
   repaired with focused patches; see `../g3_viewer/REVIEW.md`.

## Browser tooling and platform limits

The in-app browser's checkbox input targeting required clicking its visible label.
Its iframe locator clicks did not reliably scroll/target the embedded file label;
a screenshot-grounded native click opened the real chooser successfully.
The embedded viewer's Blob download produced no captured download event in this
browser, despite an enabled button and no logged console error. This is not counted
as a successful in-app viewer download. The main app's HTTP report download worked.
Separate actual Chrome testing of the integrated viewer passed all eight checks,
including both actual downloads and byte comparison with a fresh CLI run; see
`../g3_viewer/embedded_result.json`. This did not establish the cause of the in-app
browser difference. No native printer output is claimed.

No browser observation, passing test, or file hash establishes human source review,
clinical accuracy, real-patient suitability, or another-machine validation.
