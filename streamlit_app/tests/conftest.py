import pytest
from src.config import MODEL_DIR
from src.database import Database

@pytest.fixture(scope='session')
def bundle():
    from src.model_loader import load_model
    if not (MODEL_DIR/'model.pt').exists():
        pytest.skip('Real model artifacts missing; run scripts/setup_model.py to enable integration tests.')
    return load_model()

@pytest.fixture
def db(tmp_path):
    return Database(tmp_path/'test.sqlite3')

@pytest.fixture(scope='session')
def real_result(bundle):
    from src.inference import analyze_complaint
    return analyze_complaint(bundle,'Сабақ кестесі дұрыс жасалмаған. Екі пән бір уақытта тұр.')
