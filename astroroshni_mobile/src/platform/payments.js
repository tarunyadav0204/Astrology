/** Native platforms use react-native-razorpay / IAP — no Checkout.js here. */
export function loadRazorpayScript() {
  return Promise.reject(new Error('Web Razorpay Checkout is only available on web'));
}

export async function openRazorpayCheckout() {
  throw new Error('Web Razorpay Checkout is only available on web');
}

export async function openRazorpaySubscriptionCheckout() {
  throw new Error('Web Razorpay Checkout is only available on web');
}
