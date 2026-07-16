/** Web stub — Google Play / App Store IAP is unavailable in browsers. */
const RNIap = {
  initConnection: async () => false,
  endConnection: async () => {},
  getProducts: async () => [],
  getSubscriptions: async () => [],
  requestPurchase: async () => {
    throw new Error('In-app purchases are not available on web. Use Razorpay checkout.');
  },
  purchaseUpdatedListener: () => ({ remove() {} }),
  purchaseErrorListener: () => ({ remove() {} }),
  finishTransaction: async () => {},
  getAvailablePurchases: async () => [],
};

module.exports = {
  __esModule: true,
  default: RNIap,
  ...RNIap,
};
