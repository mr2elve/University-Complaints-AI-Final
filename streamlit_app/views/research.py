import json
import textwrap
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import ROOT, TARGETS
from src.translations import t, label, column_labels, display_frame
from src.ui import heading, chart, table, COLORS
from src.utils import csv_bytes


def render(db):
    heading(t('ui.evidence_behind_the_model'),t('ui.published_multilingual_evaluation_and_original_research_four_classification_tasks'))
    st.subheader(t('ui.deployed_multilingual_xlm_roberta'))
    multilingual = pd.read_csv(ROOT/'data/research/xlmr_metrics_by_language.csv')
    table(multilingual)
    st.caption(t('ui.published_export_results_150_held_out_complaints_per_language'))
    st.subheader(t('ui.original_kazakh_only_research_comparison'))
    st.caption(t('ui.the_historical_results_below_use_a_different_experiment_and'))
    df=pd.read_csv(ROOT/'data/research/test_comparison.csv')
    a,b,c=st.columns(3)
    a.metric(t('ui.best_overall_linear_svm'),'0.9731')
    b.metric(t('ui.best_category_kazroberta'),'0.9933')
    c.metric(t('ui.best_urgency_bilstm'),'0.9790')
    st.caption(t('ui.values_are_macro_f1_svm_and_bilstm_both_achieved'))
    st.subheader(t('ui.architecture_comparison'))
    display=df[['Model',*TARGETS,'mean_macro_f1']].sort_values('mean_macro_f1',ascending=False)
    st.dataframe(display_frame(display).style.format({column_labels([c])[c]:'{:.4f}' for c in [*TARGETS,'mean_macro_f1']}),hide_index=True,width='stretch')
    long=df.melt(id_vars='Model',value_vars=list(TARGETS),var_name='task',value_name='Macro-F1')
    long['task']=long.task.map(label)
    fig=px.bar(long,x='Model',y='Macro-F1',color='task',barmode='group',color_discrete_sequence=COLORS,labels=column_labels(long.columns))
    fig.update_yaxes(range=[0,1.05]);chart(fig)
    with st.container(border=True):
        st.subheader(t('ui.mean_macro_f1_ranking'))
        fig=px.bar(df.sort_values('mean_macro_f1'),y='Model',x='mean_macro_f1',orientation='h',text='mean_macro_f1',color='Model',color_discrete_sequence=COLORS,labels=column_labels(df.columns))
        fig.update_xaxes(range=[0,1]);fig.update_layout(showlegend=False);chart(fig)
    st.info(t('ui.the_application_now_uses_the_multilingual_xlm_roberta_checkpoint'))
    models=[('Linear SVM',t('ui.character_tf_idf_char_wb_2_5_grams_with')),
            ('BiLSTM + Attention',t('ui.shared_bidirectional_lstm_learned_attention_pooling_and_four_linear')),
            ('XLM-RoBERTa',t('ui.multilingual_pretrained_encoder_masked_mean_pooling_dropout_0_2')),
            ('KazRoBERTa',t('ui.kazakh_conversational_roberta_6_encoder_layers_hidden_size_768'))]
    with st.expander(t('ui.how_the_architectures_work')):
        for name,description in models:
            st.markdown(f'**{name}**');st.write(description)
    st.subheader(t('ui.urgency_deserves_special_attention'))
    misses=df[['Model','missed_high','total_high']].copy()
    misses['missed']=misses.missed_high.astype(str)+' / '+misses.total_high.astype(str)
    fig=px.bar(misses,x='Model',y='missed_high',text='missed',color_discrete_sequence=['#E16A81'],labels={**column_labels(misses.columns),'missed_high':t('ui.high_urgency_complaints_missed')});chart(fig)
    st.warning(t('ui.kazroberta_missed_5_of_38_high_urgency_test_cases'))
    st.subheader(t('ui.routing_trade_off_validation_only'))
    routing=pd.read_csv(ROOT/'data/research/routing_validation.csv')
    table(routing)
    routing_plot=routing.melt(id_vars='threshold',value_vars=['coverage','routing_accuracy','manual_review'],var_name='metric',value_name='value')
    routing_plot['metric']=routing_plot.metric.map(column_labels(routing.columns))
    chart(px.line(routing_plot,x='threshold',y='value',color='metric',markers=True,color_discrete_sequence=COLORS,labels={**column_labels(routing_plot.columns),'value':t('ui.share_accuracy'),'threshold':t('ui.confidence_threshold')}))
    st.caption(t('ui.routing_accuracy_measures_department_correctness_only_among_automatically_routed'))
    with st.expander(t('ui.original_svm_test_confusion_matrices')):
        matrices=json.loads((ROOT/'data/research/svm_confusion_matrices.json').read_text())
        for col, (task, matrix) in zip(st.columns(2) * 2, matrices.items()):
            with col:
                st.markdown('**' + t('ui.svm_matrix',task=label(task)) + '**')
                xnames=['<br>'.join(textwrap.wrap(label(name), 18, break_long_words=False)) for name in matrix['labels']]
                ynames=['<br>'.join(textwrap.wrap(label(name), 12, break_long_words=False)) for name in matrix['labels']]
                fig=px.imshow(np.array(matrix['counts']),x=xnames,y=ynames,text_auto=True,aspect='auto',
                              color_continuous_scale='Blues',labels={'x':t('ui.predicted_label'),
                              'y':t('ui.true_label'),'color':t('columns.count')})
                fig.update_layout(coloraxis_showscale=False)
                # Use the available height and narrow, vertical labels so long
                # translated departments remain legible on a mobile viewport.
                fig.update_xaxes(tickangle=-90, tickfont_size=9)
                fig.update_yaxes(tickfont_size=10)
                chart(fig,height=480)
        st.caption(t('ui.matrix_provenance'))
        image=ROOT/'assets/svm_test_confusion_matrices.png'
        if image.exists():
            st.download_button(t('ui.download_original_matrices'),image.read_bytes(),
                               file_name='svm_test_confusion_matrices.png',mime='image/png')
        st.caption(t('ui.numerical_confusion_matrices_for_the_other_models_were_not'))
    st.subheader(t('ui.interpretation_limits'))
    st.write(t('ui.department_classification_was_generally_the_hardest_task_the_1'))
    st.download_button(t('ui.download_reported_test_metrics'),csv_bytes(df),file_name='reported_test_metrics.csv',mime='text/csv')
    st.caption(t('ui.source_supplied_university_complaints_ai_final_ipynb_saved_outputs'))
