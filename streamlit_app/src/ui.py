from html import escape
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import MODEL_DIR, ROOT, TARGETS
from src.translations import t, label, column_labels, display_frame, error_text

COLORS = ['#285AE8', '#14A5A0', '#8B6BD6', '#F0A44B', '#E16A81', '#617A9D']


@st.cache_resource(show_spinner=False)
def cached_model(path):
    from src.model_loader import load_model
    return load_model(path)


def get_model():
    try:
        with st.spinner(t('ui.loading_local_xlm_roberta_on_cpu')):
            return cached_model(str(MODEL_DIR))
    except Exception as exc:
        st.error(t('ui.the_trained_model_could_not_be_loaded_no_prediction'))
        st.error(error_text(exc))
        st.info(t('ui.check_model_files_and_run_the_setup_command_in'))
        return None


def heading(title, subtitle):
    st.markdown('<div class="eyebrow">' + t('ui.eyebrow') + '</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(subtitle)


def empty(title, description):
    st.markdown(f'<div class="empty"><h3>{escape(title)}</h3><p>{escape(description)}</p></div>', unsafe_allow_html=True)


def chart(fig, *, height=320):
    fig.update_layout(font=dict(family='Arial, sans-serif', color='#42536e'), paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=12,r=12,t=25,b=15),
                      legend_title_text='', colorway=COLORS, height=height)
    fig.update_xaxes(gridcolor='#edf0f6')
    fig.update_yaxes(gridcolor='#edf0f6')
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})


def prediction_cards(result):
    for col, task, color in zip(st.columns(4), TARGETS, COLORS):
        value = result['predictions'][task]
        with col:
            st.markdown(f'<div class="result-card" style="border-top-color:{color}"><div class="label">{escape(label(task))}</div><div class="value">{escape(label(value))}</div><div class="taxonomy">{escape(t("ui.ai_prediction"))}</div></div>', unsafe_allow_html=True)


def prediction_details(result):
    prediction_cards(result)
    a,b,c = st.columns(3)
    a.metric(t('ui.routing_confidence'), f"{result['routing_confidence']:.1%}")
    b.metric(t('ui.high_urgency_probability'), f"{result['high_urgency_probability']:.1%}")
    c.metric(t('ui.suggested_sla_example_only'), t('ui.hours', hours=result['suggested_sla_hours']))
    reasons = ' · '.join(label(r) for r in result['review_reasons'])
    if result['requires_review']:
        st.warning(t('ui.manual_review') + ' — ' + reasons)
    else:
        st.success(t('ui.auto_routed_eligible_after_saving') + ' — ' + reasons)
    st.caption(t('ui.operational_review_priority') + label('priority_' + result['operational_priority']))
    st.caption(t('ui.sla_values_4_24_72_hours_are_research_examples'))
    st.info(t('ui.raw_softmax_scores_are_uncalibrated_they_do_not_guarantee'))
    if result.get('truncated'):
        limit = result.get('max_length')
        st.warning(t('ui.truncated', limit=limit or t('ui.not_recorded')))
    with st.expander(t('ui.full_probability_distributions')):
        for col, task in zip(st.columns(2) * 2, TARGETS):
            with col:
                st.markdown('**' + label(task) + '**')
                df = pd.DataFrame({'label': [label(value) for value in result['probabilities'][task]], 'probability': list(result['probabilities'][task].values())})
                fig = px.bar(df.sort_values('probability'), x='probability', y='label', orientation='h', color_discrete_sequence=[COLORS[TARGETS.index(task)]], labels={'probability':t('ui.probability'),'label':''})
                fig.update_xaxes(range=[0,1], tickformat='.0%')
                chart(fig)


def table(frame, *, user_data=False):
    display = frame.copy() if user_data else display_frame(frame)
    st.dataframe(display, hide_index=True, width='stretch')
