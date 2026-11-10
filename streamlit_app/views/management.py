import streamlit as st
from src.analytics import filter_complaints
from src.record_ui import record_editor, clear_editor
from src.translations import t, label, label_formatter
from src.ui import heading, empty, table
from src.utils import csv_bytes


def render(db):
    heading(t('Complaint management','Шағымдарды басқару'),t('Track every case from submission to resolution. Human decisions remain separate from AI predictions.','Әр істі тіркелгеннен шешілгенге дейін бақылаңыз. Адам шешімдері AI болжамдарынан бөлек сақталады.'))
    if notice:=st.session_state.pop('record_notice',None):st.success(notice)
    df=db.list()
    if df.empty:
        empty(t('No complaints yet','Шағымдар әлі жоқ'),t('Save an analysis to begin managing complaints.','Шағымдарды басқаруды бастау үшін талдауды сақтаңыз.'))
        return
    search=st.text_input(t('Search complaint text or ID','Шағым мәтіні немесе ID бойынша іздеу'),key='search')
    with st.expander(t('Filters & sorting','Сүзгілер және сұрыптау'),expanded=True):
        filters={}
        fields=[('predicted_category',t('AI category','AI санаты')),('effective_urgency',t('Current urgency','Ағымдағы шұғылдық')),('assigned_department',t('Assigned department','Тағайындалған бөлім')),('status',t('Status','Мәртебе'))]
        for col,(field,name) in zip(st.columns(4),fields):
            options=sorted(df[field].dropna().unique().tolist())
            if field=='assigned_department':
                options=['Unassigned',*options]
            filters[field]=col.multiselect(name,options,format_func=label_formatter())
        a,b=st.columns(2)
        review=a.selectbox(t('Review requirement','Тексеру қажеттілігі'),['all','awaiting','reviewed','auto'],format_func={'all':t('All','Барлығы'),'awaiting':t('Awaiting review','Тексеруді күтуде'),'reviewed':t('Reviewed','Тексерілген'),'auto':t('Automatically routed','Автоматты бағытталған')}.get)
        ascending=b.selectbox(t('Submission date','Тіркелген күні'),[False,True],format_func={True:t('Oldest first','Ескісі алдымен'),False:t('Newest first','Жаңасы алдымен')}.get)
    df['assigned_department']=df.assigned_department.fillna('Unassigned')
    filtered=filter_complaints(df,search,filters,review,ascending)
    st.caption(t(f'{len(filtered)} matching complaints',f'{len(filtered)} сәйкес шағым'))
    table(filtered[['id','complaint_text','predicted_category','predicted_urgency','effective_urgency','predicted_department','assigned_department','status','submitted_at']])
    st.download_button(t('Export filtered records · CSV','Сүзілген жазбаларды экспорттау · CSV'),csv_bytes(filtered.drop(columns=['save_key'])),file_name='complaints.csv',mime='text/csv')
    if not filtered.empty:
        ident=st.selectbox(t('Open complaint','Шағымды ашу'),filtered.id.tolist(),format_func=lambda v:f'#{v}',key='manage_record',on_change=clear_editor)
        if st.session_state.get('active_record') != ('manage',ident):
            clear_editor(); st.session_state['active_record']=('manage',ident)
        record_editor(db,ident)
