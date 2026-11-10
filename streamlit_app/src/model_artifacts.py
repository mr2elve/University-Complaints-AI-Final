"""Local-first installation of the trained export, never base model weights."""
import json
import os
from pathlib import Path
import tempfile
import threading

from huggingface_hub import hf_hub_download

from src.config import MODEL_DIR, MODEL_REPO_ID, MODEL_REVISION, read_config

EXPORT_FILES = ('config.json', 'model.pt', 'tokenizer.json', 'tokenizer_config.json')
_setup_lock = threading.Lock()


class ModelDownloadError(RuntimeError):
    """An artifact could not be obtained; inference must remain unavailable."""


def _download(repo_id, filename, directory, revision):
    try:
        # Hub writes completed files atomically and retains download metadata and
        # resumable partial downloads under directory/.cache/huggingface.
        return Path(hf_hub_download(
            repo_id=repo_id, filename=filename, revision=revision,
            local_dir=directory,
        ))
    except Exception as exc:
        raise ModelDownloadError(
            f'Could not download {filename} from {repo_id} (revision {revision}). '
            'Check network access and repository availability, then retry model '
            'loading or run python scripts/setup_model.py. '
            'Existing local files were kept; no prediction was made.'
        ) from exc


def ensure_model_artifacts(model_dir=MODEL_DIR, *, repo_id=MODEL_REPO_ID,
                           revision=MODEL_REVISION, allow_download=True):
    """Fill missing files only and return the unchanged, validated task config.

    A complete local installation makes no Hub requests. The task config and
    encoder config have different meanings and must never overwrite each other.
    """
    path = Path(model_dir)
    with _setup_lock:
        for filename in EXPORT_FILES:
            if not (path / filename).is_file():
                if not allow_download:
                    raise FileNotFoundError(f'Missing {path / filename}; automatic downloads are disabled.')
                _download(repo_id, filename, path, revision)
            if filename == 'config.json':
                config = read_config(path)

        encoder_path = path / 'encoder_config.json'
        if not encoder_path.is_file():
            if not allow_download:
                raise FileNotFoundError(f'Missing {encoder_path}; automatic downloads are disabled.')
            # The four-file trained export names the original encoder. Fetch
            # only its small architecture JSON into a separate cached directory.
            source = _download(config['model_name'], 'config.json', path / '.cache' / 'encoder', 'main')
            data = source.read_bytes()
            if json.loads(data).get('model_type') != 'roberta':
                raise ValueError('Unexpected encoder type; expected the original RoBERTa architecture.')
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=path, suffix='.tmp', delete=False) as output:
                    temporary = Path(output.name)
                    output.write(data)
                os.replace(temporary, encoder_path)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        return config
