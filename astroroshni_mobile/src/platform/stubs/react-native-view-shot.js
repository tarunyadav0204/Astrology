/** Web stub — view-shot is not available in browsers. */
async function captureRef() {
  throw new Error('Screenshot capture is not available on web.');
}
async function captureScreen() {
  throw new Error('Screenshot capture is not available on web.');
}

module.exports = {
  __esModule: true,
  default: { captureRef, captureScreen },
  captureRef,
  captureScreen,
};
