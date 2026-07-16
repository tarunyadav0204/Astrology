/** Web stub — native Razorpay module is replaced by Checkout.js on web. */
const RazorpayCheckout = {
  open: async () => {
    throw new Error('Use web Razorpay Checkout instead of react-native-razorpay on web.');
  },
};

module.exports = {
  __esModule: true,
  default: RazorpayCheckout,
};
