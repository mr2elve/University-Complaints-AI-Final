from copy import deepcopy
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from src.database import Database

APP=str(Path(__file__).resolve().parent.parent/'app.py')
PAGES=['dashboard','analyzer','management','review','batch','research','about']

@pytest.fixture
def app(monkeypatch,tmp_path):
    import src.config
    import src.database
    path=tmp_path/'ui.sqlite3'
    # The app constructor's default was bound on import; replace only its path default.
    monkeypatch.setattr(Database.__init__,'__defaults__',(path,))
    return AppTest.from_file(APP,default_timeout=60)

@pytest.mark.parametrize('language',['English','Қазақша'])
def test_all_pages_empty(app,language):
    app.run()
    app.selectbox(key='language').set_value(language).run()
    for page in PAGES:
        app.radio(key='page').set_value(page).run()
        assert not app.exception, (page,[e.message for e in app.exception])
        assert not app.error, (page,[e.value for e in app.error])

@pytest.mark.model
def test_analyze_save_and_edit(app):
    app.run()
    app.radio(key='page').set_value('analyzer').run()
    app.text_area(key='complaint_input').set_value('Сабақ кестесі дұрыс жасалмаған. Екі пән бір уақытта тұр.')
    next(b for b in app.button if b.label=='Analyze Complaint').click().run(timeout=90)
    assert not app.exception
    assert app.session_state['analysis']['predictions']['category']=='academic_process'
    next(b for b in app.button if b.label=='Save complaint').click().run()
    assert not app.exception
    assert len(Database().list())==1
    app.radio(key='page').set_value('management').run()
    assert not app.exception
    app.selectbox(key='edit_status').set_value('Resolved')
    app.text_area(key='edit_notes').set_value('Resolved in UI integration test.')
    next(b for b in app.button if b.label=='Save changes').click().run()
    assert not app.exception
    assert Database().get(1)['status']=='Resolved'
    assert len(Database().history(1))==1
    app.radio(key='page').set_value('dashboard').run()
    assert not app.exception
    assert next(m for m in app.metric if m.label=='Resolved / closed').value=='1'

@pytest.mark.model
def test_review_workflow_and_bilingual_populated_pages(app,real_result):
    result=deepcopy(real_result)
    result['requires_review']=True
    result['review_reasons']=['Low prediction confidence']
    ident=Database().save(result,'ui_review')
    app.run()
    for language in ['English','Қазақша']:
        app.selectbox(key='language').set_value(language).run()
        for page in ['dashboard','management','review']:
            app.radio(key='page').set_value(page).run()
            assert not app.exception, (page,[e.message for e in app.exception])
    app.selectbox(key='language').set_value('English').run()
    app.checkbox(key='review_confirmed').check()
    app.selectbox(key='edit_urgency').set_value('high')
    next(b for b in app.button if b.label=='Approve routing & mark reviewed').click().run()
    assert not app.exception
    assert Database().get(ident)['reviewed_at']
    assert Database().get(ident)['effective_urgency']=='high'


def test_empty_analyzer_error(app):
    app.run()
    app.radio(key='page').set_value('analyzer').run()
    next(b for b in app.button if b.label=='Analyze Complaint').click().run()
    assert not app.exception and app.error
    assert Database().list().empty

@pytest.mark.model
def test_batch_upload_export_and_explicit_save(app):
    app.run()
    app.radio(key='page').set_value('batch').run()
    payload='id,text_kk\n1,Сабақ кестесі дұрыс жасалмаған. Екі пән бір уақытта тұр.\n2,\n3,Оқу ақысын төледім бірақ жүйеде төлем көрсетілмейді.\n'.encode()
    app.file_uploader[0].set_value(('complaints.csv',payload,'text/csv')).run()
    assert not app.exception
    next(b for b in app.button if b.label=='Analyze batch').click().run(timeout=90)
    assert not app.exception
    assert len(app.session_state['batch_results'])==3
    assert 'error' in app.session_state['batch_results'][1]
    assert Database().list().empty
    assert any('Export predictions' in b.label for b in app.get('download_button'))
    app.checkbox[0].check().run()
    next(b for b in app.button if b.label=='Save batch').click().run()
    assert not app.exception
    assert len(Database().list())==2
    assert next(b for b in app.button if b.label=='Save batch').disabled
    app.file_uploader[0].set_value(('other.csv',b'text_kk\nnew text\n','text/csv')).run()
    assert not app.exception
    assert 'batch_results' not in app.session_state

@pytest.mark.model
def test_stale_form_cannot_overwrite_another_session(app,real_result):
    from src.config import DEPARTMENTS
    ident=Database().save(real_result,'stale-ui')
    app.run()
    app.radio(key='page').set_value('management').run()
    Database().update(ident,status='In Progress',department='academic_affairs',urgency='high',notes='Other session',expected_version=1,departments=DEPARTMENTS)
    app.text_area(key='edit_notes').set_value('Stale notes')
    next(b for b in app.button if b.label=='Save changes').click().run()
    assert not app.exception
    assert any('record changed' in e.value for e in app.error)
    assert Database().get(ident)['admin_notes']=='Other session'
    next(b for b in app.button if b.label=='Reload record').click().run()
    assert not app.exception
    assert app.text_area(key='edit_notes').value=='Other session'
