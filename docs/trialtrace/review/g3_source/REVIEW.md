# Public source acquisition and app scope review

The app can honestly combine a real public study source with explicitly synthetic operational examples. The official registry response was acquired successfully; it is not participant-level visit data and does not supply real deviation findings.

## Actual acquisition

The official single-study API returned HTTP 200 and `application/json` on 2026-10-18 at `08:24:23.752134+00:00`. Native curl completed with exit 0 and TLS verification result 0. The exact 556,931-byte response is retained locally in `work/g3_source/NCT04470427.registry.json`; it was not copied into the repository. SHA-256: `c351b22aaebc03899673e14b1af2e3cd6c4d3740af3935ef4920502fd255260c`.

The app-ready selected facts and provenance are in `registry_snapshot.json`. `registry_fetch_record.json` preserves safe acquisition metadata. The official API returned NCT04470427, protocol ID mRNA-1273-P301, ModernaTX, Inc. as lead sponsor, COMPLETED status, and actual trialwide enrollment of 30,415. Its last posted update is 2024-03-21. The public document listing identifies `Prot_000.pdf`, dated 2022-04-07, with 2,728,675 bytes, matching the candidate identity and the previously acquired protocol's size. The registry does not provide the PDF hash; the snapshot labels that hash as prior local PDF evidence. [Official study API](https://clinicaltrials.gov/api/v2/studies/NCT04470427), [study page](https://clinicaltrials.gov/study/NCT04470427).

NLM recommends the single-study API for usable JSON study data instead of scraping the study page. Its published description distinguishes registry metadata and statistics from a participant-event feed. [NLM API guidance](https://www.nlm.nih.gov/pubs/techbull/ja25/ja25_clinical_trials_screen-scraping.html).

## What the fetched data supports

- A real public study card: study/protocol IDs, title, sponsor, registry status, last update, retrieved timestamp and response hash.
- A link to the actual public protocol, with separate source acquisition and human interpretation-review states.
- Describing that public aggregate results exist. The returned participant-flow data consists of study-group counts, not individual participants' visit timelines.

The response does not provide the core's participant-level actual vaccination dates, safety phone-call dates or completion, or Table 21 assignment rows. Its registered individual-participant-data sharing flag is `NO`; that field is not a claim that private data cannot exist elsewhere. No patient records were acquired. The registry's enrollment count must never be displayed as the number of records this app analyzed or used to synthesize purported real people.

## Honest launch scope

Use labels such as **Real public study source**, **Synthetic demonstration records**, and **Draft timing check — source interpretation pending human review**. Show the registry fetch timestamp and record-update date, since this is a retrieved snapshot. Keep registry facts separate from synthetic analysis counts.

The analysis can accept three explicitly synthetic CSV files, apply the existing importer/relationship checks and deterministic engine, display each source row and diagnosis, and download the same validated evidence JSON. Use an explicit draft action and pass `DRAFT_ENGINEERING` to the shared API; do not let a public registry match or `DEMO_REVIEWED` CSV label promote the run. Never derive personal dates from aggregate results, substitute registry group IDs for participant IDs, or label synthetic findings as real study deviations.

Reviewed execution is deliberately unavailable in the current core. Human review still needs to settle the exact source interpretation, including zero early allowance, endpoint inclusion, and the previously observed note-number discrepancy. Source identity checks and public registry corroboration do not satisfy that review. Clinical validation remains false.

## Independent current-core review

The existing application suite actually ran in this continuation: **236 passed in 3.96 seconds**, subprocess exit 0, with the reviewed files unchanged during that run. No new material core defect was reproduced in the bounded review. Logs and per-file hashes are retained here. `core_review_state.json` records the reviewed snapshot and explicitly notes that the implementation owner changed `cli.py` afterward; the 236-test result does not validate those later edits or the new UI. Final UI/CLI parity and browser tests must bind to the final package digest.

The earlier teammate viewer year-0001-through-0099 defect remains a known separate integration issue unless the viewer owner repairs and verifies it. The core and immutable reference validator support those calendar years; do not change calendar semantics or silently narrow input validity to conceal a display-validator defect.

For the UI, surface structural input failures without keeping an old report presented as new. Changing any uploaded file must invalidate prior results and downloads. Keep raw imported text escaped, respect the existing per-table and export limits, and preserve DATA_QUERY/NOT_EVALUABLE with null calculations. These are integration requirements to verify in the actual served app, not completed browser-test claims from this review.

No production source, candidate file, teammate viewer file, or human review artifact was changed by this reviewer. This continuation writes only its assigned review documentation and local scratch acquisition/probe evidence.
