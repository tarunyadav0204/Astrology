const RAZORPAY_SCRIPT = 'https://checkout.razorpay.com/v1/checkout.js';

export function loadRazorpayScript() {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined') {
      reject(new Error('Razorpay checkout requires a browser'));
      return;
    }
    if (window.Razorpay) {
      resolve(window.Razorpay);
      return;
    }
    const existing = document.querySelector(`script[src="${RAZORPAY_SCRIPT}"]`);
    if (existing) {
      existing.addEventListener('load', () => resolve(window.Razorpay));
      existing.addEventListener('error', () =>
        reject(new Error('Payment script failed to load'))
      );
      return;
    }
    const s = document.createElement('script');
    s.src = RAZORPAY_SCRIPT;
    s.async = true;
    s.onload = () => resolve(window.Razorpay);
    s.onerror = () => reject(new Error('Payment script failed to load'));
    document.body.appendChild(s);
  });
}

/**
 * Open Razorpay Checkout.js for a credit pack order created by the backend.
 * @returns {Promise<object>} verify API response payload
 */
export async function openRazorpayCheckout({
  orderData,
  verifyPayment,
  description,
  themeColor = '#f97316',
  onDismiss,
}) {
  const Razorpay = await loadRazorpayScript();

  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (fn, value) => {
      if (settled) return;
      settled = true;
      fn(value);
    };

    const options = {
      key: orderData.key_id,
      amount: orderData.amount,
      currency: orderData.currency || 'INR',
      order_id: orderData.order_id,
      name: 'AstroRoshni',
      description: description || `${orderData.credits || ''} credits`.trim(),
      theme: { color: themeColor },
      modal: {
        ondismiss: () => {
          onDismiss?.();
          finish(reject, Object.assign(new Error('Payment cancelled'), { code: 'USER_CANCELLED' }));
        },
      },
      handler: async (response) => {
        try {
          const verifyData = await verifyPayment({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          finish(resolve, verifyData);
        } catch (err) {
          finish(reject, err);
        }
      },
    };

    try {
      const rzp = new Razorpay(options);
      rzp.open();
    } catch (err) {
      finish(reject, err);
    }
  });
}

export async function openRazorpaySubscriptionCheckout({
  subscriptionData,
  verifySubscription,
  description,
  themeColor = '#f97316',
  onDismiss,
}) {
  const Razorpay = await loadRazorpayScript();

  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (fn, value) => {
      if (settled) return;
      settled = true;
      fn(value);
    };
    const options = {
      key: subscriptionData.key_id,
      subscription_id: subscriptionData.subscription_id,
      name: 'AstroRoshni',
      description: description || `${subscriptionData.tier_name || 'Subscription'} — monthly`,
      theme: { color: themeColor },
      modal: {
        ondismiss: () => {
          onDismiss?.();
          finish(reject, Object.assign(new Error('Payment cancelled'), { code: 'USER_CANCELLED' }));
        },
      },
      handler: async (response) => {
        try {
          const data = await verifySubscription({
            razorpay_subscription_id: response.razorpay_subscription_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          finish(resolve, data);
        } catch (error) {
          finish(reject, error);
        }
      },
    };
    try {
      const checkout = new Razorpay(options);
      checkout.open();
    } catch (error) {
      finish(reject, error);
    }
  });
}
