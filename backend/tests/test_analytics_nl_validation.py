import pytest

from nudge_engine.analytics_nl import validate_analytics_sql


def test_accepts_aggregate_on_curated_view():
    sql, warnings = validate_analytics_sql(
        """
        SELECT currency, COUNT(*) AS purchase_count,
               COUNT(DISTINCT userid) AS unique_buyers,
               SUM(purchase_amount) AS total_purchase_amount
        FROM admin_analytics_purchase_facts
        WHERE purchased_at >= date_trunc('month', NOW() AT TIME ZONE 'UTC')
        GROUP BY currency
        """
    )
    assert sql.endswith("LIMIT 200")
    assert warnings == ["Added LIMIT 200"]


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM admin_analytics_purchase_facts",
        "SELECT userid, COUNT(*) FROM admin_analytics_purchase_facts GROUP BY userid",
        "SELECT transaction_id, SUM(credits_purchased) FROM admin_analytics_purchase_facts GROUP BY transaction_id",
        "SELECT SUM(amount) FROM credit_transactions",
        "DELETE FROM admin_analytics_purchase_facts",
        "SELECT credits_purchased FROM admin_analytics_purchase_facts",
    ],
)
def test_rejects_unsafe_or_nonaggregate_queries(sql):
    with pytest.raises(ValueError):
        validate_analytics_sql(sql)


def test_clamps_result_rows():
    sql, warnings = validate_analytics_sql(
        "SELECT provider, COUNT(*) FROM admin_analytics_purchase_facts GROUP BY provider LIMIT 999"
    )
    assert sql.endswith("LIMIT 200")
    assert warnings == ["LIMIT clamped to 200"]
