# Subscription Tier Design (VIP Plans + Credit Discount)

## 1. What is RTDN?

**RTDN = Real-Time Developer Notifications** (Google Play).

- Google can send **HTTP POST requests to your backend** when subscription events happen: new purchase, renewal, cancellation, expiry, pause, etc.
- You register a URL in Play Console; Google calls it with a signed message (e.g. one-time token, subscription state).
- **Why use it:** So your server can update `user_subscriptions` (e.g. set status = expired, extend end_date on renewal) **without the user opening the app**. If you don’t use RTDN, you only know the subscription state when the app calls your “verify subscription” API (e.g. at app open or before a feature). That’s simpler but can be slightly out of date (e.g. user cancelled yesterday, app still shows active until next open).
- **Recommendation:** Start with **verify-on-app-open** (simpler). Add RTDN later when you want automatic sync of renewals/cancellations.

---

## 2. Current Subscription Usage (Findings)

### Tables
- **subscription_plans:** Referenced in `main.py` (APIs, register, admin). Table creation is commented out in current `main.py`; it exists in backup with columns: `plan_id`, `platform`, `plan_name`, `price`, `duration_months`, `features` (JSON), `is_active`.
- **user_subscriptions:** Used in register, get-user, subscription APIs, admin. Backup schema: `id` (or `subscription_id` in live query), `userid`, `plan_id`, `status`, `start_date`, `end_date`.

### Plan names in code (old, can be replaced)
- **Seed data (commented):**  
  `astrovishnu`: Free, Premium.  
  `astroroshni`: Free, Basic, Premium.
- **Register / OAuth:** Only looks up **`plan_name = 'Free'`** and **`platform IN ('astrovishnu','astroroshni')`** to assign new users a free plan. No other logic depends on “Basic” or “Premium” by name.
- **Frontend:** `frontend/src/config/domains.config.js` – `getPrimaryPlatform()` checks `plan_name === 'Premium'` to choose platform. This is the **only** place that treats a plan name as special. We can change it to “highest paid tier” (e.g. by discount or tier order) when we introduce VIP names.
- **Mobile app:** Does **not** call `/api/user-subscriptions` or `/api/subscription-plans`. No breaking change there.
- **Credits/pricing:** No code applies subscription or plan to credit cost today. All feature costs come from `credit_settings` only.

**Conclusion:** Old plan names (Free, Basic, Premium) and platforms (astrovishnu, astroroshni) are only used for: (1) register giving “Free”, (2) admin display/edit, (3) web `getPrimaryPlatform` for “Premium”. We can safely replace/rename plans and add new columns; we will keep one **Free** plan for astroroshni (and optionally astrovishnu) for register, and add **VIP Silver / VIP Gold / VIP Platinum** with explicit names and discount.

---

## 3. Design Summary

| Item | Choice |
|------|--------|
| Tier names | Explicit: e.g. **VIP Silver**, **VIP Gold**, **VIP Platinum** (plus **Free** for no paid plan). |
| Discount | **Same % for all features** per tier (e.g. Silver 10%, Gold 20%, Platinum 30%). |
| Free / no plan | **Current behaviour:** no discount (full price from `credit_settings`). |
| Tables | Reuse **subscription_plans** and **user_subscriptions**; extend plans with tier + discount + Google product id. |
| Google Play | Subscription product IDs: **subscription_400**, **subscription_500**, **subscription_600** (monthly). |
| Renewal/expiry | Start with **verify when app opens**; add **RTDN** later for automatic renewal/expiry. |
| Credits | Tier = **discount on credit cost**; user still spends credits, at a lower rate. |

---

## 4. Schema Changes

### 4.1 subscription_plans (extend)

Add columns (or ensure they exist):

| Column | Type | Purpose |
|--------|------|--------|
| `tier_name` | TEXT | Display name, e.g. "Free", "VIP Silver", "VIP Gold", "VIP Platinum". |
| `discount_percent` | INTEGER | 0–100. Same discount for all features. Free = 0. |
| `google_play_product_id` | TEXT NULL | e.g. subscription_400, subscription_500, subscription_600. NULL for Free. |

- **platform:** Keep; use **astroroshni** for these plans (and optionally keep astrovishnu + Free for legacy).
- **plan_name:** Can keep for backward compatibility; use same as tier_name or a slug (e.g. `vip_silver`). Register will still look for `plan_name = 'Free'` and `platform = 'astroroshni'` (and optionally astrovishnu).

### 4.2 user_subscriptions

- No new columns required. Already has `userid`, `plan_id`, `status`, `start_date`, `end_date`. Optional: store `purchase_token` or `order_id` for Google subscription for support/refunds (can be added later).
- **Backward compat:** Some DBs use `subscription_id` as the primary key column (main.py selects `us.subscription_id`). The migration does **not** create `user_subscriptions`; it only ensures `subscription_plans` and seeds. New server installs that need `user_subscriptions` should use existing init or a separate migration that matches the column name used in main.py.

### 4.3 Migration / seed

1. **Ensure tables exist** (create if not, as in backup).
2. **Add columns** to `subscription_plans`: `tier_name`, `discount_percent`, `google_play_product_id` (with defaults if needed).
3. **Replace or insert plans** (one-time):
   - **astroroshni – Free:** price 0, discount_percent 0, tier_name "Free", google_play_product_id NULL. (Keep for register.)
   - **astroroshni – VIP Silver:** discount_percent 10, tier_name "VIP Silver", product_id **subscription_vip_silver** (price in DB/Play is independent).
   - **astroroshni – VIP Gold:** 20%, "VIP Gold", **subscription_vip_gold**.
   - **astroroshni – VIP Platinum:** 30%, "VIP Platinum", **subscription_vip_platinum**.
- **Product IDs are tier-based, not price-based:** You set the actual price in Google Play Console (and optionally in `subscription_plans.price` for display). Changing price does not require code or product ID changes.
4. **Deactivate or remove** old plans (astrovishnu Free/Premium, astroroshni Basic/Premium) if you want a clean slate; or keep Free for both platforms and mark others inactive. **Register must still find a plan_id for `plan_name = 'Free'` and platform `astroroshni`** (and optionally astrovishnu) so new users get a row in user_subscriptions.

---

## 5. Credit Cost Logic

- **Current:** Feature cost = value from `credit_settings` (with optional admin discount column).
- **New:**  
  1. Resolve user’s **active subscription** (user_subscriptions where status = 'active', end_date >= today) → **plan_id** → **subscription_plans** row.  
  2. Read **discount_percent** (0 if no plan or Free).  
  3. **effective_cost = base_cost * (100 - discount_percent) / 100** (integer rounding).  
- Apply this in:
  - **Credits service** (or a small helper): e.g. `get_effective_cost(userid, feature_key)` that (a) gets base cost from credit_settings, (b) gets user’s plan discount, (c) returns discounted cost.  
  - **Chat (chat_routes.py and chat_history/routes.py),** muhurat, and any other feature that checks/deducts credits: use **effective_cost** instead of raw cost.

---

## 6. Google Play Subscriptions

- **Products:** Create in Play Console with **product IDs**: **subscription_vip_silver**, **subscription_vip_gold**, **subscription_vip_platinum**. Set prices and billing (e.g. monthly) in Play; you can change prices anytime without touching backend.
- **App:** Use Billing Library **subscriptions** API (not one-time products). On purchase, get purchase token + product id → call backend.
- **Backend:** New endpoint, e.g. `POST /credits/google-play/subscription/verify`:
  - Verify with **Google Play Developer API (subscriptions)**.
  - Map product_id → plan (e.g. subscription_400 → VIP Silver).
  - Create or update **user_subscriptions** (plan_id, start_date, end_date from Google, optional purchase_token).
- **Renewal/expiry:** Initially: when user opens app, app can call verify or a “sync subscription” endpoint; backend re-checks with Google and updates user_subscriptions. Later: add RTDN and a webhook endpoint to update on renewal/cancel/expiry.

---

## 7. Frontend / Admin

- **Admin:** Subscription plans list and user subscription edit already use `platform` and `plan_name`. Show new plans (Free, VIP Silver, VIP Gold, VIP Platinum); optional: show tier_name and discount_percent. No need to change API contract if plan_id and plan_name are still returned.
- **Web `getPrimaryPlatform`:** Update so “highest tier” is not hardcoded to `plan_name === 'Premium'`. For example: prefer plan with highest discount_percent, or check tier_name in a fixed order (Platinum > Gold > Silver > Free).

---

## 8. Implementation Order (suggested)

1. **Backend: migration** – Ensure subscription_plans and user_subscriptions exist; add tier_name, discount_percent, google_play_product_id; seed Free + VIP Silver/Gold/Platinum; deactivate old plans (except Free).
2. **Backend: credit helper** – `get_effective_cost(userid, feature_key)` using subscription + discount_percent.
3. **Backend: feature routes** – Use effective cost in chat (both routes), muhurat, and any other credit-deducting flows.
4. **Backend: subscription verify** – POST verify Google Play subscription → update user_subscriptions.
5. **Mobile:** Credits/pricing API – Ensure app gets and displays discounted cost (and optional “You’re on VIP Silver – 10% off”) where needed.
6. **Mobile:** Subscription purchase – Add subscription products in app; on purchase, call backend verify; then refresh user subscription state.
7. **Admin + web** – Adjust plan list and getPrimaryPlatform as above.
8. **(Later)** RTDN endpoint and handling for renewal/expiry.

---

## 8.1 Deduction flow and VIP discount

**Display (app):** The app calls `GET /credits/settings/my-pricing` when logged in. The backend returns `pricing` (effective cost per feature after subscription discount) and optionally `pricing_original` (for strikethrough). So the user sees e.g. "7 credits" (30% off 10).

**Deduction (backend):** Each feature route that deducts credits must use **effective cost**, not base cost:

1. Get base cost: `base = credit_service.get_credit_setting(setting_key)` (e.g. `chat_question_cost`).
2. Get effective cost for the user: `effective = credit_service.get_effective_cost(current_user.userid, base)` (applies VIP discount %).
3. Check balance: `user_balance >= effective`.
4. After the feature succeeds, deduct: `credit_service.spend_credits(current_user.userid, effective, feature, description)`.

**Features that do this:** Chat (streaming and chat_history), event timeline, career, wealth, health, marriage, education, progeny, muhurat (childbirth/vehicle/griha_pravesh/etc.), trading (daily + monthly), karma analysis, mundane chat. All use `get_effective_cost` so VIP users are charged the discounted amount.

**Generic `POST /credits/spend`:** Used when the app explicitly sends `amount` and `feature`. The backend deducts the given amount (no server-side lookup of effective cost). So the app **must** send the same amount it got from my-pricing for that feature; otherwise the user could be over- or under-charged. Feature routes that deduct inside the backend (chat, analysis, etc.) do not use this endpoint; they compute effective cost and call `spend_credits` directly.

---

## 9. Plan Names to Keep vs Replace

| Current (seed) | Action |
|----------------|--------|
| astroroshni – Free | **Keep** (required for register). Add tier_name "Free", discount_percent 0. |
| astroroshni – Basic, Premium | **Remove or set is_active = 0.** Replace with VIP Silver, Gold, Platinum. |
| astrovishnu – Free, Premium | **Optional:** Keep Free for backward compat; else remove/deactivate. Not used for credits. |

Register will continue to look up `plan_name = 'Free'` and `platform = 'astroroshni'` (and optionally astrovishnu) and insert into user_subscriptions; no change to register flow except that the Free plan row now has tier_name and discount_percent.
