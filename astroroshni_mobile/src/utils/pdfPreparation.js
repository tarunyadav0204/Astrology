/** Bound preparation work and clear timers when it finishes. */
export async function withPdfTimeout(operation, timeoutMs, message = 'PDF generation timeout') {
  let timer;
  try {
    return await Promise.race([
      Promise.resolve().then(operation),
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error(message)), timeoutMs);
      }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

/** The preparation indicator must not depend on the native share dialog closing. */
export async function prepareAndSharePdf({ prepare, share, setPreparing, timeoutMs = 60000 }) {
  let uri;
  setPreparing(true);
  try {
    uri = await withPdfTimeout(prepare, timeoutMs);
  } finally {
    setPreparing(false);
  }
  await share(uri);
}
