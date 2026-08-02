from __future__ import annotations

import asyncio
import base64
import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi import HTTPException

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from credits import routes
from credits import play_rtdn_worker
import db


class _CreditService:
    def __init__(self, mapped_user=None):
        self.mapped_user = mapped_user
        self.upserts = []
        self.logged = []

    def get_user_id_by_play_purchase_token(self, _purchase_token):
        return self.mapped_user

    def upsert_play_subscription_token(
        self,
        userid,
        purchase_token,
        product_id,
        latest_order_id=None,
    ):
        self.upserts.append((userid, purchase_token, product_id, latest_order_id))
        return True

    def has_processed_play_subscription_event(self, _event_id):
        return False

    def log_play_subscription_event(self, **kwargs):
        self.logged.append(kwargs)
        return True


class _SyncCreditService(_CreditService):
    def __init__(self, *, mapping_succeeds=True):
        super().__init__()
        self.mapping_succeeds = mapping_succeeds
        self.subscriptions = []

    def get_plan_id_by_google_play_product_id(self, _product_id):
        return 3

    def get_latest_subscription_on_platform(self, _userid, _platform, family="vip"):
        return None

    def upsert_play_subscription_token(
        self,
        userid,
        purchase_token,
        product_id,
        latest_order_id=None,
    ):
        super().upsert_play_subscription_token(
            userid,
            purchase_token,
            product_id,
            latest_order_id,
        )
        return self.mapping_succeeds

    def set_user_subscription(
        self,
        userid,
        plan_id,
        start_date,
        end_date,
        **kwargs,
    ):
        self.subscriptions.append((userid, plan_id, start_date, end_date, kwargs))
        return True

    def get_plan_by_internal_id(self, _plan_id):
        return {"tier_name": "VIP Platinum"}

    def get_subscription_tier_name(self, _userid):
        return "VIP Platinum"


class _Cursor:
    def fetchone(self):
        return ("astroroshni", "vip")


class _Connection:
    pass


class _OneTimeCreditService:
    def __init__(self):
        self.logged = []
        self.resolved = []

    def has_processed_play_onetime_event(self, _event_id):
        return False

    def get_user_id_by_play_onetime_purchase_token(self, _purchase_token):
        return 77

    def log_play_onetime_event(self, **kwargs):
        self.logged.append(kwargs)
        return True

    def resolve_pending_play_onetime_event(self, event_id, **kwargs):
        self.resolved.append((event_id, kwargs))
        return True


@contextmanager
def _connection():
    yield _Connection()


def _push_body(payload: dict, message_id: str = "message-1") -> dict:
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    return {"message": {"messageId": message_id, "data": encoded}}


def test_subscription_owner_is_read_from_v2_external_account_identifiers():
    purchase = {
        "externalAccountIdentifiers": {
            "obfuscatedExternalAccountId": "user:435",
        }
    }

    assert routes._userid_from_google_play_subscription_purchase(purchase) == 435


def test_subscription_owner_recovery_persists_token_mapping(monkeypatch):
    service = _CreditService()
    monkeypatch.setattr(routes, "credit_service", service)
    monkeypatch.setattr(
        routes,
        "_fetch_google_play_subscription_purchase",
        lambda *_args, **_kwargs: {
            "externalAccountIdentifiers": {
                "obfuscatedExternalAccountId": "user:435",
            },
            "orderId": "GPA.3392-3365-1829-59452",
        },
    )

    userid = routes._resolve_userid_from_google_play_subscription(
        purchase_token="purchase-token",
        product_id="subscription_vip_platinum",
    )

    assert userid == 435
    assert service.upserts == [
        (
            435,
            "purchase-token",
            "subscription_vip_platinum",
            "GPA.3392-3365-1829-59452",
        )
    ]


def test_rtdn_push_recovers_unknown_subscription_owner_and_syncs(monkeypatch):
    service = _CreditService()
    sync_calls = []
    monkeypatch.setattr(routes, "credit_service", service)
    monkeypatch.setattr(
        routes,
        "_resolve_userid_from_google_play_subscription",
        lambda **_kwargs: 435,
    )
    monkeypatch.setattr(
        routes,
        "_sync_subscription_from_play",
        lambda **kwargs: sync_calls.append(kwargs)
        or {
            "start_date": "2026-07-24",
            "end_date": "2026-08-24",
            "google_play_order_id": "GPA.test",
        },
    )
    body = _push_body(
        {
            "eventTimeMillis": "1784883735490",
            "subscriptionNotification": {
                "purchaseToken": "purchase-token",
                "subscriptionId": "subscription_vip_platinum",
                "notificationType": 4,
            },
        }
    )

    result = asyncio.run(routes.google_play_rtdn_push(body))

    assert result["success"] is True
    assert sync_calls[0]["userid"] == 435
    assert sync_calls[0]["accept_any_payment_state"] is True
    assert service.logged[0]["userid"] == 435


def test_rtdn_push_quarantines_unresolved_subscription_owner_without_retry(monkeypatch):
    service = _CreditService()
    monkeypatch.setattr(routes, "credit_service", service)
    monkeypatch.setattr(
        routes,
        "_resolve_userid_from_google_play_subscription",
        lambda **_kwargs: None,
    )
    body = _push_body(
        {
            "eventTimeMillis": "1784883735490",
            "subscriptionNotification": {
                "purchaseToken": "unknown-token",
                "subscriptionId": "subscription_vip_platinum",
                "notificationType": 4,
            },
        }
    )

    result = asyncio.run(routes.google_play_rtdn_push(body))

    assert result == {"success": True, "ignored": "unresolved_subscription_owner"}
    assert service.logged[0]["userid"] is None
    assert service.logged[0]["event_kind"] == "unresolved_owner"


def test_pull_worker_quarantines_unresolved_subscription_owner(monkeypatch):
    service = _CreditService()
    monkeypatch.setattr(
        play_rtdn_worker,
        "_resolve_userid_from_google_play_subscription",
        lambda **_kwargs: None,
    )

    processed = play_rtdn_worker._process_one(
        payload={
            "eventTimeMillis": "1784883735490",
            "subscriptionNotification": {
                "purchaseToken": "unknown-token",
                "subscriptionId": "subscription_vip_platinum",
                "notificationType": 4,
            },
        },
        message_id="message-unresolved",
        credit_service=service,
    )

    assert processed is True
    assert service.logged[0]["userid"] is None
    assert service.logged[0]["event_kind"] == "unresolved_owner"


def test_pull_worker_uses_same_unknown_subscription_owner_recovery(monkeypatch):
    service = _CreditService()
    sync_calls = []
    monkeypatch.setattr(
        play_rtdn_worker,
        "_resolve_userid_from_google_play_subscription",
        lambda **_kwargs: 435,
    )
    monkeypatch.setattr(
        play_rtdn_worker,
        "_sync_subscription_from_play",
        lambda **kwargs: sync_calls.append(kwargs)
        or {
            "start_date": "2026-07-24",
            "end_date": "2026-08-24",
            "google_play_order_id": "GPA.test",
        },
    )

    processed = play_rtdn_worker._process_one(
        payload={
            "eventTimeMillis": "1784883735490",
            "subscriptionNotification": {
                "purchaseToken": "purchase-token",
                "subscriptionId": "subscription_vip_platinum",
                "notificationType": 4,
            },
        },
        message_id="message-2",
        credit_service=service,
    )

    assert processed is True
    assert sync_calls[0]["userid"] == 435
    assert service.logged[0]["userid"] == 435


def test_pull_worker_one_time_credit_purchase_path_is_unchanged(monkeypatch):
    service = _OneTimeCreditService()
    credit_calls = []
    monkeypatch.setattr(
        play_rtdn_worker,
        "_credit_verified_google_play_purchase",
        lambda **kwargs: credit_calls.append(kwargs) or {"success": True},
    )

    processed = play_rtdn_worker._process_one(
        payload={
            "eventTimeMillis": "1784883735490",
            "oneTimeProductNotification": {
                "purchaseToken": "credit-token",
                "sku": "credits_24",
                "notificationType": 1,
            },
        },
        message_id="credit-message",
        credit_service=service,
    )

    assert processed is True
    assert credit_calls[0]["userid"] == 77
    assert credit_calls[0]["product_id"] == "credits_24"
    assert service.logged
    assert service.resolved


def test_rtdn_push_one_time_credit_purchase_path_is_unchanged(monkeypatch):
    service = _OneTimeCreditService()
    credit_calls = []
    monkeypatch.setattr(routes, "credit_service", service)
    monkeypatch.setattr(
        routes,
        "_credit_verified_google_play_purchase",
        lambda **kwargs: credit_calls.append(kwargs) or {"success": True},
    )
    body = _push_body(
        {
            "eventTimeMillis": "1784883735490",
            "oneTimeProductNotification": {
                "purchaseToken": "credit-token",
                "sku": "credits_24",
                "notificationType": 1,
            },
        },
        message_id="credit-push-message",
    )

    result = asyncio.run(routes.google_play_rtdn_push(body))

    assert result["success"] is True
    assert credit_calls[0]["userid"] == 77
    assert credit_calls[0]["product_id"] == "credits_24"
    assert service.logged
    assert service.resolved


def test_sync_accepts_active_v2_purchase_and_persists_mapping_before_entitlement(monkeypatch):
    service = _SyncCreditService()
    monkeypatch.setattr(routes, "credit_service", service)
    monkeypatch.setattr(db, "get_conn", _connection)
    monkeypatch.setattr(db, "execute", lambda *_args, **_kwargs: _Cursor())
    monkeypatch.setattr(
        routes,
        "_verify_google_play_subscription",
        lambda *_args, **_kwargs: {
            "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
            "startTimeMillis": "1784883735000",
            "expiryTimeMillis": "1787562135000",
            "orderId": "GPA.test",
            "externalAccountIdentifiers": {
                "obfuscatedExternalAccountId": "user:435",
            },
        },
    )

    result = routes._sync_subscription_from_play(
        userid=435,
        product_id="subscription_vip_platinum",
        purchase_token="purchase-token",
    )

    assert result["tier_name"] == "VIP Platinum"
    assert service.upserts
    assert service.subscriptions
    assert service.upserts[0][0] == service.subscriptions[0][0] == 435


def test_sync_does_not_grant_entitlement_when_token_mapping_cannot_persist(monkeypatch):
    service = _SyncCreditService(mapping_succeeds=False)
    monkeypatch.setattr(routes, "credit_service", service)
    monkeypatch.setattr(db, "get_conn", _connection)
    monkeypatch.setattr(db, "execute", lambda *_args, **_kwargs: _Cursor())
    monkeypatch.setattr(
        routes,
        "_verify_google_play_subscription",
        lambda *_args, **_kwargs: {
            "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
            "startTimeMillis": "1784883735000",
            "expiryTimeMillis": "1787562135000",
            "orderId": "GPA.test",
            "externalAccountIdentifiers": {
                "obfuscatedExternalAccountId": "user:435",
            },
        },
    )

    with pytest.raises(HTTPException) as exc_info:
        routes._sync_subscription_from_play(
            userid=435,
            product_id="subscription_vip_platinum",
            purchase_token="purchase-token",
        )

    assert exc_info.value.status_code == 500
    assert service.subscriptions == []


def test_sync_rejects_subscription_owned_by_a_different_user(monkeypatch):
    service = _SyncCreditService()
    monkeypatch.setattr(routes, "credit_service", service)
    monkeypatch.setattr(db, "get_conn", _connection)
    monkeypatch.setattr(db, "execute", lambda *_args, **_kwargs: _Cursor())
    monkeypatch.setattr(
        routes,
        "_verify_google_play_subscription",
        lambda *_args, **_kwargs: {
            "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
            "startTimeMillis": "1784883735000",
            "expiryTimeMillis": "1787562135000",
            "externalAccountIdentifiers": {
                "obfuscatedExternalAccountId": "user:999",
            },
        },
    )

    with pytest.raises(HTTPException) as exc_info:
        routes._sync_subscription_from_play(
            userid=435,
            product_id="subscription_vip_platinum",
            purchase_token="purchase-token",
        )

    assert exc_info.value.status_code == 403
    assert service.upserts == []
    assert service.subscriptions == []


@pytest.mark.parametrize(
    "purchase",
    [
        {"paymentState": 1},
        {"paymentState": 2},
        {"subscriptionState": "SUBSCRIPTION_STATE_ACTIVE"},
        {"subscriptionState": "SUBSCRIPTION_STATE_IN_GRACE_PERIOD"},
        {
            "subscriptionState": "SUBSCRIPTION_STATE_CANCELED",
            "expiryTimeMillis": str(int(time.time() * 1000) + 86400000),
        },
    ],
)
def test_subscription_activation_accepts_valid_v1_and_v2_states(purchase):
    assert routes._subscription_purchase_is_valid_for_activation(purchase)


@pytest.mark.parametrize(
    "purchase",
    [
        {},
        {"subscriptionState": "SUBSCRIPTION_STATE_EXPIRED"},
        {"subscriptionState": "SUBSCRIPTION_STATE_PAUSED"},
        {
            "subscriptionState": "SUBSCRIPTION_STATE_CANCELED",
            "expiryTimeMillis": str(int(time.time() * 1000) - 86400000),
        },
    ],
)
def test_subscription_activation_rejects_non_entitled_v2_states(purchase):
    assert not routes._subscription_purchase_is_valid_for_activation(purchase)
