from __future__ import annotations

import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from credits.credit_service import CreditService
from credits import razorpay_routes
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
        "get_purchase_discount_status",
        lambda *args, **kwargs: {"enabled": False, "eligible": False},
    )

    status = service.get_first_purchase_bonus_status(123)

    assert status["starter_pack"]["enabled"] is False
    assert status["starter_pack"]["eligible"] is False
    assert status["starter_pack"]["reason"] == "starter_offer_disabled"
    assert status["offer_eligible"] is False


def test_razorpay_starter_price_uses_admin_config(monkeypatch):
    monkeypatch.setattr(
        admin_settings,
        "get_first_purchase_bonus_config",
        lambda: {"starter_amount_paise": 3750},
    )

    assert razorpay_routes._expected_paise_for_pack(24) == 3750
