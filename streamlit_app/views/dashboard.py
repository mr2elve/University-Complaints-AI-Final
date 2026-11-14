import pandas as pd
import plotly.express as px
import streamlit as st
from src.analytics import dashboard_metrics, trends
from src.translations import t, label
from src.ui import heading, empty, chart, table, COLORS


def render(db):
    heading(t('ui.a_clearer_view_of_student_concerns'), t('ui.monitor_complaints_routing_decisions_and_the_work_that_needs'))
    df = db.list()
    m = dashboard_metrics(df)
    st.markdown('<div class="hero"><h3>' + t('ui.every_student_voice_deserves_a_response') + '</h3><p>' + t('ui.understand_the_issue_connect_it_to_the_right_team') + '</p></div>', unsafe_allow_html=True)
    metrics = [('total',t('ui.registered_complaints')),('pending',t('ui.pending_complaints')),('review',t('ui.awaiting_manual_review')),('high',t('ui.high_priority_active')),
               ('auto',t('ui.automatically_routed')),('resolved',t('ui.resolved_closed')),('confidence',t('ui.average_routing_confidence'))]
    for start in (0,4):
        for col, (key,name) in zip(st.columns(4 if start == 0 else 3), metrics[start:start+4]):
            col.metric(name, f'{m[key]:.1%}' if key == 'confidence' and m['total'] else ('—' if key == 'confidence' else str(m[key])))
    st.caption(t('ui.high_priority_includes_active_complaints_with_human_assigned_high'))
    if df.empty:
        empty(t('ui.your_workspace_is_ready'), t('ui.analyze_a_kazakh_complaint_and_choose_save_to_create'))
        return
    for columns in [('predicted_category','effective_urgency'),('assigned_department','status')]:
        for col,field in zip(st.columns(2),columns):
            with col, st.container(border=True):
                names={'predicted_category':t('ui.ai_category_distribution'),'effective_urgency':t('ui.current_urgency_distribution'),'assigned_department':t('ui.assigned_departments'),'status':t('ui.complaint_status')}
                st.subheader(names[field])
                counts=df[field].fillna('Unassigned').map(label).value_counts().rename_axis('label').reset_index(name='count')
                chart(px.pie(counts,names='label',values='count',hole=.68,color_discrete_sequence=COLORS,labels={'label':names[field],'count':t('columns.count')}))
    with st.container(border=True):
        st.subheader(t('ui.complaint_activity'))
        activity=trends(df)
        activity['date']=pd.to_datetime(activity['date']).dt.strftime('%d.%m.%Y')
        fig=px.area(activity,x='date',y='count',color_discrete_sequence=COLORS,labels={'date':t('ui.date'),'count':t('ui.complaints')})
        fig.update_xaxes(type='category')
        chart(fig)
    st.subheader(t('ui.recent_complaints'))
    table(df[['id','complaint_text','predicted_category','effective_urgency','assigned_department','status','submitted_at']].head(8))
