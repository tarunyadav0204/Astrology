"""Regeneration quotes preserve the original report and do not charge credits."""
import json
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from next_chapter import customer


def setup_db(monkeypatch, source, saved=None):
    calls = []
    monkeypatch.setattr(customer, 'get_conn', lambda: nullcontext(SimpleNamespace(commit=lambda: None)))
    def execute(conn, sql, params):
        calls.append((sql, params))
        result = source if 'SELECT request_json' in sql else ((saved,) if saved else None)
        return SimpleNamespace(fetchone=lambda: result)
    monkeypatch.setattr(customer, 'execute', execute)
    monkeypatch.setattr(customer, 'owned_birth', lambda chart, user: {'name': 'Native', 'id': chart})
    monkeypatch.setattr(customer, 'price', lambda user: (63, 200))
    return calls


def request_data():
    return {'chart_id': 17, 'cache_key': 'original', 'as_of': '2025-01-01T00:00:00+00:00',
            'selection': 'current', 'language': 'hi', 'spine': {'antardasha': {'start_at': '2024-01-01'}}}


def test_regeneration_uses_admin_price_and_preserves_selected_period(monkeypatch):
    original = request_data()
    calls = setup_db(monkeypatch, (json.dumps(original), 'completed'))
    quote = customer.regeneration_quote('chapter_old', 3)
    assert quote['credit_cost'] == 63 and quote['credits'] == 200
    payload = json.loads(next(params[2] for sql, params in calls if 'INSERT INTO next_chapter_quotes' in sql))
    for key in ('as_of', 'selection', 'language', 'spine'):
        assert payload[key] == original[key]
    assert payload['cache_key'] == 'original:regenerate:chapter_old'
    assert all('UPDATE' not in sql and 'credit_transactions' not in sql for sql, _ in calls)
    assert calls[0][1] == ('chapter_old', 3)


def test_repeat_click_returns_existing_regeneration(monkeypatch):
    setup_db(monkeypatch, (json.dumps(request_data()), 'completed'), saved='chapter_new')
    assert customer.regeneration_quote('chapter_old', 3)['saved_job_id'] == 'chapter_new'


@pytest.mark.parametrize('source,code', [(None,404), ((json.dumps(request_data()),'processing'),409)])
def test_missing_or_in_progress_report_cannot_regenerate(monkeypatch, source, code):
    calls = setup_db(monkeypatch, source)
    with pytest.raises(HTTPException) as exc:
        customer.regeneration_quote('chapter_old', 3)
    assert exc.value.status_code == code
    assert not any('INSERT' in sql for sql, _ in calls)
