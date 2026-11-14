"""Localize built-in Streamlit chrome not exposed by its Python widget API.

The adapter only handles known framework strings in framework controls. It never
walks complaint text, user data cells, or inputs to translate user content.
"""
import json
from pathlib import Path
import streamlit as st
from src.translations import TRANSLATIONS, language, t


def install_native_locale():
    keys = [key for key in TRANSLATIONS['en'] if key.startswith('native.')]
    locale = language()
    replacements = {values[key]: TRANSLATIONS[locale][key]
                    for values in TRANSLATIONS.values() for key in keys}
    payload = json.dumps({'language': locale, 'title': t('ui.ai_university_complaint_management_system'),
                          'replacements': replacements,
                          'availableCount': TRANSLATIONS[locale]['native.available_count'],
                          'searchResults': TRANSLATIONS[locale]['native.search_results'],
                          'searchPosition': TRANSLATIONS[locale]['native.search_position'],
                          'selectMatches': TRANSLATIONS[locale]['native.select_matches'],
                          'fileTypeError': TRANSLATIONS[locale]['native.file_type_error'],
                          'fileSizeError': TRANSLATIONS[locale]['native.file_size_error']}, ensure_ascii=False).replace('<', '\\u003c')
    script = (Path(__file__).resolve().parents[1] / 'assets/native_locale.js').read_text()
    st.html('<script>' + script.replace('__LOCALE_PAYLOAD__', payload) + '</script>',
            unsafe_allow_javascript=True)
