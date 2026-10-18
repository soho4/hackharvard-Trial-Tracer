# Independent G3 upload application review

No material issue remains open in the reviewed upload/parser/source-hash path at the recorded snapshot. A real regression in the intermediate upload-lock implementation was found and repaired. The public registry snapshot supports study-source context, not real participant event analysis. Human source interpretation review remains blocked.

## Scope and evidence boundary

Read-only production review covered `app.py`, `src/trialtrace/source.py`, `workflow.py`, the `parse_table` importer extraction and the CLI shared source-hash refactor. The final app snapshot was `dadd4092cc9b16709ee2a9594fc36f855223767aed5f2a7d9ea1886c24a431cd`. Exact per-file hashes appear in the successful probe outputs. This reviewer changed no production source or tests.

The two successful probes execute the actual application through Streamlit AppTest plus a direct parser call. They are **component/API checks, not served-browser end-to-end tests**. The implementation owner separately owns real-browser upload/download and final suite evidence. Earlier 236-test logs in this directory do not validate this UI or later changes.

## Finding and repair

**Resolved: immediately disabling the arriving file uploader discarded its newly submitted value.** In the intermediate design, `disabled=st.session_state.get(upload_key) is not None` became true during the same rerun receiving the upload. The installed Streamlit 1.66.0 registration path discards incoming widget state when the widget is disabled (`runtime/state/session_state.py`, disabled-value enforcement). The actual script probe observed all three controls disabled with no retained file, no Clear buttons, and Run disabled. A following rerun returned empty enabled controls. The captured `configuration_fixed.stderr` contains the resulting disabled-Run failure; `configuration_fixed.record.json` records exit 1 at 08:32:54 UTC. The failed run did not print its code fingerprints, so it must not be treated as a hash-bound final snapshot.

The owner repaired this by capturing exact filename/bytes in separate `selected_upload_*` session state, showing selected-file text and a Clear action, and showing a fresh uploader only after Clear. The successful lifecycle probe at 08:34:50 UTC verified initial upload persistence, successful calculation/JSON serialization, and Clear removing report data, metrics and download before the replacement chooser appears. It also verified persistent rejection of invalid UTF-8 and a 1,000,001-byte replacement without a previous report resurfacing. All reviewed files were unchanged during that probe.

The implementation owner separately reported and repaired the original **browser-side oversized replacement** problem: the widget can reject an oversized file in the browser without notifying Python, leaving an old report active. The final clear-before-choose design addresses that ordering. This review verifies the server/component ordering, but does not claim to have independently observed the browser's size rejection. Use the owner's actual browser records for that requirement.

**Resolved during review: validate rule configuration before source-card rendering; derive the window from the validated values.** Initial code parsed JSON and rendered fixed +7/+10 text before semantic validation ran. The owner added `validate_rule` to initial configuration loading and derived offsets, table, amendment and document date from that validated rule. The successful configuration probe at 08:34:04 UTC verifies a missing-fields object produces a controlled error with no report and no exception. An in-memory, deliberately synthetic +0/+0 rule variation displays +0/+0 and produces the matching 9-days-outside calculation. The actual candidate file was never edited; this is a display/configuration check, not new source interpretation or approval.

An earlier reviewer probe used a widget key removed during the concurrent UI repair and failed with `KeyError`; that harness failure remains in local scratch. It is not counted as an application defect or a passing check.

## Review conclusions

- Uploaded bytes pass through the same bounded parser as filesystem inputs. The adapter requires all three logical roles and explicit synthetic draft confirmation, then uses the same evaluator and serializer. There is no sample-data fallback or runtime read of acceptance fixtures in these entry points.
- File display names are metadata, not filesystem targets. Evidence uses canonical role names. The parser removes nonprintable characters and truncates names to 200 characters. The independent path/markup-name probe retained the role and sanitized controls; the app uses escaped text/JSON and the viewer uses text nodes. Path-like text is not opened or written as a path.
- Changing or clearing uploads invalidates the previous report. Fingerprints include role, supplied display name, complete raw-byte hash, rule hash, source-PDF hash and draft confirmation. Malformed uploads cannot produce partial success; output size limits preserve full evidence or reject it.
- The source helper hashes every byte in bounded chunks and checks the PDF signature, while reporting `LOCAL_PDF_BYTES_HASHED_IDENTITY_NOT_CHECKED_BY_RUNTIME`. It does not claim source identity review. The CLI refactor retains prior collision/stale-output protection and merely delegates the same hashing operation.
- Registry metadata remains separate from synthetic report counts. The app labels the protocol/registry as public source material, operational inputs as synthetic, and findings as draft. The registry response provides aggregate results and study metadata, not participant vaccination, safety-call or assignment rows. No patient records were acquired or manufactured from those aggregates.

## Remaining limitations

Human source interpretation and integrator acceptance remain pending; runtime byte hashes and registry corroboration do not unlock reviewed execution or clinical validity. The app does not establish eligibility, applicable amendments, missing activities, or adequacy of a safety assessment. Browser transport behavior and actual downloaded-file parity require the separate final browser evidence. Later code changes invalidate only affected evidence and need their own verification; these records identify the code that actually ran.

## Preserved checks

`configuration_repaired.record.json` and `upload_lifecycle.record.json` record actual commands, UTC times, stdout/stderr hashes and exit 0. Their stdout contains assertions' observations and before/after code hashes. `configuration_fixed.record.json` and stderr preserve the real intermediate failure. The `.py` probes are synthetic, read-only review helpers, and are not imported by runtime application code. No PDF, full registry response, virtual environment, patient data or approval object is included here.
