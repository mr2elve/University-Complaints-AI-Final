"""MultiTaskXLMR reconstructed from export config, model card and checkpoint keys.

The original notebook cell 13 confirms the pooling computation; this new export
uses named ModuleDict heads (heads.category.*, etc.), unlike its ModuleList.
"""
from dataclasses import dataclass
from pathlib import Path
import threading
import torch
from torch import nn
from transformers import AutoConfig, AutoModel, AutoTokenizer, PreTrainedTokenizerFast
from src.config import MODEL_DIR
from src.model_artifacts import ensure_model_artifacts


class MultiTaskXLMR(nn.Module):
    def __init__(self, encoder_config, config):
        super().__init__()
        self.encoder = AutoModel.from_config(encoder_config)
        self.dropout = nn.Dropout(config['dropout'])
        self.heads = nn.ModuleDict({
            t: nn.Linear(self.encoder.config.hidden_size, len(config['label_maps'][t]))
            for t in config['tasks']
        })

    def forward(self, input_ids, attention_mask):
        hidden = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        mask = attention_mask.unsqueeze(-1)
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        pooled = self.dropout(pooled)
        return {task: head(pooled) for task, head in self.heads.items()}


@dataclass
class ModelBundle:
    model: MultiTaskXLMR
    tokenizer: PreTrainedTokenizerFast
    config: dict
    lock: threading.Lock


def load_model(model_dir=MODEL_DIR, *, allow_download=True):
    path = Path(model_dir)
    config = ensure_model_artifacts(path, allow_download=allow_download)
    encoder_config = AutoConfig.from_pretrained(str(path / 'encoder_config.json'), local_files_only=True)
    expected = {'model_type': 'xlm-roberta', 'hidden_size': 768, 'num_hidden_layers': 12,
                'num_attention_heads': 12, 'vocab_size': 250002, 'max_position_embeddings': 514}
    if any(getattr(encoder_config, key, None) != value for key, value in expected.items()):
        raise ValueError('Encoder configuration does not match FacebookAI/xlm-roberta-base.')
    # Eager attention avoids backend-dependent changes and supports ordinary CPUs.
    encoder_config._attn_implementation = 'eager'
    torch.set_num_threads(min(2, torch.get_num_threads()))
    # Meta construction + assignment avoids allocating/initializing another 1 GiB
    # of parameters. Every parameter must be supplied by the trained checkpoint.
    with torch.device('meta'):
        model = MultiTaskXLMR(encoder_config, config)
    state = torch.load(path / 'model.pt', map_location='cpu', weights_only=True, mmap=True)
    model.load_state_dict(state, strict=True, assign=True)
    # Transformers' two deterministic, nonpersistent buffers are absent from
    # state_dict; recreate them exactly as XLMRobertaEmbeddings.__init__ does.
    embeddings = model.encoder.embeddings
    embeddings.position_ids = torch.arange(encoder_config.max_position_embeddings).expand((1, -1))
    embeddings.token_type_ids = torch.zeros(embeddings.position_ids.size(), dtype=torch.long)
    model.cpu().eval()
    # The exported graph is authoritative; do not apply the unrelated Mistral
    # regex heuristic triggered by a task config without a model_type field.
    tokenizer = AutoTokenizer.from_pretrained(
        str(path), local_files_only=True, use_fast=True, fix_mistral_regex=False,
    )
    if tokenizer.__class__.__name__ != 'XLMRobertaTokenizerFast' or len(tokenizer) != encoder_config.vocab_size:
        raise ValueError('Expected the exported XLM-RoBERTa fast tokenizer.')
    tokenizer.model_max_length = config['max_length']
    return ModelBundle(model, tokenizer, config, threading.Lock())
