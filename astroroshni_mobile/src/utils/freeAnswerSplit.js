/**
 * Split a free-question answer into quick card vs detailed sections for blur/reveal UX.
 * @returns {{ quick: string, detail: string, canBlur: boolean }}
 */
export function splitFreeAnswerContent(raw) {
  const s = String(raw || '');
  if (!s.trim()) {
    return { quick: '', detail: '', canBlur: false };
  }

  // Keep the response in its natural reading order. The free portion includes
  // any short preamble and the complete direct-answer card; only content after
  // that card is gated.
  const cardMatch = s.match(
    /<div\b[^>]*\bclass\s*=\s*["'][^"']*\bquick-answer-card\b[^"']*["'][^>]*>[\s\S]*?<\/div\s*>/i,
  );
  if (cardMatch && typeof cardMatch.index === 'number') {
    const boundary = cardMatch.index + cardMatch[0].length;
    const quick = s.slice(0, boundary).trim();
    const detail = s.slice(boundary).trim();
    return { quick, detail, canBlur: detail.length > 40 };
  }

  const headingMatch = s.match(
    /^\s*#{1,6}\s*(?:Quick Answer|Direct Answer|Short Answer|Bottom Line|Executive Summary|Answer)\b[^\n]*(?:\n|$)/im,
  );
  if (headingMatch && typeof headingMatch.index === 'number') {
    const sectionBodyStart = headingMatch.index + headingMatch[0].length;
    const remainder = s.slice(sectionBodyStart);
    const nextHeading = remainder.match(/^\s*#{1,6}\s+\S/im);
    const boundary = nextHeading && typeof nextHeading.index === 'number'
      ? sectionBodyStart + nextHeading.index
      : s.length;
    const quick = s.slice(0, boundary).trim();
    const detail = s.slice(boundary).trim();
    return { quick, detail, canBlur: detail.length > 40 };
  }

  // Some model responses preserve the required label but omit the wrapper.
  // Treat the next markdown heading as the start of paid detail.
  const labelMatch = s.match(
    /(?:\*\*|__)?(?:Quick Answer|Direct Answer|Short Answer|Bottom Line|Executive Summary|Daily Outlook)(?:\*\*|__)?\s*:/i,
  );
  if (labelMatch && typeof labelMatch.index === 'number') {
    const afterLabel = labelMatch.index + labelMatch[0].length;
    const remainder = s.slice(afterLabel);
    const nextHeading = remainder.match(/^\s*#{1,6}\s+\S/im);
    if (nextHeading && typeof nextHeading.index === 'number') {
      const boundary = afterLabel + nextHeading.index;
      const quick = s.slice(0, boundary).trim();
      const detail = s.slice(boundary).trim();
      return { quick, detail, canBlur: detail.length > 40 };
    }
  }

  return { quick: s, detail: '', canBlur: false };
}

export function freeDetailUnlockStorageKey(messageId) {
  return `free_detail_unlocked:${String(messageId || '')}`;
}

export function freeDetailRevealClickedStorageKey(messageId) {
  return `free_detail_reveal_clicked:${String(messageId || '')}`;
}
