The application automatically downloads missing trained artifacts from
https://huggingface.co/mr2elve/kazroberta-university-complaints on first model load.
To download ahead of time, run `python scripts/setup_model.py` from `streamlit_app/`.

Required: `model.pt`, `config.json` (application config), `tokenizer.json`, `tokenizer_config.json`, and `encoder_config.json` (base Transformer architecture).
The loader and setup script preserve existing local files. They download only the
four trained export files plus the small base architecture config when absent;
they never download base encoder weights or retrain the model. Hugging Face
download metadata stays under `.cache/` here. A complete installation works offline.

For an offline ZIP installation, use `python scripts/setup_model.py /path/to/KazRoBERTa_Trained_Model.zip --encoder-config /path/to/encoder_config.json --offline`.

`COMPLAINT_MODEL_DIR` overrides this directory. Model artifacts and their cache are
ignored by Git. See the application README for repository/revision overrides.
