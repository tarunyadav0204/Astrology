# Google Play Billing for Credits

This doc describes how to enable in-app purchase of credits on Android via Google Play Billing. The backend verification and Credit screen UI are already in place; you need to configure Play Console, a service account, and (optionally) wire the app with `react-native-iap`.

## Overview

- **Backend:** `POST /api/credits/google-play/verify` verifies a purchase with the Google Play Developer API and grants credits. Idempotent by `order_id` (same order is not credited twice).
- **App:** Credit screen shows a “Buy credits” section on Android with product tiles (50, 100, 250, 500 credits). After a successful purchase, the app sends `purchase_token`, `product_id`, and `order_id` to the verify endpoint, then refreshes balance and history.
- **Products:** Backend expects these product IDs and grants the corresponding credits: `credits_50` → 50, `credits_100` → 100, `credits_250` → 250, `credits_500` → 500.

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
