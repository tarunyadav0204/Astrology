/** Web stub for expo-notifications (push is unsupported in v1 mobile-web). */
const Notifications = {
  setNotificationHandler: () => {},
  getPermissionsAsync: async () => ({ status: 'denied', granted: false }),
  requestPermissionsAsync: async () => ({ status: 'denied', granted: false }),
  getExpoPushTokenAsync: async () => ({ data: null }),
  addNotificationReceivedListener: () => ({ remove() {} }),
  addNotificationResponseReceivedListener: () => ({ remove() {} }),
  getLastNotificationResponseAsync: async () => null,
  setBadgeCountAsync: async () => false,
  scheduleNotificationAsync: async () => null,
  AndroidImportance: { MAX: 5, DEFAULT: 3 },
  IosAuthorizationStatus: { AUTHORIZED: 2, DENIED: 1, NOT_DETERMINED: 0 },
};

module.exports = {
  __esModule: true,
  default: Notifications,
  ...Notifications,
};
