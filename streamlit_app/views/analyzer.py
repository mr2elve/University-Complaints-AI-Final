import uuid
import streamlit as st
from src.inference import analyze_complaint
from src.translations import t
from src.ui import heading, get_model, prediction_details

SAMPLES = [
    ('Exam schedule','Емтихан кестесі','Емтихан кестесінде екі пән бір уақытта қойылған. Бұл мәселені тез арада шешуді сұраймын.'),
    ('Dormitory','Жатақхана','Жатақханада бірнеше күннен бері ыстық су жоқ. Студенттер қатты қиналып жатыр.'),
    ('Tuition payment','Оқу ақысы','Оқу ақысын төледім, бірақ жүйеде төлем көрсетілмейді. Осы мәселені шешуге көмектесіңіздер.'),
    ('Campus security','Кампус қауіпсіздігі','Кешкі уақытта жатақхана маңында жарық жоқ, бөгде адамдар студенттерге тиісіп жүр. Қауіпсіздікті қамтамасыз етуді сұраймын.'),
    ('Administration','Әкімшілік','Транскрипт алу үшін өтініш бердім, бірақ құжат әлі дайын емес. Деканаттан жауап күтіп жүрмін.'),
]


def set_sample(text):
    st.session_state['complaint_input'] = text


def render(db):
    heading(t('From complaint to clarity','Шағымнан нақты шешімге'),t('Four predictions. One local model. A human in control.','Төрт болжам. Бір жергілікті модель. Адам бақылауы.'))
    st.caption(t('Try an illustrative Kazakh complaint','Қазақша мысал шағымды қолданып көріңіз'))
    for col,(en,kk,text) in zip(st.columns(5), SAMPLES):
        col.button(t(en,kk), on_click=set_sample,args=(text,),width='stretch')
    with st.form('analyze_form'):
        text=st.text_area(t('Complaint in Kazakh','Қазақша шағым'),key='complaint_input',height=180,max_chars=10000,placeholder='Мәселеңізді осында жазыңыз…')
        st.caption(t('Text stays in this local app. Analysis is not saved until you choose Save. Only the first 96 model tokens are analyzed.','Мәтін осы жергілікті қолданбада қалады. «Сақтау» таңдағанға дейін талдау дерекқорға жазылмайды. Алғашқы 96 модель токені ғана талданады.'))
        analyze=st.form_submit_button(t('Analyze Complaint','Шағымды талдау'),type='primary',width='stretch')
    if analyze:
        st.session_state.pop('analysis',None)
        try:
            from src.utils import validate_text
            validate_text(text)
            bundle=get_model()
            if bundle:
                with st.spinner(t('Analyzing with your trained checkpoint…','Үйретілген модель арқылы талдануда…')):
                    st.session_state['analysis']=analyze_complaint(bundle,text)
                    st.session_state['analysis_key']=str(uuid.uuid4())
        except (ValueError, RuntimeError) as exc:
            st.error(str(exc))
    result=st.session_state.get('analysis')
    if result:
        st.subheader(t('Analysis results','Талдау нәтижелері'))
        if result['text'] != text:
            st.warning(t('These results belong to the previously analyzed text below. Analyze again to use your edits.','Бұл нәтижелер төмендегі бұрын талданған мәтінге қатысты. Өзгерістерді қолдану үшін қайта талдаңыз.'))
        with st.expander(t('Analyzed text','Талданған мәтін')):
            st.text(result['text'])
        prediction_details(result)
        saved=st.session_state.get('saved_analysis_key') == st.session_state['analysis_key']
        if st.button(t('Save complaint','Шағымды сақтау'),icon=':material/save:',type='primary',disabled=saved):
            ident=db.save(result,st.session_state['analysis_key'])
            st.session_state['saved_analysis_key']=st.session_state['analysis_key']
            st.session_state['saved_complaint_id']=ident
            st.rerun()
        if saved:
            st.success(t('Saved complaint #','Сақталған шағым №') + str(st.session_state['saved_complaint_id']))
