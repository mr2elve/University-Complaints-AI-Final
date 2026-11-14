# Multilingual XLM-RoBERTa validation — 14 November 2026

Implemented and tested locally on Apple Silicon macOS, Python 3.11.4, PyTorch 2.15.0 and Transformers 4.57.6. No commit, push or deployment was performed. The old Hugging Face repository and local KazRoBERTa artifacts were not modified.

## Results

- `python -m pytest -q`: **59 passed in 9.19 seconds**, no skips or failures.
- Real CPU inference passed on Kazakh, Russian, English and mixed Kazakh–Russian examples. All four tuition-payment examples predicted `administrative_services / medium / neutral / finance_office`; routing confidence was approximately 0.938 / 0.972 / 0.969 / 0.962 respectively. This is a smoke test, not a held-out accuracy evaluation.
- Strict state-dictionary loading matched all **207 tensors / 278,055,183 parameters**. Named `ModuleDict` heads match the new checkpoint, replacing the old numbered-head architecture.
- Tests verify exported label ordering, named-head decoding independently of task iteration order, all-language single/batch agreement, masked padding, truncation, tokenizer parity, CPU placement, Streamlit resource reuse, offline setup, resumable-failure behavior, Hub snapshot symlink installation, and rejection of incompatible exports.
- Streamlit AppTest covers all seven pages in both UI languages, analyzer saving, batch CSV/export/saving, manual review, database audit and stale-edit protection. Test databases are temporary; no operational complaint records were inserted.
- `python scripts/setup_model.py --offline`: passed using the complete new installation.
- `python -m pip check`: no broken requirements. Existing dependency pins support this model; the fast exported tokenizer works without a SentencePiece runtime.
- `git diff --check`: passed. No weights/tokenizers were added to tracked source files.

## Measured resources

These are single-run local observations, not Community Cloud measurements. Weights were already downloaded. Model loading uses memory mapping, so some file pages are first read during inference; local OS file-cache state influences timing. Process RSS includes dependencies and accessed checkpoint pages, not only model tensors.

| Measurement | Direct loader | With Streamlit UI imports and resource cache |
|---|---:|---:|
| Python/dependency imports | 3.097 s | 3.685 s |
| Local artifact/model load | 0.562 s | 0.605 s |
| Peak RSS through load | 609.12 MiB | 674.09 MiB |
| Four-language batch inference | 0.835 s | 0.859 s |
| Peak RSS through first inference | 879.44 MiB | 930.53 MiB |
| Full-length batch (4 × 128 tokens) | 0.208 s | 0.208 s |
| Peak RSS through full-length batch | **943.81 MiB** | **994.59 MiB** |
| Second cached load | — | **0.000300 s**, identical object |

`model.pt`: **1,112,274,807 bytes** (about 1.04 GiB). Learned FP32 parameters: **1,060.7 MiB**. The initial export download via `huggingface_hub.snapshot_download`, including tokenizer and evaluation artifacts from the required subfolder, took approximately **4 minutes 51 seconds**; this is network-dependent and excluded from model load times. The application's installer uses `hf_hub_download` with the same subfolder and pinned revision, with local caching/reuse verified by tests.

Raw measurements and real probability distributions: [direct loader](data/research/xlmr_runtime_validation.json), [Streamlit cache](data/research/xlmr_streamlit_runtime_validation.json). Reproduce with the benchmark commands in [README.md](README.md).

[Streamlit's published resource limits](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app#resource-limits) describe changeable allocations of approximately 690 MB–2.7 GB memory and up to two CPU cores. The observed local footprint is above the lowest documented memory allocation. The two-thread cap, shared cache, serialized inference, memory-mapped assignment and default batch size 4 reduce overhead, but do not guarantee deployment success. More vocabulary coverage, larger batches and multiple sessions can increase memory use. Actual account allocation, Linux RSS and Cloud logs must be checked after deployment; no Community Cloud account/runtime was available for this validation. No quantization or substituted checkpoint was used.

## Files changed

All paths below are relative to the repository root.

Modified:

- `README.md`
- `streamlit_app/README.md`
- `streamlit_app/VALIDATION.md`
- `streamlit_app/app.py`
- `streamlit_app/requirements.txt` (documents fast-tokenizer dependency behavior; pins retained)
- `streamlit_app/src/config.py`
- `streamlit_app/src/model_artifacts.py`
- `streamlit_app/src/model_loader.py`
- `streamlit_app/src/inference.py`
- `streamlit_app/src/ui.py`
- `streamlit_app/scripts/setup_model.py`
- `streamlit_app/scripts/smoke_test.py`
- `streamlit_app/tests/test_model_artifacts.py`
- `streamlit_app/tests/test_inference.py`
- `streamlit_app/views/analyzer.py`
- `streamlit_app/views/batch.py`
- `streamlit_app/views/about.py`
- `streamlit_app/views/research.py`
- `streamlit_app/model/README.md`
- `streamlit_app/data/research/PROVENANCE.md`

Added:

- `streamlit_app/tests/fixtures/xlmr_config.json`
- `streamlit_app/data/multilingual_examples.json`
- `streamlit_app/data/research/xlmr_metrics_by_language.csv`
- `streamlit_app/data/research/xlmr_mixed_synthetic_metrics.json`
- `streamlit_app/data/research/xlmr_model_checksums.json`
- `streamlit_app/data/research/xlmr_runtime_validation.json`
- `streamlit_app/data/research/xlmr_streamlit_runtime_validation.json`

Downloaded, Git-ignored: the new export under `streamlit_app/model/xlmr/XLMR_Multilingual_University_Complaints/`, plus Hugging Face caches and the base architecture configuration. The database schema, routing implementation, review logic, CSS, seven-page navigation and old research artifacts remain intact. Model-related UI wording and research provenance changed; no new Chrome screenshot audit was performed for this upgrade.

---

# Historical KazRoBERTa validation record

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

No authentication, encrypted storage, official university SLA, production retention policy, real department notifications, or model calibration is claimed. The old checkpoint used a 96-token limit; the multilingual upgrade above uses 128.
