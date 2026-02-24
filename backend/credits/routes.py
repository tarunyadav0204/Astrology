from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
import logging
import re
import sqlite3
from auth import get_current_user, User
from .credit_service import CreditService
from .admin.promo_manager import PromoCodeManager

router = APIRouter()
credit_service = CreditService()
promo_manager = PromoCodeManager()

logger = logging.getLogger(__name__)

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
    """Build Android Publisher API service with service account credentials."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        import os
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Google Play not configured (install google-api-python-client and google-auth).",
        )
    credentials_path = os.environ.get("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON")
    if not credentials_path or not os.path.isfile(credentials_path):
        raise HTTPException(
            status_code=503,
            detail="Google Play service account JSON not configured (set GOOGLE_PLAY_SERVICE_ACCOUNT_JSON).",
        )
    scopes = ["https://www.googleapis.com/auth/androidpublisher"]
    credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
    return build("androidpublisher", "v3", credentials=credentials)


def _verify_google_play_purchase(package_name: str, product_id: str, purchase_token: str) -> dict:
    """Verify purchase with Google Play Developer API. Returns purchase info or raises."""
    service = _get_play_service()
    request = service.purchases().products().get(
        packageName=package_name,
        productId=product_id,
        token=purchase_token,
    )
    return request.execute()


def _credits_from_product_id(product_id: str) -> Optional[int]:
    """Parse product_id per convention credits_N -> N. Returns None if not a credit product."""
    m = CREDITS_PRODUCT_PATTERN.match((product_id or "").strip())
    return int(m.group(1)) if m else None


def _list_google_play_products(package_name: str) -> List[dict]:
    """
    Fetch in-app products from Google Play and return credit products only.
    Includes only active one-time products whose sku matches credits_N; credits derived from sku.
    This helper is also safe to tweak for deploy triggers (no runtime behavior change).
    """
    try:
        service = _get_play_service()
        all_products: List[dict] = []

        # ---- Preferred: new monetization.onetimeproducts.list API ----
        logger.info("Google Play: listing one-time products via monetization.onetimeproducts.list")
        try:
            token = None
            while True:
                request = service.monetization().onetimeproducts().list(
                    packageName=package_name,
                    pageToken=token,
                )
                resp = request.execute()
                one_time_products = resp.get("oneTimeProducts") or []
                for p in one_time_products:
                    sku = (p.get("productId") or "").strip()
                    credits = _credits_from_product_id(sku)
                    if credits is None:
                        continue
                    listings = p.get("listings") or {}
                    default_lang = p.get("defaultLanguage") or "en-US"
                    listing = listings.get(default_lang) or listings.get("en-US") or next(iter(listings.values()), None) if listings else None
                    title = (listing.get("title") or sku) if listing else sku
                    description = (listing.get("description") or "") if listing else ""
                    # Price information is nested under purchaseOptions; we don't strictly need it,
                    # so keep a simple placeholder for now.
                    price_micros = None
                    price_currency = None
                    all_products.append({
                        "product_id": sku,
                        "credits": credits,
                        "title": title,
                        "description": description,
                        "price_micros": "0" if price_micros is None else str(price_micros),
                        "price_currency": price_currency or "USD",
                    })
                token = resp.get("nextPageToken")
                if not token:
                    break
        except Exception as e:
            # If the new monetization API is unavailable or permission-restricted, fall back.
            logger.warning("Google Play monetization.onetimeproducts.list failed, falling back to inappproducts.list: %s", str(e))
            all_products = []

        # ---- Fallback: legacy inappproducts.list API ----
        if not all_products:
            logger.info("Google Play: falling back to legacy inappproducts.list for product listing")
            token = None
            while True:
                request = service.inappproducts().list(packageName=package_name, token=token)
                resp = request.execute()
                inappproduct_list = resp.get("inappproduct") or []
                for p in inappproduct_list:
                    sku = (p.get("sku") or "").strip()
                    status = (p.get("status") or "").lower()
                    purchase_type = (p.get("purchaseType") or "").lower()
                    if status != "active":
                        continue
                    # One-time managed product (not subscription)
                    if purchase_type not in ("manageduser", "purchasetypeunspecified", ""):
                        continue
                    credits = _credits_from_product_id(sku)
                    if credits is None:
                        continue
                    default_price = p.get("defaultPrice") or {}
                    price_micros = default_price.get("priceMicros")
                    price_micros = str(price_micros) if price_micros is not None else "0"
                    price_currency = default_price.get("currency") or "USD"
                    listings = p.get("listings") or {}
                    default_lang = p.get("defaultLanguage") or "en-US"
                    listing = listings.get(default_lang) or listings.get("en-US") or next(iter(listings.values()), None) if listings else None
                    title = (listing.get("title") or sku) if listing else sku
                    description = (listing.get("description") or "") if listing else ""
                    all_products.append({
                        "product_id": sku,
                        "credits": credits,
                        "title": title,
                        "description": description,
                        "price_micros": price_micros,
                        "price_currency": price_currency,
                    })
                token = (resp.get("tokenPagination") or {}).get("nextPageToken")
                if not token:
                    break

        sorted_products = sorted(all_products, key=lambda x: x["credits"])
        logger.info("Google Play: listed %d credit products", len(sorted_products))
        return sorted_products
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Google Play: unexpected error while listing products: %s", str(e))
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


@router.get("/google-play/products")
async def get_google_play_products(current_user: User = Depends(get_current_user)):
    """List credit products from Google Play (active in-app products with id convention credits_N)."""
    try:
        products = _list_google_play_products(PACKAGE_NAME)
        return {"products": products}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch products: {str(e)}")


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
    })

    credit_service.add_credits(
        current_user.userid,
        amount,
        GOOGLE_PLAY_SOURCE,
        reference_id=order_id,
        description=f"Google Play: {product_id}",
        metadata=purchase_metadata,
    )
    return {"success": True, "message": "Credits added", "credits_added": amount}


@router.get("/balance")
async def get_credit_balance(current_user: User = Depends(get_current_user)):
    balance = credit_service.get_user_credits(current_user.userid)
    return {"credits": balance}

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
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO promo_codes (code, credits, max_uses, max_uses_per_user, expires_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.code.upper(),
            request.credits,
            request.max_uses,
            request.max_uses_per_user,
            request.expires_at,
            current_user.userid
        ))
        
        conn.commit()
        conn.close()
        
        return {"message": "Promo code created successfully"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Promo code already exists")

@router.get("/admin/promo-codes")
async def get_promo_codes(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT code, credits, max_uses, max_uses_per_user, used_count, is_active, expires_at, created_at
        FROM promo_codes 
        ORDER BY created_at DESC
    """)
    
    codes = []
    for row in cursor.fetchall():
        codes.append({
            "code": row[0],
            "credits": row[1],
            "max_uses": row[2],
            "max_uses_per_user": row[3],
            "used_count": row[4],
            "is_active": row[5],
            "expires_at": row[6],
            "created_at": row[7]
        })
    
    conn.close()
    return {"promo_codes": codes}

@router.put("/admin/promo-codes/{code}")
async def update_promo_code(code: str, request: UpdatePromoCodeRequest, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE promo_codes 
        SET credits = ?, max_uses = ?, max_uses_per_user = ?, is_active = ?
        WHERE code = ?
    """, (request.credits, request.max_uses, request.max_uses_per_user, request.is_active, code.upper()))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Promo code updated successfully"}

@router.delete("/admin/promo-codes/{code}")
async def delete_promo_code(code: str, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM promo_codes WHERE code = ?", (code.upper(),))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "Promo code deleted successfully"}

@router.post("/admin/delete-promo-code")
async def delete_promo_code_post(request: dict, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    code = request.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Promo code is required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM promo_codes WHERE code = ?", (code.upper(),))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    conn.commit()
    conn.close()
    
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

    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT userid, amount, source, reference_id, description
            FROM credit_transactions
            WHERE id = ?
            """,
            (request.transaction_id,),
        )
        row = cursor.fetchone()
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
        # Close DB before calling service (it opens its own connection)
        conn.close()
        credit_service.refund_credits(request.userid, request.amount, feature_key, description)
        return {"message": "Refund applied", "credits_refunded": request.amount}
    finally:
        try:
            conn.close()
        except Exception:
            pass


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
            success = credit_service.update_credit_setting(key, int(value))
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

@router.get("/settings/premium-chat-cost")
async def get_premium_chat_cost():
    cost = credit_service.get_credit_setting('premium_chat_cost')
    return {"cost": cost}

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
    cost = credit_service.get_credit_setting('event_timeline_cost')
    return {"cost": cost}

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
    
    stats = promo_manager.get_usage_stats()
    return stats

@router.get("/admin/users")
async def get_all_users_with_credits(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.userid, u.name, u.phone, COALESCE(uc.credits, 0) as credits
        FROM users u
        LEFT JOIN user_credits uc ON u.userid = uc.userid
        ORDER BY u.name
    """)
    
    users = []
    for row in cursor.fetchall():
        users.append({
            "userid": row[0],
            "name": row[1],
            "phone": row[2],
            "credits": row[3]
        })
    
    conn.close()
    return {"users": users}

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
    transactions = credit_service.get_google_play_transactions(
        fd.isoformat(), td.isoformat(), query=query, order_id_filter=order_id
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