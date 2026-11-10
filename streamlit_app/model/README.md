Place the trusted research export here using `python scripts/setup_model.py /path/to/KazRoBERTa_Trained_Model.zip`.

Required: `model.pt`, `config.json` (application config), `tokenizer.json`, `tokenizer_config.json`, and `encoder_config.json` (base Transformer architecture).
The setup script downloads only the small base config when absent. It never downloads or trains model weights unless you explicitly pass a future published `--hub-repo` containing the trained export.

Model artifacts are ignored by Git. The original trained archive has been installed locally for this workspace.
