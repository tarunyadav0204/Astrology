from __future__ import annotations

import sys
import json
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi import HTTPException

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from utils import payment_failure_alerts
from credits import routes, razorpay_routes
from credits.credit_service import CreditService
import db


def test_payment_failure_email_uses_fixed_ops_recipients_and_redacts_sensitive_metadata(monkeypatch):
    sent = {}
    marked = []
    monkeypatch.delenv("PAYMENT_FAILURE_ALERT_EMAILS", raising=False)
    monkeypatch.setattr(payment_failure_alerts, "_claim_alert", lambda *_args: 42)
    monkeypatch.setattr(
        payment_failure_alerts,
        "_mark_delivery",
        lambda alert_id, ok: marked.append((alert_id, ok)),
    )
    monkeypatch.setattr(
        payment_failure_alerts,
        "send_plain_text_email",
        lambda recipients, subject, body: sent.update(
            recipients=recipients,
            subject=subject,
            body=body,
        )
        or True,
    )

    ok = payment_failure_alerts._deliver_payment_failure_alert(
        {
            "provider": "razorpay",
            "stage": "credit_grant",
            "userid": 435,
            "reference_id": "pay_test",
            "product_id": "credits_100",
            "error_code": "credits_not_saved",
            "detail": "DB update failed",
            "metadata": {
                "order_id": "order_test",
                "purchase_token": "must-not-appear",
                "signature": "must-not-appear",
            },
        }
    )

    assert ok is True
    assert sent["recipients"] == [
        "tarun.yadav@gmail.com",
        "anilasnani@gmail.com",
    ]
    assert "razorpay" in sent["subject"]
    assert "pay_test" in sent["body"]
    assert "order_test" in sent["body"]
    assert "must-not-appear" not in sent["body"]
    assert marked == [(42, True)]


def test_payment_failure_email_redacts_google_purchase_token_from_http_error(monkeypatch):
    sent = {}
    token = "eljjkhgcgdegbjfcplgmamfd.AO-J1OyJXv5qDBgLns1RXETfzGxpxD-zNO2rDdVCZ8zrjtB_Gg0"
    monkeypatch.setattr(payment_failure_alerts, "_claim_alert", lambda *_args: 43)
    monkeypatch.setattr(payment_failure_alerts, "_mark_delivery", lambda *_args: None)
    monkeypatch.setattr(
        payment_failure_alerts,
        "send_plain_text_email",
        lambda recipients, subject, body: sent.update(body=body) or True,
    )

    ok = payment_failure_alerts._deliver_payment_failure_alert(
        {
            "provider": "google_play",
            "stage": "credit_verify",
            "userid": 73,
            "reference_id": None,
            "product_id": "credits_100",
            "error_code": "HttpError",
            "detail": (
                "HttpError 500 requesting "
                "https://androidpublisher.googleapis.com/androidpublisher/v3/"
                f"applications/com.astroroshni.mobile/purchases/products/credits_100/tokens/{token}?alt=json"
            ),
        }
    )

    assert ok is True
    assert token not in sent["body"]
    assert "/tokens/?REDACTED?" in sent["body"]


def test_duplicate_payment_failure_does_not_send_email(monkeypatch):
    calls = []
    monkeypatch.setattr(payment_failure_alerts, "_claim_alert", lambda *_args: 0)
    monkeypatch.setattr(
        payment_failure_alerts,
        "send_plain_text_email",
        lambda *_args, **_kwargs: calls.append(True) or True,
    )

    ok = payment_failure_alerts._deliver_payment_failure_alert(
        {
            "provider": "google_play",
            "stage": "credit_verify",
            "userid": 435,
            "reference_id": "GPA.test",
            "product_id": "credits_100",
            "error_code": "http_500",
            "detail": "failed",
        }
    )

    assert ok is False
    assert calls == []


def test_google_play_credit_verify_failure_queues_operational_alert(monkeypatch):
    alerts = []
    monkeypatch.setattr(
        payment_failure_alerts,
        "notify_payment_failure",
        lambda **kwargs: alerts.append(kwargs),
    )
    monkeypatch.setattr(
        routes,
        "_verify_google_play_purchase",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("Play unavailable")),
    )

    with pytest.raises(HTTPException):
        routes._credit_verified_google_play_purchase(
            userid=435,
            user_phone=None,
            user_name=None,
            purchase_token="purchase-token",
            product_id="credits_100",
            order_id_hint="GPA.test",
        )

    assert alerts[0]["provider"] == "google_play"
    assert alerts[0]["stage"] == "credit_verify"
    assert alerts[0]["reference_id"] == "GPA.test"


def test_already_credited_google_play_token_skips_provider_verification(monkeypatch):
    verify_calls = []
    monkeypatch.setattr(
        routes.credit_service,
        "get_credited_google_play_order_for_token",
        lambda userid, token, product_id: "GPA.already-credited",
    )
    monkeypatch.setattr(
        routes.credit_service,
        "apply_purchase_extras",
        lambda **_kwargs: {},
    )
    monkeypatch.setattr(
        routes,
        "_verify_google_play_purchase",
        lambda *_args, **_kwargs: verify_calls.append(True),
    )

    result = routes._credit_verified_google_play_purchase(
        userid=73,
        user_phone=None,
        user_name=None,
        purchase_token="restored-purchase-token",
        product_id="credits_100",
        order_id_hint=None,
    )

    assert result["success"] is True
    assert result["message"] == "Already credited"
    assert result["credits_added"] == 0
    assert result["order_id"] == "GPA.already-credited"
    assert verify_calls == []


def test_credited_google_play_order_is_resolved_by_exact_token_and_product(monkeypatch):
    token = "existing-play-token"
    rows = [
        (
            "GPA.wrong-product",
            json.dumps({"purchase_token": token, "product_id": "credits_50"}),
        ),
        (
            "GPA.correct",
            json.dumps({"purchase_token": token, "product_id": "credits_100"}),
        ),
    ]

    class FakeCursor:
        def fetchall(self):
            return rows

    @contextmanager
    def fake_get_conn():
        yield object()

    def fake_execute(_conn, _sql, params):
        assert params == (73, f"%{token}%")
        return FakeCursor()

    monkeypatch.setattr(db, "get_conn", fake_get_conn)
    monkeypatch.setattr(db, "execute", fake_execute)

    order_id = CreditService().get_credited_google_play_order_for_token(
        73,
        token,
        "credits_100",
    )

    assert order_id == "GPA.correct"


def test_razorpay_credit_grant_failure_queues_operational_alert(monkeypatch):
    alerts = []
    monkeypatch.setattr(
        payment_failure_alerts,
        "notify_payment_failure",
        lambda **kwargs: alerts.append(kwargs),
    )

    result = razorpay_routes._process_captured_payment(
        {
            "id": "pay_test",
            "order_id": "order_test",
            "status": "captured",
            "amount": 1,
            "notes": {
                "userid": "435",
                "credits": "100",
                "product_id": "credits_100",
            },
        }
    )

    assert result["success"] is False
    assert alerts[0]["provider"] == "razorpay"
    assert alerts[0]["reference_id"] == "pay_test"
    assert alerts[0]["error_code"] == "payment_amount_mismatch"
