/** Split free-question answer into quick card vs detail for blur/reveal. */
export function splitFreeAnswerContent(raw) {
  const s = String(raw || '');
  if (!s.trim()) return { quick: '', detail: '', canBlur: false };

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
