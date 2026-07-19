from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import base64
import logging
import os
import re
import time
import math
import uuid
import requests
from collections import OrderedDict
from threading import Lock
from auth import get_current_user, User
from .credit_service import CreditService
from .admin.promo_manager import PromoCodeManager
from utils.env_json import parse_json_from_env
from activity.publisher import publish_activity
from db import get_conn, execute, SQL_SUBSCRIPTION_PLAN_ACTIVE
from .razorpay_routes import refund_razorpay_payment, fetch_razorpay_payment
from utils.admin_settings import get_chart_guide_video_url, get_nakshatra_guide_videos

router = APIRouter()
credit_service = CreditService()
promo_manager = PromoCodeManager()

logger = logging.getLogger(__name__)

DEFAULT_STANDARD_CHAT_COUNTDOWN_SECONDS = 110
DEFAULT_PREMIUM_CHAT_COUNTDOWN_SECONDS = 210
GOOGLE_PLAY_HTTP_TIMEOUT_SECONDS = float(os.getenv("GOOGLE_PLAY_HTTP_TIMEOUT_SECONDS", "3.0"))
GOOGLE_PLAY_PRODUCTS_CACHE_TTL_SECONDS = int(os.getenv("GOOGLE_PLAY_PRODUCTS_CACHE_TTL_SECONDS", "86400"))
GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE_TTL_SECONDS = int(os.getenv("GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE_TTL_SECONDS", "86400"))
GOOGLE_PLAY_PRODUCTS_CACHE_MAX = 8
GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE_MAX = 32
PLAY_PAYMENT_SERVICE_TIMEOUT_SECONDS = float(os.getenv("PLAY_PAYMENT_SERVICE_TIMEOUT_SECONDS", "8.0"))
SPEECH_BILLING_MIN_START_MINUTES = 5

# Env var name preferred; GOOGLE_SERVICE_ACCOUNT_KEY accepted as fallback.
# Keep trying fallback values if the preferred env points at a missing file.
PLAY_CREDENTIAL_ENV_KEYS = ("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "GOOGLE_SERVICE_ACCOUNT_KEY")
_GOOGLE_PLAY_PRODUCTS_CACHE: OrderedDict = OrderedDict()
_GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE: OrderedDict = OrderedDict()
_GOOGLE_PLAY_CACHE_LOCK = Lock()


def _cache_get(cache: OrderedDict, key):
    now = time.monotonic()
    with _GOOGLE_PLAY_CACHE_LOCK:
        entry = cache.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if expires_at <= now:
            cache.pop(key, None)
            return None
        cache.move_to_end(key)
        return value


def _cache_set(cache: OrderedDict, key, value, ttl_seconds: int, max_entries: int):
    expires_at = time.monotonic() + max(1, int(ttl_seconds))
    with _GOOGLE_PLAY_CACHE_LOCK:
        cache[key] = (expires_at, value)
        cache.move_to_end(key)
        while len(cache) > max_entries:
            cache.popitem(last=False)


def _get_play_credentials_candidates():
    candidates = []
    for key in PLAY_CREDENTIAL_ENV_KEYS:
        raw = os.environ.get(key)
        if raw and raw.strip():
            candidates.append((key, raw.strip()))
    return candidates


def _get_play_credentials_path():
    candidates = _get_play_credentials_candidates()
    return candidates[0][1] if candidates else None


def _ensure_speech_billing_table(conn) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS speech_billing_sessions (
            session_id TEXT PRIMARY KEY,
            userid INTEGER NOT NULL,
            started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'active',
            per_minute_cost INTEGER NOT NULL,
            original_per_minute_cost INTEGER NOT NULL,
            discount_percent INTEGER NOT NULL DEFAULT 0,
            required_start_credits INTEGER NOT NULL,
            starting_balance INTEGER NOT NULL,
            charged_credits INTEGER NOT NULL DEFAULT 0,
            elapsed_seconds INTEGER NOT NULL DEFAULT 0,
            ended_reason TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        (),
    )


def _speech_minutes_from_seconds(seconds: int) -> int:
    return max(1, int(math.ceil(max(1, int(seconds or 0)) / 60.0)))


def _iso_utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _get_play_credentials():
    """
    Return Google service account credentials from env.
    Supports (1) file path to JSON, or (2) inline JSON string in the env var.
    """
    from google.oauth2 import service_account
    _ensure_play_env_loaded()
    candidates = _get_play_credentials_candidates()
    if not candidates:
        return None
    scopes = ["https://www.googleapis.com/auth/androidpublisher"]
    for key, raw in candidates:
        # Inline JSON: value starts with { (or is wrapped in quotes by .env)
        info = parse_json_from_env(raw)
        if info:
            try:
                return service_account.Credentials.from_service_account_info(info, scopes=scopes)
            except (ValueError, TypeError) as e:
                logger.warning("Google Play: invalid inline JSON credentials in %s: %s", key, e)
                continue
        # File path
        if os.path.isfile(raw):
            return service_account.Credentials.from_service_account_file(raw, scopes=scopes)
        logger.warning(
            "Google Play: %s is neither a valid file path nor JSON (starts with %r)",
            key,
            raw[:50] if len(raw) > 50 else raw,
        )
    return None

# Load backend/.env when credentials path is missing (e.g. gunicorn/workers or import order)
def _ensure_play_env_loaded():
    if _get_play_credentials_path():
        return
    try:
        from dotenv import load_dotenv
        # __file__ is backend/credits/routes.py -> backend_dir = backend
        _backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _env_path = os.path.join(_backend_dir, ".env")
        logger.info("Google Play: env var not set, trying .env at %s (exists=%s)", _env_path, os.path.isfile(_env_path))
        if os.path.isfile(_env_path):
            # override=True so we replace any empty/wrong value already in os.environ
            load_dotenv(_env_path, override=True)
            val = _get_play_credentials_path()
            if val:
                logger.info("Google Play: loaded credentials path from .env (length=%s)", len(val))
            else:
                # Show which keys in .env look related (for debugging typo in var name)
                try:
                    with open(_env_path, "r") as f:
                        keys = [line.split("=")[0].strip() for line in f if line.strip() and "=" in line and not line.strip().startswith("#")]
                    play_keys = [k for k in keys if "GOOGLE" in k.upper() or "PLAY" in k.upper() or "CREDENTIAL" in k.upper()]
                    logger.warning("Google Play: .env loaded but no credentials path. Use GOOGLE_PLAY_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_KEY. Found: %s", play_keys)
                except Exception:
                    logger.warning("Google Play: .env loaded but no credentials path (GOOGLE_PLAY_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_KEY)")
    except Exception as e:
        logger.warning("Google Play: could not load .env in credits route: %s", e, exc_info=True)

# Product ID convention for credit packs: credits_N -> N credits (used when fetching from Play or when no map)
CREDITS_PRODUCT_PATTERN = re.compile(r"^credits_(\d+)$")

class PromoCodeRequest(BaseModel):
    code: str

class CreatePromoCodeRequest(BaseModel):
    code: str
    credits: int
    max_uses: int = 1
    max_uses_per_user: int = 1
    expires_at: Optional[str] = None

class UpdatePromoCodeRequest(BaseModel):
    credits: int
    max_uses: int
    max_uses_per_user: int
    is_active: bool


class UpdateCreditProductRequest(BaseModel):
    is_active: bool


class AdminRefundRequest(BaseModel):
    userid: int
    transaction_id: int
    amount: int
    comment: Optional[str] = None


GOOGLE_PLAY_SOURCE = "google_play"


PACKAGE_NAME = "com.astroroshni.mobile"


def _userid_from_play_obfuscated_account(value: Optional[str]) -> Optional[int]:
    raw = str(value or "").strip()
    if not raw:
        return None
    lowered = raw.lower()
    for prefix in ("user:", "uid:", "userid:", "u:"):
        if lowered.startswith(prefix):
            raw = raw[len(prefix):].strip()
            break
    if raw.isdigit():
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
    return None


def _get_play_service():
    """Build Android Publisher API service with service account credentials (file path or inline JSON)."""
    try:
        from googleapiclient.discovery import build
    except ImportError as e:
        logger.error("Google Play: missing dependency: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Google Play not configured (install google-api-python-client and google-auth).",
        )
    credentials = _get_play_credentials()
    if not credentials:
        logger.error("Google Play: credentials not available (set GOOGLE_PLAY_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_KEY to a file path or inline JSON)")
        raise HTTPException(
            status_code=503,
            detail="Google Play service account JSON not configured (set GOOGLE_PLAY_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_KEY).",
        )
    return build("androidpublisher", "v3", credentials=credentials)


def _verify_google_play_purchase(package_name: str, product_id: str, purchase_token: str) -> dict:
    """Verify purchase with Google Play Developer API. Returns purchase info or raises."""
    logger.info("Google Play: verifying product purchase package=%s productId=%s", package_name, product_id)
    try:
        service = _get_play_service()
        request = service.purchases().products().get(
            packageName=package_name,
            productId=product_id,
            token=purchase_token,
        )
        result = request.execute()
        logger.info("Google Play: product verify response keys=%s", list(result.keys()) if isinstance(result, dict) else type(result))
        return result
    except Exception as e:
        logger.error("Google Play: product verify error: %s", e, exc_info=True)
        raise


def _verify_google_play_subscription(package_name: str, subscription_id: str, purchase_token: str) -> dict:
    """Verify subscription with Google Play Developer API. Returns subscription info (expiryTimeMillis, startTimeMillis, etc.) or raises."""
    return _fetch_google_play_subscription_purchase(
        package_name, subscription_id, purchase_token, prefer_v2=True
    )


def _fetch_google_play_subscription_purchase(
    package_name: str,
    subscription_id: str,
    purchase_token: str,
    *,
    prefer_v2: bool = True,
) -> dict:
    """
    Load subscription state from Play (subscriptionsv2, then v1 fallback).
    Normalizes v2 fields onto v1-style keys where possible (orderId, startTimeMillis, expiryTimeMillis).
    """
    token = (purchase_token or "").strip()
    if not token:
        raise ValueError("purchase_token is required")
    service = _get_play_service()
    last_err: Optional[Exception] = None

    def _try_v2() -> Optional[dict]:
        try:
            result = (
                service.purchases()
                .subscriptionsv2()
                .get(packageName=package_name, token=token)
                .execute()
            )
            if not isinstance(result, dict):
                return None
            line_items = result.get("lineItems") or []
            line = line_items[0] if line_items else {}
            order_id = (
                line.get("latestSuccessfulOrderId")
                or result.get("latestOrderId")
            )
            start_iso = result.get("startTime") or line.get("startTime")
            expiry_iso = line.get("expiryTime") or result.get("expiryTime")
            out = dict(result)
            if order_id:
                out["orderId"] = order_id
                out["latestOrderId"] = order_id
            if start_iso:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(str(start_iso).replace("Z", "+00:00"))
                    out["startTimeMillis"] = int(dt.timestamp() * 1000)
                except Exception:
                    pass
            if expiry_iso:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(str(expiry_iso).replace("Z", "+00:00"))
                    out["expiryTimeMillis"] = int(dt.timestamp() * 1000)
                except Exception:
                    pass
            product_id = line.get("productId") or subscription_id
            if product_id:
                out["productId"] = product_id
            return out
        except Exception as e:
            nonlocal last_err
            last_err = e
            return None

    def _try_v1() -> dict:
        logger.info(
            "Google Play: verifying subscription package=%s subscriptionId=%s",
            package_name,
            subscription_id,
        )
        result = (
            service.purchases()
            .subscriptions()
            .get(
                packageName=package_name,
                subscriptionId=subscription_id,
                token=token,
            )
            .execute()
        )
        logger.info(
            "Google Play: subscription verify response keys=%s",
            list(result.keys()) if isinstance(result, dict) else type(result),
        )
        return result

    if prefer_v2:
        v2 = _try_v2()
        if v2:
            return v2
    try:
        return _try_v1()
    except Exception as e:
        last_err = e
    if prefer_v2:
        try:
            return _try_v1()
        except Exception as e:
            last_err = e
    raise last_err or RuntimeError("Failed to fetch subscription from Google Play")


def _subscription_period_dates_from_purchase(purchase: dict) -> tuple:
    """Return (start_date, end_date) as YYYY-MM-DD from Play subscription payload."""
    from datetime import datetime

    purchase = purchase or {}
    expiry_ms = purchase.get("expiryTimeMillis") or purchase.get("startTimeMillis") or 0
    start_ms = purchase.get("startTimeMillis") or expiry_ms
    start_date = datetime.utcfromtimestamp(int(start_ms) / 1000).strftime("%Y-%m-%d")
    end_date = datetime.utcfromtimestamp(int(expiry_ms) / 1000).strftime("%Y-%m-%d")
    return start_date, end_date


def _credits_from_product_id(product_id: str) -> Optional[int]:
    """Parse product_id per convention credits_N -> N. Returns None if not a credit product."""
    m = CREDITS_PRODUCT_PATTERN.match((product_id or "").strip())
    return int(m.group(1)) if m else None


def _price_from_play_money(price_obj: dict) -> Optional[tuple]:
    """
    Extract (amount, currency_code) from Play Money object.
    Supports: priceAmountMicros + currencyCode, or units + nanos + currencyCode.
    """
    if not price_obj or not isinstance(price_obj, dict):
        return None
    currency = price_obj.get("currencyCode")
    micros = price_obj.get("priceAmountMicros")
    if micros is not None:
        try:
            amount = int(micros) / 1_000_000
            return (amount, currency)
        except (TypeError, ValueError):
            pass
    units = price_obj.get("units")
    nanos = price_obj.get("nanos")
    if units is not None:
        try:
            u = int(units)
            n = int(nanos) if nanos is not None else 0
            amount = u + n / 1_000_000_000
            return (amount, currency)
        except (TypeError, ValueError):
            pass
    return None


def _format_play_money(price_amount_micros: Optional[str], currency_code: Optional[str]) -> Optional[str]:
    """Format Google Play Money (priceAmountMicros, currencyCode) to a display string e.g. '₹399' or '$4.99'."""
    if price_amount_micros is None:
        return None
    try:
        micros = int(price_amount_micros)
    except (TypeError, ValueError):
        return None
    amount = micros / 1_000_000
    return _format_amount_currency(amount, currency_code)


def _format_amount_currency(amount: float, currency_code: Optional[str]) -> str:
    """Format amount + currency to display string e.g. '₹399', '$4.99'."""
    if currency_code == "INR":
        return f"₹{int(amount)}" if amount == int(amount) else f"₹{amount:.2f}"
    if currency_code == "USD":
        return f"${amount:.2f}"
    if currency_code == "EUR":
        return f"€{amount:.2f}"
    if currency_code:
        return f"{amount:.2f} {currency_code}"
    return f"{amount:.2f}"


def _get_subscription_price_from_play(package_name: str, product_id: str) -> Optional[str]:
    """
    Fetch subscription product from Google Play (monetization.subscriptions.get) and return
    a formatted price string from the first base plan's first regional config (or otherRegionsConfig).
    """
    cache_key = (package_name, product_id)
    cached = _cache_get(_GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE, cache_key)
    if cached is not None:
        return cached
    try:
        from google.auth.transport.requests import AuthorizedSession

        credentials = _get_play_credentials()
        if not credentials:
            return None
        session = AuthorizedSession(credentials)
        url = f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{package_name}/subscriptions/{product_id}"
        logger.info("Google Play: fetching subscription price GET %s", url)
        resp = session.get(url, timeout=GOOGLE_PLAY_HTTP_TIMEOUT_SECONDS)
        if resp.status_code != 200:
            logger.warning(
                "Google Play subscription get %s/%s: status=%s body=%s",
                package_name, product_id, resp.status_code, resp.text[:500] if resp.text else "(empty)"
            )
            return None
        data = resp.json()
        logger.info("Google Play subscription get %s: basePlans count=%s", product_id, len(data.get("basePlans") or []))
        # Log response structure for debugging price extraction
        try:
            struct = {k: (list(v[0].keys()) if isinstance(v, list) and v and isinstance(v[0], dict) else type(v).__name__) for k, v in data.items()}
            logger.info("Google Play subscription response keys: %s", list(data.keys()))
            for i, bp in enumerate(data.get("basePlans") or []):
                bp_keys = list(bp.keys()) if isinstance(bp, dict) else []
                logger.info("Google Play basePlan[%s] keys: %s state=%s", i, bp_keys, bp.get("state") if isinstance(bp, dict) else "?")
                reg = bp.get("regionalConfigs") or [] if isinstance(bp, dict) else []
                if reg and isinstance(reg, list):
                    rc0 = reg[0] if reg else {}
                    logger.info("Google Play basePlan[%s] regionalConfigs[0] keys: %s price=%s", i, list(rc0.keys()) if isinstance(rc0, dict) else [], rc0.get("price") if isinstance(rc0, dict) else None)
                other = bp.get("otherRegionsConfig") or {} if isinstance(bp, dict) else {}
                if other:
                    logger.info("Google Play basePlan[%s] otherRegionsConfig keys: %s", i, list(other.keys()) if isinstance(other, dict) else [])
            full_json = json.dumps(data, indent=2, default=str)
            logger.info("Google Play subscription full response (first 3000 chars): %s", full_json[:3000])
        except Exception as le:
            logger.warning("Google Play subscription log structure: %s", le)
        base_plans = data.get("basePlans") or []
        for bp in base_plans:
            if bp.get("state") == "INACTIVE":
                continue
            regional = (bp.get("regionalConfigs") or [])
            # Prefer INR, then USD, then EUR, then first regional
            for region_code in ("IN", "US", "GB", "AE", "AT"):
                rc = next((r for r in regional if r.get("regionCode") == region_code), None)
                if rc:
                    parsed = _price_from_play_money(rc.get("price") or {})
                    if parsed:
                        amount, currency = parsed
                        formatted = _format_amount_currency(amount, currency)
                        logger.info("Google Play subscription price %s: %s (region %s)", product_id, formatted, region_code)
                        _cache_set(
                            _GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE,
                            cache_key,
                            formatted,
                            GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE_TTL_SECONDS,
                            GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE_MAX,
                        )
                        return formatted
            # Fallback: first regional config
            for rc in regional:
                parsed = _price_from_play_money(rc.get("price") or {})
                if parsed:
                    amount, currency = parsed
                    formatted = _format_amount_currency(amount, currency)
                    logger.info("Google Play subscription price %s: %s (from regionalConfig)", product_id, formatted)
                    _cache_set(
                        _GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE,
                        cache_key,
                        formatted,
                        GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE_TTL_SECONDS,
                        GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE_MAX,
                    )
                    return formatted
            other = bp.get("otherRegionsConfig") or {}
            for key in ("usdPrice", "eurPrice"):
                parsed = _price_from_play_money(other.get(key) or {})
                if parsed:
                    amount, currency = parsed
                    formatted = _format_amount_currency(amount, currency or ("USD" if key == "usdPrice" else "EUR"))
                    logger.info("Google Play subscription price %s: %s (from %s)", product_id, formatted, key)
                    _cache_set(
                        _GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE,
                        cache_key,
                        formatted,
                        GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE_TTL_SECONDS,
                        GOOGLE_PLAY_SUBSCRIPTION_PRICE_CACHE_MAX,
                    )
                    return formatted
        logger.info("Google Play subscription price %s: no price found in basePlans", product_id)
        return None
    except Exception as e:
        logger.warning("Google Play subscription price for %s: %s", product_id, e, exc_info=True)
        return None


def _list_google_play_products(package_name: str) -> List[dict]:
    """
    Fetch in-app products from Google Play and return credit products only.
    Uses the new monetization.onetimeproducts.list endpoint and includes only
    one-time products whose productId matches credits_N; credits are derived from N.
    """
    cached = _cache_get(_GOOGLE_PLAY_PRODUCTS_CACHE, package_name)
    if cached is not None:
        return [dict(product) for product in cached]
    try:
        # Use google-auth directly because the installed google-api-python-client
        # may not yet expose monetization.onetimeproducts on the discovery stub.
        from google.auth.transport.requests import AuthorizedSession

        credentials = _get_play_credentials()
        if not credentials:
            logger.error("Google Play products: credentials not available (file path or inline JSON)")
            raise HTTPException(
                status_code=503,
                detail="Google Play service account JSON not configured (set GOOGLE_PLAY_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_KEY).",
            )
        session = AuthorizedSession(credentials)

        all_products: List[dict] = []
        # Use the new one-time products REST endpoint:
        # GET https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{packageName}/oneTimeProducts
        base_url = f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{package_name}/oneTimeProducts"
        logger.info("Google Play: listing one-time products GET %s", base_url)

        page_token: Optional[str] = None
        while True:
            params = {}
            if page_token:
                params["pageToken"] = page_token
            resp = session.get(base_url, params=params, timeout=GOOGLE_PLAY_HTTP_TIMEOUT_SECONDS)
            if resp.status_code != 200:
                logger.error(
                    "Google Play oneTimeProducts list: status=%s body=%s",
                    resp.status_code, resp.text[:1000] if resp.text else "(empty)"
                )
            if resp.status_code == 403:
                # Surface the body so we can see the exact permission error.
                logger.error("Google Play: 403 from monetization.onetimeproducts.list: %s", resp.text)
                raise HTTPException(status_code=403, detail=resp.text)
            resp.raise_for_status()
            data = resp.json()
            logger.info("Google Play oneTimeProducts response: oneTimeProducts count=%s nextPageToken=%s", len(data.get("oneTimeProducts") or []), bool(data.get("nextPageToken")))
            for p in data.get("oneTimeProducts", []):
                sku = (p.get("productId") or "").strip()
                credits = _credits_from_product_id(sku)
                if credits is None:
                    continue

                # listings can be either a dict keyed by language, or a list of objects
                listings = p.get("listings") or []
                default_lang = p.get("defaultLanguage") or "en-US"
                listing = None
                if isinstance(listings, dict):
                    listing = (
                        listings.get(default_lang)
                        or listings.get("en-US")
                        or (next(iter(listings.values()), None) if listings else None)
                    )
                elif isinstance(listings, list):
                    # Try to find the default language entry; otherwise take the first
                    listing = next(
                        (l for l in listings if isinstance(l, dict) and l.get("languageCode") == default_lang),
                        None,
                    )
                    if listing is None and listings:
                        listing = listings[0]

                title = (listing.get("title") or sku) if isinstance(listing, dict) else sku
                description = (listing.get("description") or "") if isinstance(listing, dict) else ""
                # Price lives under purchaseOptions; we don't need it for now, so just send placeholders.
                all_products.append({
                    "product_id": sku,
                    "credits": credits,
                    "title": title,
                    "description": description,
                    "price_micros": "0",
                    "price_currency": "USD",
                })
            page_token = data.get("nextPageToken")
            if not page_token:
                break

        sorted_products = sorted(all_products, key=lambda x: x["credits"])
        logger.info("Google Play: listed %d credit products via monetization.onetimeproducts.list", len(sorted_products))
        _cache_set(
            _GOOGLE_PLAY_PRODUCTS_CACHE,
            package_name,
            [dict(product) for product in sorted_products],
            GOOGLE_PLAY_PRODUCTS_CACHE_TTL_SECONDS,
            GOOGLE_PLAY_PRODUCTS_CACHE_MAX,
        )
        return sorted_products
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Google Play: unexpected error while listing products: %s", str(e), exc_info=True)
        raise HTTPException(status_code=503, detail=f"Failed to list Google Play products: {str(e)}")


def _refund_google_play_order(package_name: str, order_id: str):
    """
    Call Google Play orders.refund API. Returns (True, "Refund succeeded") on success,
    (True, "Already refunded") if order was already refunded, (False, error_message) on failure.
    """
    try:
        from googleapiclient.errors import HttpError
    except ImportError:
        return False, "Google API client not available"
    try:
        service = _get_play_service()
        service.orders().refund(packageName=package_name, orderId=order_id).execute()
        return True, "Refund succeeded"
    except HttpError as e:
        if e.resp.status in (400, 404):
            content = (e.content or b"").decode("utf-8", errors="ignore")
            if "refund" in content.lower() or "already" in content.lower() or e.resp.status == 404:
                return True, "Already refunded"
        return False, (e.content and e.content.decode("utf-8", errors="ignore")) or str(e)
    except HTTPException:
        raise
    except Exception as e:
        return False, str(e)


class GooglePlayVerifyRequest(BaseModel):
    purchase_token: str
    product_id: str
    order_id: str
    price_amount_micros: Optional[int] = None
    price_currency: Optional[str] = None
    localized_price: Optional[str] = None


class GooglePlaySubscriptionVerifyRequest(BaseModel):
    purchase_token: str
    product_id: str  # subscription_vip_silver, subscription_vip_gold, subscription_vip_platinum (tier-based; price set in Play Console)
    order_id: Optional[str] = None  # GPA order id from client (Play verify response is authoritative when present)


def _play_payment_service_shared_secret() -> str:
    return (os.getenv("PLAY_PAYMENT_SERVICE_SHARED_SECRET") or "").strip()


def _payment_service_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    secret = _play_payment_service_shared_secret()
    if secret:
        headers["X-Play-Payment-Service-Secret"] = secret
    return headers


def _proxy_to_play_payment_service(
    *,
    path: str,
    payload: Dict[str, Any],
    current_user: User,
) -> Optional[Dict[str, Any]]:
    from utils.admin_settings import (
        get_play_payment_service_base_url,
        play_payment_service_enabled_for_user,
    )

    if not play_payment_service_enabled_for_user(getattr(current_user, "userid", None)):
        return None

    base_url = get_play_payment_service_base_url()
    if not base_url:
        logger.warning(
            "Play payment service flag is enabled for user=%s but base URL is not configured; using legacy local flow",
            getattr(current_user, "userid", None),
        )
        return None

    request_body = {
        **payload,
        "userid": current_user.userid,
        "user_phone": getattr(current_user, "phone", None),
        "user_name": getattr(current_user, "name", None),
    }
    target_url = f"{base_url}{path}"
    order_id = str(payload.get("order_id") or "").strip() or "n/a"

    try:
        response = requests.post(
            target_url,
            json=request_body,
            headers=_payment_service_headers(),
            timeout=PLAY_PAYMENT_SERVICE_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        logger.warning(
            "Play payment service proxy failed for user=%s path=%s error=%s; using legacy local flow",
            current_user.userid,
            path,
            exc,
        )
        return None

    if response.status_code < 200 or response.status_code >= 300:
        logger.warning(
            "Play payment service returned %s for user=%s path=%s; using legacy local flow",
            response.status_code,
            current_user.userid,
            path,
        )
        return None

    try:
        data = response.json() if response.content else {}
    except ValueError:
        logger.warning(
            "Play payment service returned non-JSON response for user=%s path=%s; using legacy local flow",
            current_user.userid,
            path,
        )
        return None

    if not isinstance(data, dict):
        logger.warning(
            "Play payment service returned unexpected JSON shape for user=%s path=%s; using legacy local flow",
            current_user.userid,
            path,
        )
        return None
    logger.info(
        "Play payment served_by=play-payment-service user=%s path=%s order_id=%s status=%s",
        current_user.userid,
        path,
        order_id,
        response.status_code,
    )
    return data


def _mark_main_backend_fallback(
    response: Dict[str, Any],
    *,
    path: str,
    current_user: User,
    order_id: Optional[str] = None,
) -> Dict[str, Any]:
    response["served_by"] = "main-backend-fallback"
    logger.info(
        "Play payment served_by=main-backend-fallback user=%s path=%s order_id=%s",
        getattr(current_user, "userid", None),
        path,
        (order_id or "").strip() or "n/a",
    )
    return response


def _credit_verified_google_play_purchase(
    *,
    userid: int,
    user_phone: Optional[str],
    user_name: Optional[str],
    purchase_token: str,
    product_id: str,
    order_id_hint: Optional[str] = None,
    price_amount_micros: Optional[int] = None,
    price_currency: Optional[str] = None,
    localized_price: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify one-time Play purchase, then credit user idempotently by order_id."""
    amount = _credits_from_product_id(product_id)
    if amount is None:
        raise HTTPException(status_code=400, detail=f"Unknown or invalid product_id (expected credits_N): {product_id}")
    token = (purchase_token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="purchase_token is required")

    try:
        purchase = _verify_google_play_purchase(PACKAGE_NAME, product_id, token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid or expired purchase: {str(e)}")

    purchase_state = purchase.get("purchaseState")
    if purchase_state != 0:  # 0 = Purchased
        raise HTTPException(status_code=400, detail="Purchase not in completed state")

    order_id = (purchase.get("orderId") or order_id_hint or "").strip()
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id is required")

    # Keep purchase token ownership map fresh so RTDN can resolve user by token.
    try:
        credit_service.upsert_play_onetime_token(userid, token, product_id)
    except Exception:
        pass

    if credit_service.has_transaction_with_reference(userid, GOOGLE_PLAY_SOURCE, order_id):
        extras = credit_service.apply_purchase_extras(
            userid=userid,
            purchased_credits=amount,
            purchase_source=GOOGLE_PLAY_SOURCE,
            purchase_reference_id=order_id,
            product_id=product_id,
        )
        return {
            "success": True,
            "message": "Already credited",
            "credits_added": 0,
            "order_id": order_id,
            "first_purchase_bonus": extras.get("first_purchase_bonus"),
            "purchase_discount": extras.get("purchase_discount"),
            "bonus_credits_added": int(extras.get("bonus_credits_added") or 0),
            "first_purchase_bonus_credits_added": int(extras.get("first_purchase_bonus_credits_added") or 0),
            "discount_credits_added": int(extras.get("discount_credits_added") or 0),
        }

    purchase_metadata = json.dumps({
        "purchase_token": purchase.get("purchaseToken") or token,
        "purchase_time_millis": purchase.get("purchaseTimeMillis"),
        "product_id": product_id,
        "order_id": order_id,
        "price_amount_micros": price_amount_micros,
        "price_currency": price_currency,
        "localized_price": localized_price,
    })

    ok = credit_service.add_credits(
        userid,
        amount,
        GOOGLE_PLAY_SOURCE,
        reference_id=order_id,
        description=f"Google Play: {product_id}",
        metadata=purchase_metadata,
    )
    if not ok:
        logger.error(
            "Google Play: verify OK with Play but add_credits failed user=%s order_id=%s product=%s amount=%s",
            userid,
            order_id,
            product_id,
            amount,
        )
        raise HTTPException(
            status_code=500,
            detail="Purchase verified with Google Play but credits could not be saved. Please contact support with your order id.",
        )

    publish_activity(
        "credits_purchased",
        user_id=userid,
        user_phone=user_phone,
        user_name=user_name,
        resource_type="order",
        resource_id=order_id,
        metadata={
            "credits_added": amount,
            "product_id": product_id,
            "order_id": order_id,
        },
    )
    extras = credit_service.apply_purchase_extras(
        userid=userid,
        purchased_credits=amount,
        purchase_source=GOOGLE_PLAY_SOURCE,
        purchase_reference_id=order_id,
        product_id=product_id,
    )
    bonus_added = int(extras.get("bonus_credits_added") or 0)
    return {
        "success": True,
        "message": "Credits added",
        "credits_added": amount + bonus_added,
        "purchased_credits_added": amount,
        "bonus_credits_added": bonus_added,
        "first_purchase_bonus_credits_added": int(extras.get("first_purchase_bonus_credits_added") or 0),
        "discount_credits_added": int(extras.get("discount_credits_added") or 0),
        "first_purchase_bonus": extras.get("first_purchase_bonus"),
        "purchase_discount": extras.get("purchase_discount"),
        "order_id": order_id,
    }


def _process_pending_google_play_onetime_events_for_token(
    *,
    userid: int,
    purchase_token: str,
    product_id_hint: Optional[str] = None,
) -> Dict[str, Any]:
    token = (purchase_token or "").strip()
    if not token:
        return {"found": 0, "resolved": 0, "failed": 0}

    pending_rows = credit_service.get_pending_play_onetime_events(
        purchase_token=token,
        userid=userid,
        limit=50,
    )
    found = len(pending_rows or [])
    resolved = 0
    failed = 0
    for row in pending_rows or []:
        event_id = str(row[0] or "").strip()
        product_id = str(row[2] or product_id_hint or "").strip()
        if not event_id or not product_id:
            failed += 1
            credit_service.resolve_pending_play_onetime_event(
                event_id,
                userid=userid,
                status="failed",
                resolution_note="missing_token_or_product",
                last_error="Missing purchase token or product id while retrying pending one-time RTDN",
            )
            continue
        try:
            result = _credit_verified_google_play_purchase(
                userid=userid,
                user_phone=None,
                user_name=None,
                purchase_token=token,
                product_id=product_id,
                order_id_hint=None,
            )
            resolution_note = (
                "already_credited"
                if int(result.get("credits_added") or 0) == 0 and "already" in str(result.get("message") or "").lower()
                else "credited"
            )
            credit_service.log_play_onetime_event(
                event_id=event_id,
                purchase_token=token,
                product_id=product_id,
                notification_type=row[3],
                event_time_millis=row[4],
                payload_json=row[5],
            )
            credit_service.resolve_pending_play_onetime_event(
                event_id,
                userid=userid,
                status="resolved",
                resolution_note=resolution_note,
            )
            resolved += 1
        except HTTPException as exc:
            failed += 1
            detail = getattr(exc, "detail", None) or str(exc)
            credit_service.mark_pending_play_onetime_event_retry(
                event_id,
                userid=userid,
                last_error=str(detail),
            )
            logger.warning(
                "Pending Google Play one-time retry failed event_id=%s user=%s product=%s detail=%s",
                event_id,
                userid,
                product_id,
                detail,
            )
        except Exception as exc:
            failed += 1
            credit_service.mark_pending_play_onetime_event_retry(
                event_id,
                userid=userid,
                last_error=str(exc),
            )
            logger.exception(
                "Pending Google Play one-time retry crashed event_id=%s user=%s product=%s",
                event_id,
                userid,
                product_id,
            )
    return {"found": found, "resolved": resolved, "failed": failed}


def _resolve_userid_from_google_play_onetime_purchase(
    *,
    purchase_token: str,
    product_id: str,
) -> Optional[int]:
    try:
        purchase = _verify_google_play_purchase(PACKAGE_NAME, product_id, purchase_token)
    except Exception:
        logger.exception(
            "Google Play one-time ownership resolve failed product=%s token_prefix=%s",
            product_id,
            (purchase_token or "")[:12],
        )
        return None
    for key in ("obfuscatedExternalAccountId", "obfuscatedAccountId", "obfuscatedExternalProfileId"):
        userid = _userid_from_play_obfuscated_account(purchase.get(key))
        if userid is not None:
            return userid
    return None


@router.get("/google-play/products")
async def get_google_play_products(current_user: User = Depends(get_current_user)):
    """List credit products from Google Play (active in-app products with id convention credits_N)."""
    try:
        products = _list_google_play_products(PACKAGE_NAME)
        # Admin portal can disable packs without removing them from Play Console.
        sellable_ids = credit_service.list_active_credit_product_ids()
        products = [p for p in products if str(p.get("product_id") or "") in sellable_ids]
        first_purchase_base_status = credit_service._first_purchase_bonus_base_status(current_user.userid)
        purchase_discount_base_status = credit_service._purchase_discount_base_status(current_user.userid)
        try:
            from credits.razorpay_routes import CREDIT_PACK_META
        except Exception:
            CREDIT_PACK_META = {}
        for product in products:
            try:
                credits = int(product.get("credits") or 0)
                meta = CREDIT_PACK_META.get(credits) or {}
                if meta:
                    product["name"] = meta.get("name") or product.get("title")
                    product["badge"] = meta.get("badge")
                    product["questions"] = meta.get("questions")
                    product["save_percent"] = meta.get("save_percent") or 0
                    product["value_prop"] = meta.get("value_prop")
                    product["pack_bonus_credits"] = int(meta.get("bonus_credits") or 0)
                product_id = str(product.get("product_id") or "").strip() or None
                status = credit_service._compose_bonus_status(
                    first_purchase_base_status,
                    purchased_credits=credits,
                    product_id=product_id,
                )
                product["first_purchase_bonus"] = status
                discount_status = credit_service._compose_bonus_status(
                    purchase_discount_base_status,
                    purchased_credits=credits,
                    product_id=product_id,
                )
                product["purchase_discount"] = discount_status
                pack_bonus = int(product.get("pack_bonus_credits") or 0)
                bonus_total = pack_bonus
                if status.get("eligible") and int(status.get("bonus_credits") or 0) > 0:
                    bonus_total += int(status.get("bonus_credits") or 0)
                if discount_status.get("eligible") and int(discount_status.get("bonus_credits") or 0) > 0:
                    bonus_total += int(discount_status.get("bonus_credits") or 0)
                if bonus_total > 0:
                    product["bonus_credits"] = bonus_total
                    product["total_credits"] = credits + bonus_total
            except Exception:
                logger.exception(
                    "Google Play product bonus decoration failed user=%s product_id=%s raw_product=%s",
                    current_user.userid,
                    product.get("product_id"),
                    product,
                )
        # Shuruaat → Aashirwad → Sadhak → Guru order
        products.sort(key=lambda p: int(p.get("credits") or 0))
        return {"products": products}
    except HTTPException as e:
        # When Play is not configured (e.g. local dev without GOOGLE_PLAY_SERVICE_ACCOUNT_JSON), return empty list so app still works
        if e.status_code == 503:
            logger.warning("Google Play products: returning empty list due to 503 (detail=%s)", e.detail)
            return {"products": []}
        raise
    except Exception as e:
        logger.warning("Google Play products unavailable: %s", e, exc_info=True)
        return {"products": []}


@router.get("/purchase-discount/status")
async def get_purchase_discount_status(
    purchased_credits: Optional[int] = Query(default=None),
    product_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    """Preview the open purchase discount campaign for the current user."""
    return credit_service.get_purchase_discount_status(
        current_user.userid,
        purchased_credits,
        product_id=(product_id or "").strip() or None,
    )


@router.get("/first-purchase-bonus/status")
async def get_first_purchase_bonus_status(
    purchased_credits: Optional[int] = Query(default=None),
    product_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    """Preview the gated post-free-question first purchase bonus for the current user."""
    return credit_service.get_first_purchase_bonus_status(
        current_user.userid,
        purchased_credits,
        product_id=(product_id or "").strip() or None,
    )


class FreeAnswerFunnelEventBody(BaseModel):
    event: str
    message_id: Optional[str] = None
    platform: Optional[str] = None


@router.post("/free-answer-funnel/event")
async def record_free_answer_funnel_event(
    body: FreeAnswerFunnelEventBody,
    current_user: User = Depends(get_current_user),
):
    """Client breadcrumb: blur_shown | reveal_clicked (conversion is recorded on purchase)."""
    from credits.free_answer_funnel import record_funnel_event

    try:
        inserted = record_funnel_event(
            userid=int(current_user.userid),
            event_name=body.event,
            message_id=body.message_id,
            platform=body.platform,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("free_answer_funnel event failed user=%s", current_user.userid)
        raise HTTPException(status_code=500, detail="Failed to record funnel event") from e
    return {"ok": True, "inserted": inserted}


@router.get("/admin/free-answer-funnel")
async def admin_free_answer_funnel(
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    """Admin funnel: saw blur → tapped reveal → purchased credits."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from credits.free_answer_funnel import get_funnel_analytics

    try:
        return get_funnel_analytics(from_date=from_date, to_date=to_date)
    except Exception as e:
        logger.exception("free_answer_funnel analytics failed")
        raise HTTPException(status_code=500, detail="Failed to load free-answer funnel") from e


@router.post("/google-play/verify")
async def verify_google_play_purchase(
    request: GooglePlayVerifyRequest,
    current_user: User = Depends(get_current_user),
):
    """Verify a Google Play one-time purchase and grant credits idempotently by order_id."""
    proxied = _proxy_to_play_payment_service(
        path="/internal/google-play/verify",
        payload=request.model_dump(),
        current_user=current_user,
    )
    if proxied is not None:
        return proxied

    result = _credit_verified_google_play_purchase(
        userid=current_user.userid,
        user_phone=current_user.phone,
        user_name=current_user.name,
        purchase_token=request.purchase_token,
        product_id=(request.product_id or "").strip(),
        order_id_hint=(request.order_id or "").strip(),
        price_amount_micros=request.price_amount_micros,
        price_currency=request.price_currency,
        localized_price=request.localized_price,
    )
    try:
        pending_summary = _process_pending_google_play_onetime_events_for_token(
            userid=current_user.userid,
            purchase_token=request.purchase_token,
            product_id_hint=(request.product_id or "").strip() or None,
        )
        if pending_summary.get("found"):
            result["pending_rtdn_recovery"] = pending_summary
    except Exception:
        logger.exception(
            "Google Play verify succeeded but pending RTDN recovery failed user=%s product=%s",
            current_user.userid,
            (request.product_id or "").strip(),
        )
    return _mark_main_backend_fallback(
        result,
        path="/google-play/verify",
        current_user=current_user,
        order_id=(request.order_id or "").strip(),
    )


@router.post("/google-play/subscription/verify")
async def verify_google_play_subscription(
    request: GooglePlaySubscriptionVerifyRequest,
    current_user: User = Depends(get_current_user),
):
    """Verify a Google Play subscription and set user's tier (VIP Silver/Gold/Platinum). Idempotent: re-calling extends/updates end_date."""
    proxied = _proxy_to_play_payment_service(
        path="/internal/google-play/subscription/verify",
        payload=request.model_dump(),
        current_user=current_user,
    )
    if proxied is not None:
        return proxied

    if not (request.purchase_token or "").strip():
        raise HTTPException(status_code=400, detail="purchase_token is required")
    product_id = (request.product_id or "").strip()
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id is required")
    try:
        result = _sync_subscription_from_play(
            current_user.userid,
            product_id,
            request.purchase_token.strip(),
            accept_any_payment_state=False,
            event_source="verify",
            order_id_hint=(request.order_id or "").strip() or None,
        )
        return _mark_main_backend_fallback({
            "success": True,
            "message": "Subscription active",
            "subscription_tier_name": result["tier_name"],
            "end_date": result["end_date"],
        },
            path="/google-play/subscription/verify",
            current_user=current_user,
            order_id=(request.order_id or "").strip(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid or expired subscription: {str(e)}")
    # unreachable


def _subscription_order_id_from_purchase(purchase: dict, order_id_hint: Optional[str] = None) -> Optional[str]:
    """Resolve GPA order id from Play subscription verify payload or client hint."""
    from credits.play_order_id_util import normalize_play_order_id

    raw = (
        (purchase or {}).get("orderId")
        or (purchase or {}).get("latestOrderId")
        or order_id_hint
    )
    return normalize_play_order_id(raw)


def _infer_app_subscription_event_kind(
    prior: Optional[dict],
    plan_id: int,
    start_date: str,
    end_date: str,
) -> str:
    """Classify verify/sync updates for admin event log (not used for RTDN)."""
    if not prior:
        return "purchased"
    try:
        prior_plan = int(prior.get("plan_id"))
    except (TypeError, ValueError):
        prior_plan = None
    if prior_plan is not None and prior_plan != plan_id:
        return "upgraded"
    prior_end = (prior.get("end_date") or "")[:10]
    prior_start = (prior.get("start_date") or "")[:10]
    if prior_end and end_date and end_date > prior_end:
        return "renewed"
    if prior_start == start_date and prior_end == end_date:
        return "synced"
    return "updated"


def _log_app_subscription_event(
    *,
    userid: int,
    product_id: str,
    purchase_token: str,
    source: str,
    event_kind: str,
    start_date: str,
    end_date: str,
    google_play_order_id: Optional[str] = None,
) -> None:
    """Idempotent audit log for in-app verify/sync (distinct from RTDN event_id)."""
    eid = "|".join(
        [
            "app",
            (source or "sync").strip().lower(),
            str(userid),
            (product_id or "").strip(),
            start_date,
            end_date,
            (event_kind or "updated").strip().lower(),
        ]
    )
    credit_service.log_play_subscription_event(
        event_id=eid,
        purchase_token=purchase_token,
        product_id=product_id,
        userid=userid,
        source=source,
        event_kind=event_kind,
        start_date=start_date,
        end_date=end_date,
        google_play_order_id=google_play_order_id,
    )


def _sync_subscription_from_play(
    userid: int,
    product_id: str,
    purchase_token: str,
    *,
    accept_any_payment_state: bool = False,
    event_source: Optional[str] = None,
    order_id_hint: Optional[str] = None,
) -> dict:
    """Verify subscription with Google Play and update our DB. Used by both verify and sync.
    If accept_any_payment_state is True (sync), we update DB even when cancelled/expired so our record matches Play."""
    plan_id = credit_service.get_plan_id_by_google_play_product_id(product_id)
    if not plan_id:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown subscription product_id: {product_id}",
        )
    from db import get_conn, execute

    platform = "astroroshni"
    with get_conn() as conn:
        cur = execute(conn, "SELECT platform FROM subscription_plans WHERE plan_id = ?", (plan_id,))
        prow = cur.fetchone()
        if prow and prow[0]:
            platform = prow[0]
    prior = credit_service.get_latest_subscription_on_platform(userid, platform)

    purchase = _verify_google_play_subscription(PACKAGE_NAME, product_id, purchase_token)
    if not accept_any_payment_state:
        payment_state = purchase.get("paymentState")
        if payment_state not in (0, 1):
            raise HTTPException(status_code=400, detail="Subscription not in valid payment state")
    from datetime import datetime
    expiry_ms = purchase.get("expiryTimeMillis") or purchase.get("startTimeMillis") or 0
    start_ms = purchase.get("startTimeMillis") or expiry_ms
    start_date = datetime.utcfromtimestamp(int(start_ms) / 1000).strftime("%Y-%m-%d")
    # Google keeps cancelled subscriptions entitled until expiryTimeMillis.
    # userCancellationTimeMillis only means renewal is off, not that access ended.
    end_date = datetime.utcfromtimestamp(int(expiry_ms) / 1000).strftime("%Y-%m-%d")
    play_order_id = _subscription_order_id_from_purchase(purchase, order_id_hint)
    # Keep token->user mapping fresh so RTDN worker can resolve ownership.
    try:
        credit_service.upsert_play_subscription_token(
            userid, purchase_token, product_id, latest_order_id=play_order_id
        )
    except Exception:
        pass
    success = credit_service.set_user_subscription(
        userid,
        plan_id,
        start_date,
        end_date,
        google_play_order_id=play_order_id,
        billing_provider="google_play",
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update subscription")
    tier_name = credit_service.get_subscription_tier_name(userid)

    if event_source in ("verify", "sync"):
        kind = _infer_app_subscription_event_kind(prior, plan_id, start_date, end_date)
        _log_app_subscription_event(
            userid=userid,
            product_id=product_id,
            purchase_token=purchase_token,
            source=event_source,
            event_kind=kind,
            start_date=start_date,
            end_date=end_date,
            google_play_order_id=play_order_id,
        )

    return {
        "tier_name": tier_name or product_id,
        "end_date": end_date,
        "start_date": start_date,
        "google_play_order_id": play_order_id,
    }


def _extract_rtdn_payload_from_pubsub_push(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pub/Sub push body format:
    {
      "message": {"data": "<base64-json>", "messageId": "...", ...},
      "subscription": "..."
    }
    """
    if not isinstance(body, dict):
        return {}
    msg = body.get("message")
    if not isinstance(msg, dict):
        return {}
    data_b64 = str(msg.get("data") or "").strip()
    if not data_b64:
        return {}
    try:
        raw = base64.b64decode(data_b64)
        parsed = json.loads(raw.decode("utf-8"))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


@router.post("/google-play/subscription/sync")
async def sync_google_play_subscription(
    request: GooglePlaySubscriptionVerifyRequest,
    current_user: User = Depends(get_current_user),
):
    """Re-verify subscription with Google Play and update our DB. Call this when the app opens or user visits Credits
    so we stay in sync if they changed/cancelled/renewed on Play. Accepts any payment state so we can update end_date."""
    proxied = _proxy_to_play_payment_service(
        path="/internal/google-play/subscription/sync",
        payload=request.model_dump(),
        current_user=current_user,
    )
    if proxied is not None:
        return proxied

    if not (request.purchase_token or "").strip():
        raise HTTPException(status_code=400, detail="purchase_token is required")
    product_id = (request.product_id or "").strip()
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id is required")
    try:
        result = _sync_subscription_from_play(
            current_user.userid,
            product_id,
            request.purchase_token.strip(),
            accept_any_payment_state=True,
            event_source="sync",
            order_id_hint=(request.order_id or "").strip() or None,
        )
        return _mark_main_backend_fallback({
            "success": True,
            "message": "Subscription synced",
            "subscription_tier_name": result["tier_name"],
            "end_date": result["end_date"],
        },
            path="/google-play/subscription/sync",
            current_user=current_user,
            order_id=(request.order_id or "").strip(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not sync subscription: {str(e)}")


@router.post("/google-play/rtdn/push")
async def google_play_rtdn_push(body: Dict[str, Any]):
    """
    Pub/Sub push endpoint for Google Play RTDN events.
    Returns 200 only after we have either processed the event or recorded it
    durably enough to retry later. If we cannot make durable progress, return a
    non-2xx so Pub/Sub retries delivery.
    """
    msg = body.get("message") if isinstance(body, dict) else None
    message_id = str((msg or {}).get("messageId") or (msg or {}).get("message_id") or "").strip()
    payload = _extract_rtdn_payload_from_pubsub_push(body)
    if not payload:
        logger.warning("RTDN push: invalid payload envelope (message_id=%s)", message_id or "n/a")
        return {"success": True, "ignored": "invalid_payload"}

    if isinstance(payload.get("testNotification"), dict):
        logger.info("RTDN push: test notification received (message_id=%s)", message_id or "n/a")
        return {"success": True, "test": True}

    sub_notif = payload.get("subscriptionNotification")
    if isinstance(sub_notif, dict):
        purchase_token = str(sub_notif.get("purchaseToken") or "").strip()
        product_id = str(sub_notif.get("subscriptionId") or "").strip()
        notification_type = sub_notif.get("notificationType")
        event_time_millis = payload.get("eventTimeMillis")

        if not purchase_token or not product_id:
            logger.warning("RTDN push: missing token/product (message_id=%s)", message_id or "n/a")
            return {"success": True, "ignored": "missing_token_or_product"}

        event_id = "|".join(
            [
                "sub",
                purchase_token,
                product_id,
                str(notification_type or ""),
                str(event_time_millis or ""),
                message_id or "",
            ]
        )
        if credit_service.has_processed_play_subscription_event(event_id):
            return {"success": True, "duplicate": True}

        userid = credit_service.get_user_id_by_play_purchase_token(purchase_token)
        if userid is None:
            logger.warning(
                "RTDN push: unknown subscription token; ignoring (product=%s message_id=%s)",
                product_id,
                message_id or "n/a",
            )
            return {"success": True, "ignored": "unknown_purchase_token"}

        from credits.play_subscription_events import rtdn_kind_for_notification_type

        sync_result = _sync_subscription_from_play(
            userid=userid,
            product_id=product_id,
            purchase_token=purchase_token,
            accept_any_payment_state=True,
        )
        if not credit_service.log_play_subscription_event(
            event_id=event_id,
            purchase_token=purchase_token,
            product_id=product_id,
            notification_type=int(notification_type) if notification_type is not None else None,
            event_time_millis=int(event_time_millis) if event_time_millis is not None else None,
            payload_json=json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
            userid=userid,
            source="rtdn",
            event_kind=rtdn_kind_for_notification_type(notification_type),
            start_date=sync_result.get("start_date"),
            end_date=sync_result.get("end_date"),
            google_play_order_id=sync_result.get("google_play_order_id"),
        ):
            raise HTTPException(status_code=503, detail="Failed to log subscription RTDN event")
        return {"success": True}

    onetime_notif = payload.get("oneTimeProductNotification")
    if isinstance(onetime_notif, dict):
        purchase_token = str(onetime_notif.get("purchaseToken") or "").strip()
        product_id = str(
            onetime_notif.get("sku")
            or onetime_notif.get("productId")
            or ""
        ).strip()
        notification_type = onetime_notif.get("notificationType")
        event_time_millis = payload.get("eventTimeMillis")
        if not purchase_token or not product_id:
            logger.warning("RTDN push: one-time event missing token/product (message_id=%s)", message_id or "n/a")
            return {"success": True, "ignored": "missing_token_or_product"}

        event_id = "|".join(
            [
                "one",
                purchase_token,
                product_id,
                str(notification_type or ""),
                str(event_time_millis or ""),
                message_id or "",
            ]
        )
        if credit_service.has_processed_play_onetime_event(event_id):
            return {"success": True, "duplicate": True}

        userid = credit_service.get_user_id_by_play_onetime_purchase_token(purchase_token)
        if userid is None:
            userid = _resolve_userid_from_google_play_onetime_purchase(
                purchase_token=purchase_token,
                product_id=product_id,
            )
            if userid is not None:
                try:
                    credit_service.upsert_play_onetime_token(userid, purchase_token, product_id)
                except Exception:
                    pass
        if userid is None:
            queued = credit_service.enqueue_pending_play_onetime_event(
                event_id=event_id,
                purchase_token=purchase_token,
                product_id=product_id,
                notification_type=int(notification_type) if notification_type is not None else None,
                event_time_millis=int(event_time_millis) if event_time_millis is not None else None,
                payload_json=json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
                resolution_note="waiting_for_token_mapping",
            )
            if not queued:
                raise HTTPException(status_code=503, detail="Failed to queue unresolved one-time RTDN event")
            logger.warning(
                "RTDN push: unknown one-time token; queued for retry (product=%s message_id=%s)",
                product_id,
                message_id or "n/a",
            )
            return {"success": True, "queued": "unknown_purchase_token"}

        _credit_verified_google_play_purchase(
            userid=userid,
            user_phone=None,
            user_name=None,
            purchase_token=purchase_token,
            product_id=product_id,
            order_id_hint=None,
        )
        if not credit_service.log_play_onetime_event(
            event_id=event_id,
            purchase_token=purchase_token,
            product_id=product_id,
            notification_type=int(notification_type) if notification_type is not None else None,
            event_time_millis=int(event_time_millis) if event_time_millis is not None else None,
            payload_json=json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
        ):
            raise HTTPException(status_code=503, detail="Failed to log one-time RTDN event")
        credit_service.resolve_pending_play_onetime_event(
            event_id,
            userid=userid,
            status="resolved",
            resolution_note="processed_from_rtdn",
        )
        return {"success": True}

    logger.info("RTDN push: unsupported event type ignored (message_id=%s)", message_id or "n/a")
    return {"success": True, "ignored": "unsupported_event"}


@router.post("/google-play/subscription/clear")
async def clear_subscription_no_purchase(current_user: User = Depends(get_current_user)):
    """Backward-compatible endpoint for older apps that call clear when Play returns no token.
    Do not expire future-dated subscriptions here; cancelled users keep benefits until end_date.
    """
    try:
        updated = credit_service.expire_user_subscription_for_platform(current_user.userid, "astroroshni")
        return {"success": True, "cleared": updated, "message": "Subscription status updated." if updated else "No active subscription to clear."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google-play/subscription-plans")
async def get_google_play_subscription_plans(current_user: User = Depends(get_current_user)):
    """List VIP subscription plans available for in-app purchase (platform=astroroshni, with google_play_product_id). For mobile to show and purchase."""
    with get_conn() as conn:
        try:
            cur = execute(
                conn,
                f"""
                SELECT plan_id, tier_name, discount_percent, google_play_product_id, price, features
                FROM subscription_plans
                WHERE platform = %s
                  AND {SQL_SUBSCRIPTION_PLAN_ACTIVE}
                  AND google_play_product_id IS NOT NULL
                  AND google_play_product_id != ''
                ORDER BY COALESCE(discount_percent, 0) ASC
                """,
                ("astroroshni",),
            )
            rows = cur.fetchall()
        except Exception as e:
            # First query failed (e.g. missing columns). Postgres aborts the transaction — must rollback
            # before running the fallback query on the same connection.
            logger.warning(
                "subscription-plans primary query failed, using legacy columns: %s",
                e,
            )
            try:
                conn.rollback()
            except Exception:
                pass
            cur = execute(
                conn,
                f"""
                SELECT plan_id, plan_name, 0, NULL, price, features
                FROM subscription_plans
                WHERE platform = %s
                  AND {SQL_SUBSCRIPTION_PLAN_ACTIVE}
                ORDER BY plan_name
                """,
                ("astroroshni",),
            )
            rows = [(r[0], r[1], 0, None, r[4], r[5]) for r in cur.fetchall()]
    plans = []
    for r in rows:
        plan_id, name, discount, product_id, price, features_raw = r[0], r[1], r[2] or 0, r[3], float(r[4]) if r[4] is not None else 0, r[5]
        if not product_id:
            continue
        # Fetch live price from Google Play so app shows same price as Play Store
        formatted_price = _get_subscription_price_from_play(PACKAGE_NAME, product_id)
        features = None
        benefits = []
        if features_raw is not None:
            features = str(features_raw)
            try:
                parsed = json.loads(features)
                if isinstance(parsed, list):
                    benefits = [str(x).strip() for x in parsed if str(x).strip()]
                elif isinstance(parsed, dict):
                    arr = parsed.get("benefits")
                    if isinstance(arr, list):
                        benefits = [str(x).strip() for x in arr if str(x).strip()]
            except Exception:
                lines = [ln.strip("- \t\r\n") for ln in str(features_raw).splitlines()]
                benefits = [ln for ln in lines if ln]
        plans.append({
            "plan_id": plan_id,
            "tier_name": name or f"Plan {plan_id}",
            "discount_percent": discount,
            "google_play_product_id": product_id,
            "price": price,
            "formatted_price": formatted_price,
            "features": features,
            "benefits": benefits,
        })
    return {"plans": plans}


class WebNotificationOptInRequest(BaseModel):
    """Set when the browser reports notification permission granted (honor-system for web free-first-question)."""
    granted: bool = True


@router.post("/web-notification-opt-in")
async def web_notification_opt_in(
    body: WebNotificationOptInRequest,
    current_user: User = Depends(get_current_user),
):
    credit_service.set_web_notifications_granted(current_user.userid, bool(body.granted))
    return {"ok": True}


@router.get("/balance")
async def get_credit_balance(current_user: User = Depends(get_current_user)):
    balance = credit_service.get_user_credits(current_user.userid)
    free_used = credit_service.get_free_chat_question_used(current_user.userid)
    free_ok = credit_service.is_free_standard_chat_question_available(current_user.userid)
    pending_notif = credit_service.free_question_pending_notification_opt_in(current_user.userid)
    result = {
        "credits": balance,
        "free_question_available": free_ok,
        "free_question_requires_notifications": pending_notif,
    }
    try:
        result["is_guru_member"] = credit_service.user_is_guru_member(current_user.userid)
    except Exception:
        result["is_guru_member"] = False
    try:
        result["first_purchase_bonus"] = credit_service.get_first_purchase_bonus_status(current_user.userid)
    except Exception:
        pass
    try:
        result["purchase_discount"] = credit_service.get_purchase_discount_status(current_user.userid)
    except Exception:
        pass
    # Optional: subscription tier for app to show "VIP Silver" etc. (backward compat: new keys)
    try:
        discount = credit_service.get_subscription_discount_percent(current_user.userid)
        if discount > 0:
            result["subscription_discount_percent"] = discount
            tier = credit_service.get_subscription_tier_name(current_user.userid)
            if tier:
                result["subscription_tier_name"] = tier
    except Exception:
        pass
    return result


@router.get("/subscription")
async def get_subscription_details(current_user: User = Depends(get_current_user)):
    """Return full subscription details for the current user: tier_name, discount_percent, start_date, end_date (renewal), features. None if no active subscription."""
    try:
        details = credit_service.get_user_subscription_details(current_user.userid)
        if details is None:
            return {"subscription": None}
        return {"subscription": details}
    except Exception:
        return {"subscription": None}

@router.get("/history")
async def get_credit_history(current_user: User = Depends(get_current_user)):
    transactions = credit_service.get_transaction_history(current_user.userid)
    return {"transactions": transactions}

@router.post("/redeem")
async def redeem_promo_code(request: PromoCodeRequest, current_user: User = Depends(get_current_user)):
    code = request.code.strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Promo code is required")
    
    result = credit_service.redeem_promo_code(current_user.userid, code)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.post("/spend")
async def spend_credits(request: dict, current_user: User = Depends(get_current_user)):
    """Deduct credits for a feature. Amount must match the user's effective cost (VIP discount applied).
    App should send the same amount returned by GET /credits/settings/my-pricing for that feature."""
    amount = request.get("amount")
    feature = request.get("feature")
    description = request.get("description")
    
    if not amount or not feature:
        raise HTTPException(status_code=400, detail="Amount and feature are required")
    
    success = credit_service.spend_credits(current_user.userid, amount, feature, description)
    
    if not success:
        raise HTTPException(status_code=400, detail="Insufficient credits")
    
    return {"success": True, "message": f"Successfully spent {amount} credits"}


@router.post("/speech-session/start")
async def start_speech_billing_session(current_user: User = Depends(get_current_user)):
    """Start a live speech billing session.

    Requires at least 5 minutes worth of the user's discounted per-minute price in wallet.
    Actual deduction happens when /speech-session/end is called.
    """
    base_cost = int(credit_service.get_credit_setting("speech_chat_per_minute_cost") or 1)
    per_minute_cost = int(
        credit_service.get_effective_cost(
            current_user.userid,
            base_cost,
            "speech_chat_per_minute_cost",
        )
        or base_cost
    )
    per_minute_cost = max(1, per_minute_cost)
    original_cost = int(credit_service.get_credit_setting_and_original("speech_chat_per_minute_cost")[1] or base_cost)
    discount_percent = int(credit_service.get_subscription_discount_percent(current_user.userid) or 0)
    required_start_credits = per_minute_cost * SPEECH_BILLING_MIN_START_MINUTES
    balance = int(credit_service.get_user_credits(current_user.userid) or 0)
    if balance < required_start_credits:
        raise HTTPException(
            status_code=402,
            detail={
                "message": (
                    f"Speech chat requires at least {required_start_credits} credits "
                    f"for {SPEECH_BILLING_MIN_START_MINUTES} minutes."
                ),
                "required_credits": required_start_credits,
                "balance": balance,
                "per_minute_cost": per_minute_cost,
                "minimum_minutes": SPEECH_BILLING_MIN_START_MINUTES,
            },
        )

    billing_session_id = f"speech_{uuid.uuid4().hex}"
    with get_conn() as conn:
        _ensure_speech_billing_table(conn)
        execute(
            conn,
            """
            INSERT INTO speech_billing_sessions (
                session_id, userid, per_minute_cost, original_per_minute_cost,
                discount_percent, required_start_credits, starting_balance
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                billing_session_id,
                current_user.userid,
                per_minute_cost,
                original_cost,
                discount_percent,
                required_start_credits,
                balance,
            ),
        )
        conn.commit()

    max_seconds = int((balance // per_minute_cost) * 60)
    warning_after_seconds = max(0, max_seconds - 60)
    return {
        "session_id": billing_session_id,
        "started_at": _iso_utc_now(),
        "balance": balance,
        "per_minute_cost": per_minute_cost,
        "original_per_minute_cost": original_cost,
        "subscription_discount_percent": discount_percent,
        "required_start_credits": required_start_credits,
        "minimum_minutes": SPEECH_BILLING_MIN_START_MINUTES,
        "max_seconds": max_seconds,
        "warning_after_seconds": warning_after_seconds,
        "warning_interval_seconds": 10,
    }


@router.get("/speech-session/{session_id}/status")
async def get_speech_billing_session_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    with get_conn() as conn:
        _ensure_speech_billing_table(conn)
        cur = execute(
            conn,
            """
            SELECT session_id, userid, status, per_minute_cost, charged_credits,
                   elapsed_seconds, started_at, ended_at
            FROM speech_billing_sessions
            WHERE session_id = ? AND userid = ?
            """,
            (session_id, current_user.userid),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Speech billing session not found")
    return {
        "session_id": row[0],
        "status": row[2],
        "per_minute_cost": int(row[3] or 0),
        "charged_credits": int(row[4] or 0),
        "elapsed_seconds": int(row[5] or 0),
        "started_at": str(row[6]) if row[6] is not None else None,
        "ended_at": str(row[7]) if row[7] is not None else None,
    }


@router.post("/speech-session/{session_id}/end")
async def end_speech_billing_session(
    session_id: str,
    request: dict,
    current_user: User = Depends(get_current_user),
):
    reason = str((request or {}).get("reason") or "ended").strip()[:80] or "ended"
    with get_conn() as conn:
        _ensure_speech_billing_table(conn)
        cur = execute(
            conn,
            """
            SELECT session_id, userid, status, per_minute_cost,
                   EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at))::INTEGER AS elapsed_seconds
            FROM speech_billing_sessions
            WHERE session_id = ? AND userid = ?
            FOR UPDATE
            """,
            (session_id, current_user.userid),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Speech billing session not found")

        status = str(row[2] or "")
        if status != "active":
            cur = execute(
                conn,
                """
                SELECT charged_credits, elapsed_seconds, per_minute_cost
                FROM speech_billing_sessions
                WHERE session_id = ? AND userid = ?
                """,
                (session_id, current_user.userid),
            )
            existing = cur.fetchone()
            return {
                "success": True,
                "already_ended": True,
                "session_id": session_id,
                "charged_credits": int(existing[0] or 0) if existing else 0,
                "elapsed_seconds": int(existing[1] or 0) if existing else 0,
                "per_minute_cost": int(existing[2] or 0) if existing else 0,
            }

        per_minute_cost = max(1, int(row[3] or 1))
        elapsed_seconds = max(1, int(row[4] or 1))
        minutes = _speech_minutes_from_seconds(elapsed_seconds)
        charge = max(1, minutes * per_minute_cost)
        balance = int(credit_service.get_user_credits(current_user.userid, conn=conn) or 0)
        charge = min(charge, balance)
        new_balance = balance - charge
        execute(
            conn,
            "UPDATE user_credits SET credits = ?, updated_at = CURRENT_TIMESTAMP WHERE userid = ?",
            (new_balance, current_user.userid),
        )
        execute(
            conn,
            """
            INSERT INTO credit_transactions
            (userid, transaction_type, amount, balance_after, source, reference_id, description)
            VALUES (?, 'spent', ?, ?, 'feature_usage', 'speech_chat_minutes', ?)
            """,
            (
                current_user.userid,
                -charge,
                new_balance,
                f"Speech chat call: {minutes} minute(s), {elapsed_seconds}s ({reason})",
            ),
        )
        execute(
            conn,
            """
            UPDATE speech_billing_sessions
            SET status = 'ended',
                ended_at = CURRENT_TIMESTAMP,
                elapsed_seconds = ?,
                charged_credits = ?,
                ended_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ? AND userid = ?
            """,
            (elapsed_seconds, charge, reason, session_id, current_user.userid),
        )
        conn.commit()

    return {
        "success": True,
        "session_id": session_id,
        "elapsed_seconds": elapsed_seconds,
        "billed_minutes": minutes,
        "per_minute_cost": per_minute_cost,
        "charged_credits": charge,
        "balance_after": new_balance,
    }

# Admin endpoints
@router.get("/admin/credit-products")
async def admin_list_credit_products(current_user: User = Depends(get_current_user)):
    """List all credit packs (Google Play + Razorpay) with visibility flags.

    First call creates `credit_product_catalog` and seeds the default packs if missing.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        products = credit_service.list_credit_products(active_only=False)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load/initialize credit_product_catalog: {e}",
        ) from e
    return {"products": products}


@router.post("/admin/credit-products/seed")
async def admin_seed_credit_products(current_user: User = Depends(get_current_user)):
    """Force-create + seed default credit packs (idempotent)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        credit_service._ensure_credit_product_catalog()
        products = credit_service.list_credit_products(active_only=False)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to seed credit_product_catalog: {e}",
        ) from e
    return {"message": "Credit product catalog ready", "products": products}


@router.put("/admin/credit-products/{product_id}")
async def admin_update_credit_product(
    product_id: str,
    request: UpdateCreditProductRequest,
    current_user: User = Depends(get_current_user),
):
    """Enable/disable a credit pack for both Google Play catalog and Razorpay."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    updated = credit_service.set_credit_product_active(product_id, request.is_active)
    if not updated:
        raise HTTPException(status_code=404, detail="Credit product not found")
    return {"message": "Credit product updated", "product": updated}


@router.post("/admin/promo-codes")
async def create_promo_code(request: CreatePromoCodeRequest, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        with get_conn() as conn:
            execute(
                conn,
                """
                INSERT INTO promo_codes (code, credits, max_uses, max_uses_per_user, expires_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    request.code.upper(),
                    request.credits,
                    request.max_uses,
                    request.max_uses_per_user,
                    request.expires_at,
                    current_user.userid,
                ),
            )
            conn.commit()
        return {"message": "Promo code created successfully"}
    except Exception:
        # Most likely a uniqueness violation on code
        raise HTTPException(status_code=400, detail="Promo code already exists")

@router.get("/admin/promo-codes")
async def get_promo_codes(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT code, credits, max_uses, max_uses_per_user, used_count, is_active, expires_at, created_at
            FROM promo_codes
            ORDER BY created_at DESC
            """,
        )
        rows = cur.fetchall()

    codes = []
    for row in rows:
        codes.append({
            "code": row[0],
            "credits": row[1],
            "max_uses": row[2],
            "max_uses_per_user": row[3],
            "used_count": row[4],
            "is_active": row[5],
            "expires_at": row[6],
            "created_at": row[7],
        })
    return {"promo_codes": codes}

@router.put("/admin/promo-codes/{code}")
async def update_promo_code(code: str, request: UpdatePromoCodeRequest, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    with get_conn() as conn:
        cur = execute(
            conn,
            """
            UPDATE promo_codes
            SET credits = %s, max_uses = %s, max_uses_per_user = %s, is_active = %s
            WHERE code = %s
            """,
            (request.credits, request.max_uses, request.max_uses_per_user, request.is_active, code.upper()),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Promo code not found")
        conn.commit()

    return {"message": "Promo code updated successfully"}

@router.delete("/admin/promo-codes/{code}")
async def delete_promo_code(code: str, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    with get_conn() as conn:
        cur = execute(
            conn,
            "DELETE FROM promo_codes WHERE code = %s",
            (code.upper(),),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Promo code not found")
        conn.commit()

    return {"message": "Promo code deleted successfully"}

@router.post("/admin/delete-promo-code")
async def delete_promo_code_post(request: dict, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    code = request.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Promo code is required")

    with get_conn() as conn:
        cur = execute(
            conn,
            "DELETE FROM promo_codes WHERE code = %s",
            (code.upper(),),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Promo code not found")
        conn.commit()

    return {"message": "Promo code deleted successfully"}

@router.post("/admin/add-credits")
async def admin_add_credits(request: dict, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    userid = request.get("userid")
    amount = request.get("amount")
    description = request.get("description", "Admin credit adjustment")
    
    if not userid or not amount:
        raise HTTPException(status_code=400, detail="User ID and amount are required")
    
    success = credit_service.add_credits(userid, amount, 'admin_adjustment', None, description)
    
    if success:
        return {"message": f"Successfully added {amount} credits to user {userid}"}
    else:
        raise HTTPException(status_code=400, detail="Failed to add credits")


@router.post("/admin/adjust-credits")
async def admin_adjust_credits(request: dict, current_user: User = Depends(get_current_user)):
    """Add or remove credits (amount positive = add, negative = remove). Partial credits allowed."""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    userid = request.get("userid")
    amount = request.get("amount")
    description = request.get("description", "").strip() or "Admin adjustment"
    if userid is None:
        raise HTTPException(status_code=400, detail="userid is required")
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="amount must be an integer")
    if amount == 0:
        raise HTTPException(status_code=400, detail="amount must be non-zero")
    success = credit_service.admin_adjust_credits(userid, amount, description)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Adjustment failed (e.g. not enough credits to deduct)",
        )
    action = "added" if amount > 0 else "removed"
    return {"message": f"Successfully {action} {abs(amount)} credits for user {userid}"}


@router.post("/admin/refund-credits")
async def admin_refund_credits(request: AdminRefundRequest, current_user: User = Depends(get_current_user)):
    """
    Admin refund of credits to a user, linked to an original transaction.
    This adds credits back (full or partial) and records a 'refund' transaction.
    """
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Refund amount must be positive")

    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT userid, amount, source, reference_id, description
            FROM credit_transactions
            WHERE id = %s
            """,
            (request.transaction_id,),
        )
        row = cur.fetchone()

    if not row or row[0] != request.userid:
        raise HTTPException(status_code=404, detail="Original transaction not found for this user")

    original_amount = row[1]
    source = row[2]
    reference_id = row[3]

    if abs(request.amount) > abs(original_amount):
        raise HTTPException(status_code=400, detail="Refund amount cannot exceed original transaction amount")

    comment_parts = [f"Admin refund of {request.amount} credits for tx #{request.transaction_id}"]
    if request.comment:
        comment_parts.append(request.comment)
    description = " - ".join(comment_parts)

    # Use reference_id as feature key for refund_credits
    feature_key = reference_id or source or "admin_refund"
    credit_service.refund_credits(request.userid, request.amount, feature_key, description)
    return {"message": "Refund applied", "credits_refunded": request.amount}


@router.post("/admin/reverse-google-play-purchase")
async def admin_reverse_google_play_purchase(request: dict, current_user: User = Depends(get_current_user)):
    """Reverse a Google Play credit grant after you have refunded the payment in Play Console. Deducts credits and records a reversal (idempotent per order)."""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    userid = request.get("userid")
    order_id = (request.get("order_id") or "").strip()
    amount = request.get("amount")
    reason = (request.get("reason") or "").strip() or None
    if not userid or not order_id:
        raise HTTPException(status_code=400, detail="userid and order_id are required")
    success, deduct_or_msg, _ = credit_service.reverse_google_play_purchase(userid, order_id, amount=amount, reason=reason)
    if success:
        return {"message": f"Reversed: {deduct_or_msg} credits deducted for order {order_id}", "credits_deducted": deduct_or_msg}
    raise HTTPException(status_code=400, detail=deduct_or_msg)


@router.post("/admin/google-play-refund")
async def admin_google_play_refund_full(request: dict, current_user: User = Depends(get_current_user)):
    """
    Single refund flow: (1) Refund on Google Play via API, (2) then deduct credits in our DB.
    Idempotent: if already reversed in DB, returns success without calling Google.
    Returns both statuses for UI: google_play, astroroshni, credits_deducted.
    """
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    userid = request.get("userid")
    order_id = (request.get("order_id") or "").strip()
    amount = request.get("amount")
    reason = (request.get("reason") or "").strip() or None
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id is required")
    if userid is None:
        raise HTTPException(status_code=400, detail="userid is required")
    userid = int(userid) if not isinstance(userid, int) else userid

    # Idempotent: already reversed in our DB -> return success without calling Google
    if credit_service.is_google_play_order_reversed(userid, order_id):
        return {
            "google_play": "Already refunded",
            "astroroshni": "Credits already taken back",
            "credits_deducted": 0,
        }

    # 1) Refund on Google Play
    gp_ok, gp_msg = _refund_google_play_order(PACKAGE_NAME, order_id)
    if not gp_ok:
        raise HTTPException(status_code=400, detail=f"Google Play: {gp_msg}")

    # 2) Deduct credits in our DB (atomic after Google success)
    ok, credits, original_amount = credit_service.reverse_google_play_purchase(userid, order_id, amount=amount, reason=reason)
    if not ok:
        raise HTTPException(
            status_code=500,
            detail="Google Play refund succeeded but AstroRoshni credit reversal failed. Please retry or reverse manually.",
        )
    return {
        "google_play": gp_msg,
        "astroroshni": "Credits taken back",
        "credits_deducted": credits,
        "original_amount": original_amount,
    }


@router.post("/admin/reverse-razorpay-purchase")
async def admin_reverse_razorpay_purchase(request: dict, current_user: User = Depends(get_current_user)):
    """
    Take back credits after you refunded the payment in Razorpay Dashboard (no Razorpay API call).
    Idempotent per payment id.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    userid = request.get("userid")
    payment_id = (request.get("payment_id") or "").strip()
    amount = request.get("amount")
    reason = (request.get("reason") or "").strip() or None
    if userid is None or not payment_id:
        raise HTTPException(status_code=400, detail="userid and payment_id are required")
    success, deduct_or_msg, _ = credit_service.reverse_razorpay_purchase(
        int(userid), payment_id, amount=amount, reason=reason
    )
    if success:
        return {
            "message": f"Reversed: {deduct_or_msg} credits deducted for payment {payment_id}",
            "credits_deducted": deduct_or_msg,
        }
    raise HTTPException(status_code=400, detail=deduct_or_msg)


@router.post("/admin/razorpay-refund")
async def admin_razorpay_refund(request: dict, current_user: User = Depends(get_current_user)):
    """
    Refund payment via Razorpay API, then deduct credits. Idempotent if credits already reversed.
    Partial credits: proportional INR refund in paise when metadata or payment fetch supplies amount.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    userid = request.get("userid")
    payment_id = (request.get("payment_id") or "").strip()
    amount = request.get("amount")
    reason = (request.get("reason") or "").strip() or None
    if userid is None:
        raise HTTPException(status_code=400, detail="userid is required")
    if not payment_id:
        raise HTTPException(status_code=400, detail="payment_id is required")
    userid = int(userid) if not isinstance(userid, int) else userid

    if credit_service.is_razorpay_payment_reversed(userid, payment_id):
        return {
            "razorpay": "Already refunded",
            "astroroshni": "Credits already taken back",
            "credits_deducted": 0,
        }

    snap = credit_service.get_razorpay_earned_snapshot(userid, payment_id)
    if not snap:
        raise HTTPException(status_code=400, detail="Payment not found or not a Razorpay credit transaction")

    original_credits = snap["credits"]
    try:
        credits_to_reverse = int(amount) if amount is not None else original_credits
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid amount")
    if credits_to_reverse < 1 or credits_to_reverse > original_credits:
        raise HTTPException(status_code=400, detail="Invalid credits amount (must be 1 to original pack size)")

    original_paise = snap.get("amount_paise")
    if original_paise is None or original_paise < 1:
        try:
            pay = fetch_razorpay_payment(payment_id)
            original_paise = int(pay.get("amount") or 0)
        except HTTPException:
            original_paise = None

    if credits_to_reverse < original_credits:
        if not original_paise or original_paise < 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot compute partial INR refund. Refund in Razorpay Dashboard, then use reverse-razorpay-purchase (credits only).",
            )
        refund_paise = max(1, int(round(original_paise * credits_to_reverse / original_credits)))
    else:
        refund_paise = None

    rp_ok, rp_msg, _ = refund_razorpay_payment(payment_id, refund_paise)
    if not rp_ok:
        raise HTTPException(status_code=400, detail=f"Razorpay: {rp_msg}")

    ok, credits_deducted_or_err, original_amount = credit_service.reverse_razorpay_purchase(
        userid, payment_id, amount=credits_to_reverse, reason=reason
    )
    if not ok:
        # Money may already be refunded on Razorpay; surface the real reason (e.g. no credits left).
        raise HTTPException(
            status_code=400,
            detail=(
                f"Razorpay refund ok, but credit reversal failed: {credits_deducted_or_err}. "
                "If money was refunded, use “Credits only” after the issue is fixed, or contact support."
            ),
        )
    return {
        "razorpay": rp_msg,
        "astroroshni": "Credits taken back",
        "credits_deducted": credits_deducted_or_err,
        "original_amount": original_amount,
    }


@router.get("/admin/settings")
async def get_credit_settings(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = credit_service.get_all_credit_settings()
    return {"settings": settings}

@router.put("/admin/settings")
async def update_credit_settings(request: dict, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = request.get("settings", [])
    updated_count = 0
    
    for setting in settings:
        key = setting.get("key")
        value = setting.get("value")
        if key and value is not None:
            discount = setting.get("discount")
            if "discount" in setting:
                if discount is not None and discount != "":
                    try:
                        d = int(discount)
                        success = credit_service.update_credit_setting(key, int(value), discount=d)
                    except (TypeError, ValueError):
                        success = credit_service.update_credit_setting(key, int(value), discount=None)
                else:
                    success = credit_service.update_credit_setting(key, int(value), discount=None)  # clear discount
            else:
                success = credit_service.update_credit_setting(key, int(value))  # leave discount unchanged
            if success:
                updated_count += 1
    
    return {"message": f"Updated {updated_count} settings"}

@router.get("/settings/chat-cost")
async def get_chat_cost():
    cost = credit_service.get_credit_setting('chat_question_cost')
    return {"cost": cost}

@router.get("/settings/wealth-cost")
async def get_wealth_cost():
    cost = credit_service.get_credit_setting('wealth_analysis_cost')
    return {"cost": cost}


@router.get("/settings/chart-guide-video-url")
async def get_chart_guide_video_url_public():
    return {"url": get_chart_guide_video_url()}


@router.get("/settings/nakshatra-guide-videos")
async def get_nakshatra_guide_videos_public():
    return {"videos": get_nakshatra_guide_videos()}

@router.get("/settings/marriage-cost")
async def get_marriage_cost():
    cost = credit_service.get_credit_setting('marriage_analysis_cost')
    return {"cost": cost}

@router.get("/settings/health-cost")
async def get_health_cost():
    cost = credit_service.get_credit_setting('health_analysis_cost')
    return {"cost": cost}

@router.get("/settings/education-cost")
async def get_education_cost():
    cost = credit_service.get_credit_setting('education_analysis_cost')
    return {"cost": cost}

@router.get("/settings/career-cost")
async def get_career_cost():
    cost = credit_service.get_credit_setting('career_analysis_cost')
    return {"cost": cost}

@router.get("/settings/progeny-cost")
async def get_progeny_cost():
    cost = credit_service.get_credit_setting('progeny_analysis_cost')
    return {"cost": cost}

def _get_pricing_with_originals():
    """Returns effective pricing and original (for display when discount set). Backward compatible."""
    keys_map = [
        ("chat", "chat_question_cost"),
        ("instant_chat", "instant_chat_cost"),
        ("speech_chat", "speech_chat_cost"),
        ("speech_chat_per_minute", "speech_chat_per_minute_cost"),
        ("premium_chat", "premium_chat_cost"),
        ("partnership", "partnership_analysis_cost"),
        ("events", "event_timeline_cost"),
        ("career", "career_analysis_cost"),
        ("wealth", "wealth_analysis_cost"),
        ("health", "health_analysis_cost"),
        ("marriage", "marriage_analysis_cost"),
        ("education", "education_analysis_cost"),
        ("progeny", "progeny_analysis_cost"),
        ("childbirth", "childbirth_planner_cost"),
        ("trading", "trading_daily_cost"),
        ("vehicle", "vehicle_purchase_cost"),
        ("griha_pravesh", "griha_pravesh_cost"),
        ("gold", "gold_purchase_cost"),
        ("business", "business_opening_cost"),
        ("karma", "karma_analysis_cost"),
        ("ashtakavarga", "ashtakavarga_life_predictions_cost"),
        ("podcast", "podcast_cost"),
    ]
    pricing = {}
    pricing_original = {}
    for short_key, setting_key in keys_map:
        effective, original, discount = credit_service.get_credit_setting_and_original(setting_key)
        pricing[short_key] = effective
        if discount is not None and discount >= 0 and original != discount:
            pricing_original[short_key] = original
    return pricing, pricing_original


def _safe_countdown_seconds(value, fallback: int) -> int:
    try:
        parsed = int(str(value).strip())
        return parsed if parsed > 0 else fallback
    except Exception:
        return fallback


def _get_chat_countdown_settings() -> Dict[str, int]:
    """Timer settings for chat loading countdown (mobile/web)."""
    try:
        from utils.admin_settings import get_setting
        standard_raw = get_setting("chat_countdown_standard_seconds")
        premium_raw = get_setting("chat_countdown_premium_seconds")
    except Exception:
        standard_raw = None
        premium_raw = None
    return {
        "standard": _safe_countdown_seconds(standard_raw, DEFAULT_STANDARD_CHAT_COUNTDOWN_SECONDS),
        "premium": _safe_countdown_seconds(premium_raw, DEFAULT_PREMIUM_CHAT_COUNTDOWN_SECONDS),
    }


@router.get("/settings/analysis-pricing")
async def get_analysis_pricing():
    """Same source as deduction: all analysis costs from credit_settings. pricing = effective; pricing_original = only when discount set (for strikethrough). Unauthenticated; base/admin pricing."""
    from utils.admin_settings import (
        is_instant_chat_enabled,
        is_speech_chat_enabled,
        get_speech_tts_provider,
        get_chat_static_suggestions,
    )
    pricing, pricing_original = _get_pricing_with_originals()
    result = {
        "pricing": pricing,
        "chat_countdown_seconds": _get_chat_countdown_settings(),
        "features": {
            "instant_chat_enabled": is_instant_chat_enabled(),
            "speech_chat_enabled": is_speech_chat_enabled(),
            "speech_tts_provider": get_speech_tts_provider(),
            "chat_static_suggestions": get_chat_static_suggestions(),
        },
    }
    if pricing_original:
        result["pricing_original"] = pricing_original
    return result


# Keys map for user-tier discounted pricing (same as _get_pricing_with_originals)
_PRICING_KEYS_MAP = [
    ("chat", "chat_question_cost"),
    ("instant_chat", "instant_chat_cost"),
    ("speech_chat", "speech_chat_cost"),
    ("speech_chat_per_minute", "speech_chat_per_minute_cost"),
    ("premium_chat", "premium_chat_cost"),
    ("partnership", "partnership_analysis_cost"),
    ("partnership_report", "partnership_report_cost"),
    ("events", "event_timeline_cost"),
    ("career", "career_analysis_cost"),
    ("career_report", "career_report_cost"),
    ("wealth", "wealth_analysis_cost"),
    ("wealth_report", "wealth_report_cost"),
    ("health", "health_analysis_cost"),
    ("health_report", "health_report_cost"),
    ("marriage", "marriage_analysis_cost"),
    ("education", "education_analysis_cost"),
    ("progeny", "progeny_analysis_cost"),
    ("progeny_report", "progeny_report_cost"),
    ("childbirth", "childbirth_planner_cost"),
    ("trading", "trading_daily_cost"),
    ("trading_monthly", "trading_monthly_cost"),
    ("vehicle", "vehicle_purchase_cost"),
    ("griha_pravesh", "griha_pravesh_cost"),
    ("gold", "gold_purchase_cost"),
    ("business", "business_opening_cost"),
    ("karma", "karma_analysis_cost"),
    ("ashtakavarga", "ashtakavarga_life_predictions_cost"),
    ("podcast", "podcast_cost"),
]


@router.get("/settings/my-pricing")
async def get_my_pricing(current_user: User = Depends(get_current_user)):
    """Authenticated: return user pricing quickly with one DB roundtrip for settings + one for subscription."""
    from utils.admin_settings import (
        instant_chat_enabled_for_user,
        speech_chat_enabled_for_user,
        get_speech_tts_provider,
        get_chat_static_suggestions,
    )
    pricing = {}
    pricing_original = {}
    discount_percent = 0
    tier_name = None

    # Avoid N× DB calls over high-latency links by bulk-fetching all settings once.
    settings_keys = [setting_key for _, setting_key in _PRICING_KEYS_MAP]
    with get_conn() as conn:
        # Active subscription (max discount) for this user.
        date_expr = credit_service._date_today_expr()
        cur = execute(
            conn,
            f"""
            SELECT COALESCE(sp.discount_percent, 0), sp.tier_name
            FROM user_subscriptions us
            JOIN subscription_plans sp ON us.plan_id = sp.plan_id
            WHERE us.userid = %s AND us.status = 'active' AND us.end_date >= {date_expr}
            ORDER BY sp.discount_percent DESC
            LIMIT 1
            """,
            (current_user.userid,),
        )
        row = cur.fetchone()
        if row:
            discount_percent = max(0, min(100, int(row[0]) if row[0] is not None else 0))
            tier_name = row[1] if len(row) > 1 else None

        # Fetch all credit settings in one query.
        placeholders = ", ".join(["%s"] * len(settings_keys))
        cur = execute(
            conn,
            f"""
            SELECT setting_key, setting_value, discount
            FROM credit_settings
            WHERE setting_key IN ({placeholders})
            """,
            tuple(settings_keys),
        )
        rows = cur.fetchall() or []

    settings_map = {
        r[0]: {"value": int(r[1]) if r[1] is not None else 1, "discount": r[2]}
        for r in rows
    }

    def _effective_from_setting(setting_key: str) -> tuple[int, int]:
        s = settings_map.get(setting_key)
        if not s:
            original = 1
            base_effective = 1
        else:
            original = int(s["value"])
            d = s["discount"]
            base_effective = int(d) if (d is not None and int(d) >= 0) else original
        if discount_percent > 0:
            effective = max(1, round(original * (100 - discount_percent) / 100))
        else:
            effective = base_effective
        return effective, original

    for short_key, setting_key in _PRICING_KEYS_MAP:
        effective, original_val = _effective_from_setting(setting_key)
        pricing[short_key] = effective
        if original_val is not None and effective < original_val:
            pricing_original[short_key] = original_val

    # Computed: trading premium daily/monthly from effective base costs.
    try:
        daily_effective, daily_original = _effective_from_setting("trading_daily_cost")
        premium_effective, premium_original = _effective_from_setting("premium_chat_cost")
        raw_effective = int(daily_effective) * int(premium_effective)
        raw_original = int(daily_original) * int(premium_original)
        pricing["trading_premium"] = raw_effective
        if raw_original > 0 and raw_effective < raw_original:
            pricing_original["trading_premium"] = raw_original
    except (TypeError, ValueError):
        pass

    try:
        monthly_effective, monthly_original = _effective_from_setting("trading_monthly_cost")
        premium_effective, premium_original = _effective_from_setting("premium_chat_cost")
        raw_effective = int(monthly_effective) * int(premium_effective)
        raw_original = int(monthly_original) * int(premium_original)
        pricing["trading_monthly_premium"] = raw_effective
        if raw_original > 0 and raw_effective < raw_original:
            pricing_original["trading_monthly_premium"] = raw_original
    except (TypeError, ValueError):
        pass

    result = {
        "pricing": pricing,
        "subscription_discount_percent": discount_percent,
        "chat_countdown_seconds": _get_chat_countdown_settings(),
        "features": {
            "instant_chat_enabled": instant_chat_enabled_for_user(current_user.userid),
            "speech_chat_enabled": speech_chat_enabled_for_user(current_user.userid),
            "speech_tts_provider": get_speech_tts_provider(),
            "chat_static_suggestions": get_chat_static_suggestions(),
        },
    }
    if tier_name:
        result["subscription_tier_name"] = tier_name
    if pricing_original:
        result["pricing_original"] = pricing_original
    return result

@router.get("/settings/premium-chat-cost")
async def get_premium_chat_cost():
    effective, original, discount = credit_service.get_credit_setting_and_original('premium_chat_cost')
    try:
        cost_int = int(effective)
        original_int = int(original)
    except (TypeError, ValueError):
        cost_int = effective if isinstance(effective, int) else 3
        original_int = original if isinstance(original, int) else None
    result = {"cost": cost_int}
    # Return original_cost when discount is set and original > cost so app can show strikethrough
    if discount is not None and discount >= 0 and original_int is not None and original_int > cost_int:
        result["original_cost"] = original_int
    return result

@router.get("/settings/partnership-cost")
async def get_partnership_cost():
    cost = credit_service.get_credit_setting('partnership_analysis_cost')
    return {"cost": cost}

@router.get("/settings/childbirth-cost")
async def get_childbirth_cost():
    cost = credit_service.get_credit_setting('childbirth_planner_cost')
    return {"cost": cost}

@router.get("/settings/vehicle-cost")
async def get_vehicle_cost():
    cost = credit_service.get_credit_setting('vehicle_purchase_cost')
    return {"cost": cost}

@router.get("/settings/griha-pravesh-cost")
async def get_griha_pravesh_cost():
    cost = credit_service.get_credit_setting('griha_pravesh_cost')
    return {"cost": cost}

@router.get("/settings/gold-cost")
async def get_gold_cost():
    cost = credit_service.get_credit_setting('gold_purchase_cost')
    return {"cost": cost}

@router.get("/settings/business-cost")
async def get_business_cost():
    cost = credit_service.get_credit_setting('business_opening_cost')
    return {"cost": cost}

@router.get("/settings/event-timeline-cost")
async def get_event_timeline_cost():
    effective, original, discount = credit_service.get_credit_setting_and_original('event_timeline_cost')
    result = {"cost": effective}
    if discount is not None and discount >= 0 and original != discount:
        result["original_cost"] = original
    return result

@router.get("/settings/karma-cost")
async def get_karma_cost():
    cost = credit_service.get_credit_setting('karma_analysis_cost')
    return {"cost": cost}

@router.get("/settings")
async def get_all_settings():
    """Get all credit settings for frontend use"""
    settings = credit_service.get_all_credit_settings()
    return settings

@router.post("/admin/bulk-promo-codes")
async def create_bulk_promo_codes(request: dict, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    prefix = request.get("prefix", "PROMO")
    count = request.get("count", 10)
    credits = request.get("credits", 100)
    max_uses = request.get("max_uses", 1)
    max_uses_per_user = request.get("max_uses_per_user", 1)
    expires_days = request.get("expires_days", 30)
    
    codes = promo_manager.create_bulk_codes(prefix, count, credits, max_uses, max_uses_per_user, expires_days)
    
    return {
        "message": f"Created {len(codes)} promo codes",
        "codes": codes
    }

@router.get("/admin/stats")
async def get_credit_stats(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        return promo_manager.get_usage_stats()
    except Exception as e:
        logger.exception("GET /admin/stats failed")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load credit stats: {e!s}",
        ) from e

@router.get("/admin/users")
async def get_all_users_with_credits(
    search: Optional[str] = None,
    with_credits_only: Optional[bool] = None,
    page: Optional[int] = 1,
    limit: Optional[int] = 50,
    current_user: User = Depends(get_current_user),
):
    """List users with credit balance. search: filter by name/phone; with_credits_only: only users with credits > 0; page/limit for pagination."""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    page = max(1, page or 1)
    limit = max(1, min(100, limit or 50))
    offset = (page - 1) * limit

    base = """
        FROM users u
        LEFT JOIN user_credits uc ON u.userid = uc.userid
        WHERE 1=1
    """
    params: list = []
    if search and search.strip():
        q = f"%{search.strip()}%"
        base += " AND (u.name ILIKE %s OR u.phone ILIKE %s)"
        params.extend([q, q])
    if with_credits_only:
        base += " AND COALESCE(uc.credits, 0) > 0"

    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT COUNT(*) " + base,
            tuple(params),
        )
        count_row = cur.fetchone()
        total = count_row[0] if count_row else 0

        cur = execute(
            conn,
            "SELECT u.userid, u.name, u.phone, COALESCE(uc.credits, 0) as credits "
            + base
            + " ORDER BY u.name LIMIT %s OFFSET %s",
            tuple(params + [limit, offset]),
        )
        rows = cur.fetchall()

    users = [
        {"userid": row[0], "name": row[1], "phone": row[2], "credits": row[3]}
        for row in rows
    ]
    return {"users": users, "total": total, "page": page, "limit": limit}

@router.get("/admin/user-history/{userid}")
async def get_user_transaction_history(
    userid: int,
    exclude_zero_amount: bool = Query(False),
    ledger_filter: Optional[str] = Query(
        None,
        description="Optional: purchases (earned+refund) or spend (spent only). Omit for full history.",
    ),
    limit: int = Query(50, ge=1, le=2000),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    lf = (ledger_filter or "").strip().lower() or None
    if lf is not None and lf not in ("purchases", "spend"):
        raise HTTPException(
            status_code=400,
            detail="ledger_filter must be 'purchases', 'spend', or omitted",
        )
    transactions = credit_service.get_transaction_history(
        userid,
        limit=limit,
        exclude_zero_amount=exclude_zero_amount,
        ledger_filter=lf,
    )
    return {"transactions": transactions}


@router.get("/admin/daily-activity")
async def get_daily_activity(
    date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Get all credit transactions for a given date (YYYY-MM-DD) across all users. Default: today."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from datetime import date as date_type
    target = date_type.today().isoformat() if not date else date
    transactions = credit_service.get_daily_activity(target)
    earned = sum(t["amount"] for t in transactions if t["type"] == "earned" or t["type"] == "refund")
    spent = sum(-t["amount"] for t in transactions if t["type"] == "spent")
    return {
        "date": target,
        "transactions": transactions,
        "summary": {"total_earned": earned, "total_spent": spent, "count": len(transactions)},
    }


@router.get("/admin/search")
async def search_credit_transactions(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    query: Optional[str] = None,
    exclude_zero_amount: bool = Query(False),
    buy_only: bool = Query(False),
    non_admin_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    cohort_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Search credit transactions across all users with optional date range (YYYY-MM-DD)
    and wildcard search on user name or phone. Paginated.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from datetime import date as date_type, timedelta
    today = date_type.today()

    # Default range: last 30 days
    if from_date and to_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = date_type.fromisoformat(to_date)
            if fd > td:
                fd, td = td, fd
        except ValueError:
            fd = today - timedelta(days=30)
            td = today
    else:
        fd = today - timedelta(days=30)
        td = today

    offset = (page - 1) * page_size
    summary = credit_service.get_search_transaction_summary(
        fd.isoformat(),
        td.isoformat(),
        query,
        exclude_zero_amount=exclude_zero_amount,
        cohort_filter=cohort_filter,
    )
    result = credit_service.search_transactions(
        fd.isoformat(),
        td.isoformat(),
        query,
        limit=page_size,
        offset=offset,
        exclude_zero_amount=exclude_zero_amount,
        cohort_filter=cohort_filter,
        buy_only=buy_only,
        non_admin_only=non_admin_only,
    )
    total = int(result.get("total") or 0)
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
    return {
        "from_date": fd.isoformat(),
        "to_date": td.isoformat(),
        "cohort_filter": cohort_filter,
        "summary": summary,
        "transactions": result.get("transactions") or [],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "buy_only": buy_only,
            "non_admin_only": non_admin_only,
        },
    }


@router.get("/admin/google-play-transactions")
async def get_google_play_transactions(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    query: Optional[str] = None,
    order_id: Optional[str] = None,
    currency: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    List Google Play purchases for the refund screen. Date range (YYYY-MM-DD), optional
    wildcard on user name/phone and order_id. Default range: last 30 days.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from datetime import date as date_type, timedelta
    today = date_type.today()
    # Default: last 2 years — Google Play credit purchases are infrequent; 30 days hid migrated/historical rows.
    default_start = today - timedelta(days=730)
    if from_date and to_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = date_type.fromisoformat(to_date)
            if fd > td:
                fd, td = td, fd
        except ValueError:
            fd = default_start
            td = today
    elif from_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = today
        except ValueError:
            fd = default_start
            td = today
    elif to_date:
        try:
            td = date_type.fromisoformat(to_date)
            fd = td - timedelta(days=730)
        except ValueError:
            fd = default_start
            td = today
    else:
        fd = default_start
        td = today
    transactions = credit_service.get_google_play_transactions(
        fd.isoformat(),
        td.isoformat(),
        query=query,
        order_id_filter=order_id,
        currency_filter=currency,
    )
    return {
        "from_date": fd.isoformat(),
        "to_date": td.isoformat(),
        "transactions": transactions,
    }


@router.get("/admin/razorpay-transactions")
async def get_razorpay_transactions(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    query: Optional[str] = None,
    payment_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """List Razorpay web credit purchases for the refund screen. Default range: last 730 days."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from datetime import date as date_type, timedelta

    today = date_type.today()
    default_start = today - timedelta(days=730)
    if from_date and to_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = date_type.fromisoformat(to_date)
            if fd > td:
                fd, td = td, fd
        except ValueError:
            fd = default_start
            td = today
    elif from_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = today
        except ValueError:
            fd = default_start
            td = today
    elif to_date:
        try:
            td = date_type.fromisoformat(to_date)
            fd = td - timedelta(days=730)
        except ValueError:
            fd = default_start
            td = today
    else:
        fd = default_start
        td = today
    transactions = credit_service.get_razorpay_transactions(
        fd.isoformat(),
        td.isoformat(),
        query=query,
        payment_id_filter=payment_id,
    )
    return {
        "from_date": fd.isoformat(),
        "to_date": td.isoformat(),
        "transactions": transactions,
    }


def _serialize_admin_subscription_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """JSON-friendly values for admin subscription purchase list."""
    from credits.play_order_id_util import play_order_id_base, play_order_renewal_index

    out: Dict[str, Any] = {}
    for key, val in row.items():
        if val is None:
            out[key] = None
        elif hasattr(val, "isoformat"):
            out[key] = val.isoformat()
        elif isinstance(val, (int, float, str, bool)):
            out[key] = val
        else:
            # Decimal etc.
            try:
                out[key] = float(val)
            except (TypeError, ValueError):
                out[key] = str(val)
    oid = out.get("google_play_order_id")
    out["order_id_base"] = play_order_id_base(oid)
    out["renewal_index"] = play_order_renewal_index(oid)
    return out


def _group_admin_subscription_purchases(purchases: List[Dict[str, Any]], *, limit: int) -> dict:
    """Group purchase rows by Play order_id_base (renewal family)."""
    from credits.play_order_id_util import play_order_sort_key

    groups_map: Dict[str, dict] = {}
    for row in purchases:
        base = row.get("order_id_base") or row.get("google_play_order_id") or (
            f"unknown-{row.get('userid')}-{row.get('google_play_product_id')}"
        )
        key = f"{row.get('userid')}|{row.get('google_play_product_id')}|{base}"
        if key not in groups_map:
            groups_map[key] = {
                "order_id_base": base,
                "userid": row.get("userid"),
                "user_name": row.get("user_name"),
                "user_phone": row.get("user_phone"),
                "google_play_product_id": row.get("google_play_product_id"),
                "plan_name": row.get("plan_name"),
                "tier_name": row.get("tier_name"),
                "purchases": [],
            }
        groups_map[key]["purchases"].append(row)

    groups = []
    for g in groups_map.values():
        g["purchases"].sort(
            key=lambda p: (
                play_order_sort_key(p.get("google_play_order_id")),
                p.get("start_date") or "",
            )
        )
        groups.append(g)
    groups.sort(
        key=lambda g: (
            (g.get("purchases") or [{}])[-1].get("start_date") or "",
            g.get("order_id_base") or "",
        ),
        reverse=True,
    )
    return {"total_groups": len(groups), "groups": groups[:limit]}


@router.get("/admin/subscription-purchases")
async def admin_subscription_purchases(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    query: Optional[str] = None,
    page: Optional[int] = 1,
    limit: Optional[int] = 50,
    grouped: Optional[bool] = False,
    current_user: User = Depends(get_current_user),
):
    """
    Paid subscription rows from user_subscriptions (excludes free plans).
    Filter by subscription start date (start_date), inclusive YYYY-MM-DD range.
    Optional wildcard on user name or phone.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from datetime import date as date_type, timedelta

    today = date_type.today()
    if from_date and to_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = date_type.fromisoformat(to_date)
            if fd > td:
                fd, td = td, fd
        except ValueError:
            fd = today - timedelta(days=30)
            td = today
    elif from_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = today
        except ValueError:
            fd = today - timedelta(days=30)
            td = today
    elif to_date:
        try:
            td = date_type.fromisoformat(to_date)
            fd = td - timedelta(days=30)
        except ValueError:
            fd = today - timedelta(days=30)
            td = today
    else:
        fd = today - timedelta(days=30)
        td = today

    page = max(1, page or 1)
    limit = max(1, min(200, limit or 50))
    offset = (page - 1) * limit
    use_grouped = bool(grouped)

    base_from = """
        FROM user_subscriptions us
        JOIN subscription_plans sp ON us.plan_id = sp.plan_id
        JOIN users u ON u.userid = us.userid
        WHERE DATE(us.start_date) >= %s AND DATE(us.start_date) <= %s
          AND (
            (sp.google_play_product_id IS NOT NULL AND TRIM(sp.google_play_product_id) <> '')
            OR COALESCE(sp.price, 0) > 0
          )
    """
    params: List[Any] = [fd.isoformat(), td.isoformat()]
    if query and query.strip():
        q = f"%{query.strip()}%"
        base_from += " AND (u.name ILIKE %s OR u.phone ILIKE %s)"
        params.extend([q, q])

    dedup_cte = (
        """
        WITH ranked AS (
            SELECT us.id AS row_id,
                   us.id AS subscription_id,
                   us.userid,
                   u.name AS user_name,
                   u.phone AS user_phone,
                   sp.platform,
                   sp.plan_name,
                   sp.tier_name,
                   sp.google_play_product_id,
                   sp.price AS plan_price,
                   sp.discount_percent AS plan_discount_percent,
                   us.status,
                   us.start_date,
                   us.end_date,
                   us.google_play_order_id,
                   us.created_at AS recorded_at,
                   CASE
                       WHEN us.status = 'active' AND us.end_date >= CURRENT_DATE THEN TRUE
                       ELSE FALSE
                   END AS is_current,
                   CASE
                       WHEN us.status <> 'active' AND us.end_date < CURRENT_DATE THEN us.end_date
                       WHEN us.status <> 'active' THEN us.created_at
                       ELSE NULL
                   END AS cancelled_or_ended_at_estimate,
                   CASE
                       WHEN us.status = 'active' AND us.end_date >= CURRENT_DATE THEN 'current_active'
                       WHEN us.status <> 'active'
                            AND EXISTS (
                                SELECT 1
                                FROM user_subscriptions us2
                                JOIN subscription_plans sp2 ON sp2.plan_id = us2.plan_id
                                WHERE us2.userid = us.userid
                                  AND sp2.platform = sp.platform
                                  AND us2.status = 'active'
                                  AND us2.end_date >= CURRENT_DATE
                            ) THEN 'inactive_superseded'
                       WHEN us.status <> 'active' AND us.end_date < CURRENT_DATE THEN 'inactive_ended'
                       WHEN us.status <> 'active' THEN 'inactive_unknown'
                       ELSE 'active_not_current'
                   END AS lifecycle_state,
                   ROW_NUMBER() OVER (
                       PARTITION BY us.userid, us.plan_id, DATE(us.start_date), DATE(us.end_date)
                       ORDER BY us.created_at DESC NULLS LAST, us.id DESC
                   ) AS rn
        """
        + base_from
        + """
        )
        """
    )

    select_sql = (
        dedup_cte
        + """
        SELECT row_id, subscription_id, userid, user_name, user_phone, platform,
               plan_name, tier_name, google_play_product_id, plan_price,
               plan_discount_percent, status, start_date, end_date, google_play_order_id,
               recorded_at, is_current, cancelled_or_ended_at_estimate, lifecycle_state
        FROM ranked
        WHERE rn = 1
        ORDER BY start_date DESC, row_id DESC
        LIMIT %s OFFSET %s
        """
    )

    count_sql = dedup_cte + "SELECT COUNT(*) FROM ranked WHERE rn = 1"
    flat_select_sql = (
        dedup_cte
        + """
        SELECT row_id, subscription_id, userid, user_name, user_phone, platform,
               plan_name, tier_name, google_play_product_id, plan_price,
               plan_discount_percent, status, start_date, end_date, google_play_order_id,
               recorded_at, is_current, cancelled_or_ended_at_estimate, lifecycle_state
        FROM ranked
        WHERE rn = 1
        ORDER BY start_date DESC, row_id DESC
        """
    )

    try:
        with get_conn() as conn:
            cur = execute(conn, count_sql, tuple(params))
            count_row = cur.fetchone()
            total = int(count_row[0]) if count_row and count_row[0] is not None else 0

            if use_grouped:
                cur = execute(conn, flat_select_sql, tuple(params))
            else:
                cur = execute(conn, select_sql, tuple(params + [limit, offset]))
            colnames = [d[0] for d in (cur.description or [])]
            raw_rows = cur.fetchall() or []
            purchases = [
                _serialize_admin_subscription_row(dict(zip(colnames, r)))
                for r in raw_rows
            ]
    except Exception as e:
        logger.exception("GET /admin/subscription-purchases failed")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load subscription purchases: {e!s}",
        ) from e

    result = {
        "from_date": fd.isoformat(),
        "to_date": td.isoformat(),
        "page": page,
        "limit": limit,
        "total": total,
        "purchases": purchases,
    }
    if use_grouped:
        grouped_data = _group_admin_subscription_purchases(purchases, limit=limit)
        result["grouped"] = True
        result["groups"] = grouped_data["groups"]
        result["total_groups"] = grouped_data["total_groups"]
    return result


@router.get("/admin/subscription-events")
async def admin_subscription_events(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    query: Optional[str] = None,
    event_kind: Optional[str] = None,
    source: Optional[str] = None,
    renewals_only: Optional[bool] = False,
    grouped: Optional[bool] = False,
    page: Optional[int] = 1,
    limit: Optional[int] = 50,
    current_user: User = Depends(get_current_user),
):
    """
    Play subscription lifecycle events (RTDN + in-app verify/sync).
    Filter by processed_at date. Use event_kind=renewed or renewals_only=true for renewals.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    from datetime import date as date_type, timedelta

    today = date_type.today()
    if from_date and to_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = date_type.fromisoformat(to_date)
            if fd > td:
                fd, td = td, fd
        except ValueError:
            fd = today - timedelta(days=30)
            td = today
    elif from_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = today
        except ValueError:
            fd = today - timedelta(days=30)
            td = today
    elif to_date:
        try:
            td = date_type.fromisoformat(to_date)
            fd = td - timedelta(days=30)
        except ValueError:
            fd = today - timedelta(days=30)
            td = today
    else:
        fd = today - timedelta(days=30)
        td = today

    kind_filter = (event_kind or "").strip().lower() or None
    if renewals_only:
        kind_filter = "renewed"

    try:
        if grouped:
            data = credit_service.list_admin_subscription_event_groups(
                fd.isoformat(),
                td.isoformat(),
                query=query,
                event_kind=kind_filter,
                source=(source or "").strip().lower() or None,
                renewals_only=bool(renewals_only),
                limit=limit or 50,
            )
            data["grouped"] = True
        else:
            data = credit_service.list_admin_subscription_events(
                fd.isoformat(),
                td.isoformat(),
                query=query,
                event_kind=kind_filter,
                source=(source or "").strip().lower() or None,
                page=page or 1,
                limit=limit or 50,
            )
    except Exception as e:
        logger.exception("GET /admin/subscription-events failed")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load subscription events: {e!s}",
        ) from e

    return data


@router.post("/admin/subscription-events/backfill")
async def admin_subscription_events_backfill(
    dry_run: bool = Query(True, description="Preview only; set false to insert rows"),
    current_user: User = Depends(get_current_user),
):
    """Backfill event log from user_subscriptions. Idempotent via event_id backfill|sub|{id}."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        stats = credit_service.backfill_subscription_events_from_history(dry_run=dry_run)
    except Exception as e:
        logger.exception("POST /admin/subscription-events/backfill failed")
        raise HTTPException(
            status_code=500,
            detail=f"Backfill failed: {e!s}",
        ) from e
    return stats


@router.post("/admin/subscription-order-ids/backfill")
async def admin_subscription_order_ids_backfill(
    dry_run: bool = Query(True, description="Preview only; set false to write order IDs"),
    limit: Optional[int] = Query(None, ge=1, le=5000, description="Max tokens to process"),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch latest GPA order id from Google Play for each known subscription purchase_token.
    Does not recover full renewal chains (..0, ..1) — only Play's latest order per token.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        stats = credit_service.backfill_subscription_order_ids_from_play(
            dry_run=dry_run,
            limit=limit,
        )
    except Exception as e:
        logger.exception("POST /admin/subscription-order-ids/backfill failed")
        raise HTTPException(
            status_code=500,
            detail=f"Order ID backfill failed: {e!s}",
        ) from e
    if stats.get("error"):
        raise HTTPException(status_code=503, detail=stats["error"])
    return stats


@router.get("/admin/dashboard")
async def get_credits_dashboard(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Dashboard stats for a date range. from_date, to_date: YYYY-MM-DD. Default: this month."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from datetime import date as date_type, timedelta
    today = date_type.today()
    if from_date and to_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = date_type.fromisoformat(to_date)
            if fd > td:
                fd, td = td, fd
        except ValueError:
            fd = today.replace(day=1)
            td = today
    else:
        fd = today.replace(day=1)
        td = today
    return credit_service.get_dashboard_stats(fd.isoformat(), td.isoformat())


@router.get("/admin/intelligence")
async def get_credits_intelligence(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Aggregated payer/spend intelligence for admin. Default range: this month."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from datetime import date as date_type

    today = date_type.today()
    if from_date and to_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = date_type.fromisoformat(to_date)
            if fd > td:
                fd, td = td, fd
        except ValueError:
            fd = today.replace(day=1)
            td = today
    else:
        fd = today.replace(day=1)
        td = today
    return credit_service.get_admin_intelligence_stats(fd.isoformat(), td.isoformat())


@router.get("/admin/intelligence-segment")
async def get_credits_intelligence_segment(
    segment_key: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from datetime import date as date_type

    today = date_type.today()
    if from_date and to_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = date_type.fromisoformat(to_date)
            if fd > td:
                fd, td = td, fd
        except ValueError:
            fd = today.replace(day=1)
            td = today
    else:
        fd = today.replace(day=1)
        td = today
    try:
        return credit_service.get_admin_campaign_segment(
            segment_key,
            from_date=fd.isoformat(),
            to_date=td.isoformat(),
            page=page,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _question_cost_rate_for_model(model_name: Optional[str], input_tokens_est: int) -> Dict[str, Any]:
    m = (model_name or "").strip()
    if not m or m.lower() == "unknown":
        # Prefer configured chat model when historical row lacks model id.
        try:
            from utils.admin_settings import get_gemini_chat_model
            m = (get_gemini_chat_model() or "").strip() or "models/gemini-2.5-flash"
        except Exception:
            m = "models/gemini-2.5-flash"
    tier = "gt_200k" if int(input_tokens_est or 0) > 200_000 else "le_200k"
    rates = {
        "models/gemini-3.1-flash-lite": {"in_le": 0.25, "in_gt": 0.25, "cached_in_le": 0.025, "cached_in_gt": 0.025, "out_le": 1.50, "out_gt": 1.50},
        "models/gemini-3.1-pro-preview": {"in_le": 2.00, "in_gt": 4.00, "cached_in_le": 0.20, "cached_in_gt": 0.40, "out_le": 12.00, "out_gt": 18.00},
        "models/gemini-3.1-flash-live-preview": {"in_le": 0.75, "in_gt": 0.75, "cached_in_le": 0.075, "cached_in_gt": 0.075, "out_le": 4.50, "out_gt": 4.50},
        "models/gemini-3.1-flash-image-preview": {"in_le": 0.25, "in_gt": 0.25, "cached_in_le": 0.025, "cached_in_gt": 0.025, "out_le": 1.50, "out_gt": 1.50},
        "models/gemini-3.1-flash-tts-preview": {"in_le": 1.00, "in_gt": 1.00, "cached_in_le": 0.10, "cached_in_gt": 0.10, "out_le": 20.00, "out_gt": 20.00},
        "models/gemini-3.5-flash": {"in_le": 1.50, "in_gt": 1.50, "cached_in_le": 0.15, "cached_in_gt": 0.15, "out_le": 9.00, "out_gt": 9.00},
        "models/gemini-3-pro-preview": {"in_le": 2.00, "in_gt": 4.00, "cached_in_le": 0.20, "cached_in_gt": 0.40, "out_le": 12.00, "out_gt": 18.00},
        "models/gemini-3-flash-preview": {"in_le": 0.50, "in_gt": 0.50, "cached_in_le": 0.05, "cached_in_gt": 0.05, "out_le": 3.00, "out_gt": 3.00},
        "models/gemini-2.5-pro": {"in_le": 1.25, "in_gt": 2.50, "cached_in_le": 0.125, "cached_in_gt": 0.25, "out_le": 10.00, "out_gt": 15.00},
        "models/gemini-2.5-flash": {"in_le": 0.30, "in_gt": 0.30, "cached_in_le": 0.03, "cached_in_gt": 0.03, "out_le": 2.50, "out_gt": 2.50},
        "models/gemini-2.5-flash-lite": {"in_le": 0.10, "in_gt": 0.10, "cached_in_le": 0.01, "cached_in_gt": 0.01, "out_le": 0.40, "out_gt": 0.40},
        "models/gemini-2.0-flash-001": {"in_le": 0.10, "in_gt": 0.10, "cached_in_le": 0.01, "cached_in_gt": 0.01, "out_le": 0.40, "out_gt": 0.40},
        "models/gemini-2.0-flash-lite-001": {"in_le": 0.075, "in_gt": 0.075, "cached_in_le": 0.0075, "cached_in_gt": 0.0075, "out_le": 0.30, "out_gt": 0.30},
        # DeepSeek (published cache-miss input + output per 1M; V4 uses same estimate until pricing differs)
        "deepseek-chat": {"in_le": 0.28, "in_gt": 0.28, "out_le": 0.42, "out_gt": 0.42},
        "deepseek-reasoner": {"in_le": 0.28, "in_gt": 0.28, "out_le": 0.42, "out_gt": 0.42},
        "deepseek-v4": {"in_le": 0.28, "in_gt": 0.28, "out_le": 0.42, "out_gt": 0.42},
        "deepseek-v4-reasoner": {"in_le": 0.28, "in_gt": 0.28, "out_le": 0.42, "out_gt": 0.42},
    }
    row = rates.get(m)
    if not row:
        ml = m.lower()
        if "gemini-3.1-flash-lite" in ml or ("3.1" in ml and "flash-lite" in ml):
            row = {"in_le": 0.25, "in_gt": 0.25, "cached_in_le": 0.025, "cached_in_gt": 0.025, "out_le": 1.50, "out_gt": 1.50}
        elif "gemini-3.1-flash-live" in ml or ("3.1" in ml and "flash-live" in ml):
            row = {"in_le": 0.75, "in_gt": 0.75, "cached_in_le": 0.075, "cached_in_gt": 0.075, "out_le": 4.50, "out_gt": 4.50}
        elif "gemini-3.1-flash-image" in ml or ("3.1" in ml and "flash-image" in ml):
            row = {"in_le": 0.25, "in_gt": 0.25, "cached_in_le": 0.025, "cached_in_gt": 0.025, "out_le": 1.50, "out_gt": 1.50}
        elif "gemini-3.1-flash-tts" in ml or ("gemini-3.1" in ml and "tts" in ml):
            row = {"in_le": 1.00, "in_gt": 1.00, "cached_in_le": 0.10, "cached_in_gt": 0.10, "out_le": 20.00, "out_gt": 20.00}
        elif "gemini-3.1-pro" in ml:
            row = {"in_le": 2.00, "in_gt": 4.00, "cached_in_le": 0.20, "cached_in_gt": 0.40, "out_le": 12.00, "out_gt": 18.00}
        elif "gemini-3.5-flash" in ml or ("3.5" in ml and "flash" in ml):
            row = {"in_le": 1.50, "in_gt": 1.50, "cached_in_le": 0.15, "cached_in_gt": 0.15, "out_le": 9.00, "out_gt": 9.00}
        elif "flash-lite" in ml:
            row = {"in_le": 0.10, "in_gt": 0.10, "cached_in_le": 0.01, "cached_in_gt": 0.01, "out_le": 0.40, "out_gt": 0.40}
        elif "flash" in ml:
            row = {"in_le": 0.50, "in_gt": 0.50, "cached_in_le": 0.05, "cached_in_gt": 0.05, "out_le": 3.00, "out_gt": 3.00}
        elif "pro" in ml:
            row = {"in_le": 2.00, "in_gt": 4.00, "cached_in_le": 0.20, "cached_in_gt": 0.40, "out_le": 12.00, "out_gt": 18.00}
        elif ml.startswith("deepseek-"):
            row = {"in_le": 0.28, "in_gt": 0.28, "cached_in_le": 0.28, "cached_in_gt": 0.28, "out_le": 0.42, "out_gt": 0.42}
        else:
            row = {"in_le": 0.10, "in_gt": 0.10, "cached_in_le": 0.10, "cached_in_gt": 0.10, "out_le": 0.40, "out_gt": 0.40}
    return {
        "input": float(row["in_gt"] if tier == "gt_200k" else row["in_le"]),
        "cached_input": float(row["cached_in_gt"] if tier == "gt_200k" else row["cached_in_le"]),
        "output": float(row["out_gt"] if tier == "gt_200k" else row["out_le"]),
        "tier": tier,
        "resolved_model": m,
    }


def _extract_cache_setup_tokens(raw_parallel_usage: Any) -> int:
    if not raw_parallel_usage:
        return 0
    try:
        data = json.loads(raw_parallel_usage) if isinstance(raw_parallel_usage, str) else raw_parallel_usage
    except Exception:
        return 0
    if not isinstance(data, dict):
        return 0
    totals = data.get("totals")
    if not isinstance(totals, dict):
        return 0
    try:
        return max(0, int(totals.get("cache_setup_input_tokens") or 0))
    except Exception:
        return 0


@router.get("/admin/question-cost-summary")
async def get_question_cost_summary(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Question unit economics summary: question counts, paid/free split, charged money, and rough AI cost."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from datetime import date as date_type, timedelta
    today = date_type.today()
    if from_date and to_date:
        try:
            fd = date_type.fromisoformat(from_date)
            td = date_type.fromisoformat(to_date)
            if fd > td:
                fd, td = td, fd
        except ValueError:
            fd = today
            td = today
    else:
        fd = today
        td = today
    # Use ISO timestamp strings for cross-DB compatibility (postgres/sqlite adapters).
    start_dt = f"{fd.isoformat()} 00:00:00"
    end_exclusive_dt = f"{(td + timedelta(days=1)).isoformat()} 00:00:00"

    # Business rule requested: 1 credit = ₹1
    inr_per_credit = 1.0
    usd_to_inr = float(os.getenv("USD_TO_INR_RATE") or 93.0)
    fixed_input_chars_per_question = 200_000
    fixed_input_tokens_per_question = max(1, int(round(fixed_input_chars_per_question / 4.0)))
    light_input_chars_per_question = 5_000
    light_input_tokens_per_question = max(1, int(round(light_input_chars_per_question / 4.0)))
    try:
        chat_question_cost = int(credit_service.get_credit_setting("chat_question_cost") or 1)
    except Exception:
        chat_question_cost = 1

    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT COUNT(*)
            FROM chat_messages cm
            WHERE cm.sender = 'assistant'
              AND cm.status = 'completed'
              AND COALESCE(cm.message_type, 'answer') = 'answer'
              AND cm.completed_at IS NOT NULL
              AND cm.completed_at >= %s AND cm.completed_at < %s
            """,
            (start_dt, end_exclusive_dt),
        )
        total_completed_answers = int((cur.fetchone() or [0])[0] or 0)

        cur = execute(
            conn,
            """
            SELECT COUNT(*), COALESCE(SUM(ABS(amount)), 0)
            FROM credit_transactions
            WHERE transaction_type = 'spent'
              AND source = 'feature_usage'
              AND reference_id = 'chat_question'
              AND created_at >= %s AND created_at < %s
            """,
            (start_dt, end_exclusive_dt),
        )
        paid_question_rows, paid_credits_spent = cur.fetchone() or (0, 0)
        paid_question_rows = int(paid_question_rows or 0)
        paid_credits_spent = float(paid_credits_spent or 0.0)

        free_question_rows = max(0, total_completed_answers - paid_question_rows)
        free_credits_equivalent = float(free_question_rows * chat_question_cost)
        charged_credits = paid_credits_spent
        total_credits_equivalent = charged_credits + free_credits_equivalent

        # Rough model cost for answered questions in range.
        cur = execute(
            conn,
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'chat_messages'
            """,
            (),
        )
        msg_cols = {r[0] for r in (cur.fetchall() or [])}
        has_llm_input_tokens = "llm_input_tokens" in msg_cols
        has_llm_output_tokens = "llm_output_tokens" in msg_cols
        has_llm_cached_input_tokens = "llm_cached_input_tokens" in msg_cols
        has_llm_non_cached_input_tokens = "llm_non_cached_input_tokens" in msg_cols
        has_parallel_llm_usage = "parallel_llm_usage" in msg_cols
        input_tok_expr = "COALESCE(cm.llm_input_tokens, 0)" if has_llm_input_tokens else "0"
        output_tok_expr = "COALESCE(cm.llm_output_tokens, 0)" if has_llm_output_tokens else "0"
        cached_input_tok_expr = "COALESCE(cm.llm_cached_input_tokens, 0)" if has_llm_cached_input_tokens else "0"
        non_cached_input_tok_expr = "COALESCE(cm.llm_non_cached_input_tokens, 0)" if has_llm_non_cached_input_tokens else "0"
        parallel_usage_expr = "cm.parallel_llm_usage" if has_parallel_llm_usage else "CAST(NULL AS TEXT)"

        cur = execute(
            conn,
            f"""
            SELECT cm.content AS assistant_answer,
                   cs.chat_llm_model,
                   {input_tok_expr} AS llm_input_tokens,
                   {output_tok_expr} AS llm_output_tokens,
                   {cached_input_tok_expr} AS llm_cached_input_tokens,
                   {non_cached_input_tok_expr} AS llm_non_cached_input_tokens,
                   {parallel_usage_expr} AS parallel_llm_usage
            FROM chat_messages cm
            JOIN chat_sessions cs ON cs.session_id = cm.session_id
            WHERE cm.sender = 'assistant'
              AND cm.status = 'completed'
              AND COALESCE(cm.message_type, 'answer') = 'answer'
              AND cm.completed_at IS NOT NULL
              AND cm.completed_at >= %s AND cm.completed_at < %s
            """,
            (start_dt, end_exclusive_dt),
        )
        rows = cur.fetchall() or []

    model_breakdown: Dict[str, Dict[str, Any]] = {}
    ai_cost_total_inr = 0.0
    input_non_cached_cost_total_inr = 0.0
    input_cached_cost_total_inr = 0.0
    cache_setup_cost_total_inr = 0.0
    output_cost_total_inr = 0.0
    for r in rows:
        model = (r[1] or "unknown").strip() or "unknown"
        a = str(r[0] or "")
        llm_input_tokens = int(r[2] or 0)
        llm_output_tokens = int(r[3] or 0)
        llm_cached_input_tokens = int(r[4] or 0)
        llm_non_cached_input_tokens = int(r[5] or 0)
        llm_parallel_usage_raw = r[6] if len(r) > 6 else None
        cache_setup_tokens = _extract_cache_setup_tokens(llm_parallel_usage_raw)
        if llm_input_tokens > 0:
            q_tokens = llm_input_tokens
        else:
            # Lightweight turns (intent-routing-like, very short outputs) likely don't carry full context.
            q_tokens = light_input_tokens_per_question if len(a) < 280 else fixed_input_tokens_per_question
        a_tokens = llm_output_tokens if llm_output_tokens > 0 else max(1, int(round(len(a) / 4.0)))
        if llm_non_cached_input_tokens <= 0 and llm_input_tokens > 0:
            llm_non_cached_input_tokens = max(llm_input_tokens - llm_cached_input_tokens, 0)
        rate = _question_cost_rate_for_model(model, max(q_tokens, llm_non_cached_input_tokens))
        non_cached_q_tokens = llm_non_cached_input_tokens if llm_input_tokens > 0 else q_tokens
        cached_q_tokens = llm_cached_input_tokens if llm_input_tokens > 0 else 0
        input_non_cached_usd_cost = (non_cached_q_tokens / 1_000_000.0) * float(rate["input"])
        input_cached_usd_cost = (cached_q_tokens / 1_000_000.0) * float(rate.get("cached_input") or rate["input"])
        cache_setup_usd_cost = (cache_setup_tokens / 1_000_000.0) * float(rate["input"])
        output_usd_cost = (a_tokens / 1_000_000.0) * float(rate["output"])
        usd_cost = (
            input_non_cached_usd_cost
            + input_cached_usd_cost
            + cache_setup_usd_cost
            + output_usd_cost
        )
        inr_cost = usd_cost * usd_to_inr
        input_non_cached_inr_cost = input_non_cached_usd_cost * usd_to_inr
        input_cached_inr_cost = input_cached_usd_cost * usd_to_inr
        cache_setup_inr_cost = cache_setup_usd_cost * usd_to_inr
        output_inr_cost = output_usd_cost * usd_to_inr
        ai_cost_total_inr += inr_cost
        input_non_cached_cost_total_inr += input_non_cached_inr_cost
        input_cached_cost_total_inr += input_cached_inr_cost
        cache_setup_cost_total_inr += cache_setup_inr_cost
        output_cost_total_inr += output_inr_cost
        resolved_model = str(rate.get("resolved_model") or model)
        if resolved_model not in model_breakdown:
            model_breakdown[resolved_model] = {
                "model": resolved_model,
                "questions": 0,
                "input_tokens_estimate": 0,
                "output_tokens_estimate": 0,
                "cached_input_tokens": 0,
                "non_cached_input_tokens": 0,
                "cache_setup_input_tokens": 0,
                "input_cost_non_cached_inr_estimate": 0.0,
                "input_cost_cached_inr_estimate": 0.0,
                "cache_setup_cost_inr_estimate": 0.0,
                "output_cost_inr_estimate": 0.0,
                "ai_cost_inr_estimate": 0.0,
            }
        m = model_breakdown[resolved_model]
        m["questions"] += 1
        m["input_tokens_estimate"] += q_tokens
        m["output_tokens_estimate"] += a_tokens
        m["cached_input_tokens"] += cached_q_tokens
        m["non_cached_input_tokens"] += non_cached_q_tokens
        m["cache_setup_input_tokens"] += cache_setup_tokens
        m["input_cost_non_cached_inr_estimate"] += input_non_cached_inr_cost
        m["input_cost_cached_inr_estimate"] += input_cached_inr_cost
        m["cache_setup_cost_inr_estimate"] += cache_setup_inr_cost
        m["output_cost_inr_estimate"] += output_inr_cost
        m["ai_cost_inr_estimate"] += inr_cost

    for m in model_breakdown.values():
        m["input_cost_non_cached_inr_estimate"] = round(float(m["input_cost_non_cached_inr_estimate"]), 4)
        m["input_cost_cached_inr_estimate"] = round(float(m["input_cost_cached_inr_estimate"]), 4)
        m["cache_setup_cost_inr_estimate"] = round(float(m["cache_setup_cost_inr_estimate"]), 4)
        m["output_cost_inr_estimate"] = round(float(m["output_cost_inr_estimate"]), 4)
        m["ai_cost_inr_estimate"] = round(float(m["ai_cost_inr_estimate"]), 4)
    models_sorted = sorted(model_breakdown.values(), key=lambda x: x["questions"], reverse=True)

    return {
        "from_date": fd.isoformat(),
        "to_date": td.isoformat(),
        "inr_per_credit": inr_per_credit,
        "chat_question_cost_credits": chat_question_cost,
        "summary": {
            "questions_total": total_completed_answers,
            "questions_paid": paid_question_rows,
            "questions_free_estimated": free_question_rows,
            "credits_charged": round(charged_credits, 2),
            "credits_free_equivalent": round(free_credits_equivalent, 2),
            "credits_total_equivalent": round(total_credits_equivalent, 2),
            "money_charged_inr": round(charged_credits * inr_per_credit, 2),
            "money_free_equivalent_inr": round(free_credits_equivalent * inr_per_credit, 2),
            "money_total_equivalent_inr": round(total_credits_equivalent * inr_per_credit, 2),
            "input_cost_non_cached_inr_estimate": round(input_non_cached_cost_total_inr, 4),
            "input_cost_cached_inr_estimate": round(input_cached_cost_total_inr, 4),
            "cache_setup_cost_inr_estimate": round(cache_setup_cost_total_inr, 4),
            "output_cost_inr_estimate": round(output_cost_total_inr, 4),
            "ai_cost_inr_estimate": round(ai_cost_total_inr, 4),
            "gross_margin_inr_estimate": round((charged_credits * inr_per_credit) - ai_cost_total_inr, 4),
        },
        "model_breakdown": models_sorted,
        "note": (
            "Free questions are estimated as completed chat answers minus paid chat_question debit rows. "
            f"Input uses full {fixed_input_chars_per_question} chars/question ({fixed_input_tokens_per_question} tokens est) "
            f"and light {light_input_chars_per_question} chars/question ({light_input_tokens_per_question} tokens est) for lightweight turns."
        ),
    }
