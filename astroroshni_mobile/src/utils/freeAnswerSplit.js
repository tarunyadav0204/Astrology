/**
 * Split a free-question answer into quick card vs detailed sections for blur/reveal UX.
 * @returns {{ quick: string, detail: string, canBlur: boolean }}
 */
export function splitFreeAnswerContent(raw) {
  const s = String(raw || '');
  if (!s.trim()) {
    return { quick: '', detail: '', canBlur: false };
  }

  const cardMatch = s.match(/<div class=["']quick-answer-card["']>[\s\S]*?<\/div>/i);
  if (cardMatch && typeof cardMatch.index === 'number') {
    const quick = cardMatch[0];
    const detail = `${s.slice(0, cardMatch.index)}${s.slice(cardMatch.index + quick.length)}`.trim();
    return { quick, detail, canBlur: detail.length > 40 };
  }

  const headingMatch = s.match(
    /###\s*(?:Quick Answer|Direct Answer|Short Answer|Bottom Line|Answer)\b[\s\S]*?(?=###|$)/i,
  );
  if (headingMatch && typeof headingMatch.index === 'number') {
    const quick = headingMatch[0];
    const detail = `${s.slice(0, headingMatch.index)}${s.slice(headingMatch.index + quick.length)}`.trim();
    return { quick, detail, canBlur: detail.length > 40 };
  }

  return { quick: s, detail: '', canBlur: false };
}

export function freeDetailUnlockStorageKey(messageId) {
  return `free_detail_unlocked:${String(messageId || '')}`;
}

export function freeDetailRevealClickedStorageKey(messageId) {
  return `free_detail_reveal_clicked:${String(messageId || '')}`;
}
