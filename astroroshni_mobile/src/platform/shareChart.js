/**
 * Capture a RN View (DOM node on web) to a PNG blob and share/download it.
 * Native keeps using react-native-view-shot + expo-sharing.
 */
import { Platform, Alert } from 'react-native';
import * as Sharing from 'expo-sharing';

function resolveDomNode(ref) {
  let node = ref && (ref.current !== undefined ? ref.current : ref);
  if (!node) return null;
  if (typeof HTMLElement !== 'undefined' && node instanceof HTMLElement) {
    return node;
  }
  // react-native-web host instances
  if (node._nativeNode instanceof HTMLElement) return node._nativeNode;
  if (node.hostNode instanceof HTMLElement) return node.hostNode;
  if (typeof node.getNode === 'function') {
    try {
      const n = node.getNode();
      if (n instanceof HTMLElement) return n;
    } catch (_) {}
  }
  // Fallback: marked capture root (RN Web dataSet → data-ar-chart-capture)
  if (typeof document !== 'undefined') {
    return (
      document.getElementById('ar-chart-capture') ||
      document.querySelector('[data-ar-chart-capture="1"]') ||
      document.querySelector('[data-archartexapture="1"]')
    );
  }
  return null;
}

async function captureWebBlob(ref) {
  const { toBlob } = await import('html-to-image');
  const node = resolveDomNode(ref);
  if (!node) {
    throw new Error('Chart is not ready to share yet.');
  }
  const blob = await toBlob(node, {
    pixelRatio: Math.min(2, (typeof window !== 'undefined' && window.devicePixelRatio) || 2),
    cacheBust: true,
    backgroundColor: '#1a0033',
    // Skip portaled bottom nav / fixed UI if somehow nested
    filter: (el) => {
      if (!el || !el.tagName) return true;
      if (el.getAttribute && el.getAttribute('data-ar-skip-capture') === '1') return false;
      return true;
    },
  });
  if (!blob) {
    throw new Error('Could not create chart image.');
  }
  return blob;
}

async function shareOrDownloadWebBlob(blob, filename = 'astroroshni-chart.png') {
  const file = new File([blob], filename, { type: 'image/png' });
  try {
    if (typeof navigator !== 'undefined' && navigator.share) {
      if (!navigator.canShare || navigator.canShare({ files: [file] })) {
        await navigator.share({
          files: [file],
          title: 'AstroRoshni Chart',
          text: 'My cosmic blueprint from AstroRoshni',
        });
        return;
      }
    }
  } catch (err) {
    // User cancel should not show error
    if (err && (err.name === 'AbortError' || err.name === 'NotAllowedError')) {
      return;
    }
    // Fall through to download
  }

  const url = URL.createObjectURL(blob);
  try {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.rel = 'noopener';
    document.body.appendChild(a);
    a.click();
    a.remove();
  } finally {
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

/**
 * Capture the chart view and open the system share sheet (or download on web fallback).
 */
export async function shareCapturedChart(captureViewRef) {
  if (Platform.OS === 'web') {
    const blob = await captureWebBlob(captureViewRef);
    await shareOrDownloadWebBlob(blob);
    return;
  }

  const { captureRef } = require('react-native-view-shot');
  const uri = await captureRef(captureViewRef, {
    format: 'png',
    quality: 0.8,
  });
  const available = await Sharing.isAvailableAsync();
  if (!available) {
    throw new Error('Sharing is not available on this device.');
  }
  await Sharing.shareAsync(uri, {
    mimeType: 'image/png',
    dialogTitle: 'Share your Cosmic Blueprint',
    UTI: 'public.png',
  });
}

export function shareChartErrorMessage(error) {
  const msg = String(error?.message || error || '');
  if (/not available on web|Screenshot capture/i.test(msg)) {
    return 'Sharing is not supported in this browser yet.';
  }
  return 'Failed to share chart. Please try again.';
}

export function alertShareFailure(error) {
  console.error('Error sharing chart:', error);
  Alert.alert('Error', shareChartErrorMessage(error));
}
