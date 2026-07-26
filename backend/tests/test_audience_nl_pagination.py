import json

from nudge_engine.audience_nl import validate_audience_sql
from nudge_engine.routes import CampaignUpsertRequest, _validate_campaign_payload


def test_audience_validation_does_not_add_a_result_limit():
    sql, warnings = validate_audience_sql(
        "SELECT userid FROM admin_audience_user_facts ORDER BY userid"
    )

    assert "LIMIT" not in sql.upper()
    assert warnings == []


def test_audience_validation_preserves_an_explicit_admin_limit():
    sql, warnings = validate_audience_sql(
        "SELECT userid FROM admin_audience_user_facts ORDER BY userid LIMIT 750"
    )

    assert sql.endswith("LIMIT 750")
    assert warnings == []


def test_large_paginated_audience_is_saved_as_valid_complete_json():
    user_ids = list(range(1, 10_001))
    body = CampaignUpsertRequest(
        name="Large audience",
        title_template="Hello",
        body_template="A campaign message",
        audience_filter={"type": "user_ids", "user_ids": user_ids},
    )

    serialized = _validate_campaign_payload(body)["audience_filter_json"]

    assert len(serialized) > 20_000
    assert json.loads(serialized)["user_ids"] == user_ids
