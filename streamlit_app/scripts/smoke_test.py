"""Real multilingual CPU inference and reproducible process resource measurements."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def memory():
    # macOS reports ru_maxrss in bytes; Linux reports KiB. RSS includes imports.
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    try:
        rss_kib = int(subprocess.check_output(['ps', '-o', 'rss=', '-p', str(os.getpid())]))
        rss_mib = round(rss_kib / 1024, 2)
    except (OSError, subprocess.CalledProcessError):
        rss_mib = None  # Restricted environments may forbid process inspection.
    return {'rss_mib': rss_mib,
            'peak_rss_mib': round(peak / (1024 ** 2 if sys.platform == 'darwin' else 1024), 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Write measurements and real predictions as JSON.')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--streamlit-cache', action='store_true', help='Include Streamlit UI imports and verify resource reuse; requires local artifacts.')
    args = parser.parse_args()
    started = time.perf_counter()
    from src.model_loader import load_model
    from src.inference import predict_batch
    from src.config import MODEL_DIR, MODEL_REPO_ID, MODEL_REVISION, MODEL_SUBFOLDER
    if args.streamlit_cache:
        from src.ui import cached_model
        # Ensure the benchmark cannot silently include a network download.
        from src.model_artifacts import ensure_model_artifacts
        ensure_model_artifacts(allow_download=False)
    imported = time.perf_counter()
    report = {'platform': sys.platform, 'python': sys.version.split()[0],
              'repo': MODEL_REPO_ID, 'revision': MODEL_REVISION, 'subfolder': MODEL_SUBFOLDER,
              'import_seconds': round(imported - started, 3), 'before_load': memory()}
    bundle = cached_model(str(MODEL_DIR)) if args.streamlit_cache else load_model(allow_download=not args.offline)
    report.update(load_seconds=round(time.perf_counter() - imported, 3), after_load=memory(),
                  parameter_count=sum(p.numel() for p in bundle.model.parameters()),
                  parameter_mib=round(sum(p.numel() * p.element_size() for p in bundle.model.parameters()) / 1024**2, 2),
                  checkpoint_bytes=(MODEL_DIR / 'model.pt').stat().st_size)
    if args.streamlit_cache:
        started = time.perf_counter()
        assert cached_model(str(MODEL_DIR)) is bundle
        report['cache_hit_seconds'] = round(time.perf_counter() - started, 6)
    examples = json.loads((ROOT / 'data/multilingual_examples.json').read_text())
    started = time.perf_counter()
    results = predict_batch(bundle, [e['text'] for e in examples])
    report.update(inference_seconds=round(time.perf_counter() - started, 3), after_inference=memory(),
                  results=[{'language': e['language'], **r} for e, r in zip(examples, results)])
    started = time.perf_counter()
    stress = predict_batch(bundle, [e['text'] * 30 for e in examples], batch_size=4)
    assert all(r['truncated'] for r in stress)
    report.update(full_length_batch_seconds=round(time.perf_counter() - started, 3), after_full_length_batch=memory())
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(output + '\n', encoding='utf-8')
    print(output)
    print('PASS: strict CPU checkpoint load and real Kazakh, Russian, English and mixed inference.')


if __name__ == '__main__':
    main()
