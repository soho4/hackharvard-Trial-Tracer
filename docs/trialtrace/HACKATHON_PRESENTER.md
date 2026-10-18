# TrialTrace: presenter briefing

## The one-sentence explanation

TrialTrace checks whether a recorded trial activity happened within its allowed time window and shows the evidence behind its answer.

## A 60-second pitch

“Clinical-trial reviewers need to check whether study activities happened when the protocol required. Missing or inconsistent records make that harder to explain.

“TrialTrace lets a reviewer upload a spreadsheet, identify the relevant columns, and inspect a timing result with its original evidence. Our demo uses a public Moderna protocol and entirely synthetic participant records. We support one candidate rule: a follow-up safety phone call seven through ten calendar days after vaccination. That interpretation still needs independent review.

“Watch this record: the last permitted date is March third, but the call is recorded on March fourth. TrialTrace shows that it is one day outside the window. If the vaccination date is missing, it explains the missing information instead of guessing.

“Existing systems already perform checks. Our proposed value is making exported-data review easy to inspect and reproduce. Today we demonstrate that mechanism; we have not yet measured time savings or clinical benefit.”

Problem evidence and citations are in [HACKATHON_CLAIMS.md](HACKATHON_CLAIMS.md).

## What the result actually tells someone

**Potential deviation:** the recorded activity is outside the candidate window. The calculation includes the target date, earliest and latest permitted dates, actual activity date, and number of days outside. This is a prompt to investigate, not a judgment of harm, severity, or regulatory reportability.

**Data query:** a required fact is missing, invalid or conflicting. The evidence contains reason codes and the relevant source records. Examples include a missing vaccination date, unconfirmed call completion and duplicate identifiers. No timing calculation is presented for these cases. The reviewer must check the underlying source and correct or clarify the record. We do not estimate the missing clinical fact.

**Not evaluable:** the record falls outside the supported check; for example, another study. It is not a pass.

**Pass:** this one recorded activity fits this one supported timing rule. It is not an assessment of the participant's health, the quality of the safety call, or the entire trial record.

## Demo you can rehearse

Use `examples/preparation/synthetic-wide.csv`. It contains seven fabricated records, with deliberate problems. Its mapping is documented in `examples/preparation/mapping.json`.

1. Explain that the file and participant identifiers are synthetic.
2. In the browser Timing review workspace, select **Load demo file**. This loads the real synthetic CSV and its explicit demonstration mapping into the Python checker. Review the eight column choices and `done` completion value, then confirm the synthetic draft scope. For your own synthetic file, use **Choose a CSV** and select its columns yourself.
3. Select **Review 7 records**. The expected counts are **1 pass, 1 potential deviation, 4 data queries and 1 not evaluable**.
4. Inspect record 2. Vaccination: **2028-02-22**. Window: **2028-02-29 through 2028-03-03**. Recorded call: **2028-03-04**. It is **1 day late**. The leap-year arithmetic is intentional.
5. Inspect record 3. Its vaccination date is missing. There is no justified window to calculate; the result asks for clarification.
6. Inspect record 4. Its status indicates data entry rather than a confirmed completed call. TrialTrace withholds a timing conclusion.
7. Select **Download evidence package**. Show that it includes the original file, column mapping, generated internal tables and result. The result is computed from the input, not a canned dashboard.
8. Open **Demonstrate a changed date** and select **Load changed-date demo**. Confirm the mapping and run again. Record 2 now has a call date of **2028-03-05**, and the flag becomes **2 days outside the window**. This behavior was exercised in the actual browser.

The demo loader processes supplied fixture bytes through the real checker. It does not prove compatibility with an arbitrary trial-system export. Rehearse against the final presentation build. Public hosting is a separate step and is not established by this briefing.

## Architecture in ordinary language

```text
Uploaded spreadsheet + user's explicit column choices
                         |
             Preserve the original file
                         |
         Check structure, identifiers and dates
                         |
        Apply the fixed, versioned candidate rule
                         |
    Results + missing-information explanations + evidence
```

The presentation interface uses HTML, CSS and JavaScript. Pyodide runs the existing Python checker inside a browser worker. The earlier local Streamlit interface and the command line use the same core. The timing calculation uses ordinary calendar arithmetic; it does not ask a language model to decide dates. This demonstration has no participant database.

Actual browser verification found that the original demonstration's evidence JSON was byte-identical to the local Python report. Changing the recorded call from March 4 to March 5 changed its result from one day to two days outside the window. Malformed and oversized inputs were rejected. The application suite passed 457 tests at this checkpoint. These are engineering checks on synthetic inputs, not independent clinical validation or measured workflow benefit.

Internally, the spreadsheet is converted into three tables. **Anchors** hold the starting event, such as vaccination. **Visits** hold the activity being checked, such as the safety phone call. **Assignments** record which draft rule is explicitly attached to the synthetic record. In the one-spreadsheet workflow, the user does not upload three separate files.

The downloadable package preserves the original values and the mapping into those tables. File fingerprints identify the exact inputs and rule used. Fingerprints show which bytes were used; they do not prove those bytes are true or medically correct.

## Questions judges may ask

**Who uses it?** Our intended user is a clinical-trial data manager or reviewer checking exported records. The buyer and demand are not validated.

**Is the source real?** Yes: a public trial protocol. The participant records are fabricated. There is no live patient feed or EDC connection.

**Why only one rule?** A narrow demonstration lets us show a complete, inspectable calculation and uncertainty behavior. Arbitrary protocols, eligibility and amendment applicability are not implemented.

**Why not just use Excel?** A spreadsheet can calculate a date window. We package original inputs, an explicit rule, uncertainty checks and reproducible evidence together. Whether that saves enough effort is still to be measured.

**Why do we need a human?** Someone must confirm the protocol interpretation and the meaning of the uploaded columns. A reviewer must also determine whether a flagged record reflects a data-entry problem, an actual late activity or context absent from the file.

**Does this assess safety?** It checks the timing of a recorded safety phone call. It does not assess symptoms, adverse events, participant health, or whether the call's medical assessment was adequate.

**Can it handle every file?** No. The current mapping route requires a CSV with one call record per row, both relevant date columns, identifiers and completion status. Missing individual values can be queried; absent required columns prevent preparation. Separate event exports, repeated vaccination keys and partial dates need additional handling.

**Is it operational?** It is a functioning hackathon prototype. Public hosting makes it accessible, but does not establish readiness for patient data. Access controls, data handling and retention decisions, operational support, independent rule review and validation in the intended workflow remain work for a real deployment.

**How much time does it save?** We have not measured that. Internet research supports that the underlying issues exist; it cannot substitute for a comparison of preparation plus review time using this product.

## A simple five-slide story

1. **Problem:** timing and record-quality concerns are real; cite the claim ledger.
2. **User:** a reviewer with an exported spreadsheet and a question to resolve.
3. **Live demo:** late activity, missing date, original evidence.
4. **How it works:** explicit mapping, deterministic check, reproducible package.
5. **What we proved and what is next:** working narrow mechanism; independent review and workflow benefit remain unproven.

Do not make the presentation a tour of every tab. Show one record a judge can understand, then one case where the app refuses to guess.
