"""Column dictionary for the curated admin Analytics Q&A purchase view."""

from __future__ import annotations

VIEW_NAME = "admin_analytics_purchase_facts"

COLUMN_DOCS = [
    ("transaction_id", "integer", "Internal paid-purchase transaction id; use only for COUNT(DISTINCT ...)"),
    ("userid", "integer", "Purchasing user id; use only for COUNT(DISTINCT ...)"),
    ("purchased_at", "timestamp", "Paid purchase timestamp stored in UTC"),
    ("provider", "text", "Payment provider: razorpay or google_play"),
    ("credits_purchased", "bigint", "Credits granted by the paid purchase before refunds"),
    (
        "purchase_amount",
        "numeric",
        "Purchase money amount in major currency units when payment metadata contains it; may be NULL",
    ),
    ("currency", "text", "ISO currency code; normally INR"),
    ("refunded_credits", "bigint", "Credits reversed for this purchase"),
    ("net_credits_purchased", "bigint", "Purchased credits minus refunded credits, floored at zero"),
    ("purchase_status", "text", "paid, partially_refunded, or refunded"),
]


def schema_prompt_block() -> str:
    lines = [
        f"You may query ONLY this Postgres view: {VIEW_NAME}",
        "One row per paid credit purchase. Columns:",
    ]
    for name, typ, desc in COLUMN_DOCS:
        lines.append(f"- {name} ({typ}): {desc}")
    lines.extend(
        [
            "For calendar periods, purchased_at is UTC. Use date_trunc with NOW() AT TIME ZONE 'UTC'.",
            "For revenue, group by currency and SUM(purchase_amount); do not combine different currencies.",
            "When the request says total credit purchases, return purchase_count, unique_buyers, "
            "gross_credits_purchased, net_credits_purchased, and purchase_amount where useful.",
        ]
    )
    return "\n".join(lines)
