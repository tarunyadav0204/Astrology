/** Web stub — AppsFlyer native SDK is not used in the browser. */
const appsFlyer = {
  initSdk: (_options, success) => {
    if (typeof success === 'function') success('web-stub');
  },
  logEvent: () => {},
  setCustomerUserId: () => {},
  onInstallConversionData: () => ({ remove: () => {} }),
  onDeepLink: () => ({ remove: () => {} }),
};

module.exports = {
  __esModule: true,
  default: appsFlyer,
};
