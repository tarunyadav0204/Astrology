# Google Play Billing for Credits

This doc describes how to enable in-app purchase of credits on Android via Google Play Billing. The backend verification and Credit screen UI are already in place; you need to configure Play Console, a service account, and (optionally) wire the app with `react-native-iap`.

## Overview

- **Backend:** `GET /api/credits/google-play/products` fetches active in-app products from Google Play and returns credit products (product IDs following the `credits_N` convention). `POST /api/credits/google-play/verify` verifies a purchase with the Google Play Developer API and grants credits. Idempotent by `order_id` (same order is not credited twice).
- **App:** Credit screen fetches products from the backend (which in turn lists them from Play), shows a “Buy credits” section on Android, and after a successful purchase sends `purchase_token`, `product_id`, and `order_id` to the verify endpoint.
- **Products:** Create products in Play Console with **Product ID** format `credits_N` (e.g. `credits_50`, `credits_100`, `credits_250`, `credits_500`). The backend lists only active one-time products whose ID matches this pattern and grants N credits per purchase. You can add or change products in Play Console; the app will show whatever is returned by the API.

---

## 1. Google Play Console

1. Open [Google Play Console](https://play.google.com/console) → your app (**com.astroroshni.mobile**).
2. **Monetize** → **Products** → **In-app products** → Create product.
3. Create four products with these **Product IDs** (exactly):
   - `credits_50`
   - `credits_100`
   - `credits_250`
   - `credits_500`
4. For each: set name, description, and price. Save and activate.
5. Use **Consumable** so the same user can buy the same product again.

---

## 2. Service account for server-side verification

1. **Google Cloud:** Open [APIs & Services](https://console.cloud.google.com/apis) for the project linked to your Play Console app (or create one and link it in Play Console).
2. Enable **Google Play Android Developer API**.
3. **Credentials** → **Create credentials** → **Service account**. Create a key (JSON), download the file, and keep it secret.
4. **Play Console** → **Users and permissions** → Invite the service account email with at least:
   - **View financial data**
   - **View app information and download bulk reports (read-only)**
5. On the server where the backend runs, set the path to the JSON key:
   ```bash
   export GOOGLE_PLAY_SERVICE_ACCOUNT_JSON=/path/to/your-service-account.json
   ```
   Restart the backend after setting this.

Without this, the verify endpoint returns 503 and does not grant credits.

---

## 3. Backend (already implemented)

- **Endpoint:** `POST /api/credits/google-play/verify`  
  **Body:** `{ "purchase_token": "...", "product_id": "credits_50", "order_id": "GPA.1234..." }`  
  **Auth:** Bearer token (same as other credit APIs).

- **Dependencies:** `google-api-python-client` and `google-auth` are in `backend/requirements.txt`. Install with `pip install -r requirements.txt`.

- **Idempotency:** The same `order_id` is only credited once (stored in `credit_transactions.reference_id` with `source = 'google_play'`).

- **Customer support / disputes:** For each verified Google Play purchase we store in `credit_transactions.metadata` (JSON):
  - `purchase_token` – Required by Google Play support to look up the order; use when a user says they were charged but didn’t get credits.
  - `purchase_time_millis` – Purchase time from Google (milliseconds since epoch) to match bank/Play order history.
  - `product_id`, `order_id` – Redundant with `reference_id` and `description`, kept in metadata for one-place receipt data.

Support can query the DB for the user’s transaction and use `purchase_token` with the [Play Developer API](https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.products/get) or share with Google support for refund/order lookup. Do not expose `purchase_token` in user-facing APIs.

---

## 3b. Returning payment to the user (refunds)

You don't return money from your app — **Google** does. Your app only needs to **reverse the credits** after a refund so the user doesn't keep the product.

### Step 1: Refund the money (Google)

- **Play Console (recommended):** [Order management](https://play.google.com/console) → find the order by **Order ID** (e.g. `GPA.1234-5678-9012-34567` — same as `credit_transactions.reference_id` for that purchase). Issue a full or partial refund. You can search by order ID or by the user's Google account email.
- **API:** You can also call the [Google Play Developer API `orders.refund`](https://developers.google.com/android-publisher/api-ref/rest/v3/orders/refund) (needs OAuth and the order ID). Refunds are typically done from Play Console for one-off cases.

### Step 2: Reverse the credits (your backend)

After you've refunded in Play, deduct the credits so the user's balance matches the refund:

- **Admin endpoint:** `POST /api/credits/admin/reverse-google-play-purchase`  
  **Body:** `{ "userid": 123, "order_id": "GPA.1234-5678-9012-34567" }`  
  **Auth:** Admin Bearer token.

  The backend finds the original Google Play transaction for that user and order, deducts the same credit amount, and records a reversal transaction. If the user has already spent some of those credits, their balance can go negative (or you can fail and handle manually).

- **Alternative:** If you prefer not to use the endpoint, an admin can deduct credits manually (e.g. via an "admin deduct" tool) and set the description to `Reversal for Google Play order GPA.xxx` for audit.

### Summary

| Step | Where | Action |
|------|--------|--------|
| 1. Return money | Google Play Console (or API) | Refund the order (search by order_id from your DB). |
| 2. Reverse credits | Your backend | Call admin reverse endpoint with `userid` and `order_id`, or deduct manually and note the order_id. |

---

## 4. App: react-native-iap (implemented)

The Credit screen is wired for in-app purchases on Android:

- **Buy credits** section shows product tiles (50, 100, 250, 500 credits).
- On load: `initConnection()`, `flushFailedPurchasesCachedAsPendingAndroid()`, `getProducts()`, and `purchaseUpdatedListener` / `purchaseErrorListener` are set up.
- When the user taps **Buy**, `requestPurchase({ sku: productId })` runs. On success, the listener calls the backend verify API, then `finishTransaction({ purchase, isConsumable: true })`, and refreshes balance/history.

**You must rebuild the native app** (IAP does not work in Expo Go):

```bash
cd astroroshni_mobile && npx expo run:android
```

Or create a new AAB with EAS and upload to Internal testing / Production.

---

## 5. Testing

- Use **License testers** in Play Console so test Google accounts can make test purchases without being charged.
- Verify that:
  - After a successful purchase, the app calls the verify endpoint and the user’s balance and history update.
  - Sending the same `order_id` again returns “Already credited” and does not add credits again.

---

## Summary

| Step | Action |
|------|--------|
| Play Console | Create consumable in-app products: `credits_50`, `credits_100`, `credits_250`, `credits_500`. |
| Google Cloud | Enable Play Developer API; create service account; download JSON key. |
| Play Console | Invite service account with “View financial data” (and read app info). |
| Backend | Set `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` to the JSON key path; install `google-api-python-client` and `google-auth`. |
| App | `react-native-iap` is integrated; rebuild with `expo run:android` or EAS. |
