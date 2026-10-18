# TrialTrace: defensible hackathon claims

Research checked 18 October 2026. This is desk research, not customer interviews, independent source approval, clinical validation, or a study of TrialTrace's benefit.

## What the internet can establish

The underlying problem exists. It cannot establish that our particular tool saves time, prevents harm, or is better than a trial team's existing process.

| Evidence | Safe claim | Boundary |
| --- | --- | --- |
| Getz, Smith, Jain and Krauss, 2022, *Benchmarking Protocol Deviations and Their Variation by Major Disease Categories*, original research, Table 2. [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8979478/) · [DOI](https://doi.org/10.1007/s43441-022-00401-4) | In a convenience sample of 187 protocols, the authors reported averages of 75.3 deviations per phase II protocol and 118.5 per phase III protocol. The sample included 48 phase I, 72 phase II and 67 phase III protocols. | A pre-pandemic baseline with wide variation. These are all protocol deviations, not just timing errors, patient injuries, or deviations TrialTrace could prevent. Participating companies funded the research. Do not generalize the sample into a universal rate. |
| FDA, *FY 2024 Clinical Investigator FDA 483 Observation Trends*, slides 6 and 8. [Official report](https://www.fda.gov/files/science%20%26%20research/published/fy_2024_ci_fda_483_observations_trends_1.pdf) | FDA inspection-observation themes include visits, assessments and labs outside their allowed windows, plus missing or inaccurate records. | This demonstrates relevance of the issue, not its population prevalence or our ability to fix it. The report covers much more than TrialTrace. |
| FDA, December 2024 draft guidance, *Protocol Deviations for Clinical Investigations of Drugs, Biological Products, and Devices*. [Official page](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/protocol-deviations-clinical-investigations-drugs-biological-products-and-devices) | FDA has addressed consistent identification, classification and documentation of protocol deviations. | The accessed page labels this draft guidance, not for implementation, with nonbinding recommendations. Do not claim FDA endorses TrialTrace or that a timing flag automatically establishes clinical importance or a reporting obligation. |
| OpenClinica, *Calendar – Introduction*, current vendor documentation. [Official documentation](https://servicedesk.openclinica.com/support/solutions/articles/158000442542-calendar-introduction) | Existing trial software already supports scheduling, notifications and conditional rules. | “Nobody checks dates today” and “we invented automated protocol checking” are false positioning. Portable, inspectable review of exported records is our proposed benefit; superiority is untested. |

Suggested evidence sentence: “Published research documents protocol deviations, and FDA inspection themes include out-of-window activities and missing records. We built a transparent way to examine one narrow example.” Use the numerical study only when there is time to state its sample and limits.

## Claims about this build

| Say | Do not say |
| --- | --- |
| “A real public Moderna protocol supplies the source for one candidate timing rule.” | “We analyzed real patient records” or “this is Regeneron data.” |
| “Our participant records are synthetic; the uploaded values drive real calculations.” | “Live clinical-trial monitoring.” |
| “The rule's interpretation is pending independent human review.” | “Clinically validated,” “FDA approved,” or “approved protocol interpretation.” |
| “The result shows the permitted dates, recorded date, and days outside the window.” | “This participant was harmed” or “this is a major deviation.” |
| “Missing or conflicting information produces an explanation and no timing conclusion.” | “We estimate missing vaccination dates” or “an incomplete record is a pass.” |
| “The target user is a clinical-trial data manager or reviewer.” | “Customers have validated demand” or “we have demonstrated willingness to pay.” |
| “Our engineering evidence checks implementation behavior on synthetic cases.” | “Passing software tests proves clinical accuracy or workflow value.” |
| “We aim to reduce the work of checking and explaining exported records.” | Any percentage, hours saved, cost savings, fewer injuries, or trial acceleration attributed to TrialTrace. |
| “A hosted hackathon demo makes the prototype accessible.” | “Hosting makes it production-ready for patient data.” |

The current source is [ClinicalTrials.gov's public protocol for NCT04470427](https://cdn.clinicaltrials.gov/large-docs/27/NCT04470427/Prot_000.pdf), mRNA-1273-P301 amendment 10, Table 21. This ledger does not reapprove the source interpretation. The exact candidate and its pending-review status remain in `rules/candidate_rule.json`.

Current engineering checkpoint: the original synthetic demo's actual browser evidence JSON matched the local Python report byte for byte (SHA-256 `2758951f4329194dfbe047212573dc6f6448982701e798d2c9162a82e26681ae`). A changed call date produced two rather than one day outside the window. Browser malformed/oversized input rejection and 457 passing application tests support the implementation claim. They do not establish clinical correctness, general export compatibility, measured usefulness or public hosting. Evidence is under `docs/trialtrace/review/web/browser/`.

## Event fit

[HackHarvard's current website](https://www.hhuh.io/) lists the “Reinvent Clinical Trials” healthcare track presented by Regeneron and the “Hack to the Moon” theme. The inspected public page did not provide a general judging rubric or the detailed clinical-track problem statement. Do not invent either or imply sponsor endorsement. Track presence supports relevance of the subject, not acceptance of this product idea.

## What can be delivered in the final hour

An understandable, deployed demonstration; an honest problem statement supported by the sources above; inspectable results; documented engineering checks; and a practiced explanation. Independent clinical source approval, a representative workflow study, institutional procurement, and an operational patient-data service cannot honestly be replaced by an internet search.
