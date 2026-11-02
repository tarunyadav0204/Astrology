from datetime import datetime

from credits.credit_grant_campaigns import _campaign_query, _row_dict


def test_campaign_metrics_expose_paid_purchase_outcomes_after_grant():
    row = (
        41, "Diwali goodwill", 10, "completed", 4, 4, datetime(2026, 11, 2),
        4, 4, 3, 2, 1, 1, 2,
        2, 85, 3,
        0, 40, 3, 1, 12, 28,
    )

    metrics = _row_dict(row)["metrics"]

    assert metrics["paid_buyers"] == 2
    assert metrics["paid_credit_purchased"] == 85
    assert metrics["paid_purchase_count"] == 3
    assert metrics["credits_granted"] == 40
    assert metrics["whatsapp_eligible"] == 3
    assert metrics["chat_converted"] == 1
    assert metrics["grant_credits_used"] == 12
    assert metrics["grant_credits_remaining"] == 28


def test_campaign_query_counts_only_paid_purchase_ledger_entries_after_grant():
    query = _campaign_query()

    assert "ct.created_at >= r.credited_at" in query
    assert "ct.transaction_type = 'earned'" in query
    assert "ct.source IN ('google_play', 'razorpay')" in query
    assert "paid_credit_purchased" in query
    assert "ct.source = 'feature_usage'" in query
    assert "chat_converted" in query
