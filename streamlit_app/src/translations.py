import streamlit as st


def t(english, kazakh):
    return kazakh if st.session_state.get('language') == 'Қазақша' else english


LABELS = {
    'category': ('Category', 'Санат'), 'urgency': ('Urgency', 'Шұғылдық'),
    'tone': ('Tone', 'Эмоциялық реңк'), 'department': ('Department', 'Бөлім'),
    'academic_process': ('Academic process', 'Оқу үдерісі'),
    'administrative_services': ('Administrative services', 'Әкімшілік қызметтер'),
    'campus_environment': ('Campus environment', 'Кампус ортасы'),
    'high': ('High', 'Жоғары'), 'medium': ('Medium', 'Орташа'), 'low': ('Low', 'Төмен'),
    'neutral': ('Neutral', 'Бейтарап'), 'dissatisfied': ('Dissatisfied', 'Көңілі толмаған'),
    'intense_negative': ('Intense negative', 'Қатты наразылық'),
    'academic_affairs': ('Academic affairs', 'Академиялық мәселелер бөлімі'),
    'faculty_dean_office': ("Faculty dean’s office", 'Факультет деканаты'),
    'student_service_center': ('Student service center', 'Студенттерге қызмет көрсету орталығы'),
    'facilities_office': ('Facilities office', 'Шаруашылық бөлімі'),
    'finance_office': ('Finance office', 'Қаржы бөлімі'),
    'security_ombudsperson': ('Security / ombudsperson', 'Қауіпсіздік / омбудсмен'),
    'New': ('New', 'Жаңа'), 'Pending Review': ('Pending Review', 'Тексеруді күтуде'),
    'Assigned': ('Assigned', 'Тағайындалды'), 'In Progress': ('In Progress', 'Орындалуда'),
    'Resolved': ('Resolved', 'Шешілді'), 'Closed': ('Closed', 'Жабылды'),
    'Low prediction confidence': ('Low prediction confidence', 'Болжам сенімділігі төмен'),
    'Potentially high urgency': ('Potentially high urgency', 'Шұғыл болуы мүмкін'),
    'Eligible for automatic routing': ('Eligible for automatic routing', 'Автоматты бағыттауға жарамды'),
}


def label(value):
    if value is None:
        return t('Unassigned', 'Тағайындалмаған')
    return t(*LABELS[value]) if value in LABELS else str(value)


def label_formatter():
    # Capture language at render time so widget formatting stays stable across reruns.
    translated = {key: t(*values) for key, values in LABELS.items()}
    translated[None] = t('Unassigned', 'Тағайындалмаған')
    translated['Unassigned'] = translated[None]
    return lambda value: translated.get(value, str(value))

COLUMNS = {
 'id': ('ID','ID'), 'complaint_text':('Complaint','Шағым'), 'text':('Text','Мәтін'),
 'predicted_category':('AI category','AI санаты'), 'predicted_urgency':('AI urgency','AI шұғылдығы'),
 'predicted_tone':('AI tone','AI реңкі'), 'predicted_department':('AI department','AI бөлімі'),
 'effective_urgency':('Current urgency','Ағымдағы шұғылдық'),
 'assigned_department':('Assigned department','Тағайындалған бөлім'), 'status':('Status','Мәртебе'),
 'submitted_at':('Submitted · Almaty','Тіркелген · Алматы'), 'resolved_at':('Resolved · Almaty','Шешілген · Алматы'),
 'reviewed_at':('Reviewed · Almaty','Тексерілген · Алматы'), 'timestamp':('Changed · Almaty','Өзгертілген · Алматы'),
 'routing_confidence':('Routing confidence','Бағыттау сенімділігі'),
 'high_urgency_probability':('P(high urgency)','P(жоғары шұғылдық)'),
 'requires_review':('AI review flag','AI тексеру белгісі'), 'review_reasons':('Routing reasons','Бағыттау себептері'),
 'admin_notes':('Administrator notes','Әкімші ескертпелері'), 'review_notes':('Review notes','Тексеру ескертпелері'),
 'previous_notes':('Previous notes','Алдыңғы ескертпелер'), 'action':('Action','Әрекет'),
 'previous_status':('Previous status','Алдыңғы мәртебе'), 'new_status':('New status','Жаңа мәртебе'),
 'previous_department':('Previous department','Алдыңғы бөлім'), 'new_department':('New department','Жаңа бөлім'),
 'previous_urgency':('Previous urgency','Алдыңғы шұғылдық'), 'new_urgency':('New urgency','Жаңа шұғылдық'),
 'row':('Source row','Бастапқы жол'), 'error':('Validation error','Тексеру қатесі'),
 'operational_priority':('Review priority','Тексеру басымдығы'), 'suggested_sla_hours':('Example SLA · hours','SLA мысалы · сағат'),
 'truncated':('Truncated to 96 tokens','96 токенге қысқартылған'),
 'Model':('Model','Модель'), 'mean_macro_f1':('Mean Macro-F1','Орташа Macro-F1'),
 'threshold':('Threshold','Шек'), 'coverage':('Auto-routing coverage','Автоматты бағыттау үлесі'),
 'routing_accuracy':('Routing accuracy','Бағыттау дәлдігі'), 'manual_review':('Manual review share','Қолмен тексеру үлесі'),
 'missed_urgent_auto_routed':('Missed urgent · auto-routed','Анықталмаған шұғыл · авто бағытталған'),
}


def column_labels(columns):
    return {c:t(*COLUMNS[c]) if c in COLUMNS else label(c) for c in columns}
