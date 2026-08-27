from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from credits.credit_service import CreditService
from credits import razorpay_routes
from credits import credit_campaigns
from utils import admin_settings


def test_starter_config_is_admin_controlled(monkeypatch):
    values = {
        "first_purchase_starter_enabled": "false",
        "first_purchase_starter_price_rupees": "31.50",
    }
    monkeypatch.setattr(admin_settings, "get_setting", lambda key: values.get(key))

    config = admin_settings.get_first_purchase_bonus_config()

    assert config["starter_enabled"] is False
    assert config["starter_price_rupees"] == 31.5
    assert config["starter_amount_paise"] == 3150
    assert admin_settings.is_credits_setting_key("first_purchase_starter_enabled") is True
    assert admin_settings.is_credits_setting_key("first_purchase_starter_price_rupees") is True


def test_starter_switch_does_not_depend_on_legacy_bonus_switch(monkeypatch):
    values = {
        "first_purchase_bonus_enabled": "false",
        "first_purchase_starter_enabled": "true",
        "first_purchase_bonus_user_allowlist": "",
    }
    monkeypatch.setattr(admin_settings, "get_setting", lambda key: values.get(key))

    assert admin_settings.is_first_purchase_bonus_enabled() is False
    assert admin_settings.first_purchase_starter_enabled_for_user(123) is True


def test_starter_expiry_is_returned_as_explicit_utc(monkeypatch):
    values = {
        "first_purchase_bonus_enabled": "false",
        "first_purchase_starter_enabled": "true",
        "first_purchase_bonus_user_allowlist": "",
        "first_purchase_bonus_window_minutes": "30",
    }
    monkeypatch.setattr(admin_settings, "get_setting", lambda key: values.get(key))
    service = CreditService()
    monkeypatch.setattr(service, "get_free_chat_question_used", lambda userid: True)
    monkeypatch.setattr(service, "_has_prior_credit_purchase", lambda *args, **kwargs: False)
    monkeypatch.setattr(service, "has_first_purchase_bonus", lambda userid: False)
    monkeypatch.setattr(
        service,
        "_recent_free_chat_question_row",
        lambda userid, minutes: {"id": 7, "created_at": datetime(2026, 8, 14, 10, 0, 0)},
    )

    status = service._first_purchase_starter_base_status(123)

    assert status["eligible"] is True
    assert status["expires_at"] == "2026-08-14T10:30:00+00:00"


def test_hidden_starter_is_not_exposed_to_existing_clients(monkeypatch):
    service = CreditService()
    monkeypatch.setattr(
        service,
        "_first_purchase_bonus_base_status",
        lambda *args, **kwargs: {
            "enabled": True,
            "eligible": True,
            "reason": "eligible",
            "starter_enabled": False,
            "starter_amount_paise": 3100,
            "window_minutes": 30,
            "percent": 20,
            "fixed_credits": 0,
            "max_bonus_credits": 1000,
            "bonus_type": "percent",
            "pack_overrides": {},
        },
    )
    monkeypatch.setattr(
        service,
        "_first_purchase_starter_base_status",
        lambda *args, **kwargs: {
            "enabled": False,
            "eligible": False,
            "reason": "starter_offer_disabled",
            "starter_enabled": False,
            "starter_amount_paise": 3100,
            "window_minutes": 30,
        },
    )
    monkeypatch.setattr(
        service,
        "get_purchase_discount_status",
        lambda *args, **kwargs: {"enabled": False, "eligible": False},
    )

    status = service.get_first_purchase_bonus_status(123)

    assert status["starter_pack"]["enabled"] is False
    assert status["starter_pack"]["eligible"] is False
    assert status["starter_pack"]["reason"] == "starter_offer_disabled"
    assert status["offer_eligible"] is False


def test_starter_is_exposed_when_legacy_bonus_is_disabled(monkeypatch):
    service = CreditService()
    monkeypatch.setattr(
        service,
        "_first_purchase_bonus_base_status",
        lambda *args, **kwargs: {
            "enabled": False,
            "eligible": False,
            "reason": "feature_disabled_or_user_not_allowed",
            "starter_enabled": True,
            "starter_amount_paise": 2400,
            "window_minutes": 30,
            "percent": 20,
            "fixed_credits": 0,
            "max_bonus_credits": 1000,
            "bonus_type": "percent",
            "pack_overrides": {},
        },
    )
    monkeypatch.setattr(
        service,
        "_first_purchase_starter_base_status",
        lambda *args, **kwargs: {
            "enabled": True,
            "eligible": True,
            "reason": "eligible",
            "starter_enabled": True,
            "starter_amount_paise": 2400,
            "window_minutes": 30,
            "expires_at": "2026-08-14T10:30:00+00:00",
        },
    )
    monkeypatch.setattr(
        service,
        "get_purchase_discount_status",
        lambda *args, **kwargs: {"enabled": False, "eligible": False},
    )

    status = service.get_first_purchase_bonus_status(123)

    assert status["enabled"] is True
    assert status["eligible"] is False
    assert status["starter_pack"]["eligible"] is True
    assert status["offer_eligible"] is True


def test_razorpay_catalog_includes_independently_enabled_starter(monkeypatch):
    monkeypatch.setattr(
        razorpay_routes,
        "_first_purchase_starter_is_eligible",
        lambda userid: userid == 123,
    )
    monkeypatch.setattr(
        razorpay_routes.credit_service,
        "list_active_credit_amounts",
        lambda: [50, 100, 250, 999],
    )
    monkeypatch.setattr(
        admin_settings,
        "get_first_purchase_bonus_config",
        lambda: {"starter_amount_paise": 2400},
    )
    monkeypatch.setattr(admin_settings, "is_web_topup_bonus_enabled", lambda: False)
    monkeypatch.setattr(admin_settings, "get_web_topup_bonus_percent", lambda: 0)

    packs = razorpay_routes.get_razorpay_credit_packs(123)

    starter = next(pack for pack in packs if pack["credits"] == 24)
    assert starter["amount_paise"] == 2400
    assert starter["is_first_purchase_offer"] is True


def test_razorpay_catalog_scales_questions_for_credit_campaign(monkeypatch):
    monkeypatch.setattr(razorpay_routes, "_first_purchase_starter_is_eligible", lambda _userid: False)
    monkeypatch.setattr(razorpay_routes.credit_service, "list_active_credit_amounts", lambda: [100])
    monkeypatch.setattr(admin_settings, "is_web_topup_bonus_enabled", lambda: False)
    monkeypatch.setattr(admin_settings, "get_web_topup_bonus_percent", lambda: 0)
    monkeypatch.setattr(
        credit_campaigns,
        "active_credit_campaigns_for_user",
        lambda _userid: [
            {
                "id": 7,
                "name": "Double credits",
                "multiplier": 2.0,
                "starts_at": "2026-08-01T00:00:00Z",
                "ends_at": "2026-09-01T00:00:00Z",
                "product_ids": ["credits_100"],
            }
        ],
    )

    pack = razorpay_routes.get_razorpay_credit_packs(123)[0]

    assert pack["base_questions"] == 4
    assert pack["questions"] == 8
    assert pack["credit_campaign"]["question_count"] == 8
    assert pack["total_credits"] == 200


def test_razorpay_starter_price_uses_admin_config(monkeypatch):
    monkeypatch.setattr(
        admin_settings,
        "get_first_purchase_bonus_config",
        lambda: {"starter_amount_paise": 3750},
    )

    assert razorpay_routes._expected_paise_for_pack(24) == 3750
