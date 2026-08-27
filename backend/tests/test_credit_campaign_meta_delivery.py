from unittest.mock import MagicMock, patch

from nudge_engine.credit_campaign_whatsapp import (
    _delivery_metrics,
    _provider_status,
    _reconcile_pending_meta_statuses,
    extract_meta_whatsapp_status_updates,
    record_meta_whatsapp_status_updates,
)
from whatsapp.messaging import send_whatsapp_template


def _status_payload(status="delivered", *, message_id="wamid.abc", timestamp="1787800000"):
    row = {
        "id": message_id,
        "status": status,
        "timestamp": timestamp,
        "recipient_id": "919999999999",
    }
    if status == "failed":
        row["errors"] = [{"code": 131049, "title": "Message not delivered"}]
    return {
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"field": "messages", "value": {"statuses": [row]}}]}],
    }


def test_template_send_keeps_legacy_tuple_and_can_return_wamid(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "token")
    response = MagicMock(status_code=200, content=b"{}")
    response.json.return_value = {
        "contacts": [{"wa_id": "919999999999"}],
        "messages": [{"id": "wamid.abc"}],
    }
    with patch("whatsapp.messaging.requests.post", return_value=response):
        legacy = send_whatsapp_template(
            to="919999999999",
            phone_number_id="phone-id",
            template_name="credit_offer",
            return_error=True,
        )
        enriched = send_whatsapp_template(
            to="919999999999",
            phone_number_id="phone-id",
            template_name="credit_offer",
            return_error=True,
            return_meta=True,
        )

    assert legacy == (True, None)
    assert enriched == (
        True,
        None,
        {"message_id": "wamid.abc", "wa_id": "919999999999"},
    )


def test_extract_meta_status_webhook():
    updates = extract_meta_whatsapp_status_updates(_status_payload())

    assert len(updates) == 1
    assert updates[0]["message_id"] == "wamid.abc"
    assert updates[0]["status"] == "delivered"
    assert updates[0]["recipient_id"] == "919999999999"


def test_record_meta_status_is_idempotent_notification_db_update():
    connection = MagicMock()
    context = MagicMock()
    context.__enter__.return_value = connection
    cursor = MagicMock(rowcount=1)
    with (
        patch("nudge_engine.credit_campaign_whatsapp.db.get_conn", return_value=context),
        patch("nudge_engine.credit_campaign_whatsapp.ensure_credit_campaign_whatsapp_tables"),
        patch("nudge_engine.credit_campaign_whatsapp.execute", return_value=cursor) as execute,
    ):
        result = record_meta_whatsapp_status_updates(_status_payload("failed"))

    assert result == {"received": 1, "matched": 1, "buffered": 0}
    assert any("meta_failed_at" in call.args[1] for call in execute.call_args_list)
    connection.commit.assert_called_once_with()


def test_status_that_arrives_before_wamid_persistence_is_buffered_and_reconciled():
    connection = MagicMock()
    context = MagicMock()
    context.__enter__.return_value = connection

    def record_execute(_conn, sql, _params=None):
        cursor = MagicMock()
        cursor.rowcount = 0 if "UPDATE credit_campaign_whatsapp_recipients" in sql else 1
        return cursor

    with (
        patch("nudge_engine.credit_campaign_whatsapp.db.get_conn", return_value=context),
        patch("nudge_engine.credit_campaign_whatsapp.ensure_credit_campaign_whatsapp_tables"),
        patch("nudge_engine.credit_campaign_whatsapp.execute", side_effect=record_execute) as execute,
    ):
        result = record_meta_whatsapp_status_updates(_status_payload("sent"))

    assert result == {"received": 1, "matched": 0, "buffered": 1}
    assert any(
        "INSERT INTO credit_campaign_whatsapp_pending_statuses" in call.args[1]
        for call in execute.call_args_list
    )

    updates_time = extract_meta_whatsapp_status_updates(_status_payload("sent"))[0]["occurred_at"]
    pending_cursor = MagicMock()
    pending_cursor.fetchall.return_value = [
        ("wamid.abc", "sent", updates_time, "919999999999", None)
    ]
    update_cursor = MagicMock(rowcount=1)
    delete_cursor = MagicMock(rowcount=1)
    with patch(
        "nudge_engine.credit_campaign_whatsapp.execute",
        side_effect=[pending_cursor, update_cursor, delete_cursor],
    ) as execute:
        matched = _reconcile_pending_meta_statuses(connection, ["wamid.abc"])

    assert matched == 1
    assert "DELETE FROM credit_campaign_whatsapp_pending_statuses" in execute.call_args_list[-1].args[1]


def test_legacy_accepted_rows_remain_visible_without_false_delivery_counts():
    metrics = _delivery_metrics(
        [
            {
                "state": "accepted",
                "meta_message_id": None,
                "meta_accepted_at": None,
                "meta_sent_at": None,
                "meta_delivered_at": None,
                "meta_read_at": None,
                "meta_failed_at": None,
            }
        ]
    )

    assert metrics["accepted"] == 1
    assert metrics["legacy_accepted"] == 1
    assert metrics["sent"] == 0
    assert metrics["delivered"] == 0
    assert metrics["read"] == 0


def test_failed_status_wins_over_an_earlier_sent_receipt():
    assert _provider_status({"meta_sent_at": "earlier", "meta_failed_at": "later"}) == "failed"
