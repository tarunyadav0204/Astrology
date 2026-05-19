const RAZORPAY_SCRIPT = 'https://checkout.razorpay.com/v1/checkout.js';

export function loadRazorpayScript() {
  return new Promise((resolve, reject) => {
    if (typeof window !== 'undefined' && window.Razorpay) {
      resolve(window.Razorpay);
      return;
    }
    const existing = document.querySelector(`script[src="${RAZORPAY_SCRIPT}"]`);
    if (existing) {
      existing.addEventListener('load', () => resolve(window.Razorpay));
      existing.addEventListener('error', () => reject(new Error('Payment script failed to load')));
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
