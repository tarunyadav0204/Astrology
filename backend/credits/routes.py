from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
import logging
import os
import re
from auth import get_current_user, User
from .credit_service import CreditService
from .admin.promo_manager import PromoCodeManager
from utils.env_json import parse_json_from_env
from activity.publisher import publish_activity
from db import get_conn, execute, SQL_SUBSCRIPTION_PLAN_ACTIVE
from .razorpay_routes import refund_razorpay_payment, fetch_razorpay_payment

router = APIRouter()
credit_service = CreditService()
promo_manager = PromoCodeManager()

logger = logging.getLogger(__name__)

# Env var name preferred; GOOGLE_SERVICE_ACCOUNT_KEY accepted as fallback
def _get_play_credentials_path():
    return os.environ.get("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON") or os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")


def _get_play_credentials():
    """
    Return Google service account credentials from env.
    Supports (1) file path to JSON, or (2) inline JSON string in the env var.
    """
    from google.oauth2 import service_account
    _ensure_play_env_loaded()
    raw = _get_play_credentials_path()
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    scopes = ["https://www.googleapis.com/auth/androidpublisher"]
    # Inline JSON: value starts with { (or is wrapped in quotes by .env)
    info = parse_json_from_env(raw)
    if info:
        try:
            return service_account.Credentials.from_service_account_info(info, scopes=scopes)
        except (ValueError, TypeError) as e:
            logger.warning("Google Play: invalid inline JSON credentials: %s", e)
            return None
    # File path
    if os.path.isfile(raw):
        return service_account.Credentials.from_service_account_file(raw, scopes=scopes)
    logger.warning("Google Play: credentials value is neither a valid file path nor JSON (starts with %r)", raw[:50] if len(raw) > 50 else raw)
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


class AdminRefundRequest(BaseModel):
    userid: int
    transaction_id: int
    amount: int
    comment: Optional[str] = None


GOOGLE_PLAY_SOURCE = "google_play"


PACKAGE_NAME = "com.astroroshni.mobile"


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
    logger.info("Google Play: verifying subscription package=%s subscriptionId=%s", package_name, subscription_id)
    try:
        service = _get_play_service()
        request = service.purchases().subscriptions().get(
            packageName=package_name,
            subscriptionId=subscription_id,
            token=purchase_token,
        )
        result = request.execute()
        logger.info("Google Play: subscription verify response keys=%s", list(result.keys()) if isinstance(result, dict) else type(result))
        return result
    except Exception as e:
        logger.error("Google Play: subscription verify error: %s", e, exc_info=True)
        raise


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
    try:
        from google.auth.transport.requests import AuthorizedSession

        credentials = _get_play_credentials()
        if not credentials:
            return None
        session = AuthorizedSession(credentials)
        url = f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{package_name}/subscriptions/{product_id}"
        logger.info("Google Play: fetching subscription price GET %s", url)
        resp = session.get(url)
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
                        return formatted
            # Fallback: first regional config
            for rc in regional:
                parsed = _price_from_play_money(rc.get("price") or {})
                if parsed:
                    amount, currency = parsed
                    formatted = _format_amount_currency(amount, currency)
                    logger.info("Google Play subscription price %s: %s (from regionalConfig)", product_id, formatted)
                    return formatted
            other = bp.get("otherRegionsConfig") or {}
            for key in ("usdPrice", "eurPrice"):
                parsed = _price_from_play_money(other.get(key) or {})
                if parsed:
                    amount, currency = parsed
                    formatted = _format_amount_currency(amount, currency or ("USD" if key == "usdPrice" else "EUR"))
                    logger.info("Google Play subscription price %s: %s (from %s)", product_id, formatted, key)
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
            resp = session.get(base_url, params=params)
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


@router.get("/google-play/products")
async def get_google_play_products(current_user: User = Depends(get_current_user)):
    """List credit products from Google Play (active in-app products with id convention credits_N)."""
    try:
        products = _list_google_play_products(PACKAGE_NAME)
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


@router.post("/google-play/verify")
async def verify_google_play_purchase(
    request: GooglePlayVerifyRequest,
    current_user: User = Depends(get_current_user),
):
    """Verify a Google Play in-app purchase and grant credits. Idempotent by order_id. Product ID must follow credits_N convention."""
    product_id = request.product_id.strip()
    amount = _credits_from_product_id(product_id)
    if amount is None:
        raise HTTPException(status_code=400, detail=f"Unknown or invalid product_id (expected credits_N): {product_id}")
    order_id = (request.order_id or "").strip()
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id is required")
    if not request.purchase_token.strip():
        raise HTTPException(status_code=400, detail="purchase_token is required")

    if credit_service.has_transaction_with_reference(current_user.userid, GOOGLE_PLAY_SOURCE, order_id):
        return {"success": True, "message": "Already credited", "credits_added": 0}

    try:
        purchase = _verify_google_play_purchase(
            PACKAGE_NAME, product_id, request.purchase_token.strip()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid or expired purchase: {str(e)}")

    purchase_state = purchase.get("purchaseState")
    if purchase_state != 0:  # 0 = Purchased
        raise HTTPException(status_code=400, detail="Purchase not in completed state")
    # Optional: check consumptionState if you use consumables (1 = consumed, 0 = yet to consume)
    # Acknowledge if required (some products require acknowledgement)
    # service.purchases().products().acknowledge(...)

    # Store receipt details for customer support / disputes (order_id already in reference_id)
    purchase_metadata = json.dumps({
        "purchase_token": purchase.get("purchaseToken") or request.purchase_token.strip(),
        "purchase_time_millis": purchase.get("purchaseTimeMillis"),
        "product_id": product_id,
        "order_id": order_id,
        "price_amount_micros": request.price_amount_micros,
        "price_currency": request.price_currency,
        "localized_price": request.localized_price,
    })

    ok = credit_service.add_credits(
        current_user.userid,
        amount,
        GOOGLE_PLAY_SOURCE,
        reference_id=order_id,
        description=f"Google Play: {product_id}",
        metadata=purchase_metadata,
    )
    if not ok:
        logger.error(
            "Google Play: verify OK with Play but add_credits failed user=%s order_id=%s product=%s amount=%s",
            current_user.userid,
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
        user_id=current_user.userid,
        user_phone=current_user.phone,
        user_name=current_user.name,
        resource_type="order",
        resource_id=order_id,
        metadata={
            "credits_added": amount,
            "product_id": product_id,
            "order_id": order_id,
        },
    )
    return {"success": True, "message": "Credits added", "credits_added": amount}


@router.post("/google-play/subscription/verify")
async def verify_google_play_subscription(
    request: GooglePlaySubscriptionVerifyRequest,
    current_user: User = Depends(get_current_user),
):
    """Verify a Google Play subscription and set user's tier (VIP Silver/Gold/Platinum). Idempotent: re-calling extends/updates end_date."""
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
        )
        return {
            "success": True,
            "message": "Subscription active",
            "subscription_tier_name": result["tier_name"],
            "end_date": result["end_date"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid or expired subscription: {str(e)}")


def _sync_subscription_from_play(
    userid: int,
    product_id: str,
    purchase_token: str,
    *,
    accept_any_payment_state: bool = False,
) -> dict:
    """Verify subscription with Google Play and update our DB. Used by both verify and sync.
    If accept_any_payment_state is True (sync), we update DB even when cancelled/expired so our record matches Play."""
    plan_id = credit_service.get_plan_id_by_google_play_product_id(product_id)
    if not plan_id:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown subscription product_id: {product_id}",
        )
    purchase = _verify_google_play_subscription(PACKAGE_NAME, product_id, purchase_token)
    if not accept_any_payment_state:
        payment_state = purchase.get("paymentState")
        if payment_state not in (0, 1):
            raise HTTPException(status_code=400, detail="Subscription not in valid payment state")
    from datetime import datetime, timedelta
    expiry_ms = purchase.get("expiryTimeMillis") or purchase.get("startTimeMillis") or 0
    start_ms = purchase.get("startTimeMillis") or expiry_ms
    start_date = datetime.utcfromtimestamp(int(start_ms) / 1000).strftime("%Y-%m-%d")
    # If user cancelled on Play, set end_date to yesterday so they stop appearing as subscribed immediately
    if accept_any_payment_state and purchase.get("userCancellationTimeMillis"):
        end_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        end_date = datetime.utcfromtimestamp(int(expiry_ms) / 1000).strftime("%Y-%m-%d")
    success = credit_service.set_user_subscription(userid, plan_id, start_date, end_date)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update subscription")
    tier_name = credit_service.get_subscription_tier_name(userid)
    return {"tier_name": tier_name or product_id, "end_date": end_date}


@router.post("/google-play/subscription/sync")
async def sync_google_play_subscription(
    request: GooglePlaySubscriptionVerifyRequest,
    current_user: User = Depends(get_current_user),
):
    """Re-verify subscription with Google Play and update our DB. Call this when the app opens or user visits Credits
    so we stay in sync if they changed/cancelled/renewed on Play. Accepts any payment state so we can update end_date."""
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
        )
        return {
            "success": True,
            "message": "Subscription synced",
            "subscription_tier_name": result["tier_name"],
            "end_date": result["end_date"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not sync subscription: {str(e)}")


@router.post("/google-play/subscription/clear")
async def clear_subscription_no_purchase(current_user: User = Depends(get_current_user)):
    """Clear subscription status when the app could not get any purchase token from the device (e.g. after user cancelled, getAvailablePurchases may return empty). Expires the user's subscription so the UI stops showing 'Current plan'. Call this only when the user has a subscription in our DB but the device returns no subscription purchase to sync."""
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
                SELECT plan_id, tier_name, discount_percent, google_play_product_id, price
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
                SELECT plan_id, plan_name, 0, NULL, price
                FROM subscription_plans
                WHERE platform = %s
                  AND {SQL_SUBSCRIPTION_PLAN_ACTIVE}
                ORDER BY plan_name
                """,
                ("astroroshni",),
            )
            rows = [(r[0], r[1], 0, None, r[4]) for r in cur.fetchall()]
    plans = []
    for r in rows:
        plan_id, name, discount, product_id, price = r[0], r[1], r[2] or 0, r[3], float(r[4]) if r[4] is not None else 0
        if not product_id:
            continue
        # Fetch live price from Google Play so app shows same price as Play Store
        formatted_price = _get_subscription_price_from_play(PACKAGE_NAME, product_id)
        plans.append({
            "plan_id": plan_id,
            "tier_name": name or f"Plan {plan_id}",
            "discount_percent": discount,
            "google_play_product_id": product_id,
            "price": price,
            "formatted_price": formatted_price,
        })
    return {"plans": plans}


@router.get("/balance")
async def get_credit_balance(current_user: User = Depends(get_current_user)):
    balance = credit_service.get_user_credits(current_user.userid)
    free_used = credit_service.get_free_chat_question_used(current_user.userid)
    result = {"credits": balance, "free_question_available": not free_used}
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

# Admin endpoints
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


@router.get("/settings/analysis-pricing")
async def get_analysis_pricing():
    """Same source as deduction: all analysis costs from credit_settings. pricing = effective; pricing_original = only when discount set (for strikethrough). Unauthenticated; base/admin pricing."""
    pricing, pricing_original = _get_pricing_with_originals()
    result = {"pricing": pricing}
    if pricing_original:
        result["pricing_original"] = pricing_original
    return result


# Keys map for user-tier discounted pricing (same as _get_pricing_with_originals)
_PRICING_KEYS_MAP = [
    ("chat", "chat_question_cost"),
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

    result = {"pricing": pricing, "subscription_discount_percent": discount_percent}
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
async def get_user_transaction_history(userid: int, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    transactions = credit_service.get_transaction_history(userid)
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
    current_user: User = Depends(get_current_user),
):
    """
    Search credit transactions across all users with optional date range (YYYY-MM-DD)
    and wildcard search on user name or phone.
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

    transactions = credit_service.search_transactions(fd.isoformat(), td.isoformat(), query)
    return {"from_date": fd.isoformat(), "to_date": td.isoformat(), "transactions": transactions}


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