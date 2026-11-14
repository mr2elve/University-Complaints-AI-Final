import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import ROOT, TARGETS
from src.translations import t, label, column_labels
from src.ui import heading, chart, COLORS
from src.utils import csv_bytes


def render(db):
    heading(t('Evidence behind the model','Модельдің зерттеу негізі'),t('Published multilingual evaluation and original research · four classification tasks','Жарияланған көптілді бағалау және бастапқы зерттеу · төрт жіктеу міндеті'))
    st.subheader(t('Deployed multilingual XLM-RoBERTa', 'Қолданыстағы көптілді XLM-RoBERTa'))
    multilingual = pd.read_csv(ROOT/'data/research/xlmr_metrics_by_language.csv')
    st.dataframe(multilingual, hide_index=True, width='stretch')
    st.caption(t('Published export results: 150 held-out complaints per language, grouped by original complaint ID before translation expansion. Synthetic Kazakh–Russian mixed-input mean Macro-F1: 0.9829; this is not a real-user benchmark.', 'Жарияланған экспорт нәтижелері: әр тілде 150 тест шағымы; аудармаларды қоспас бұрын бастапқы шағым ID бойынша бөлінген. Жасанды қазақша–орысша аралас мәтіннің орташа Macro-F1: 0.9829; бұл нақты пайдаланушылар бағалауы емес.'))
    st.subheader(t('Original Kazakh-only research comparison', 'Бастапқы қазақша зерттеуді салыстыру'))
    st.caption(t('The historical results below use a different experiment and split; they do not evaluate the newly deployed checkpoint.', 'Төмендегі тарихи нәтижелер басқа тәжірибе мен бөлуге негізделген; олар жаңа модельді бағаламайды.'))
    df=pd.read_csv(ROOT/'data/research/test_comparison.csv')
    a,b,c=st.columns(3)
    a.metric(t('Best overall · Linear SVM','Ең үздік жалпы нәтиже · Linear SVM'),'0.9731')
    b.metric(t('Best category · KazRoBERTa','Ең үздік санат · KazRoBERTa'),'0.9933')
    c.metric(t('Best urgency · BiLSTM','Ең үздік шұғылдық · BiLSTM'),'0.9790')
    st.caption(t('Values are Macro-F1. SVM and BiLSTM both achieved 1.0000 Tone Macro-F1.','Мәндер — Macro-F1. SVM және BiLSTM реңк бойынша 1.0000 Macro-F1 көрсетті.'))
    st.subheader(t('Architecture comparison','Архитектураларды салыстыру'))
    display=df[['Model',*TARGETS,'mean_macro_f1']].sort_values('mean_macro_f1',ascending=False)
    st.dataframe(display.style.format({c:'{:.4f}' for c in [*TARGETS,'mean_macro_f1']}),hide_index=True,width='stretch',column_config=column_labels(display.columns))
    long=df.melt(id_vars='Model',value_vars=list(TARGETS),var_name='task',value_name='Macro-F1')
    long['task']=long.task.map(label)
    fig=px.bar(long,x='Model',y='Macro-F1',color='task',barmode='group',color_discrete_sequence=COLORS)
    fig.update_yaxes(range=[0,1.05]);chart(fig)
    with st.container(border=True):
        st.subheader(t('Mean Macro-F1 ranking','Орташа Macro-F1 рейтингі'))
        fig=px.bar(df.sort_values('mean_macro_f1'),y='Model',x='mean_macro_f1',orientation='h',text='mean_macro_f1',color='Model',color_discrete_sequence=COLORS,labels={'mean_macro_f1':'Mean Macro-F1'})
        fig.update_xaxes(range=[0,1]);fig.update_layout(showlegend=False);chart(fig)
    st.info(t('The application now uses the multilingual XLM-RoBERTa checkpoint. The following comparison is retained from the original study. Linear SVM achieved the highest overall mean test Macro-F1. These results do not establish that a larger model is better.','Қолданба қазір көптілді XLM-RoBERTa моделін қолданады. Келесі салыстыру бастапқы зерттеуден сақталған. Linear SVM тестте ең жоғары орташа Macro-F1 көрсетті. Бұл нәтижелер үлкенірек модельдің жақсырақ екенін дәлелдемейді.'))
    models=[('Linear SVM',t('Character TF-IDF (char_wb, 2–5 grams), with four independently trained classifiers. C was selected on validation.','Таңбалық TF-IDF (char_wb, 2–5 грамма), төрт бөлек жіктеуіш. C валидацияда таңдалды.')),
            ('BiLSTM + Attention',t('Shared bidirectional LSTM, learned attention pooling, and four linear heads.','Ортақ екібағытты LSTM, үйретілген attention pooling және төрт сызықтық бас.')),
            ('XLM-RoBERTa',t('Multilingual pretrained encoder, masked mean pooling, dropout 0.2, and four heads.','Алдын ала үйретілген көптілді кодтағыш, маскаланған орташа біріктіру, dropout 0.2 және төрт бас.')),
            ('KazRoBERTa',t('Kazakh conversational RoBERTa: 6 encoder layers, hidden size 768; masked mean pooling, dropout 0.2, and 3 / 3 / 3 / 6 output classes.','Қазақша сөйлесу RoBERTa: 6 кодтағыш қабаты, жасырын өлшемі 768; маскаланған орташа біріктіру, dropout 0.2 және 3 / 3 / 3 / 6 шығыс класы.'))]
    with st.expander(t('How the architectures work','Архитектуралар қалай жұмыс істейді')):
        for name,description in models:
            st.markdown(f'**{name}**');st.write(description)
    st.subheader(t('Urgency deserves special attention','Шұғылдық ерекше назарды қажет етеді'))
    misses=df[['Model','missed_high','total_high']].copy()
    misses['missed']=misses.missed_high.astype(str)+' / '+misses.total_high.astype(str)
    fig=px.bar(misses,x='Model',y='missed_high',text='missed',color_discrete_sequence=['#E16A81'],labels={'missed_high':t('High-urgency complaints missed','Жоғары шұғылдықтағы өткізіп алған шағымдар')});chart(fig)
    st.warning(t('KazRoBERTa missed 5 of 38 high-urgency test cases. At confidence threshold 0.75, one high-urgency validation case was still auto-routed with an incorrect urgency prediction. High confidence is not a safety guarantee.','KazRoBERTa жоғары шұғылдықтағы 38 тест жағдайының 5-еуін анықтамады. 0.75 шегінде жоғары шұғылдықтағы бір валидация жағдайы қате шұғылдық болжамымен автоматты бағытталды. Жоғары сенімділік қауіпсіздікке кепілдік бермейді.'))
    st.subheader(t('Routing trade-off · validation only','Бағыттау теңгерімі · тек валидация'))
    routing=pd.read_csv(ROOT/'data/research/routing_validation.csv')
    st.dataframe(routing,hide_index=True,width='stretch',column_config=column_labels(routing.columns))
    routing_plot=routing.melt(id_vars='threshold',value_vars=['coverage','routing_accuracy','manual_review'],var_name='metric',value_name='value')
    routing_plot['metric']=routing_plot.metric.map(column_labels(routing.columns))
    chart(px.line(routing_plot,x='threshold',y='value',color='metric',markers=True,color_discrete_sequence=COLORS,labels={'value':t('Share / accuracy','Үлес / дәлдік'),'threshold':t('Confidence threshold','Сенімділік шегі')}))
    st.caption(t('Routing accuracy measures department correctness only among automatically routed complaints. All points also require P(high) < 0.30. The 0.85 point’s 100% observed accuracy is based on a small validation subset, not a guarantee.','Бағыттау дәлдігі тек автоматты бағытталған шағымдардың бөлім болжамының дұрыстығын өлшейді. Барлық нүктеде P(high) < 0.30 шарты бар. 0.85 шегіндегі 100% дәлдік шағын валидация ішкі жиынына негізделген, кепілдік емес.'))
    with st.expander(t('Original SVM test confusion matrices','Бастапқы SVM тест қателік матрицалары')):
        image=ROOT/'assets/svm_test_confusion_matrices.png'
        if image.exists():st.image(str(image),caption=t('Original notebook cell 19 · Linear SVM · test split','Бастапқы ноутбуктың 19-ұяшығы · Linear SVM · тест жиыны'))
        else:st.info(t('The original notebook image is unavailable.','Бастапқы ноутбук кескіні қолжетімсіз.'))
        st.caption(t('Numerical confusion matrices for the other models were not supplied. No synthetic matrices are displayed.','Басқа модельдердің сандық қателік матрицалары берілмеген. Жасанды матрицалар көрсетілмейді.'))
    st.subheader(t('Interpretation & limits','Түсіндіру және шектеулер'))
    st.write(t('Department classification was generally the hardest task. The 1,000-example dataset contains similar textual patterns across splits; the split was not group-aware. A small test set, uncalibrated probabilities, limited training runs, and no operational university evaluation restrict generalization.','Бөлімді жіктеу көбіне ең күрделі міндет болды. 1 000 мысалдық деректер жиынының бөліктерінде ұқсас мәтіндік құрылымдар бар; бөлу топтарды ескермеген. Шағын тест жиыны, калибрленбеген ықтималдықтар, шектеулі үйрету тәжірибелері және нақты университеттегі бағалаудың болмауы жалпылауды шектейді.'))
    st.download_button(t('Download reported test metrics','Тест көрсеткіштерін жүктеу'),csv_bytes(df),file_name='reported_test_metrics.csv',mime='text/csv')
    st.caption(t('Source: supplied University_Complaints_AI_Final.ipynb, saved outputs in cells 18, 19, 23; supplied research README. These are reported research results, separate from live application analytics.','Дереккөз: берілген University_Complaints_AI_Final.ipynb, 18, 19, 23 ұяшықтардың сақталған шығыстары; зерттеу README. Бұл — қолданбаның ағымдағы аналитикасынан бөлек зерттеу нәтижелері.'))
