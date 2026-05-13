/**
 * Chat → PDF section drafts: same logical sections as web/mobile, without relying on
 * brittle "\\n\\n" blocks. Uses (1) optional DOM pass on markdown→<h3> when headings
 * survive formatting, and (2) ordered scans of known section labels in normalized plain
 * text (works when ### is wrapped in <p>… so formatChatMessageHtml never emits <h3>).
 */

import { formatChatMessageHtml } from './markdown';

/** @typedef {{ kind: string, title?: string, text?: string }} PdfSectionDraft */

/** Longer labels first so overlapping matches prefer the specific header. */
const SECTION_LABEL_SCAN = [
  ['Executive Summary:', 'quick_card', 'Executive Summary'],
  ['Astrological Analysis:', 'section_primary', 'Astrological Analysis'],
  ['Triple Perspective (Sudarshana):', 'section_secondary', 'Triple Perspective (Sudarshana)'],
  ['Ashtakavarga (SAV & BAV):', 'section_secondary', 'Ashtakavarga (SAV & BAV)'],
  ['Divisional Chart Analysis:', 'section_secondary', 'Divisional Chart Analysis'],
  ['KP Stellar Perspective:', 'section_secondary', 'KP Stellar Perspective'],
  ['Nadi Interpretation:', 'section_secondary', 'Nadi Interpretation'],
  ['The Planetary View:', 'section_secondary', 'The Planetary View'],
  ['The Parashari View:', 'section_secondary', 'The Parashari View'],
  ['Parashari View:', 'section_secondary', 'Parashari View'],
  ['The Jaimini View:', 'section_secondary', 'The Jaimini View'],
  ['Jaimini View:', 'section_secondary', 'Jaimini View'],
  ['Timing Through The Day:', 'section_primary', 'Timing Through The Day'],
  ['Guidance for the Day:', 'section_primary', 'Guidance for the Day'],
  ['Nakshatra Insights:', 'section_primary', 'Nakshatra Insights'],
  ['Timing & Guidance:', 'section_primary', 'Timing & Guidance'],
  ['Key Insights:', 'section_primary', 'Key Insights'],
  ['Daily Outlook:', 'quick_card', 'Daily Outlook'],
  ['Main Day Triggers:', 'section_primary', 'Main Day Triggers'],
  ['Final Verdict:', 'final_card', 'Final Verdict'],
  ['Final Thoughts:', 'final_card', 'Final Thoughts'],
  ['Quick Answer:', 'quick_card', 'Quick Answer'],
  ['KP View:', 'section_secondary', 'KP View'],
  ['Nadi View:', 'section_secondary', 'Nadi View'],
  ['Timing Synthesis:', 'section_secondary', 'Timing Synthesis'],
  ['What To Watch:', 'section_primary', 'What To Watch'],
  ['What To Use:', 'section_primary', 'What To Use'],
];

const PDF_SECTION_LABELS_FOR_NORMALIZE = [
  'Quick Answer:',
  'Executive Summary:',
  'Daily Outlook:',
  'Key Insights:',
  'Astrological Analysis:',
  'Nakshatra Insights:',
  'Timing & Guidance:',
  'Timing Through The Day:',
  'Guidance for the Day:',
  'Main Day Triggers:',
  'What To Use:',
  'What To Watch:',
  'Final Thoughts:',
  'Final Verdict:',
  'The Parashari View:',
  'The Planetary View:',
  'Ashtakavarga (SAV & BAV):',
  'The Jaimini View:',
  'KP Stellar Perspective:',
  'Nadi Interpretation:',
  'Timing Synthesis:',
  'Triple Perspective (Sudarshana):',
  'Divisional Chart Analysis:',
  'Parashari View:',
  'Jaimini View:',
  'Nadi View:',
  'KP View:',
];

const PDF_SUBSECTION_BREAK_LABELS = [
  'Triple Perspective (Sudarshana):',
  'Ashtakavarga (SAV & BAV):',
  'The Parashari View:',
  'The Planetary View:',
  'The Jaimini View:',
  'KP Stellar Perspective:',
  'Nadi Interpretation:',
  'Divisional Chart Analysis:',
  'Parashari View:',
  'Jaimini View:',
  'Nadi View:',
  'KP View:',
  'Timing Synthesis:',
];

function escapeRegex(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * So ### / ## headings can match ^### in formatChatMessageHtml after HTML wrappers.
 */
function prepareRawForMarkdownHeadings(raw) {
  let s = String(raw || '');
  s = s.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  s = s
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
  s = s.replace(/<p[^>]*>/gi, '\n');
  s = s.replace(/<\/p>/gi, '\n');
  s = s.replace(/<br\s*\/?>/gi, '\n');
  s = s.replace(/<\/(div|li|h[1-6]|blockquote)>/gi, '\n');
  s = s.replace(/([^\n])(#{1,6}\s)/g, '$1\n$2');
  return s.replace(/\n{3,}/g, '\n\n').trim();
}

function roughHtmlToPlain(html) {
  if (typeof window === 'undefined' || !window.DOMParser) {
    return String(html || '')
      .replace(/<[^>]+>/g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  }
  const d = new window.DOMParser().parseFromString(`<div class="chat-pdf-plain">${html}</div>`, 'text/html');
  const el = d.body.querySelector('.chat-pdf-plain');
  const t = (el && el.textContent) || '';
  return t.replace(/\r\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
}

/**
 * Same structural normalization as admin `normalizePdfSourceText` but starts from plain
 * (already stripped tags) so section labels get newlines before them.
 */
function normalizePlainForSectionScan(plainIn) {
  let plain = String(plainIn || '').trim();
  if (!plain) return '—';
  plain = plain
    .replace(/[\u200B-\u200D\uFEFF]/g, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    .replace(/^[\s\uFEFF]*#{1,6}\s*/gm, '')
    .replace(/\s+:\s+/g, ': ')
    .replace(/([a-z])([A-Z][a-z]+:)/g, '$1\n\n$2');
  const labelsSorted = [...PDF_SECTION_LABELS_FOR_NORMALIZE].sort((a, b) => b.length - a.length);
  for (const label of labelsSorted) {
    const esc = label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    plain = plain.replace(new RegExp(`([^\\n])(${esc})`, 'gi'), '$1\n\n$2');
  }
  const subSorted = [...PDF_SUBSECTION_BREAK_LABELS].sort((a, b) => b.length - a.length);
  for (const label of subSorted) {
    const esc = label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    plain = plain.replace(new RegExp(`\\n\\s*(${esc})`, 'gi'), '\n\n$1');
  }
  plain = plain
    .replace(/The Parashari View\s*-\s*/gi, 'The Parashari View:\n\n')
    .replace(/The Planetary View\s*-\s*/gi, 'The Planetary View:\n\n')
    .replace(/The Jaimini View\s*-\s*/gi, 'The Jaimini View:\n\n')
    .replace(/KP Stellar Perspective\s*-\s*/gi, 'KP Stellar Perspective:\n\n')
    .replace(/Nadi Interpretation\s*-\s*/gi, 'Nadi Interpretation:\n\n')
    .replace(/Timing Synthesis\s*-\s*/gi, 'Timing Synthesis:\n\n')
    .replace(/Divisional Chart Analysis\s*-\s*/gi, 'Divisional Chart Analysis:\n\n');
  plain = plain
    .replace(/(\n\s*){4,}/g, '\n\n\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
  return plain || '—';
}

function rawToNormalizedPlain(raw) {
  const prepared = prepareRawForMarkdownHeadings(raw);
  const html = formatChatMessageHtml(prepared);
  const rough = roughHtmlToPlain(html);
  return normalizePlainForSectionScan(rough);
}

/**
 * Find every section header in document order; body runs until the next header (any label).
 */
function extractSectionsByOrderedLabelMatches(plain) {
  const hits = [];
  for (const [label, kind, title] of SECTION_LABEL_SCAN) {
    const esc = escapeRegex(label);
    const re = new RegExp(`(^|[\\n\\r])\\s*(${esc})\\s*`, 'gi');
    let m;
    while ((m = re.exec(plain)) !== null) {
      const start = m.index + m[1].length;
      const end = m.index + m[0].length;
      hits.push({ at: start, end, kind, title, label });
    }
  }
  hits.sort((a, b) => a.at - b.at || b.label.length - a.label.length);
  const picked = [];
  for (const h of hits) {
    if (picked.some((p) => p.at === h.at)) continue;
    picked.push(h);
  }
  picked.sort((a, b) => a.at - b.at);

  if (picked.length === 0) {
    return null;
  }

  /** @type {PdfSectionDraft[]} */
  const sections = [];
  const pre = plain.slice(0, picked[0].at).trim();
  if (pre) sections.push({ kind: 'paragraph', text: pre });

  for (let i = 0; i < picked.length; i++) {
    const bodyStart = picked[i].end;
    const bodyEnd = i + 1 < picked.length ? picked[i + 1].at : plain.length;
    const text = plain.slice(bodyStart, bodyEnd).trim();
    sections.push({ kind: picked[i].kind, title: picked[i].title, text });
  }
  return sections;
}

const H3_TO_PDF = [
  { re: /^Quick Answer$/i, kind: 'quick_card', title: 'Quick Answer' },
  { re: /^Executive Summary$/i, kind: 'quick_card', title: 'Executive Summary' },
  { re: /^Daily Outlook$/i, kind: 'quick_card', title: 'Daily Outlook' },
  { re: /^Final Thoughts$/i, kind: 'final_card', title: 'Final Thoughts' },
  { re: /^Final Verdict$/i, kind: 'final_card', title: 'Final Verdict' },
  { re: /^The Parashari View$/i, kind: 'section_secondary', title: 'The Parashari View' },
  { re: /^The Planetary View$/i, kind: 'section_secondary', title: 'The Planetary View' },
  { re: /^Parashari View$/i, kind: 'section_secondary', title: 'Parashari View' },
  { re: /^Ashtakavarga \(SAV & BAV\)$/i, kind: 'section_secondary', title: 'Ashtakavarga (SAV & BAV)' },
  { re: /^The Jaimini View$/i, kind: 'section_secondary', title: 'The Jaimini View' },
  { re: /^Jaimini View$/i, kind: 'section_secondary', title: 'Jaimini View' },
  { re: /^KP Stellar Perspective$/i, kind: 'section_secondary', title: 'KP Stellar Perspective' },
  { re: /^KP View$/i, kind: 'section_secondary', title: 'KP View' },
  { re: /^Nadi Interpretation$/i, kind: 'section_secondary', title: 'Nadi Interpretation' },
  { re: /^Nadi View$/i, kind: 'section_secondary', title: 'Nadi View' },
  { re: /^Timing Synthesis$/i, kind: 'section_secondary', title: 'Timing Synthesis' },
  { re: /^Triple Perspective \(Sudarshana\)$/i, kind: 'section_secondary', title: 'Triple Perspective (Sudarshana)' },
  { re: /^Divisional Chart Analysis$/i, kind: 'section_secondary', title: 'Divisional Chart Analysis' },
  { re: /^Key Insights$/i, kind: 'section_primary', title: 'Key Insights' },
  { re: /^Astrological Analysis$/i, kind: 'section_primary', title: 'Astrological Analysis' },
  { re: /^Nakshatra Insights$/i, kind: 'section_primary', title: 'Nakshatra Insights' },
  { re: /^Timing & Guidance$/i, kind: 'section_primary', title: 'Timing & Guidance' },
  { re: /^Timing Through The Day$/i, kind: 'section_primary', title: 'Timing Through The Day' },
  { re: /^Guidance for the Day$/i, kind: 'section_primary', title: 'Guidance for the Day' },
  { re: /^Main Day Triggers$/i, kind: 'section_primary', title: 'Main Day Triggers' },
  { re: /^What To Use$/i, kind: 'section_primary', title: 'What To Use' },
  { re: /^What To Watch$/i, kind: 'section_primary', title: 'What To Watch' },
];

function normalizeH3Title(raw) {
  return String(raw || '')
    .replace(/\s+/g, ' ')
    .replace(/\s*:\s*$/, '')
    .trim();
}

function mapH3ToPdfSection(titleNorm) {
  for (const row of H3_TO_PDF) {
    if (row.re.test(titleNorm)) return { kind: row.kind, title: row.title };
  }
  return null;
}

function fragmentToPlainText(ownerDoc, fragment) {
  const w = ownerDoc.createElement('div');
  Array.from(fragment.childNodes).forEach((ch) => {
    try {
      w.appendChild(ch.cloneNode(true));
    } catch {
      /* ignore */
    }
  });
  const t = (w.innerText != null ? w.innerText : w.textContent) || '';
  return t.replace(/\r\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
}

function innerDivToPlain(ownerDoc, el) {
  const frag = ownerDoc.createDocumentFragment();
  Array.from(el.childNodes).forEach((ch) => frag.appendChild(ch.cloneNode(true)));
  return fragmentToPlainText(ownerDoc, frag);
}

function extractFromDomMarkersOnFormattedHtml(formatted) {
  if (typeof window === 'undefined' || !window.DOMParser) return null;
  const wrapped = `<div class="chat-pdf-root">${formatted}</div>`;
  const pdoc = new window.DOMParser().parseFromString(wrapped, 'text/html');
  const root = pdoc.body.querySelector('.chat-pdf-root');
  if (!root) return null;

  const markers = Array.from(
    root.querySelectorAll('h3, div.quick-answer-card, div.final-thoughts-card'),
  );
  if (markers.length === 0) return null;

  /** @type {PdfSectionDraft[]} */
  const sections = [];

  const rp = pdoc.createRange();
  rp.setStart(root, 0);
  rp.setEndBefore(markers[0]);
  const preText = fragmentToPlainText(pdoc, rp.cloneContents());
  if (preText) sections.push({ kind: 'paragraph', text: preText });

  for (let mi = 0; mi < markers.length; mi++) {
    const m = markers[mi];
    const next = markers[mi + 1] || null;

    if (m.nodeType === 1 && m.classList && m.classList.contains('quick-answer-card')) {
      sections.push({
        kind: 'quick_card',
        title: 'Quick Answer',
        text: innerDivToPlain(pdoc, m),
      });
      continue;
    }
    if (m.nodeType === 1 && m.classList && m.classList.contains('final-thoughts-card')) {
      sections.push({
        kind: 'final_card',
        title: 'Final Thoughts',
        text: innerDivToPlain(pdoc, m),
      });
      continue;
    }

    if (m.tagName && m.tagName.toLowerCase() === 'h3') {
      const titleNorm = normalizeH3Title(m.textContent || '');
      const mapped = mapH3ToPdfSection(titleNorm);
      const r = pdoc.createRange();
      r.setStartAfter(m);
      if (next) r.setEndBefore(next);
      else {
        const last = root.lastChild;
        if (last) r.setEndAfter(last);
        else r.setEndAfter(m);
      }
      const bodyPlain = fragmentToPlainText(pdoc, r.cloneContents());

      if (mapped) {
        sections.push({ kind: mapped.kind, title: mapped.title, text: bodyPlain });
      } else if (bodyPlain) {
        sections.push({ kind: 'section_primary', title: titleNorm, text: bodyPlain });
      } else {
        sections.push({ kind: 'heading', text: titleNorm });
      }
    }
  }

  return sections.length ? sections : null;
}

/**
 * Single entry for admin PDF (and any caller): never returns null — at least one section.
 * Prefers ordered label scan on normalized plain text; supplements with DOM markers when useful.
 */
export function extractChatSectionDrafts(raw) {
  const normalizedPlain = rawToNormalizedPlain(raw);

  const byLabels = extractSectionsByOrderedLabelMatches(normalizedPlain);
  const prepared = prepareRawForMarkdownHeadings(raw);
  const formattedHtml = formatChatMessageHtml(prepared);
  const byDom = extractFromDomMarkersOnFormattedHtml(formattedHtml);

  /** Prefer label scan whenever it found structured sections (matches real chat templates). */
  if (byLabels && byLabels.length) {
    return byLabels;
  }
  if (byDom && byDom.length) {
    return byDom;
  }
  return [{ kind: 'paragraph', text: normalizedPlain || '—' }];
}

/** @deprecated use extractChatSectionDrafts */
export function extractChatSectionsFromMessageHtml(raw) {
  const prepared = prepareRawForMarkdownHeadings(raw);
  const formatted = formatChatMessageHtml(prepared).trim();
  if (!formatted) return null;
  return extractFromDomMarkersOnFormattedHtml(formatted);
}
