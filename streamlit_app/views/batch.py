import hashlib
import uuid
import pandas as pd
import streamlit as st
from src.inference import predict_batch, batch_frame
from src.translations import t
from src.ui import heading, get_model, table
from src.utils import read_upload, csv_bytes, combine_batch_export


def render(db):
    heading(t('Analyze at scale','Топтық талдау'),t('Upload a CSV, choose a text column, and run real batched inference on your CPU.','CSV жүктеп, мәтін бағанын таңдап, CPU-да нақты топтық талдауды іске қосыңыз.'))
    st.caption(t('UTF-8 CSV · up to 5 MB / 1,000 rows · empty or invalid rows are reported and skipped · no automatic database saving.','UTF-8 CSV · 5 МБ / 1 000 жолға дейін · бос немесе жарамсыз жолдар белгіленіп, өткізіледі · дерекқорға автоматты түрде сақталмайды.'))
    sample=pd.DataFrame({'text_kk':['Сабақ кестесі дұрыс жасалмаған. Екі пән бір уақытта тұр.','Оқу ақысын төледім, бірақ жүйеде төлем көрсетілмейді.']})
    st.download_button(t('Download sample CSV','CSV мысалын жүктеу'),csv_bytes(sample),file_name='sample_complaints.csv',mime='text/csv')
    uploaded=st.file_uploader(t('Upload complaints','Шағымдарды жүктеу'),type=['csv'])
    if uploaded is None:
        return
    try:
        data=uploaded.getvalue()
        frame=read_upload(data)
    except (ValueError,UnicodeError,pd.errors.ParserError) as exc:
        st.error(str(exc));return
    columns=frame.columns.tolist()
    column=st.selectbox(t('Complaint text column','Шағым мәтінінің бағаны'),columns,index=columns.index('text_kk') if 'text_kk' in columns else 0)
    signature=hashlib.sha256(data+column.encode()).hexdigest()
    if st.session_state.get('batch_signature') != signature:
        st.session_state.pop('batch_results',None)
    table(frame.head(10))
    size=st.select_slider(t('Inference batch size','Талдау тобының өлшемі'),options=[1,2,4,8,16],value=4)
    if st.button(t('Analyze batch','Топты талдау'),type='primary'):
        st.session_state.pop('batch_results',None)
        bundle=get_model()
        if bundle:
            progress=st.progress(0.0)
            try:
                results=predict_batch(bundle,frame[column].tolist(),batch_size=size,progress=progress.progress)
                progress.progress(1.0)
                st.session_state.update(batch_results=results,batch_signature=signature,batch_key=str(uuid.uuid4()))
            except (ValueError,RuntimeError) as exc:
                st.error(str(exc))
    results=st.session_state.get('batch_results')
    if results is not None:
        output=batch_frame(results)
        valid=sum('error' not in r for r in results)
        st.success(t(f'{valid} analyzed · {len(results)-valid} invalid rows',f'{valid} талданды · {len(results)-valid} жарамсыз жол'))
        st.caption(t('Uncalibrated softmax probabilities; every prediction can be wrong. SLA values are demonstration examples.','Калибрленбеген softmax ықтималдықтары; әр болжам қате болуы мүмкін. SLA мәндері — демонстрациялық мысалдар.'))
        table(output)
        export=combine_batch_export(frame,output)
        st.download_button(t('Export predictions · CSV','Болжамдарды экспорттау · CSV'),csv_bytes(export),file_name='batch_predictions.csv',mime='text/csv')
        consent=st.checkbox(t('Save valid analyzed rows to the local complaint database.','Талданған жарамды жолдарды жергілікті шағым дерекқорына сақтау.'))
        saved=st.session_state.get('saved_batch_key')==st.session_state['batch_key']
        if st.button(t('Save batch','Топты сақтау'),disabled=not consent or not valid or saved):
            db.save_batch(results,st.session_state['batch_key'])
            st.session_state['saved_batch_key']=st.session_state['batch_key']
            st.rerun()
        if saved:st.success(t('This batch has been saved.','Бұл топ сақталды.'))
