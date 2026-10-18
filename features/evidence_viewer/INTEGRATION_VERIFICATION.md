# G3 integration verification

The original README and VERIFICATION documents describe the teammate's earlier
standalone review; retain them as history. This continuation imports all 18 files
from commit `1b216519e93866bca3fc36be174ec0f5bf05f793` and applies two focused changes:

- `contract.js`: use `setUTCFullYear` instead of the Date.UTC 1900 remapping for years 0001–0099; reject year 0000.
- `style.css`: wrap actual long engine run/finding IDs and status filenames at narrow widths.

The schema and six fixtures remain byte-for-byte identical to the upstream files.
No redesign or source-review promotion occurred. Provenance, original source tree,
patches, deliberate failing regressions, 58 passing Node tests, and 21 standalone
served-browser cases are in `tools/g3_viewer/` and `docs/trialtrace/review/g3_viewer/`.
The current integrated feature itself also passed the 58 tests, not only a copy.

`app.py` inlines the trusted local HTML/CSS/JS into a Streamlit iframe. Uploaded
report values remain handled by the viewer's existing textContent rendering.
The main app separately exposes input_accounting, which this reader does not display.
Main app downloads and saved-report viewer downloads are distinct paths; see the
browser reports for platform-specific behavior and exact executed evidence.
