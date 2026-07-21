from contextlib import contextmanager

import pytest

import nudge_engine.data_explorer_nl as explorer
from nudge_engine.data_explorer_nl import (
    fetch_schema_catalog,
    relevant_relations,
    schema_prompt_block,
    validate_data_explorer_sql,
)


def test_campaign_conversion_question_loads_join_bridge_relations():
    relations = set(relevant_relations("Which campaigns converted to a question within 7 days?"))

    assert {"nudge_campaigns", "nudge_deliveries", "nudge_conversions"}.issubset(relations)


def test_safe_cross_table_aggregate_is_allowed_and_capped():
    sql, warnings = validate_data_explorer_sql(
        """
        SELECT nc.id AS campaign_id,
               COUNT(DISTINCT nd.delivery_group_id) AS sends
        FROM nudge_campaigns nc
        LEFT JOIN nudge_deliveries nd ON nd.campaign_id = nc.id
        GROUP BY nc.id
        """
    )

    assert "LIMIT 500" in sql
    assert warnings == ["Added LIMIT 500"]


def test_cte_over_approved_relations_is_allowed():
    sql, _ = validate_data_explorer_sql(
        """
        WITH sends AS (
            SELECT campaign_id, COUNT(DISTINCT delivery_group_id) AS send_count
            FROM nudge_deliveries
            GROUP BY campaign_id
        )
        SELECT nc.id AS campaign_id, s.send_count
        FROM nudge_campaigns nc
        LEFT JOIN sends s ON s.campaign_id = nc.id
        """
    )

    assert "FROM nudge_campaigns" in sql


@pytest.mark.parametrize(
    "sql, message",
    [
        ("SELECT * FROM users", "SELECT \\* is not allowed"),
        ("SELECT secret FROM private_table", "Relation is not approved"),
        ("DELETE FROM users", "SELECT queries only"),
        ("SELECT dt.token FROM device_tokens dt", "Sensitive column"),
        ("SELECT token FROM device_tokens", "Sensitive column"),
        ("SELECT cm.content FROM chat_messages cm", "Sensitive column"),
        ("SELECT name FROM users", "Sensitive column"),
        ("SELECT date FROM birth_charts", "Sensitive column"),
        ("SELECT current_setting('server_version') FROM users", "forbidden operation"),
    ],
)
def test_unsafe_or_sensitive_queries_are_rejected(sql, message):
    with pytest.raises(ValueError, match=message):
        validate_data_explorer_sql(sql)


def test_prompt_schema_contains_only_catalog_columns_given_to_it():
    prompt = schema_prompt_block(
        {
            "device_tokens": [("userid", "bigint"), ("platform", "text")],
            "users": [("userid", "bigint"), ("created_at", "timestamp with time zone")],
        }
    )

    assert "device_tokens" in prompt
    assert "platform (text)" in prompt
    assert "token (" not in prompt
    assert "email (" not in prompt


def test_live_catalog_drops_blocked_columns(monkeypatch):
    class Cursor:
        @staticmethod
        def fetchall():
            return [
                ("users", "userid", "bigint"),
                ("users", "email", "text"),
                ("device_tokens", "platform", "text"),
                ("device_tokens", "token", "text"),
            ]

    @contextmanager
    def fake_connection():
        yield object()

    monkeypatch.setattr(explorer, "get_conn", fake_connection)
    monkeypatch.setattr(explorer, "execute", lambda *_args, **_kwargs: Cursor())

    catalog = fetch_schema_catalog(["users", "device_tokens"])

    assert catalog == {
        "users": [("userid", "bigint")],
        "device_tokens": [("platform", "text")],
    }
