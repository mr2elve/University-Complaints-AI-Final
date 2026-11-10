# Validation record

Validated on 10 November 2026, using the supplied local checkpoint and Python 3.11 on Apple Silicon macOS.

- **32 pytest tests passed**, including real checkpoint loading, inference, routing boundaries, database persistence/audit, stale-edit protection, CSV upload/batch saving, and Streamlit navigation in English and Kazakh.
- The original exported tokenizer's IDs and attention masks match the application's tokenizer on Kazakh examples.
- Strict state-dictionary loading succeeds for all **83,462,415** model parameters. Output dimensions are **3 / 3 / 3 / 6** in the saved target order.
- Real inference smoke test passed on three Kazakh examples. Outputs are recorded in `data/research/smoke_test_output.json.txt`; these are illustrative inputs, not university records.
- The dependency consistency check reports no broken requirements.
- Actual Chrome navigation covered all seven sections, real analysis, and explicit saving in an isolated QA database. No browser JavaScript exceptions were observed. A fresh 390-pixel mobile viewport had no document-level horizontal overflow.
- Desktop and mobile screenshots are in `assets/screenshots/`. Screenshots show illustrative QA records only.
- The application's default `data/complaints.sqlite3` was not populated during testing. Unit/UI tests use temporary databases; browser QA uses a separate file under `/private/tmp`.

## Scope of verification

This verifies the local demonstration implementation, not institutional production readiness or clinical/safety reliability. The reported research F1 values were checked against saved notebook outputs; the research experiment was not retrained or rerun. Browser QA is a smoke check, not an exhaustive accessibility or cross-browser audit. Concurrent edit conflicts are tested; high-load multi-user deployment has not been benchmarked.

No authentication, encrypted storage, official university SLA, production retention policy, real department notifications, or model calibration is claimed. The 96-token model limit remains in effect.
