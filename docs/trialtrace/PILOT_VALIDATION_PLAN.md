# Validation plan — not completed research

Current stage: functioning local synthetic prototype. This plan converts product uncertainty into observable decisions. It does not authorize real patient data, a deployment or a clinical decision. Use a fabricated dataset exported from a configured test project first. No reviewer has been recruited or contacted by this agent.

## 1. Establish a useful problem with a reviewer

Invite a trial data manager, monitor or coordinator who actually handles the relevant review. In a 30-minute session, ask them to walk through a recent type of timing query using synthetic examples:

- What triggers the review, who owns it, and what action follows a flag?
- Which existing system/report/edit check already handles it? What is still manual?
- Where do actual intervention and contact dates live? How are completion, repeated events and protocol versions represented?
- What evidence is needed to confirm or dismiss a flag? Which missing data must stay unresolved?
- How often does this occur? Can they show the steps and record elapsed time, rather than estimate a saving?
- Would a separate tool duplicate their work or make the handoff easier? What would make them refuse to use it?

Record observations, disagreements and counterexamples. Do not reinterpret interest or polite feedback as adoption. Use their existing tool as the baseline if one exists.

## 2. Validate input fit without patient records

Request a **synthetic export from a real configured test workflow**, an export configuration description and the corresponding data dictionary. Record system/version, format, which forms/events/permissions were included, repeat keys, date conventions, completion semantics and export time. Do not request clinical production credentials or actual participant files under this scope.

Build a field matrix before an adapter:

| Meaning required | Export column/path | Definition from dictionary | Transformation/join, if any | Reviewer confirmation |
|---|---|---|---|---|
| Study, participant and site identity | Pending | Pending | Pending | Pending |
| Actual vaccination identity and date | Pending | Pending | Pending | Pending |
| Actual safety-call identity, date and completion | Pending | Pending | Pending | Pending |
| Applicable protocol version/cohort/event | Pending | Pending | Pending | Pending |
| Repeat occurrence and extract coverage | Pending | Pending | Pending | Pending |

Do not fabricate missing fields to fit TrialTrace. Keep source files and transformation records. If dates reside on different event rows, specify and review identity/cardinality rules first. A form marked complete is not automatically evidence that the safety call occurred. Do not apply Moderna's rule to unrelated study data. A different study needs its own reviewed rule and cases.

## 3. Review the source independently

A qualified independent human must inspect the exact public protocol, Table 21 and footnotes, establish applicable cohort/amendment, confirm the actual vaccination anchor and inclusive +7..+10 candidate interpretation, and independently work examples. Use the existing source-review packet; leave identities, signatures and approval fields empty until a person actually completes them. Hashes bind evidence bytes; they do not authenticate clinical truth. G0 remains blocked meanwhile.

## 4. Evaluate engineering and reviewer performance separately

Freeze an answer set before running the tool. Prefer a reviewer who did not author the implementation. Include ordinary records and boundary days, a late call, unknown completion, absent/partial dates, wrong-person/site links, repeat occurrences, conflicting versions, excluded extract data and duplicate IDs. Include cases from the export's actual structure, not just our convenient examples. Record disagreements and adjudication separately from the expected labels.

Compare equivalent case batches in counterbalanced order: reviewer A manual/existing-tool first, reviewer B TrialTrace first if two reviewers are available. With one reviewer, use distinct matched batches and disclose practice effects. Record:

- Export, cleaning/mapping, rule setup, review, correction and handoff minutes separately; compare **total** minutes.
- Correct and incorrect timing flags, missed supported timing issues, unresolved cases, and inappropriate confident conclusions.
- Whether each result can be traced back to original values and the applicable rule without developer help.
- Corrections required, failures, excluded cases and reviewer explanations.

Report numerator/denominator and raw observations. Do not turn a small exercise into a general accuracy or savings claim. For time reduction, compare matched total baseline versus tool-assisted time, disclose sample size and variability, and include preparation. There is currently no measured saving.

## 5. Proposed decision gates

These are proposed criteria to agree with the reviewer before measurement, not achieved results:

1. **Input fit:** required meanings and identity relationships can be established from the test export and dictionary without guessing; all unsupported records remain visible.
2. **Source fit:** independent review resolves candidate interpretation and applicability. Technical test success cannot substitute.
3. **Engineering fit:** every frozen supported case matches the adjudicated answer; uncertainty does not produce confident timing conclusions; originals and transformations are reproducible.
4. **Usefulness:** reviewer can complete the intended review and recover evidence unaided; measured total burden improves or the reviewer identifies a specific evidence-quality benefit worth the cost. Otherwise redesign or stop.
5. **Pilot readiness:** a separate agreement defines data permissions, security, deployment, audit/change controls and responsibility. None of that production scope is currently implemented or approved.

## Review record template

Date / reviewer role / workflow / export origin / source and rule versions: **pending**.
Observed current steps and burden: **pending**.
Known-answer cases and adjudicator: **pending**.
Results, disagreements and preparation-inclusive timing: **pending**.
Decision and reasons, including negative evidence: **pending**.
