"""Trilingual Chrome QA. Run only against an isolated test database."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
CATALOGS={lang:json.loads((ROOT/'locales'/f'{lang}.json').read_text()) for lang in ('en','kk','ru')}
NAMES={'en':'English','kk':'Қазақша','ru':'Русский'}
NAV={'dashboard':'ui.dashboard','analyzer':'ui.ai_complaint_analyzer','management':'ui.complaint_management',
     'review':'ui.manual_review_queue','batch':'ui.batch_analysis','research':'ui.model_analytics','about':'ui.about_the_project'}
TITLES={'dashboard':'ui.a_clearer_view_of_student_concerns','analyzer':'ui.from_complaint_to_clarity',
        'management':'ui.complaint_management_97','review':'ui.human_judgment_comes_first',
        'batch':'ui.analyze_at_scale','research':'ui.evidence_behind_the_model','about':'ui.ai_university_complaint_management_system'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8511')
    parser.add_argument('--output-dir',type=Path,default=Path('/tmp/university-localization-browser'))
    parser.add_argument('--confirm-isolated-database',action='store_true')
    parser.add_argument('--mobile-only',action='store_true',help='Run just the 21 mobile page/language checks.')
    args=parser.parse_args()
    if not args.confirm_isolated_database:
        parser.error('Use an isolated test database and pass --confirm-isolated-database; this test saves illustrative complaints.')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    report={'page_checks':[], 'browser_errors':[], 'workflows':[]}
    examples=json.loads((ROOT/'data/multilingual_examples.json').read_text())
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
        page.on('pageerror',lambda error:report['browser_errors'].append(str(error)))
        locale='en';active='dashboard'

        def text(key): return CATALOGS[locale][key]

        def sidebar():
            if page.get_by_test_id('stSidebar').get_attribute('data-collapsed')=='true':
                page.get_by_test_id('stExpandSidebarButton').click()
            expect(page.get_by_test_id('stSidebar')).to_have_attribute('data-collapsed','false')
            # Wait for the slide-in transition; opening a popup while its anchor
            # is still moving can cause React Aria to dismiss that popup.
            page.wait_for_function("document.querySelector('[data-testid=stSidebar]').getBoundingClientRect().x >= -0.5")
            page.get_by_test_id('stSidebar').get_by_role('combobox').scroll_into_view_if_needed()
            page.wait_for_timeout(200)

        def settle():
            expect(page.get_by_role('heading',name=text(TITLES[active]),exact=True)).to_be_visible()
            expect(page.locator('html')).to_have_attribute('lang',locale)
            page.wait_for_timeout(120)  # Give the scoped native-chrome MutationObserver one frame.
            assert page.get_by_test_id('stException').count()==0

        def switch(target):
            nonlocal locale
            sidebar()
            page.get_by_test_id('stSidebar').get_by_test_id('stSelectbox').get_by_role('button').last.click()
            try:
                page.get_by_role('option',name=NAMES[target],exact=True).click(timeout=5000)
            except Exception:
                page.screenshot(path=str(args.output_dir/'language-switch-failure.png'),full_page=True)
                print('LANGUAGE SWITCH DEBUG',page.locator('body').inner_text(),flush=True)
                raise
            locale=target;settle()

        def navigate(target):
            nonlocal active
            sidebar();page.get_by_test_id('stSidebar').get_by_text(text(NAV[target]),exact=True).click()
            active=target;settle()

        def button(key):return page.get_by_role('button',name=text(key),exact=True)

        def inspect_page(viewport):
            settle()
            if viewport=='mobile':
                sidebar();page.get_by_test_id('stSidebarCollapseButton').click()
                expect(page.get_by_test_id('stSidebar')).to_have_attribute('data-collapsed','true')
                page.wait_for_function("document.querySelector('[data-testid=stSidebar]').getBoundingClientRect().right <= 1")
            overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth')
            assert not overflow,(viewport,locale,active)
            if locale!='en':
                content=page.locator('body').inner_text()
                for leaked in ('Skip to main content','per file','options available.','academic_process','finance_office','review_approved'):
                    assert leaked not in content,(locale,active,leaked)
            page.screenshot(path=str(args.output_dir/f'{viewport}-{locale}-{active}.png'),full_page=True)
            report['page_checks'].append({'viewport':viewport,'locale':locale,'page':active,'horizontal_overflow':overflow})
            if active=='about' and viewport=='desktop':
                page.get_by_role('button',name=text('native.32'),exact=True).click()
                expect(page.get_by_test_id('stMainMenuPopover')).to_contain_text(
                    text('native.made_with_streamlit_version_prefix')+'1.67.0')
                page.keyboard.press('Escape')
            if active=='research':
                matrix_toggle=page.get_by_text(text('ui.original_svm_test_confusion_matrices'),exact=True)
                matrix_toggle.click()
                plot=page.get_by_test_id('stPlotlyChart').last
                expect(plot).to_be_visible()
                page.wait_for_timeout(1000)  # Expander and Plotly resize must settle before the screenshot.
                plot.scroll_into_view_if_needed()
                axis_text=' '.join(plot.locator('svg').all_text_contents())
                assert text('ui.true_label') in axis_text
                assert text('ui.predicted_label') in axis_text
                assert 'finance_office' not in axis_text
                plot.screenshot(path=str(args.output_dir/f'{viewport}-{locale}-matrix.png'))
                matrix_toggle.click()

        if not args.mobile_only:
            page.goto(args.url,wait_until='networkidle');settle()
            for lang in ('en','kk','ru'):
                switch(lang)
                for target in NAV:
                    navigate(target);inspect_page('desktop')
            print('PASS: 21 desktop page/language combinations',flush=True)

            # Real browser typing without submitting: switching language must retain the draft.
            navigate('analyzer')
            draft='Қазақша мәтін / Русский текст / English draft'
            page.get_by_role('textbox').fill(draft)
            for lang in ('en','kk','ru','en'):
                switch(lang)
                expect(page.get_by_role('textbox')).to_have_value(draft)
            report['workflows'].append('Unsubmitted draft retained through EN → KK → RU → EN')

            for lang in ('en','kk','ru'):
                switch(lang)
                for example in examples:
                    page.get_by_role('textbox').fill(example['text'])
                    button('ui.analyze_complaint').click()
                    expect(page.get_by_role('heading',name=text('ui.analysis_results'),exact=True)).to_be_visible(timeout=60000)
                    expect(page.get_by_test_id('stText').last).to_have_text(example['text'],timeout=60000)
                    expect(page.get_by_test_id('stStatusWidget')).to_be_hidden(timeout=60000)
                    expect(page.locator('.result-card .value').last).to_have_text(text('labels.finance_office'))
                report['workflows'].append(f'Real kk/ru/en/mixed inference with {lang} interface')
            button('ui.save_complaint').click()
            expect(page.get_by_text(text('ui.saved_complaint'),exact=False)).to_be_visible()
            report['workflows'].append('Explicit complaint saving')
            for lang in ('en','kk','ru','en'):
                switch(lang)
                expect(page.locator('.result-card .value').last).to_have_text(text('labels.finance_office'))
                expect(page.get_by_role('textbox')).to_have_value(examples[-1]['text'])
            report['workflows'].append('Saved analysis/results retained through language cycle')

            # This actual model output requires review; no artificial probabilities are injected.
            security='Бір студент мені қорқытып, ақша талап етіп жүр. Өзімді қауіпсіз сезінбеймін. Шұғыл көмек керек.'
            page.get_by_role('textbox').fill(security);button('ui.analyze_complaint').click()
            expect(page.get_by_test_id('stText').last).to_have_text(security,timeout=60000)
            expect(page.get_by_test_id('stStatusWidget')).to_be_hidden(timeout=60000)
            expect(page.get_by_text(text('ui.manual_review')+' —',exact=False)).to_be_visible()
            button('ui.save_complaint').click();expect(page.get_by_text(text('ui.saved_complaint'),exact=False)).to_be_visible()
            navigate('review')
            reviewed_choice=page.get_by_role('combobox',name=text('ui.review_complaint'),exact=True).input_value()
            expect(page.get_by_role('combobox',name=text('ui.assigned_department_human_decision'),exact=True)).to_have_value(text('labels.security_ombudsperson'))
            notes='Browser QA / Қазақша / Русский'
            page.get_by_role('textbox',name=text('ui.administrator_notes'),exact=True).fill(notes)
            for lang in ('kk','ru','en'):
                switch(lang)
                expect(page.get_by_role('textbox',name=text('ui.administrator_notes'),exact=True)).to_have_value(notes)
                expect(page.get_by_role('combobox',name=text('ui.assigned_department_human_decision'),exact=True)).to_have_value(text('labels.security_ombudsperson'))
            page.get_by_text(text('ui.i_have_reviewed_the_full_complaint_considered_urgency_and'),exact=True).click()
            expect(page.get_by_role('checkbox',name=text('ui.i_have_reviewed_the_full_complaint_considered_urgency_and'),exact=True)).to_be_checked()
            button('ui.approve_routing_mark_reviewed').click()
            expect(page.get_by_text(text('ui.decision_saved_original_ai_predictions_are_preserved'),exact=True)).to_be_visible()
            report['workflows'].append('Actual flagged complaint, notes retained, human review approval')
            navigate('management')
            page.get_by_role('textbox',name=text('ui.search_complaint_text_or_id'),exact=True).fill('Бір студент')
            page.get_by_role('textbox',name=text('ui.search_complaint_text_or_id'),exact=True).press('Tab')
            page.get_by_text(text('ui.change_history'),exact=True).click()
            expect(page.get_by_test_id('stDataFrame').last).to_be_visible()
            for lang in ('kk','ru','en'):
                switch(lang)
                expect(page.get_by_role('textbox',name=text('ui.search_complaint_text_or_id'),exact=True)).to_have_value('Бір студент')
            page.get_by_role('combobox',name=text('ui.open_complaint'),exact=True).click()
            page.get_by_role('option',name=reviewed_choice,exact=True).click()
            expect(page.get_by_role('textbox',name=text('ui.administrator_notes'),exact=True)).to_have_value(notes)
            page.get_by_label(text('ui.current_status'),exact=True).click()
            page.get_by_role('option',name=text('labels.Resolved'),exact=True).click()
            button('ui.save_changes').click()
            expect(page.get_by_text(text('ui.decision_saved_original_ai_predictions_are_preserved'),exact=True)).to_be_visible()
            assert page.get_by_test_id('stAlert').filter(has_text=text('error.review_required')).count()==0
            report['workflows'].append('Search, status update and audit history')

            switch('ru')
            grid=page.get_by_test_id('stDataFrame').first
            grid.hover()
            # Exercise keyboard access to the hover toolbar. Pointer movement
            # while auto-scrolling can hide it beneath the dataframe canvas.
            columns_button=page.get_by_role('button',name=text('native.17'),exact=True).first
            columns_button.focus();columns_button.press('Enter')
            expect(page.get_by_test_id('stDataFrameColumnVisibilityMenu')).to_contain_text(text('native.index'))
            page.keyboard.press('Escape');grid.hover()
            search_button=page.get_by_role('button',name=text('native.9'),exact=True).first
            search_button.focus();search_button.press('Enter')
            expect(page.get_by_text(text('native.type_to_search'),exact=True)).to_be_visible()
            expect(page.get_by_test_id('search-input')).to_have_attribute('aria-label',text('native.10'))
            page.keyboard.press('Escape')
            report['workflows'].append('Localized native table column menu, search prompt and accessible search label')

            navigate('batch')
            page.locator('input[type=file]').set_input_files({'name':'localization.csv','mimeType':'text/csv',
                'buffer':('text\n'+examples[0]['text']+'\n""\n').encode()})
            button('ui.analyze_batch').click()
            expect(button('ui.export_predictions_csv')).to_be_visible(timeout=60000)
            for lang in ('kk','ru','en'):
                switch(lang);expect(button('ui.export_predictions_csv')).to_be_visible()
            with page.expect_download() as download:
                button('ui.export_predictions_csv').click()
            destination=args.output_dir/'batch_predictions.csv';download.value.save_as(destination)
            assert 'finance_office' in destination.read_text(encoding='utf-8-sig')
            page.get_by_text(text('ui.save_valid_analyzed_rows_to_the_local_complaint_database'),exact=True).click()
            expect(page.get_by_role('checkbox',name=text('ui.save_valid_analyzed_rows_to_the_local_complaint_database'),exact=True)).to_be_checked()
            button('ui.save_batch').click();expect(page.get_by_text(text('ui.this_batch_has_been_saved'),exact=True)).to_be_visible()
            report['workflows'].append('CSV upload, invalid row, real batch inference, export and opt-in saving')

            # Native upload errors and framework accessibility labels are also localized.
            switch('ru')
            page.locator('input[type=file]').set_input_files({'name':'bad.txt','mimeType':'text/plain','buffer':b'invalid'})
            expect(page.get_by_test_id('stFileUploader')).to_contain_text(text('native.file_type_error').format(type='text/plain'))
            expect(page.get_by_test_id('stFileUploader')).not_to_contain_text('files are not allowed')
            page.locator('input[type=file]').set_input_files([])
            report['workflows'].append('Localized native upload error')

        # A fresh mobile tab matches a real mobile visit (including the default
        # collapsed sidebar) instead of inheriting a desktop sidebar width.
        page.close()
        page=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
        page.on('pageerror',lambda error:report['browser_errors'].append(str(error)))
        locale='en';active='dashboard'
        page.goto(args.url,wait_until='networkidle');settle()
        for lang in ('en','kk','ru'):
            switch(lang)
            for target in NAV:
                navigate(target);inspect_page('mobile')
        print('PASS: 21 mobile page/language combinations',flush=True)
        report['browser_version']=browser.version
        assert not report['browser_errors'],report['browser_errors']
        (args.output_dir/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'page_checks':len(report['page_checks']),'workflows':report['workflows'],
                          'browser_errors':report['browser_errors'],'artifacts':str(args.output_dir)},ensure_ascii=False,indent=2))
        browser.close()


if __name__=='__main__':
    main()
