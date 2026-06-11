"""
Per-user dynamic parameters for campaign message framing.

Resolves three groups of placeholders in batch (no N+1 queries):
- profile:  {name} {sun_sign} {moon_sign} {current_dasha}
- behavior: {last_question_topic} {days_since_last_chat} {questions_asked}
- wallet:   {credits_balance} {free_question_available}

Astrology values are only computed when the campaign templates actually use them
(swisseph + DashaCalculator per user is the expensive part).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Set

from db import execute

logger = logging.getLogger(__name__)

PROFILE_PLACEHOLDERS: FrozenSet[str] = frozenset({"name", "sun_sign", "moon_sign", "current_dasha"})
BEHAVIOR_PLACEHOLDERS: FrozenSet[str] = frozenset(
    {"last_question_topic", "days_since_last_chat", "questions_asked"}
)
WALLET_PLACEHOLDERS: FrozenSet[str] = frozenset({"credits_balance", "free_question_available"})

CAMPAIGN_PLACEHOLDERS: FrozenSet[str] = PROFILE_PLACEHOLDERS | BEHAVIOR_PLACEHOLDERS | WALLET_PLACEHOLDERS

_ASTRO_PLACEHOLDERS: FrozenSet[str] = frozenset({"sun_sign", "moon_sign", "current_dasha"})

_SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

_DEFAULTS: Dict[str, str] = {
    "name": "there",
    "sun_sign": "",
    "moon_sign": "",
    "current_dasha": "",
    "last_question_topic": "your life path",
    "days_since_last_chat": "a few",
    "questions_asked": "0",
    "credits_balance": "0",
    "free_question_available": "no",
}


def default_params() -> Dict[str, str]:
    return dict(_DEFAULTS)


def _clean_ids(user_ids: Iterable[Any]) -> List[int]:
    out: List[int] = []
    seen: Set[int] = set()
    for uid in user_ids or []:
        try:
            v = int(uid)
        except (TypeError, ValueError):
            continue
        if v > 0 and v not in seen:
            out.append(v)
            seen.add(v)
    return out


def _resolve_names(conn, ids: List[int], params: Dict[int, Dict[str, str]]) -> None:
    cur = execute(
        conn,
        "SELECT userid, COALESCE(NULLIF(TRIM(name), ''), '') FROM users WHERE userid = ANY(%s)",
        (ids,),
    )
    for uid, name in cur.fetchall() or []:
        if name:
            params[int(uid)]["name"] = str(name)[:80]


def _resolve_behavior(conn, ids: List[int], params: Dict[int, Dict[str, str]]) -> None:
    cur = execute(
        conn,
        """
        SELECT cs.user_id,
               COUNT(*) FILTER (WHERE cm.sender = 'user') AS questions_asked,
               MAX(cm.timestamp) FILTER (WHERE cm.sender = 'user') AS last_user_msg_at
        FROM chat_sessions cs
        JOIN chat_messages cm ON cm.session_id = cs.session_id
        WHERE cs.user_id = ANY(%s)
        GROUP BY cs.user_id
        """,
        (ids,),
    )
    now = datetime.utcnow()
    for uid, n_questions, last_at in cur.fetchall() or []:
        p = params[int(uid)]
        p["questions_asked"] = str(int(n_questions or 0))
        if last_at is not None:
            try:
                days = max(0, int((now - last_at.replace(tzinfo=None)).days))
                p["days_since_last_chat"] = str(days)
            except Exception:
                pass

    # Latest question topic (canonical_question/category, content excerpt as fallback).
    topic_sql = """
        SELECT DISTINCT ON (cs.user_id)
               cs.user_id,
               COALESCE(NULLIF(TRIM(cm.canonical_question), ''),
                        NULLIF(TRIM(cm.category), ''),
                        LEFT(TRIM(cm.content), 90))
        FROM chat_messages cm
        JOIN chat_sessions cs ON cs.session_id = cm.session_id
        WHERE cm.sender = 'user' AND cs.user_id = ANY(%s)
        ORDER BY cs.user_id, cm.timestamp DESC, cm.message_id DESC
    """
    try:
        cur = execute(conn, topic_sql, (ids,))
        rows = cur.fetchall() or []
    except Exception:
        # Older schemas may not have canonical_question / category columns.
        try:
            conn.rollback()
        except Exception:
            pass
        cur = execute(
            conn,
            """
            SELECT DISTINCT ON (cs.user_id) cs.user_id, LEFT(TRIM(cm.content), 90)
            FROM chat_messages cm
            JOIN chat_sessions cs ON cs.session_id = cm.session_id
            WHERE cm.sender = 'user' AND cs.user_id = ANY(%s)
            ORDER BY cs.user_id, cm.timestamp DESC, cm.message_id DESC
            """,
            (ids,),
        )
        rows = cur.fetchall() or []
    for uid, topic in rows:
        if topic:
            params[int(uid)]["last_question_topic"] = str(topic)[:120]


def _resolve_wallet(conn, ids: List[int], params: Dict[int, Dict[str, str]]) -> None:
    cur = execute(
        conn,
        """
        SELECT userid, COALESCE(credits, 0), COALESCE(free_chat_question_used, 0)
        FROM user_credits
        WHERE userid = ANY(%s)
        """,
        (ids,),
    )
    for uid, credits, free_used in cur.fetchall() or []:
        p = params[int(uid)]
        p["credits_balance"] = str(int(credits or 0))
        p["free_question_available"] = "no" if int(free_used or 0) else "yes"


def _self_charts_for_users(conn, ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Decrypted self birth charts for the given users (first self chart per user)."""
    from . import db as nudge_db

    cur = execute(
        conn,
        """
        SELECT id, userid, date, time, latitude, longitude, timezone
        FROM birth_charts
        WHERE LOWER(COALESCE(relation, '')) = 'self' AND userid = ANY(%s)
        ORDER BY userid ASC, id ASC
        """,
        (ids,),
    )
    rows = cur.fetchall() or []
    enc = nudge_db._nudge_encryptor
    out: Dict[int, Dict[str, Any]] = {}
    for cid, uid, d, t, lat, lon, tz in rows:
        uid = int(uid)
        if uid in out:
            continue
        try:
            if enc:
                d = enc.decrypt(d) if d else ""
                t = enc.decrypt(t) if t else ""
                lat_s = enc.decrypt(str(lat)) if lat is not None else "0"
                lon_s = enc.decrypt(str(lon)) if lon is not None else "0"
                lat_f = float(lat_s) if lat_s else 0.0
                lon_f = float(lon_s) if lon_s else 0.0
            else:
                lat_f = float(lat) if lat is not None else 0.0
                lon_f = float(lon) if lon is not None else 0.0
            out[uid] = {
                "birth_chart_id": int(cid),
                "date": (d or "").strip(),
                "time": (t or "").strip(),
                "latitude": lat_f,
                "longitude": lon_f,
                "timezone": (tz or "").strip() or "UTC+0",
            }
        except (TypeError, ValueError) as e:
            logger.debug("Skip birth chart %s for params: %s", cid, e)
    return out


def _birth_jd(date_str: str, time_str: str, lat: float, lon: float, tz: str) -> float:
    import swisseph as swe
    from utils.timezone_service import parse_timezone_offset

    time_parts = (time_str or "00:00").split(":")
    h = int(time_parts[0])
    mi = int(time_parts[1]) if len(time_parts) > 1 else 0
    hour = float(h) + float(mi) / 60.0
    tz_offset = parse_timezone_offset(tz, lat, lon)
    utc_hour = float(hour) - float(tz_offset)
    y, m, d = (int(x) for x in date_str.split("-"))
    return swe.julday(y, m, d, utc_hour)


def _natal_sign(planet_id: int, birth_jd: float) -> str:
    import swisseph as swe

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    pos = swe.calc_ut(birth_jd, planet_id, swe.FLG_SIDEREAL)
    if not pos:
        return ""
    lon = pos[0][0] % 360.0
    return _SIGN_NAMES[int(lon // 30.0) % 12]


def _current_dasha_label(chart: Dict[str, Any]) -> str:
    from shared.dasha_calculator import DashaCalculator

    birth_data = {
        "date": chart["date"],
        "time": chart["time"],
        "timezone": chart["timezone"],
        "latitude": chart["latitude"],
        "longitude": chart["longitude"],
        "name": "Self",
    }
    d = DashaCalculator().calculate_current_dashas(birth_data, datetime.now())
    md = (d.get("mahadasha") or {}).get("planet") or ""
    ad = (d.get("antardasha") or {}).get("planet") or ""
    if md and ad:
        return f"{md}-{ad}"
    return md or ""


def _resolve_astro(conn, ids: List[int], params: Dict[int, Dict[str, str]], needed: Set[str]) -> None:
    import swisseph as swe

    charts = _self_charts_for_users(conn, ids)
    for uid, chart in charts.items():
        p = params[uid]
        try:
            if not chart.get("date"):
                continue
            jd = _birth_jd(
                chart["date"], chart["time"], chart["latitude"],
                chart["longitude"], chart["timezone"],
            )
            if "sun_sign" in needed:
                p["sun_sign"] = _natal_sign(swe.SUN, jd)
            if "moon_sign" in needed:
                p["moon_sign"] = _natal_sign(swe.MOON, jd)
        except Exception as e:
            logger.debug("Sign computation failed for user %s: %s", uid, e)
        if "current_dasha" in needed:
            try:
                p["current_dasha"] = _current_dasha_label(chart)
            except Exception as e:
                logger.debug("Dasha computation failed for user %s: %s", uid, e)


def resolve_params_for_users(
    conn,
    user_ids: Iterable[Any],
    needed: Optional[Set[str]] = None,
) -> Dict[int, Dict[str, str]]:
    """
    Return {userid: {placeholder: value}} with ALL campaign placeholders present
    (defaults fill any missing value, so template rendering never fails).
    `needed` limits expensive astro computation to placeholders actually used.
    """
    ids = _clean_ids(user_ids)
    params: Dict[int, Dict[str, str]] = {uid: default_params() for uid in ids}
    if not ids:
        return params
    need = set(needed) if needed is not None else set(CAMPAIGN_PLACEHOLDERS)

    steps = (
        ("names", lambda: _resolve_names(conn, ids, params), bool(need & {"name"})),
        ("behavior", lambda: _resolve_behavior(conn, ids, params), bool(need & BEHAVIOR_PLACEHOLDERS)),
        ("wallet", lambda: _resolve_wallet(conn, ids, params), bool(need & WALLET_PLACEHOLDERS)),
        ("astro", lambda: _resolve_astro(conn, ids, params, need & _ASTRO_PLACEHOLDERS), bool(need & _ASTRO_PLACEHOLDERS)),
    )
    for label, fn, wanted in steps:
        if not wanted:
            continue
        try:
            fn()
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.warning("param resolution step %s failed: %s", label, e)
    return params
