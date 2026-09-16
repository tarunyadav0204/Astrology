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

const cleanDetailHeading = (value) => String(value || '')
  .replace(/<[^>]+>/g, ' ')
  .replace(/[*_`#]+/g, '')
  .replace(/\s+/g, ' ')
  .replace(/\s*:\s*$/, '')
  .trim();

/**
 * Pull the real section names out of the gated portion of a free answer.
 * Answers can contain markdown headings, HTML headings, or labelled cards.
 * Returning the authored labels keeps the purchase promise relevant to the
 * user's question instead of hard-coding timing or another specific outcome.
 */
export function extractFreeAnswerDetailHeadings(raw, limit = 3) {
  const source = String(raw || '');
  if (!source.trim()) return [];

  const candidates = [];
  const collect = (pattern, group = 1) => {
    let match;
    while ((match = pattern.exec(source)) !== null) {
      candidates.push(match[group]);
    }
  };

  collect(/^\s*#{1,6}\s+([^\n]+)/gim);
  collect(/<h[1-6]\b[^>]*>([\s\S]*?)<\/h[1-6]\s*>/gim);
  collect(/(?:^|\n)\s*(?:\*\*|__)([^\n:*_][^\n]*?)(?:\*\*|__)\s*:/gim);

  const excluded = /^(?:quick answer|direct answer|short answer|bottom line|executive summary|daily outlook|answer)$/i;
  const unique = [];
  for (const candidate of candidates) {
    const heading = cleanDetailHeading(candidate);
    if (!heading || heading.length > 72 || excluded.test(heading)) continue;
    if (unique.some((item) => item.toLocaleLowerCase() === heading.toLocaleLowerCase())) continue;
    unique.push(heading);
    if (unique.length >= Math.max(1, Number(limit) || 3)) break;
  }
  return unique;
}

export function freeDetailUnlockStorageKey(messageId) {
  return `free_detail_unlocked:${String(messageId || '')}`;
}

export function freeDetailRevealClickedStorageKey(messageId) {
  return `free_detail_reveal_clicked:${String(messageId || '')}`;
}
