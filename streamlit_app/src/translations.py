"""Presentation-only localization. Database values and model labels stay canonical."""
from datetime import datetime
import json
import logging
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

LANGUAGES = {'English': 'en', 'Қазақша': 'kk', 'Русский': 'ru'}
LOCALE_DIR = Path(__file__).resolve().parents[1] / 'locales'
TRANSLATIONS = {code: json.loads((LOCALE_DIR / f'{code}.json').read_text(encoding='utf-8'))
                for code in LANGUAGES.values()}


def language():
    return LANGUAGES.get(st.session_state.get('language', 'English'), 'en')


def translate(key, locale, **values):
    # Missing keys fail loudly in development/tests instead of leaking English.
    return TRANSLATIONS[locale][key].format(**values)


def t(key, **values):
    return translate(key, language(), **values)


def label(value):
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        value = 'Unassigned'
    key = f'labels.{value}'
    return t(key) if key in TRANSLATIONS['en'] else str(value)


def label_formatter():
    locale = language()
    labels = {key.removeprefix('labels.'): value for key, value in TRANSLATIONS[locale].items()
              if key.startswith('labels.')}
    labels[None] = labels['Unassigned']
    return lambda value: labels.get(value, str(value))


def column_labels(columns):
    return {column: t(f'columns.{column}') if f'columns.{column}' in TRANSLATIONS['en'] else label(column)
            for column in columns}


def display_time(value):
    # Numeric dates avoid host-dependent English month names, while preserving Almaty time.
    return datetime.fromisoformat(value).astimezone(ZoneInfo('Asia/Almaty')).strftime('%d.%m.%Y · %H:%M') if value else '—'


ERROR_KEYS = {value: key for key, value in TRANSLATIONS['en'].items() if key.startswith('error.')}


def error_text(error):
    message = str(error)
    if message in ERROR_KEYS:
        return t(ERROR_KEYS[message])
    if isinstance(error, (UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError)):
        return t('error.csv_invalid')
    logging.getLogger(__name__).error('UI operation failed: %s', message)
    return t('error.generic')


ENUM_COLUMNS = {'category', 'urgency', 'tone', 'department', 'predicted_category', 'predicted_urgency',
                'predicted_tone', 'predicted_department', 'effective_urgency', 'assigned_department',
                'status', 'previous_status', 'new_status', 'previous_department', 'new_department',
                'previous_urgency', 'new_urgency', 'action', 'operational_priority', 'language'}


def display_frame(frame):
    """Copy and localize known application fields; never modify source text or stored rows."""
    result = frame.copy()
    for column in result:
        if column == 'operational_priority':
            result[column] = result[column].map(lambda v: label('priority_' + str(v)))
        elif column in ENUM_COLUMNS:
            result[column] = result[column].map(lambda v: label(v) if isinstance(v, str) or pd.isna(v) else v)
        elif column in ('submitted_at', 'resolved_at', 'reviewed_at', 'timestamp'):
            result[column] = result[column].map(display_time)
        elif column in ('requires_review', 'truncated'):
            result[column] = result[column].map(lambda v: label('yes' if v else 'no'))
        elif column == 'review_reasons':
            result[column] = result[column].map(lambda v: ' · '.join(label(x.strip()) for x in str(v).replace(' · ', ';').split(';')))
        elif column == 'error':
            result[column] = result[column].map(lambda v: error_text(v) if isinstance(v, str) and v else '')
    return result.rename(columns=column_labels(result.columns))
