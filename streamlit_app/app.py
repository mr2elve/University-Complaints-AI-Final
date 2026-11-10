from pathlib import Path
import streamlit as st
from src.config import ROOT
from src.database import Database
from src.translations import t

st.set_page_config(page_title='AI University Complaint Management System', page_icon='🎓', layout='wide')
st.markdown('<style>' + (ROOT / 'assets/style.css').read_text() + '</style>', unsafe_allow_html=True)
with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-icon">U</div><div><div class="brand-title">University AI</div><div class="brand-subtitle">STUDENT VOICE · AITU</div></div></div>', unsafe_allow_html=True)
    st.selectbox('Language / Тіл', ['English', 'Қазақша'], key='language')
    pages = {
        'dashboard': t('Dashboard', 'Басқару тақтасы'),
        'analyzer': t('AI Complaint Analyzer', 'Шағымды AI талдау'),
        'management': t('Complaint Management', 'Шағымдарды басқару'),
        'review': t('Manual Review Queue', 'Қолмен тексеру кезегі'),
        'batch': t('Batch Analysis', 'Топтық талдау'),
        'research': t('Model Analytics', 'Модель аналитикасы'),
        'about': t('About the Project', 'Жоба туралы'),
    }
    page = st.radio(t('WORKSPACE', 'ЖҰМЫС КЕҢІСТІГІ'), list(pages), format_func=pages.get, key='page')
    st.divider()
    st.caption(t('LOCAL INFERENCE', 'ЖЕРГІЛІКТІ ТАЛДАУ'))
    st.markdown('**KazRoBERTa** · CPU')
    st.caption(t('4 prediction heads · human oversight', '4 болжам басы · адам бақылауы'))
    st.caption(t('Academic prototype. No authentication is implemented. Keep this app on localhost.', 'Академиялық прототип. Аутентификация енгізілмеген. Қолданбаны localhost-та ұстаңыз.'))
try:
    db = Database()
except Exception as exc:
    st.error(t('Could not open the local database.', 'Жергілікті дерекқор ашылмады.'))
    st.code(str(exc))
    st.stop()
from views import dashboard, analyzer, management, review, batch, research, about
{'dashboard':dashboard, 'analyzer':analyzer, 'management':management, 'review':review, 'batch':batch, 'research':research, 'about':about}[page].render(db)
st.divider()
st.caption(t('AI University Complaint Management System · Academic demonstration · Not an official Astana IT University service.', 'AI университет шағымдарын басқару жүйесі · Академиялық демонстрация · Astana IT University ресми қызметі емес.'))
