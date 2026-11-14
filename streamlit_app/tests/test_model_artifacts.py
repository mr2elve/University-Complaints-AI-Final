"""Network-independent setup tests; actual predictions use the real checkpoint."""
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from src import model_artifacts as artifacts
from src.config import DEPARTMENTS, ROOT, TARGETS, MODEL_SUBFOLDER, ENCODER_REPO_ID, read_config
from src.model_loader import load_model


@pytest.fixture
def export_files():
    config = json.loads((Path(__file__).parent / 'fixtures/xlmr_config.json').read_text())
    # Placeholders exercise file transport only; never passed to inference.
    return {
        'config.json': json.dumps(config).encode(),
        'model.pt': b'transport test placeholder, not a checkpoint',
        'tokenizer.json': b'{}', 'tokenizer_config.json': b'{}',
        'special_tokens_map.json': b'{}', 'sentencepiece.bpe.model': b'transport-only',
        'encoder_config.json': b'{"model_type": "xlm-roberta", "hidden_size": 768}',
    }


def install(path, files):
    path.mkdir(parents=True, exist_ok=True)
    for filename, data in files.items():
        (path / filename).write_bytes(data)


@pytest.fixture
def hub(monkeypatch, export_files):
    calls = []

    def download(*, repo_id, filename, revision, cache_dir, subfolder):
        calls.append((repo_id, filename, revision, Path(cache_dir), subfolder))
        key = 'encoder_config.json' if repo_id == ENCODER_REPO_ID else filename
        install(Path(cache_dir), {filename: export_files[key]})
        return str(Path(cache_dir) / filename)

    monkeypatch.setattr(artifacts, 'hf_hub_download', download)
    return calls


def test_empty_directory_downloads_only_required_artifacts(tmp_path, hub, export_files):
    path = tmp_path / 'model'
    config = artifacts.ensure_model_artifacts(path, repo_id='owner/trained', revision='commit-sha')
    assert config == read_config(path)
    assert [(repo, name, revision) for repo, name, revision, _, _ in hub] == [
        *[('owner/trained', name, 'commit-sha') for name in artifacts.EXPORT_FILES],
        (ENCODER_REPO_ID, 'config.json', 'main'),
    ]
    assert [folder for *_, folder in hub] == [MODEL_SUBFOLDER] * len(artifacts.EXPORT_FILES) + [None]
    for name, data in export_files.items():
        assert (path / name).read_bytes() == data
    assert not list(path.glob('*.tmp'))


def test_complete_local_installation_never_contacts_hub(tmp_path, hub, export_files):
    install(tmp_path, export_files)
    artifacts.ensure_model_artifacts(tmp_path)
    artifacts.ensure_model_artifacts(tmp_path, allow_download=False)
    assert hub == []


def test_hub_snapshot_symlinks_remain_valid_after_install(tmp_path, hub, monkeypatch, export_files):
    download = artifacts.hf_hub_download

    def snapshot_download(**kwargs):
        blob = Path(download(**kwargs))
        snapshot = blob.parent / 'snapshots' / 'revision'
        snapshot.mkdir(parents=True, exist_ok=True)
        link = snapshot / blob.name
        link.symlink_to(os.path.relpath(blob, snapshot))
        return str(link)

    monkeypatch.setattr(artifacts, 'hf_hub_download', snapshot_download)
    artifacts.ensure_model_artifacts(tmp_path)
    for name, data in export_files.items():
        assert (tmp_path / name).read_bytes() == data
        assert not (tmp_path / name).is_symlink()


def test_partial_installation_keeps_local_weights_and_config(tmp_path, hub, export_files):
    install(tmp_path, {'config.json': export_files['config.json']})
    (tmp_path / 'model.pt').write_bytes(b'existing local weights must not be replaced')
    artifacts.ensure_model_artifacts(tmp_path)
    assert [name for _, name, _, _, _ in hub] == ['tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'sentencepiece.bpe.model', 'config.json']
    assert (tmp_path / 'model.pt').read_bytes() == b'existing local weights must not be replaced'
    assert (tmp_path / 'config.json').read_bytes() == export_files['config.json']


@pytest.mark.parametrize('missing', artifacts.EXPORT_FILES + ('encoder_config.json',))
def test_offline_missing_file_never_contacts_hub(tmp_path, hub, export_files, missing):
    install(tmp_path, {k: v for k, v in export_files.items() if k != missing})
    with pytest.raises(FileNotFoundError, match=missing):
        artifacts.ensure_model_artifacts(tmp_path, allow_download=False)
    assert hub == []


def test_download_failure_preserves_files_and_retry_fetches_only_missing(tmp_path, monkeypatch, hub, export_files):
    download = artifacts.hf_hub_download

    def fail_weights(**kwargs):
        if kwargs['filename'] == 'model.pt':
            raise OSError('network unavailable')
        return download(**kwargs)

    monkeypatch.setattr(artifacts, 'hf_hub_download', fail_weights)
    with pytest.raises(artifacts.ModelDownloadError, match='model.pt') as failure:
        load_model(tmp_path)  # Default app loading must attempt automatic setup.
    assert isinstance(failure.value.__cause__, OSError)
    assert 'no prediction was made' in str(failure.value)
    assert (tmp_path / 'config.json').read_bytes() == export_files['config.json']
    assert not (tmp_path / 'model.pt').exists()
    hub.clear()
    monkeypatch.setattr(artifacts, 'hf_hub_download', download)
    artifacts.ensure_model_artifacts(tmp_path)
    assert [name for _, name, _, _, _ in hub] == ['model.pt', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'sentencepiece.bpe.model', 'config.json']


def test_invalid_task_config_stops_before_weight_download(tmp_path, hub, export_files):
    config = json.loads(export_files['config.json'])
    config['tasks'] = ['category'] * 4
    install(tmp_path, {'config.json': json.dumps(config).encode()})
    with pytest.raises(ValueError, match='tasks'):
        artifacts.ensure_model_artifacts(tmp_path)
    assert hub == []


def test_invalid_encoder_is_not_installed(tmp_path, hub, export_files):
    export_files['encoder_config.json'] = b'{"model_type": "bert"}'
    with pytest.raises(ValueError, match='encoder type'):
        artifacts.ensure_model_artifacts(tmp_path)
    assert not (tmp_path / 'encoder_config.json').exists()
    assert (tmp_path / 'config.json').read_bytes() == export_files['config.json']


def test_local_archive_setup_still_works_offline(tmp_path, export_files):
    archive = tmp_path / 'trusted.zip'
    with zipfile.ZipFile(archive, 'w') as output:
        for name in artifacts.EXPORT_FILES:
            output.writestr(f'model/{name}', export_files[name])
    encoder = tmp_path / 'original_encoder.json'
    encoder.write_bytes(export_files['encoder_config.json'])
    destination = tmp_path / 'installed'
    result = subprocess.run([
        sys.executable, str(ROOT / 'scripts' / 'setup_model.py'), str(archive),
        '--model-dir', str(destination), '--encoder-config', str(encoder), '--offline',
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for name, data in export_files.items():
        assert (destination / name).read_bytes() == data


def test_export_label_order_and_task_order_are_preserved(tmp_path, export_files):
    config = json.loads(export_files['config.json'])
    config['tasks'].reverse()
    for task, names in config['label_names'].items():
        names.reverse()
        config['label2id'][task] = {name: i for i, name in enumerate(names)}
        config['id2label'][task] = {str(i): name for i, name in enumerate(names)}
    raw = json.dumps(config).encode()
    install(tmp_path, {'config.json': raw})
    actual = read_config(tmp_path)
    assert actual['targets'] == config['tasks']
    assert actual['label_maps'] == config['label2id']
    assert actual['confidence_threshold'] == .75
    assert actual['urgent_review_threshold'] == .30
    assert actual['sla_hours'] == {'high': 4, 'medium': 24, 'low': 72}
    assert (tmp_path / 'config.json').read_bytes() == raw


@pytest.mark.parametrize('change', ['old_encoder', 'pooling', 'labels', 'length'])
def test_incompatible_export_fails_before_download(tmp_path, hub, export_files, change):
    config = json.loads(export_files['config.json'])
    if change == 'old_encoder':
        config['base_model'] = 'kz-transformers/kaz-roberta-conversational'
    elif change == 'pooling':
        config['pooling'] = 'cls'
    elif change == 'labels':
        config['label2id']['category']['academic_process'] = 2
    else:
        config['max_length'] = 1024
    install(tmp_path, {'config.json': json.dumps(config).encode()})
    with pytest.raises(ValueError):
        artifacts.ensure_model_artifacts(tmp_path)
    assert hub == []
