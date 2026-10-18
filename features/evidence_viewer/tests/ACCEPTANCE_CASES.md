# Viewer acceptance cases

## 7. Acceptance cases

| Test | Expected observation |
|---|---|
| `mixed.json` | Four findings: one PASS, one potential deviation, one data query, one not evaluable. |
| Filter to DATA_QUERY | One listed finding; overall report still shows all four category counts. |
| Search `demo-p002` | The corresponding event and its supplied evidence appear. Search is case-insensitive. |
| `empty.json` | Zero counts, no selected finding, honest empty-state text. |
| `invalid_status.json` | Rejected; no old results or download remain available. |
| `invalid_duplicate_id.json` | Rejected rather than silently choosing one record. |
| `invalid_evidence_hash.json` | Rejected due to mismatched declared provenance. |
| Missing required field or unknown schema | Rejected with a useful error. |
| `markup.json` | HTML-like strings appear literally; no injected script runs; unsafe source link is disabled. |
| Source PDF hash is null | “Not available,” not a fabricated hash or verified-source badge. |
| New fifth PASS finding with unique ID | Total becomes five and PASS count becomes two. No static counts. |
| Broken JSON or a file above 2 MB | Rejected visibly before a success state. |
| Valid file, then invalid replacement | Old report disappears; old download cannot be used as the new report. |
| Original-report download | Downloaded content equals uploaded content; filtering does not silently remove records. |
| Narrow viewport and print view | Evidence remains readable; no horizontal overflow or clipped dates. |

The supplied examples are **hand-authored contract fixtures**, not clinical validation or independently confirmed detector outputs. They are useful for checking this reader because expected display behavior is explicit. Add your own cases; do not generate expected answers by calling the function you are testing.

