"""Exact notebook cell 15 architecture with local-first trained artifact setup."""
from dataclasses import dataclass
from pathlib import Path
import threading
import torch
from torch import nn
from transformers import AutoConfig, AutoModel, PreTrainedTokenizerFast
from src.config import MODEL_DIR, TARGETS
from src.model_artifacts import ensure_model_artifacts


class MultiTaskKazRoBERTa(nn.Module):
    def __init__(self, encoder_config, label_maps):
        super().__init__()
        self.encoder = AutoModel.from_config(encoder_config)
        self.dropout = nn.Dropout(0.2)
        self.heads = nn.ModuleList([
            nn.Linear(self.encoder.config.hidden_size, len(label_maps[t])) for t in TARGETS
        ])

    def forward(self, input_ids, attention_mask):
        hidden = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        mask = attention_mask.unsqueeze(-1)
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        pooled = self.dropout(pooled)
        return [head(pooled) for head in self.heads]


@dataclass
class ModelBundle:
    model: MultiTaskKazRoBERTa
    tokenizer: PreTrainedTokenizerFast
    config: dict
    lock: threading.Lock


def load_model(model_dir=MODEL_DIR, *, allow_download=True):
    path = Path(model_dir)
    config = ensure_model_artifacts(path, allow_download=allow_download)
    encoder_config = AutoConfig.from_pretrained(str(path / 'encoder_config.json'), local_files_only=True)
    # Eager attention avoids backend-dependent changes and supports ordinary CPUs.
    encoder_config._attn_implementation = 'eager'
    model = MultiTaskKazRoBERTa(encoder_config, config['label_maps'])
    # Memory mapping avoids allocating a second full checkpoint buffer on Cloud.
    state = torch.load(path / 'model.pt', map_location='cpu', weights_only=True, mmap=True)
    model.load_state_dict(state, strict=True)
    model.cpu().eval()
    # Loading the complete exported tokenizers graph preserves its postprocessor.
    tokenizer = PreTrainedTokenizerFast(
        tokenizer_file=str(path / 'tokenizer.json'),
        bos_token='<s>', eos_token='</s>', cls_token='<s>', sep_token='</s>',
        pad_token='<pad>', unk_token='<unk>', mask_token='<mask>', model_max_length=96,
    )
    torch.set_num_threads(min(4, torch.get_num_threads()))
    return ModelBundle(model, tokenizer, config, threading.Lock())
