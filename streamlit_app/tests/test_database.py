from copy import deepcopy
import pytest
from src.config import DEPARTMENTS
from src.database import ConflictError, Database
from src.analytics import dashboard_metrics, filter_complaints


def update(db,ident,**kwargs):
    row=db.get(ident)
    values=dict(status='Assigned',department='academic_affairs',urgency='medium',notes='Reviewed by demo operator',expected_version=row['version'],departments=DEPARTMENTS)
    values.update(kwargs)
    db.update(ident,**values)


def test_crud_idempotency_and_audit(db,real_result):
    ident=db.save(real_result,'one')
    assert db.save(real_result,'one')==ident
    assert len(db.list())==1
    original=db.get(ident)['prediction_json']
    update(db,ident,department='faculty_dean_office',urgency='high')
    row=db.get(ident)
    assert row['prediction_json']==original
    assert row['predicted_department']==real_result['predictions']['department']
    assert row['effective_urgency']=='high'
    assert row['assigned_department']=='faculty_dean_office'
    assert db.history(ident).iloc[0].previous_department==real_result['predictions']['department']
    with pytest.raises(ConflictError):update(db,ident,expected_version=1)
    update(db,ident,status='Resolved')
    assert db.get(ident)['resolved_at']
    update(db,ident,status='In Progress')
    assert db.get(ident)['resolved_at'] is None
    assert len(Database(db.path).list())==1
    db.delete(ident)
    assert db.list().empty and db.history(ident).empty


def test_review_preserves_original_decision(db,real_result):
    result=deepcopy(real_result)
    result['requires_review']=True
    result['review_reasons']=['Low prediction confidence']
    ident=db.save(result,'review')
    assert db.get(ident)['assigned_department'] is None
    with pytest.raises(ValueError):update(db,ident,status='Resolved')
    with pytest.raises(ValueError):update(db,ident,reviewed=True,department=None)
    update(db,ident,reviewed=True,urgency='high')
    row=db.get(ident)
    assert row['reviewed_at'] and row['requires_review']==1
    assert db.history(ident).iloc[0].action=='review_approved'
    assert dashboard_metrics(db.list())['review']==0


def test_batch_transaction_and_filters(db,real_result):
    ids=db.save_batch([real_result,{'error':'empty'},real_result],'batch')
    assert len(ids)==2
    assert db.save_batch([real_result,{'error':'empty'},real_result],'batch')==ids
    assert len(db.list())==2
    assert len(filter_complaints(db.list(),search='Сабақ'))==2
    assert filter_complaints(db.list(),search="' OR 1=1 --").empty
    broken=deepcopy(real_result);broken['routing_confidence']=2
    with pytest.raises(Exception):db.save_batch([real_result,broken],'rollback')
    assert len(db.list())==2
