# Three-minute honest demo

**Demonstration goal:** show that supplied records drive a repeatable timing check and that every result can be inspected back to its original data. Current stage: local synthetic prototype with one candidate rule, before independent pilot validation.

## 0:00–0:30 — Problem and boundary

“Reviewers may need to explain timing flags from exported trial records. TrialTrace makes one timing check and its derivation inspectable. Existing trial systems already perform checks; we are testing whether portable evidence improves a specific review workflow. This uses a real public Moderna protocol and fabricated participant records. The rule interpretation still awaits independent human review.”

Do not say “automates safety assessment,” “finds every protocol deviation,” “proves eligibility,” “works with any trial,” “validated on patients,” or quote a saving. None is established.

## 0:30–1:15 — Data actually enters the tool

Launch from the repository root using the README commands. Open **Map one spreadsheet**. Use [the mapping walkthrough](../../examples/preparation/README.md). Show that every field is deliberately selected and that `done` means completed call. Show the preview before calculation. The app constructs its three internal tables; it does not require the presenter to pretend those are universal trial exports.

## 1:15–2:00 — Show correct and unresolved outcomes

Run the check: seven rows produce one timing pass, one potential deviation, four data queries and one unsupported-study result. Select record 2: original vaccination February 22, 2028; candidate inclusive window February 29–March 3; call March 4; one day outside. Select the missing date or unknown completion row: no confident timing calculation. This checks recorded call timing, not whether the clinical assessment itself was adequate.

## 2:00–2:40 — Show it is computation, not a canned pitch

Clear the source and upload a copy with record 2's call date changed to March 5, then remap and run: two days outside. Alternatively, change a selected column and show that old results disappear until preparation is redone. Download the complete package and inspect original CSV, chosen columns, declared scope, generated tables and evidence JSON. Hashes establish byte identity, not medical truth.

## 2:40–3:00 — What happens next

“Our next evidence is a synthetic export from a real configured workflow, a reviewer-verified dictionary and independently worked examples. We will measure total preparation plus review time against their current process. If it does not improve that process, we will change the product.”

There is no customer interview, human source approval, real participant pilot, production deployment or quantified saving to report yet. See [the validation plan](PILOT_VALIDATION_PLAN.md).

## Demo recovery

Keep the prepared synthetic source and mapping walkthrough locally. Clear an input before replacing it. A failed upload is not a valid result. If the in-app browser displays AxiosError, remove the failed file and retry; if it persists, reopen the local app in a supported normal browser and disclose the failure. Do not replace a failed live run with a prerecorded output while claiming it was computed live. Saved evidence may be shown explicitly as a saved earlier run.
