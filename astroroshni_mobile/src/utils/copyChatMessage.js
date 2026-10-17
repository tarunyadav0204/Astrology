export const copyableChatText = (content, role) => {
  const text = String(content ?? '');
  if (role === 'user') return text;
  return text
    .replace(/<br\s*\/?\s*>/gi, '\n')
    .replace(/<\/(?:p|div|li|h[1-6])>/gi, '\n')
    .replace(/<[^>]*>/g, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/•\s*/g, '• ')
    .trim();
};

// Expo may reject a clipboard write on a device even when the core native
// clipboard is available. Both APIs write only; never read private clipboard data.
export async function copyChatMessage(content, role, primaryWrite, fallbackWrite) {
  const text = copyableChatText(content, role);
  if (!text.trim()) throw new Error('No message text to copy');
  try {
    const result = await primaryWrite(text);
    if (result === false) throw new Error('Clipboard write was not accepted');
  } catch (error) {
    if (!fallbackWrite) throw error;
    const result = await fallbackWrite(text);
    if (result === false) throw new Error('Clipboard fallback was not accepted');
  }
}
