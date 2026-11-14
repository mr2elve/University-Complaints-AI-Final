"""Trilingual presentation contracts and real-model UI workflows."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import re
from string import Formatter
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from src.config import ROOT, TARGETS
from src.database import Database
from src.translations import TRANSLATIONS, LANGUAGES, translate, display_frame, error_text

PAGES = ['dashboard', 'analyzer', 'management', 'review', 'batch', 'research', 'about']
LANGUAGE_CYCLE = ['English', 'Қазақша', 'Русский', 'English']
EXAMPLES = json.loads((ROOT/'data/multilingual_examples.json').read_text())


@pytest.fixture
def localized_app(monkeypatch, tmp_path):
    monkeypatch.setattr(Database.__init__, '__defaults__', (tmp_path/'localization.sqlite3',))
    return AppTest.from_file(str(ROOT/'app.py'), default_timeout=60).run()


def tr(key, language):
    return translate(key, LANGUAGES[language])


def switch(app, language):
    app.selectbox(key='language').set_value(language).run()
    assert not app.exception


def test_catalog_keys_and_format_placeholders_match():
    reference = TRANSLATIONS['en']
    for locale, catalog in TRANSLATIONS.items():
        assert set(catalog) == set(reference)
        for key, value in catalog.items():
            assert isinstance(value, str) and value.strip(), (locale, key)
            fields = lambda s: {field for _, field, _, _ in Formatter().parse(s) if field}
            assert fields(value) == fields(reference[key]), (locale, key)
            assert not re.search(r'\b(TODO|TBD|TRANSLATE)\b', value)


def test_no_inline_bilingual_calls_or_missing_literal_keys():
    for path in [ROOT/'app.py', ROOT/'src/ui.py', ROOT/'src/record_ui.py', *ROOT.glob('views/*.py')]:
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 't':
                assert len(node.args) == 1, (path, node.lineno)
                if isinstance(node.args[0], ast.Constant):
                    assert node.args[0].value in TRANSLATIONS['en'], (path, node.lineno)


@pytest.mark.parametrize('language', LANGUAGES)
@pytest.mark.parametrize('page', PAGES)
def test_each_page_in_each_language(localized_app, language, page):
    switch(localized_app, language)
    localized_app.radio(key='page').set_value(page).run()
    assert not localized_app.exception
    assert not localized_app.error
    assert localized_app.selectbox(key='language').label == tr('ui.language', language)
    assert localized_app.radio(key='page').value == page


@pytest.mark.parametrize('language', LANGUAGES)
def test_display_translation_does_not_mutate_records(monkeypatch, language):
    import src.translations as translations
    monkeypatch.setattr(translations, 'language', lambda: LANGUAGES[language])
    source = pd.DataFrame({'complaint_text':['English complaint / Қазақша / Русский'],
                           'status':['In Progress'], 'assigned_department':['finance_office'],
                           'action':['review_approved'], 'requires_review':[True],
                           'submitted_at':['2026-11-14T00:00:00+00:00']})
    before = source.copy(deep=True)
    output = display_frame(source)
    pd.testing.assert_frame_equal(source, before)
    assert output.iloc[0, 0] == source.iloc[0, 0]
    assert output.iloc[0, 1] == tr('labels.In Progress', language)
    assert output.iloc[0, 2] == tr('labels.finance_office', language)
    assert output.iloc[0, 3] == tr('labels.review_approved', language)
    assert output.iloc[0, 4] == tr('labels.yes', language)
    assert output.iloc[0, 5] == '14.11.2026 · 05:00'
    scores = display_frame(pd.DataFrame({'category':[.9], 'urgency':[.8]}))
    assert scores.iloc[0,0] == .9
    assert error_text(ValueError('Complaint must contain non-empty text.')) == tr('error.empty_text', language)
    assert error_text(RuntimeError('Untranslated dependency details')) == tr('error.generic', language)


@pytest.mark.model
@pytest.mark.parametrize('language', LANGUAGES)
@pytest.mark.parametrize('example', EXAMPLES, ids=lambda e:e['language'])
def test_any_input_language_in_any_ui(localized_app, language, example):
    switch(localized_app, language)
    localized_app.radio(key='page').set_value('analyzer').run()
    localized_app.text_area(key='complaint_input').set_value(example['text'])
    localized_app.button(key='analyze_complaint').click().run()
    assert not localized_app.exception and not localized_app.error
    result = localized_app.session_state['analysis']
    assert result['text'] == example['text']
    assert result['predictions']['department'] == 'finance_office'
    assert set(result['predictions']) == set(TARGETS)
    localized_app.button(key='save_complaint').click().run()
    row = Database().get(1)
    assert row['complaint_text'] == example['text']
    assert row['predicted_department'] == 'finance_office'
    localized_app.radio(key='page').set_value('dashboard').run()
    assert next(m for m in localized_app.metric if m.label == tr('ui.registered_complaints', language)).value == '1'


@pytest.mark.model
def test_language_cycle_preserves_draft_analysis_and_navigation(localized_app):
    app=localized_app
    app.radio(key='page').set_value('analyzer').run()
    text=EXAMPLES[0]['text']
    app.text_area(key='complaint_input').set_value(text)
    app.button(key='analyze_complaint').click().run()
    original=deepcopy(app.session_state['analysis'])
    analysis_key=app.session_state['analysis_key']
    draft=text+' Unsaved changes.'
    app.text_area(key='complaint_input').set_value(draft).run()
    for language in LANGUAGE_CYCLE:
        switch(app, language)
        assert app.radio(key='page').value == 'analyzer'
        assert app.text_area(key='complaint_input').value == draft
        assert app.session_state['analysis'] == original
        assert app.session_state['analysis_key'] == analysis_key
        assert any(w.value == tr('ui.these_results_belong_to_the_previously_analyzed_text_below', language) for w in app.warning)
        for page in PAGES:
            app.radio(key='page').set_value(page).run()
            assert not app.error and not app.exception
        app.radio(key='page').set_value('analyzer').run()
        assert app.text_area(key='complaint_input').value == draft
    assert Database().list().empty


@pytest.mark.model
def test_filters_edits_review_and_audit_survive_language_cycle(localized_app, real_result):
    app=localized_app
    result=deepcopy(real_result);result['requires_review']=True
    result['review_reasons']=['Low prediction confidence']
    ident=Database().save(result,'localization-review')
    app.radio(key='page').set_value('review').run()
    app.text_area(key='edit_notes').set_value('Қазақша / Русский / English notes').run()
    app.selectbox(key='edit_department').set_value('finance_office').run()
    app.selectbox(key='edit_urgency').set_value('high').run()
    app.checkbox(key='review_confirmed').check().run()
    for language in LANGUAGE_CYCLE:
        switch(app,language)
        assert app.text_area(key='edit_notes').value == 'Қазақша / Русский / English notes'
        assert app.selectbox(key='edit_department').value == 'finance_office'
        assert app.selectbox(key='edit_urgency').value == 'high'
        assert app.checkbox(key='review_confirmed').value
    app.button(key='approve_review').click().run()
    assert Database().get(ident)['reviewed_at']
    assert Database().history(ident).iloc[0]['action']=='review_approved'
    app.radio(key='page').set_value('management').run()
    app.text_input(key='search').set_value('Сабақ').run()
    app.multiselect(key='filter_status').set_value(['Assigned']).run()
    for language in LANGUAGE_CYCLE:
        switch(app,language)
        assert app.text_input(key='search').value == 'Сабақ'
        assert app.multiselect(key='filter_status').value == ['Assigned']
        assert app.selectbox(key='manage_record').value == ident
    app.selectbox(key='edit_status').set_value('Resolved').run()
    app.button(key='save_changes').click().run()
    assert Database().get(ident)['status']=='Resolved'
    assert len(Database().history(ident))==2


@pytest.mark.model
def test_batch_upload_results_and_consent_survive_switches(localized_app):
    app=localized_app
    app.radio(key='page').set_value('batch').run()
    payload=('text\n'+EXAMPLES[1]['text']+'\n""\n').encode()
    app.file_uploader(key='batch_upload').set_value(('complaints.csv',payload,'text/csv')).run()
    app.button(key='analyze_batch').click().run()
    results=deepcopy(app.session_state['batch_results'])
    batch_key=app.session_state['batch_key']
    app.checkbox(key='batch_consent').check().run()
    for language in LANGUAGE_CYCLE:
        switch(app,language)
        assert app.session_state['batch_results']==results
        assert app.session_state['batch_key']==batch_key
        assert app.checkbox(key='batch_consent').value
        assert app.selectbox(key='batch_column').value=='text'
        assert any(b.label == tr('ui.export_predictions_csv',language) for b in app.get('download_button'))
        assert not app.exception and not app.error
    app.radio(key='page').set_value('dashboard').run()
    app.radio(key='page').set_value('batch').run()
    assert app.session_state['batch_results']==results
    app.button(key='save_batch').click().run()
    assert len(Database().list())==1


@pytest.mark.parametrize('language', LANGUAGES)
def test_error_and_sample_states(localized_app,language):
    app=localized_app
    app.radio(key='page').set_value('analyzer').run()
    app.button(key='analyze_complaint').click().run()
    switch(app,language)
    assert any(e.value==tr('error.empty_text',language) for e in app.error)
    app.button(key='sample_tuition').click().run()
    assert app.text_area(key='complaint_input').value == tr('sample.tuition.text',language)
    assert not app.error
    app.radio(key='page').set_value('batch').run()
    app.file_uploader(key='batch_upload').set_value(('empty.csv',b'text\n','text/csv')).run()
    assert any(e.value==tr('error.csv_empty',language) for e in app.error)


def test_transcribed_matrices_match_reported_research_metrics():
    matrices=json.loads((ROOT/'data/research/svm_confusion_matrices.json').read_text())
    reported=pd.read_csv(ROOT/'data/research/test_comparison.csv').set_index('Model').loc['Linear SVM']
    for task,data in matrices.items():
        matrix=np.array(data['counts'])
        assert matrix.sum()==150
        score=np.mean(2*np.diag(matrix)/(matrix.sum(axis=0)+matrix.sum(axis=1)))
        assert score == pytest.approx(reported[task],abs=0.00005)
