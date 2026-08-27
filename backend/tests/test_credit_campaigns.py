from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from credits.credit_campaign_routes import (
    CreditCampaignCreate,
    _template_values,
    _validate_campaign_template,
    admin_create_credit_campaign,
)
from credits.credit_campaigns import calculate_campaign_bonus, maybe_apply_credit_campaign
from credits.web_continue_routes import _split_campaign_continue_token


def test_campaign_fills_only_gap_after_existing_bonuses():
    result = calculate_campaign_bonus(100, "1.5", existing_bonus_credits=10)

    assert result == {
        "target_total_credits": 150,
        "campaign_bonus_credits": 40,
        "existing_bonus_credits": 10,
    }


def test_campaign_rounds_fractional_credit_half_up():
    result = calculate_campaign_bonus(999, "1.5")

    assert result["target_total_credits"] == 1499
    assert result["campaign_bonus_credits"] == 500


def test_campaign_never_removes_a_better_existing_bonus():
    result = calculate_campaign_bonus(100, "1.5", existing_bonus_credits=75)

    assert result["campaign_bonus_credits"] == 0


def test_campaign_award_is_idempotent_for_payment():
    service = MagicMock()
    service.has_transaction_with_reference.return_value = True
    campaign = {"id": 7, "name": "Win back", "multiplier": 2.0}

    with patch("credits.credit_campaigns.active_credit_campaign_for_user", return_value=campaign):
        result = maybe_apply_credit_campaign(
            service,
            userid=18,
            purchased_credits=100,
            purchase_source="razorpay",
            purchase_reference_id="pay_1",
            product_id="credits_100",
            existing_bonus_credits=10,
        )

    assert result["reason"] == "already_applied"
    service.add_credits.assert_not_called()


def test_campaign_eligibility_uses_payment_timestamp():
    service = MagicMock()
    service.has_transaction_with_reference.return_value = True
    paid_at = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    campaign = {"id": 7, "name": "Win back", "multiplier": 2.0}

    with patch(
        "credits.credit_campaigns.active_credit_campaign_for_user",
        return_value=campaign,
    ) as active:
        maybe_apply_credit_campaign(
            service,
            userid=18,
            purchased_credits=100,
            purchase_source="razorpay",
            purchase_reference_id="pay_1",
            product_id="credits_100",
            existing_bonus_credits=10,
            purchase_at=paid_at,
        )

    assert active.call_args.kwargs["now"] == paid_at


@pytest.mark.asyncio
async def test_create_campaign_rejects_inverted_window():
    body = CreditCampaignCreate(
        name="Invalid window",
        multiplier="1.5",
        starts_at="2026-09-02T00:00:00Z",
        ends_at="2026-09-01T00:00:00Z",
        recipient_ids=[18],
        product_ids=["credits_100"],
        status="active",
    )

    with pytest.raises(HTTPException) as exc:
        await admin_create_credit_campaign(
            body,
            current_user=SimpleNamespace(role="admin", userid=1),
        )

    assert exc.value.status_code == 400


def test_campaign_whatsapp_template_requires_multiplier_expiry_and_button():
    template = {
        "components": [
            {"type": "BODY", "text": "Hi {{customer_name}}, get {{multiplier}}x credits before {{expires_at}}"},
            {"type": "BUTTONS", "buttons": [{"type": "URL", "text": "Recharge", "url": "https://astroroshni.com/mobile/?c={{1}}"}]},
        ]
    }

    _validate_campaign_template(template)


def test_campaign_whatsapp_template_accepts_meta_positional_variables():
    template = {
        "components": [
            {"type": "BODY", "text": "Hi {{1}}, get {{2}}x credits before {{3}}"},
            {"type": "BUTTONS", "buttons": [{"type": "URL", "text": "Recharge", "url": "https://astroroshni.com/mobile/?c={{1}}"}]},
        ]
    }

    _validate_campaign_template(template)
    values = _template_values(
        template,
        {
            "name": "September offer",
            "multiplier": "1.5",
            "ends_at": "2026-09-30T18:29:00+00:00",
        },
        {"name": "Tarun"},
        "secure-token.cc7",
    )

    assert values["body.1"] == "Tarun"
    assert values["body.2"] == "1.5"
    assert values["body.3"] == "30 Sep 2026, 11:59 PM IST"
    assert values["button.0.1"] == "secure-token.cc7"


def test_old_ten_percent_template_is_rejected_for_multiplier_campaign():
    template = {
        "components": [
            {"type": "BODY", "text": "Hi {{customer_name}}, get 10% extra"},
            {"type": "BUTTONS", "buttons": [{"type": "URL", "text": "Recharge", "url": "https://astroroshni.com/mobile/?c={{1}}"}]},
        ]
    }

    with pytest.raises(HTTPException) as exc:
        _validate_campaign_template(template)

    assert "multiplier variable" in exc.value.detail


def test_campaign_marker_is_split_without_changing_secure_token():
    token, campaign_id = _split_campaign_continue_token("secure_token-value.cc42.")

    assert token == "secure_token-value"
    assert campaign_id == 42
