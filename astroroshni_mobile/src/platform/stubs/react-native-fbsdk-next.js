/** Web stub — Facebook native SDK is not used in the browser. */
const sdk = {
  AppEventsLogger: {
    logEvent: () => {},
    logPurchase: () => {},
    setUserID: () => {},
    clearUserID: () => {},
  },
  Settings: {
    initializeSDK: () => {},
    setAdvertiserTrackingEnabled: () => {},
  },
};

module.exports = {
  __esModule: true,
  default: sdk,
  ...sdk,
};
