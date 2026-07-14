/**
 * Razorpay checkout for Google Play User Choice billing (alternative path on Android).
 * Requires react-native-razorpay and backend support for google_play_external_transaction_token.
 */

/** Filter: adb logcat | grep '\[USER_CHOICE_IAP\]' — remove after one successful capture / prod. */
const USER_CHOICE_IAP_TAG = '[USER_CHOICE_IAP]';
export function userChoiceIapLog(phase, data = {}) {
  try {
    console.log(USER_CHOICE_IAP_TAG, phase, { ts: Date.now(), ...data });
  } catch (_) {
    /* ignore */
  }
}

/** Safe summary of Play `details.products` for logcat (no full tokens). */
export function describeUserChoiceRawProductsForLog(raw) {
  if (!Array.isArray(raw)) return { notArray: true, type: typeof raw };
  return raw.map((p, i) => ({
    i,
    t: typeof p,
    keys: p && typeof p === 'object' && !Array.isArray(p) ? Object.keys(p).slice(0, 16) : null,
    strPreview: typeof p === 'string' ? String(p).slice(0, 120) : null,
  }));
}

/** Native SDKs sometimes omit the `razorpay_` prefix or use alternate keys. */
function normalizeRazorpayCheckoutSuccess(payData) {
  if (!payData || typeof payData !== 'object') {
    return payData;
  }
  const paymentId =
    payData.razorpay_payment_id || payData.payment_id || payData.razorpayPaymentId;
  const orderId = payData.razorpay_order_id || payData.order_id;
  const subscriptionId =
    payData.razorpay_subscription_id ||
    payData.subscription_id ||
    payData.subscriptionId;
  const signature =
    payData.razorpay_signature || payData.signature || payData.razorpaySignature;
  return {
    ...payData,
    ...(paymentId != null && String(paymentId) !== ''
      ? { razorpay_payment_id: String(paymentId) }
      : {}),
    ...(orderId != null && String(orderId) !== '' ? { razorpay_order_id: String(orderId) } : {}),
    ...(subscriptionId != null && String(subscriptionId) !== ''
      ? { razorpay_subscription_id: String(subscriptionId) }
      : {}),
    ...(signature != null && String(signature) !== '' ? { razorpay_signature: String(signature) } : {}),
  };
}

/**
 * Google Play returns {@link https://developer.android.com/reference/com/android/billingclient/api/UserChoiceDetails.Product UserChoiceDetails.Product}
 * per item (getId, getOfferToken, getType). Nitro/JSON may expose `id` / `productId` / snake_case, or a single
 * string from `toString()` like `{id: my_sub, type: subs, ...}` — not always plain SKUs.
 */
function parseOneUserChoiceProductEntry(p) {
  if (p == null) return null;
  if (typeof p === 'object') {
    const oid =
      p.id ??
      p.productId ??
      p.product_id ??
      p.sku ??
      (typeof p.getId === 'function' ? p.getId() : undefined);
    if (oid != null && String(oid).trim() !== '') return String(oid).trim();
    return null;
  }
  if (typeof p === 'number' && Number.isFinite(p)) return String(p);
  if (typeof p === 'string') {
    const s = p.trim();
    if (!s) return null;
    const mId = s.match(/\bid:\s*([^,}\s]+)/);
    if (mId) return mId[1].trim();
    const mPid = s.match(/\bproductId:\s*([^,}\s]+)/i);
    if (mPid) return mPid[1].trim();
    return s;
  }
  return null;
}

export function extractUserChoiceProductIds(rawProducts) {
  if (!Array.isArray(rawProducts)) return [];
  return rawProducts
    .map(parseOneUserChoiceProductEntry)
    .filter((id) => id != null && String(id).trim() !== '');
}

/**
 * Match Play user-choice line items to backend catalog SKUs.
 * Play may send `productId:basePlanId`; our API stores the subscription product id only.
 * Resolves subscription first (same UX as tapping Subscribe), then credits.
 *
 * @returns {{ playProductIds: string[], creditSku: string|null, subSku: string|null }}
 */
export function resolveUserChoiceCatalogSkus(rawProducts, creditProductIds, subscriptionProductIds) {
  const playProductIds = extractUserChoiceProductIds(rawProducts);

  const matchCatalog = (catalogIds) => {
    const catalog = (catalogIds || []).map((k) => String(k).trim()).filter(Boolean);
    for (const known of catalog) {
      const kk = known.toLowerCase();
      for (const raw of playProductIds) {
        const rl = String(raw).trim().toLowerCase();
        if (rl === kk || rl.startsWith(`${kk}:`)) return known;
      }
    }
    return null;
  };

  const subSku = matchCatalog(subscriptionProductIds);
  const creditSku = subSku ? null : matchCatalog(creditProductIds);

  return { playProductIds, creditSku, subSku };
}

export function creditsFromGooglePlayProductId(productId) {
  const m = /^credits_(\d+)$/i.exec(String(productId || ''));
  return m ? parseInt(m[1], 10) : null;
}

/**
 * @param {object} params
 * @param {import('../services/api').creditAPI} params.creditAPI
 * @param {number} params.credits
 * @param {string} params.externalTransactionToken
 * @param {string} [params.description]
 * @returns {Promise<object>}
 */
export async function payCreditPackUserChoiceRazorpay({
  creditAPI,
  credits,
  externalTransactionToken,
  description,
}) {
  const t0 = Date.now();
  // Preload native module before network so open() is ready when order returns.
  const RazorpayCheckout = require('react-native-razorpay').default;
  userChoiceIapLog('credit_create_order', {
    credits,
    tokenLen: externalTransactionToken ? String(externalTransactionToken).length : 0,
  });
  const { data } = await creditAPI.createRazorpayOrder(
    credits,
    { google_play_external_transaction_token: externalTransactionToken },
    { preferMainApi: true }
  );
  userChoiceIapLog('credit_create_order_ok', {
    order_id: data?.order_id,
    amount: data?.amount,
    create_order_ms: Date.now() - t0,
  });
  const options = {
    key: data.key_id,
    amount: String(data.amount),
    currency: data.currency || 'INR',
    order_id: data.order_id,
    name: 'AstroRoshni',
    description: description || `${data.credits} credits`,
    theme: { color: '#e91e63' },
  };
  const openAt = Date.now();
  const rawCheckout = await RazorpayCheckout.open(options);
  userChoiceIapLog('credit_checkout_opened_returned', {
    open_to_return_ms: Date.now() - openAt,
    total_ms: Date.now() - t0,
  });
  userChoiceIapLog('credit_checkout_raw_keys', {
    keys: rawCheckout && typeof rawCheckout === 'object' ? Object.keys(rawCheckout) : [],
  });
  const payData = normalizeRazorpayCheckoutSuccess(rawCheckout);
  const { data: verifyData } = await creditAPI.verifyRazorpayPayment({
    razorpay_order_id: payData.razorpay_order_id,
    razorpay_payment_id: payData.razorpay_payment_id,
    razorpay_signature: payData.razorpay_signature,
    google_play_external_transaction_token: externalTransactionToken,
  });
  userChoiceIapLog('credit_verify_ok', { credits_added: verifyData?.credits_added });
  return verifyData;
}

/**
 * @param {object} params
 * @param {import('../services/api').creditAPI} params.creditAPI
 * @param {number} params.planId
 * @param {string} params.externalTransactionToken
 * @param {string} [params.tierName]
 * @returns {Promise<object>}
 */
export async function paySubscriptionUserChoiceRazorpay({
  creditAPI,
  planId,
  externalTransactionToken,
  tierName,
}) {
  const RazorpayCheckout = require('react-native-razorpay').default;
  try {
    userChoiceIapLog('sub_create_request', {
      planId,
      tokenLen: externalTransactionToken ? String(externalTransactionToken).length : 0,
    });
    const { data } = await creditAPI.createRazorpaySubscription(planId, {
      google_play_external_transaction_token: externalTransactionToken,
    });
    userChoiceIapLog('sub_create_ok', {
      subscription_id: data?.subscription_id,
      tier_name: data?.tier_name,
      key_id: data?.key_id ? `${String(data.key_id).slice(0, 8)}...` : null,
    });
    const options = {
      key: data.key_id,
      subscription_id: data.subscription_id,
      name: 'AstroRoshni',
      description: `${tierName || data.tier_name || 'VIP'} — monthly`,
      theme: { color: '#e91e63' },
    };
    const rawCheckout = await RazorpayCheckout.open(options);
    userChoiceIapLog('sub_checkout_raw_keys', {
      keys: rawCheckout && typeof rawCheckout === 'object' ? Object.keys(rawCheckout) : [],
    });
    const payData = normalizeRazorpayCheckoutSuccess(rawCheckout);
    userChoiceIapLog('sub_checkout_normalized', {
      has_razorpay_payment_id: !!payData?.razorpay_payment_id,
      has_razorpay_subscription_id: !!payData?.razorpay_subscription_id,
      has_razorpay_signature: !!payData?.razorpay_signature,
    });
    if (!payData.razorpay_payment_id || !payData.razorpay_subscription_id || !payData.razorpay_signature) {
      userChoiceIapLog('sub_checkout_missing_fields', {
        message: 'Razorpay checkout missing id/signature for verify',
      });
      throw new Error(
        'Razorpay did not return payment id, subscription id, and signature. Update the app or try again.'
      );
    }
    userChoiceIapLog('sub_verify_request', {
      razorpay_subscription_id: payData.razorpay_subscription_id,
      razorpay_payment_id: payData.razorpay_payment_id,
    });
    const { data: verifyData } = await creditAPI.verifyRazorpaySubscription({
      razorpay_subscription_id: payData.razorpay_subscription_id,
      razorpay_payment_id: payData.razorpay_payment_id,
      razorpay_signature: payData.razorpay_signature,
      google_play_external_transaction_token: externalTransactionToken,
    });
    userChoiceIapLog('sub_verify_ok', {
      success: verifyData?.success,
      tier_name: verifyData?.subscription?.tier_name,
    });
    return verifyData;
  } catch (e) {
    userChoiceIapLog('sub_flow_caught_error', {
      message: e?.message,
      status: e?.response?.status,
      detail: e?.response?.data?.detail,
    });
    throw e;
  }
}
