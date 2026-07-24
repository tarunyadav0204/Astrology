from __future__ import annotations

from pathlib import Path


MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


def test_astrologer_subscription_seed_has_true_zero_row_guard():
    sql = (MIGRATIONS / "add_astrologer_subscription.sql").read_text(
        encoding="utf-8"
    )

    # An aggregate SELECT directly FROM subscription_plans with WHERE NOT EXISTS
    # still emits one row (MAX becomes NULL), which caused later deploys to retry
    # plan_id=1. The aggregate must be isolated before applying the guard.
    assert "WITH next_plan AS" in sql
    assert "FROM next_plan\nWHERE NOT EXISTS" in sql
    assert "FROM subscription_plans\nWHERE NOT EXISTS" not in sql
