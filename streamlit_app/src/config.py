import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = Path(os.environ.get('COMPLAINT_MODEL_DIR', ROOT / 'model'))
DB_PATH = Path(os.environ.get('COMPLAINT_DB_PATH', ROOT / 'data' / 'complaints.sqlite3'))
TARGETS = ('category', 'urgency', 'tone', 'department')
STATUSES = ('New', 'Pending Review', 'Assigned', 'In Progress', 'Resolved', 'Closed')
MAX_TEXT_LENGTH = 10000
MAX_BATCH_ROWS = 1000


def read_config(model_dir=MODEL_DIR):
    path = Path(model_dir) / 'config.json'
    if not path.exists():
        raise FileNotFoundError(f'Missing {path}. Run scripts/setup_model.py with your exported ZIP.')
    config = json.loads(path.read_text(encoding='utf-8'))
    if config.get('targets') != list(TARGETS):
        raise ValueError('Checkpoint head order must be category, urgency, tone, department.')
    for task, size in zip(TARGETS, (3, 3, 3, 6)):
        mapping = config['label_maps'][task]
        if len(mapping) != size or sorted(mapping.values()) != list(range(size)):
            raise ValueError(f'Invalid label index mapping: {task}')
    if set(config['label_maps']['urgency']) != {'high', 'low', 'medium'}:
        raise ValueError('Expected original urgency taxonomy.')
    for key in ('confidence_threshold', 'urgent_review_threshold'):
        if not 0 <= config[key] <= 1:
            raise ValueError(f'Invalid {key}')
    if config['max_length'] != 96:
        raise ValueError('Expected the notebook token limit of 96.')
    return config

DEPARTMENTS = ('academic_affairs', 'facilities_office', 'faculty_dean_office', 'finance_office', 'security_ombudsperson', 'student_service_center')
