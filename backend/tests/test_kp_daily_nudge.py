from datetime import date
from unittest.mock import MagicMock, patch

from nudge_engine import kp_daily


def _result(row):
    return {"today": {"houses_giving_results": [row]}}


def test_kp_daily_requires_fine_period_and_ruling_planet_confirmation():
    row = {
        "house": 10,
        "activation_score": 5.2,
        "rp_confirmation": [{"planet": "Mercury", "weight": 0.9}],
        "period_support": [{"level": "sookshma", "planet": "Mercury", "weight": 1.6}],
        "tone": "supportive",
    }
    opportunity = kp_daily._select_opportunity(_result(row))
    assert opportunity["house"] == 10
    assert "work" in opportunity["action"]

    row["rp_confirmation"] = []
    assert kp_daily._select_opportunity(_result(row)) is None

    row["rp_confirmation"] = [{"planet": "Mercury", "weight": 0.9}]
    row["period_support"] = [{"level": "mahadasha", "planet": "Mercury", "weight": 0.5}]
    assert kp_daily._select_opportunity(_result(row)) is None


def test_kp_daily_never_sends_challenging_or_non_actionable_house():
    row = {
        "house": 8,
        "activation_score": 6.0,
        "rp_confirmation": [{"planet": "Saturn", "weight": 0.9}],
        "period_support": [{"level": "sookshma", "planet": "Saturn", "weight": 1.6}],
        "tone": "supportive",
    }
    assert kp_daily._select_opportunity(_result(row)) is None
    row["house"] = 10
    row["tone"] = "challenging"
    assert kp_daily._select_opportunity(_result(row)) is None


def test_enqueue_kp_daily_pages_opted_in_tokens_and_uses_dedicated_worker_queue():
    pages = [[101, 102], []]
    queued = []

    class Conn:
        def __enter__(self):
            return MagicMock()

        def __exit__(self, *args):
            return False

    with (
        patch.object(kp_daily, "nudge_tasks_enabled", return_value=True),
        patch.object(kp_daily, "nudge_tasks_are_isolated", return_value=True),
        patch.object(kp_daily.db, "get_conn", return_value=Conn()),
        patch.object(kp_daily.db, "get_push_enabled_user_ids_after", side_effect=pages),
        patch.object(kp_daily, "enqueue_nudge_task", side_effect=lambda **kw: queued.append(kw) or True),
    ):
        summary = kp_daily.enqueue_kp_daily_batches(date(2026, 10, 29))

    assert summary == {"date": "2026-10-29", "candidates": 2, "batches_enqueued": 1}
    assert queued[0]["task_kind"] == "kp-daily-batch"
    assert queued[0]["payload"]["user_ids"] == [101, 102]
