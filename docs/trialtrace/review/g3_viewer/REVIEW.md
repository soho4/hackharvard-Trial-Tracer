# G3 teammate viewer review — 18 October 2026

The actual teammate viewer is usable with real engine exports after two focused
repairs. This review ran the original Node suite, added independent challenge
cases, generated three new CSV datasets through the actual CLI, and launched the
served candidate in Chrome. It is technical review by an AI agent, not human
source acceptance or clinical validation.

## Findings and proposed repairs

**Calendar parsing rejected valid core output in years 0001–0099.** The viewer
used `Date.UTC(year, month, day)`, which changes those years to 1900–1999. The
original 27 tests passed, but the new challenge produced three assertion failures
for years 0001, 0004, and 0099. The proposed helper uses `setUTCFullYear` and rejects
year zero explicitly. Tests still reject impossible dates, including non-leap
centuries. Three new actual CLI exports for early years now validate and display.

**Long engine IDs overflowed narrow screens.** The original fixture-based browser
notes did not expose this: fixture run IDs and finding IDs are short. With an
actual core report, a 390-pixel viewport expanded to 643 pixels because its
64-character run ID and finding ID did not wrap. A single targeted CSS rule wraps
these IDs and filenames. The same browser case now reports viewport/scroll width
390/390, including a long uploaded filename. The failing screenshot and layout
measurement remain in `viewer-engine-narrow-before-fix.png` and
`narrow_layout_before_fix.json`.

The separate viewer does not recompute timing or authenticate declared hashes;
its labels accurately state this. Input accounting is an additional core field
the original viewer does not display. The main app must expose that accounting
separately so unreferenced input problems remain visible.

## Executed checks

| Check | Result | Evidence |
|---|---|---|
| Original native suite | 27 passed | `commands/20261018T082601.615992Z-native-suite-d90a6dbc/record.json` |
| Original contract against initial challenge | 3 assertion failures, preserved | `commands/20261018T082601.616077Z-native-challenge-c8c1712a/record.json` |
| Candidate suite plus final challenge | 58 passed; zero skips | `commands/20261018T083119.394318Z-candidate-full-final-5fba29de/record.json` |
| New CSV cases through actual CLI | 3 passed literal date/status checks | `inputs/engine_results.json` plus individual command records |
| Initial actual browser run | Failed actual narrow-width assertion | `commands/20261018T082808.919868Z-actual-browser-candidate-5ebd7a3d/record.json` |
| Diagnostic browser repeat | Same narrow-width assertion failure | `commands/20261018T082929.314403Z-narrow-layout-diagnostic-178ed546/record.json` |
| Actual served browser after both fixes | 21 cases passed | `commands/20261018T083052.265370Z-actual-browser-both-fixes-9a46299e/record.json`, `browser_results.json` |

The browser was installed Chrome 155.0.8059.80, launched headless in an isolated
context. It navigated over HTTP to the actual local server and chose filesystem
files using the page's native file input. The observed cases covered:

- Actual CLI PASS, changed-date potential deviation, missing anchor, wrong person,
  unsupported event, and empty visits; selected raw evidence and full hashes.
- Three newly generated early-year CLI reports with independently written dates.
- Status filtering/search without changing overall counts, and exact original
  bytes downloaded from both an actual CLI export and the supplied mixed fixture.
- Valid report followed by each invalid status, duplicate finding ID, mismatched
  evidence hash, unknown schema, broken JSON, and oversized file. Every rejection
  cleared old IDs/counts/report and disabled the download.
- Literal markup, no created injected image or executed script, and disabled
  unsafe source link.
- Actual 390-pixel viewport, long names, and Chrome print media/PDF generation.

There were zero page exceptions. One console resource error was a request for
the absent `favicon.ico` (HTTP 404); the actual server log records it. It was not
an application exception. Wide and narrow screenshots were also visually
inspected after repair.

## Provenance and integration

The upstream tree is pinned to commit
`1b216519e93866bca3fc36be174ec0f5bf05f793`. The 18 file hashes, exact native snapshot,
candidate copy, and proposed patches live under `tools/g3_viewer/`. The pinned
schema and six fixtures were not changed. No teammate-path file was edited by
this review agent.

Smallest integration: import the exact existing feature, then apply the two
focused patches. Preserve its UI and read-only boundary. When inlining the
assets inside a Streamlit component, keep report values on the existing
`textContent` path. Verify the iframe's real file picker, Blob/original-file
download, source-link popup policy, and printing behavior in the main app.

## Limits

This is a real browser test of the separate served viewer, not the main Streamlit
upload workflow or its embedded iframe. The main app's raw CSV upload,
recalculation, export equivalence, and embedding need separate evidence. No OS
print dialog was opened; Chrome's print CSS and PDF renderer were exercised.
The source review remains pending, and all operational records here are
explicitly synthetic engineering inputs. Historical native README/VERIFICATION
files are kept unchanged; this document records the current additional checks.
