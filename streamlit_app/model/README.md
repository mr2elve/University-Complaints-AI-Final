The multilingual model is installed under `xlmr/XLMR_Multilingual_University_Complaints/`.
The older KazRoBERTa artifacts in this directory are retained and are not loaded.

Run `python scripts/setup_model.py` from `streamlit_app/`, or let the first analysis
fetch missing artifacts. Source: `mr2elve/xlmr-university-complaints-multilingual`,
subfolder `XLMR_Multilingual_University_Complaints`, pinned revision
`f15eb91b1b494b4ed92978a89b1f628e338b0ce3`.

Required export files: `model.pt`, `config.json`, `tokenizer.json`,
`tokenizer_config.json`, `special_tokens_map.json`, `sentencepiece.bpe.model`.
The additional `encoder_config.json` comes from `FacebookAI/xlm-roberta-base`;
base encoder weights are never downloaded. Complete local installations work offline.
Weights and caches are Git-ignored. See `../README.md` for setup, overrides and resources.
