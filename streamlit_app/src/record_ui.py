import json
import streamlit as st
from src.config import DEPARTMENTS, STATUSES
from src.translations import t, label, label_formatter
from src.ui import prediction_details, table
from src.utils import local_time


def record_editor(db, complaint_id, reviewing=False):
    row = db.get(complaint_id)
    st.subheader(t('Complaint #', 'Шағым №') + str(complaint_id))
    st.caption(local_time(row['submitted_at']) + ' · Asia/Almaty')
    with st.container(border=True):
        st.text(row['complaint_text'])
    snapshot=json.loads(row['prediction_json'])
    with st.expander(t('Original AI analysis · preserved','Бастапқы AI талдауы · сақталған'), expanded=reviewing):
        prediction_details(snapshot)
    st.caption(t('AI-suggested department: ', 'AI ұсынған бөлім: ') + label(row['predicted_department']))
    if row['reviewed_at']:
        st.success(t('Reviewed: ','Тексерілген: ') + local_time(row['reviewed_at']))
    st.markdown('**' + t('Human decision','Адамның шешімі') + '**')
    if 'edit_version' not in st.session_state:
        st.session_state['edit_version'] = row['version']
    if st.session_state['edit_version'] != row['version']:
        st.warning(t('This record changed in another session. Reload before saving.', 'Бұл жазба басқа сессияда өзгертілді. Сақтау алдында қайта жүктеңіз.'))
    st.button(t('Reload record', 'Жазбаны қайта жүктеу'), on_click=clear_editor, key='reload_record')
    with st.form(f'edit_{complaint_id}_{reviewing}'):
        cols=st.columns(3)
        status=cols[0].selectbox(t('Current status','Ағымдағы мәртебе'),STATUSES,index=STATUSES.index(row['status']),format_func=label_formatter(),key='edit_status')
        departments=[None,*DEPARTMENTS]
        default=row['assigned_department'] or (row['predicted_department'] if reviewing else None)
        department=cols[1].selectbox(t('Assigned department · human decision','Тағайындалған бөлім · адам шешімі'),departments,index=departments.index(default),format_func=label_formatter(),key='edit_department')
        urgency=cols[2].selectbox(t('Operational urgency','Операциялық шұғылдық'),['high','medium','low'],index=['high','medium','low'].index(row['effective_urgency']),format_func=label_formatter(),key='edit_urgency')
        notes=st.text_area(t('Administrator notes','Әкімші ескертпелері'),value=row['admin_notes'],max_chars=10000,key='edit_notes')
        if reviewing:
            confirmed=st.checkbox(t('I have reviewed the full complaint, considered urgency, and approve this routing decision.','Мен толық шағымды қарап, шұғылдығын бағаладым және бағыттау шешімін мақұлдаймын.'),key='review_confirmed')
            submit=st.form_submit_button(t('Approve routing & mark reviewed','Бағыттауды мақұлдау және тексерілді деп белгілеу'),type='primary')
        else:
            confirmed=False
            submit=st.form_submit_button(t('Save changes','Өзгерістерді сақтау'),type='primary')
    if submit:
        if reviewing and not confirmed:
            st.error(t('Confirm that you reviewed the complaint before approving.','Мақұлдау алдында шағымды тексергеніңізді растаңыз.'))
        else:
            try:
                db.update(complaint_id,status='Assigned' if reviewing and status in ('New','Pending Review') else status,department=department,urgency=urgency,notes=notes,expected_version=st.session_state['edit_version'],departments=DEPARTMENTS,reviewed=reviewing)
                st.session_state['record_notice']=t('Decision saved. Original AI predictions are preserved.','Шешім сақталды. Бастапқы AI болжамдары сақталған.')
                for key in ('edit_status','edit_department','edit_urgency','edit_notes','review_confirmed','edit_version'):
                    st.session_state.pop(key,None)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    with st.expander(t('Change history','Өзгерістер тарихы')):
        history=db.history(complaint_id)
        if history.empty:
            st.caption(t('No manual changes yet.','Қолмен өзгерістер әлі енгізілмеген.'))
        else:
            table(history.drop(columns=['id','complaint_id']))


def clear_editor():
    for key in ('edit_status','edit_department','edit_urgency','edit_notes','review_confirmed','edit_version'):
        st.session_state.pop(key,None)
