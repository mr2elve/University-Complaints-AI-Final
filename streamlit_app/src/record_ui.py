import json
import streamlit as st
from src.config import DEPARTMENTS, STATUSES
from src.ui_state import selection_index
from src.translations import t, label, label_formatter, display_time, error_text
from src.ui import prediction_details, table


def record_editor(db, complaint_id, reviewing=False):
    row = db.get(complaint_id)
    st.subheader(t('ui.complaint') + str(complaint_id))
    st.caption(display_time(row['submitted_at']) + ' · ' + t('ui.almaty'))
    with st.container(border=True):
        st.text(row['complaint_text'])
    snapshot=json.loads(row['prediction_json'])
    with st.expander(t('ui.original_ai_analysis_preserved'), expanded=reviewing):
        prediction_details(snapshot)
    st.caption(t('ui.ai_suggested_department') + label(row['predicted_department']))
    if row['reviewed_at']:
        st.success(t('ui.reviewed') + display_time(row['reviewed_at']))
    st.markdown('**' + t('ui.human_decision') + '**')
    if 'edit_version' not in st.session_state:
        # Explicit values also reset the browser controls when switching records
        # or between management/review; these editors now share persistent keys.
        st.session_state.update(
            edit_version=row['version'], edit_status=row['status'],
            edit_department=row['assigned_department'] or (row['predicted_department'] if reviewing else None),
            edit_urgency=row['effective_urgency'], edit_notes=row['admin_notes'],
            review_confirmed=False,
        )
    if st.session_state['edit_version'] != row['version']:
        st.warning(t('ui.this_record_changed_in_another_session_reload_before_saving'))
    st.button(t('ui.reload_record'), on_click=clear_editor, key='reload_record')
    with st.container(border=True, key=f'edit_{complaint_id}_{reviewing}'):
        cols=st.columns(3)
        status=cols[0].selectbox(t('ui.current_status'),STATUSES,index=selection_index('edit_status', STATUSES, STATUSES.index(row['status'])),format_func=label_formatter(),key='edit_status',persist_state='session')
        departments=[None,*DEPARTMENTS]
        default=row['assigned_department'] or (row['predicted_department'] if reviewing else None)
        department=cols[1].selectbox(t('ui.assigned_department_human_decision'),departments,index=selection_index('edit_department', departments, departments.index(default)),format_func=label_formatter(),key='edit_department',persist_state='session')
        urgency=cols[2].selectbox(t('ui.operational_urgency'),['high','medium','low'],index=selection_index('edit_urgency', ['high','medium','low'], ['high','medium','low'].index(row['effective_urgency'])),format_func=label_formatter(),key='edit_urgency',persist_state='session')
        notes=st.text_area(t('ui.administrator_notes'),value=row['admin_notes'],max_chars=10000,key='edit_notes',persist_state='session')
        if reviewing:
            confirmed=st.checkbox(t('ui.i_have_reviewed_the_full_complaint_considered_urgency_and'),key='review_confirmed',persist_state='session')
            submit=st.button(t('ui.approve_routing_mark_reviewed'),key='approve_review',type='primary')
        else:
            confirmed=False
            submit=st.button(t('ui.save_changes'),key='save_changes',type='primary')
    if submit:
        if reviewing and not confirmed:
            st.error(t('ui.confirm_that_you_reviewed_the_complaint_before_approving'))
        else:
            try:
                db.update(complaint_id,status='Assigned' if reviewing and status in ('New','Pending Review') else status,department=department,urgency=urgency,notes=notes,expected_version=st.session_state['edit_version'],departments=DEPARTMENTS,reviewed=reviewing)
                st.session_state['record_notice']='ui.decision_saved_original_ai_predictions_are_preserved'
                for key in ('edit_status','edit_department','edit_urgency','edit_notes','review_confirmed','edit_version'):
                    st.session_state.pop(key,None)
                st.rerun()
            except ValueError as exc:
                st.error(error_text(exc))
    with st.expander(t('ui.change_history')):
        history=db.history(complaint_id)
        if history.empty:
            st.caption(t('ui.no_manual_changes_yet'))
        else:
            table(history.drop(columns=['id','complaint_id']))


def clear_editor():
    for key in ('edit_status','edit_department','edit_urgency','edit_notes','review_confirmed','edit_version'):
        st.session_state.pop(key,None)
