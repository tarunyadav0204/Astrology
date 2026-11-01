import pytest
from fastapi import HTTPException

from credits import credit_grant_routes as module


def _template(*, body="Balance: +{{1}} credits\nCurrent balance: {{2}} credits", url="https://astroroshni.onelink.me/v3R9/q4qx8wk3?af_sub1={{1}}"):
    return {
        "components": [
            {"type": "BODY", "text": body},
            {"type": "BUTTONS", "buttons": [{"type": "URL", "text": "Visit website", "url": url}]},
        ],
    }


def test_credit_grant_template_accepts_body_variables_and_dynamic_url(monkeypatch):
    monkeypatch.setattr(module, "_find_template", lambda *_: _template())
    monkeypatch.setenv("CREDIT_GRANT_WHATSAPP_CHAT_URL", "https://astroroshni.onelink.me/v3R9/q4qx8wk3?af_sub1={{1}}")

    module._validate_grant_template("credit_balance_updated_v3", "en")


def test_credit_grant_template_also_accepts_chat_now_button(monkeypatch):
    template = _template()
    template["components"][1]["buttons"][0]["text"] = "Chat Now"
    monkeypatch.setattr(module, "_find_template", lambda *_: template)
    monkeypatch.setenv("CREDIT_GRANT_WHATSAPP_CHAT_URL", "https://astroroshni.onelink.me/v3R9/q4qx8wk3?af_sub1={{1}}")

    module._validate_grant_template("credit_balance_updated_v3", "en")


def test_credit_grant_template_rejects_extra_body_variable(monkeypatch):
    monkeypatch.setattr(module, "_find_template", lambda *_: _template(body="{{1}} {{2}} {{3}}"))

    with pytest.raises(HTTPException) as exc_info:
        module._validate_grant_template("credit_balance_updated_v3", "en")
    assert "exactly BODY" in str(exc_info.value.detail)
