/**
 * Razorpay checkout for Google Play User Choice billing (alternative path on Android).
 * Requires react-native-razorpay and backend support for google_play_external_transaction_token.
 */

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
  const RazorpayCheckout = require('react-native-razorpay').default;
  const { data } = await creditAPI.createRazorpayOrder(credits, {
    google_play_external_transaction_token: externalTransactionToken,
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
  const payData = normalizeRazorpayCheckoutSuccess(await RazorpayCheckout.open(options));
  const { data: verifyData } = await creditAPI.verifyRazorpayPayment({
    razorpay_order_id: payData.razorpay_order_id,
    razorpay_payment_id: payData.razorpay_payment_id,
    razorpay_signature: payData.razorpay_signature,
    google_play_external_transaction_token: externalTransactionToken,
  });
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
  const { data } = await creditAPI.createRazorpaySubscription(planId, {
    google_play_external_transaction_token: externalTransactionToken,
  });
  const options = {
    key: data.key_id,
    subscription_id: data.subscription_id,
    name: 'AstroRoshni',
    description: `${tierName || data.tier_name || 'VIP'} — monthly`,
    theme: { color: '#e91e63' },
  };
  const payData = normalizeRazorpayCheckoutSuccess(await RazorpayCheckout.open(options));
  if (!payData.razorpay_payment_id || !payData.razorpay_subscription_id || !payData.razorpay_signature) {
    throw new Error(
      'Razorpay did not return payment id, subscription id, and signature. Update the app or try again.'
    );
  }
  const { data: verifyData } = await creditAPI.verifyRazorpaySubscription({
    razorpay_subscription_id: payData.razorpay_subscription_id,
    razorpay_payment_id: payData.razorpay_payment_id,
    razorpay_signature: payData.razorpay_signature,
    google_play_external_transaction_token: externalTransactionToken,
  });
  return verifyData;
}
