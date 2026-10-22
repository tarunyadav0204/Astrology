from nudge_engine.routes import CampaignUpsertRequest, _validate_campaign_payload
from nudge_engine.sms_channel import (
    PARTNER_PORTRAIT_DLT_TEMPLATE_ID,
    PARTNER_PORTRAIT_TEMPLATE_KEY,
    _dlt_name,
    _india_mobile,
)
from fastapi import HTTPException
from unittest.mock import patch


def _campaign(**overrides):
    payload = {
        "name": "Partner Portrait",
        "title_template": "Partner Portrait",
        "body_template": "Hi {name}",
        "channels": ["sms"],
        "channel_policy": "blast",
        "sms_template": {"key": PARTNER_PORTRAIT_TEMPLATE_KEY},
    }
    payload.update(overrides)
    return CampaignUpsertRequest(**payload)


def test_partner_portrait_sms_campaign_is_stored_as_locked_template():
    fields = _validate_campaign_payload(_campaign())
    assert fields["sms_template_json"] == '{"key": "partner_portrait"}'
    assert PARTNER_PORTRAIT_DLT_TEMPLATE_ID == "1077020640025488277"


def test_sms_campaign_rejects_unapproved_template_configuration():
    try:
        _validate_campaign_payload(_campaign(sms_template={"key": "other"}))
    except HTTPException as exc:
        assert "approved Partner Portrait" in str(exc.detail)
    else:
        raise AssertionError("unapproved SMS DLT template must be rejected")


def test_dlt_variable_and_indian_phone_are_normalized_safely():
    assert _dlt_name("Roshni D.") == "RoshniD"
    assert _dlt_name("नमस्ते") == "there"
    assert _india_mobile("+91 98765 43210") == "919876543210"
    assert _india_mobile("1234567890") is None


def test_sms_configuration_exposes_safe_provider_readiness(monkeypatch):
    monkeypatch.setenv("MTALKZ_API_KEY", "secret")
    monkeypatch.setenv("MTALKZ_SENDER_ID", "ASTROS")
    monkeypatch.setenv("MTALKZ_PE_ID", "pe-123")
    monkeypatch.setenv("MSG91_SMS_AUTHKEY", "secret")
    monkeypatch.setenv("MSG91_SMS_TEMPLATE_ID", "msg91-flow-123")
    from nudge_engine.sms_channel import campaign_sms_configuration

    config = campaign_sms_configuration()
    assert config["primary_provider"] == "mtalkz"
    assert config["fallback_provider"] == "msg91"
    assert config["providers"]["mtalkz"]["sender_id"] == "ASTROS"
    assert "secret" not in str(config)


def test_msg91_is_used_after_mtalkz_rejection(monkeypatch):
    monkeypatch.setenv("MTALKZ_API_KEY", "primary-key")
    monkeypatch.setenv("MTALKZ_SENDER_ID", "ASTROS")
    monkeypatch.setenv("MTALKZ_PE_ID", "pe-123")
    monkeypatch.setenv("MSG91_SMS_AUTHKEY", "fallback-key")
    monkeypatch.setenv("MSG91_SMS_TEMPLATE_ID", "msg91-flow-123")
    from nudge_engine.sms_channel import send_partner_portrait_sms

    with patch("nudge_engine.sms_channel._send_mtalkz", return_value=(False, "MTalkz rejected", {"provider": "mtalkz"})), patch(
        "nudge_engine.sms_channel._send_msg91",
        return_value=(True, None, {"provider": "msg91", "message_id": "request-1"}),
    ):
        ok, error, meta = send_partner_portrait_sms(phone="9876543210", name="Roshni")

    assert ok is True
    assert error is None
    assert meta["provider"] == "msg91"
    assert meta["fallback_from"] == "mtalkz"
