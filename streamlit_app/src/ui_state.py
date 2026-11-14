"""Keep translated widget defaults aligned with stable session values.

Streamlit's browser can reinitialize a selection when its displayed options
change, even with a stable key. Explicit current defaults prevent that reset.
"""
import streamlit as st


def rebind_localized_widgets():
    """Re-serialize canonical values when translated option strings change.

    Streamlit 1.67 sends formatted option strings over the wire. At this callback
    the old deserializers still recover canonical values. Explicit assignments
    tell the next render to send the new translated values back to the browser.
    UploadedFile widgets cannot be assigned and do not have translated options.
    """
    keys = ('page', 'complaint_input', 'search', 'filter_review', 'filter_sort',
            'manage_record', 'review_record', 'edit_status', 'edit_department',
            'edit_urgency', 'edit_notes', 'review_confirmed', 'batch_column',
            'batch_size', 'batch_consent', 'filter_predicted_category',
            'filter_effective_urgency', 'filter_assigned_department', 'filter_status')
    for key in keys:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]


def selection_index(key, options, default=0):
    options = list(options)
    if key not in st.session_state:
        return default
    current = st.session_state.get(key)
    return options.index(current) if current in options else default


def selection_values(key, options):
    return [value for value in st.session_state.get(key, []) if value in options]
