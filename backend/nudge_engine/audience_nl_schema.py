"""Column dictionary for admin_audience_user_facts (NL Audience Builder LLM prompt)."""

from __future__ import annotations

VIEW_NAME = "admin_audience_user_facts"

# Columns always returned to the admin UI table (merged by userid after filter query).
DISPLAY_COLUMNS = [
    "userid",
    "name",
    "phone",
    "email",
    "credits_balance",
    "lifetime_purchased_credits",
    "last_purchase_at",
    "last_purchase_amount",
    "last_purchase_credits",
    "last_user_chat_at",
    "days_since_last_chat",
    "questions_asked_yesterday",
    "questions_asked_today",
    "paid_questions_yesterday",
    "paid_questions_today",
    "has_device_token",
    "has_whatsapp",
]

COLUMN_DOCS = [
    ("userid", "integer", "Primary user id"),
    ("name", "text", "Display name"),
    ("phone", "text", "Phone number if known"),
    ("email", "text", "Email if known"),
    ("credits_balance", "bigint", "Current credit wallet balance"),
    ("lifetime_purchased_credits", "bigint", "Sum of credits from paid purchases (razorpay + google_play)"),
    ("lifetime_spent_credits", "bigint", "Sum of credits spent"),
    ("purchase_count", "bigint", "Number of paid credit purchases"),
    ("last_purchase_at", "timestamptz/timestamp", "Timestamp of most recent paid credit purchase; NULL if never purchased"),
    (
        "last_purchase_amount",
        "numeric",
        "Money amount of last paid purchase in major currency units (INR etc.) when metadata has amount_paise or price_amount_micros; NULL if unknown",
    ),
    ("last_purchase_credits", "bigint", "Credits granted in the last paid purchase (0 if never purchased)"),
    ("last_user_chat_at", "timestamptz/timestamp", "Last time user sent a chat message; NULL if never"),
    ("days_since_last_chat", "integer", "Whole days since last user chat message; NULL if never chatted"),
    ("questions_asked_30d", "bigint", "User chat messages in last 30 days"),
    ("questions_asked_lifetime", "bigint", "Lifetime user chat messages"),
    ("questions_asked_today", "bigint", "User chat messages during the current Asia/Kolkata calendar day"),
    ("questions_asked_yesterday", "bigint", "User chat messages during the previous Asia/Kolkata calendar day"),
    (
        "paid_questions_today",
        "bigint",
        "Credit-charged chat questions completed during the current Asia/Kolkata calendar day",
    ),
    (
        "paid_questions_yesterday",
        "bigint",
        "Credit-charged chat questions completed during the previous Asia/Kolkata calendar day",
    ),
    ("last_paid_question_at", "timestamp", "Timestamp of the most recent credit-charged chat question"),
    ("has_device_token", "boolean", "True if user has a push device token"),
    ("has_whatsapp", "boolean", "True if WhatsApp wa_id is linked"),
    ("has_email", "boolean", "True if email is present"),
    ("signup_at", "timestamptz/timestamp", "Account created_at"),
    ("signup_client", "text", "Signup client label (android, ios, web, whatsapp, etc.)"),
]


def schema_prompt_block() -> str:
    lines = [
        f"You may query ONLY this Postgres view: {VIEW_NAME}",
        "One row per user. Columns:",
    ]
    for name, typ, desc in COLUMN_DOCS:
        lines.append(f"- {name} ({typ}): {desc}")
    lines.append(
        "Paid purchase means credit_transactions already filtered into lifetime_purchased_* / last_purchase_* "
        "(razorpay + google_play only)."
    )
    return "\n".join(lines)
