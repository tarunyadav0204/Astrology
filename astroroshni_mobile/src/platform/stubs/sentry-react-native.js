/** Minimal @sentry/react-native stand-in for Expo Web exports. */
const noop = () => {};
const scope = {
  setTag: noop,
  setExtra: noop,
  setContext: noop,
  setUser: noop,
  clear: noop,
};

const Sentry = {
  init: noop,
  captureException: (err) => {
    if (typeof console !== 'undefined') console.error('[Sentry web]', err);
  },
  captureMessage: (msg) => {
    if (typeof console !== 'undefined') console.warn('[Sentry web]', msg);
  },
  wrap: (App) => App,
  withScope: (cb) => {
    try {
      cb(scope);
    } catch (_) {
      /* ignore */
    }
  },
  setUser: noop,
  setTag: noop,
  setContext: noop,
  addBreadcrumb: noop,
  reactNavigationIntegration: () => ({
    registerNavigationContainer: noop,
  }),
  ReactNativeTracing: function ReactNativeTracing() {},
};

module.exports = {
  __esModule: true,
  default: Sentry,
  ...Sentry,
};
