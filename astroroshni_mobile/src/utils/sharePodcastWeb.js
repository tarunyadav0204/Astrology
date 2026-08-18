const audioBlobFromBase64 = (base64Audio) => {
  const binary = globalThis.atob(base64Audio);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return new Blob([bytes], { type: 'audio/mpeg' });
};

const downloadBlob = (blob, filename) => {
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.style.display = 'none';
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
};

/**
 * Share an authenticated podcast from the PWA without relying on expo-sharing,
 * which is unavailable on web. Browsers that cannot share files download the
 * MP3 instead, so the action always produces a useful result.
 */
export const sharePodcastBlobOnWeb = async (blob, filename) => {
  const file = typeof File === 'function'
    ? new File([blob], filename, { type: blob.type || 'audio/mpeg' })
    : null;
  const canShareFile = Boolean(
    file
    && globalThis.navigator?.share
    && globalThis.navigator?.canShare?.({ files: [file] }),
  );

  if (canShareFile) {
    try {
      await globalThis.navigator.share({
        files: [file],
        title: 'AstroRoshni Podcast',
      });
    } catch (error) {
      // Closing the operating-system share sheet is not an application error.
      if (error?.name === 'AbortError') return 'cancelled';
      throw error;
    }
    return 'shared';
  }

  downloadBlob(blob, filename);
  return 'downloaded';
};

export const sharePodcastBase64OnWeb = (base64Audio, filename) => (
  sharePodcastBlobOnWeb(audioBlobFromBase64(base64Audio), filename)
);
