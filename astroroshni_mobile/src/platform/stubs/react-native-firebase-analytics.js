/** Web stub — Firebase Analytics native SDK is not used in the browser. */
const analytics = () => ({
  logEvent: async () => {},
  logPurchase: async () => {},
  logSignUp: async () => {},
  logLogin: async () => {},
  logScreenView: async () => {},
  setUserId: async () => {},
  setAnalyticsCollectionEnabled: async () => {},
});

module.exports = {
  __esModule: true,
  default: analytics,
};
