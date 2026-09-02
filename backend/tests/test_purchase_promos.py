from datetime import datetime, timezone, timedelta

from credits.purchase_promos import (
    calculate_purchase_promo_bonus,
    canonical_purchase_channel,
    channel_allows,
    normalize_channel,
    normalize_code,
    promo_is_live,
    serialize_promo,
    _as_utc,
)


def test_calculate_purchase_promo_bonus():
    assert calculate_purchase_promo_bonus(100, 20) == 20
    assert calculate_purchase_promo_bonus(50, 10) == 5
    assert calculate_purchase_promo_bonus(999, 10) == 99
    assert calculate_purchase_promo_bonus(0, 20) == 0
    assert calculate_purchase_promo_bonus(100, 0) == 0


def test_channel_allows():
    assert channel_allows("web", "web") is True
    assert channel_allows("web", "play") is False
    assert channel_allows("play", "play") is True
    assert channel_allows("play", "web") is False
    assert channel_allows("both", "web") is True
    assert channel_allows("both", "play") is True
    assert channel_allows("web", "pwa") is True
    assert channel_allows("web", "mobile_pwa") is True
    assert channel_allows("play", "pwa") is False
    assert normalize_channel("android") == "web"
    assert canonical_purchase_channel("pwa") == "web"
    assert canonical_purchase_channel("expo_web") == "web"
    assert canonical_purchase_channel("google_play") == "play"


def test_normalize_code():
    assert normalize_code("  diwali20 ") == "DIWALI20"


def test_promo_is_live_window_and_stop():
    now = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)
    live = {
        "is_active": True,
        "starts_at": now - timedelta(days=1),
        "ends_at": now + timedelta(days=1),
    }
    assert promo_is_live(live, now=now) is True

    stopped = dict(live, is_active=False)
    assert promo_is_live(stopped, now=now) is False

    future = dict(live, starts_at=now + timedelta(hours=1))
    assert promo_is_live(future, now=now) is False

    expired = dict(live, ends_at=now - timedelta(minutes=1))
    assert promo_is_live(expired, now=now) is False


def test_serialize_promo_iso_dates_and_date_only_eligibility_window():
    now = datetime.now(timezone.utc)
    row = {
        "id": 1,
        "name": "Diwali",
        "code": "DIWALI20",
        "percent": 20,
        "channels": "both",
        "starts_at": now - timedelta(hours=1),
        "ends_at": now + timedelta(days=7),
        "is_active": True,
        "user_created_after": datetime(2026, 9, 1),
        "max_uses": None,
        "max_uses_per_user": 1,
        "used_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    out = serialize_promo(row)
    assert "T" in out["starts_at"]
    assert out["user_created_after"].startswith("2026-09-01")
    assert out["live"] is True
    assert _as_utc("2026-09-01T00:00:00").date().isoformat() == "2026-09-01"
