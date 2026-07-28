/** Lightweight PDF user-facing errors (no expo / native PDF deps). */

const PDF_EXPORT_DEFAULT_ERROR = 'We could not export the PDF. Please try again.';

export function userFacingPdfExportError(error) {
  const raw = error?.message || error?.detail || String(error || '');
  const msg = String(raw || '').trim();
  const lower = msg.toLowerCase();

  if (!msg) return PDF_EXPORT_DEFAULT_ERROR;
  if (lower.includes('timeout')) {
    return 'PDF generation took too long. Please try again.';
  }
  if (lower.includes('sharing is not available')) {
    return 'Sharing is not available on this device. Please try saving the PDF instead.';
  }
  if (
    lower.includes('destructure') ||
    lower.includes('undefined') ||
    lower.includes('null') ||
    lower.includes('not created')
  ) {
    return PDF_EXPORT_DEFAULT_ERROR;
  }
  if (lower.includes('network') || lower.includes('fetch failed') || lower.includes('failed to fetch')) {
    return 'Network error while creating the PDF. Check your connection and try again.';
  }
  if (lower.includes('traceback') || lower.includes('file "') || lower.includes('intermediate value')) {
    return PDF_EXPORT_DEFAULT_ERROR;
  }
  if (msg.length > 160) {
    return PDF_EXPORT_DEFAULT_ERROR;
  }
  return PDF_EXPORT_DEFAULT_ERROR;
}
