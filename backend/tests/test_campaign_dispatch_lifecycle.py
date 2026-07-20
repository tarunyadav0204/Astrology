from unittest.mock import patch

from nudge_engine.campaigns import _dispatch_one_campaign


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
