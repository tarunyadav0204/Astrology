from contextlib import contextmanager
from types import SimpleNamespace
import sqlite3

import pytest
import db
from credits import chart_chat, entitlements
from credits.credit_service import CreditService, ledger_feature_sql


@pytest.fixture
def settings_db(monkeypatch):
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE credit_settings (setting_key TEXT PRIMARY KEY, setting_value INTEGER, discount INTEGER, description TEXT, updated_at TEXT)')
    @contextmanager
    def connection():
        yield conn
    monkeypatch.setattr(db, 'get_conn', connection)
    monkeypatch.setattr(db, 'execute', lambda conn, sql, params=(): conn.execute(sql, params))
    yield conn
    conn.close()


def test_unseeded_default_admin_update_and_discount_roundtrip(settings_db, monkeypatch):
    service = CreditService.__new__(CreditService)
    monkeypatch.setattr(service, 'get_subscription_discount_percent', lambda _: 0)
    monkeypatch.setattr(chart_chat, 'chart_chat_is_free', lambda _: False)
    user = SimpleNamespace(userid=42, role='user')
    assert chart_chat.chart_chat_cost(service, user) == 2
    assert service.get_credit_setting('instant_chat_cost') == 1
    assert service.update_credit_setting('chart_chat_cost', 7, discount=None)
    assert chart_chat.chart_chat_cost(service, user) == 7
    assert service.update_credit_setting('chart_chat_cost', 7, discount=3)
    assert chart_chat.chart_chat_cost(service, user) == 3
    listed = {row['key']: row for row in service.get_all_credit_settings()}
    assert listed['chart_chat_cost']['value'] == 7
    assert listed['chart_chat_cost']['discount'] == 3
    assert 'Astrologer License' in listed['chart_chat_cost']['description']


@pytest.mark.parametrize('role,entitlement_rows,expected', [
    ('user', [('astrologer_tools',)], 0),
    ('user', [], 2),  # expired/inactive licenses are excluded by the DB predicate
    ('user', [('pandit_desk',)], 2),
    ('admin', [], 0),
])
def test_license_is_authoritative_and_only_astrologer_access_is_free(monkeypatch, role, entitlement_rows, expected):
    @contextmanager
    def connection(): yield object()
    monkeypatch.setattr(entitlements, 'get_conn', connection)
    def execute(_, sql, params):
        assert "us.status = 'active'" in sql
        assert 'us.end_date >= CURRENT_DATE' in sql
        assert params == (42,)
        return SimpleNamespace(fetchall=lambda: entitlement_rows)
    monkeypatch.setattr(entitlements, 'execute', execute)
    service = SimpleNamespace(get_credit_setting=lambda key: 2, get_effective_cost=lambda *args: 2)
    assert chart_chat.chart_chat_cost(service, SimpleNamespace(userid=42, role=role)) == expected


def test_licensed_user_needs_no_paid_pricing_lookup(monkeypatch):
    monkeypatch.setattr(chart_chat, 'chart_chat_is_free', lambda _: True)
    assert chart_chat.chart_chat_cost(object(), SimpleNamespace(userid=42)) == 0


def test_chart_chat_has_separate_ledger_filter():
    _, params = ledger_feature_sql('chart_chat')
    assert 'chart_chat' in params
    assert 'instant_chat' not in params
