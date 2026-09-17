from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path


BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import db
from credits.credit_service import CreditService


class _Cursor:
    def fetchone(self):
        return (0, 0, 0, 0, 0, 100, 0, 0)


class _Connection:
    pass


@contextmanager
def _connection():
    yield _Connection()


def test_credit_ledger_summary_nets_payment_reversals(monkeypatch):
    captured = {}

    def _execute(_conn, sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return _Cursor()

    monkeypatch.setattr(db, "get_conn", _connection)
    monkeypatch.setattr(db, "execute", _execute)

    summary = CreditService().get_search_transaction_summary(
        "2026-07-24",
        "2026-07-24",
    )

    sql = captured["sql"]
    assert "ct.source IN ('google_play_refund', 'razorpay_refund')" in sql
    assert "THEN -ABS(ct.amount)" in sql
    assert "original.reference_id = ct.reference_id" in sql
    assert summary["purchased_credits"] == 0
    assert summary["purchased_amount_inr"] == 0
    assert summary["refund_reversal_credits"] == 100


def test_ledger_feature_sql_uses_indexed_equality_not_full_text():
    from credits.credit_service import ledger_feature_sql, normalize_ledger_feature_filter

    sql, params = ledger_feature_sql("talk_to_tara")
    assert "ct.source = 'feature_usage'" in sql
    assert "ct.reference_id IN" in sql
    assert "starts_with" in sql
    assert "ILIKE" not in sql
    assert "%" not in "".join(str(p) for p in params)
    assert "speech_chat" in params
    assert "speech_chat_minutes" in params
    assert "Talk To Tara" in params
    assert normalize_ledger_feature_filter("Live Chat") == "live_chat"

    try:
        ledger_feature_sql("not_a_real_feature")
        raise AssertionError("expected invalid feature to raise")
    except ValueError:
        pass


def test_credit_ledger_summary_feature_filter_parameter_count(monkeypatch):
    captured = {}

    def _execute(_conn, sql, params):
        captured["sql"] = sql
        captured["params"] = list(params)
        return _Cursor()

    monkeypatch.setattr(db, "get_conn", _connection)
    monkeypatch.setattr(db, "execute", _execute)

    CreditService().get_search_transaction_summary(
        "2026-08-01",
        "2026-08-14",
        feature="standard_chat",
    )

    adapted = db._adapt_query_for_postgres(captured["sql"])
    assert adapted.count("%s") == len(captured["params"])
    assert "starts_with" in captured["sql"]
    assert "chat_question" in captured["params"]
    assert "Standard Chat" in captured["params"]


def test_credit_ledger_summary_query_has_matching_postgres_parameters(monkeypatch):
    captured = {}

    def _execute(_conn, sql, params):
        captured["sql"] = sql
        captured["params"] = list(params)
        return _Cursor()

    monkeypatch.setattr(db, "get_conn", _connection)
    monkeypatch.setattr(db, "execute", _execute)

    CreditService().get_search_transaction_summary(
        "2026-08-01",
        "2026-08-14",
        "Tarun",
        cohort_filter="new_users_bought_in_range",
    )

    adapted = db._adapt_query_for_postgres(captured["sql"])
    assert adapted.count("%s") == len(captured["params"])
    assert "ILIKE '%credits_24%'" not in captured["sql"]


def test_credit_ledger_summary_uses_google_play_inr_snapshot(monkeypatch):
    captured = {}

    def _execute(_conn, sql, params):
        captured["sql"] = sql
        return _Cursor()

    monkeypatch.setattr(db, "get_conn", _connection)
    monkeypatch.setattr(db, "execute", _execute)

    CreditService().get_search_transaction_summary("2026-08-14", "2026-08-14")

    sql = captured["sql"]
    assert '"price_amount_micros"' in sql
    assert '"price_currency"' in sql
    assert "= 'INR'" in sql
    assert "::numeric / 1000000" in sql
