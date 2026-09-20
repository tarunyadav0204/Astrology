"""Opt-in integration tests confined to a disposable local PostgreSQL schema."""
from contextlib import contextmanager
from datetime import datetime, timezone
import os
import uuid
import pytest
from credits import subscription_ledger as ledger
from credits import subscription_admin as admin
from auth import User
from fastapi import HTTPException

@pytest.fixture
def database(monkeypatch):
    if os.getenv('RUN_SUBSCRIPTION_DB_TESTS') != '1':
        pytest.skip('Set RUN_SUBSCRIPTION_DB_TESTS=1 for local PostgreSQL tests')
    import psycopg2
    from dotenv import dotenv_values
    dsn = dotenv_values('.env').get('POSTGRES_DSN')
    assert psycopg2.extensions.parse_dsn(dsn).get('host') in ('/tmp','localhost','127.0.0.1')
    schema = 'test_billing_' + uuid.uuid4().hex
    root = psycopg2.connect(dsn); root.autocommit = True
    root.cursor().execute('CREATE SCHEMA ' + schema)
    @contextmanager
    def connect():
        conn = psycopg2.connect(dsn, options='-c search_path=' + schema)
        try:
            yield conn
        finally:
            conn.close()
    monkeypatch.setattr(ledger,'get_conn',connect)
    monkeypatch.setattr(admin,'get_conn',connect)
    try:
        with connect() as conn:
            conn.cursor().execute('''CREATE TABLE razorpay_subscription_map(razorpay_subscription_id TEXT PRIMARY KEY,userid INT,internal_plan_id INT,product_id TEXT);
CREATE TABLE user_subscriptions(id SERIAL PRIMARY KEY,userid INT,plan_id INT,start_date TIMESTAMP,end_date TIMESTAMP,status TEXT,billing_provider TEXT,razorpay_subscription_id TEXT,cancel_at_period_end BOOLEAN DEFAULT FALSE,google_play_order_id TEXT);
CREATE TABLE users(userid INT PRIMARY KEY,name TEXT,phone TEXT);
CREATE TABLE subscription_plans(plan_id INT PRIMARY KEY,plan_name TEXT,tier_name TEXT,google_play_product_id TEXT,price NUMERIC);
CREATE TABLE play_subscription_token_map(purchase_token TEXT,userid INT,product_id TEXT,latest_order_id TEXT);
CREATE TABLE play_subscription_event_log(google_play_order_id TEXT,userid INT,event_kind TEXT,source TEXT,event_time_millis BIGINT,processed_at TIMESTAMP,purchase_token TEXT);
INSERT INTO users VALUES(435,'Test subscriber','0000');
INSERT INTO subscription_plans VALUES(8,'VIP Platinum','vip_platinum',NULL,100);
INSERT INTO razorpay_subscription_map VALUES('sub_test',435,8,'vip');
INSERT INTO user_subscriptions(userid,plan_id,start_date,end_date,status) VALUES(435,8,'2026-09-08','2026-10-08','active');''')
            conn.commit()
        ledger.ensure_schema()
        yield connect
    finally:
        root.cursor().execute('DROP SCHEMA ' + schema + ' CASCADE'); root.close()

def entity():
    return dict(id='sub_test',status='cancelled',current_start=1788881067,current_end=1791397800,ended_at=1789905366,paid_count=1,notes={'userid':'435','internal_plan_id':'8'})

def test_cancel_repairs_ist_period_preserves_access_and_deduplicates(database):
    event = ledger.receive_event(entity(),'subscription.cancelled',event_id='evt1',event_time=1789905366)
    assert ledger.apply_billing_event(event)['status'] == 'processed'
    assert ledger.receive_event(entity(),'subscription.cancelled',event_id='evt1')['done']
    with database() as conn:
        row = ledger.execute(conn,'SELECT billing_provider,razorpay_subscription_id,cancel_at_period_end,status,end_date FROM user_subscriptions').fetchone()
        assert row == ('razorpay','sub_test',True,'active',datetime(2026,10,8))
    result = admin.overview(page=1,limit=50)
    assert result['subscriptions'][0]['auto_renew'] is False
    assert result['subscriptions'][0]['next_charge_at'] is None
    assert admin.activity(page=1,limit=50)['events'][0]['actor'] == 'unknown'

def test_ambiguous_mapping_never_guesses_and_is_visible(database):
    with database() as conn:
        ledger.execute(conn,"INSERT INTO razorpay_subscription_map VALUES('sub_other',435,8,'vip')"); conn.commit()
    event = ledger.receive_event(entity(),'subscription.cancelled',event_time=1789905366)
    assert ledger.apply_billing_event(event)['status'] == 'needs_attention'
    with database() as conn:
        assert ledger.execute(conn,'SELECT razorpay_subscription_id FROM user_subscriptions').fetchone()[0] is None
    assert admin.overview(page=1,limit=50)['summary']['unresolved_events'] == 1

def test_recovery_idempotent_and_older_activation_cannot_replace_cancel(database):
    ledger.reconcile_razorpay('sub_test',lambda _: entity())
    ledger.reconcile_razorpay('sub_test',lambda _: entity())
    older=entity(); older['status']='active'
    event=ledger.receive_event(older,'subscription.activated',event_time=1788881067)
    assert ledger.is_stale(event)
    assert ledger.apply_billing_event(event)['status'] == 'stale'
    with database() as conn:
        assert ledger.execute(conn,"SELECT COUNT(*) FROM subscription_lifecycle_events WHERE source='provider_recovery'").fetchone()[0] == 1
        assert ledger.execute(conn,'SELECT snapshot FROM subscription_billing_state').fetchone()[0]['status'] == 'cancelled'

def test_provider_read_allows_matching_charged_webhook(database):
    active=entity(); active['status']='active'
    ledger.reconcile_razorpay('sub_test',lambda _: active)
    event=ledger.receive_event(active,'subscription.charged',event_time=1788881067)
    assert not ledger.is_stale(event)

def test_play_snapshot_never_exposes_token(database):
    ledger.record_play_state(435,'vip','secret-token',{'subscriptionState':'SUBSCRIPTION_STATE_CANCELED','expiryTimeMillis':1791397800000,'lineItems':[{'autoRenewingPlan':{'autoRenewEnabled':False}}]})
    with database() as conn:
        row=ledger.execute(conn,'SELECT external_id,snapshot FROM subscription_billing_state').fetchone()
        assert 'secret-token' not in str(row)
        assert row[1]['status']=='cancelled' and row[1]['charge_at'] is None

def test_admin_only_and_cancelled_access_has_no_charge():
    with pytest.raises(HTTPException) as exc:
        admin.admin(User(userid=1,name='Test',phone='000',role='user'))
    assert exc.value.status_code == 403
    row=admin.present({'provider':'razorpay','snapshot':{'status':'cancelled','charge_at':1791397800},'access_until':datetime(2026,10,8),'checked_at':datetime.now(timezone.utc)})
    assert row['next_charge_at'] is None and row['access_until'].tzinfo == timezone.utc

def test_successful_reconciliation_resolves_missing_link_alert(database):
    with database() as conn:
        ledger.execute(conn,"INSERT INTO razorpay_subscription_map VALUES('sub_other',435,8,'vip')"); conn.commit()
    event=ledger.receive_event(entity(),'subscription.cancelled',event_time=1789905366)
    assert ledger.apply_billing_event(event)['issue']
    other=entity(); other.update(id='sub_other',status='created',current_start=None,current_end=None,paid_count=0)
    ledger.reconcile_razorpay('sub_other',lambda _: other)
    assert ledger.reconcile_razorpay('sub_test',lambda _: entity())['issue'] is None
    assert ledger.event_is_done(event['id'])
    assert admin.activity(view='unresolved',page=1,limit=50)['events'] == []


def test_webhook_failure_is_durable_and_retry_succeeds(database,monkeypatch):
    from credits import razorpay_subscription_routes as routes
    payload={'event':'subscription.cancelled','created_at':1789905366,'payload':{'subscription':{'entity':entity()}}}
    monkeypatch.setattr(routes,'_process_razorpay_subscription_webhook_event',lambda _: {'status':'error'})
    with pytest.raises(HTTPException) as exc:
        routes.process_razorpay_subscription_webhook_event(payload,event_id='retry')
    assert exc.value.status_code == 503
    assert admin.activity(view='unresolved',page=1,limit=50)['events'][0]['processing_status'] == 'failed'
    monkeypatch.setattr(routes,'_process_razorpay_subscription_webhook_event',lambda _: {'status':'ok'})
    assert routes.process_razorpay_subscription_webhook_event(payload,event_id='retry')['status'] == 'ok'
    assert routes.process_razorpay_subscription_webhook_event(payload,event_id='retry')['status'] == 'duplicate'
    assert admin.activity(view='unresolved',page=1,limit=50)['events'] == []
