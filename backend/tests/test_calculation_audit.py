import json
from types import SimpleNamespace
from chat import calculation_audit

def test_audit_saves_exact_request_and_response_with_message_link(monkeypatch):
    calls=[]
    monkeypatch.setattr(calculation_audit,'execute',lambda *args: calls.append(args))
    payload={'events':[{'round':1,'requested':{'houses':[10]},'provided':{'windows':[]}}]}
    calculation_audit.store_audit(None,12,payload)
    assert 'ON DELETE CASCADE' in calls[0][1]
    assert calls[1][2][0]==12
    assert json.loads(calls[1][2][1])==payload

def test_missing_audit_returns_empty_without_creating_table(monkeypatch):
    rows=iter([(12,), (None,)])
    monkeypatch.setattr(calculation_audit,'execute',lambda *args: SimpleNamespace(fetchone=lambda:next(rows)))
    assert calculation_audit.read_audit(None,12)=={}

def test_missing_message_returns_none(monkeypatch):
    monkeypatch.setattr(calculation_audit,'execute',lambda *args: SimpleNamespace(fetchone=lambda:None))
    assert calculation_audit.read_audit(None,12) is None

def test_read_audit_returns_recorded_json(monkeypatch):
    payload={'events':[{'round':1,'provided':{'windows':[]}}]}
    rows=iter([(12,),('chat_calculation_audits',),(json.dumps(payload),)])
    monkeypatch.setattr(calculation_audit,'execute',lambda *args: SimpleNamespace(fetchone=lambda:next(rows)))
    assert calculation_audit.read_audit(None,12)==payload


def test_round_endpoint_requires_admin_dependency():
    from chat_history.admin_routes import router, require_admin
    from fastapi import HTTPException
    import pytest
    endpoint=next(r for r in router.routes if r.path=='/admin/chat/information-rounds/{message_id}')
    assert any(dependency.call is require_admin for dependency in endpoint.dependant.dependencies)
    with pytest.raises(HTTPException) as error:
        require_admin(SimpleNamespace(role='user'))
    assert error.value.status_code==403
