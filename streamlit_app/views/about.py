import streamlit as st
from src.translations import t
from src.ui import heading


def render(db):
    heading(t('ui.ai_university_complaint_management_system'),t('ui.master_s_final_project_ai_essentials_astana_it_university'))
    st.markdown('<div class="hero"><h3>'+t('ui.multilingual_nlp_with_human_responsibility')+'</h3><p>'+t('ui.a_research_demonstration_of_intelligent_complaint_analysis_and_confidence')+'</p></div>',unsafe_allow_html=True)
    st.warning(t('ui.this_is_an_academic_prototype_not_an_official_astana'))
    st.info(t('ui.current_model_xlm_roberta_trained_on_kazakh_russian_and'))
    sections=['background', 'objectives', 'methodology', 'results', 'routing', 'limitations', 'future']
    for section in sections:
        with st.container(border=True):
            st.subheader(t(f'about.{section}.title'));st.write(t(f'about.{section}.body'))
