# Startup ImportError investigation — 14 November 2026

## Finding

**The production cause is not established by the supplied traceback excerpt. No application-code fix is justified yet.** The line `from src.translations import t, error_text` identifies the import statement, but not which name/dependency failed or which file the worker loaded.

The inspected checkout is branch `main`, commit `2a859fcbe5145934b1838abbfe3ca0f812701ba3`. Both the committed file and the working copy define `t` (line 25) and `error_text` (line 57). A fresh Python process imports both successfully from this checkout's `streamlit_app/src/translations.py`.

All translation imports in `app.py`, the seven views, `src/ui.py`, `src/record_ui.py` and `src/native_locale.py` resolve. `src/__init__.py` contains only a docstring. The translation module does not import the app or its helpers, so no application-level circular import was found. All three UTF-8 catalogs are committed, have the correct case-sensitive paths and contain 427 keys.

The previous commit's translation module defines `t` but does **not** define `error_text`. A worker loading the old module alongside the new entrypoint could therefore fail at this statement. This is a hypothesis, not a confirmed diagnosis of the production worker. A nested dependency ImportError also cannot be excluded without the complete exception.

The public production page did not expose a traceback to the read-only browser inspection. Private Community Cloud deployment logs were not available.

## Validation

- Full suite: **106 passed in 27.80 seconds**, no failures or skips. This includes the 104 existing tests and two new subprocess startup tests.
- Each new test launches a fresh Python interpreter, ignores Python environment customization and user-site packages, and uses a new bytecode-cache prefix with bytecode writes disabled. One runs from `streamlit_app/`; the other runs from the repository root. Both render all seven pages in EN, KK and RU and verify every translation import plus the resolved module path.
- The exact Streamlit CLI entrypoint was also launched in a new process from `streamlit_app/`, with an isolated temporary SQLite database and separate bytecode path. Chrome checked all 21 page/language combinations on that server.
- Existing tests continue to exercise real XLM-RoBERTa inference in Kazakh, Russian, English and mixed input, saving, routing, review, audit history and batch processing.
- `pip check` reports no broken installed requirements. `git diff --check` passes.

Reproduce the startup regression checks from `streamlit_app/`:

```bash
python -m pytest -q tests/test_startup.py
python -m pytest -q
```

## Linux and Community Cloud checks

Local execution used macOS and Python 3.11.4. Actual Linux execution was **not** performed: the installed Docker command is a broken link to a missing Docker application. These results do not establish that production has recovered.

Static checks confirmed exact-case package/catalog filenames and that catalog paths are anchored to `__file__`, not the working directory. The Linux dependency marker selects `torch==2.15.0+cpu`. The installed packages' Python-version metadata is compatible with Python 3.11/3.12; Streamlit, NumPy and PyTorch pins require Python 3.11 or newer. This checks metadata/markers, not availability or installation of Linux wheels in the production environment.

Community Cloud starts from the repository root and prefers a dependency file beside the entrypoint. With entrypoint `streamlit_app/app.py`, the intended file is `streamlit_app/requirements.txt`, not the repository-root research/training requirements. The deployment's actual entrypoint, selected dependency file and Python version still need confirmation. See the official [file organization](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization) and [dependency selection](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies) documentation.

## Log lines needed to identify and fix production

Please provide the relevant text from Community Cloud's app logs:

1. The complete exception, from `Traceback (most recent call last):` through the final `ImportError: ...` line. Preserve the missing symbol/module name, absolute module path and any “partially initialized module” or nested exception details.
2. The deployment/pull lines showing repository, branch, entrypoint and revision/commit, if logged. If not logged, provide the deployed branch and commit from deployment settings/history.
3. The Python/Streamlit version lines and dependency-install lines identifying the requirements file and any installer errors.

Those distinguish a stale/mismatched deployed source from package shadowing, a partial import or a dependency failure. No import fallback, manual `sys.modules` manipulation or silent error suppression has been added.

## Changes

- Added `tests/test_startup.py`: fresh-process startup/import regression tests.
- Added `STARTUP_VALIDATION.md`: this investigation and the exact missing evidence.

Application code, translations, dependencies, model architecture/weights/Hugging Face configuration, inference, routing and SQLite data were not modified. The existing repository-root README change was preserved. No commit, push, production restart or deployment was performed.
