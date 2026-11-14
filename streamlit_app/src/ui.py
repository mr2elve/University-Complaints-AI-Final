from html import escape
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import MODEL_DIR, ROOT, TARGETS
from src.translations import t, label, column_labels
from src.utils import local_time

COLORS = ['#285AE8', '#14A5A0', '#8B6BD6', '#F0A44B', '#E16A81', '#617A9D']


@st.cache_resource(show_spinner=False)
def cached_model(path):
    from src.model_loader import load_model
    return load_model(path)


def get_model():
    try:
        with st.spinner(t('Loading local XLM-RoBERTa on CPU…', 'XLM-RoBERTa моделі CPU-ға жүктелуде…')):
            return cached_model(str(MODEL_DIR))
    except Exception as exc:
        st.error(t('The trained model could not be loaded. No prediction was made.', 'Үйретілген модель жүктелмеді. Болжам жасалмады.'))
        st.code(str(exc), language=None)
        st.info(t('Check model files and run the setup command in README.md.', 'Модель файлдарын тексеріп, README.md ішіндегі орнату пәрменін орындаңыз.'))
        return None


def heading(title, subtitle):
    st.markdown('<div class="eyebrow">AITU · AI ESSENTIALS</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(subtitle)


def empty(title, description):
    st.markdown(f'<div class="empty"><h3>{escape(title)}</h3><p>{escape(description)}</p></div>', unsafe_allow_html=True)


def chart(fig):
    fig.update_layout(font=dict(family='Arial, sans-serif', color='#42536e'), paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=12,r=12,t=25,b=15),
                      legend_title_text='', colorway=COLORS, height=320)
    fig.update_xaxes(gridcolor='#edf0f6')
    fig.update_yaxes(gridcolor='#edf0f6')
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})


def prediction_cards(result):
    for col, task, color in zip(st.columns(4), TARGETS, COLORS):
        value = result['predictions'][task]
        with col:
            st.markdown(f'<div class="result-card" style="border-top-color:{color}"><div class="label">{escape(label(task))}</div><div class="value">{escape(label(value))}</div><div class="taxonomy">{escape(value)}</div></div>', unsafe_allow_html=True)


def prediction_details(result):
    prediction_cards(result)
    a,b,c = st.columns(3)
    a.metric(t('Routing confidence', 'Бағыттау сенімділігі'), f"{result['routing_confidence']:.1%}")
    b.metric(t('High urgency probability', 'Жоғары шұғылдық ықтималдығы'), f"{result['high_urgency_probability']:.1%}")
    c.metric(t('Suggested SLA · example only', 'Ұсынылған SLA · тек мысал'), t(f"{result['suggested_sla_hours']} hours", f"{result['suggested_sla_hours']} сағат"))
    reasons = ' · '.join(label(r) for r in result['review_reasons'])
    if result['requires_review']:
        st.warning(t('Manual Review', 'Қолмен тексеру') + ' — ' + reasons)
    else:
        st.success(t('Auto-Routed · eligible after saving', 'Автоматты бағыттау · сақтағаннан кейін') + ' — ' + reasons)
    st.caption(t('Operational review priority: ', 'Тексерудің операциялық басымдығы: ') + label(result['operational_priority']))
    st.caption(t('SLA values (4 / 24 / 72 hours) are research examples based on predicted urgency, not university policy. Potentially urgent cases need prompt human assessment.', 'SLA мәндері (4 / 24 / 72 сағат) болжамды шұғылдыққа негізделген зерттеу мысалдары, университет саясаты емес. Шұғыл болуы мүмкін жағдайларды адам жедел бағалауы тиіс.'))
    st.info(t('Raw softmax scores are uncalibrated. They do not guarantee that a prediction is correct.', 'Softmax бағалары калибрленбеген. Олар болжамның дұрыстығына кепілдік бермейді.'))
    if result.get('truncated'):
        limit = result.get('max_length')
        st.warning(t(f'This text was truncated to the model token limit ({limit if limit else "not recorded"}). The complete original text is retained when saved.', f'Мәтін модельдің токен шегіне дейін қысқартылды ({limit if limit else "жазылмаған"}). Сақтағанда бастапқы мәтін толық сақталады.'))
    with st.expander(t('Full probability distributions', 'Толық ықтималдық үлестірімдері')):
        for col, task in zip(st.columns(2) * 2, TARGETS):
            with col:
                st.markdown('**' + label(task) + '**')
                df = pd.DataFrame({'label': list(result['probabilities'][task]), 'probability': list(result['probabilities'][task].values())})
                fig = px.bar(df.sort_values('probability'), x='probability', y='label', orientation='h', color_discrete_sequence=[COLORS[TARGETS.index(task)]], labels={'probability':t('Probability','Ықтималдық'),'label':''})
                fig.update_xaxes(range=[0,1], tickformat='.0%')
                chart(fig)


def table(frame):
    display = frame.copy()
    for col in ('submitted_at', 'resolved_at', 'reviewed_at', 'timestamp'):
        if col in display:
            display[col] = display[col].map(local_time)
    st.dataframe(display, hide_index=True, width='stretch', column_config=column_labels(display.columns))
