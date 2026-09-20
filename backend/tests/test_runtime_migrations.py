from __future__ import annotations

from pathlib import Path

from migrations.apply_runtime_migrations import RUNTIME_MIGRATIONS


MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


def test_event_timeline_migrations_run_during_deploy_in_dependency_order():
    timeline_migrations = [
        "add_event_timeline_engine_version.sql",
        "add_event_timeline_v3_context.sql",
        "add_event_timeline_calibration.sql",
        "add_event_relative_profiles.sql",
    ]
    positions = [RUNTIME_MIGRATIONS.index(filename) for filename in timeline_migrations]

    assert positions == sorted(positions)
    for filename in timeline_migrations:
        assert (MIGRATIONS / filename).is_file()


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


def test_payment_failure_alert_migration_is_idempotent_and_deduplicated():
    sql = (MIGRATIONS / "add_payment_failure_alerts.sql").read_text(
        encoding="utf-8"
    )

    assert "CREATE TABLE IF NOT EXISTS payment_failure_alerts" in sql
    assert "dedupe_key TEXT NOT NULL UNIQUE" in sql
    assert "userid INTEGER" in sql
    assert "CREATE INDEX IF NOT EXISTS" in sql


def test_instant_billing_settings_seeds_support_legacy_credit_settings_schema():
    """Runtime migrations must not assume setting_key has a unique index.

    The canonical PostgreSQL dump and older production databases allow more
    than one credit_settings row per key, so PostgreSQL cannot accept
    ``ON CONFLICT (setting_key)`` as a conflict target.
    """
    for filename, setting_key in (
        ("add_instant_billing_sessions.sql", "instant_chat_per_minute_cost"),
        ("add_instant_billing_split_rates.sql", "instant_chat_first_minute_cost"),
    ):
        sql = (MIGRATIONS / filename).read_text(encoding="utf-8")

        assert "\nON CONFLICT (setting_key)" not in sql
        assert "WHERE NOT EXISTS" in sql
        assert f"WHERE setting_key = '{setting_key}'" in sql


def test_prashna_credit_setting_is_seeded_idempotently_during_deploy():
    filename = "add_prashna_credit_setting.sql"
    assert filename in RUNTIME_MIGRATIONS
    sql = (MIGRATIONS / filename).read_text(encoding="utf-8")
    assert "'prashna_analysis_cost', 3" in sql
    assert "WHERE NOT EXISTS" in sql
    assert "ON CONFLICT (setting_key)" not in sql


def test_engagement_suggestion_schema_runs_during_deploy():
    filename = "add_engagement_suggestions.sql"
    assert filename in RUNTIME_MIGRATIONS
    sql = (MIGRATIONS / filename).read_text(encoding="utf-8")
    for table in (
        "engagement_opportunities",
        "engagement_presentations",
        "engagement_interactions",
        "user_engagement_preferences",
        "engagement_refresh_queue",
        "engagement_delivery_attempts",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql


def test_talk_to_tara_rate_correction_runs_only_once_and_preserves_future_admin_changes():
    sql = (MIGRATIONS / "set_talk_to_tara_rate_five.sql").read_text(encoding="utf-8")
    assert "runtime_data_migrations" in sql
    assert "ON CONFLICT (migration_key) DO NOTHING" in sql
    assert "SET setting_value = CASE WHEN setting_value = 7 THEN 5 ELSE setting_value END" in sql
    assert "discount = CASE WHEN discount = 7 THEN NULL ELSE discount END" in sql
    assert "AND (setting_value = 7 OR discount = 7)" in sql
    assert "EXISTS (SELECT 1 FROM applied_now)" in sql
