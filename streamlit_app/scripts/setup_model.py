"""Download the trained Hub export, or install a trusted local exported archive."""
import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.config import MODEL_DIR, MODEL_REPO_ID, MODEL_REVISION, read_config
from src.model_artifacts import EXPORT_FILES, ensure_model_artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', nargs='?', type=Path, help='Trusted local KazRoBERTa_Trained_Model.zip')
    parser.add_argument('--model-dir', type=Path, default=MODEL_DIR)
    parser.add_argument('--encoder-config', type=Path, help='Use a previously downloaded base config; entirely offline.')
    parser.add_argument('--hub-repo', help=f'Trained export repository (default: {MODEL_REPO_ID}).')
    parser.add_argument('--revision', default=MODEL_REVISION, help='Hub branch, tag, or immutable commit revision.')
    parser.add_argument('--offline', action='store_true', help='Use local artifacts only; never contact Hugging Face.')
    args = parser.parse_args()
    if args.archive and args.hub_repo:
        parser.error('Choose a local archive or a published Hub repository, not both.')
    args.model_dir.mkdir(parents=True, exist_ok=True)
    files = EXPORT_FILES
    if args.archive:
        with zipfile.ZipFile(args.archive) as archive:
            # Never extract arbitrary paths, executable code, or archive symlinks.
            for name in files:
                member = next((x for x in (f'model/{name}', name) if x in archive.namelist()), None)
                if not member:
                    raise ValueError(f'Archive is missing {name}')
                if archive.getinfo(member).file_size > 2_000_000_000:
                    raise ValueError('Unexpectedly large model artifact.')
            with tempfile.TemporaryDirectory(dir=args.model_dir) as tmp:
                for name in files:
                    member = next(x for x in (f'model/{name}',name) if x in archive.namelist())
                    with archive.open(member) as source, open(Path(tmp)/name,'wb') as target:
                        shutil.copyfileobj(source,target)
                read_config(tmp)
                for name in files:
                    shutil.move(str(Path(tmp)/name),args.model_dir/name)
    target=args.model_dir/'encoder_config.json'
    if args.encoder_config:
        if args.encoder_config.resolve() != target.resolve():shutil.copy2(args.encoder_config,target)
    ensure_model_artifacts(
        args.model_dir, repo_id=args.hub_repo or MODEL_REPO_ID,
        revision=args.revision, allow_download=not args.offline,
    )
    print('Model artifacts ready:',args.model_dir)
    print('Run: python scripts/smoke_test.py')


if __name__=='__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError) as exc:
        sys.exit(f'Model setup failed: {exc}')
