import json
import streamlit as st
from src.record_ui import record_editor, clear_editor
from src.translations import t, label
from src.ui import heading, empty, table


def render(db):
    heading(t('Human judgment comes first','Адамның пайымы бірінші орында'),t('Review uncertain predictions and potentially urgent complaints before assigning responsibility.','Жауапты бөлімді тағайындамас бұрын сенімсіз болжамдар мен шұғыл болуы мүмкін шағымдарды тексеріңіз.'))
    st.info(t('Decision-support prototype. This queue does not monitor or resolve critical safety incidents. The 0.75 / 0.30 thresholds are research settings, not validated university safety policy.','Шешім қабылдауды қолдайтын прототип. Бұл кезек аса қауіпті оқиғаларды бақыламайды және шешпейді. 0.75 / 0.30 шектері — расталған университет қауіпсіздік саясаты емес, зерттеу баптаулары.'))
    if notice:=st.session_state.pop('record_notice',None):st.success(notice)
    df=db.list()
    queue=df[(df.requires_review==1) & df.reviewed_at.isna()].copy()
    if queue.empty:
        empty(t('No complaints awaiting review','Тексеруді күтетін шағымдар жоқ'),t('Uncertain or potentially urgent saved analyses will appear here.','Сенімсіз немесе шұғыл болуы мүмкін сақталған талдаулар осында көрсетіледі.'))
        return
    queue['priority']=((queue.high_urgency_probability>=.30)|(queue.effective_urgency=='high')).astype(int)
    queue=queue.sort_values(['priority','submitted_at'],ascending=[False,True])
    queue['review_reasons']=queue.prediction_json.map(lambda s:' · '.join(label(r) for r in json.loads(s)['review_reasons']))
    st.metric(t('Awaiting your decision','Шешіміңізді күтуде'),len(queue))
    table(queue[['id','complaint_text','predicted_category','predicted_urgency','predicted_department','routing_confidence','review_reasons','submitted_at']])
    ident=st.selectbox(t('Review complaint','Шағымды тексеру'),queue.id.tolist(),format_func=lambda v:f'#{v}',key='review_record',on_change=clear_editor)
    if st.session_state.get('active_record') != ('review',ident):
        clear_editor(); st.session_state['active_record']=('review',ident)
    record_editor(db,ident,reviewing=True)
