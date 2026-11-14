from pathlib import Path
import streamlit as st
from src.config import ROOT
from src.database import Database
from src.translations import t, error_text
from src.native_locale import install_native_locale
from src.ui_state import selection_index, rebind_localized_widgets

st.set_page_config(page_title=t('ui.ai_university_complaint_management_system'), page_icon='🎓', layout='wide')
st.markdown('<style>' + (ROOT / 'assets/style.css').read_text() + '</style>', unsafe_allow_html=True)
with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-icon">U</div><div><div class="brand-title">' + t('ui.brand_title') + '</div><div class="brand-subtitle">' + t('ui.brand_subtitle') + '</div></div></div>', unsafe_allow_html=True)
    st.selectbox(t('ui.language'), ['English', 'Қазақша', 'Русский'], key='language',
                 on_change=rebind_localized_widgets,persist_state='session')
    pages = {
        'dashboard': t('ui.dashboard'),
        'analyzer': t('ui.ai_complaint_analyzer'),
        'management': t('ui.complaint_management'),
        'review': t('ui.manual_review_queue'),
        'batch': t('ui.batch_analysis'),
        'research': t('ui.model_analytics'),
        'about': t('ui.about_the_project'),
    }
    page = st.radio(t('ui.workspace'), list(pages), index=selection_index('page', list(pages)), format_func=pages.get, key='page',persist_state='session')
    st.divider()
    st.caption(t('ui.local_inference'))
    st.markdown('**XLM-RoBERTa** · CPU')
    st.caption(t('ui.4_prediction_heads_human_oversight'))
    st.caption(t('ui.academic_prototype_no_authentication_is_implemented_keep_this_app'))
install_native_locale()
try:
    db = Database()
except Exception as exc:
    st.error(t('ui.could_not_open_the_local_database'))
    st.error(error_text(exc))
    st.stop()
from views import dashboard, analyzer, management, review, batch, research, about
try:
    {'dashboard':dashboard, 'analyzer':analyzer, 'management':management, 'review':review, 'batch':batch, 'research':research, 'about':about}[page].render(db)
except Exception as exc:
    st.error(error_text(exc))
st.divider()
st.caption(t('ui.ai_university_complaint_management_system_academic_demonstration_not_an'))
