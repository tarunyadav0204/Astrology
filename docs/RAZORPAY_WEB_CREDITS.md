# Razorpay — web credit purchases

Web users buy credits through **Razorpay Checkout** (UPI, cards, netbanking). Credit packs match the Android app: **50, 100, 250, 500** credits (`credits_50` … `credits_500` naming in order notes).

Mobile continues to use **Google Play Billing**; this is a separate payment channel with the same credit semantics.

## Environment (backend)

| Variable | Required | Description |
|----------|----------|-------------|
| `RAZORPAY_KEY_ID` | Yes | Public key (e.g. `rzp_live_…` or `rzp_test_…`). |
| `RAZORPAY_KEY_SECRET` | Yes | Secret — server only; never expose to the browser. |
| `RAZORPAY_WEBHOOK_SECRET` | Strongly recommended | From Razorpay Dashboard → Webhooks → secret for signature verification. |
| `RAZORPAY_PRICE_PAISE_50` etc. | No | Override default INR prices (values in **paise**: `4900` = ₹49). |

Defaults (paise): 50 → 4900, 100 → 9900, 250 → 22900, 500 → 44900.

## API

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/credits/razorpay/catalog` | Bearer | Returns `key_id` + pack list with authoritative `amount_paise` / display strings. |
| POST | `/api/credits/razorpay/create-order` | Bearer | Body `{ "credits": 50 \| 100 \| 250 \| 500 }`. Creates Razorpay order; notes include `userid`, `credits`, `product_id`. |
| POST | `/api/credits/razorpay/verify` | Bearer | Body: `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature` from Checkout `handler`. Verifies HMAC, fetches payment, grants credits if captured. Idempotent on `payment_id`. |
| POST | `/api/credits/razorpay/webhook` | None (signature only) | Raw body; header `X-Razorpay-Signature`. Handles `payment.captured`; same grant logic as verify. |

## Security model

1. **Amounts and packs** are defined only on the server (`create-order` ignores client-supplied prices).
2. **Client success path**: Razorpay’s `razorpay_signature` is verified with `order_id|payment_id` and **Key Secret** before granting.
3. **Payment fetch**: After signature verification, the server loads the payment via Razorpay API and checks `status === captured`, **notes** (`userid`, `credits`, `product_id`), and **amount in paise** matches the configured price for that pack.
4. **Idempotency**: `credit_transactions.reference_id` = Razorpay **payment id**; duplicate events do not double-grant.
5. **Webhook**: Verifies **webhook secret** on raw body (different from API secret). Use this so credits apply even if the user closes the tab before `verify` runs.

## Razorpay Dashboard

1. **API keys**: Test vs Live — match keys in `.env` with mode you use.
2. **Webhook**: URL `https://<your-api-host>/api/credits/razorpay/webhook`, active, subscribe at least to **payment.captured**.
3. **Settlement / KYC**: Complete per Razorpay’s requirements before live traffic.

## Frontend

`CreditsModal` loads `/api/credits/razorpay/catalog` when the user is signed in, shows a 2×2 grid of packs, and opens `https://checkout.razorpay.com/v1/checkout.js` Checkout. No Razorpay secret in the frontend — only `key_id` from the API (same as publishing Key ID in client-side Checkout).

## Refunds

Process refunds in **Razorpay Dashboard** (or API). Credits should be reversed separately (similar to Google Play: admin deduct or a dedicated `razorpay` reversal endpoint when you add one).

## Local development

Without keys, `catalog` and `create-order` return **503** with a clear message; the modal shows an error instead of packs. Use **test keys** and [test cards / UPI](https://razorpay.com/docs/payments/payments/test-card-details/) from Razorpay docs.
