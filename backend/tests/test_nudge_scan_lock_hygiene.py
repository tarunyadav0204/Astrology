"""Regression: nudge scan must not hold DB locks across Cloud Tasks I/O."""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from nudge_engine.models import NudgeEvent
from nudge_engine import service


def test_enqueue_scan_batches_releases_db_before_task_enqueue():
    events = [
        NudgeEvent(
            trigger_id="t1",
            title="Hello",
            body="Body",
            params={},
            question=None,
            user_ids=None,
            priority=1,
        )
    ]
    pages = [[1, 2], [3], []]
    open_conns = {"n": 0}
    enqueue_calls = []

    class _ConnCM:
        def __enter__(self):
            open_conns["n"] += 1
            return MagicMock(name="conn")

        def __exit__(self, *args):
            open_conns["n"] -= 1
            return False

    def fake_get_conn():
        return _ConnCM()

    def fake_get_user_ids_after(conn, *, after_userid=0, limit=50):
        assert open_conns["n"] == 1
        return pages.pop(0)

    def fake_enqueue(**kwargs):
        # Critical: no DB connection may be held while talking to Cloud Tasks.
        assert open_conns["n"] == 0
        enqueue_calls.append(kwargs)
        return True

    with (
        patch.object(service.db, "get_conn", side_effect=fake_get_conn),
        patch.object(service.db, "get_user_ids_after", side_effect=fake_get_user_ids_after),
        patch("nudge_engine.task_queue.nudge_tasks_enabled", return_value=True),
        patch("nudge_engine.task_queue.nudge_tasks_are_isolated", return_value=True),
        patch("nudge_engine.task_queue.enqueue_nudge_task", side_effect=fake_enqueue),
    ):
        summary = service._enqueue_scan_batches(events, date(2026, 7, 19))

    assert summary["pages_scanned"] == 2
    assert summary["batches_enqueued"] == 2
    assert summary["users_targeted"] == 3
    assert len(enqueue_calls) == 2


def test_run_nudge_scan_closes_conn_when_lock_busy():
    released = {"exit": 0, "unlock": 0}

    class _ConnCM:
        def __enter__(self):
            return MagicMock(name="lock_conn")

        def __exit__(self, *args):
            released["exit"] += 1
            return False

    with (
        patch.object(service.db, "get_conn", return_value=_ConnCM()),
        patch.object(service.db, "init_nudge_tables"),
        patch.object(service.db, "try_advisory_lock", return_value=False),
        patch.object(
            service.db,
            "advisory_unlock",
            side_effect=lambda *a, **k: released.__setitem__("unlock", released["unlock"] + 1),
        ),
    ):
        summary = service.run_nudge_scan(date(2026, 7, 19))

    assert summary.get("skipped") == "already_running"
    assert released["exit"] == 1
    assert released["unlock"] == 0
