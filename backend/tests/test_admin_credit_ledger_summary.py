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
