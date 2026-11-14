# AI University Complaint Management System

The Streamlit application runs the fine-tuned **multilingual XLM-RoBERTa** checkpoint on CPU for Kazakh, Russian, English and mixed Kazakh–Russian complaints. It predicts category, urgency, tone and department, preserves human review, and stores explicitly saved complaints in SQLite. The complete interface supports English, Қазақша and Русский. Interface language never restricts complaint input language.

This is an academic demonstration, not an official university service. Complaint text is processed on the application server; Hugging Face is contacted only to obtain missing model files.

## Installation and startup

Use Python 3.11. From this repository:

```bash
cd streamlit_app
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/setup_model.py
python -m pytest -q
python scripts/smoke_test.py --offline
streamlit run app.py
```

`setup_model.py` is optional: the first analysis automatically downloads missing files. Linux/Windows select the pinned CPU-only PyTorch wheel; macOS uses its native CPU-capable wheel (macOS 14+). No CUDA or MPS is used. Existing dependency pins support XLM-R's exported fast tokenizer graph; SentencePiece conversion and an additional SentencePiece runtime are unnecessary.

For Streamlit Community Cloud, select `streamlit_app/app.py` and Python 3.11. Its adjacent `requirements.txt` supplies application dependencies. Tests require `requirements-dev.txt`. See the resource caveats below before deployment.

## Model source and local reuse

- Repository: [mr2elve/xlmr-university-complaints-multilingual](https://huggingface.co/mr2elve/xlmr-university-complaints-multilingual).
- Required remote subfolder: `XLMR_Multilingual_University_Complaints/`.
- Default pinned revision: `f15eb91b1b494b4ed92978a89b1f628e338b0ce3`.
- Default local directory: `streamlit_app/model/xlmr/XLMR_Multilingual_University_Complaints/`.
- Required export files: `config.json`, `model.pt`, `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`, `sentencepiece.bpe.model`.
- `encoder_config.json` is fetched separately from **FacebookAI/xlm-roberta-base**. Only its small architecture configuration is downloaded, never the base model weights.

The loader uses `huggingface_hub.hf_hub_download` with the explicit subfolder, revision and a local Hub cache. Completed cached files are installed atomically, using hard links when possible to avoid another checkpoint-sized disk copy. Interrupted downloads retain the Hub's resumable cache. Existing local files are reused; a complete installation makes no network requests. The downloaded task `config.json` is never overwritten by the encoder configuration or application routing settings.

The old artifacts under `model/` and the old KazRoBERTa Hugging Face repository are untouched. The new default directory prevents accidentally reusing them. All weights and tokenizer artifacts remain Git-ignored.

For offline installation, either copy the complete seven-file local directory or use:

```bash
python scripts/setup_model.py /path/to/multilingual_export.zip \
  --encoder-config /path/to/encoder_config.json --offline
```

The archive supports the export's actual subfolder, a `model/` prefix, or root-level filenames. Only expected files are read; arbitrary archive paths are not extracted.

`COMPLAINT_MODEL_DIR`, `COMPLAINT_MODEL_REPO` and `COMPLAINT_MODEL_REVISION` override defaults. CLI equivalents are `--model-dir`, `--hub-repo` and `--revision`. The remote subfolder remains explicit and fixed. **Use a fresh model directory when changing repository or revision**; local-first loading intentionally does not replace existing files. Restart Streamlit after replacing an installation. `load_model(allow_download=False)` disables downloads.

## Verified architecture

The new export is not an ordinary Hugging Face sequence classifier. `MultiTaskXLMR` reconstructs:

1. An `AutoModel` encoder with the architecture of `FacebookAI/xlm-roberta-base`: 12 layers, hidden size 768, 12 attention heads, vocabulary 250,002, maximum position embeddings 514.
2. Attention-mask-weighted mean pooling: `(hidden * mask).sum(1) / mask.sum(1).clamp(min=1)`.
3. Shared dropout, read from the export (`0.2`).
4. Four **named `nn.ModuleDict` linear heads**, with keys `category`, `urgency`, `tone`, `department`; dimensions come from the exported ordered labels.

Evidence: the pinned export's model card declares masked mean pooling and four linear heads; its config declares the architecture, base model, pooling, dropout, tasks and ordered labels. Its checkpoint contains `heads.category.*`, `heads.urgency.*`, `heads.tone.*`, `heads.department.*`, plus encoder and pooler weights. The original notebook cell 13 corroborates the masked-mean computation but uses numbered heads; it must not be copied unchanged. Strict loading matches all **207 tensors / 278,055,183 parameters** with no key rewriting or missing parameters.

Initialization uses the base configuration on PyTorch's `meta` device, then `torch.load(weights_only=True, mmap=True, map_location='cpu')` and strict `load_state_dict(assign=True)`. This avoids allocating a second full parameter set. The encoder's two deterministic nonpersistent position/token-type buffers are recreated on CPU. Every learned parameter comes from `model.pt`; inference uses `eval()` and `torch.inference_mode()`.

The fast tokenizer loads the actual exported graph and special-token settings locally. The unrelated Transformers Mistral-regex heuristic is explicitly disabled; the exported tokenizer graph is preserved. Input normalization retains case and characters across all languages, applying NFC, removing selected zero-width characters and collapsing whitespace. Dynamic padding and truncation use the new export's **128-token** limit. Original full text remains available when saved.

`label_names`, `label2id` and `id2label` must agree. No old label indices or classifier sizes are used to construct heads or decode predictions. Named head outputs avoid reliance on dictionary iteration order. The urgency and department label sets are checked for compatibility with the existing routing and review workflows, while their index order comes from the export.

## Routing, database and seven pages

All seven pages remain: Dashboard, AI Complaint Analyzer, Complaint Management, Manual Review Queue, Batch Analysis, Model Analytics, and About the Project. The CSS, page layout, trilingual navigation, database schema, human review and routing implementation remain intact. Model-related text and evaluation provenance have been updated.

The new export contains no routing settings. The application retains the established policy:

```python
confidence = min(max(p_category), max(p_urgency), max(p_department))
requires_review = confidence < 0.75 or p_high >= 0.30
```

Tone is excluded from routing confidence. P(high) ≥ 0.30 raises operational priority independently of predicted urgency. Suggested SLAs remain high 4 / medium 24 / low 72 hours, based on predicted urgency; these are demonstration values, not university policy. Thresholds have not been recalibrated for the new checkpoint.

SQLite keeps explicit saving, idempotent save tokens, atomic batch saves, original prediction snapshots, editable human decisions, audit history, review approval requirements and stale-edit protection. Existing records remain unchanged. `COMPLAINT_DB_PATH` selects a separate database; tests use temporary databases and do not populate operational records.

CSV upload limits remain 5 MB / 1,000 rows; input validation retains the 10,000-character limit. Batch inference defaults to **4**, with UI choices 1 / 2 / 4 / 8 / 16. Invalid rows retain their positions, CSV exports protect against spreadsheet formulas, and persistence remains opt-in.

The Model Analytics page presents published multilingual evaluation separately from the original Kazakh-only research comparison. They use different experiments/splits and should not be treated as a controlled comparison. New training grouped the original 1,000 complaint IDs into 700 / 150 / 150 before translation expansion. Mixed-language evaluation is synthetic. See [provenance](data/research/PROVENANCE.md).

## CPU caching and Community Cloud resources

`st.cache_resource` shares one model per process and model path; a lock serializes inference. PyTorch uses at most two CPU threads. Model parameters alone total **1,060.7 MiB**, and `model.pt` is **1,112,274,807 bytes**. Memory mapping faults in only accessed pages, so measured resident memory can initially be lower than total parameter size; diverse vocabulary and larger batches can increase it.

[Streamlit documents approximate, changeable limits](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app#resource-limits), including 690 MB–2.7 GB memory and up to two CPU cores. This full-precision model cannot be assumed to fit the smallest allocation. Verify the actual allocation in [workspace Settings → Limits](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-account/workspace-settings#limits), and check Cloud logs after deployment. This upgrade has been measured locally, **not deployed or measured in a Community Cloud account**.

Memory-mapped assignment, the shared resource cache, serialized inference and a smaller default batch reduce overhead. There is no quantization or silent fallback to a different model. See [validation results](VALIDATION.md) for measured load time, RSS, and inference timing, including Streamlit imports and cache reuse.

Reproduce resource measurements (macOS/Linux):

```bash
python scripts/smoke_test.py --offline --output /tmp/xlmr-runtime.json
python scripts/smoke_test.py --offline --streamlit-cache --output /tmp/xlmr-streamlit-runtime.json
```

The benchmark separates Python imports, local model loading, four-language inference and a batch of four inputs at the full token limit. Downloads are excluded from offline timings. `rss_mib` is null if process inspection is blocked; peak RSS remains available.

## Tests and troubleshooting

`python -m pytest -q` covers real multilingual inference and batch consistency, strict CPU loading, tokenizer parity, label-order validation, cached/offline artifact reuse, partial-download recovery, original routing boundaries, SQLite audit/review behavior and all seven pages in all three UI languages. Missing weights explicitly skip dependent tests; that does not validate inference. The checked-in example complaints are illustrative, not real university records.

- Download failure: retry setup; completed local files are retained.
- Old configuration or checkpoint mismatch: use a fresh directory for the pinned multilingual export. The loader fails instead of producing substitute predictions.
- Memory pressure: use batch size 1 or 2 and inspect the hosting allocation.
- Flagged record cannot advance: approve it in Manual Review Queue first.
- Stale-record conflict: reload the record before reapplying changes.

The app has no authentication or encrypted database storage. Softmax scores are uncalibrated; human review remains necessary. Original browser screenshots and historical validation are retained as older artifacts, not evidence of a new Cloud deployment.

## Trilingual localization

All application text is centralized in `locales/en.json`, `locales/kk.json` and `locales/ru.json`. Each catalog has the same keys and interpolation placeholders. Views call `t(key, **values)`; missing translations fail explicitly instead of silently falling back to English. `label()` and `display_frame()` translate copies of presentation data only. Model label order, inference, routing thresholds, SQLite schema and existing records are unchanged. User text, notes, uploaded CSV columns and machine-readable exports remain verbatim/canonical.

Widgets have stable keys and session persistence. The language selector callback explicitly rebinds canonical selection values because Streamlit 1.67 serializes formatted option strings in browser messages. Draft editors use visually equivalent bordered containers with explicit Analyze/Save/Approve buttons so changing language can capture draft fields without submitting a form. Saving and review still require the original explicit actions.

`src/native_locale.py` and `assets/native_locale.js` provide a narrowly scoped adapter for built-in Streamlit controls whose text is not configurable through the Python API, including upload controls, native errors, toolbar text and accessibility labels. It translates actual text/ARIA attributes, not just CSS overlays, and leaves entered complaint text and data cells alone. This adapter is tested against the pinned Streamlit 1.67.0; upgrades require another browser audit. Restart the app after editing catalog files. Browser/OS-owned file dialogs follow the user's browser/OS language.

The historical SVM matrices are displayed with translated axes and class labels using counts transcribed from the unchanged original source image. Automated checks verify 150 samples per task and agreement with the published Macro-F1 values. The original image remains downloadable as a historical source, with its original English labels.

Run automated localization and regression checks:

```bash
python -m pytest -q
```

Optional Chrome/Playwright checks require `playwright` and installed Google Chrome on macOS. Use an isolated QA database because the browser script creates illustrative records:

```bash
COMPLAINT_DB_PATH=/tmp/university-localization-qa.sqlite3 \
  streamlit run app.py --server.port 8511
# In another terminal, using the same virtual environment:
python scripts/browser_check.py --confirm-isolated-database \
  --output-dir /tmp/university-localization-browser
```

The script checks all 21 page/language combinations on desktop and mobile, multilingual inference independent of interface language, draft/results preservation, saving, review, search, audit history and CSV workflows. See [localization validation](LOCALIZATION_VALIDATION.md) for results, screenshots, changed files and scope limitations.
