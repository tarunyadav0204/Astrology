"""
Admin-only: full per-user profile (Postgres + BigQuery activity) for support and debugging.
"""
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query

from auth import get_current_user, User
from db import get_conn_dict

logger = logging.getLogger(__name__)

router = APIRouter()

_INSIGHTS_PREVIEW_CHARS = 12000


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _json_safe(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime,)):
        return v.isoformat() if hasattr(v, "isoformat") else str(v)
    return v


def _row_dict(row: Any) -> Dict[str, Any]:
    if hasattr(row, "keys"):
        return {k: _json_safe(row[k]) for k in row.keys()}
    return {}


# Store purchases use add_credits → transaction_type "earned" with these sources.
_CREDIT_PURCHASE_SOURCES = frozenset({"google_play", "razorpay"})


def _credit_rollups(transactions: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Credits in: add_credits always uses transaction_type "earned" (even for admin adjustments).
    refund_credits uses transaction_type "refund". Spent rows store negative amount.
    Split "earned" by source so purchases (Play/Razorpay) are separate from admin/promo/refund rows.
    """
    purchased = 0
    refund_svc = 0
    promo = 0
    admin_grants = 0
    other_earned = 0
    spent = 0
    for t in transactions:
        tt = (t.get("transaction_type") or "").strip().lower()
        src = (t.get("source") or "").strip().lower()
        try:
            amt = int(t.get("amount") or 0)
        except (TypeError, ValueError):
            amt = 0
        if tt == "spent":
            spent += -amt
        elif tt == "refund":
            refund_svc += amt
        elif tt == "earned":
            if src in _CREDIT_PURCHASE_SOURCES:
                purchased += amt
            elif src == "promo_code":
                promo += amt
            elif src in ("admin_adjustment", "admin_approval"):
                admin_grants += amt
            else:
                other_earned += amt
    non_store = refund_svc + promo + admin_grants + other_earned
    received_total = purchased + non_store
    return {
        "credits_purchased": purchased,
        "credits_refunds": refund_svc,
        "credits_promo": promo,
        "credits_admin_grants": admin_grants,
        "credits_other_received": other_earned,
        "credits_non_store_total": non_store,
        "credits_received_total": received_total,
        "credits_spent": spent,
    }


def _parse_profile_dates(
    date_from: Optional[str], date_to: Optional[str]
) -> Tuple[str, str]:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    to_date = (date_to or "").strip() or today
    if not date_from or not str(date_from).strip():
        to_d = datetime.strptime(to_date, "%Y-%m-%d").date()
        from_d = to_d - timedelta(days=90)
        from_date = from_d.isoformat()
    else:
        from_date = str(date_from).strip()
    return from_date, to_date


def _search_users_by_query(q: str, limit: int = 40) -> List[Dict[str, Any]]:
    q = (q or "").strip()
    if not q:
        return []
    pat = f"%{q}%"
    phone_digits = "".join(c for c in q if c.isdigit())
    digit_pat = f"%{phone_digits}%" if len(phone_digits) >= 3 else None
    with get_conn_dict() as conn:
        cur = conn.cursor()
        if digit_pat:
            cur.execute(
                """
                SELECT userid, name, phone, email
                FROM users
                WHERE COALESCE(TRIM(name), '') ILIKE %s
                   OR COALESCE(TRIM(email), '') ILIKE %s
                   OR COALESCE(phone::text, '') ILIKE %s
                   OR regexp_replace(COALESCE(phone::text, ''), '[^0-9]', '', 'g') LIKE %s
                ORDER BY userid DESC
                LIMIT %s
                """,
                (pat, pat, pat, digit_pat, limit),
            )
        else:
            cur.execute(
                """
                SELECT userid, name, phone, email
                FROM users
                WHERE COALESCE(TRIM(name), '') ILIKE %s
                   OR COALESCE(TRIM(email), '') ILIKE %s
                   OR COALESCE(phone::text, '') ILIKE %s
                ORDER BY userid DESC
                LIMIT %s
                """,
                (pat, pat, pat, limit),
            )
        return [_row_dict(r) for r in (cur.fetchall() or [])]


def _build_user_profile_payload(user_id: int, from_date: str, to_date: str) -> Dict[str, Any]:
    profile: Dict[str, Any] = {
        "user_id": user_id,
        "date_from": from_date,
        "date_to": to_date,
        "ambiguous": False,
        "matches": [],
        "user": None,
        "summary": {},
        "chat_questions": [],
        "bigquery_activity": [],
        "insights": {
            "health": [],
            "wealth": [],
            "marriage": [],
            "education": [],
            "career": [],
        },
        "karma_insights": [],
        "event_timeline_jobs": [],
        "credit_transactions": [],
        "trading": {"daily": [], "monthly": []},
    }

    try:
        with get_conn_dict() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT u.userid, u.name, u.phone, u.email, u.role, u.created_at,
                       COALESCE(uc.credits, 0) AS credits_balance,
                       COALESCE(uc.free_chat_question_used, 0) AS free_chat_question_used
                FROM users u
                LEFT JOIN user_credits uc ON uc.userid = u.userid
                WHERE u.userid = %s
                """,
                (user_id,),
            )
            urow = cur.fetchone()
            if not urow:
                raise HTTPException(status_code=404, detail="User not found")
            profile["user"] = _row_dict(urow)

            cur.execute(
                """
                SELECT cm.message_id, cm.session_id, cm.content, cm.timestamp, cm.category, cm.canonical_question
                FROM chat_messages cm
                INNER JOIN chat_sessions cs ON cs.session_id = cm.session_id
                WHERE cs.user_id = %s
                  AND cm.sender = 'user'
                  AND DATE(cm.timestamp) >= %s::date
                  AND DATE(cm.timestamp) <= %s::date
                ORDER BY cm.timestamp DESC
                LIMIT 2000
                """,
                (user_id, from_date, to_date),
            )
            profile["chat_questions"] = [_row_dict(r) for r in (cur.fetchall() or [])]

            def _fetch_insights(table: str) -> List[Dict[str, Any]]:
                cur.execute(
                    f"""
                    SELECT id, userid, birth_hash,
                           LEFT(COALESCE(insights_data, ''), {_INSIGHTS_PREVIEW_CHARS}) AS insights_preview,
                           created_at, updated_at
                    FROM {table}
                    WHERE userid = %s
                      AND DATE(created_at) >= %s::date
                      AND DATE(created_at) <= %s::date
                    ORDER BY created_at DESC
                    LIMIT 500
                    """,
                    (user_id, from_date, to_date),
                )
                return [_row_dict(r) for r in (cur.fetchall() or [])]

            profile["insights"]["health"] = _fetch_insights("ai_health_insights")
            profile["insights"]["wealth"] = _fetch_insights("ai_wealth_insights")
            profile["insights"]["marriage"] = _fetch_insights("ai_marriage_insights")
            profile["insights"]["education"] = _fetch_insights("ai_education_insights")
            profile["insights"]["career"] = _fetch_insights("ai_career_insights")

            cur.execute(
                """
                SELECT id, chart_id, user_id, status,
                       LEFT(COALESCE(karma_context, ''), 4000) AS karma_context_preview,
                       LEFT(COALESCE(ai_interpretation, ''), 8000) AS ai_interpretation_preview,
                       created_at, updated_at
                FROM karma_insights
                WHERE user_id = %s
                  AND DATE(created_at) >= %s::date
                  AND DATE(created_at) <= %s::date
                ORDER BY created_at DESC
                LIMIT 500
                """,
                (user_id, from_date, to_date),
            )
            profile["karma_insights"] = [_row_dict(r) for r in (cur.fetchall() or [])]

            cur.execute(
                """
                SELECT job_id, user_id, birth_chart_id, selected_year, selected_month, status,
                       LEFT(COALESCE(result_data, ''), 8000) AS result_preview,
                       error_message, created_at, started_at, completed_at
                FROM event_timeline_jobs
                WHERE user_id = %s
                  AND DATE(created_at) >= %s::date
                  AND DATE(created_at) <= %s::date
                ORDER BY created_at DESC
                LIMIT 500
                """,
                (user_id, from_date, to_date),
            )
            profile["event_timeline_jobs"] = [_row_dict(r) for r in (cur.fetchall() or [])]

            cur.execute(
                """
                SELECT id, userid, transaction_type, amount, balance_after, source, reference_id,
                       description, created_at
                FROM credit_transactions
                WHERE userid = %s
                  AND DATE(created_at) >= %s::date
                  AND DATE(created_at) <= %s::date
                ORDER BY created_at DESC
                LIMIT 2000
                """,
                (user_id, from_date, to_date),
            )
            profile["credit_transactions"] = [_row_dict(r) for r in (cur.fetchall() or [])]

            cur.execute(
                """
                SELECT id, cache_key, user_id, target_date,
                       LEFT(COALESCE(analysis_data, ''), 8000) AS analysis_preview,
                       created_at
                FROM trading_daily_cache
                WHERE user_id = %s
                  AND DATE(created_at) >= %s::date
                  AND DATE(created_at) <= %s::date
                ORDER BY created_at DESC
                LIMIT 500
                """,
                (user_id, from_date, to_date),
            )
            profile["trading"]["daily"] = [_row_dict(r) for r in (cur.fetchall() or [])]

            cur.execute(
                """
                SELECT id, cache_key, user_id, year, month,
                       LEFT(COALESCE(analysis_data, ''), 8000) AS analysis_preview,
                       created_at
                FROM trading_monthly_cache
                WHERE user_id = %s
                  AND DATE(created_at) >= %s::date
                  AND DATE(created_at) <= %s::date
                ORDER BY created_at DESC
                LIMIT 200
                """,
                (user_id, from_date, to_date),
            )
            profile["trading"]["monthly"] = [_row_dict(r) for r in (cur.fetchall() or [])]

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("admin user profile postgres failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    try:
        from activity.admin_routes import fetch_activity_rows_for_user

        profile["bigquery_activity"] = fetch_activity_rows_for_user(
            user_id, from_date, to_date, limit=2000
        )
    except Exception as e:
        logger.warning("admin user profile BigQuery: %s", e)
        profile["bigquery_activity"] = []

    ins = profile["insights"]
    credit_r = _credit_rollups(profile["credit_transactions"])
    profile["summary"] = {
        "chat_questions_count": len(profile["chat_questions"]),
        "bigquery_activity_count": len(profile["bigquery_activity"]),
        "insights_counts": {
            "health": len(ins["health"]),
            "wealth": len(ins["wealth"]),
            "marriage": len(ins["marriage"]),
            "education": len(ins["education"]),
            "career": len(ins["career"]),
        },
        "karma_insights_count": len(profile["karma_insights"]),
        "event_timeline_jobs_count": len(profile["event_timeline_jobs"]),
        "credit_transactions_count": len(profile["credit_transactions"]),
        "credits_purchased": credit_r["credits_purchased"],
        "credits_refunds": credit_r["credits_refunds"],
        "credits_promo": credit_r["credits_promo"],
        "credits_admin_grants": credit_r["credits_admin_grants"],
        "credits_other_received": credit_r["credits_other_received"],
        "credits_non_store_total": credit_r["credits_non_store_total"],
        "credits_received_total": credit_r["credits_received_total"],
        "credits_spent": credit_r["credits_spent"],
        "trading_daily_count": len(profile["trading"]["daily"]),
        "trading_monthly_count": len(profile["trading"]["monthly"]),
    }

    return profile


@router.get("/admin/users/profile")
async def get_admin_user_profile_by_search(
    q: str = Query(..., min_length=1, description="Name, email, or phone (partial match)"),
    date_from: Optional[str] = Query(None, description="Start date YYYY-MM-DD (default: 90 days ago)"),
    date_to: Optional[str] = Query(None, description="End date YYYY-MM-DD (default: today UTC)"),
    current_user: User = Depends(_require_admin),
):
    """
    Resolve user by display name, email, or phone; return full profile if exactly one match,
    or ambiguous matches for the UI to choose from.
    """
    from_date, to_date = _parse_profile_dates(date_from, date_to)
    matches = _search_users_by_query(q)
    if not matches:
        raise HTTPException(status_code=404, detail="No user matches that search.")
    if len(matches) > 1:
        return {
            "ambiguous": True,
            "matches": matches,
            "date_from": from_date,
            "date_to": to_date,
            "search_query": q.strip(),
        }
    uid = int(matches[0]["userid"])
    return _build_user_profile_payload(uid, from_date, to_date)


@router.get("/admin/users/{user_id}/profile")
async def get_admin_user_profile(
    user_id: int,
    date_from: Optional[str] = Query(None, description="Start date YYYY-MM-DD (default: 90 days ago)"),
    date_to: Optional[str] = Query(None, description="End date YYYY-MM-DD (default: today UTC)"),
    current_user: User = Depends(_require_admin),
):
    """
    Aggregated view: user row, chat questions, AI insight rows, karma, timeline jobs,
    credits, trading caches, and BigQuery activity for the user_id.
    """
    from_date, to_date = _parse_profile_dates(date_from, date_to)
    return _build_user_profile_payload(user_id, from_date, to_date)
