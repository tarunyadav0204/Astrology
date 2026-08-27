from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from credits.credit_campaign_routes import (
    CreditCampaignCreate,
    CreditCampaignSendBody,
    _template_values,
    _validate_campaign_template,
    admin_credit_campaign_recipient_report,
    admin_create_credit_campaign,
    admin_send_credit_campaign_whatsapp,
)
from credits.credit_campaigns import (
    calculate_campaign_bonus,
    calculate_campaign_question_count,
    get_credit_campaign_recipient_report,
    maybe_apply_credit_campaign,
)
from credits.web_continue_routes import (
    _split_attributed_continue_token,
    _split_campaign_continue_token,
)


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


@pytest.mark.parametrize(
    ("base_questions", "multiplier", "expected"),
    [(4, "2", 8), (11, "1.5", 17), (45, "1.5", 68)],
)
def test_campaign_scales_displayed_question_count_half_up(base_questions, multiplier, expected):
    assert calculate_campaign_question_count(base_questions, multiplier) == expected


def test_campaign_never_removes_a_better_existing_bonus():
    result = calculate_campaign_bonus(100, "1.5", existing_bonus_credits=75)

    assert result["campaign_bonus_credits"] == 0


@pytest.mark.asyncio
async def test_admin_campaign_recipient_report_returns_clicked_and_purchased_users():
    campaign = {
        "id": 3,
        "name": "Double credits",
        "summary": {"recipients": 2, "opened": 1, "buyers": 1},
    }
    recipients = [
        {"userid": 18, "name": "Asha", "clicked": True, "purchased": True},
        {"userid": 42, "name": "Ravi", "clicked": False, "purchased": False},
    ]
    with (
        patch("credits.credit_campaign_routes.get_credit_campaign", return_value=campaign),
        patch(
            "credits.credit_campaign_routes.get_credit_campaign_recipient_report",
            return_value=recipients,
        ),
        patch("nudge_engine.connections.assert_explicit_isolated_database_configuration"),
        patch(
            "nudge_engine.credit_campaign_whatsapp.get_credit_campaign_whatsapp_delivery_report",
            return_value={
                "job": {"job_id": "job-1"},
                "metrics": {"accepted": 1, "delivered": 1, "read": 0},
                "recipients": {
                    18: {
                        "send_state": "accepted",
                        "meta_status": "delivered",
                        "meta_tracking_available": True,
                    }
                },
            },
        ),
    ):
        result = await admin_credit_campaign_recipient_report(
            3,
            current_user=SimpleNamespace(role="admin", userid=1),
        )

    assert result["campaign"] == campaign
    assert result["recipients"][0]["meta_status"] == "delivered"
    assert result["recipients"][1]["meta_tracking_available"] is False
    assert result["delivery"]["metrics"]["delivered"] == 1


@pytest.mark.asyncio
async def test_admin_campaign_recipient_report_preserves_legacy_status_without_delivery_db():
    campaign = {
        "id": 2,
        "name": "Historical offer",
        "summary": {"recipients": 1, "notified": 1, "opened": 1, "buyers": 0},
    }
    recipients = [{
        "userid": 18,
        "name": "Asha",
        "message_status": "accepted",
        "message_error": None,
        "notified_at": "2026-01-01T00:00:00+00:00",
        "clicked": True,
        "purchased": False,
    }]
    with (
        patch("credits.credit_campaign_routes.get_credit_campaign", return_value=campaign),
        patch(
            "credits.credit_campaign_routes.get_credit_campaign_recipient_report",
            return_value=recipients,
        ),
        patch(
            "nudge_engine.connections.assert_explicit_isolated_database_configuration",
            side_effect=RuntimeError("not configured"),
        ),
    ):
        result = await admin_credit_campaign_recipient_report(
            2,
            current_user=SimpleNamespace(role="admin", userid=1),
        )

    assert result["recipients"][0]["meta_status"] == "accepted"
    assert result["recipients"][0]["meta_tracking_available"] is False
    assert result["recipients"][0]["accepted_at"] == "2026-01-01T00:00:00+00:00"
    assert result["delivery"] == {"job": None, "metrics": {}}


def test_campaign_recipient_report_reads_replica_and_maps_purchase_status():
    read_conn = MagicMock()
    read_context = MagicMock()
    read_context.__enter__.return_value = read_conn
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        (18, "Asha", "+919999999999", "accepted", None, "sent", "clicked", 2, "first", "latest", 150, 50),
    ]

    with (
        patch("nudge_engine.connections.get_audience_conn", return_value=read_context) as get_replica,
        patch("credits.credit_campaigns.execute", return_value=cursor),
    ):
        rows = get_credit_campaign_recipient_report(3)

    get_replica.assert_called_once_with()
    assert rows[0]["clicked"] is True
    assert rows[0]["purchased"] is True
    assert rows[0]["purchase_count"] == 2
    assert rows[0]["campaign_bonus_credits"] == 50


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


def test_nudge_campaign_marker_is_split_without_changing_secure_token():
    token, credit_campaign_id, nudge_campaign_id = _split_attributed_continue_token(
        "secure_token-value.nc17."
    )

    assert token == "secure_token-value"
    assert credit_campaign_id is None
    assert nudge_campaign_id == 17


@pytest.mark.asyncio
async def test_campaign_whatsapp_send_only_enqueues_isolated_worker_tasks():
    campaign = {
        "id": 7,
        "name": "September offer",
        "multiplier": 1.5,
        "starts_at": "2026-01-01T00:00:00+00:00",
        "ends_at": "2099-01-01T00:00:00+00:00",
        "status": "active",
    }
    template = {
        "name": "credit_multiplier_campaign",
        "language": "en",
        "components": [
            {"type": "BODY", "text": "Hi {{1}}, get {{2}}x credits before {{3}}"},
            {"type": "BUTTONS", "buttons": [{"type": "URL", "text": "Recharge", "url": "https://astroroshni.com/mobile/?c={{1}}"}]},
        ],
    }
    user_ids = list(range(1, 26))
    tokens = {uid: f"token-{uid}" for uid in user_ids}
    queued_job = {
        "job_id": "job-1",
        "campaign_id": 7,
        "status": "queued",
        "total": 25,
        "accepted": 0,
        "failed": 0,
        "skipped": 0,
    }

    with (
        patch("credits.credit_campaign_routes.get_credit_campaign", return_value=campaign),
        patch("credits.credit_campaign_routes.ensure_continue_link_environment_is_safe"),
        patch("credits.credit_campaign_routes._phone_number_id", return_value="phone-id"),
        patch("credits.credit_campaign_routes._find_template", return_value=template),
        patch("credits.credit_campaign_routes.get_campaign_recipient_ids", return_value=user_ids),
        patch("credits.credit_campaign_routes.get_or_create_continue_tokens", return_value=tokens),
        patch("credits.credit_campaign_routes._save_campaign_template"),
        patch("nudge_engine.connections.assert_explicit_isolated_database_configuration"),
        patch("nudge_engine.task_queue.nudge_tasks_enabled", return_value=True),
        patch("nudge_engine.task_queue.nudge_tasks_are_isolated", return_value=True),
        patch("nudge_engine.task_queue.enqueue_nudge_task", return_value=True) as enqueue,
        patch("nudge_engine.credit_campaign_whatsapp.active_credit_campaign_whatsapp_job", return_value=None),
        patch("nudge_engine.credit_campaign_whatsapp.create_credit_campaign_whatsapp_job", return_value=queued_job),
        patch("nudge_engine.credit_campaign_whatsapp.set_job_enqueue_result", return_value=queued_job),
        patch("credits.credit_campaign_routes.uuid.uuid4", return_value=SimpleNamespace(hex="job-1")),
        patch.dict("os.environ", {"WHATSAPP_CAMPAIGN_BATCH_SIZE": "10"}),
    ):
        result = await admin_send_credit_campaign_whatsapp(
            7,
            CreditCampaignSendBody(
                template_name="credit_multiplier_campaign",
                language="en",
            ),
            current_user=SimpleNamespace(role="admin", userid=1),
        )

    assert result["job"]["status"] == "queued"
    assert enqueue.call_count == 3
    first_payload = enqueue.call_args_list[0].kwargs["payload"]
    assert first_payload["recipients"][0] == {"user_id": 1, "secure_token": "token-1"}
