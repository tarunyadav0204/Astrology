/** Web stub — store review prompts are native-only. */
async function isAvailableAsync() {
  return false;
}
async function requestReview() {
  return false;
}
async function hasAction() {
  return false;
}

module.exports = {
  __esModule: true,
  default: { isAvailableAsync, requestReview, hasAction },
  isAvailableAsync,
  requestReview,
  hasAction,
};
