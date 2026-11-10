"""Network-independent setup tests; actual predictions use the real checkpoint."""
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from src import model_artifacts as artifacts
from src.config import DEPARTMENTS, ROOT, TARGETS, read_config
from src.model_loader import load_model


@pytest.fixture
def export_files():
    labels = (
        ('academic_process', 'administrative_services', 'campus_environment'),
        ('high', 'low', 'medium'),
        ('dissatisfied', 'intense_negative', 'neutral'),
        DEPARTMENTS,
    )
    config = {
        'model_name': 'kz-transformers/kaz-roberta-conversational',
        'targets': list(TARGETS),
        'label_maps': {task: dict(zip(names, range(len(names)))) for task, names in zip(TARGETS, labels)},
        'confidence_threshold': .75, 'urgent_review_threshold': .3, 'max_length': 96,
    }
    # Placeholders exercise file transport only; never passed to inference.
    return {
        'config.json': json.dumps(config).encode(),
        'model.pt': b'transport test placeholder, not a checkpoint',
        'tokenizer.json': b'{}', 'tokenizer_config.json': b'{}',
        'encoder_config.json': b'{"model_type": "roberta", "hidden_size": 768}',
    }


def install(path, files):
    path.mkdir(parents=True, exist_ok=True)
    for filename, data in files.items():
        (path / filename).write_bytes(data)


@pytest.fixture
def hub(monkeypatch, export_files):
    calls = []

    def download(*, repo_id, filename, revision, local_dir):
        calls.append((repo_id, filename, revision, Path(local_dir)))
        key = 'encoder_config.json' if repo_id.startswith('kz-transformers/') else filename
        install(Path(local_dir), {filename: export_files[key]})
        return str(Path(local_dir) / filename)

    monkeypatch.setattr(artifacts, 'hf_hub_download', download)
    return calls


def test_empty_directory_downloads_only_required_artifacts(tmp_path, hub, export_files):
    path = tmp_path / 'model'
    config = artifacts.ensure_model_artifacts(path, repo_id='owner/trained', revision='commit-sha')
    assert config == read_config(path)
    assert [(repo, name, revision) for repo, name, revision, _ in hub] == [
        *[('owner/trained', name, 'commit-sha') for name in artifacts.EXPORT_FILES],
        ('kz-transformers/kaz-roberta-conversational', 'config.json', 'main'),
    ]
    assert [directory for *_, directory in hub] == [path] * 4 + [path / '.cache' / 'encoder']
    for name, data in export_files.items():
        assert (path / name).read_bytes() == data
    assert not list(path.glob('*.tmp'))


def test_complete_local_installation_never_contacts_hub(tmp_path, hub, export_files):
    install(tmp_path, export_files)
    artifacts.ensure_model_artifacts(tmp_path)
    artifacts.ensure_model_artifacts(tmp_path, allow_download=False)
    assert hub == []


def test_partial_installation_keeps_local_weights_and_config(tmp_path, hub, export_files):
    install(tmp_path, {'config.json': export_files['config.json']})
    (tmp_path / 'model.pt').write_bytes(b'existing local weights must not be replaced')
    artifacts.ensure_model_artifacts(tmp_path)
    assert [name for _, name, _, _ in hub] == ['tokenizer.json', 'tokenizer_config.json', 'config.json']
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
    assert [name for _, name, _, _ in hub] == ['model.pt', 'tokenizer.json', 'tokenizer_config.json', 'config.json']


def test_invalid_task_config_stops_before_weight_download(tmp_path, hub, export_files):
    config = json.loads(export_files['config.json'])
    config['targets'].reverse()
    install(tmp_path, {'config.json': json.dumps(config).encode()})
    with pytest.raises(ValueError, match='head order'):
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
