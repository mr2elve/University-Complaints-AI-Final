"""Transactional SQLite persistence; AI snapshots are never overwritten by edits."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import pandas as pd
from src.config import DB_PATH, STATUSES
from src.utils import utc_now, validate_text

MIGRATIONS = [(1, '''
CREATE TABLE IF NOT EXISTS complaints (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 save_key TEXT NOT NULL UNIQUE,
 complaint_text TEXT NOT NULL,
 predicted_category TEXT NOT NULL,
 predicted_urgency TEXT NOT NULL,
 predicted_tone TEXT NOT NULL,
 predicted_department TEXT NOT NULL,
 routing_confidence REAL NOT NULL CHECK(routing_confidence BETWEEN 0 AND 1),
 high_urgency_probability REAL NOT NULL CHECK(high_urgency_probability BETWEEN 0 AND 1),
 requires_review INTEGER NOT NULL,
 prediction_json TEXT NOT NULL,
 assigned_department TEXT,
 effective_urgency TEXT NOT NULL,
 status TEXT NOT NULL,
 submitted_at TEXT NOT NULL,
 resolved_at TEXT,
 reviewed_at TEXT,
 admin_notes TEXT NOT NULL DEFAULT '',
 version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS review_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 complaint_id INTEGER NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
 previous_status TEXT, new_status TEXT,
 previous_department TEXT, new_department TEXT,
 previous_urgency TEXT, new_urgency TEXT,
 previous_notes TEXT, review_notes TEXT,
 action TEXT NOT NULL,
 timestamp TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_complaint_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_review_queue ON complaints(requires_review, reviewed_at);
''')]


class ConflictError(ValueError):
    pass


class Database:
    def __init__(self, path=DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.execute('PRAGMA journal_mode=WAL')
            version = con.execute('PRAGMA user_version').fetchone()[0]
            if version > MIGRATIONS[-1][0]:
                raise ValueError('Database is newer than this application.')
            for number, script in MIGRATIONS:
                if number > version:
                    con.executescript(f'BEGIN IMMEDIATE;\n{script}\nPRAGMA user_version={number};\nCOMMIT;')
        self.path.chmod(0o600)

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path, timeout=15)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        try:
            with con:
                yield con
        finally:
            con.close()

    def _insert(self, con, result, key):
        validate_text(result['text'])
        p = result['predictions']
        params = (key, result['text'], p['category'], p['urgency'], p['tone'], p['department'],
                  result['routing_confidence'], result['high_urgency_probability'], int(result['requires_review']),
                  json.dumps(result, ensure_ascii=False), None if result['requires_review'] else p['department'],
                  p['urgency'], 'Pending Review' if result['requires_review'] else 'New', utc_now())
        con.execute('''INSERT INTO complaints
          (save_key, complaint_text, predicted_category, predicted_urgency, predicted_tone, predicted_department,
           routing_confidence, high_urgency_probability, requires_review, prediction_json, assigned_department,
           effective_urgency, status, submitted_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(save_key) DO NOTHING''', params)
        return con.execute('SELECT id FROM complaints WHERE save_key=?', (key,)).fetchone()[0]

    def save(self, result, key):
        with self.connect() as con:
            return self._insert(con, result, key)

    def save_batch(self, results, key):
        with self.connect() as con:
            return [self._insert(con, r, f'{key}:{i}') for i, r in enumerate(results) if 'error' not in r]

    def list(self):
        with self.connect() as con:
            return pd.read_sql_query('SELECT * FROM complaints ORDER BY submitted_at DESC, id DESC', con)

    def get(self, complaint_id):
        with self.connect() as con:
            row = con.execute('SELECT * FROM complaints WHERE id=?', (int(complaint_id),)).fetchone()
        if row is None:
            raise ValueError('Complaint no longer exists.')
        return dict(row)

    def history(self, complaint_id):
        with self.connect() as con:
            return pd.read_sql_query('SELECT * FROM review_history WHERE complaint_id=? ORDER BY id DESC', con, params=(int(complaint_id),))

    def update(self, complaint_id, *, status, department, urgency, notes, expected_version, departments, reviewed=False):
        if status not in STATUSES or department not in [None, *departments] or urgency not in ('high', 'medium', 'low'):
            raise ValueError('Invalid status, urgency, or department.')
        if len(notes) > 10000:
            raise ValueError('Notes exceed 10,000 characters.')
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row = con.execute('SELECT * FROM complaints WHERE id=?', (int(complaint_id),)).fetchone()
            if row is None or row['version'] != expected_version:
                raise ConflictError('This record changed. Reload it before saving your edits.')
            if row['requires_review'] and not row['reviewed_at'] and not reviewed and status in ('Assigned', 'In Progress', 'Resolved', 'Closed'):
                raise ValueError('Complete manual review before advancing this complaint.')
            if (reviewed or status in ('Assigned', 'In Progress')) and not department:
                raise ValueError('Select an assigned department before approval or assignment.')
            now = utc_now()
            resolved_at = (row['resolved_at'] or now) if status in ('Resolved', 'Closed') else None
            con.execute('''UPDATE complaints SET status=?, assigned_department=?, effective_urgency=?,
                admin_notes=?, resolved_at=?, reviewed_at=?, version=version+1 WHERE id=?''',
                (status, department, urgency, notes, resolved_at, now if reviewed else row['reviewed_at'], complaint_id))
            con.execute('''INSERT INTO review_history
                (complaint_id, previous_status, new_status, previous_department, new_department,
                 previous_urgency, new_urgency, previous_notes, review_notes, action, timestamp)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (complaint_id, row['status'], status, row['assigned_department'], department,
                 row['effective_urgency'], urgency, row['admin_notes'], notes, 'review_approved' if reviewed else 'updated', now))

    def delete(self, complaint_id):
        """Maintenance API only; explicitly deletes a complaint and associated audit rows."""
        with self.connect() as con:
            con.execute('DELETE FROM complaints WHERE id=?', (int(complaint_id),))
