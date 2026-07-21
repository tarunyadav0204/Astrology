"""
Natural-language audience builder: LLM → validated SELECT on admin_audience_user_facts → user table.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from db import execute, get_conn

from .audience_nl_schema import DISPLAY_COLUMNS, VIEW_NAME, schema_prompt_block

logger = logging.getLogger(__name__)

MAX_LIMIT = 2000
DEFAULT_LIMIT = 500
STATEMENT_TIMEOUT_MS = 8000

_FORBIDDEN = re.compile(
    r"\b("
    r"insert|update|delete|drop|alter|truncate|create|grant|revoke|copy|"
    r"execute|call|do|vacuum|analyze|comment|security|set\s+role|"
    r"pg_|dblink|lo_|into\s+outfile|load_file"
    r")\b",
    re.IGNORECASE,
)

_SQL_REL = os.path.join("migrations", "add_admin_audience_user_facts.sql")


def _migration_path() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), _SQL_REL)


def _users_has_column(conn, column_name: str) -> bool:
    cur = execute(
        conn,
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'users'
          AND column_name = %s
        LIMIT 1
        """,
        (column_name,),
    )
    return bool(cur.fetchone())


def ensure_admin_audience_user_facts_view() -> None:
    """Create or replace admin_audience_user_facts (idempotent)."""
    path = _migration_path()
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    except OSError as e:
        logger.warning("Could not read audience facts migration %s: %s", path, e)
        return

    # Strip full-line comments; keep single CREATE VIEW statement.
    lines = []
    for line in raw.splitlines():
        if re.match(r"^\s*--", line):
            continue
        lines.append(line)
    sql = "\n".join(lines).strip().rstrip(";")

    with get_conn() as conn:
        if not _users_has_column(conn, "whatsapp_wa_id"):
            sql = sql.replace(
                """    (
        COALESCE(NULLIF(btrim(u.whatsapp_wa_id), ''), '') <> ''
    ) AS has_whatsapp,""",
                "    FALSE AS has_whatsapp,",
            )
        # device_tokens may be missing on fresh DBs — create empty-safe view branch
        cur = execute(
            conn,
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'device_tokens'
            LIMIT 1
            """,
        )
        if not cur.fetchone():
            sql = sql.replace(
                """push AS (
    SELECT DISTINCT userid
    FROM device_tokens
)""",
                "push AS (SELECT NULL::integer AS userid WHERE FALSE)",
            )
        execute(conn, sql)
        conn.commit()
    logger.info("admin_audience_user_facts view ensured")


def _strip_sql_comments(sql: str) -> str:
    # Remove /* ... */ and -- line comments
    no_block = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    no_line = re.sub(r"--[^\n]*", " ", no_block)
    return no_line


def validate_audience_sql(sql: str) -> Tuple[str, List[str]]:
    """
    Validate LLM/admin SQL. Returns (normalized_sql, warnings).
    Raises ValueError on hard failures.
    """
    warnings: List[str] = []
    if not sql or not str(sql).strip():
        raise ValueError("SQL is empty")

    cleaned = _strip_sql_comments(str(sql)).strip().rstrip(";")
    if ";" in cleaned:
        raise ValueError("Only a single SQL statement is allowed")

    lowered = cleaned.lower()
    if not (lowered.lstrip().startswith("select") or lowered.lstrip().startswith("with")):
        raise ValueError("Only SELECT (or WITH ... SELECT) queries are allowed")

    if _FORBIDDEN.search(cleaned):
        raise ValueError("SQL contains forbidden keywords")

    # Must reference the curated view; block other FROM/JOIN targets loosely.
    if VIEW_NAME not in cleaned.lower():
        raise ValueError(f"Query must use {VIEW_NAME}")

    # Disallow other relation-looking FROM/JOIN identifiers (simple heuristic).
    for match in re.finditer(r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_\.]*)", cleaned, re.IGNORECASE):
        name = match.group(1).lower().split(".")[-1]
        if name != VIEW_NAME and name not in {"lateral"}:
            raise ValueError(f"Only {VIEW_NAME} may be queried (found {name})")

    # Force/clamp LIMIT
    limit_match = re.search(r"\blimit\s+(\d+)\b", cleaned, re.IGNORECASE)
    if limit_match:
        lim = int(limit_match.group(1))
        if lim > MAX_LIMIT:
            cleaned = re.sub(
                r"\blimit\s+\d+\b",
                f"LIMIT {MAX_LIMIT}",
                cleaned,
                count=1,
                flags=re.IGNORECASE,
            )
            warnings.append(f"LIMIT clamped to {MAX_LIMIT}")
    else:
        cleaned = f"{cleaned}\nLIMIT {DEFAULT_LIMIT}"
        warnings.append(f"Added LIMIT {DEFAULT_LIMIT}")

    return cleaned, warnings


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    raw = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.IGNORECASE)
    if fence:
        raw = fence.group(1).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _gemini_response_text(response: Any) -> str:
    try:
        t = (getattr(response, "text", None) or "").strip()
        if t:
            return t
    except Exception:
        pass
    parts: List[str] = []
    for cand in getattr(response, "candidates", None) or []:
        content = getattr(cand, "content", None)
        for p in getattr(content, "parts", None) or []:
            txt = getattr(p, "text", None)
            if txt:
                parts.append(txt)
    return "\n".join(parts).strip()


def _calendar_day_question_audience(prompt: str) -> Optional[Dict[str, Any]]:
    """Return an exact query for common yesterday-but-not-today audience requests."""
    text = " ".join(str(prompt or "").strip().lower().split())
    mentions_questions = bool(
        re.search(r"\b(question|questions|chat|chats|chatted|chatting)\b", text)
    )
    excludes_today = bool(
        re.search(
            r"\b(?:but\s+)?not\s+today\b|\bno\s+(?:paid\s+)?(?:questions?|chats?)\s+today\b",
            text,
        )
    )
    if "yesterday" not in text or not mentions_questions or not excludes_today:
        return None

    paid = bool(re.search(r"\b(paid|charged|credit[- ]charged)\b", text))
    yesterday_column = "paid_questions_yesterday" if paid else "questions_asked_yesterday"
    today_column = "paid_questions_today" if paid else "questions_asked_today"
    order_column = "last_paid_question_at" if paid else "last_user_chat_at"
    normalized, warnings = validate_audience_sql(
        f"""
        SELECT *
        FROM {VIEW_NAME}
        WHERE {yesterday_column} > 0
          AND {today_column} = 0
        ORDER BY {order_column} DESC NULLS LAST
        """
    )
    activity = "credit-charged questions" if paid else "questions"
    return {
        "explanation": (
            f"Users with one or more {activity} during yesterday's Asia/Kolkata calendar day "
            f"and zero {activity} during today's Asia/Kolkata calendar day."
        ),
        "sql": normalized,
        "warnings": warnings,
        "model_used": "deterministic-calendar-day",
    }


def validate_prompt_sql_alignment(prompt: str, sql: str) -> None:
    """Reject rolling-window proxies for explicit calendar-day question audiences."""
    text = " ".join(str(prompt or "").strip().lower().split())
    if "yesterday" not in text or not re.search(
        r"\b(question|questions|chat|chats|chatted|chatting)\b",
        text,
    ):
        return
    lowered_sql = str(sql or "").lower()
    paid = bool(re.search(r"\b(paid|charged|credit[- ]charged)\b", text))
    expected = "paid_questions_yesterday" if paid else "questions_asked_yesterday"
    if expected not in lowered_sql:
        raise ValueError(
            f"Calendar-day question audiences must use {expected}; rolling-window count differences are not allowed"
        )


def generate_audience_sql(prompt: str) -> Dict[str, Any]:
    """Ask Gemini for explanation + SELECT against admin_audience_user_facts."""
    user_prompt = (prompt or "").strip()
    if len(user_prompt) < 8:
        raise ValueError("Describe the audience in a bit more detail")
    if len(user_prompt) > 4000:
        user_prompt = user_prompt[:4000]

    exact_calendar_query = _calendar_day_question_audience(user_prompt)
    if exact_calendar_query:
        return exact_calendar_query

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

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

    system = f"""You are an analytics SQL assistant for AstroRoshni admin campaigns.

{schema_prompt_block()}

Rules:
1. Return ONLY a JSON object with keys: explanation (short English), sql (one SELECT).
2. SQL must be a single SELECT or WITH...SELECT against {VIEW_NAME} only.
3. Prefer filtering with WHERE on the view columns. Always include userid in the SELECT list (SELECT * is fine).
4. Do not invent columns. Do not use other tables.
5. Use UTC-aware comparisons with NOW() AT TIME ZONE 'UTC' when needed.
6. Add a reasonable ORDER BY (e.g. last_purchase_at DESC NULLS LAST) when helpful.
7. You may omit LIMIT; the server will add one.
8. For exact calendar days, use the exact *_today / *_yesterday columns. Never subtract rolling counts.
9. "Paid question" means a credit-charged question; use paid_questions_today, paid_questions_yesterday, or last_paid_question_at.
10. "Question" without "paid" uses questions_asked_today / questions_asked_yesterday for calendar-day requests.

Example audience: users who bought credits, still have balance, no chat in 14 days.
Example SQL:
SELECT *
FROM {VIEW_NAME}
WHERE lifetime_purchased_credits > 0
  AND credits_balance > 0
  AND (days_since_last_chat IS NULL OR days_since_last_chat >= 14)
ORDER BY last_purchase_at DESC NULLS LAST
"""

    response = model.generate_content(
        f"{system}\n\nAdmin request:\n{user_prompt}",
        generation_config={"temperature": 0.2},
    )
    text = _gemini_response_text(response)
    parsed = _extract_json_object(text)
    if not parsed:
        raise RuntimeError("Model did not return valid JSON")

    explanation = str(parsed.get("explanation") or "").strip()
    sql = str(parsed.get("sql") or "").strip()
    if not sql:
        # Sometimes models put SQL in a code fence key
        sql = str(parsed.get("query") or "").strip()
    normalized, warnings = validate_audience_sql(sql)
    validate_prompt_sql_alignment(user_prompt, normalized)
    return {
        "explanation": explanation or "Audience filter generated.",
        "sql": normalized,
        "warnings": warnings,
        "model_used": used_name,
    }


def _serialize_cell(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat()
        return value.isoformat()
    if isinstance(value, bool):
        return value
    if hasattr(value, "as_integer_ratio") and not isinstance(value, bool):
        # Decimal / numeric
        try:
            return float(value)
        except Exception:
            return str(value)
    return value


def _audience_user_ids_sql(normalized_sql: str, *, push_only: bool = False) -> str:
    push_clause = ""
    if push_only:
        push_clause = f"""
        AND EXISTS (
            SELECT 1
            FROM {VIEW_NAME} AS push_facts
            WHERE push_facts.userid = audience_sub.userid
              AND push_facts.has_device_token = TRUE
        )
        """
    return f"""
    SELECT DISTINCT userid
    FROM (
        {normalized_sql}
    ) AS audience_sub
    WHERE userid IS NOT NULL
    {push_clause}
    """


def execute_audience_sql(
    sql: str,
    *,
    page: int = 1,
    page_size: int = 50,
    push_only: bool = False,
) -> Dict[str, Any]:
    """
    Run validated filter SQL, then return DISPLAY_COLUMNS rows for matching userids.
    """
    normalized, warnings = validate_audience_sql(sql)
    page = max(1, int(page or 1))
    page_size = max(1, min(200, int(page_size or 50)))

    # Ensure filter query returns userid; wrap to collect ids.
    wrap_sql = _audience_user_ids_sql(normalized, push_only=bool(push_only))

    with get_conn() as conn:
        try:
            execute(conn, f"SET statement_timeout = {int(STATEMENT_TIMEOUT_MS)}")
        except Exception:
            pass

        try:
            try:
                cur = execute(conn, wrap_sql)
            except Exception as e:
                logger.warning("audience_nl execute failed: %s | sql=%s", e, normalized[:500])
                raise ValueError(f"Query failed: {e}") from e

            id_rows = cur.fetchall() or []
            user_ids = [int(r[0]) for r in id_rows if r and r[0] is not None]
            total = len(user_ids)
            truncated = total >= MAX_LIMIT

            if not user_ids:
                return {
                    "columns": DISPLAY_COLUMNS,
                    "rows": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "truncated": False,
                    "warnings": warnings,
                    "sql": normalized,
                    "user_ids": [],
                    "push_only": bool(push_only),
                }

            offset = (page - 1) * page_size
            page_ids = user_ids[offset : offset + page_size]
            cols_sql = ", ".join(DISPLAY_COLUMNS)
            cur = execute(
                conn,
                f"""
                SELECT {cols_sql}
                FROM {VIEW_NAME}
                WHERE userid = ANY(%s)
                """,
                (page_ids,),
            )
            colnames = [d[0] for d in (cur.description or [])]
            raw_rows = cur.fetchall() or []
            by_id = {}
            for row in raw_rows:
                item = {colnames[i]: _serialize_cell(row[i]) for i in range(len(colnames))}
                by_id[int(item["userid"])] = item

            # Preserve filter order
            ordered = [by_id[uid] for uid in page_ids if uid in by_id]
        finally:
            try:
                execute(conn, "SET statement_timeout = 0")
            except Exception:
                pass

    return {
        "columns": DISPLAY_COLUMNS,
        "rows": ordered,
        "total": total,
        "page": page,
        "page_size": page_size,
        "truncated": bool(truncated and total >= MAX_LIMIT),
        "warnings": warnings,
        "sql": normalized,
        "user_ids": user_ids,
        "push_only": bool(push_only),
    }


def generate_and_run(
    prompt: str,
    *,
    page: int = 1,
    page_size: int = 50,
    push_only: bool = False,
) -> Dict[str, Any]:
    generated = generate_audience_sql(prompt)
    executed = execute_audience_sql(
        generated["sql"],
        page=page,
        page_size=page_size,
        push_only=push_only,
    )
    return {
        **executed,
        "explanation": generated.get("explanation"),
        "model_used": generated.get("model_used"),
        "warnings": list(
            dict.fromkeys(
                list(generated.get("warnings") or []) + list(executed.get("warnings") or [])
            )
        ),
        "prompt": (prompt or "").strip()[:4000],
    }
