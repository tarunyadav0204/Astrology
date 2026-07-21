"""Governed natural-language data explorer for approved AstroRoshni admin data."""
from __future__ import annotations

import logging
import os
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from db import execute, get_conn

from .audience_nl import (
    STATEMENT_TIMEOUT_MS,
    _extract_json_object,
    _gemini_response_text,
    _strip_sql_comments,
)

logger = logging.getLogger(__name__)

MAX_ROWS = 500
MAX_CELL_CHARS = 2000


RELATION_CONFIG: Dict[str, Dict[str, Any]] = {
    "users": {
        "description": "User accounts, signup source, role, gender, and creation time.",
        "blocked": {"password", "phone", "email", "name", "whatsapp_wa_id"},
        "keywords": {"user", "users", "signup", "registered", "registration", "gender", "client"},
    },
    "user_credits": {
        "description": "Current user credit wallet and free-question usage state.",
        "blocked": set(),
        "keywords": {"credit", "credits", "wallet", "balance", "free question"},
    },
    "credit_transactions": {
        "description": "Credit earnings and spending. Negative amount means credits spent; positive means earned.",
        "blocked": {"metadata", "description"},
        "keywords": {"credit", "credits", "purchase", "payment", "paid", "revenue", "spend", "spent", "refund"},
    },
    "admin_analytics_purchase_facts": {
        "description": "Normalized paid credit purchases and reversals with provider, currency, credits, and money amount.",
        "blocked": set(),
        "keywords": {"purchase", "payment", "paid", "revenue", "buyer", "refund", "razorpay", "google play"},
    },
    "admin_audience_user_facts": {
        "description": "One safe analytical row per user with balances, purchase activity, chat activity, and reachability.",
        "blocked": {"phone", "email", "name"},
        "keywords": {"user", "audience", "active", "inactive", "question", "chat", "push", "whatsapp"},
    },
    "chat_sessions": {
        "description": "Chat sessions linked to users and birth charts.",
        "blocked": set(),
        "keywords": {"chat", "question", "session", "conversation", "active", "inactive"},
    },
    "chat_messages": {
        "description": "Chat message events and processing metadata. Message text is intentionally unavailable.",
        "blocked": {
            "content", "canonical_question", "gate_metadata", "terms", "glossary", "images",
            "follow_up_questions", "error_message", "next_action", "chart_insights",
            "parallel_llm_usage", "engagement_updates",
        },
        "keywords": {"chat", "question", "message", "answer", "category", "language", "latency", "llm"},
    },
    "birth_charts": {
        "description": "Birth-chart ownership and profile metadata; raw birth details are intentionally unavailable.",
        "blocked": {"name", "date", "time", "latitude", "longitude", "timezone", "place", "birth_hash"},
        "keywords": {"chart", "birth chart", "native", "relation", "self chart", "rectified"},
    },
    "user_subscriptions": {
        "description": "User subscription status and active date windows.",
        "blocked": {"purchase_token", "razorpay_subscription_id", "google_play_order_id"},
        "keywords": {"subscription", "subscriber", "renewal", "plan", "guru"},
    },
    "subscription_plans": {
        "description": "Subscription plan names, platform, price, duration, and tier.",
        "blocked": {"google_play_product_id"},
        "keywords": {"subscription", "plan", "price", "tier", "guru"},
    },
    "device_tokens": {
        "description": "Push reachability by user and platform. Raw device tokens are intentionally unavailable.",
        "blocked": {"token"},
        "keywords": {"push", "notification", "device", "android", "ios", "reachable"},
    },
    "nudge_campaigns": {
        "description": "Campaign configuration, lifecycle status, scheduling, policy, and target counts.",
        "blocked": {"body_template", "question_template", "ai_base_prompt", "audience_filter_json"},
        "keywords": {"campaign", "nudge", "notification", "push", "blast", "waterfall"},
    },
    "nudge_deliveries": {
        "description": "Per-channel campaign/nudge delivery outcomes, sends, reads, and clicks.",
        "blocked": {"body", "data_json", "event_params"},
        "keywords": {"campaign", "nudge", "notification", "delivery", "sent", "read", "click", "push", "whatsapp", "email"},
    },
    "nudge_conversions": {
        "description": "Attributed post-nudge question conversions and time-to-conversion.",
        "blocked": {"question"},
        "keywords": {"campaign", "nudge", "conversion", "converted", "funnel", "question after", "attribution"},
    },
    "app_installations": {
        "description": "App acquisition, UTM attribution, app version/build, opens, registration, and linked user.",
        "blocked": {"installation_id", "referrer_raw", "client_install_key", "lead_phone", "lead_email"},
        "keywords": {"install", "acquisition", "utm", "campaign source", "first open", "app version", "registration"},
    },
    "app_installation_events": {
        "description": "Installation funnel event names, statuses, screens, and timestamps.",
        "blocked": {"installation_id", "metadata"},
        "keywords": {"install", "acquisition", "funnel", "event", "screen", "first open"},
    },
    "admin_company_expenses": {
        "description": "Company expenses by date, amount, currency, vendor, category, and payer.",
        "blocked": {"notes", "invoice_original_name", "invoice_storage_path", "invoice_mime"},
        "keywords": {"expense", "expenses", "vendor", "cost", "paid by", "spend", "company"},
    },
    "admin_expense_vendors": {
        "description": "Expense vendor master list.",
        "blocked": set(),
        "keywords": {"expense", "vendor"},
    },
    "admin_expense_paid_by": {
        "description": "Expense payer master list.",
        "blocked": set(),
        "keywords": {"expense", "paid by", "payer"},
    },
}

ALLOWED_RELATIONS: Set[str] = set(RELATION_CONFIG)

JOIN_GUIDE = """
Approved relationship paths:
- users.userid = user_credits.userid = credit_transactions.userid = device_tokens.userid
- users.userid = chat_sessions.user_id; chat_sessions.session_id = chat_messages.session_id
- users.userid = birth_charts.userid = user_subscriptions.userid
- user_subscriptions.plan_id = subscription_plans.plan_id
- nudge_campaigns.id = nudge_deliveries.campaign_id = nudge_conversions.campaign_id
- nudge_deliveries.delivery_group_id = nudge_conversions.delivery_group_id
- users.userid = nudge_deliveries.userid = nudge_conversions.userid
- users.userid = app_installations.userid
- admin_company_expenses.vendor_id = admin_expense_vendors.id
- admin_company_expenses.paid_by_id = admin_expense_paid_by.id
""".strip()

BUSINESS_DEFINITIONS = """
Business definitions:
- A user question is chat_messages.sender = 'user'. Count distinct chat_messages.message_id.
- A completed answer is an assistant chat_messages row with status = 'completed'.
- A paid question is a credit_transactions row with transaction_type='spent', source='feature_usage', amount < 0,
  and reference_id in ('chat_question', 'instant_chat', 'speech_chat'). Free questions have amount = 0.
- A paid credit purchase should use admin_analytics_purchase_facts, not raw metadata parsing.
- Push-enabled means at least one device_tokens row exists for the userid. Never select the token.
- A successful delivery has nudge_deliveries.send_status='sent' (legacy NULL rows may represent sent records).
- A campaign conversion is a nudge_conversions row; seconds_since_sent is time to the attributed question.
- Unless the admin explicitly asks for UTC, calendar-day reporting uses Asia/Kolkata boundaries.
""".strip()

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|copy|execute|call|do|"
    r"vacuum|analyze|comment|merge|replace|set\s+role|pg_|dblink|lo_|information_schema|"
    r"pg_catalog|current_setting|current_database|current_user|session_user|inet_server|"
    r"query_to_xml|has_[a-z_]+_privilege|into\s+outfile|load_file|for\s+update)\b",
    re.IGNORECASE,
)
_RELATION_REF = re.compile(
    r"\b(?:from|join)\s+\"?([a-zA-Z_][a-zA-Z0-9_\.]*)\"?"
    r"(?:\s+(?:as\s+)?\"?([a-zA-Z_][a-zA-Z0-9_]*)\"?)?",
    re.IGNORECASE,
)
_SQL_KEYWORDS = {
    "where", "join", "left", "right", "full", "inner", "outer", "cross", "on", "group",
    "order", "limit", "offset", "union", "having", "window", "fetch",
}


def relevant_relations(question: str) -> List[str]:
    text = " ".join(str(question or "").lower().split())
    matched = {
        name
        for name, config in RELATION_CONFIG.items()
        if any(keyword in text for keyword in config.get("keywords") or set())
    }
    if not matched:
        return sorted(ALLOWED_RELATIONS)
    if any(name != "users" for name in matched):
        matched.add("users")
    # Include bridge/definition tables required by common joins.
    if "chat_messages" in matched:
        matched.add("chat_sessions")
    if "nudge_conversions" in matched:
        matched.update({"nudge_deliveries", "nudge_campaigns"})
    if "user_subscriptions" in matched:
        matched.add("subscription_plans")
    if "admin_company_expenses" in matched:
        matched.update({"admin_expense_vendors", "admin_expense_paid_by"})
    return sorted(matched)


def fetch_schema_catalog(relation_names: Optional[Sequence[str]] = None) -> Dict[str, List[Tuple[str, str]]]:
    requested = sorted(set(relation_names or ALLOWED_RELATIONS) & ALLOWED_RELATIONS)
    if not requested:
        return {}
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = ANY(%s)
            ORDER BY table_name, ordinal_position
            """,
            (requested,),
        )
        rows = cur.fetchall() or []
    catalog: Dict[str, List[Tuple[str, str]]] = {}
    for table_name, column_name, data_type in rows:
        name = str(table_name).lower()
        column = str(column_name).lower()
        if name not in ALLOWED_RELATIONS:
            continue
        if column in set(RELATION_CONFIG[name].get("blocked") or set()):
            continue
        catalog.setdefault(name, []).append((column, str(data_type)))
    return catalog


def schema_prompt_block(catalog: Dict[str, List[Tuple[str, str]]]) -> str:
    lines = ["Approved read-only relations and currently available safe columns:"]
    for relation in sorted(catalog):
        config = RELATION_CONFIG[relation]
        lines.append(f"\n{relation}: {config['description']}")
        for column, data_type in catalog[relation]:
            lines.append(f"- {column} ({data_type})")
    lines.extend(["", JOIN_GUIDE, "", BUSINESS_DEFINITIONS])
    return "\n".join(lines)


def _cte_names(sql: str) -> Set[str]:
    scan = str(sql or "").replace('"', "")
    return {
        match.group(1).lower()
        for match in re.finditer(r"(?:\bwith\b|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s*\(", scan, re.I)
    }


def _relation_aliases(sql: str) -> Tuple[Set[str], Dict[str, str]]:
    ctes = _cte_names(sql)
    relations: Set[str] = set()
    aliases: Dict[str, str] = {}
    scan = str(sql or "").replace('"', "")
    for match in _RELATION_REF.finditer(scan):
        raw_name = match.group(1).lower()
        name = raw_name.split(".")[-1]
        alias = str(match.group(2) or "").lower()
        if alias in _SQL_KEYWORDS:
            alias = ""
        if name in ctes:
            continue
        relations.add(name)
        aliases[name] = name
        if alias:
            aliases[alias] = name
    return relations, aliases


def _validate_sensitive_columns(sql: str, aliases: Dict[str, str], relations: Set[str]) -> None:
    scan = str(sql or "").replace('"', "")
    blocked_union: Set[str] = set()
    for relation in relations:
        blocked = set(RELATION_CONFIG.get(relation, {}).get("blocked") or set())
        blocked_union.update(blocked)
        for alias, alias_relation in aliases.items():
            if alias_relation != relation:
                continue
            for column in blocked:
                if re.search(rf"\b{re.escape(alias)}\s*\.\s*{re.escape(column)}\b", scan, re.I):
                    raise ValueError(f"Sensitive column is not available: {relation}.{column}")
    # Also reject unqualified sensitive identifiers. Date/time are relation-specific
    # and therefore checked only in qualified birth-chart references above.
    for column in blocked_union - {"date", "time"}:
        if re.search(rf"(?<!\.)\b{re.escape(column)}\b", scan, re.I):
            raise ValueError(f"Sensitive column is not available: {column}")
    # These generic column names are only sensitive on birth_charts. Reject
    # unqualified references whenever that relation is present so `SELECT date`
    # cannot bypass the qualified-column check. CURRENT_DATE/created_date do not
    # match because the adjacent underscore is a word character.
    if "birth_charts" in relations:
        for column in ("date", "time"):
            if re.search(rf"(?<![.\w]){column}(?!\w)", scan, re.I):
                raise ValueError(f"Sensitive column is not available: birth_charts.{column}")


def validate_data_explorer_sql(sql: str) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    if not sql or not str(sql).strip():
        raise ValueError("SQL is empty")
    cleaned = _strip_sql_comments(str(sql)).strip().rstrip(";")
    if ";" in cleaned:
        raise ValueError("Only one SQL statement is allowed")
    lowered = cleaned.lower().lstrip()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise ValueError("Data Explorer allows SELECT queries only")
    if _FORBIDDEN.search(cleaned):
        raise ValueError("SQL contains a forbidden operation or system relation")
    if re.search(r"\bselect\s+(?:distinct\s+)?(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?\*", cleaned, re.I):
        raise ValueError("SELECT * is not allowed; select only the fields needed for the answer")

    relations, aliases = _relation_aliases(cleaned)
    if not relations:
        raise ValueError("Query must use at least one approved relation")
    unknown = sorted(relations - ALLOWED_RELATIONS)
    if unknown:
        raise ValueError(f"Relation is not approved for Data Explorer: {', '.join(unknown)}")
    _validate_sensitive_columns(cleaned, aliases, relations)

    limit_matches = list(re.finditer(r"\blimit\s+(\d+)\b", cleaned, re.I))
    if not limit_matches:
        cleaned = f"{cleaned}\nLIMIT {MAX_ROWS}"
        warnings.append(f"Added LIMIT {MAX_ROWS}")
    elif int(limit_matches[-1].group(1)) > MAX_ROWS:
        match = limit_matches[-1]
        cleaned = cleaned[: match.start()] + f"LIMIT {MAX_ROWS}" + cleaned[match.end() :]
        warnings.append(f"LIMIT clamped to {MAX_ROWS}")
    return cleaned, warnings


def generate_data_explorer_sql(prompt: str) -> Dict[str, Any]:
    user_prompt = str(prompt or "").strip()
    if len(user_prompt) < 8:
        raise ValueError("Describe the data question in a bit more detail")
    user_prompt = user_prompt[:4000]
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    # The approved catalog is deliberately small enough to provide in full.
    # This avoids silently omitting a valid join merely because keyword routing
    # did not recognize the administrator's wording.
    catalog = fetch_schema_catalog(sorted(ALLOWED_RELATIONS))
    if not catalog:
        raise RuntimeError("No approved Data Explorer relations are available")

    import google.generativeai as genai
    from .chat_nudge_suggestion import _nudge_suggestion_model_names

    genai.configure(api_key=api_key)
    model = None
    used_name = None
    for name in _nudge_suggestion_model_names():
        try:
            model = genai.GenerativeModel(name)
            used_name = name
            break
        except Exception:
            continue
    if not model:
        raise RuntimeError("No Gemini model available")

    system = f"""You are AstroRoshni's governed admin Data Explorer.

{schema_prompt_block(catalog)}

Rules:
1. Return ONLY JSON with keys explanation, sql, and result_kind.
2. result_kind must be metric, table, or trend.
3. Generate one PostgreSQL SELECT (WITH CTEs are allowed) using only listed relations and columns.
4. Never use SELECT *. Select only fields required to answer the question.
5. Never invent a column, relationship, business definition, or proxy metric.
6. Qualify columns with table aliases whenever more than one relation is used.
7. Avoid row multiplication: aggregate before joining one-to-many facts or use COUNT(DISTINCT primary_id).
8. Use Asia/Kolkata calendar boundaries unless the admin explicitly requests UTC.
9. Give computed fields clear snake_case aliases.
10. Do not include LIMIT; the server enforces it.
11. If the requested fact is unavailable, return sql as an empty string and explain what field is missing.
"""
    response = model.generate_content(
        f"{system}\n\nAdmin question:\n{user_prompt}",
        generation_config={"temperature": 0.05},
    )
    parsed = _extract_json_object(_gemini_response_text(response))
    if not parsed:
        raise RuntimeError("Model did not return valid JSON")
    raw_sql = str(parsed.get("sql") or parsed.get("query") or "").strip()
    if not raw_sql:
        explanation = str(parsed.get("explanation") or "The requested fact is unavailable.").strip()
        raise ValueError(explanation)
    normalized, warnings = validate_data_explorer_sql(raw_sql)
    kind = str(parsed.get("result_kind") or "table").strip().lower()
    if kind not in {"metric", "table", "trend"}:
        kind = "table"
    return {
        "explanation": str(parsed.get("explanation") or "Data query generated.").strip(),
        "sql": normalized,
        "warnings": warnings,
        "model_used": used_name,
        "result_kind": kind,
        "relations_used": sorted(_relation_aliases(normalized)[0]),
    }


def _serialize(value: Any) -> Any:
    if value is None or isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        value = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value)
    return text if len(text) <= MAX_CELL_CHARS else f"{text[:MAX_CELL_CHARS]}…"


def execute_data_explorer_sql(sql: str) -> Dict[str, Any]:
    normalized, warnings = validate_data_explorer_sql(sql)
    # The wrapper is the authoritative row cap even if an editable query puts a
    # LIMIT inside a CTE/subquery. Fetch one extra row to report truncation.
    wrapped = f"SELECT * FROM ({normalized}) AS governed_result LIMIT {MAX_ROWS + 1}"
    with get_conn() as conn:
        try:
            execute(conn, "SET TRANSACTION READ ONLY")
        except Exception:
            pass
        try:
            execute(conn, f"SET statement_timeout = {int(STATEMENT_TIMEOUT_MS)}")
        except Exception:
            pass
        try:
            try:
                cur = execute(conn, wrapped)
            except Exception as exc:
                logger.warning("data_explorer execute failed: %s | sql=%s", exc, normalized[:1000])
                raise ValueError(
                    "Query could not be executed. Review the generated SQL and the listed source columns."
                ) from exc
            columns = [str(desc[0]) for desc in (cur.description or [])]
            raw_rows = list(cur.fetchall() or [])
        finally:
            try:
                execute(conn, "SET statement_timeout = 0")
            except Exception:
                pass
    truncated = len(raw_rows) > MAX_ROWS
    raw_rows = raw_rows[:MAX_ROWS]
    rows = [
        {columns[index]: _serialize(row[index]) for index in range(len(columns))}
        for row in raw_rows
    ]
    userid_column = next((column for column in columns if column.lower() in {"userid", "user_id"}), None)
    audience_user_ids: List[int] = []
    if userid_column:
        seen: Set[int] = set()
        for row in rows:
            try:
                userid = int(row.get(userid_column))
            except (TypeError, ValueError):
                continue
            if userid > 0 and userid not in seen:
                seen.add(userid)
                audience_user_ids.append(userid)
    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
        "warnings": warnings,
        "sql": normalized,
        "audience_user_ids": audience_user_ids,
        "can_create_audience": bool(audience_user_ids),
        "relations_used": sorted(_relation_aliases(normalized)[0]),
    }


def generate_and_run_data_explorer(prompt: str) -> Dict[str, Any]:
    generated = generate_data_explorer_sql(prompt)
    executed = execute_data_explorer_sql(generated["sql"])
    return {
        **executed,
        "explanation": generated.get("explanation"),
        "model_used": generated.get("model_used"),
        "result_kind": generated.get("result_kind") or "table",
        "warnings": list(
            dict.fromkeys(list(generated.get("warnings") or []) + list(executed.get("warnings") or []))
        ),
    }
