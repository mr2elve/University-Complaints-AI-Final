import plotly.express as px
import streamlit as st
from src.analytics import dashboard_metrics, trends
from src.translations import t, label
from src.ui import heading, empty, chart, table, COLORS


def render(db):
    heading(t('A clearer view of student concerns', 'Студент мәселелерінің айқын көрінісі'), t('Monitor complaints, routing decisions, and the work that needs your attention.', 'Шағымдарды, бағыттау шешімдерін және назар аударуды қажет ететін жұмыстарды бақылаңыз.'))
    df = db.list()
    m = dashboard_metrics(df)
    st.markdown('<div class="hero"><h3>' + t('Every student voice deserves a response.', 'Әр студенттің үні жауапқа лайық.') + '</h3><p>' + t('Understand the issue. Connect it to the right team. Keep people in the decision loop.', 'Мәселені түсініңіз. Тиісті бөлімге бағыттаңыз. Шешім қабылдауда адам бақылауын сақтаңыз.') + '</p></div>', unsafe_allow_html=True)
    metrics = [('total',t('Registered complaints','Тіркелген шағымдар')),('pending',t('Pending complaints','Күтілудегі шағымдар')),('review',t('Awaiting manual review','Қолмен тексеруді күтуде')),('high',t('High-priority · active','Жоғары басымдық · белсенді')),
               ('auto',t('Automatically routed','Автоматты бағытталған')),('resolved',t('Resolved / closed','Шешілген / жабылған')),('confidence',t('Average routing confidence','Орташа бағыттау сенімділігі'))]
    for start in (0,4):
        for col, (key,name) in zip(st.columns(4 if start == 0 else 3), metrics[start:start+4]):
            col.metric(name, f'{m[key]:.1%}' if key == 'confidence' and m['total'] else ('—' if key == 'confidence' else str(m[key])))
    st.caption(t('High priority includes active complaints with human-assigned high urgency or model P(high) ≥ 0.30. Auto-routing counts original AI decisions; review counts outstanding reviews.', 'Жоғары басымдық: адам жоғары шұғылдық берген немесе модельдің P(high) ≥ 0.30 болған белсенді шағымдар. Автоматты бағыттау бастапқы AI шешімдерін, тексеру аяқталмаған тексерулерді санайды.'))
    if df.empty:
        empty(t('Your workspace is ready', 'Жұмыс кеңістігі дайын'), t('Analyze a Kazakh complaint and choose Save to create your first record. Dashboard numbers will come from your saved records.', 'Қазақша шағымды талдап, алғашқы жазбаны жасау үшін «Сақтау» таңдаңыз. Көрсеткіштер сақталған жазбалардан есептеледі.'))
        return
    for columns in [('predicted_category','effective_urgency'),('assigned_department','status')]:
        for col,field in zip(st.columns(2),columns):
            with col, st.container(border=True):
                names={'predicted_category':t('AI category distribution','AI санаттарының үлестірімі'),'effective_urgency':t('Current urgency distribution','Ағымдағы шұғылдық үлестірімі'),'assigned_department':t('Assigned departments','Тағайындалған бөлімдер'),'status':t('Complaint status','Шағым мәртебесі')}
                st.subheader(names[field])
                counts=df[field].fillna('Unassigned').map(label).value_counts().rename_axis('label').reset_index(name='count')
                chart(px.pie(counts,names='label',values='count',hole=.68,color_discrete_sequence=COLORS))
    with st.container(border=True):
        st.subheader(t('Complaint activity','Шағымдар динамикасы'))
        chart(px.area(trends(df),x='date',y='count',color_discrete_sequence=COLORS,labels={'date':t('Date','Күні'),'count':t('Complaints','Шағымдар')}))
    st.subheader(t('Recent complaints','Соңғы шағымдар'))
    table(df[['id','complaint_text','predicted_category','effective_urgency','assigned_department','status','submitted_at']].head(8))
