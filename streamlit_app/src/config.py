import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL_SUBFOLDER = 'XLMR_Multilingual_University_Complaints'
MODEL_DIR = Path(os.environ.get('COMPLAINT_MODEL_DIR', ROOT / 'model' / 'xlmr' / MODEL_SUBFOLDER))
MODEL_REPO_ID = os.environ.get('COMPLAINT_MODEL_REPO', 'mr2elve/xlmr-university-complaints-multilingual')
MODEL_REVISION = os.environ.get('COMPLAINT_MODEL_REVISION', 'f15eb91b1b494b4ed92978a89b1f628e338b0ce3')
ENCODER_REPO_ID = 'FacebookAI/xlm-roberta-base'
DB_PATH = Path(os.environ.get('COMPLAINT_DB_PATH', ROOT / 'data' / 'complaints.sqlite3'))
TARGETS = ('category', 'urgency', 'tone', 'department')
STATUSES = ('New', 'Pending Review', 'Assigned', 'In Progress', 'Resolved', 'Closed')
MAX_TEXT_LENGTH = 10000
MAX_BATCH_ROWS = 1000


def read_config(model_dir=MODEL_DIR):
    path = Path(model_dir) / 'config.json'
    if not path.exists():
        raise FileNotFoundError(f'Missing {path}. Run python scripts/setup_model.py to download the trained export.')
    config = json.loads(path.read_text(encoding='utf-8'))
    if (config.get('architecture') != 'MultiTaskXLMR'
            or config.get('base_model') != ENCODER_REPO_ID
            or config.get('encoder_model_name') != ENCODER_REPO_ID
            or config.get('pooling') != 'masked_mean'):
        raise ValueError('Expected the verified MultiTaskXLMR masked-mean XLM-R export; old KazRoBERTa files are incompatible.')
    tasks = config.get('tasks', [])
    if len(tasks) != len(TARGETS) or set(tasks) != set(TARGETS):
        raise ValueError('Checkpoint tasks must contain category, urgency, tone, department once each.')
    for task in tasks:
        names = config['label_names'][task]
        if not names or any(not isinstance(n, str) or not n for n in names) or len(set(names)) != len(names):
            raise ValueError(f'Invalid ordered labels: {task}')
        mapping = {name: index for index, name in enumerate(names)}
        if (config['label2id'][task] != mapping
                or config['id2label'][task] != {str(i): n for n, i in mapping.items()}):
            raise ValueError(f'Invalid label index mapping: {task}')
    if set(config['label_names']['urgency']) != {'high', 'low', 'medium'}:
        raise ValueError('Urgency labels are incompatible with the existing routing policy.')
    if set(config['label_names']['department']) != set(DEPARTMENTS):
        raise ValueError('Department labels are incompatible with the existing human-review workflow.')
    if type(config.get('max_length')) is not int or not 1 <= config['max_length'] <= 512:
        raise ValueError('Invalid max_length for XLM-RoBERTa.')
    if not isinstance(config.get('dropout'), (int, float)) or not 0 <= config['dropout'] < 1:
        raise ValueError('Invalid dropout.')
    # Adapt the new export to the app contract without modifying the downloaded JSON.
    # Routing policy is application-owned: this export contains no policy settings.
    config['targets'] = tasks
    config['label_maps'] = config['label2id']
    config.update(confidence_threshold=.75, urgent_review_threshold=.30,
                  sla_hours={'high': 4, 'medium': 24, 'low': 72})
    return config

DEPARTMENTS = ('academic_affairs', 'facilities_office', 'faculty_dean_office', 'finance_office', 'security_ombudsperson', 'student_service_center')
