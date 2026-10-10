/** Create a real PDF for browser sharing; browser print produces no shareable file. */
export async function renderShareablePdfOnWeb(html) {
  const { jsPDF } = await import('jspdf');
  const doc = new jsPDF({ unit: 'pt', format: 'a4' });
  await doc.html(html, {
    margin: [30, 30, 30, 30],
    width: 535,
    windowWidth: 820,
    autoPaging: 'text',
    html2canvas: { useCORS: true, backgroundColor: '#ffffff' },
  });
  return doc.output('blob');
}

export async function sharePdfBlobOnWeb(blob, options = {}) {
  const filename = `AstroRoshni-Prediction-${Date.now()}.pdf`;
  const file = new File([blob], filename, { type: 'application/pdf' });
  if (typeof navigator.share === 'function'
      && typeof navigator.canShare === 'function'
      && navigator.canShare({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: options.dialogTitle || 'AstroRoshni Prediction' });
      return;
    } catch (error) {
      if (error?.name === 'AbortError') return;
      // Async PDF rendering can consume the browser's user activation.
      // Provide the file as a download when opening the share sheet is denied.
      if (error?.name !== 'NotAllowedError') throw error;
    }
  }
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  try {
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
  } finally {
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }
}
