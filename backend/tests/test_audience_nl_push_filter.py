from nudge_engine.audience_nl import _audience_user_ids_sql


def test_audience_ids_sql_does_not_filter_push_by_default():
    sql = _audience_user_ids_sql(
        "SELECT userid FROM admin_audience_user_facts LIMIT 50",
        push_only=False,
    )

    assert "has_device_token = TRUE" not in sql


def test_audience_ids_sql_filters_all_matching_ids_to_push_enabled_users():
    sql = _audience_user_ids_sql(
        "SELECT userid FROM admin_audience_user_facts LIMIT 50",
        push_only=True,
    )

    assert "push_facts.userid = audience_sub.userid" in sql
    assert "push_facts.has_device_token = TRUE" in sql

