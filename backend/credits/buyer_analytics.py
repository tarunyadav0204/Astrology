"""Admin buyer analysis: week × UTM, new vs repeat, cohorts.

Designed for the shared API pool:
- one short-lived connection per request
- SET LOCAL statement_timeout so heavy admin scans cannot stall chat
- bounded date window
- index-friendly timestamptz predicates
- tiny in-process TTL cache to absorb refresh spam
- never CREATE INDEX on the request path (catalog peek only)
"""
from __future__ import annotations

import json
import logging
import threading
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from db import execute, get_conn

logger = logging.getLogger(__name__)

_ADMIN_TZ = "Asia/Kolkata"
_MAX_RANGE_DAYS = 182  # ~26 weeks
_DEFAULT_RANGE_DAYS = 84  # 12 weeks
_STATEMENT_TIMEOUT_MS = 15_000
_CACHE_TTL_SEC = 90.0
_CACHE_LOCK = threading.Lock()
_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_INDEXES_READY = False
_INDEXES_LOCK = threading.Lock()

_CHANNEL_SQL = {
    "source": "COALESCE(NULLIF(btrim(u.utm_source), ''), '(none)')",
    "medium": "COALESCE(NULLIF(btrim(u.utm_medium), ''), '(none)')",
    "campaign": "COALESCE(NULLIF(btrim(u.utm_campaign), ''), '(none)')",
    "source_medium": (
        "COALESCE(NULLIF(btrim(u.utm_source), ''), '(none)')"
        " || ' / ' || "
        "COALESCE(NULLIF(btrim(u.utm_medium), ''), '(none)')"
    ),
}


def _parse_date(value: Optional[str], fallback: date) -> date:
    if not value:
        return fallback
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return fallback


def _admin_today() -> date:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo(_ADMIN_TZ)).date()
    except Exception:
        return datetime.now(timezone.utc).date()


def _normalize_range(
    from_date: Optional[str],
    to_date: Optional[str],
) -> Tuple[date, date]:
    today = _admin_today()
    td = _parse_date(to_date, today)
    fd = _parse_date(from_date, td - timedelta(days=_DEFAULT_RANGE_DAYS - 1))
    if fd > td:
        fd, td = td, fd
    if (td - fd).days + 1 > _MAX_RANGE_DAYS:
        fd = td - timedelta(days=_MAX_RANGE_DAYS - 1)
    return fd, td


def _cache_key(fd: date, td: date, group_by: str) -> str:
    return f"{fd.isoformat()}|{td.isoformat()}|{group_by}"


def _cache_get(key: str) -> Optional[Dict[str, Any]]:
    now = time.monotonic()
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
        if not hit:
            return None
        expires_at, payload = hit
        if expires_at < now:
            _CACHE.pop(key, None)
            return None
        out = dict(payload)
        out["cached"] = True
        return out


def _cache_set(key: str, payload: Dict[str, Any]) -> None:
    with _CACHE_LOCK:
        if len(_CACHE) > 64:
            oldest = sorted(_CACHE.items(), key=lambda kv: kv[1][0])[:16]
            for old_key, _ in oldest:
                _CACHE.pop(old_key, None)
        _CACHE[key] = (time.monotonic() + _CACHE_TTL_SEC, dict(payload))


# Recommended indexes (create offline / migration — never on the request path):
#   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ct_paid_created
#     ON credit_transactions (created_at DESC)
#     WHERE transaction_type = 'earned' AND source IN ('google_play', 'razorpay');
#   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ct_paid_userid_created
#     ON credit_transactions (userid, created_at)
#     WHERE transaction_type = 'earned' AND source IN ('google_play', 'razorpay');
#   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_app_installations_userid_first_open
#     ON app_installations (userid, first_open_at)
#     WHERE userid IS NOT NULL;
# Existing credit_service indexes (idx_credit_tx_source_type_created, idx_credit_tx_created_at)
# already cover most of the purchase range scan.


def _note_helpful_indexes(conn) -> None:
    """One-shot catalog peek; never CREATE INDEX (avoids locking credit_transactions)."""
    global _INDEXES_READY
    if _INDEXES_READY:
        return
    with _INDEXES_LOCK:
        if _INDEXES_READY:
            return
        try:
            execute(conn, f"SET LOCAL statement_timeout = '2000'")
            cur = execute(
                conn,
                """
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = ANY (current_schemas(false))
                  AND indexname IN (
                    'idx_ct_paid_created',
                    'idx_ct_paid_userid_created',
                    'idx_credit_tx_source_type_created',
                    'idx_credit_tx_created_at',
                    'idx_app_installations_userid_first_open'
                  )
                """,
            )
            found = {r[0] for r in (cur.fetchall() or [])}
            if not found.intersection(
                {
                    "idx_ct_paid_created",
                    "idx_credit_tx_source_type_created",
                    "idx_credit_tx_created_at",
                }
            ):
                logger.warning(
                    "buyer_analytics: no paid-purchase index found; queries may be slower. "
                    "Run migrations/add_buyer_analytics_indexes.sql offline (CONCURRENTLY preferred)."
                )
            _INDEXES_READY = True
        except Exception:
            logger.warning("buyer_analytics index catalog peek skipped", exc_info=True)
            try:
                conn.rollback()
            except Exception:
                pass
            # Don't retry every request if catalog is unavailable
            _INDEXES_READY = True


def _revenue_inr_sql(alias: str = "ct") -> str:
    meta = f"{alias}.metadata"
    return f"""
    CASE
      WHEN {meta} IS NULL OR btrim({meta}::text) = '' THEN NULL
      WHEN {meta}::text ~ '"amount_paise"[[:space:]]*:[[:space:]]*[0-9]+'
        THEN (substring({meta}::text from '"amount_paise"[[:space:]]*:[[:space:]]*([0-9]+)')::numeric / 100.0)
      WHEN {meta}::text ~ '"price_amount_micros"[[:space:]]*:[[:space:]]*[0-9]+'
        THEN (substring({meta}::text from '"price_amount_micros"[[:space:]]*:[[:space:]]*([0-9]+)')::numeric / 1000000.0)
      ELSE NULL
    END
    """


def _as_dict(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if hasattr(raw, "keys"):
        return dict(raw)
    if isinstance(raw, (bytes, bytearray)):
        return json.loads(raw.decode("utf-8"))
    if isinstance(raw, str):
        return json.loads(raw)
    return {}


def get_buyer_analytics(
    *,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    group_by: str = "source",
) -> Dict[str, Any]:
    fd, td = _normalize_range(from_date, to_date)
    gb = str(group_by or "source").strip().lower()
    if gb not in _CHANNEL_SQL:
        gb = "source"
    channel_sql = _CHANNEL_SQL[gb]

    cache_key = _cache_key(fd, td, gb)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    started = time.perf_counter()
    sql = f"""
    WITH bounds AS (
      SELECT
        (%s::timestamp AT TIME ZONE '{_ADMIN_TZ}') AS range_start,
        ((%s::date + 1)::timestamp AT TIME ZONE '{_ADMIN_TZ}') AS range_end
    ),
    purchases AS (
      SELECT
        ct.userid,
        ct.amount::bigint AS credits,
        ct.source,
        ct.created_at,
        {_revenue_inr_sql('ct')} AS revenue_inr,
        (
          date_trunc(
            'week',
            ((ct.created_at AT TIME ZONE 'UTC') AT TIME ZONE '{_ADMIN_TZ}')
          )
        )::date AS week_start
      FROM credit_transactions ct
      CROSS JOIN bounds b
      WHERE ct.transaction_type = 'earned'
        AND ct.source IN ('google_play', 'razorpay')
        AND ct.created_at >= b.range_start
        AND ct.created_at < b.range_end
    ),
    buyer_ids AS (
      SELECT DISTINCT userid FROM purchases
    ),
    user_first AS (
      SELECT ct.userid, MIN(ct.created_at) AS first_purchase_at
      FROM credit_transactions ct
      INNER JOIN buyer_ids b ON b.userid = ct.userid
      WHERE ct.transaction_type = 'earned'
        AND ct.source IN ('google_play', 'razorpay')
      GROUP BY ct.userid
    ),
    user_utm AS (
      SELECT DISTINCT ON (ai.userid)
        ai.userid,
        ai.utm_source,
        ai.utm_medium,
        ai.utm_campaign,
        ai.first_open_at
      FROM app_installations ai
      INNER JOIN buyer_ids b ON b.userid = ai.userid
      WHERE ai.userid IS NOT NULL
      ORDER BY ai.userid, ai.first_open_at ASC NULLS LAST
    ),
    enriched AS (
      SELECT
        p.userid,
        p.credits,
        p.source,
        p.created_at,
        p.revenue_inr,
        p.week_start,
        uf.first_purchase_at,
        (
          date_trunc(
            'week',
            ((uf.first_purchase_at AT TIME ZONE 'UTC') AT TIME ZONE '{_ADMIN_TZ}')
          )
        )::date AS first_week,
        {channel_sql} AS channel,
        u.first_open_at
      FROM purchases p
      INNER JOIN user_first uf ON uf.userid = p.userid
      LEFT JOIN user_utm u ON u.userid = p.userid
    ),
    kpis AS (
      SELECT
        COUNT(*)::bigint AS purchase_count,
        COUNT(DISTINCT userid)::bigint AS unique_buyers,
        COALESCE(SUM(credits), 0)::bigint AS credits_purchased,
        COALESCE(SUM(revenue_inr), 0)::float8 AS estimated_revenue_inr,
        COUNT(DISTINCT userid) FILTER (WHERE first_week = week_start)::bigint AS new_buyers,
        COUNT(DISTINCT userid) FILTER (WHERE first_week < week_start)::bigint AS repeat_buyers
      FROM enriched
    ),
    weekly_nr AS (
      SELECT
        week_start,
        COUNT(*)::bigint AS purchase_count,
        COUNT(DISTINCT userid)::bigint AS buyers,
        COALESCE(SUM(credits), 0)::bigint AS credits,
        COALESCE(SUM(revenue_inr), 0)::float8 AS revenue_inr,
        COUNT(DISTINCT userid) FILTER (WHERE first_week = week_start)::bigint AS new_buyers,
        COUNT(DISTINCT userid) FILTER (WHERE first_week < week_start)::bigint AS repeat_buyers
      FROM enriched
      GROUP BY week_start
    ),
    weekly_ch AS (
      SELECT
        week_start,
        channel,
        COUNT(*)::bigint AS purchase_count,
        COUNT(DISTINCT userid)::bigint AS buyers,
        COALESCE(SUM(credits), 0)::bigint AS credits,
        COALESCE(SUM(revenue_inr), 0)::float8 AS revenue_inr,
        COUNT(DISTINCT userid) FILTER (WHERE first_week = week_start)::bigint AS new_buyers,
        COUNT(DISTINCT userid) FILTER (WHERE first_week < week_start)::bigint AS repeat_buyers
      FROM enriched
      GROUP BY week_start, channel
    ),
    leaderboard AS (
      SELECT
        channel,
        COUNT(*)::bigint AS purchase_count,
        COUNT(DISTINCT userid)::bigint AS buyers,
        COALESCE(SUM(credits), 0)::bigint AS credits,
        COALESCE(SUM(revenue_inr), 0)::float8 AS revenue_inr,
        COUNT(DISTINCT userid) FILTER (
          WHERE first_week >= %s::date AND first_week <= %s::date
        )::bigint AS new_buyers_in_range,
        COUNT(DISTINCT userid) FILTER (WHERE first_week < week_start)::bigint AS repeat_purchase_users,
        ROUND(
          (
            PERCENTILE_CONT(0.5) WITHIN GROUP (
              ORDER BY EXTRACT(EPOCH FROM (first_purchase_at - first_open_at)) / 86400.0
            )
          )::numeric,
          1
        ) AS median_days_install_to_first_buy
      FROM enriched
      GROUP BY channel
    ),
    cohort_base AS (
      SELECT DISTINCT userid, first_week AS cohort_week
      FROM enriched
      WHERE first_week >= %s::date
        AND first_week <= %s::date
    ),
    cohort_returns AS (
      SELECT
        c.cohort_week,
        (e.week_start - c.cohort_week) AS weeks_later,
        COUNT(DISTINCT e.userid)::bigint AS buyers
      FROM cohort_base c
      INNER JOIN enriched e
        ON e.userid = c.userid
       AND e.week_start >= c.cohort_week
       AND e.week_start <= c.cohort_week + 8
      GROUP BY c.cohort_week, weeks_later
    ),
    cohort_sizes AS (
      SELECT cohort_week, COUNT(*)::bigint AS cohort_size
      FROM cohort_base
      GROUP BY cohort_week
    ),
    billing AS (
      SELECT
        source,
        COUNT(*)::bigint AS purchase_count,
        COUNT(DISTINCT userid)::bigint AS buyers,
        COALESCE(SUM(credits), 0)::bigint AS credits,
        COALESCE(SUM(revenue_inr), 0)::float8 AS revenue_inr
      FROM enriched
      GROUP BY source
    )
    SELECT json_build_object(
      'kpis', (SELECT row_to_json(k) FROM kpis k),
      'weekly_new_vs_repeat', COALESCE(
        (SELECT json_agg(row_to_json(w) ORDER BY w.week_start) FROM weekly_nr w),
        '[]'::json
      ),
      'weekly_by_channel', COALESCE(
        (
          SELECT json_agg(row_to_json(w) ORDER BY w.week_start, w.buyers DESC)
          FROM weekly_ch w
        ),
        '[]'::json
      ),
      'channel_leaderboard', COALESCE(
        (
          SELECT json_agg(row_to_json(l) ORDER BY l.revenue_inr DESC NULLS LAST, l.buyers DESC)
          FROM leaderboard l
        ),
        '[]'::json
      ),
      'cohorts', COALESCE(
        (
          SELECT json_agg(row_to_json(x) ORDER BY x.cohort_week)
          FROM (
            SELECT
              s.cohort_week,
              s.cohort_size,
              COALESCE(
                (
                  SELECT json_object_agg(r.weeks_later::text, r.buyers)
                  FROM cohort_returns r
                  WHERE r.cohort_week = s.cohort_week
                ),
                '{{}}'::json
              ) AS returns
            FROM cohort_sizes s
          ) x
        ),
        '[]'::json
      ),
      'by_billing', COALESCE(
        (
          SELECT json_agg(row_to_json(b) ORDER BY b.purchase_count DESC)
          FROM billing b
        ),
        '[]'::json
      )
    ) AS payload
    """

    query_params = (
        fd.isoformat(),
        td.isoformat(),
        fd.isoformat(),
        td.isoformat(),
        fd.isoformat(),
        td.isoformat(),
    )

    # Single pool checkout: catalog peek (cheap) + one analytics statement, then release.
    with get_conn() as conn:
        _note_helpful_indexes(conn)
        try:
            execute(conn, f"SET LOCAL statement_timeout = '{_STATEMENT_TIMEOUT_MS}'")
            execute(conn, "SET LOCAL idle_in_transaction_session_timeout = '20000'")
            # Read-only; keep work_mem modest so admin analytics cannot balloon RAM.
            execute(conn, "SET LOCAL work_mem = '32MB'")
            cur = execute(conn, sql, query_params)
            row = cur.fetchone()
            payload = _as_dict(row[0] if row else None)
        except Exception:
            logger.exception("buyer_analytics query failed from=%s to=%s group_by=%s", fd, td, gb)
            raise
        finally:
            # Always rollback so LOCAL settings / any open txn never leak into the pool.
            try:
                conn.rollback()
            except Exception:
                pass

    kpis = payload.get("kpis") or {}
    unique_buyers = int(kpis.get("unique_buyers") or 0)
    repeat_buyers = int(kpis.get("repeat_buyers") or 0)
    repeat_pct = round(100.0 * repeat_buyers / unique_buyers, 1) if unique_buyers else None

    cohorts_out: List[Dict[str, Any]] = []
    for c in payload.get("cohorts") or []:
        returns = c.get("returns") or {}
        if isinstance(returns, dict):
            returns_norm = {str(k): int(v or 0) for k, v in returns.items()}
        else:
            returns_norm = {}
        cohorts_out.append(
            {
                "cohort_week": str(c.get("cohort_week") or "")[:10],
                "cohort_size": int(c.get("cohort_size") or 0),
                "returns": returns_norm,
            }
        )

    weekly_nr = []
    for r in payload.get("weekly_new_vs_repeat") or []:
        weekly_nr.append(
            {
                "week_start": str(r.get("week_start") or "")[:10],
                "purchase_count": int(r.get("purchase_count") or 0),
                "buyers": int(r.get("buyers") or 0),
                "credits": int(r.get("credits") or 0),
                "revenue_inr": round(float(r.get("revenue_inr") or 0), 2),
                "new_buyers": int(r.get("new_buyers") or 0),
                "repeat_buyers": int(r.get("repeat_buyers") or 0),
            }
        )

    weekly_ch = []
    for r in payload.get("weekly_by_channel") or []:
        weekly_ch.append(
            {
                "week_start": str(r.get("week_start") or "")[:10],
                "channel": r.get("channel") or "(none)",
                "purchase_count": int(r.get("purchase_count") or 0),
                "buyers": int(r.get("buyers") or 0),
                "credits": int(r.get("credits") or 0),
                "revenue_inr": round(float(r.get("revenue_inr") or 0), 2),
                "new_buyers": int(r.get("new_buyers") or 0),
                "repeat_buyers": int(r.get("repeat_buyers") or 0),
            }
        )

    leaderboard = []
    for r in payload.get("channel_leaderboard") or []:
        median = r.get("median_days_install_to_first_buy")
        leaderboard.append(
            {
                "channel": r.get("channel") or "(none)",
                "purchase_count": int(r.get("purchase_count") or 0),
                "buyers": int(r.get("buyers") or 0),
                "credits": int(r.get("credits") or 0),
                "revenue_inr": round(float(r.get("revenue_inr") or 0), 2),
                "new_buyers_in_range": int(r.get("new_buyers_in_range") or 0),
                "repeat_purchase_users": int(r.get("repeat_purchase_users") or 0),
                "median_days_install_to_first_buy": float(median) if median is not None else None,
            }
        )

    billing = []
    for r in payload.get("by_billing") or []:
        billing.append(
            {
                "source": r.get("source"),
                "purchase_count": int(r.get("purchase_count") or 0),
                "buyers": int(r.get("buyers") or 0),
                "credits": int(r.get("credits") or 0),
                "revenue_inr": round(float(r.get("revenue_inr") or 0), 2),
            }
        )

    result = {
        "from_date": fd.isoformat(),
        "to_date": td.isoformat(),
        "timezone": _ADMIN_TZ,
        "group_by": gb,
        "attribution": "first_touch_install",
        "max_range_days": _MAX_RANGE_DAYS,
        "kpis": {
            "purchase_count": int(kpis.get("purchase_count") or 0),
            "unique_buyers": unique_buyers,
            "credits_purchased": int(kpis.get("credits_purchased") or 0),
            "estimated_revenue_inr": round(float(kpis.get("estimated_revenue_inr") or 0), 2),
            "new_buyers": int(kpis.get("new_buyers") or 0),
            "repeat_buyers": repeat_buyers,
            "repeat_buyer_pct": repeat_pct,
        },
        "weekly_new_vs_repeat": weekly_nr,
        "weekly_by_channel": weekly_ch,
        "channel_leaderboard": leaderboard,
        "cohorts": cohorts_out,
        "by_billing": billing,
        "query_ms": round((time.perf_counter() - started) * 1000, 1),
        "cached": False,
        "cache_ttl_sec": int(_CACHE_TTL_SEC),
    }
    _cache_set(cache_key, result)
    return result
