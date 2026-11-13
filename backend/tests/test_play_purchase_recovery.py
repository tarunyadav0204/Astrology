"""Regression coverage for paid starter purchases and replay safety."""
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from credits import routes, play_credit_grant
from utils import payment_failure_alerts

@pytest.fixture
def flow(monkeypatch):
    grants, alerts = [], []
    service = SimpleNamespace(
        get_credited_google_play_order_for_token=lambda *a: None,
        can_redeem_first_purchase_starter=lambda *a: False,
        upsert_play_onetime_token=lambda *a: True,
        has_transaction_with_reference=lambda *a: False,
        apply_purchase_extras=lambda **kw: {},
    )
    monkeypatch.setattr(routes, 'credit_service', service)
    monkeypatch.setattr(routes, 'publish_activity', lambda *a, **kw: None)
    from credits import invoice_service
    monkeypatch.setattr(invoice_service, 'ensure_purchase_invoice_for_reference', lambda *a: None)
    monkeypatch.setattr(payment_failure_alerts, 'notify_payment_failure', lambda **kw: alerts.append(kw))
    monkeypatch.setattr(play_credit_grant, 'grant_verified_order', lambda **kw: grants.append(kw) or {'already_credited': False})
    purchase={'purchaseState':0,'orderId':'GPA.real','obfuscatedExternalAccountId':'user:24867','consumptionState':1}
    monkeypatch.setattr(routes, '_verify_google_play_purchase', lambda *a: purchase)
    def run(**kw):
        return routes._credit_verified_google_play_purchase(**dict(userid=24867,user_phone=None,user_name=None,purchase_token='secret-token',product_id='credits_24',**kw))
    return purchase, grants, alerts, run

def test_paid_starter_is_fulfilled_even_after_offer_expires(flow):
    p, grants, alerts, run=flow
    result=run(order_id_hint='GPA.untrusted')
    assert result['credits_added']==24
    assert grants[0]['order_id']=='GPA.real'
    assert alerts==[]

@pytest.mark.parametrize('state,status', [(2,409),(7,400)])
def test_unpaid_purchase_does_not_grant(flow,state,status):
    p,grants,alerts,run=flow;p['purchaseState']=state
    with pytest.raises(HTTPException) as exc:run()
    assert exc.value.status_code==status
    assert not grants
    if state==2:assert not alerts

def test_foreign_account_cannot_claim_order(flow):
    p,grants,alerts,run=flow;p['obfuscatedExternalAccountId']='user:12'
    with pytest.raises(HTTPException) as exc:run()
    assert exc.value.status_code==403 and not grants

def test_order_hint_cannot_replace_verified_order(flow):
    p,grants,alerts,run=flow;p.pop('orderId')
    with pytest.raises(HTTPException):run(order_id_hint='GPA.fake')
    assert not grants

def test_concurrent_duplicate_returns_success_without_second_grant(flow,monkeypatch):
    p,grants,alerts,run=flow
    monkeypatch.setattr(play_credit_grant,'grant_verified_order',lambda **kw: {'already_credited':True})
    result=run()
    assert result['success'] and result['credits_added']==0

def test_retry_alerts_have_stable_redacted_reference(flow,monkeypatch):
    p,grants,alerts,run=flow
    def fail(*a):raise RuntimeError('Provider unavailable')
    monkeypatch.setattr(routes,'_verify_google_play_purchase',fail)
    for _ in range(2):
        with pytest.raises(HTTPException):run()
    assert alerts[0]['reference_id']==alerts[1]['reference_id']
    assert alerts[0]['reference_id'].startswith('play-token:')
    assert 'secret-token' not in alerts[0]['reference_id']
