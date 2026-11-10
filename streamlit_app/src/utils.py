import re
import unicodedata
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import pandas as pd
from src.config import MAX_TEXT_LENGTH


def normalize_kazakh(text):
    """Notebook cell 4, with validation performed separately."""
    text = unicodedata.normalize('NFC', str(text))
    text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def validate_text(text):
    if not isinstance(text, str) or not normalize_kazakh(text):
        raise ValueError('Complaint must contain non-empty text.')
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f'Complaint exceeds {MAX_TEXT_LENGTH:,} characters.')
    return normalize_kazakh(text)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def local_time(value):
    return datetime.fromisoformat(value).astimezone(ZoneInfo('Asia/Almaty')).strftime('%d %b %Y · %H:%M') if value else '—'


def csv_bytes(frame):
    """Neutralize spreadsheet formulas while preserving the stored source text."""
    safe = frame.copy()
    safe.columns = ["'" + c if isinstance(c, str) and c.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else c for c in safe.columns]
    for col in safe.columns:
        safe[col] = safe[col].map(lambda v: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else v)
    return safe.to_csv(index=False).encode('utf-8-sig')


def read_upload(data):
    import io
    if len(data) > 5 * 1024 * 1024:
        raise ValueError('CSV exceeds the 5 MB upload limit.')
    frame = pd.read_csv(io.BytesIO(data), encoding='utf-8-sig', nrows=1001)
    if len(frame) > 1000:
        raise ValueError('Upload at most 1,000 rows per file.')
    if frame.empty:
        raise ValueError('CSV has no data rows.')
    return frame


def combine_batch_export(source, predictions):
    result = source.reset_index(drop=True).copy()
    for column in predictions:
        name = 'ai_' + column
        while name in result.columns:
            name = 'ai_' + name
        result[name] = predictions[column].to_numpy()
    return result
