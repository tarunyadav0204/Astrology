from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from whatsapp.admin_routes import (
    TemplateSendRequest,
    VariableMapping,
    _build_send_components,
    _mapping_preview,
    _resolve_parameters_for_recipient,
    _resolve_recipients,
    _template_dto,
    send_template,
)
from whatsapp.messaging import fetch_whatsapp_message_templates


def _approved_template():
    return {
        "id": "template-1",
        "name": "account_update",
        "language": "en_US",
        "status": "APPROVED",
        "category": "UTILITY",
        "components": [
            {"type": "HEADER", "format": "TEXT", "text": "Hello {{1}}"},
            {"type": "BODY", "text": "Your update is {{update_text}}."},
            {
                "type": "BUTTONS",
                "buttons": [{"type": "URL", "text": "View", "url": "https://example.com/{{1}}"}],
            },
        ],
    }


def test_template_dto_extracts_send_parameters():
    dto = _template_dto(_approved_template())

    assert dto["supported"] is True
    assert [item["key"] for item in dto["variables"]] == [
        "header.1",
        "body.update_text",
        "button.0.1",
    ]


def test_credits_template_suggests_name_and_secure_token_mappings():
    template = _approved_template()
    template["name"] = "credits_web_topup_bonus"
    template["components"][1]["text"] = "Hi {{customer_name}}"
    dto = _template_dto(template)
    suggestions = {
        item["key"]: item["suggested_mapping"] for item in dto["variables"]
    }

    assert suggestions["body.customer_name"] == {
        "source": "user_field",
        "field": "name",
        "fallback": "there",
    }
    assert suggestions["button.0.1"] == {
        "source": "generator",
        "generator": "credits_continue_token",
    }


def test_build_components_supports_named_and_positional_text():
    components = _build_send_components(
        _approved_template(),
        {
            "header.1": "Tarun",
            "body.update_text": "ready",
            "button.0.1": "abc123",
        },
    )

    assert components[0]["parameters"] == [{"type": "text", "text": "Tarun"}]
    assert components[1]["parameters"] == [
        {"type": "text", "text": "ready", "parameter_name": "update_text"}
    ]
    assert components[2]["index"] == "0"


def test_media_header_template_is_not_sendable():
    template = _approved_template()
    template["components"][0]["format"] = "IMAGE"

    assert _template_dto(template)["supported"] is False
    with pytest.raises(HTTPException) as exc:
        _build_send_components(template, {})
    assert "media upload" in exc.value.detail


def test_quick_reply_button_requires_and_builds_payload():
    template = _approved_template()
    template["components"][2]["buttons"] = [
        {"type": "QUICK_REPLY", "text": "Continue"}
    ]
    dto = _template_dto(template)

    assert dto["variables"][-1]["key"] == "button.0.payload"
    components = _build_send_components(
        template,
        {
            "header.1": "Tarun",
            "body.update_text": "ready",
            "button.0.payload": "continue_user_1",
        },
    )
    assert components[-1] == {
        "type": "button",
        "sub_type": "quick_reply",
        "index": "0",
        "parameters": [{"type": "payload", "payload": "continue_user_1"}],
    }


def test_fetch_templates_follows_meta_pagination_and_filters_status(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "secret")
    monkeypatch.setenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "waba-1")
    first = MagicMock(status_code=200)
    first.json.return_value = {
        "data": [_approved_template()],
        "paging": {"next": "https://graph.facebook.com/v22.0/next-page"},
    }
    second = MagicMock(status_code=200)
    second.json.return_value = {
        "data": [{**_approved_template(), "id": "template-2", "status": "PAUSED"}]
    }

    with patch("whatsapp.messaging.requests.get", side_effect=[first, second]) as get:
        rows = fetch_whatsapp_message_templates()

    assert [row["id"] for row in rows] == ["template-1"]
    assert get.call_count == 2


def test_recipient_validation_classifies_linked_phone_only_and_missing():
    connection = MagicMock()
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        (1, "Linked", "+91 90000 00001", "919000000001", "one@example.com"),
        (2, "Phone", "+91 90000 00002", "", ""),
        (3, "Missing", "", "", ""),
    ]

    @contextmanager
    def fake_connection():
        yield connection

    with (
        patch("whatsapp.admin_routes.get_conn", side_effect=fake_connection),
        patch("whatsapp.admin_routes.execute", return_value=cursor),
    ):
        rows = _resolve_recipients([1, 2, 3, 4])

    assert [row["status"] for row in rows] == [
        "linked",
        "phone_only",
        "no_phone",
        "not_found",
    ]


def test_mapping_preview_resolves_each_recipient_independently():
    template = _approved_template()
    recipients = [
        {"user_id": 1, "name": "Asha", "phone": "911", "email": "", "status": "linked"},
        {"user_id": 2, "name": "", "phone": "922", "email": "", "status": "linked"},
    ]
    mappings = {
        "header.1": VariableMapping(source="user_field", field="name", fallback="there"),
        "body.update_text": VariableMapping(
            source="per_user", values={"1": "ready", "2": "pending"}
        ),
        "button.0.1": VariableMapping(source="fixed", value="campaign"),
    }

    preview = _mapping_preview(template, mappings, recipients)

    assert preview[0]["values"]["header.1"] == "Asha"
    assert preview[1]["values"]["header.1"] == "there"
    assert preview[0]["values"]["body.update_text"] == "ready"
    assert all(row["resolved"] for row in preview)


def test_missing_per_user_value_blocks_recipient():
    template = _approved_template()
    recipient = {"user_id": 2, "name": "Asha", "phone": "922", "email": ""}
    mappings = {
        "header.1": VariableMapping(source="user_field", field="name"),
        "body.update_text": VariableMapping(source="per_user", values={"1": "ready"}),
        "button.0.1": VariableMapping(source="fixed", value="campaign"),
    }

    _, missing = _resolve_parameters_for_recipient(
        template, mappings, recipient, generate=False
    )

    assert missing == ["body.update_text"]


def test_user_id_profile_mapping_uses_internal_user_id():
    template = _approved_template()
    recipient = {"user_id": 42, "name": "Asha", "phone": "922", "email": ""}
    mappings = {
        "header.1": VariableMapping(source="user_field", field="userid"),
        "body.update_text": VariableMapping(source="fixed", value="ready"),
        "button.0.1": VariableMapping(source="fixed", value="campaign"),
    }

    values, missing = _resolve_parameters_for_recipient(
        template, mappings, recipient, generate=False
    )

    assert values["header.1"] == "42"
    assert missing == []


def test_secure_generator_is_hidden_in_preview_and_generated_for_send():
    template = _approved_template()
    recipient = {"user_id": 2, "name": "Asha", "phone": "922", "email": ""}
    mappings = {
        "header.1": VariableMapping(source="fixed", value="Hello"),
        "body.update_text": VariableMapping(source="fixed", value="ready"),
        "button.0.1": VariableMapping(
            source="generator", generator="credits_continue_token"
        ),
    }

    preview_values, preview_missing = _resolve_parameters_for_recipient(
        template, mappings, recipient, generate=False
    )
    with (
        patch(
            "credits.web_continue.get_or_create_continue_token", return_value="private-token"
        ),
        patch("credits.web_continue.ensure_continue_link_environment_is_safe"),
    ):
        send_values, send_missing = _resolve_parameters_for_recipient(
            template, mappings, recipient, generate=True
        )

    assert preview_values["button.0.1"] == "Secure value generated at send time"
    assert "private-token" not in preview_values.values()
    assert preview_missing == []
    assert send_values["button.0.1"] == "private-token"
    assert send_missing == []

@pytest.mark.asyncio
async def test_unlinked_recipients_require_explicit_override(monkeypatch):
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "sender-1")
    recipients = [
        {"user_id": 1, "name": "One", "phone": "911", "email": "", "status": "linked", "recipient": "911111111111"},
        {"user_id": 2, "name": "Two", "phone": "922", "email": "", "status": "phone_only", "recipient": "922222222222"},
    ]
    body = TemplateSendRequest(
        user_ids=[1, 2],
        template_name="account_update",
        language="en_US",
        mappings={
            "header.1": {"source": "user_field", "field": "name"},
            "body.update_text": {"source": "fixed", "value": "ready"},
            "button.0.1": {"source": "fixed", "value": "abc123"},
        },
        include_unlinked=False,
    )
    with (
        patch("whatsapp.admin_routes._resolve_recipients", return_value=recipients),
        patch("whatsapp.admin_routes._find_template", return_value=_approved_template()),
        patch("whatsapp.admin_routes.send_whatsapp_template", return_value=(True, None)) as send,
    ):
        result = await send_template(
            body, current_user=SimpleNamespace(role="admin", userid=99)
        )

    assert result["accepted"] == 1
    assert result["skipped"] == 1
    assert send.call_count == 1
