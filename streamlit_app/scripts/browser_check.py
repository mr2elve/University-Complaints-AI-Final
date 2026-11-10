"""Optional visual QA using installed Chrome. Run against an isolated test database."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'assets/screenshots'
OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto('http://127.0.0.1:8501',wait_until='networkidle')
    page.get_by_role('heading',name='A clearer view of student concerns').wait_for()
    if page.get_by_text('Your workspace is ready',exact=True).count():
        page.screenshot(path=str(OUT/'dashboard-empty.png'),full_page=True)
    page.get_by_text('AI Complaint Analyzer',exact=True).click()
    page.get_by_role('button',name='Exam schedule',exact=True).click()
    expect(page.get_by_label('Complaint in Kazakh',exact=True)).to_have_value('Емтихан кестесінде екі пән бір уақытта қойылған. Бұл мәселені тез арада шешуді сұраймын.')
    print('Sample inserted',flush=True)
    page.get_by_role('button',name='Analyze Complaint',exact=True).click()
    try:
        page.get_by_role('heading',name='Analysis results').wait_for(timeout=30000)
    except Exception:
        page.screenshot(path=str(OUT/'browser-failure.png'),full_page=True)
        print(page.locator('body').inner_text(),flush=True)
        raise
    print('Real prediction rendered',flush=True)
    page.get_by_role('button',name='Save complaint',exact=True).wait_for()
    page.screenshot(path=str(OUT/'analyzer.png'),full_page=True)
    page.get_by_role('button',name='Save complaint',exact=True).click()
    page.get_by_text('Saved complaint #',exact=False).wait_for()
    page.get_by_text('Dashboard',exact=True).click()
    page.get_by_role('heading',name='Complaint activity').wait_for()
    page.screenshot(path=str(OUT/'dashboard.png'),full_page=True)
    for name,heading in [
        ('Complaint Management','Complaint management'),('Manual Review Queue','Human judgment comes first'),
        ('Batch Analysis','Analyze at scale'),('Model Analytics','Evidence behind the model'),
        ('About the Project','AI University Complaint Management System')]:
        page.get_by_text(name,exact=True).first.click()
        page.get_by_role('heading',name=heading,exact=True).wait_for()
        assert page.locator('[data-testid="stException"]').count()==0,name
    mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
    mobile.goto('http://127.0.0.1:8501',wait_until='networkidle')
    mobile.get_by_role('heading',name='A clearer view of student concerns').wait_for()
    mobile.screenshot(path=str(OUT/'mobile.png'),full_page=True)
    overflow=mobile.evaluate('document.documentElement.scrollWidth > window.innerWidth')
    print(json.dumps({'browser_errors':errors,'mobile_horizontal_overflow':overflow,'screenshots':str(OUT)},indent=2))
    assert not errors
    assert not overflow
    browser.close()
