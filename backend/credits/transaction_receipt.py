"""User-safe payment fields and feature links for a credit transaction.

Purchase metadata can contain tokens and raw gateway payloads. This module
returns only the amount the user paid, and GST when that amount is INR and
already includes tax. The rate matches Play external-transaction reporting.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

_SESSION_ID = re.compile(r"^[A-Za-z0-9_-]{8,80}$")
_PODCAST_MESSAGE_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
_BIRTH_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BIRTH_TIME = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")
_CHAT_SESSION_METADATA_FEATURES = frozenset({
    "instant_chat",
    "instant_chat_minutes",
    "speech_chat",
    "speech_chat_minutes",
})
_ANALYSIS_TYPES = frozenset({
    "career",
    "wealth",
    "health",
    "marriage",
    "education",
    "progeny",
})
_PROGENY_FOCUS = frozenset({"first_child", "next_child", "parenting"})


def gst_rate() -> float:
    raw = (os.environ.get("RAZORPAY_GST_RATE") or "0.18").strip()
    try:
        rate = float(raw)
    except ValueError:
        rate = 0.18
    if rate < 0 or rate >= 1:
        return 0.18
    return rate


def inclusive_tax_split(total: float, rate: float) -> tuple[float, float]:
    """Split a tax-inclusive total into pre-tax and tax, in currency units."""
    total_minor = int(round(float(total) * 100))
    if total_minor <= 0 or rate <= 0 or rate >= 1:
        return round(float(total), 2), 0.0
    pretax_minor = int(round(total_minor / (1.0 + rate)))
    tax_minor = total_minor - pretax_minor
    return pretax_minor / 100.0, tax_minor / 100.0


def _parse_meta(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def money_from_total(currency: Optional[str], total: Optional[float], *, amount_paid_label: Optional[str] = None) -> Optional[Dict[str, Any]]:
    code = (currency or "").strip().upper() or None
    if total is not None and total > 0 and code:
        paid = round(float(total), 2)
        money: Dict[str, Any] = {"currency": code, "amount_paid": paid}
        if code == "INR":
            rate = gst_rate()
            pretax, tax = inclusive_tax_split(paid, rate)
            if tax > 0:
                money["pretax_amount"] = pretax
                money["tax_amount"] = tax
                money["tax_rate"] = rate
                money["tax_included"] = True
        return money
    label = (amount_paid_label or "").strip()
    if label:
        return {"currency": code, "amount_paid_label": label}
    return None


def transaction_payment_view(
    source: Optional[str],
    metadata_raw: Any = None,
    amount_inr: Any = None,
) -> Dict[str, Any]:
    """Payment method, product id, and money. Never returns gateway secrets."""
    src = (source or "").strip()
    meta = _parse_meta(metadata_raw)
    payment_method = None
    if src in ("google_play", "google_play_refund"):
        payment_method = "google_play"
    elif src in ("razorpay", "razorpay_refund"):
        payment_method = "razorpay"

    currency = None
    total = None
    label = None
    if src == "razorpay":
        currency = str(meta.get("currency") or "INR").strip().upper() or "INR"
        paise = _as_int(meta.get("amount_paise"))
        if paise is not None and paise > 0:
            total = paise / 100.0
        if total is None:
            total = _as_float(amount_inr)
    elif src == "google_play":
        currency = str(meta.get("price_currency") or "").strip().upper() or None
        micros = _as_int(meta.get("price_amount_micros"))
        if micros is not None and micros > 0:
            total = micros / 1_000_000.0
            if not currency:
                currency = "INR" if _as_float(amount_inr) else None
        if total is None:
            inr = _as_float(amount_inr)
            if inr is not None and inr > 0:
                currency = currency or "INR"
                total = inr
        if total is not None and not currency:
            total = None
        label = str(meta.get("localized_price") or "").strip() or None
    elif src in ("razorpay_refund", "google_play_refund"):
        inr = _as_float(amount_inr)
        if inr is not None and inr > 0:
            currency = "INR"
            total = inr

    product_id = str(meta.get("product_id") or "").strip() or None
    return {
        "payment_method": payment_method,
        "product_id": product_id,
        "money": money_from_total(currency, total, amount_paid_label=label if total is None else None),
    }


def chat_usage_metadata(session_id: Any, message_id: Any = None) -> Optional[str]:
    """JSON metadata that points a credit spend at one chat session."""
    sid = str(session_id or "").strip()
    if not _SESSION_ID.match(sid):
        return None
    link: Dict[str, Any] = {"kind": "chat", "session_id": sid}
    try:
        if message_id is not None and str(message_id).strip() != "":
            link["message_id"] = int(message_id)
    except (TypeError, ValueError):
        pass
    return json.dumps({"feature_link": link})


def _coord(value: Any, low: float, high: float) -> Optional[float]:
    try:
        if value is None or str(value).strip() == "":
            return None
        number = round(float(value), 5)
    except (TypeError, ValueError):
        return None
    if number < low or number > high:
        return None
    return number


def _bounded_int(value: Any, low: int, high: int) -> Optional[int]:
    try:
        if value is None or str(value).strip() == "":
            return None
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number < low or number > high:
        return None
    return number


def event_timeline_usage_metadata(
    *,
    job_id: Any,
    year: Any,
    month: Any = None,
    birth_chart_id: Any = None,
) -> Optional[str]:
    """JSON metadata that points an event-timeline spend at one saved yearly or monthly report."""
    target_year = _bounded_int(year, 1900, 2200)
    if target_year is None:
        return None
    target_month = _bounded_int(month, 1, 12) if month is not None else None
    if month is not None and target_month is None:
        return None
    link: Dict[str, Any] = {
        "kind": "event_timeline",
        "scope": "monthly" if target_month is not None else "yearly",
        "year": target_year,
    }
    if target_month is not None:
        link["month"] = target_month
    job = str(job_id or "").strip()
    if _SESSION_ID.match(job):
        link["job_id"] = job
    chart_id = _bounded_int(birth_chart_id, 1, 2_000_000_000)
    if chart_id is not None:
        link["birth_chart_id"] = chart_id
    return json.dumps({"feature_link": link})


def analysis_usage_metadata(
    *,
    analysis: Any,
    birth_chart_id: Any,
    analysis_focus: Any = None,
    children_count: Any = None,
) -> Optional[str]:
    """JSON metadata that points an analysis-hub spend at one saved chart report."""
    slug = str(analysis or "").strip()
    chart_id = _bounded_int(birth_chart_id, 1, 2_000_000_000)
    if slug not in _ANALYSIS_TYPES or chart_id is None:
        return None
    link: Dict[str, Any] = {
        "kind": "analysis",
        "analysis": slug,
        "birth_chart_id": chart_id,
    }
    if slug == "progeny":
        focus = str(analysis_focus or "first_child").strip()
        if focus not in _PROGENY_FOCUS:
            focus = "first_child"
        count = _bounded_int(0 if children_count is None else children_count, 0, 20)
        link["analysis_focus"] = focus
        link["children_count"] = 0 if count is None else count
    return json.dumps({"feature_link": link})


def podcast_usage_metadata(
    *,
    message_id: Any,
    lang: Any,
    session_id: Any = None,
    birth_chart_id: Any = None,
) -> Optional[str]:
    """JSON metadata that points a podcast spend at one saved episode."""
    mid = str(message_id or "").strip()
    if not _PODCAST_MESSAGE_ID.match(mid):
        return None
    cache_lang = "hi" if str(lang or "").lower().startswith("hi") else "en"
    link: Dict[str, Any] = {"kind": "podcast", "message_id": mid, "lang": cache_lang}
    sid = str(session_id or "").strip()
    if _SESSION_ID.match(sid):
        link["session_id"] = sid
    chart_id = _bounded_int(birth_chart_id, 1, 2_000_000_000)
    if chart_id is not None:
        link["birth_chart_id"] = chart_id
    return json.dumps({"feature_link": link})


def speech_session_link(session_id: Any) -> Optional[Dict[str, Any]]:
    """Chat session that a Talk to Tara minute charge should reopen."""
    sid = str(session_id or "").strip()
    if not _SESSION_ID.match(sid):
        return None
    return {"kind": "speech", "session_id": sid}


def prashna_usage_metadata(reading_id: Any) -> Optional[str]:
    """JSON metadata that points a Prashna spend at one saved casting."""
    reading = _bounded_int(reading_id, 1, 2_000_000_000)
    if reading is None:
        return None
    return json.dumps({"feature_link": {"kind": "prashna", "reading_id": reading}})


def karma_usage_metadata(birth_chart_id: Any) -> Optional[str]:
    """JSON metadata that points a Karma spend at one chart's saved study."""
    chart_id = _bounded_int(birth_chart_id, 1, 2_000_000_000)
    if chart_id is None:
        return None
    return json.dumps({"feature_link": {"kind": "karma", "birth_chart_id": chart_id}})


def ashtakavarga_oracle_usage_metadata(analysis_id: Any) -> Optional[str]:
    """JSON metadata that points an Ashtakavarga insight at one history row."""
    analysis = _bounded_int(analysis_id, 1, 2_000_000_000)
    if analysis is None:
        return None
    return json.dumps({
        "feature_link": {"kind": "ashtakavarga", "scope": "oracle", "analysis_id": analysis},
    })


def ashtakavarga_life_usage_metadata(
    *,
    date: Any,
    time: Any,
    latitude: Any,
    longitude: Any,
) -> Optional[str]:
    """JSON metadata that points a life study at the birth fingerprint that was charged."""
    day = str(date or "").strip()
    clock = str(time or "").strip()
    lat = _coord(latitude, -90, 90)
    lon = _coord(longitude, -180, 180)
    if not _BIRTH_DATE.match(day) or not _BIRTH_TIME.match(clock) or lat is None or lon is None:
        return None
    return json.dumps({
        "feature_link": {
            "kind": "ashtakavarga",
            "scope": "life",
            "date": day,
            "time": clock,
            "latitude": lat,
            "longitude": lon,
        },
    })


def _chat_feature_link(explicit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    session_id = str(explicit.get("session_id") or "").strip()
    if not _SESSION_ID.match(session_id):
        return None
    link: Dict[str, Any] = {"kind": "chat", "session_id": session_id}
    message_id = _bounded_int(explicit.get("message_id"), 1, 2_000_000_000)
    if message_id is not None:
        link["message_id"] = message_id
    return link


def _event_timeline_feature_link(explicit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    scope = str(explicit.get("scope") or "").strip()
    year = _bounded_int(explicit.get("year"), 1900, 2200)
    if scope not in ("yearly", "monthly") or year is None:
        return None
    link: Dict[str, Any] = {"kind": "event_timeline", "scope": scope, "year": year}
    if scope == "monthly":
        month = _bounded_int(explicit.get("month"), 1, 12)
        if month is None:
            return None
        link["month"] = month
    job_id = str(explicit.get("job_id") or "").strip()
    if _SESSION_ID.match(job_id):
        link["job_id"] = job_id
    chart_id = _bounded_int(explicit.get("birth_chart_id"), 1, 2_000_000_000)
    if chart_id is not None:
        link["birth_chart_id"] = chart_id
    return link


def _analysis_feature_link(explicit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    slug = str(explicit.get("analysis") or "").strip()
    chart_id = _bounded_int(explicit.get("birth_chart_id"), 1, 2_000_000_000)
    if slug not in _ANALYSIS_TYPES or chart_id is None:
        return None
    link: Dict[str, Any] = {
        "kind": "analysis",
        "analysis": slug,
        "birth_chart_id": chart_id,
    }
    if slug == "progeny":
        focus = str(explicit.get("analysis_focus") or "first_child").strip()
        if focus not in _PROGENY_FOCUS:
            focus = "first_child"
        count = _bounded_int(0 if explicit.get("children_count") is None else explicit.get("children_count"), 0, 20)
        link["analysis_focus"] = focus
        link["children_count"] = 0 if count is None else count
    return link


def _podcast_feature_link(explicit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    mid = str(explicit.get("message_id") or "").strip()
    lang = str(explicit.get("lang") or "").strip().lower()
    if not _PODCAST_MESSAGE_ID.match(mid) or lang not in ("en", "hi"):
        return None
    link: Dict[str, Any] = {"kind": "podcast", "message_id": mid, "lang": lang}
    sid = str(explicit.get("session_id") or "").strip()
    if _SESSION_ID.match(sid):
        link["session_id"] = sid
    chart_id = _bounded_int(explicit.get("birth_chart_id"), 1, 2_000_000_000)
    if chart_id is not None:
        link["birth_chart_id"] = chart_id
    return link


def _speech_feature_link(explicit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return speech_session_link(explicit.get("session_id"))


def _prashna_feature_link(explicit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    reading_id = _bounded_int(explicit.get("reading_id"), 1, 2_000_000_000)
    if reading_id is None:
        return None
    return {"kind": "prashna", "reading_id": reading_id}


def _karma_feature_link(explicit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    chart_id = _bounded_int(explicit.get("birth_chart_id"), 1, 2_000_000_000)
    if chart_id is None:
        return None
    return {"kind": "karma", "birth_chart_id": chart_id}


def _ashtakavarga_feature_link(explicit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    scope = str(explicit.get("scope") or "").strip()
    if scope == "oracle":
        analysis_id = _bounded_int(explicit.get("analysis_id"), 1, 2_000_000_000)
        if analysis_id is None:
            return None
        return {"kind": "ashtakavarga", "scope": "oracle", "analysis_id": analysis_id}
    if scope != "life":
        return None
    day = str(explicit.get("date") or "").strip()
    clock = str(explicit.get("time") or "").strip()
    lat = _coord(explicit.get("latitude"), -90, 90)
    lon = _coord(explicit.get("longitude"), -180, 180)
    if not _BIRTH_DATE.match(day) or not _BIRTH_TIME.match(clock) or lat is None or lon is None:
        return None
    return {
        "kind": "ashtakavarga",
        "scope": "life",
        "date": day,
        "time": clock,
        "latitude": lat,
        "longitude": lon,
    }


def feature_link_from_usage(reference_id: Optional[str], metadata_raw: Any) -> Optional[Dict[str, Any]]:
    """Return a client-safe link for a saved chat, report, podcast, call, or reading."""
    meta = _parse_meta(metadata_raw)
    explicit = meta.get("feature_link")
    if isinstance(explicit, dict):
        kind = str(explicit.get("kind") or "")
        if kind == "chat":
            return _chat_feature_link(explicit)
        if kind == "event_timeline":
            return _event_timeline_feature_link(explicit)
        if kind == "analysis":
            return _analysis_feature_link(explicit)
        if kind == "podcast":
            return _podcast_feature_link(explicit)
        if kind == "speech":
            return _speech_feature_link(explicit)
        if kind == "prashna":
            return _prashna_feature_link(explicit)
        if kind == "karma":
            return _karma_feature_link(explicit)
        if kind == "ashtakavarga":
            return _ashtakavarga_feature_link(explicit)
        return None
    if (reference_id or "") in _CHAT_SESSION_METADATA_FEATURES:
        session_id = str(meta.get("chat_session_id") or "").strip()
        if _SESSION_ID.match(session_id):
            return {"kind": "chat", "session_id": session_id}
    return None


def refund_money_from_original(
    refund_credit_amount: Any,
    original_credit_amount: Any,
    original_source: str,
    original_metadata: Any,
) -> Dict[str, Any]:
    """Scale the original charge to the credits actually reversed."""
    original = transaction_payment_view(original_source, original_metadata, None)
    money = original.get("money") or {}
    total = _as_float(money.get("amount_paid"))
    original_credits = abs(_as_float(original_credit_amount) or 0)
    refund_credits = abs(_as_float(refund_credit_amount) or 0)
    if not total or original_credits <= 0 or refund_credits <= 0:
        return original
    scaled = total * (refund_credits / original_credits)
    return {
        "payment_method": original.get("payment_method"),
        "product_id": original.get("product_id"),
        "money": money_from_total(money.get("currency"), scaled),
    }
