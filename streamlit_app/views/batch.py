import hashlib
import uuid
import pandas as pd
import streamlit as st
from src.inference import predict_batch, batch_frame
from src.translations import t, error_text
from src.ui_state import selection_index
from src.ui import heading, get_model, table
from src.utils import read_upload, csv_bytes, combine_batch_export


def render(db):
    heading(t('ui.analyze_at_scale'),t('ui.upload_a_csv_choose_a_text_column_and_run'))
    st.caption(t('ui.utf_8_csv_up_to_5_mb_1_000'))
    sample=pd.DataFrame({'text':[t('sample.schedule.text'), t('sample.tuition.text')]})
    st.download_button(t('ui.download_sample_csv'),csv_bytes(sample),file_name='sample_complaints.csv',mime='text/csv')
    uploaded=st.file_uploader(t('ui.upload_complaints'),type=['csv'],key='batch_upload',on_change=remember_upload)
    if uploaded is not None:
        st.session_state['batch_upload_data'] = uploaded.getvalue()
        st.session_state['batch_upload_name'] = uploaded.name
    if 'batch_upload_data' not in st.session_state:
        return
    st.caption(t('ui.upload_retained', name=st.session_state['batch_upload_name']))
    try:
        data=st.session_state['batch_upload_data']
        frame=read_upload(data)
    except (ValueError,UnicodeError,pd.errors.ParserError) as exc:
        st.error(error_text(exc));return
    columns=frame.columns.tolist()
    column=st.selectbox(t('ui.complaint_text_column'),columns,key='batch_column',index=selection_index('batch_column',columns,columns.index('text_kk') if 'text_kk' in columns else 0),persist_state='session')
    signature=hashlib.sha256(data+column.encode()).hexdigest()
    if st.session_state.get('batch_signature') != signature:
        st.session_state.pop('batch_results',None)
    table(frame.head(10),user_data=True)
    size=st.select_slider(t('ui.inference_batch_size'),options=[1,2,4,8,16],value=4,key='batch_size',persist_state='session')
    if st.button(t('ui.analyze_batch'),key='analyze_batch',type='primary'):
        st.session_state.pop('batch_results',None)
        bundle=get_model()
        if bundle:
            progress=st.progress(0.0)
            try:
                results=predict_batch(bundle,frame[column].tolist(),batch_size=size,progress=progress.progress)
                progress.progress(1.0)
                st.session_state.update(batch_results=results,batch_signature=signature,batch_key=str(uuid.uuid4()))
            except (ValueError,RuntimeError) as exc:
                st.error(error_text(exc))
    results=st.session_state.get('batch_results')
    if results is not None:
        output=batch_frame(results)
        valid=sum('error' not in r for r in results)
        st.success(t('ui.batch_summary',valid=valid,invalid=len(results)-valid))
        st.caption(t('ui.uncalibrated_softmax_probabilities_every_prediction_can_be_wrong_sla'))
        table(output)
        st.caption(t('ui.export_identifiers'))
        export=combine_batch_export(frame,output)
        st.download_button(t('ui.export_predictions_csv'),csv_bytes(export),file_name='batch_predictions.csv',mime='text/csv')
        consent=st.checkbox(t('ui.save_valid_analyzed_rows_to_the_local_complaint_database'),key='batch_consent',persist_state='session')
        saved=st.session_state.get('saved_batch_key')==st.session_state['batch_key']
        if st.button(t('ui.save_batch'),key='save_batch',disabled=not consent or not valid or saved):
            db.save_batch(results,st.session_state['batch_key'])
            st.session_state['saved_batch_key']=st.session_state['batch_key']
            st.rerun()
        if saved:st.success(t('ui.this_batch_has_been_saved'))


def remember_upload():
    uploaded = st.session_state.get('batch_upload')
    for key in ('batch_results', 'batch_signature', 'batch_column'):
        st.session_state.pop(key, None)
    st.session_state['batch_consent'] = False
    if uploaded is None:
        st.session_state.pop('batch_upload_data', None)
        st.session_state.pop('batch_upload_name', None)
    else:
        st.session_state['batch_upload_data'] = uploaded.getvalue()
        st.session_state['batch_upload_name'] = uploaded.name
