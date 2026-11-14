"""Check startup without inherited modules, PYTHONPATH or existing bytecode."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


APP_DIR = Path(__file__).resolve().parents[1]


def test_translation_public_import_in_fresh_process(tmp_path):
    """Exercise the exact Cloud failure before the app can preload any module."""
    code = '''
import sys
from pathlib import Path
assert 'src.translations' not in sys.modules
from src.translations import t, error_text
import src.translations as translations
assert callable(t) and callable(error_text)
assert Path(translations.__file__).resolve() == Path('src/translations.py').resolve()
print('TRANSLATION_IMPORT_OK')
'''
    process = subprocess.run(
        [sys.executable, '-E', '-s', '-B', '-X', f'pycache_prefix={tmp_path / "bytecode"}',
         '-c', code],
        cwd=APP_DIR, capture_output=True, text=True, encoding='utf-8', timeout=60,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    assert 'TRANSLATION_IMPORT_OK' in process.stdout


SMOKE = r'''
import ast
import importlib
import json
from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest

app_dir = Path(sys.argv[1]).resolve()
assert 'src.translations' not in sys.modules
app = AppTest.from_file(str(app_dir / 'app.py'), default_timeout=60).run()
assert not app.exception, [e.message for e in app.exception]
assert not app.error, [e.value for e in app.error]

translations = importlib.import_module('src.translations')
assert Path(translations.__file__).resolve() == app_dir / 'src/translations.py'
assert callable(translations.t) and callable(translations.error_text)
checked = []
for path in [app_dir / 'app.py', *sorted((app_dir / 'src').glob('*.py')),
             *sorted((app_dir / 'views').glob('*.py'))]:
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if isinstance(node, ast.ImportFrom) and node.module == 'src.translations':
            for alias in node.names:
                assert hasattr(translations, alias.name), (str(path), alias.name)
            checked.append(str(path.relative_to(app_dir)))

pages = ['dashboard', 'analyzer', 'management', 'review', 'batch', 'research', 'about']
for name in translations.LANGUAGES:
    app.selectbox(key='language').set_value(name).run()
    for page in pages:
        app.radio(key='page').set_value(page).run()
        assert not app.exception, (name, page, [e.message for e in app.exception])
        assert not app.error, (name, page, [e.value for e in app.error])
        assert app.radio(key='page').value == page

print('STARTUP_OK ' + json.dumps({
    'cwd': str(Path.cwd()), 'translation_module': translations.__file__,
    'import_contracts': checked, 'page_language_combinations': 21,
    'catalog_sizes': {code: len(values) for code, values in translations.TRANSLATIONS.items()},
}))
'''


@pytest.mark.parametrize('working_directory', ['app', 'repository'])
def test_fresh_process_startup(working_directory, tmp_path):
    env = os.environ.copy()
    env['COMPLAINT_DB_PATH'] = str(tmp_path / 'startup.sqlite3')
    # -E ignores Python environment customization; -s excludes user site packages.
    # A fresh bytecode prefix prevents reading a previously compiled project module.
    process = subprocess.run(
        [sys.executable, '-E', '-s', '-B', '-X', f'pycache_prefix={tmp_path / "bytecode"}',
         '-c', SMOKE, str(APP_DIR)],
        cwd=APP_DIR if working_directory == 'app' else APP_DIR.parent,
        env=env, capture_output=True, text=True, encoding='utf-8', timeout=120,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    assert 'STARTUP_OK ' in process.stdout
