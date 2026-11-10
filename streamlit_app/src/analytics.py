import pandas as pd


def dashboard_metrics(df):
    if df.empty:
        return dict(total=0, pending=0, auto=0, review=0, high=0, resolved=0, confidence=0)
    active = ~df.status.isin(['Resolved', 'Closed'])
    return {
        'total': len(df), 'pending': int(active.sum()),
        'auto': int((df.requires_review == 0).sum()),
        'review': int(((df.requires_review == 1) & df.reviewed_at.isna()).sum()),
        'high': int((active & ((df.effective_urgency == 'high') | (df.high_urgency_probability >= .30))).sum()),
        'resolved': int(df.status.isin(['Resolved', 'Closed']).sum()),
        'confidence': float(df.routing_confidence.mean()),
    }


def filter_complaints(df, search='', filters=None, review='all', ascending=False):
    result = df.copy()
    if search:
        result = result[result.complaint_text.str.contains(search, case=False, regex=False) | result.id.astype(str).eq(search)]
    for column, values in (filters or {}).items():
        if values:
            result = result[result[column].isin(values)]
    if review == 'awaiting':
        result = result[(result.requires_review == 1) & result.reviewed_at.isna()]
    elif review == 'reviewed':
        result = result[result.reviewed_at.notna()]
    elif review == 'auto':
        result = result[result.requires_review == 0]
    return result.sort_values('submitted_at', ascending=ascending)


def trends(df):
    dates = pd.to_datetime(df.submitted_at, utc=True).dt.tz_convert('Asia/Almaty').dt.date
    counts = dates.value_counts().sort_index()
    index = pd.date_range(counts.index.min(), counts.index.max(), freq='D').date
    return counts.reindex(index, fill_value=0).rename_axis('date').reset_index(name='count')
