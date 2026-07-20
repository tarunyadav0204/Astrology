"""
Natural-language admin analytics: LLM -> validated aggregate SELECT on a curated view.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Tuple

from db import execute, get_conn

from .analytics_nl_schema import VIEW_NAME, schema_prompt_block
from .audience_nl import (
    STATEMENT_TIMEOUT_MS,
    _extract_json_object,
    _gemini_response_text,
    _strip_sql_comments,
)

logger = logging.getLogger(__name__)

MAX_ROWS = 200
_SQL_REL = os.path.join("migrations", "add_admin_analytics_purchase_facts.sql")
_FORBIDDEN = re.compile(
    r"\b("
    r"insert|update|delete|drop|alter|truncate|create|grant|revoke|copy|"
    r"execute|call|do|vacuum|analyze|comment|security|set\s+role|"
    r"pg_|dblink|lo_|into\s+outfile|load_file"
    r")\b",
    re.IGNORECASE,
)
_AGGREGATE = re.compile(r"\b(count|sum|avg|min|max)\s*\(", re.IGNORECASE)


def _migration_path() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), _SQL_REL)


def ensure_admin_analytics_purchase_facts_view() -> None:
    try:
        with open(_migration_path(), encoding="utf-8") as f:
            raw = f.read()
    except OSError as exc:
        logger.warning("Could not read analytics facts migration: %s", exc)
        return
    sql = "\n".join(
        line for line in raw.splitlines() if not re.match(r"^\s*--", line)
    ).strip().rstrip(";")
    with get_conn() as conn:
        execute(conn, sql)
        conn.commit()
    logger.info("%s view ensured", VIEW_NAME)


def validate_analytics_sql(sql: str) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    if not sql or not str(sql).strip():
        raise ValueError("SQL is empty")
    cleaned = _strip_sql_comments(str(sql)).strip().rstrip(";")
    if ";" in cleaned:
        raise ValueError("Only a single SQL statement is allowed")
    if not cleaned.lower().lstrip().startswith("select"):
        raise ValueError("Analytics SQL must be a SELECT query")
    if _FORBIDDEN.search(cleaned):
        raise ValueError("SQL contains forbidden keywords")
    if VIEW_NAME not in cleaned.lower():
        raise ValueError(f"Query must use {VIEW_NAME}")
    for match in re.finditer(
        r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)", cleaned, re.IGNORECASE
    ):
        name = match.group(1).lower().split(".")[-1]
        if name != VIEW_NAME:
            raise ValueError(f"Only {VIEW_NAME} may be queried (found {name})")
    if not _AGGREGATE.search(cleaned):
        raise ValueError("Analytics queries must contain an aggregate such as SUM or COUNT")
    if re.search(r"\bselect\s+\*", cleaned, re.IGNORECASE):
        raise ValueError("Analytics queries may not select raw purchase rows")
    select_list = re.split(r"\bfrom\b", cleaned, maxsplit=1, flags=re.IGNORECASE)[0]
    safe_select_list = re.sub(
        r"\bcount\s*\(\s*distinct\s+(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?"
        r"(?:userid|transaction_id)\s*\)",
        "COUNT_SAFE_IDENTIFIER",
        select_list,
        flags=re.IGNORECASE,
    )
    if re.search(r"\b(userid|transaction_id)\b", safe_select_list, re.IGNORECASE):
        raise ValueError("Analytics queries may not return raw user or transaction identifiers")

    limit_match = re.search(r"\blimit\s+(\d+)\b", cleaned, re.IGNORECASE)
    if limit_match:
        if int(limit_match.group(1)) > MAX_ROWS:
            cleaned = re.sub(
                r"\blimit\s+\d+\b", f"LIMIT {MAX_ROWS}", cleaned, count=1, flags=re.IGNORECASE
            )
            warnings.append(f"LIMIT clamped to {MAX_ROWS}")
    else:
        cleaned = f"{cleaned}\nLIMIT {MAX_ROWS}"
        warnings.append(f"Added LIMIT {MAX_ROWS}")
    return cleaned, warnings


def generate_analytics_sql(prompt: str) -> Dict[str, Any]:
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    import google.generativeai as genai
    from .chat_nudge_suggestion import _nudge_suggestion_model_names

    user_prompt = (prompt or "").strip()
    if len(user_prompt) < 8:
        raise ValueError("Describe the analytics question in a bit more detail")
    user_prompt = user_prompt[:4000]

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

    system = f"""You are an analytics SQL assistant for AstroRoshni admins.

{schema_prompt_block()}

Rules:
1. Return ONLY JSON with keys explanation and sql.
2. SQL must be one aggregate SELECT against {VIEW_NAME} only. Do not use WITH or subqueries.
3. Never SELECT raw transaction_id or userid. They may appear only inside COUNT(DISTINCT ...).
4. Do not invent columns or query other tables.
5. Give every aggregate a clear snake_case alias.
6. Use FILTER for conditional aggregates when useful.
7. Use UTC calendar boundaries. "This month" starts at
   date_trunc('month', NOW() AT TIME ZONE 'UTC') and ends before the next month.
8. For money totals, include currency in SELECT and GROUP BY currency. Never add unlike currencies.
9. purchase_amount can be NULL, so include COUNT(purchase_amount) as purchases_with_amount when useful.
10. Omit LIMIT; the server adds it.

Example question: total credit purchases this month
Example SQL:
SELECT
  currency,
  COUNT(*) AS purchase_count,
  COUNT(DISTINCT userid) AS unique_buyers,
  SUM(credits_purchased) AS gross_credits_purchased,
  SUM(net_credits_purchased) AS net_credits_purchased,
  SUM(purchase_amount) AS total_purchase_amount,
  COUNT(purchase_amount) AS purchases_with_amount
FROM {VIEW_NAME}
WHERE purchased_at >= date_trunc('month', NOW() AT TIME ZONE 'UTC')
  AND purchased_at < date_trunc('month', NOW() AT TIME ZONE 'UTC') + INTERVAL '1 month'
GROUP BY currency
ORDER BY currency
"""
    response = model.generate_content(
        f"{system}\n\nAdmin question:\n{user_prompt}",
        generation_config={"temperature": 0.1},
    )
    parsed = _extract_json_object(_gemini_response_text(response))
    if not parsed:
        raise RuntimeError("Model did not return valid JSON")
    raw_sql = str(parsed.get("sql") or parsed.get("query") or "").strip()
    normalized, warnings = validate_analytics_sql(raw_sql)
    return {
        "explanation": str(parsed.get("explanation") or "").strip()
        or "Analytics query generated.",
        "sql": normalized,
        "warnings": warnings,
        "model_used": used_name,
    }


def _serialize(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return (
            value.replace(tzinfo=timezone.utc).isoformat()
            if value.tzinfo is None
            else value.isoformat()
        )
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def execute_analytics_sql(sql: str) -> Dict[str, Any]:
    normalized, warnings = validate_analytics_sql(sql)
    with get_conn() as conn:
        try:
            execute(conn, f"SET statement_timeout = {int(STATEMENT_TIMEOUT_MS)}")
        except Exception:
            pass
        try:
            try:
                cur = execute(conn, normalized)
            except Exception as exc:
                logger.warning("analytics_nl execute failed: %s | sql=%s", exc, normalized[:500])
                raise ValueError(f"Query failed: {exc}") from exc
            columns = [d[0] for d in (cur.description or [])]
            rows = [
                {columns[i]: _serialize(row[i]) for i in range(len(columns))}
                for row in (cur.fetchall() or [])
            ]
        finally:
            try:
                execute(conn, "SET statement_timeout = 0")
            except Exception:
                pass
    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "warnings": warnings,
        "sql": normalized,
    }


def generate_and_run_analytics(prompt: str) -> Dict[str, Any]:
    generated = generate_analytics_sql(prompt)
    executed = execute_analytics_sql(generated["sql"])
    return {
        **executed,
        "explanation": generated.get("explanation"),
        "model_used": generated.get("model_used"),
        "warnings": list(
            dict.fromkeys(
                list(generated.get("warnings") or []) + list(executed.get("warnings") or [])
            )
        ),
    }
