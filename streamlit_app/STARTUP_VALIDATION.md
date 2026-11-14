# Cloud translation import recovery — 14 November 2026

## Confirmed evidence

The supplied production exception is:

```text
ImportError: cannot import name 'error_text' from 'src.translations'
(/mount/src/university-complaints-ai-final/streamlit_app/src/translations.py)
```

It identifies a loaded application module that does not expose the new translation API. It is not evidence that the function is missing from the current Git source.

| Source checked | Revision | `t` / `error_text` |
|---|---|---|
| Local HEAD (`main`) | `0aa70fbca19460dc3f475fd1166ea6a7c913e34f` | Both present |
| Local `origin/main` | Same revision | Both present |
| Live GitHub `refs/heads/main` (`git ls-remote`) | Same revision | Matches the locally available Git object |
| Cloud worker | Not exposed in the supplied logs | Reported missing `error_text` |

The working tree, HEAD and origin/main translation files are byte-identical. SHA-256: `d9afcfc33cab714902e7cfd9ac1d0e898f1e2560824313cc9a4f7c2320408578`.

`src/translations.py` defines `t` at line 25 and `error_text` at line 57. Both are unconditional module-level functions. All translation imports in the seven views and shared helpers resolve. All three locale catalogs are tracked. No Python bytecode files are tracked, and no application-level circular import was found.

The pre-localization revision `b0e489b` defines `t` but not `error_text`; its app imports only `t`. Revision `2a859fc` adds `error_text` and updates the app in the same commit. Inspection of the relevant `main` history found no committed incompatible app/translation pair.

## Diagnosis and reproduction

**The reported running app/translation API is inconsistent with current main. A stale in-memory module or mixed deployment is the supported diagnosis; the exact Cloud worker revision and memory-versus-disk mechanism remain unverified.** The exception alone cannot supply the deployed SHA, and authenticated Cloud logs were unavailable.

A controlled experiment reproduced the exact missing-name error:

1. Load the real pre-localization translation module from `b0e489b` in a temporary directory and new Python process.
2. Replace that temporary source file with the current translation source, without restarting the process.
3. Execute `from src.translations import t, error_text`. Python reuses the old module in `sys.modules`, producing `cannot import name 'error_text'` even though the source file now contains it.
4. Start a new Python process against those same updated files. The exact import succeeds.

This proves a mechanism for the observed failure and validates fresh-worker recovery locally. It does not establish that this exact sequence occurred inside Community Cloud. No experiment touched the real SQLite database or model files.

## Smallest deployment change

The application source already contains the required function, so adding a duplicate function, catching this ImportError or manually reloading modules would not repair a stale deployed process reliably.

`requirements.txt` receives one comment identifying the EN/KK/RU API deployment refresh. Every dependency pin, index and platform marker remains identical. The file change is intended to request Cloud's dependency-file rebuild path when you deploy it, instead of relying only on a live source update. Verify the build in Cloud logs; if Cloud does not rebuild for a comment-only change, use its explicit **Reboot app** action. The comment itself does not reload Python modules.

Streamlit documents dependency-file-triggered redeployment in [Manage your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app) and fresh-build/memory reset in [Reboot your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/reboot-your-app).

Manual recovery:

1. Preserve any existing Cloud-local SQLite data before rebuilding/rebooting. This patch does not change database files or schema, but [Community Cloud does not guarantee local-file persistence](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data). No production storage backup could be taken from this workspace.
2. Verify Cloud's repository is `mr2elve/University-Complaints-AI-Final`, branch `main`, entrypoint `streamlit_app/app.py`, and Python is 3.11 or newer.
3. Deploy the reviewed changes and check that a fresh build starts from the intended commit. Alternatively, the already-pushed `0aa70fb` contains the correct translation implementation and can be recovered using **Manage app → overflow menu → Reboot app**. A script rerun or Streamlit data/resource-cache clear does not guarantee a new Python interpreter.
4. Confirm the fresh startup has no import error and open the seven pages in all three languages. If it still fails, retain the new full traceback and deployment commit/build log; that would require further investigation of the worker's actual source.

No production restart or deployment was performed, as requested.

## Validation results

From `streamlit_app/`:

```bash
python -m pytest -q tests/test_startup.py
# 3 passed in 10.88 seconds
python -m pytest -q
# 107 passed in 29.90 seconds
```

No failures or skips. The new regression test executes the exact `from src.translations import t, error_text` statement before the app can preload translations. It runs in a new interpreter with Python environment customization/user-site packages excluded and a separate bytecode-cache prefix.

The existing two fresh-process startup tests run from the application directory and repository root, respectively. Each checks all 21 page/language combinations, all translation imports and the resolved module path. The full suite also covers real multilingual XLM-RoBERTa inference, routing, saving, filters, manual review/audit history and batch processing. The three catalogs still have 427 matching keys each.

`pip check` and `git diff --check` pass. A semantic comparison confirms no requirements changes beyond the comment. Tests ran on macOS/Python 3.11.4; actual Linux/Cloud execution remains unverified. The previous exact-case path and Linux CPU-marker checks remain applicable.

## Files changed in this recovery task

- `requirements.txt`: comment-only deployment refresh marker; dependency specifications unchanged.
- `tests/test_startup.py`: direct, fresh-process translation import regression test.
- `STARTUP_VALIDATION.md`: updated evidence, reproduction, recovery procedure and results.

`app.py`, `src/translations.py`, the locale catalogs, all seven views, model architecture/weights/Hugging Face configuration, inference, routing and database code remain unchanged. The pre-existing repository-root README edit was preserved. No commit or push was made.
