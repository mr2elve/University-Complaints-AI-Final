"""Install trusted exported artifacts and fetch only a small base architecture config."""
import argparse
import json
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.config import read_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', nargs='?', type=Path, help='Trusted local KazRoBERTa_Trained_Model.zip')
    parser.add_argument('--model-dir', type=Path, default=ROOT/'model')
    parser.add_argument('--encoder-config', type=Path, help='Use a previously downloaded base config; entirely offline.')
    parser.add_argument('--hub-repo', help='Future repository containing the trained export, only if it has been published.')
    parser.add_argument('--revision', default='main', help='Optional immutable Hub commit revision.')
    args = parser.parse_args()
    if args.archive and args.hub_repo:
        parser.error('Choose a local archive or a published Hub repository, not both.')
    args.model_dir.mkdir(parents=True, exist_ok=True)
    files = ['model.pt','config.json','tokenizer.json','tokenizer_config.json']
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
    elif args.hub_repo:
        from huggingface_hub import hf_hub_download
        for name in files:
            path=hf_hub_download(args.hub_repo,name,revision=args.revision)
            shutil.copy2(path,args.model_dir/name)
    config=read_config(args.model_dir)
    target=args.model_dir/'encoder_config.json'
    if args.encoder_config:
        if args.encoder_config.resolve() != target.resolve():shutil.copy2(args.encoder_config,target)
    elif not target.exists():
        url=f'https://huggingface.co/{config["model_name"]}/resolve/main/config.json'
        print('Downloading base architecture configuration only:',url)
        with urllib.request.urlopen(url,timeout=45) as response:
            data=response.read(1_000_000)
        parsed=json.loads(data)
        if parsed.get('model_type')!='roberta':raise ValueError('Unexpected encoder type')
        target.write_bytes(data)
    print('Model artifacts ready:',args.model_dir)
    print('Run: python scripts/smoke_test.py')


if __name__=='__main__':main()
