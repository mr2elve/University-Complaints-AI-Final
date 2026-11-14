import streamlit as st
from src.analytics import filter_complaints
from src.ui_state import selection_index, selection_values
from src.record_ui import record_editor, clear_editor
from src.translations import t, label, label_formatter
from src.ui import heading, empty, table
from src.utils import csv_bytes


def render(db):
    heading(t('ui.complaint_management_97'),t('ui.track_every_case_from_submission_to_resolution_human_decisions'))
    if notice:=st.session_state.get('record_notice'):st.success(t(notice))
    df=db.list()
    if df.empty:
        empty(t('ui.no_complaints_yet'),t('ui.save_an_analysis_to_begin_managing_complaints'))
        return
    search=st.text_input(t('ui.search_complaint_text_or_id'),key='search',persist_state='session')
    with st.expander(t('ui.filters_sorting'),expanded=True):
        filters={}
        fields=[('predicted_category',t('ui.ai_category')),('effective_urgency',t('ui.current_urgency')),('assigned_department',t('ui.assigned_department')),('status',t('ui.status'))]
        for col,(field,name) in zip(st.columns(4),fields):
            options=sorted(df[field].dropna().unique().tolist())
            if field=='assigned_department':
                options=['Unassigned',*options]
            filters[field]=col.multiselect(name,options,default=selection_values(f'filter_{field}',options),format_func=label_formatter(),key=f'filter_{field}',placeholder=t('ui.select_options'),persist_state='session')
        a,b=st.columns(2)
        review=a.selectbox(t('ui.review_requirement'),['all','awaiting','reviewed','auto'],key='filter_review',index=selection_index('filter_review',['all','awaiting','reviewed','auto']),format_func={'all':t('ui.all'),'awaiting':t('ui.awaiting_review'),'reviewed':t('ui.reviewed_113'),'auto':t('ui.automatically_routed')}.get,persist_state='session')
        ascending=b.selectbox(t('ui.submission_date'),[False,True],key='filter_sort',index=selection_index('filter_sort',[False,True]),format_func={True:t('ui.oldest_first'),False:t('ui.newest_first')}.get,persist_state='session')
    df['assigned_department']=df.assigned_department.fillna('Unassigned')
    filtered=filter_complaints(df,search,filters,review,ascending)
    st.caption(t('ui.matching_complaints',count=len(filtered)))
    table(filtered[['id','complaint_text','predicted_category','predicted_urgency','effective_urgency','predicted_department','assigned_department','status','submitted_at']])
    st.caption(t('ui.export_identifiers'))
    st.download_button(t('ui.export_filtered_records_csv'),csv_bytes(filtered.drop(columns=['save_key'])),file_name='complaints.csv',mime='text/csv')
    if not filtered.empty:
        ident=st.selectbox(t('ui.open_complaint'),filtered.id.tolist(),index=selection_index('manage_record',filtered.id.tolist()),format_func=lambda v:f'#{v}',key='manage_record',on_change=clear_editor,persist_state='session')
        if st.session_state.get('active_record') != ('manage',ident):
            clear_editor(); st.session_state['active_record']=('manage',ident)
        record_editor(db,ident)
