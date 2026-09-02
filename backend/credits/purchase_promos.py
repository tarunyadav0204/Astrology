"""Purchase promo codes: percent extra credits on a paid pack, not stacked with other extras."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import User, get_current_user
from db import execute, get_conn

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_CHANNELS = frozenset({"web", "play", "both"})
PURCHASE_PROMO_SOURCE = "purchase_promo"
PWA_PURCHASE_CHANNEL_ALIASES = frozenset({"pwa", "expo_web", "mobile_pwa", "web_pwa"})


def ensure_purchase_promo_tables(conn) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS purchase_promo_codes (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            percent INTEGER NOT NULL,
            channels TEXT NOT NULL DEFAULT 'web',
            starts_at TIMESTAMP,
            ends_at TIMESTAMP,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            user_created_after TIMESTAMP,
            max_uses INTEGER,
            max_uses_per_user INTEGER NOT NULL DEFAULT 1,
            used_count INTEGER NOT NULL DEFAULT 0,
            created_by INTEGER,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS purchase_promo_usage (
            id SERIAL PRIMARY KEY,
            promo_id INTEGER NOT NULL REFERENCES purchase_promo_codes(id),
            userid INTEGER NOT NULL,
            purchase_source TEXT NOT NULL,
            purchase_reference_id TEXT NOT NULL,
            product_id TEXT,
            purchased_credits INTEGER NOT NULL,
            bonus_credits INTEGER NOT NULL,
            used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (purchase_source, purchase_reference_id)
        )
        """,
    )
    execute(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_purchase_promo_usage_user ON purchase_promo_usage (userid, promo_id)",
    )


def calculate_purchase_promo_bonus(purchased_credits: int, percent: int) -> int:
    try:
        base = max(0, int(purchased_credits))
        pct = max(0, int(percent))
    except (TypeError, ValueError):
        return 0
    if base <= 0 or pct <= 0:
        return 0
    return (base * pct) // 100


def normalize_channel(value: object) -> str:
    raw = str(value or "web").strip().lower()
    return raw if raw in ALLOWED_CHANNELS else "web"


def canonical_purchase_channel(value: object) -> str:
    """Map a checkout surface to web or play. PWA uses the same Razorpay path as the website."""
    raw = str(value or "web").strip().lower()
    if raw in PWA_PURCHASE_CHANNEL_ALIASES:
        return "web"
    if raw in {"android", "google_play", "iap", "play"}:
        return "play"
    return "web"


def normalize_code(value: object) -> str:
    return str(value or "").strip().upper()


def _as_utc(value: Any) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    raw = str(value).strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_truthy_active(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "t", "true", "yes"}


def promo_is_live(row: Dict[str, Any], now: Optional[datetime] = None) -> bool:
    if not _is_truthy_active(row.get("is_active")):
        return False
    current = now or datetime.now(timezone.utc)
    starts = _as_utc(row.get("starts_at"))
    ends = _as_utc(row.get("ends_at"))
    if starts and current < starts:
        return False
    if ends and current > ends:
        return False
    return True


def channel_allows(promo_channels: str, purchase_channel: str) -> bool:
    allowed = normalize_channel(promo_channels)
    want = canonical_purchase_channel(purchase_channel)
    return allowed == "both" or allowed == want


def _row_dict(row: Any) -> Dict[str, Any]:
    if row is None:
        return {}
    if hasattr(row, "keys"):
        return {k: row[k] for k in row.keys()}
    keys = (
        "id",
        "name",
        "code",
        "percent",
        "channels",
        "starts_at",
        "ends_at",
        "is_active",
        "user_created_after",
        "max_uses",
        "max_uses_per_user",
        "used_count",
        "created_by",
        "created_at",
        "updated_at",
    )
    return {keys[i]: row[i] for i in range(min(len(keys), len(row)))}


def _json_dt(value: Any) -> Optional[str]:
    dt = _as_utc(value)
    return dt.isoformat() if dt else None


def serialize_promo(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "code": row.get("code"),
        "percent": int(row.get("percent") or 0),
        "channels": normalize_channel(row.get("channels")),
        "starts_at": _json_dt(row.get("starts_at")),
        "ends_at": _json_dt(row.get("ends_at")),
        "is_active": _is_truthy_active(row.get("is_active")),
        "user_created_after": _json_dt(row.get("user_created_after")),
        "max_uses": row.get("max_uses"),
        "max_uses_per_user": int(row.get("max_uses_per_user") or 1),
        "used_count": int(row.get("used_count") or 0),
        "created_at": _json_dt(row.get("created_at")),
        "updated_at": _json_dt(row.get("updated_at")),
        "live": promo_is_live(row),
    }


def _user_created_at(conn, userid: int) -> Optional[datetime]:
    cur = execute(conn, "SELECT created_at FROM users WHERE userid = ?", (userid,))
    row = cur.fetchone()
    if not row:
        return None
    return _as_utc(row[0] if not hasattr(row, "keys") else row["created_at"])


def _fetch_promo_by_code(conn, code: str) -> Optional[Dict[str, Any]]:
    cur = execute(
        conn,
        """
        SELECT id, name, code, percent, channels, starts_at, ends_at, is_active,
               user_created_after, max_uses, max_uses_per_user, used_count,
               created_by, created_at, updated_at
        FROM purchase_promo_codes
        WHERE code = ?
        """,
        (code,),
    )
    row = cur.fetchone()
    return _row_dict(row) if row else None


def validate_purchase_promo(
    userid: int,
    code: str,
    purchase_channel: str,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Return {ok, message, promo} without consuming a use."""
    normalized = normalize_code(code)
    if not normalized:
        return {"ok": False, "message": "Enter a promo code", "promo": None}
    channel = canonical_purchase_channel(purchase_channel)
    if channel not in {"web", "play"}:
        return {"ok": False, "message": "This promo cannot be used here", "promo": None}

    with get_conn() as conn:
        ensure_purchase_promo_tables(conn)
        promo = _fetch_promo_by_code(conn, normalized)
        if not promo:
            return {"ok": False, "message": "Invalid promo code", "promo": None}
        if not promo_is_live(promo, now=now):
            return {"ok": False, "message": "This promo is not active", "promo": None}
        if not channel_allows(promo.get("channels") or "web", channel):
            if normalize_channel(promo.get("channels")) == "play":
                return {"ok": False, "message": "This code is for the Android app", "promo": None}
            if normalize_channel(promo.get("channels")) == "web":
                return {"ok": False, "message": "This code is for website and PWA checkout", "promo": None}
            return {"ok": False, "message": "This promo cannot be used here", "promo": None}

        created_after = _as_utc(promo.get("user_created_after"))
        if created_after:
            user_created = _user_created_at(conn, userid)
            if user_created is None or user_created.date() < created_after.date():
                return {
                    "ok": False,
                    "message": "This promo is only for accounts created on or after the offer date",
                    "promo": None,
                }

        max_uses = promo.get("max_uses")
        try:
            max_uses_n = int(max_uses) if max_uses is not None else 0
        except (TypeError, ValueError):
            max_uses_n = 0
        used_count = int(promo.get("used_count") or 0)
        if max_uses_n > 0 and used_count >= max_uses_n:
            return {"ok": False, "message": "This promo has reached its use limit", "promo": None}

        max_per_user = max(1, int(promo.get("max_uses_per_user") or 1))
        cur = execute(
            conn,
            "SELECT COUNT(*) FROM purchase_promo_usage WHERE promo_id = ? AND userid = ?",
            (promo["id"], userid),
        )
        user_uses = int((cur.fetchone() or [0])[0] or 0)
        if user_uses >= max_per_user:
            return {"ok": False, "message": "You have already used this promo", "promo": None}

    return {"ok": True, "message": "ok", "promo": serialize_promo(promo)}


def require_checkout_promo_code(
    userid: int,
    raw_code: object,
    purchase_channel: str,
    credits: int,
    starter_credits: Optional[int] = None,
) -> Optional[str]:
    """Validate a checkout code or raise. Empty code returns None."""
    code = normalize_code(raw_code)
    if not code:
        return None
    if starter_credits is not None and int(credits) == int(starter_credits):
        raise HTTPException(status_code=400, detail="Promo codes cannot be used with the starter pack")
    result = validate_purchase_promo(userid, code, purchase_channel)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("message") or "Invalid promo code")
    return code


def maybe_apply_purchase_promo(
    credit_service,
    *,
    userid: int,
    purchased_credits: int,
    purchase_source: str,
    purchase_reference_id: str,
    product_id: Optional[str],
    purchase_promo_code: Optional[str],
    purchase_channel: str,
) -> Dict[str, Any]:
    code = normalize_code(purchase_promo_code)
    empty = {
        "applied": False,
        "eligible": False,
        "bonus_credits": 0,
        "reason": "no_code",
    }
    if not code:
        return empty

    checked = validate_purchase_promo(userid, code, purchase_channel)
    promo = checked.get("promo") or {}
    if not checked.get("ok") or not promo:
        return {
            "applied": False,
            "eligible": False,
            "bonus_credits": 0,
            "reason": "invalid_or_expired",
            "message": checked.get("message"),
        }

    percent = int(promo.get("percent") or 0)
    bonus = calculate_purchase_promo_bonus(purchased_credits, percent)
    if bonus <= 0:
        return {
            "applied": False,
            "eligible": True,
            "bonus_credits": 0,
            "percent": percent,
            "reason": "zero_bonus",
            "promo": promo,
        }

    reference_id = f"{purchase_source}:{purchase_reference_id}:purchase_promo"
    if credit_service.has_transaction_with_reference(userid, PURCHASE_PROMO_SOURCE, reference_id):
        return {
            "applied": False,
            "eligible": True,
            "bonus_credits": bonus,
            "percent": percent,
            "reason": "already_applied",
            "promo": promo,
        }

    metadata = json.dumps(
        {
            "purchase_source": purchase_source,
            "purchase_reference_id": purchase_reference_id,
            "product_id": product_id,
            "purchased_credits": int(purchased_credits),
            "percent": percent,
            "code": code,
            "promo_id": promo.get("id"),
            "name": promo.get("name"),
        }
    )
    ok = credit_service.add_credits(
        userid,
        bonus,
        PURCHASE_PROMO_SOURCE,
        reference_id=reference_id,
        description=f"Purchase promo {code}: +{bonus} credits ({percent}%)",
        metadata=metadata,
    )
    if not ok:
        return {
            "applied": False,
            "eligible": True,
            "bonus_credits": bonus,
            "percent": percent,
            "reason": "bonus_write_failed",
            "promo": promo,
        }

    try:
        with get_conn() as conn:
            ensure_purchase_promo_tables(conn)
            cur = execute(
                conn,
                """
                INSERT INTO purchase_promo_usage (
                    promo_id, userid, purchase_source, purchase_reference_id,
                    product_id, purchased_credits, bonus_credits
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (purchase_source, purchase_reference_id) DO NOTHING
                """,
                (
                    promo.get("id"),
                    userid,
                    purchase_source,
                    purchase_reference_id,
                    product_id,
                    int(purchased_credits),
                    bonus,
                ),
            )
            if (cur.rowcount or 0) > 0:
                execute(
                    conn,
                    "UPDATE purchase_promo_codes SET used_count = used_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (promo.get("id"),),
                )
            conn.commit()
    except Exception:
        logger.exception("purchase promo usage record failed code=%s payment=%s", code, purchase_reference_id)

    return {
        "applied": True,
        "eligible": True,
        "bonus_credits": bonus,
        "percent": percent,
        "reason": "applied",
        "promo": promo,
        "code": code,
        "name": promo.get("name"),
    }


class PurchasePromoPreviewRequest(BaseModel):
    code: str
    channel: str = "web"
    credits: Optional[int] = None


class AdminPurchasePromoBody(BaseModel):
    name: str
    code: str
    percent: int = Field(..., ge=1, le=500)
    channels: str = "web"
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    user_created_after: Optional[str] = None
    max_uses: Optional[int] = None
    max_uses_per_user: int = Field(default=1, ge=1, le=100)
    is_active: bool = True


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _payload_from_body(body: AdminPurchasePromoBody) -> Dict[str, Any]:
    channels = normalize_channel(body.channels)
    code = normalize_code(body.code)
    name = str(body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if not code:
        raise HTTPException(status_code=400, detail="Code is required")
    starts = _as_utc(body.starts_at)
    ends = _as_utc(body.ends_at)
    if starts and ends and ends <= starts:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    created_after = _as_utc(body.user_created_after)
    max_uses = body.max_uses
    if max_uses is not None:
        max_uses = int(max_uses)
        if max_uses < 0:
            raise HTTPException(status_code=400, detail="Max uses cannot be negative")
        if max_uses == 0:
            max_uses = None
    return {
        "name": name,
        "code": code,
        "percent": int(body.percent),
        "channels": channels,
        "starts_at": starts,
        "ends_at": ends,
        "user_created_after": created_after,
        "max_uses": max_uses,
        "max_uses_per_user": int(body.max_uses_per_user),
        "is_active": bool(body.is_active),
    }


@router.post("/purchase-promo/preview")
async def preview_purchase_promo(
    body: PurchasePromoPreviewRequest,
    current_user: User = Depends(get_current_user),
):
    channel = canonical_purchase_channel(body.channel)
    result = validate_purchase_promo(current_user.userid, body.code, channel)
    promo = result.get("promo")
    bonus = 0
    if result.get("ok") and promo and body.credits:
        bonus = calculate_purchase_promo_bonus(body.credits, promo.get("percent") or 0)
    return {
        "ok": bool(result.get("ok")),
        "message": result.get("message"),
        "promo": promo,
        "bonus_credits": bonus,
        "replaces_other_bonuses": True,
    }


@router.get("/admin/purchase-promos")
async def list_purchase_promos(current_user: User = Depends(_require_admin)):
    with get_conn() as conn:
        ensure_purchase_promo_tables(conn)
        cur = execute(
            conn,
            """
            SELECT id, name, code, percent, channels, starts_at, ends_at, is_active,
                   user_created_after, max_uses, max_uses_per_user, used_count,
                   created_by, created_at, updated_at
            FROM purchase_promo_codes
            ORDER BY created_at DESC
            """,
        )
        rows = cur.fetchall() or []
    return {"promos": [serialize_promo(_row_dict(row)) for row in rows]}


@router.post("/admin/purchase-promos")
async def create_purchase_promo(
    body: AdminPurchasePromoBody,
    current_user: User = Depends(_require_admin),
):
    payload = _payload_from_body(body)
    try:
        with get_conn() as conn:
            ensure_purchase_promo_tables(conn)
            execute(
                conn,
                """
                INSERT INTO purchase_promo_codes (
                    name, code, percent, channels, starts_at, ends_at, is_active,
                    user_created_after, max_uses, max_uses_per_user, created_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["name"],
                    payload["code"],
                    payload["percent"],
                    payload["channels"],
                    payload["starts_at"],
                    payload["ends_at"],
                    payload["is_active"],
                    payload["user_created_after"],
                    payload["max_uses"],
                    payload["max_uses_per_user"],
                    current_user.userid,
                ),
            )
            conn.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="Promo code already exists")
    return {"message": "Purchase promo created"}


@router.put("/admin/purchase-promos/{promo_id}")
async def update_purchase_promo(
    promo_id: int,
    body: AdminPurchasePromoBody,
    current_user: User = Depends(_require_admin),
):
    payload = _payload_from_body(body)
    with get_conn() as conn:
        ensure_purchase_promo_tables(conn)
        cur = execute(
            conn,
            """
            UPDATE purchase_promo_codes
            SET name = ?, code = ?, percent = ?, channels = ?, starts_at = ?, ends_at = ?,
                is_active = ?, user_created_after = ?, max_uses = ?, max_uses_per_user = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                payload["name"],
                payload["code"],
                payload["percent"],
                payload["channels"],
                payload["starts_at"],
                payload["ends_at"],
                payload["is_active"],
                payload["user_created_after"],
                payload["max_uses"],
                payload["max_uses_per_user"],
                promo_id,
            ),
        )
        if (cur.rowcount or 0) == 0:
            raise HTTPException(status_code=404, detail="Promo not found")
        conn.commit()
    return {"message": "Purchase promo updated"}


@router.post("/admin/purchase-promos/{promo_id}/stop")
async def stop_purchase_promo(promo_id: int, current_user: User = Depends(_require_admin)):
    with get_conn() as conn:
        ensure_purchase_promo_tables(conn)
        cur = execute(
            conn,
            """
            UPDATE purchase_promo_codes
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (promo_id,),
        )
        if (cur.rowcount or 0) == 0:
            raise HTTPException(status_code=404, detail="Promo not found")
        conn.commit()
    return {"message": "Purchase promo stopped"}
