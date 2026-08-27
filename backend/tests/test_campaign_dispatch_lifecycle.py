from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from nudge_engine.campaigns import _dispatch_one_campaign, _snapshot_campaign_batch


class _FakeConn:
    def commit(self):
        return None

    def rollback(self):
        return None


def test_queued_campaign_is_not_marked_sent_before_worker_finishes(monkeypatch):
    updates = []

    monkeypatch.setenv("NUDGE_CAMPAIGN_REQUIRE_TASKS", "true")
    with (
        patch(
            "nudge_engine.campaigns.resolve_campaign_audience",
            return_value=[101, 102, 103],
        ),
        patch(
            "nudge_engine.campaigns.db.update_campaign",
            side_effect=lambda _conn, _campaign_id, **fields: updates.append(fields) or 1,
        ),
        patch(
            "nudge_engine.campaigns.db.get_campaign",
            return_value={"id": 42, "status": "sending"},
        ),
        patch("nudge_engine.task_queue.nudge_tasks_enabled", return_value=True),
        patch("nudge_engine.task_queue.nudge_tasks_are_isolated", return_value=True),
        patch(
            "nudge_engine.task_queue.nudge_tasks_target_base_url",
            return_value="https://worker.example.com",
        ),
        patch("nudge_engine.task_queue.enqueue_nudge_task", return_value=True),
    ):
        result = _dispatch_one_campaign(
            _FakeConn(),
            {
                "id": 42,
                "status": "draft",
                "audience_filter": {
                    "type": "user_ids",
                    "user_ids": [101, 102, 103],
                },
            },
        )

    assert result["queued"] is True
    assert result["users_selected"] == 3
    assert result["users_targeted"] == 3
    assert result["status"] == "sending"
    assert updates[0]["status"] == "sending"
    assert all(update.get("status") != "sent" for update in updates)


def test_template_secure_links_are_generated_in_worker_batch_with_click_attribution():
    stored = []

    @contextmanager
    def fake_conn():
        yield MagicMock()

    campaign = {
        "id": 42,
        "title_template": "Offer",
        "body_template": "Open your offer",
        "question_template": "",
        "channels": ["whatsapp"],
        "channel_policy": "blast",
        "landing_screen": "chat",
        "whatsapp_template": {
            "name": "credit_offer",
            "language": "en",
            "include_unlinked": False,
            "template": {
                "components": [
                    {"type": "BODY", "text": "Hi {{1}}"},
                    {"type": "BUTTONS", "buttons": [{"type": "URL", "url": "https://astroroshni.com/mobile/?c={{1}}"}]},
                ]
            },
            "mappings": {
                "body.1": {"source": "user_field", "field": "name", "fallback": "there"},
                "button.0.1": {"source": "generator", "generator": "credits_continue_token"},
            },
        },
    }
    with (
        patch("nudge_engine.campaigns.db.get_read_conn", side_effect=fake_conn),
        patch("nudge_engine.campaigns.db.get_conn", side_effect=fake_conn),
        patch("nudge_engine.campaigns.resolve_params_for_users", return_value={7: {}}),
        patch(
            "nudge_engine.campaigns._resolve_delivery_endpoints",
            return_value={7: {"name": "Asha", "phone": "919999999999", "whatsapp_wa_id": "919999999999"}},
        ),
        patch("nudge_engine.campaigns._resolve_push_endpoints", return_value={7: []}),
        patch("credits.web_continue.get_or_create_continue_tokens", return_value={7: "secure-token"}),
        patch(
            "nudge_engine.campaigns.db.upsert_campaign_recipient_snapshots",
            side_effect=lambda _conn, rows: stored.extend(rows),
        ),
    ):
        _snapshot_campaign_batch(campaign=campaign, campaign_id=42, user_ids=[7])

    parameters = stored[0]["data"]["whatsapp_template"]["parameters"]
    assert parameters["body.1"] == "Asha"
    assert parameters["button.0.1"] == "secure-token.nc42"
