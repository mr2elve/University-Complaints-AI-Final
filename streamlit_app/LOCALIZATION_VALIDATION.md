# Trilingual localization validation

Validated locally on 14 November 2026. No commit, push or deployment was performed.

## Translation completeness

| Interface | Nonempty translations | Missing keys | Placeholder mismatches |
|---|---:|---:|---:|
| English (EN) | 427 / 427 | 0 | 0 |
| Қазақша (KK) | 427 / 427 | 0 | 0 |
| Русский (RU) | 427 / 427 | 0 | 0 |

All seven pages use the centralized catalogs, including navigation, examples, input help, prediction labels, routing explanations, status/filter labels, tables, charts, notices, exports, methodology, footer and supported native controls. Missing translation keys fail explicitly. Internal model/database identifiers remain canonical; presentation helpers translate copies only.

Language switching preserves unsubmitted complaint drafts, analysis results, navigation, filters, editor values, review confirmation, uploaded CSV contents, batch results and save consent. The interface language does not restrict input language. The original seven-page structure, palette and layout remain; translated labels can wrap. Draft editors use equivalent bordered containers with explicit action buttons so sidebar language changes can capture unsent text.

## Automated results

Command from `streamlit_app/`: `python -m pytest -q`

**104 passed in 18.42 seconds; no failures or skips.** This includes the 59 existing checks and 45 new localization checks. Python 3.11, Streamlit 1.67.0, PyTorch 2.15.0 and the existing local multilingual model artifacts were used.

Coverage includes:

- Translation-key and formatting-placeholder parity; missing literal keys and inline bilingual calls.
- All seven pages in each language (21 combinations), including empty database states.
- Real Kazakh, Russian, English and mixed Kazakh–Russian inference in every interface language (12 combinations), with explicit saving and dashboard statistics.
- EN → KK → RU → EN switching, draft/results/navigation preservation, canonical filter values, human decisions, review approval, status updates and audit history.
- CSV uploads, invalid rows, batch results, export controls, consent and persistence across language changes/navigation.
- Localized validation/error/sample states and unchanged source records/numeric research scores.
- Transcribed confusion-matrix counts: 150 examples per task and agreement with published SVM Macro-F1 to four decimals.

Dependency consistency, Python compilation and `git diff --check` also passed.

## Browser results

Chrome 157.0.8103.51 through Playwright, using an isolated temporary SQLite database with illustrative QA records. No operational complaint records were modified.

**42 page/viewport/language checks passed:** all 21 combinations at 1440 × 1050 desktop and all 21 at 390 × 844 mobile. No uncaught browser page errors or document-level horizontal overflow were detected. Mobile screenshots were recaptured after sidebar transitions completed. Wide tables retain their existing internal horizontal scrolling.

The browser also verified unsubmitted draft and saved-result preservation through language cycles; real inference in all 12 UI/input-language combinations; explicit saving; an actually flagged model prediction followed by human approval; preserved review notes and department selection; search, status changes and audit history; valid/invalid CSV rows, real batch inference, download contents and opt-in saving; and localized native upload errors. The browser script checked keyboard access to the Russian table column menu, search prompt and accessible search name. Expanded research matrix axes/class labels were checked in all three languages on both viewports; long department names wrap without overlapping. A final targeted browser check verified the native menu footer through EN → KK → RU → EN after adding its split-text-node translation.

Machine-readable results: [localization_browser_validation.json](data/localization_browser_validation.json). Representative screenshots:

- [English desktop dashboard](assets/screenshots/localization/desktop-en-dashboard.png)
- [Kazakh desktop management](assets/screenshots/localization/desktop-kk-management.png)
- [Russian desktop dashboard](assets/screenshots/localization/desktop-ru-dashboard.png)
- [English mobile batch page](assets/screenshots/localization/mobile-en-batch.png)
- [Kazakh mobile analytics](assets/screenshots/localization/mobile-kk-research.png)
- [Russian mobile analyzer](assets/screenshots/localization/mobile-ru-analyzer.png)
- [Kazakh mobile matrix](assets/screenshots/localization/mobile-kk-matrix.png)
- [Russian mobile matrix](assets/screenshots/localization/mobile-ru-matrix.png)

Reproduction commands are in [README.md](README.md#trilingual-localization). The browser script requires an explicit isolated-database flag because it saves illustrative records.

## Modified and added files

All paths below are relative to `streamlit_app/`.

Modified:

- `app.py`
- `assets/style.css`
- `src/translations.py`
- `src/ui.py`
- `src/record_ui.py`
- `views/dashboard.py`
- `views/analyzer.py`
- `views/management.py`
- `views/review.py`
- `views/batch.py`
- `views/research.py`
- `views/about.py`
- `scripts/browser_check.py`
- `README.md`
- `data/research/PROVENANCE.md`

Added:

- `locales/en.json`
- `locales/kk.json`
- `locales/ru.json`
- `src/native_locale.py`
- `src/ui_state.py`
- `assets/native_locale.js`
- `tests/test_localization.py`
- `data/research/svm_confusion_matrices.json`
- `data/localization_browser_validation.json`
- `LOCALIZATION_VALIDATION.md`
- `assets/screenshots/localization/desktop-en-dashboard.png`
- `assets/screenshots/localization/desktop-kk-management.png`
- `assets/screenshots/localization/desktop-ru-dashboard.png`
- `assets/screenshots/localization/mobile-en-batch.png`
- `assets/screenshots/localization/mobile-kk-research.png`
- `assets/screenshots/localization/mobile-ru-analyzer.png`
- `assets/screenshots/localization/mobile-kk-matrix.png`
- `assets/screenshots/localization/mobile-ru-matrix.png`

The repository-root `README.md` already had a user change before this task; it was preserved and is not part of these localization edits. Dependencies required no changes. Model architecture, weights, artifact configuration, label ordering, inference, routing thresholds, SQLite schema and backend review rules were not changed.

## Remaining scope limits

No known untranslated application-owned strings remain in the audited states. Standard technical/proper names, language autonyms, user complaints/notes, uploaded source columns and canonical machine-readable exports intentionally retain their original spelling. The unchanged historical source PNG still has English labels when downloaded; the on-screen matrices are localized.

Streamlit's built-in text/ARIA adapter depends on the pinned 1.67.0 frontend. Retest it after a Streamlit upgrade; a future framework dialog may introduce new strings. Browser/OS file dialogs use the browser/OS locale. The checks used local Chrome and a mobile-sized viewport, not a physical phone, Safari/Firefox, a screen-reader session or a deployed Community Cloud instance. The tests cover the listed states and workflows, not every possible upstream error or host-managed dialog.
