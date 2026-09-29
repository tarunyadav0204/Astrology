import { Platform } from 'react-native';
import * as Sharing from 'expo-sharing';

function resolveDomNode(ref) {
  const node = ref?.current !== undefined ? ref.current : ref;
  if (!node) return null;
  if (typeof HTMLElement !== 'undefined' && node instanceof HTMLElement) return node;
  if (node._nativeNode instanceof HTMLElement) return node._nativeNode;
  if (node.hostNode instanceof HTMLElement) return node.hostNode;
  if (typeof node.getNode === 'function') {
    try {
      const inner = node.getNode();
      if (inner instanceof HTMLElement) return inner;
    } catch (_) { /* fall through */ }
  }
  return null;
}

async function shareWeb(ref, filename, title, text) {
  const { toBlob } = await import('html-to-image');
  const node = resolveDomNode(ref);
  if (!node) throw new Error('The share card is not ready yet.');
  const blob = await toBlob(node, {
    pixelRatio: Math.min(2, window.devicePixelRatio || 2),
    cacheBust: true,
    backgroundColor: '#260817',
  });
  if (!blob) throw new Error('Could not create the share card.');
  const file = new File([blob], filename, { type: 'image/png' });
  if (navigator.share && (!navigator.canShare || navigator.canShare({ files: [file] }))) {
    await navigator.share({ files: [file], title, text });
    return;
  }
  const url = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.rel = 'noopener';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

export async function sharePartnerPortraitCard(ref, format = 'story', options = {}) {
  const filename = `astroroshni-partner-portrait-${format}.png`;
  const title = options.title || 'My Partner Portrait from AstroRoshni';
  const text = options.text || 'One possible partner appearance suggested by my birth chart. Create yours with AstroRoshni.';
  if (Platform.OS === 'web') {
    await shareWeb(ref, filename, title, text);
    return;
  }
  const { captureRef } = require('react-native-view-shot');
  const uri = await captureRef(ref, { format: 'png', quality: 0.92, result: 'tmpfile' });
  if (!(await Sharing.isAvailableAsync())) throw new Error('Sharing is not available on this device.');
  await Sharing.shareAsync(uri, {
    mimeType: 'image/png',
    dialogTitle: title,
    UTI: 'public.png',
  });
}
