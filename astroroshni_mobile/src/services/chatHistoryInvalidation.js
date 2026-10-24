// Chat History and ChatScreen can both remain mounted in the navigation stack.
// Keep this in-process signal deliberately small so deleting history clears the
// active screen immediately, rather than waiting for a remount or app restart.
const listeners = new Set();

export const subscribeToChatHistoryInvalidation = (listener) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};

export const invalidateChatHistory = () => {
  listeners.forEach((listener) => {
    try {
      listener();
    } catch (_) {
      // A screen being unmounted must not prevent other chat screens from
      // receiving the invalidation.
    }
  });
};
