import json
import streamlit as st
from src.record_ui import record_editor, clear_editor
from src.translations import t, label
from src.ui_state import selection_index
from src.ui import heading, empty, table


def render(db):
    heading(t('ui.human_judgment_comes_first'),t('ui.review_uncertain_predictions_and_potentially_urgent_complaints_before_assigning'))
    st.info(t('ui.decision_support_prototype_this_queue_does_not_monitor_or'))
    if notice:=st.session_state.get('record_notice'):st.success(t(notice))
    df=db.list()
    queue=df[(df.requires_review==1) & df.reviewed_at.isna()].copy()
    if queue.empty:
        empty(t('ui.no_complaints_awaiting_review'),t('ui.uncertain_or_potentially_urgent_saved_analyses_will_appear_here'))
        return
    queue['priority']=((queue.high_urgency_probability>=.30)|(queue.effective_urgency=='high')).astype(int)
    queue=queue.sort_values(['priority','submitted_at'],ascending=[False,True])
    queue['review_reasons']=queue.prediction_json.map(lambda s:' · '.join(label(r) for r in json.loads(s)['review_reasons']))
    st.metric(t('ui.awaiting_your_decision'),len(queue))
    table(queue[['id','complaint_text','predicted_category','predicted_urgency','predicted_department','routing_confidence','review_reasons','submitted_at']])
    ident=st.selectbox(t('ui.review_complaint'),queue.id.tolist(),index=selection_index('review_record',queue.id.tolist()),format_func=lambda v:f'#{v}',key='review_record',on_change=clear_editor,persist_state='session')
    if st.session_state.get('active_record') != ('review',ident):
        clear_editor(); st.session_state['active_record']=('review',ident)
    record_editor(db,ident,reviewing=True)
