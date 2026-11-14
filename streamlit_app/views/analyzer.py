import uuid
import streamlit as st
from src.inference import analyze_complaint
from src.translations import t, error_text
from src.ui import heading, get_model, prediction_details

SAMPLES = ['schedule', 'dormitory', 'tuition', 'security', 'administration']


def set_sample(text):
    st.session_state['complaint_input'] = text


def render(db):
    heading(t('ui.from_complaint_to_clarity'),t('ui.four_predictions_one_local_model_a_human_in_control'))
    st.caption(t('ui.try_an_illustrative_kazakh_complaint'))
    for col, sample in zip(st.columns(5), SAMPLES):
        col.button(t(f'sample.{sample}.title'), key=f'sample_{sample}', on_click=set_sample, args=(t(f'sample.{sample}.text'),), width='stretch')
    with st.container(border=True, key='analyze_form'):
        text=st.text_area(t('ui.complaint_kazakh_russian_english_or_mixed'),key='complaint_input',height=180,max_chars=10000,placeholder=t('ui.complaint_placeholder'),persist_state='session')
        st.caption(t('ui.text_stays_in_this_local_app_analysis_is_not'))
        analyze=st.button(t('ui.analyze_complaint'),key='analyze_complaint',type='primary',width='stretch')
    if analyze:
        st.session_state.pop('analysis',None)
        st.session_state.pop('analysis_error',None)
        try:
            from src.utils import validate_text
            validate_text(text)
            bundle=get_model()
            if bundle:
                with st.spinner(t('ui.analyzing_with_your_trained_checkpoint')):
                    st.session_state['analysis']=analyze_complaint(bundle,text)
                    st.session_state['analysis_key']=str(uuid.uuid4())
        except (ValueError, RuntimeError) as exc:
            st.session_state['analysis_error'] = (text, str(exc))
    if st.session_state.get('analysis_error', (None,))[0] == text:
        st.error(error_text(st.session_state['analysis_error'][1]))
    result=st.session_state.get('analysis')
    if result:
        st.subheader(t('ui.analysis_results'))
        if result['text'] != text:
            st.warning(t('ui.these_results_belong_to_the_previously_analyzed_text_below'))
        with st.expander(t('ui.analyzed_text')):
            st.text(result['text'])
        prediction_details(result)
        saved=st.session_state.get('saved_analysis_key') == st.session_state['analysis_key']
        if st.button(t('ui.save_complaint'),key='save_complaint',icon=':material/save:',type='primary',disabled=saved):
            ident=db.save(result,st.session_state['analysis_key'])
            st.session_state['saved_analysis_key']=st.session_state['analysis_key']
            st.session_state['saved_complaint_id']=ident
            st.rerun()
        if saved:
            st.success(t('ui.saved_complaint') + str(st.session_state['saved_complaint_id']))
