import React, { useState, useEffect, useMemo } from 'react';
import { jsPDF } from 'jspdf';
import { getAdminAuthHeaders } from '../../services/adminService';
import { formatChatMessageHtml as formatMessageContent } from '../../utils/markdown';
import { extractChatSectionDrafts } from '../../utils/chatPdfSections';
import './AdminChatHistory.css';

const USER_PAGE_SIZE = 10;
const SESSION_MESSAGE_PAGE_SIZE = 20;

const formatCompactNumber = (value) => {
  const n = Number(value);
  if (!Number.isFinite(n)) return '—';
  return n.toLocaleString('en-IN');
};

const formatInr = (value) => {
  const n = Number(value);
  if (!Number.isFinite(n)) return '—';
  return `₹${n.toLocaleString('en-IN', {
    maximumFractionDigits: n >= 100 ? 0 : 2,
  })}`;
};

/** Labels that often sit on a single newline after "Astrological Analysis" — force block boundaries. */
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
 * Model replies often glue bullets and subheads on one line (e.g. "end.- Next Insight"
 * or "The Parashari View- text"). Break those apart before parseBodyIntoFlow.
 */
function preprocessPdfSectionBody(title, text) {
  let t = String(text ?? '').replace(/\r\n/g, '\n');
  if (!t.trim()) return t;

  const tl = String(title || '');

  // Common Key Insights pattern: period then hyphen then next titled phrase
  t = t.replace(/\.\s*-\s+(?=[A-Z0-9])/g, '.\n\n- ');
  t = t.replace(/\.\s+-\s+(?=[A-Z0-9])/g, '.\n\n- ');
  // "word - Capitalized" insight separators (not single-letter words)
  t = t.replace(/([a-z]{2,})\s+-\s+(?=[A-Z][a-z]{3,})/g, '$1\n\n- ');

  // Inline numbered steps: " ... 1. Verb" / " ... 2. Verb"
  t = t.replace(/(\s)([1-9]\d?\.\s+[A-Z])/g, '$1\n\n$2');

  // Long final paragraphs: new thought after semicolon + capital
  t = t.replace(/;\s+(?=[A-Z])/g, ';\n\n');

  // Subsection / label lines embedded without newlines (skip repeating own card title)
  const embeddedHeads = [
    'Triple Perspective (Sudarshana)',
    'Ashtakavarga (SAV & BAV)',
    'The Parashari View',
    'The Planetary View',
    'The Jaimini View',
    'KP Stellar Perspective',
    'Nadi Interpretation',
    'Timing Synthesis',
    'Divisional Chart Analysis',
    'Nakshatra Insights',
    'Timing & Guidance',
  ].sort((a, b) => b.length - a.length);

  for (const h of embeddedHeads) {
    if (tl && h.toLowerCase() === tl.toLowerCase()) continue;
    const esc = escapeRegex(h);
    t = t.replace(new RegExp(`([^\\n])\\s*(${esc})\\s*[:.\-]`, 'gi'), '$1\n\n$2');
  }

  return t.replace(/\n{3,}/g, '\n\n').trim();
}

/** Match secondary chunks after split when strict "Label:" regex fails (dash titles, etc.). */
const PDF_SECONDARY_RELAXED = [
  { re: /^The Planetary View\s*[:.\-]\s*/i, title: 'The Planetary View' },
  { re: /^The Parashari View\s*[:.\-]\s*/i, title: 'The Parashari View' },
  { re: /^Parashari View\s*[:.\-]\s*/i, title: 'Parashari View' },
  { re: /^Ashtakavarga\s*\(SAV\s*&\s*BAV\)\s*[:.\-]?\s*/i, title: 'Ashtakavarga (SAV & BAV)' },
  { re: /^The Jaimini View\s*[:.\-]\s*/i, title: 'The Jaimini View' },
  { re: /^Jaimini View\s*[:.\-]\s*/i, title: 'Jaimini View' },
  { re: /^KP Stellar Perspective\s*[:.\-]\s*/i, title: 'KP Stellar Perspective' },
  { re: /^KP View\s*[:.\-]\s*/i, title: 'KP View' },
  { re: /^Nadi Interpretation\s*[:.\-]\s*/i, title: 'Nadi Interpretation' },
  { re: /^Nadi View\s*[:.\-]\s*/i, title: 'Nadi View' },
  { re: /^Timing Synthesis\s*[:.\-]\s*/i, title: 'Timing Synthesis' },
  { re: /^Triple Perspective\s*\(Sudarshana\)\s*[:.\-]?\s*/i, title: 'Triple Perspective (Sudarshana)' },
  { re: /^Divisional Chart Analysis\s*[:.\-]\s*/i, title: 'Divisional Chart Analysis' },
];

const AST_ANALYSIS_SUB_SPLIT =
  /(?=The Parashari View\s*[:.\-]|The Planetary View\s*[:.\-]|The Jaimini View\s*[:.\-]|Ashtakavarga\s*\(SAV\s*&\s*BAV\)|KP Stellar Perspective\s*[:.\-]|Nadi Interpretation\s*[:.\-]|Timing Synthesis\s*[:.\-]|Triple Perspective\s*\(Sudarshana\)\s*[:.\-]|Divisional Chart Analysis\s*[:.\-])/i;

/** Inline subsection titles inside one card (styled in drawPdfBodyFlow). */
const PDF_SUBHEADING_INLINE =
  /^(The Parashari View|The Planetary View|The Jaimini View|Ashtakavarga\s*\(SAV\s*&\s*BAV\)|KP Stellar Perspective|Nadi Interpretation|Timing Synthesis|Triple Perspective\s*\(Sudarshana\)|Divisional Chart Analysis)\s*[:.\-]\s*(.+)$/i;

function isStandalonePdfSubheadingLine(t) {
  return /^(The Parashari View|The Planetary View|The Jaimini View|Ashtakavarga\s*\(SAV\s*&\s*BAV\)|KP Stellar Perspective|Nadi Interpretation|Timing Synthesis|Triple Perspective\s*\(Sudarshana\)|Divisional Chart Analysis)\s*[:.\-]?\s*$/i.test(
    t,
  );
}

/**
 * Turn plain section text into flow blocks so jsPDF height matches content
 * (avoids one giant splitTextToSize on strings with many newlines).
 */
function parseBodyIntoFlow(text) {
  const raw = String(text || '')
    .replace(/\r\n/g, '\n')
    .replace(/[ \t]+$/gm, '')
    .trim();
  if (!raw) return [{ type: 'p', text: '—' }];

  const flow = [];
  let ul = [];
  let ol = [];
  let paraLines = [];

  const flushUl = () => {
    if (ul.length) {
      flow.push({ type: 'ul', items: ul.slice() });
      ul = [];
    }
  };
  const flushOl = () => {
    if (ol.length) {
      flow.push({ type: 'ol', items: ol.slice() });
      ol = [];
    }
  };
  const flushPara = () => {
    flushUl();
    flushOl();
    if (paraLines.length) {
      flow.push({ type: 'p', text: paraLines.join('\n') });
      paraLines = [];
    }
  };

  const lines = raw.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const t = lines[i].trim();
    if (!t) {
      flushPara();
      continue;
    }
    const bullet = /^[•\-]\s+(.+)$/.exec(t);
    const astList = /^\*\s+(.+)$/.exec(t);
    const num = /^(\d{1,3})[.)]\s+(.+)$/.exec(t);
    if (bullet) {
      flushPara();
      flushOl();
      ul.push(bullet[1].trim());
    } else if (astList && !t.startsWith('**')) {
      flushPara();
      flushOl();
      ul.push(astList[1].trim());
    } else if (num) {
      flushPara();
      flushUl();
      ol.push(num[2].trim());
    } else {
      const inlineSh = t.match(PDF_SUBHEADING_INLINE);
      if (inlineSh) {
        flushPara();
        flushUl();
        flushOl();
        flow.push({ type: 'subheading', text: inlineSh[1].trim() });
        const rest = (inlineSh[2] || '').trim();
        if (rest) paraLines.push(rest);
      } else if (isStandalonePdfSubheadingLine(t)) {
        flushPara();
        flushUl();
        flushOl();
        flow.push({ type: 'subheading', text: t.replace(/\s*[:.\-]\s*$/i, '').trim() });
      } else {
        flushUl();
        flushOl();
        paraLines.push(t);
      }
    }
  }
  flushPara();
  return flow.length ? flow : [{ type: 'p', text: raw }];
}

function attachBodyFlowToPdfSections(sections) {
  sections.forEach((s) => {
    if (s.kind === 'bullet_group' && Array.isArray(s.items)) {
      s.bodyFlow = [{ type: 'ul', items: s.items.slice() }];
      return;
    }
    if (s.text != null && s.kind !== 'heading') {
      s.bodyFlow = parseBodyIntoFlow(s.text);
    }
  });
  return sections;
}

function measurePdfBodyFlow(doc, flow, innerTextW, bodyLineMm) {
  const badgeW = 4.5;
  const listTextW = Math.max(20, innerTextW - badgeW - 5);
  const paraGap = 2.5;
  let h = 0;
  doc.setFontSize(10);
  doc.setFont(undefined, 'normal');
  (flow || []).forEach((b) => {
    if (b.type === 'p') {
      const lines = doc.splitTextToSize(String(b.text || '—').replace(/\r/g, ''), innerTextW);
      h += Math.max(lines.length, 1) * bodyLineMm + paraGap;
    } else if (b.type === 'ul' || b.type === 'ol') {
      (b.items || []).forEach((item) => {
        const lines = doc.splitTextToSize(String(item || '—'), listTextW);
        h += Math.max(lines.length, 1) * bodyLineMm + 2;
      });
      h += 2;
    }
  });
  return h;
}

/** Split flow at subheadings so each segment can be its own PDF card (subheading is first line inside the new card). */
function partitionBodyFlowAtSubheadings(flow) {
  const f = Array.isArray(flow) ? flow : [];
  if (!f.some((b) => b.type === 'subheading')) {
    return [{ subTitle: null, blocks: f.slice() }];
  }
  const parts = [];
  let pending = null;
  let buf = [];
  const flush = () => {
    if (!buf.length && pending === null) return;
    /* Never emit a segment with no blocks (e.g. two subheadings back-to-back). That produced a
     * tiny "header-only" card and the real body started in the next partition / page. */
    if (buf.length) {
      parts.push({ subTitle: pending, blocks: buf.slice() });
    }
    buf = [];
  };
  f.forEach((b) => {
    if (b.type === 'subheading') {
      flush();
      pending = b.text;
    } else {
      buf.push(b);
    }
  });
  flush();
  return parts.length ? parts : [{ subTitle: null, blocks: f.slice() }];
}

function measurePdfSubTitleBlock(doc, subTitle, innerTextW) {
  if (!subTitle) return 0;
  doc.setFontSize(10);
  doc.setFont(undefined, 'bold');
  const lines = doc.splitTextToSize(String(subTitle), innerTextW);
  doc.setFont(undefined, 'normal');
  return Math.max(lines.length, 1) * 5.8 + 3;
}

/**
 * @returns {number} baseline Y after last drawn line (mm)
 */
function drawPdfBodyFlow(doc, flow, opts) {
  const {
    textX, innerTextW, bodyLineMm, startY, badge, listTextX, listTextW,
  } = opts;
  let ty = startY;
  const paraGap = 2.5;
  doc.setFontSize(10);
  doc.setFont(undefined, 'normal');
  doc.setTextColor(44, 62, 80);
  (flow || []).forEach((b) => {
    if (b.type === 'p') {
      const lines = doc.splitTextToSize(String(b.text || '—').replace(/\r/g, ''), innerTextW);
      lines.forEach((ln) => {
        doc.text(ln, textX, ty);
        ty += bodyLineMm;
      });
      ty += paraGap;
    } else if (b.type === 'ul') {
      (b.items || []).forEach((item) => {
        const lines = doc.splitTextToSize(String(item || '—'), listTextW);
        const rowStart = ty;
        doc.setFillColor(255, 107, 53);
        doc.rect(textX - 0.5, rowStart - 3.5, badge, badge, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(8);
        doc.setFont(undefined, 'bold');
        doc.text('-', textX - 0.5 + (badge - doc.getTextWidth('-')) / 2, rowStart + 0.5);
        doc.setFont(undefined, 'normal');
        doc.setFontSize(10);
        doc.setTextColor(44, 62, 80);
        lines.forEach((ln) => {
          doc.text(ln, listTextX, ty);
          ty += bodyLineMm;
        });
        ty += 2;
      });
      ty += 2;
    } else if (b.type === 'ol') {
      let n = 1;
      (b.items || []).forEach((item) => {
        const lines = doc.splitTextToSize(String(item || '—'), listTextW);
        const rowStart = ty;
        doc.setFillColor(255, 107, 53);
        doc.rect(textX - 0.5, rowStart - 3.5, badge, badge, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(7.5);
        doc.setFont(undefined, 'bold');
        const ns = String(n);
        doc.text(ns, textX - 0.5 + (badge - doc.getTextWidth(ns)) / 2, rowStart + 0.5);
        n += 1;
        doc.setFont(undefined, 'normal');
        doc.setFontSize(10);
        doc.setTextColor(44, 62, 80);
        lines.forEach((ln) => {
          doc.text(ln, listTextX, ty);
          ty += bodyLineMm;
        });
        ty += 2;
      });
      ty += 2;
    }
  });
  return ty;
}

const AdminChatHistory = () => {
  const [userRows, setUserRows] = useState([]);
  const [listPage, setListPage] = useState(1);
  const [listTotal, setListTotal] = useState(0);
  const [listTotalPages, setListTotalPages] = useState(0);
  const [listHasMore, setListHasMore] = useState(false);
  const [selectedSession, setSelectedSession] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [sessionMsgLoading, setSessionMsgLoading] = useState(false);
  const [userValueSnapshot, setUserValueSnapshot] = useState(null);
  const [userValueLoading, setUserValueLoading] = useState(false);
  const [userValueError, setUserValueError] = useState('');
  const [pricePanelExpanded, setPricePanelExpanded] = useState(false);
  const [valuePanelExpanded, setValuePanelExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [sessionQuery, setSessionQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [branchModal, setBranchModal] = useState({
    open: false,
    loading: false,
    error: '',
    messageId: null,
    payload: null,
  });
  const [qaModal, setQaModal] = useState({
    open: false,
    loading: false,
    phase: null, // 'load' | 'run' | null
    error: '',
    messageId: null,
    adminNotes: '',
    result: null,
  });
  const [pdfMessageId, setPdfMessageId] = useState(null);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(sessionQuery.trim()), 400);
    return () => clearTimeout(t);
  }, [sessionQuery]);

  useEffect(() => {
    setListPage(1);
  }, [debouncedQuery]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          page: String(listPage),
          limit: String(USER_PAGE_SIZE),
        });
        if (debouncedQuery) params.set('q', debouncedQuery);
        const response = await fetch(`/api/admin/chat/users?${params.toString()}`, {
          headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
        });
        if (!response.ok || cancelled) {
          if (!cancelled) {
            const errText = await response.text().catch(() => '');
            console.error('Error fetching chat users:', response.status, errText);
            setUserRows([]);
            setListTotal(0);
            setListTotalPages(0);
            setListHasMore(false);
          }
          return;
        }
        const data = await response.json();
        if (cancelled) return;
        setUserRows(Array.isArray(data.users) ? data.users : []);
        setListTotal(Number(data.total) || 0);
        setListTotalPages(Number(data.total_pages) || 0);
        setListHasMore(Boolean(data.has_more));
      } catch (error) {
        if (!cancelled) console.error('Error fetching chat users:', error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [listPage, debouncedQuery]);

  const fetchSessionDetails = async (userId, page = 1) => {
    try {
      setSessionMsgLoading(true);
      const params = new URLSearchParams({
        page: String(page),
        limit: String(SESSION_MESSAGE_PAGE_SIZE),
      });
      const response = await fetch(`/api/admin/chat/user-thread/${userId}?${params.toString()}`, {
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedUserId(userId);
        setSelectedSession(data);
        setPricePanelExpanded(false);
        setValuePanelExpanded(false);
      }
    } catch (error) {
      console.error('Error fetching user thread:', error);
    } finally {
      setSessionMsgLoading(false);
    }
  };

  useEffect(() => {
    if (selectedUserId == null) {
      setUserValueSnapshot(null);
      setUserValueError('');
      setUserValueLoading(false);
      return undefined;
    }

    let cancelled = false;
    const loadUserValueSnapshot = async () => {
      setUserValueLoading(true);
      setUserValueError('');
      try {
        const response = await fetch(`/api/admin/chat/user-value-summary/${selectedUserId}`, {
          headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
        });
        if (!response.ok) {
          const errText = await response.text().catch(() => '');
          throw new Error(errText || `Failed (${response.status})`);
        }
        const data = await response.json();
        if (!cancelled) setUserValueSnapshot(data);
      } catch (error) {
        if (!cancelled) {
          console.error('Error fetching user value summary:', error);
          setUserValueSnapshot(null);
          setUserValueError('Could not load user snapshot');
        }
      } finally {
        if (!cancelled) setUserValueLoading(false);
      }
    };

    loadUserValueSnapshot();
    return () => {
      cancelled = true;
    };
  }, [selectedUserId]);

  const closeBranchModal = () => {
    setBranchModal({
      open: false,
      loading: false,
      error: '',
      messageId: null,
      payload: null,
    });
  };

  const stripBranchNoise = (txt) => {
    if (!txt) return '';
    return String(txt)
      .replace(/\[LLM_ROUNDTRIP:[^\]]+\][^\n]*\n?/g, '')
      .replace(/===== REQUEST part [^\n]*\n?/g, '')
      .trim();
  };

  const getBranchTitle = (key) => {
    const titles = {
      parashari: 'Parashari',
      jaimini: 'Jaimini',
      nadi: 'Nadi',
      nakshatra: 'Nakshatra',
      kp: 'KP',
      ashtakavarga: 'Ashtakavarga',
      sudarshan: 'Sudarshan Chakra',
    };
    return titles[key] || String(key || '').replace(/^\w/, (c) => c.toUpperCase());
  };

  const openBranchAnalysis = async (messageId) => {
    if (!messageId) return;
    setBranchModal({
      open: true,
      loading: true,
      error: '',
      messageId,
      payload: null,
    });
    try {
      const response = await fetch(`/api/admin/chat/branch-analysis/${messageId}`, {
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
      });
      if (!response.ok) {
        const t = await response.text().catch(() => '');
        throw new Error(t || `Failed (${response.status})`);
      }
      const data = await response.json();
      setBranchModal({
        open: true,
        loading: false,
        error: '',
        messageId,
        payload: data?.specialist_branch_outputs || null,
      });
    } catch (e) {
      setBranchModal({
        open: true,
        loading: false,
        error: String(e?.message || 'Failed to load branch analysis'),
        messageId,
        payload: null,
      });
    }
  };

  const closeQaModal = () => {
    setQaModal({
      open: false,
      loading: false,
      phase: null,
      error: '',
      messageId: null,
      adminNotes: '',
      result: null,
    });
  };

  const openResponseQa = async (messageId) => {
    if (!messageId) return;
    setQaModal({
      open: true,
      loading: true,
      phase: 'load',
      error: '',
      messageId,
      adminNotes: '',
      result: null,
    });
    try {
      const response = await fetch(`/api/admin/chat/response-qa/${messageId}`, {
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
      });
      if (!response.ok) {
        const t = await response.text().catch(() => '');
        throw new Error(t || `Failed (${response.status})`);
      }
      const data = await response.json();
      if (data?.found && data?.report) {
        setQaModal({
          open: true,
          loading: false,
          phase: null,
          error: '',
          messageId,
          adminNotes: data.admin_notes || '',
          result: data,
        });
        return;
      }
      setQaModal({
        open: true,
        loading: false,
        phase: null,
        error: '',
        messageId,
        adminNotes: '',
        result: null,
      });
    } catch (e) {
      setQaModal({
        open: true,
        loading: false,
        phase: null,
        error: '',
        messageId,
        adminNotes: '',
        result: null,
      });
      console.error('Failed loading stored Astrology QA:', e);
    }
  };

  const runResponseQa = async () => {
    const messageId = qaModal.messageId;
    if (!messageId) return;
    setQaModal((prev) => ({
      ...prev,
      loading: true,
      phase: 'run',
      error: '',
      result: null,
    }));
    try {
      const response = await fetch(`/api/admin/chat/response-qa/${messageId}`, {
        method: 'POST',
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          admin_notes: qaModal.adminNotes || '',
          include_prior_turns: 8,
        }),
      });
      if (!response.ok) {
        const t = await response.text().catch(() => '');
        let detail = t || `Failed (${response.status})`;
        try {
          const parsed = JSON.parse(t);
          if (parsed?.detail) detail = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
        } catch (_) {
          /* keep raw */
        }
        throw new Error(detail);
      }
      const data = await response.json();
      setQaModal((prev) => ({
        ...prev,
        loading: false,
        phase: null,
        error: '',
        result: data,
        adminNotes: data?.admin_notes || prev.adminNotes || '',
      }));
    } catch (e) {
      setQaModal((prev) => ({
        ...prev,
        loading: false,
        phase: null,
        error: String(e?.message || 'Failed to run astrology QA'),
        result: null,
      }));
    }
  };

  const severityClass = (sev) => {
    const s = String(sev || '').toLowerCase();
    if (s === 'critical') return 'admin-qa-sev--critical';
    if (s === 'high') return 'admin-qa-sev--high';
    if (s === 'medium') return 'admin-qa-sev--medium';
    return 'admin-qa-sev--low';
  };

  const gradeClass = (grade) => {
    const g = String(grade || '').toUpperCase();
    if (g === 'A' || g === 'B') return 'admin-qa-grade--good';
    if (g === 'C') return 'admin-qa-grade--mid';
    return 'admin-qa-grade--bad';
  };

  const IST = 'Asia/Kolkata';

  const parseUtcTimestamp = (dateStr) => {
    if (!dateStr) return null;
    const raw = String(dateStr).trim();
    if (!raw) return null;
    // Admin APIs return absolute UTC timestamps; older rows may still arrive
    // without a timezone suffix, so default naive values to UTC before IST formatting.
    const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(raw);
    const normalized = hasTimezone ? raw : `${raw.replace(' ', 'T')}Z`;
    const d = new Date(normalized);
    return Number.isNaN(d.getTime()) ? null : d;
  };

  const formatDate = (dateStr) => {
    const d = parseUtcTimestamp(dateStr);
    if (!d) return '—';
    return d.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: IST
    }) + ' IST';
  };

  const messageSortTime = (msg) => parseUtcTimestamp(msg?.timestamp)?.getTime() || 0;

  /** When timestamps tie (e.g. same IST minute), order user before assistant; then by message_id. */
  const senderChronologicalRank = (sender) => {
    const k = String(sender || '').toLowerCase();
    if (k === 'user') return 0;
    if (k === 'assistant') return 1;
    return 2;
  };

  const compareMessagesChronological = (a, b) => {
    const ta = messageSortTime(a);
    const tb = messageSortTime(b);
    if (ta !== tb) return ta - tb;
    const sr = senderChronologicalRank(a?.sender) - senderChronologicalRank(b?.sender);
    if (sr !== 0) return sr;
    const ma = Number(a?.message_id) || 0;
    const mb = Number(b?.message_id) || 0;
    return ma - mb;
  };

  const isAssistantClarification = (msg) =>
    String(msg?.sender || '').toLowerCase() === 'assistant' &&
    String(msg?.message_type || '').toLowerCase() === 'clarification';

  const isAssistantAnswer = (msg) =>
    String(msg?.sender || '').toLowerCase() === 'assistant' &&
    String(msg?.message_type || '').toLowerCase() !== 'clarification';

  /**
   * User-thread pane: show newest *conversation blocks* first, but preserve chronological order
   * inside each block.
   *
   * A clarification exchange must remain inside the same block:
   * user question -> assistant clarification -> user clarification answer -> assistant answer
   *
   * So we only start a new block on a user message when the immediately previous message is not
   * an assistant clarification.
   */
  const buildUserThreadBlocksNewestFirst = (messages) => {
    const sorted = messages.slice().sort(compareMessagesChronological);
    const turns = [];
    let turn = [];
    for (const m of sorted) {
      const prev = turn.length > 0 ? turn[turn.length - 1] : null;
      const startsNewTurn =
        String(m?.sender || '').toLowerCase() === 'user' &&
        turn.length > 0 &&
        !isAssistantClarification(prev);

      if (startsNewTurn) {
        turns.push(turn);
        turn = [m];
      } else {
        turn.push(m);
      }
    }
    if (turn.length) turns.push(turn);
    const turnEndTime = (t) => (t.length ? Math.max(...t.map(messageSortTime)) : 0);
    const turnMaxMessageId = (t) => (t.length ? Math.max(...t.map((m) => Number(m?.message_id) || 0)) : 0);
    turns.sort((a, b) => {
      const te = turnEndTime(b) - turnEndTime(a);
      if (te !== 0) return te;
      return turnMaxMessageId(b) - turnMaxMessageId(a);
    });
    return turns;
  };

  const orderUserThreadMessagesNewestTurnsFirst = (messages) =>
    buildUserThreadBlocksNewestFirst(messages).flat();

  const htmlToPlainText = (raw) => {
    const html = formatMessageContent(raw || '');
    if (typeof window !== 'undefined' && window.DOMParser) {
      const doc = new window.DOMParser().parseFromString(html, 'text/html');
      return (doc.body?.textContent || '').replace(/\n{3,}/g, '\n\n').trim();
    }
    return String(raw || '').trim();
  };

  const PDF_SECTION_LABELS = [
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
  ];

  const normalizePdfSourceText = (raw) => {
    let plain = htmlToPlainText(raw) || '—';
    plain = plain
      .replace(/[\u200B-\u200D\uFEFF]/g, '')
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/__(.*?)__/g, '$1')
      .replace(/^[\s\uFEFF]*#{1,6}\s*/gm, '')
      .replace(/\s+:\s+/g, ': ')
      .replace(/([a-z])([A-Z][a-z]+:)/g, '$1\n\n$2');
    const labelsSorted = [...PDF_SECTION_LABELS].sort((a, b) => b.length - a.length);
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
  };

  const PDF_SECTION_PATTERNS = [
    { test: /^Quick Answer:\s*/i, kind: 'quick_card', title: 'Quick Answer' },
    { test: /^Executive Summary:\s*/i, kind: 'quick_card', title: 'Executive Summary' },
    { test: /^Daily Outlook:\s*/i, kind: 'quick_card', title: 'Daily Outlook' },
    { test: /^Final Thoughts:\s*/i, kind: 'final_card', title: 'Final Thoughts' },
    { test: /^Final Verdict:\s*/i, kind: 'final_card', title: 'Final Verdict' },
    { test: /^The Parashari View:\s*/i, kind: 'section_secondary', title: 'The Parashari View' },
    { test: /^The Planetary View:\s*/i, kind: 'section_secondary', title: 'The Planetary View' },
    { test: /^Parashari View:\s*/i, kind: 'section_secondary', title: 'Parashari View' },
    { test: /^Ashtakavarga \(SAV & BAV\):\s*/i, kind: 'section_secondary', title: 'Ashtakavarga (SAV & BAV)' },
    { test: /^The Jaimini View:\s*/i, kind: 'section_secondary', title: 'The Jaimini View' },
    { test: /^Jaimini View:\s*/i, kind: 'section_secondary', title: 'Jaimini View' },
    { test: /^KP Stellar Perspective:\s*/i, kind: 'section_secondary', title: 'KP Stellar Perspective' },
    { test: /^KP View:\s*/i, kind: 'section_secondary', title: 'KP View' },
    { test: /^Nadi Interpretation:\s*/i, kind: 'section_secondary', title: 'Nadi Interpretation' },
    { test: /^Nadi View:\s*/i, kind: 'section_secondary', title: 'Nadi View' },
    { test: /^Timing Synthesis:\s*/i, kind: 'section_secondary', title: 'Timing Synthesis' },
    { test: /^Triple Perspective \(Sudarshana\):\s*/i, kind: 'section_secondary', title: 'Triple Perspective (Sudarshana)' },
    { test: /^Divisional Chart Analysis:\s*/i, kind: 'section_secondary', title: 'Divisional Chart Analysis' },
    { test: /^Key Insights:\s*/i, kind: 'section_primary', title: 'Key Insights' },
    { test: /^Astrological Analysis:\s*/i, kind: 'section_primary', title: 'Astrological Analysis' },
    { test: /^Nakshatra Insights:\s*/i, kind: 'section_primary', title: 'Nakshatra Insights' },
    { test: /^Timing & Guidance:\s*/i, kind: 'section_primary', title: 'Timing & Guidance' },
    { test: /^Timing Through The Day:\s*/i, kind: 'section_primary', title: 'Timing Through The Day' },
    { test: /^Guidance for the Day:\s*/i, kind: 'section_primary', title: 'Guidance for the Day' },
    { test: /^Main Day Triggers:\s*/i, kind: 'section_primary', title: 'Main Day Triggers' },
    { test: /^What To Use:\s*/i, kind: 'section_primary', title: 'What To Use' },
    { test: /^What To Watch:\s*/i, kind: 'section_primary', title: 'What To Watch' },
  ];

  const mergeAdjacentBullets = (sections) => {
    const out = [];
    sections.forEach((s) => {
      if (s.kind === 'bullet' && out.length && out[out.length - 1].kind === 'bullet_group') {
        out[out.length - 1].items.push(s.text);
      } else if (s.kind === 'bullet') {
        out.push({ kind: 'bullet_group', items: [s.text] });
      } else {
        out.push(s);
      }
    });
    return out;
  };

  /** When a titled section has no body (label-only block after \\n\\n split), fold the next block in. */
  const mergeEmptyTitledSectionForward = (sections) => {
    const out = [];
    for (let i = 0; i < sections.length; i++) {
      const s = sections[i];
      const next = sections[i + 1];
      const isTitled =
        s &&
        (s.kind === 'section_primary' ||
          s.kind === 'section_secondary' ||
          s.kind === 'quick_card' ||
          s.kind === 'final_card') &&
        s.title;
      if (
        isTitled &&
        !String(s.text ?? '').trim() &&
        next &&
        (next.kind === 'paragraph' || next.kind === 'bullet_group' || next.kind === 'bullet')
      ) {
        if (next.kind === 'bullet_group' && Array.isArray(next.items)) {
          s.text = next.items.map((t) => `• ${String(t || '').trim()}`).join('\n');
        } else if (next.kind === 'bullet') {
          s.text = `• ${String(next.text || '').trim()}`;
        } else {
          s.text = next.text;
        }
        out.push(s);
        i += 1;
      } else {
        out.push(s);
      }
    }
    return out;
  };

  const expandAstrologicalAnalysisSection = (sections) => {
    const opensSecondary = (piece) =>
      PDF_SECONDARY_RELAXED.some((def) => def.re.test(piece)) ||
      PDF_SECTION_PATTERNS.some((def) => def.kind === 'section_secondary' && def.test.test(piece));
    const pushSecondaryFromPiece = (piece) => {
      for (const def of PDF_SECONDARY_RELAXED) {
        if (def.re.test(piece)) {
          return {
            kind: 'section_secondary',
            title: def.title,
            text: piece.replace(def.re, '').trim(),
          };
        }
      }
      for (const def of PDF_SECTION_PATTERNS) {
        if (def.kind !== 'section_secondary') continue;
        if (def.test.test(piece)) {
          return {
            kind: 'section_secondary',
            title: def.title,
            text: piece.replace(def.test, '').trim(),
          };
        }
      }
      return null;
    };

    const out = [];
    sections.forEach((sec) => {
      if (sec.kind !== 'section_primary' || sec.title !== 'Astrological Analysis' || !sec.text) {
        out.push(sec);
        return;
      }
      if (sec.text.search(AST_ANALYSIS_SUB_SPLIT) < 0) {
        out.push(sec);
        return;
      }
      const parts = sec.text.split(AST_ANALYSIS_SUB_SPLIT).map((p) => p.trim());
      const nonempty = parts.filter(Boolean);
      if (nonempty.length < 2) {
        out.push(sec);
        return;
      }
      let startIdx = 0;
      let astroPrimary = null;
      if (parts[0] && !opensSecondary(parts[0])) {
        astroPrimary = { kind: 'section_primary', title: 'Astrological Analysis', text: parts[0] };
        out.push(astroPrimary);
        startIdx = 1;
      }
      for (let j = startIdx; j < parts.length; j++) {
        const piece = parts[j];
        if (!piece) continue;
        const secondary = pushSecondaryFromPiece(piece);
        if (secondary) {
          astroPrimary = null;
          out.push(secondary);
        } else if (astroPrimary) {
          astroPrimary.text = [astroPrimary.text, piece].filter(Boolean).join('\n\n');
        } else {
          out.push({ kind: 'paragraph', text: piece });
        }
      }
    });
    return out;
  };

  const extractPdfSectionsFromMessage = (raw) => {
    const fromDrafts = extractChatSectionDrafts(raw);
    const merged = mergeAdjacentBullets(fromDrafts);
    let base = mergeEmptyTitledSectionForward(merged);
    base.forEach((s) => {
      if (s.text != null && s.kind !== 'heading') {
        s.text = preprocessPdfSectionBody(s.title, s.text);
      }
    });
    const expanded = expandAstrologicalAnalysisSection(base);
    const out = mergeEmptyTitledSectionForward(expanded.length ? expanded : fromDrafts);
    return attachBodyFlowToPdfSections(out.length ? out : fromDrafts);
  };

  const downloadConversationPdf = async (messages, session, messageId) => {
    if (!Array.isArray(messages) || messages.length === 0) return;
    setPdfMessageId(messageId || 'thread');
    try {
      const doc = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'portrait' });
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 20;
      const maxWidth = pageWidth - 2 * margin;
      let yPosition = margin;

      const conversationMessages = messages.map((msg) => {
        const senderKey = String(msg?.sender || '').toLowerCase();
        return {
          role: senderKey === 'user' ? 'user' : 'assistant',
          content: String(msg?.content || ''),
          message_type: msg?.message_type || null,
          timestamp: msg?.timestamp || null,
        };
      });

      doc.setFontSize(16);
      doc.setFont(undefined, 'bold');
      doc.setTextColor(0, 0, 0);
      doc.text('AstroRoshni - Astrology Chat', margin, yPosition);
      yPosition += 10;

      doc.setFontSize(10);
      doc.setFont(undefined, 'normal');
      doc.text(`Generated on: ${new Date().toLocaleDateString()}`, margin, yPosition);
      if (session?.user_name) {
        yPosition += 6;
        doc.text(`For: ${session.user_name}`, margin, yPosition);
      }
      if (session?.native_name) {
        yPosition += 6;
        doc.text(`Chart: ${session.native_name}`, margin, yPosition);
      }
      yPosition += 15;

      const bodyLineMm = 5.3;
      const titleLinePrimaryMm = 6.2;
      const titleLineSecondaryMm = 5.6;
      const titleLineQuickMm = 6;
      const accentStripMm = 1.5;
      const cardSidePadMm = 5;
      const cardTopPadMm = 5.5;
      const cardBottomPadMm = 5;
      const titleBodyGapMm = 3.5;
      const cardW = maxWidth - 4;
      const firstBaselineExtraMm = 4;
      const innerTextW = Math.max(40, cardW - accentStripMm - cardSidePadMm * 2);

      const CARD_STACK_GAP_MM = 4;

      const measurePartitionedBody = (sec, mainTitleExtraMm) => {
        const parts = partitionBodyFlowAtSubheadings(sec.bodyFlow || []);
        let sum = 0;
        parts.forEach((part, idx) => {
          const bh = measurePdfBodyFlow(doc, part.blocks, innerTextW, bodyLineMm);
          if (idx === 0) {
            sum +=
              cardTopPadMm + firstBaselineExtraMm + (mainTitleExtraMm || 0) + bh + cardBottomPadMm;
          } else {
            /* Gap sits *between* shells (page background), not inside the next fill — otherwise
             * continuation cards visually merge with the previous one and the subtitle reads
             * as a footer of the same card. */
            sum += CARD_STACK_GAP_MM;
            sum +=
              cardTopPadMm +
              firstBaselineExtraMm +
              measurePdfSubTitleBlock(doc, part.subTitle, innerTextW) +
              bh +
              cardBottomPadMm;
          }
        });
        return sum + 2;
      };

      const measureSectionHeight = (sec) => {
        const vPad = cardTopPadMm + firstBaselineExtraMm + cardBottomPadMm;
        if (sec.kind === 'heading') {
          doc.setFontSize(12);
          doc.setFont(undefined, 'bold');
          const lines = doc.splitTextToSize(String(sec.text || '—'), innerTextW);
          return vPad + Math.max(lines.length, 1) * titleLinePrimaryMm + 2;
        }
        if (sec.kind === 'bullet_group') {
          return measurePartitionedBody(sec, 0);
        }
        const titled =
          (sec.kind === 'quick_card' || sec.kind === 'final_card' || sec.kind === 'section_primary' || sec.kind === 'section_secondary') &&
          sec.title;
        if (!titled) {
          return measurePartitionedBody(sec, 0);
        }
        let titleSize = 12;
        let titleLineMm = titleLinePrimaryMm;
        if (sec.kind === 'section_secondary') {
          titleSize = 11;
          titleLineMm = titleLineSecondaryMm;
        } else if (sec.kind === 'quick_card' || sec.kind === 'final_card') {
          titleSize = 11;
          titleLineMm = titleLineQuickMm;
        }
        doc.setFontSize(titleSize);
        doc.setFont(undefined, 'bold');
        const titleLines = doc.splitTextToSize(String(sec.title || ''), innerTextW);
        const titleGapAfter =
          sec.kind === 'quick_card' || sec.kind === 'final_card' ? titleBodyGapMm - 1 : titleBodyGapMm;
        const mainTitleExtraMm = titleLines.length * titleLineMm + titleGapAfter;
        return measurePartitionedBody(sec, mainTitleExtraMm);
      };

      const lineHeightMm = bodyLineMm;

      const ensureVerticalSpace = (neededMm) => {
        if (yPosition + neededMm > pageHeight - 18) {
          doc.addPage();
          yPosition = margin;
        }
      };

      const drawSectionCard = (sec) => {
        const h = measureSectionHeight(sec);
        ensureVerticalSpace(h + 6);
        const x0 = margin + 2;
        const stackTop = yPosition;
        const textX = x0 + accentStripMm + cardSidePadMm;
        const badge = 4.5;
        const listTextX = textX + badge + 4.5;
        const listTextW = Math.max(20, innerTextW - badge - 5);

        const paintShellAt = (shellTop, shellH, bgRgb, accentRgb) => {
          doc.setFillColor(bgRgb[0], bgRgb[1], bgRgb[2]);
          doc.rect(x0, shellTop, cardW, shellH, 'F');
          doc.setFillColor(accentRgb[0], accentRgb[1], accentRgb[2]);
          doc.rect(x0, shellTop, accentStripMm, shellH, 'F');
          doc.setDrawColor(237, 233, 228);
          doc.setLineWidth(0.2);
          doc.rect(x0, shellTop, cardW, shellH, 'S');
        };

        const drawPartitionedBody = (bgRgb, accentRgb, drawMainTitle) => {
          const parts = partitionBodyFlowAtSubheadings(sec.bodyFlow || []);
          const heights = parts.map((part, idx) => {
            const bh = measurePdfBodyFlow(doc, part.blocks, innerTextW, bodyLineMm);
            if (idx === 0) {
              const extra = drawMainTitle ? drawMainTitle.titleBlockMm : 0;
              return cardTopPadMm + firstBaselineExtraMm + extra + bh + cardBottomPadMm;
            }
            return (
              cardTopPadMm +
              firstBaselineExtraMm +
              measurePdfSubTitleBlock(doc, part.subTitle, innerTextW) +
              bh +
              cardBottomPadMm
            );
          });
          const footerSafeMm = 18;
          let runTop = stackTop;
          parts.forEach((part, idx) => {
            const hI = heights[idx];
            if (idx > 0) runTop += CARD_STACK_GAP_MM;
            if (runTop + hI > pageHeight - footerSafeMm) {
              doc.addPage();
              runTop = margin;
            }
            paintShellAt(runTop, hI, bgRgb, accentRgb);
            let ty = runTop + cardTopPadMm + firstBaselineExtraMm;
            if (idx === 0 && drawMainTitle) {
              ty = drawMainTitle.drawAt(textX, ty);
            } else if (idx > 0) {
              doc.setFontSize(10);
              doc.setFont(undefined, 'bold');
              doc.setTextColor(234, 88, 12);
              doc.splitTextToSize(String(part.subTitle || ''), innerTextW).forEach((ln) => {
                doc.text(ln, textX, ty);
                ty += 5.8;
              });
              doc.setFont(undefined, 'normal');
              doc.setTextColor(44, 62, 80);
              ty += 1;
            }
            drawPdfBodyFlow(doc, part.blocks, {
              textX,
              innerTextW,
              bodyLineMm,
              startY: ty,
              badge,
              listTextX,
              listTextW,
            });
            runTop += hI;
          });
          yPosition = runTop + 8;
          doc.setTextColor(0, 0, 0);
        };

        if (sec.kind === 'heading') {
          paintShellAt(stackTop, h, [255, 250, 246], [255, 107, 53]);
          let ty = stackTop + cardTopPadMm + firstBaselineExtraMm;
          doc.setFontSize(12);
          doc.setFont(undefined, 'bold');
          doc.setTextColor(255, 107, 53);
          const titleLines = doc.splitTextToSize(String(sec.text || ''), innerTextW);
          titleLines.forEach((ln) => {
            doc.text(ln, textX, ty);
            ty += titleLinePrimaryMm;
          });
          yPosition = stackTop + h + 6;
          doc.setTextColor(0, 0, 0);
          return;
        }

        if (sec.kind === 'bullet_group') {
          drawPartitionedBody([255, 252, 248], [255, 107, 53], null);
          return;
        }

        if (sec.kind === 'quick_card') {
          doc.setFontSize(11);
          doc.setFont(undefined, 'bold');
          const tLines = doc.splitTextToSize(String(sec.title || 'Quick Answer'), innerTextW);
          const titleBlockMm = tLines.length * titleLineQuickMm + (titleBodyGapMm - 1);
          drawPartitionedBody([255, 251, 235], [255, 193, 7], {
            titleBlockMm,
            drawAt: (tx, ty0) => {
              doc.setFontSize(11);
              doc.setFont(undefined, 'bold');
              doc.setTextColor(234, 88, 12);
              let ty = ty0;
              tLines.forEach((ln) => {
                doc.text(ln, tx, ty);
                ty += titleLineQuickMm;
              });
              ty += titleBodyGapMm - 1;
              doc.setFont(undefined, 'normal');
              doc.setTextColor(44, 62, 80);
              return ty;
            },
          });
          return;
        }

        if (sec.kind === 'final_card') {
          doc.setFontSize(11);
          doc.setFont(undefined, 'bold');
          const tLines = doc.splitTextToSize(String(sec.title || 'Final Thoughts'), innerTextW);
          const titleBlockMm = tLines.length * titleLineQuickMm + (titleBodyGapMm - 1);
          drawPartitionedBody([241, 248, 255], [59, 130, 246], {
            titleBlockMm,
            drawAt: (tx, ty0) => {
              doc.setFontSize(11);
              doc.setFont(undefined, 'bold');
              doc.setTextColor(30, 64, 175);
              let ty = ty0;
              tLines.forEach((ln) => {
                doc.text(ln, tx, ty);
                ty += titleLineQuickMm;
              });
              ty += titleBodyGapMm - 1;
              doc.setFont(undefined, 'normal');
              doc.setTextColor(44, 62, 80);
              return ty;
            },
          });
          return;
        }

        if (sec.kind === 'section_primary') {
          doc.setFontSize(12);
          doc.setFont(undefined, 'bold');
          const tLines = doc.splitTextToSize(String(sec.title || 'Section'), innerTextW);
          const titleBlockMm = tLines.length * titleLinePrimaryMm + titleBodyGapMm;
          drawPartitionedBody([255, 250, 246], [255, 107, 53], {
            titleBlockMm,
            drawAt: (tx, ty0) => {
              doc.setFontSize(12);
              doc.setFont(undefined, 'bold');
              doc.setTextColor(255, 107, 53);
              let ty = ty0;
              tLines.forEach((ln) => {
                doc.text(ln, tx, ty);
                ty += titleLinePrimaryMm;
              });
              ty += titleBodyGapMm;
              doc.setFont(undefined, 'normal');
              doc.setTextColor(44, 62, 80);
              return ty;
            },
          });
          return;
        }

        if (sec.kind === 'section_secondary') {
          doc.setFontSize(11);
          doc.setFont(undefined, 'bold');
          const tLines = doc.splitTextToSize(String(sec.title || ''), innerTextW);
          const titleBlockMm = tLines.length * titleLineSecondaryMm + titleBodyGapMm;
          drawPartitionedBody([252, 251, 249], [251, 146, 60], {
            titleBlockMm,
            drawAt: (tx, ty0) => {
              doc.setFontSize(11);
              doc.setFont(undefined, 'bold');
              doc.setTextColor(194, 65, 12);
              let ty = ty0;
              tLines.forEach((ln) => {
                doc.text(ln, tx, ty);
                ty += titleLineSecondaryMm;
              });
              ty += titleBodyGapMm;
              doc.setFont(undefined, 'normal');
              doc.setTextColor(44, 62, 80);
              return ty;
            },
          });
          return;
        }

        /* paragraph */
        drawPartitionedBody([255, 255, 255], [230, 230, 230], null);
      };

      const drawSimpleBubble = (msg, roleLabel, content) => {
        const lines = doc.splitTextToSize(content || '—', maxWidth - 20);
        const metaHeight = msg.timestamp ? 18 : 12;
        const bubbleHeight = Math.max(20, lines.length * lineHeightMm + 15 + metaHeight);

        ensureVerticalSpace(bubbleHeight + 10);

        if (msg.role === 'user') {
          doc.setFillColor(255, 255, 255);
          doc.rect(margin, yPosition - 5, maxWidth, bubbleHeight, 'F');
          doc.setDrawColor(255, 107, 53);
          doc.setLineWidth(2);
          doc.line(margin, yPosition - 5, margin, yPosition - 5 + bubbleHeight);
        } else {
          doc.setFillColor(245, 245, 245);
          doc.rect(margin, yPosition - 5, maxWidth, bubbleHeight, 'F');
        }

        doc.setFontSize(11);
        doc.setFont(undefined, 'bold');
        doc.setTextColor(msg.role === 'user' ? 51 : 0, msg.role === 'user' ? 51 : 0, msg.role === 'user' ? 51 : 0);
        doc.text(`${roleLabel}:`, margin + 5, yPosition + 5);
        yPosition += 12;

        if (msg.timestamp) {
          doc.setFontSize(8);
          doc.setFont(undefined, 'normal');
          doc.setTextColor(120, 120, 120);
          doc.text(formatDate(msg.timestamp), margin + 5, yPosition);
          yPosition += 6;
        }

        doc.setFont(undefined, 'normal');
        doc.setFontSize(10);
        doc.setTextColor(0, 0, 0);

        for (const line of lines) {
          ensureVerticalSpace(lineHeightMm + 2);
          doc.text(line, margin + 5, yPosition);
          yPosition += lineHeightMm;
        }

        yPosition += 15;
      };

      for (const msg of conversationMessages) {
        const roleLabel = msg.role === 'user'
          ? 'You'
          : (String(msg.message_type || '').toLowerCase() === 'clarification' ? 'AstroRoshni Clarification' : 'AstroRoshni');

        const plainContent = normalizePdfSourceText(msg.content)
          .replace(/<[^>]*>/g, ' ')
          .replace(/\s+\n/g, '\n')
          .replace(/\n{3,}/g, '\n\n')
          .trim();

        const isAssistantAnswer =
          msg.role === 'assistant' && String(msg.message_type || '').toLowerCase() !== 'clarification';

        if (isAssistantAnswer) {
          const sections = extractPdfSectionsFromMessage(msg.content);

          doc.setFontSize(11);
          doc.setFont(undefined, 'bold');
          doc.setTextColor(0, 0, 0);
          doc.text(`${roleLabel}:`, margin + 5, yPosition + 5);
          yPosition += 12;

          if (msg.timestamp) {
            doc.setFontSize(8);
            doc.setFont(undefined, 'normal');
            doc.setTextColor(120, 120, 120);
            doc.text(formatDate(msg.timestamp), margin + 5, yPosition);
            yPosition += 8;
            doc.setTextColor(0, 0, 0);
          } else {
            yPosition += 2;
          }

          sections.forEach((sec) => drawSectionCard(sec));
          yPosition += 6;
          continue;
        }

        drawSimpleBubble(msg, roleLabel, plainContent);
      }

      const primaryQuestion =
        messages.find((m) => String(m?.sender || '').toLowerCase() === 'user')?.content || 'chat';
      const safeStem = htmlToPlainText(primaryQuestion)
        .replace(/[^a-zA-Z0-9]+/g, '_')
        .replace(/^_+|_+$/g, '')
        .slice(0, 48) || 'chat';

      const totalPages = doc.internal.getNumberOfPages();
      for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(128, 128, 128);
        doc.text(`Page ${i} of ${totalPages}`, pageWidth - 40, pageHeight - 10);
      }

      doc.save(`astroroshni_chat_${safeStem}.pdf`);
    } finally {
      setPdfMessageId(null);
    }
  };

  const formatTimeIST = (dateStr) => {
    const d = parseUtcTimestamp(dateStr);
    if (!d) return '—';
    return d.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: IST
    }) + ' IST';
  };

  const formatParallelStageLabel = (stage) => {
    const s = String(stage || '');
    return s.replace(/^parallel_/, '').replace(/_/g, ' ') || 'stage';
  };

  const formatParallelElapsed = (ms) => {
    if (ms == null || !Number.isFinite(Number(ms))) return null;
    const n = Number(ms);
    if (n >= 1000) return `${(n / 1000).toFixed(2)}s`;
    return `${n.toLocaleString(undefined, { maximumFractionDigits: 1 })}ms`;
  };

  /** Sum a numeric field across parallel stage rows (orchestrator stores one row per branch + merge). */
  const sumParallelStageField = (stages, key) => {
    if (!Array.isArray(stages)) return 0;
    return stages.reduce((acc, st) => acc + (Number(st?.[key]) || 0), 0);
  };

  const formatLlmLabel = (s) => {
    if (!s || typeof s !== 'object') return null;
    const prov = String(s.chat_llm_provider || '').trim();
    const mod = String(s.chat_llm_model || '').trim();
    if (!mod && !prov) return null;
    if (prov && mod) return `${prov}: ${mod}`;
    return mod || prov || null;
  };

  /** Merge / final-call model for this assistant row (parallel pipeline stores it on stages, not session). */
  const MERGE_PARALLEL_STAGE_NAMES = new Set(['parallel_merge', 'parallel_relational_merge']);

  const parallelModelSummary = (usage) => {
    if (!usage || typeof usage !== 'object') return null;
    const stages = Array.isArray(usage.stages) ? usage.stages : [];
    if (!stages.length) return null;
    const models = [];
    const seen = new Set();
    stages.forEach((st) => {
      const prov = String(st?.llm_provider || '').trim();
      const mod = String(st?.llm_model || '').trim();
      const label = prov && mod ? `${prov}: ${mod}` : mod || prov;
      if (!label || seen.has(label)) return;
      seen.add(label);
      models.push(label);
    });
    if (!models.length) return null;
    return {
      primary: models[0],
      mixed: models.length > 1,
      labels: models,
    };
  };

  const parallelBranchPlanSummary = (usage) => {
    if (!usage || typeof usage !== 'object') return null;
    const plan = usage.branch_plan;
    if (!plan || typeof plan !== 'object' || !plan.enabled) return null;
    const planner = plan.planner && typeof plan.planner === 'object' ? plan.planner : {};
    const selected = Array.isArray(plan.selected_branches) ? plan.selected_branches.filter(Boolean) : [];
    const required = Array.isArray(planner.required_branches) ? planner.required_branches.filter(Boolean) : [];
    const optional = Array.isArray(planner.optional_branches) ? planner.optional_branches.filter(Boolean) : [];
    const reasoning = planner.reasoning && typeof planner.reasoning === 'object' ? planner.reasoning : {};
    const scores = planner.branch_scores && typeof planner.branch_scores === 'object' ? planner.branch_scores : {};
    const confidenceRaw = Number(planner.confidence);
    const confidence = Number.isFinite(confidenceRaw) ? confidenceRaw : null;
    const formatBranch = (b) => {
      const s = String(b || '').trim();
      if (!s) return '';
      return s.charAt(0).toUpperCase() + s.slice(1);
    };
    const entries = selected.map((branch) => ({
      branch,
      label: formatBranch(branch),
      required: required.includes(branch),
      optional: optional.includes(branch),
      reasoning: String(reasoning[branch] || '').trim(),
      score: Number.isFinite(Number(scores[branch])) ? Number(scores[branch]) : null,
    }));
    return {
      selected,
      entries,
      confidence,
      modelLabel: formatLlmLabel({
        chat_llm_provider: planner.llm_provider,
        chat_llm_model: planner.llm_model,
      }),
    };
  };

  const llmSourceFromParallelUsage = (usage) => {
    if (!usage || typeof usage !== 'object') return null;
    const stages = Array.isArray(usage.stages) ? usage.stages : [];
    if (!stages.length) return null;

    const merge = stages.find((st) => st && MERGE_PARALLEL_STAGE_NAMES.has(String(st.stage || '')));
    if (merge && (String(merge.llm_provider || '').trim() || String(merge.llm_model || '').trim())) {
      return {
        chat_llm_provider: String(merge.llm_provider || '').trim(),
        chat_llm_model: String(merge.llm_model || '').trim(),
      };
    }

    if (usage.kind === 'instant_chat_usage') {
      for (let i = stages.length - 1; i >= 0; i--) {
        const st = stages[i];
        if (st && String(st.llm_model || '').trim()) {
          return {
            chat_llm_provider: String(st.llm_provider || '').trim(),
            chat_llm_model: String(st.llm_model || '').trim(),
          };
        }
      }
    }

    return null;
  };

  const answerLlmSourceForMessage = (message) => {
    const fromUsage = llmSourceFromParallelUsage(message?.parallel_llm_usage);
    if (fromUsage && (fromUsage.chat_llm_provider || fromUsage.chat_llm_model)) return fromUsage;
    return null;
  };

  const listRangeLabel = useMemo(() => {
    if (!listTotal) return '0 users';
    const start = (listPage - 1) * USER_PAGE_SIZE + 1;
    const end = Math.min(listPage * USER_PAGE_SIZE, listTotal);
    return `${start}–${end} of ${listTotal}`;
  }, [listPage, listTotal]);

  const sessionPagination = selectedSession?.pagination || null;
  const sessionRangeLabel = useMemo(() => {
    if (!sessionPagination?.total) return '0 messages';
    const start = (sessionPagination.page - 1) * sessionPagination.limit + 1;
    const end = Math.min(sessionPagination.page * sessionPagination.limit, sessionPagination.total);
    return `${start}–${end} of ${sessionPagination.total}`;
  }, [sessionPagination]);

  const renderUserValueSnapshot = () => {
    if (userValueLoading) {
      return (
        <div className="user-value-snapshot user-value-snapshot--loading">
          Loading user snapshot…
        </div>
      );
    }

    if (userValueError) {
      return (
        <div className="user-value-snapshot user-value-snapshot--error">
          {userValueError}
        </div>
      );
    }

    const snap = userValueSnapshot;
    if (!snap) return null;

    const priorityLabel = snap.priority?.label || 'Regular';
    const priorityClass = String(priorityLabel).toLowerCase().replace(/[^a-z0-9]+/g, '-');
    const commercial = snap.commercial || {};
    const engagement = snap.engagement || {};
    const feedback = snap.feedback || {};
    const reachability = snap.reachability || {};
    const acquisition = snap.acquisition || {};
    const subscription = commercial.active_subscription;
    const sourceLabel = [acquisition.utm_source, acquisition.utm_medium]
      .filter(Boolean)
      .join(' / ');
    const appLabel = [
      acquisition.latest_app_version ? `v${acquisition.latest_app_version}` : null,
      acquisition.latest_app_build ? `build ${acquisition.latest_app_build}` : null,
    ].filter(Boolean).join(' · ');

    return (
      <section
        className={`user-value-snapshot${valuePanelExpanded ? ' user-value-snapshot--expanded' : ' user-value-snapshot--collapsed'}`}
        aria-label="User value snapshot"
      >
        <div className="user-value-snapshot-main">
          <div className="user-value-priority">
            <span className={`user-value-badge user-value-badge--${priorityClass}`}>
              {priorityLabel}
            </span>
            <span className="user-value-score">
              Score {formatCompactNumber(snap.priority?.score)}/100
            </span>
            <button
              type="button"
              className="user-value-toggle"
              onClick={() => setValuePanelExpanded((v) => !v)}
              aria-expanded={valuePanelExpanded}
            >
              {valuePanelExpanded ? 'Hide value details' : 'Show value details'}
            </button>
          </div>
          <div className="user-value-metrics" aria-label="Key user metrics">
            <div className="user-value-metric">
              <span className="user-value-metric-label">Paid credits</span>
              <strong>{formatCompactNumber(commercial.lifetime_credits_purchased)}</strong>
            </div>
            <div className="user-value-metric">
              <span className="user-value-metric-label">Spend</span>
              <strong>{commercial.lifetime_amount_inr != null ? formatInr(commercial.lifetime_amount_inr) : '—'}</strong>
            </div>
            <div className="user-value-metric">
              <span className="user-value-metric-label">Balance</span>
              <strong>{formatCompactNumber(commercial.current_credits)}</strong>
            </div>
            <div className="user-value-metric">
              <span className="user-value-metric-label">Questions</span>
              <strong>{formatCompactNumber(engagement.total_questions)}</strong>
            </div>
            <div className="user-value-metric">
              <span className="user-value-metric-label">30d</span>
              <strong>{formatCompactNumber(engagement.questions_30d)}</strong>
            </div>
            <div className="user-value-metric">
              <span className="user-value-metric-label">Feedback</span>
              <strong>
                {feedback.average_rating != null
                  ? `${Number(feedback.average_rating).toFixed(1)} (${formatCompactNumber(feedback.feedback_count)})`
                  : '—'}
              </strong>
            </div>
          </div>
        </div>

        {valuePanelExpanded && Array.isArray(snap.priority?.reasons) && snap.priority.reasons.length > 0 && (
          <div className="user-value-reasons">
            {snap.priority.reasons.map((reason, index) => (
              <span key={`${reason}-${index}`} className="user-value-reason">
                {reason}
              </span>
            ))}
          </div>
        )}

        {valuePanelExpanded && (
        <div className="user-value-details">
          <div className="user-value-detail-grid">
            <div>
              <h4>Commercial</h4>
              <p>Purchases: {formatCompactNumber(commercial.purchase_count)}</p>
              <p>Avg order: {commercial.avg_order_value_inr != null ? formatInr(commercial.avg_order_value_inr) : '—'}</p>
              <p>Credits spent: {formatCompactNumber(commercial.credits_spent)}</p>
              <p>Spent 30d: {formatCompactNumber(commercial.credits_spent_30d)}</p>
              {subscription ? (
                <p>
                  Plan: {subscription.name}
                  {subscription.discount_percent ? ` · ${subscription.discount_percent}% off` : ''}
                </p>
              ) : (
                <p>Plan: none active</p>
              )}
            </div>
            <div>
              <h4>Engagement</h4>
              <p>Questions 7d: {formatCompactNumber(engagement.questions_7d)}</p>
              <p>Sessions: {formatCompactNumber(engagement.total_sessions)}</p>
              <p>Avg/session: {formatCompactNumber(engagement.avg_questions_per_session)}</p>
              <p>Active days 30d: {formatCompactNumber(engagement.active_days_30d)}</p>
              <p>Last chat: {engagement.last_chat_at ? formatDate(engagement.last_chat_at) : '—'}</p>
            </div>
            <div>
              <h4>Satisfaction</h4>
              <p>Low ratings: {formatCompactNumber(feedback.negative_feedback_count)}</p>
              <p>Failed messages: {formatCompactNumber(engagement.failed_messages)}</p>
              <p>Latest feedback: {feedback.latest_feedback_at ? formatDate(feedback.latest_feedback_at) : '—'}</p>
              <p>Refunds: {formatCompactNumber(commercial.refund_count)}</p>
              <p>Payment failures: {formatCompactNumber(commercial.failed_payment_count)}</p>
            </div>
            <div>
              <h4>Reach</h4>
              <p>Push: {reachability.push_enabled ? 'enabled' : 'not enabled'}</p>
              <p>WhatsApp: {reachability.whatsapp_linked ? 'linked' : 'not linked'}</p>
              <p>App: {appLabel || '—'}</p>
              <p>Source: {sourceLabel || '—'}</p>
              <p>Campaign: {acquisition.utm_campaign || '—'}</p>
            </div>
          </div>
        </div>
        )}
      </section>
    );
  };

  const renderMessageSidebar = () => {
    return userRows.map((row) => {
      const isActive = selectedUserId != null && Number(selectedUserId) === Number(row.user_id);
      return (
        <div
          key={`user-${row.user_id}`}
          role="button"
          tabIndex={0}
          className={`session-card admin-chat-message-row ${isActive ? 'active' : ''}`}
          onClick={() => fetchSessionDetails(row.user_id, 1)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              fetchSessionDetails(row.user_id, 1);
            }
          }}
        >
          <div className="admin-chat-user-group-name">
            <strong>{row.user_name || 'Unknown'}</strong>
            {row.user_phone ? (
              <span className="admin-chat-user-group-phone"> · {row.user_phone}</span>
            ) : null}
          </div>
          <div className="admin-chat-user-group-hint">User ID: {row.user_id ?? '—'}</div>
          <div className="admin-chat-message-time">{formatDate(row.last_activity_at)}</div>
          <div className="session-preview">
            {Number(row.message_count || 0).toLocaleString()} total messages
          </div>
        </div>
      );
    });
  };

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape' && selectedSession) {
        setSelectedSession(null);
        setSelectedUserId(null);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [selectedSession]);

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 900px), (max-height: 700px)');
    const lock = () => {
      if (selectedSession && mq.matches) {
        document.body.classList.add('admin-chat-mobile-thread-active');
      } else {
        document.body.classList.remove('admin-chat-mobile-thread-active');
      }
    };
    lock();
    if (typeof mq.addEventListener === 'function') {
      mq.addEventListener('change', lock);
      return () => {
        mq.removeEventListener('change', lock);
        document.body.classList.remove('admin-chat-mobile-thread-active');
      };
    }
    mq.addListener(lock);
    return () => {
      mq.removeListener(lock);
      document.body.classList.remove('admin-chat-mobile-thread-active');
    };
  }, [selectedSession]);

  const msgCount = selectedSession?.pagination?.total ?? selectedSession?.messages?.length ?? 0;
  const displayedBlocks = useMemo(() => {
    const base = Array.isArray(selectedSession?.messages) ? selectedSession.messages : [];
    if (!base.length) return [];
    if (selectedSession?.view_mode === 'user_thread') {
      return buildUserThreadBlocksNewestFirst(base);
    }
    return [base];
  }, [selectedSession]);

  const displayedMessages = useMemo(() => displayedBlocks.flat(), [displayedBlocks]);

  const exportableAssistantMessageIds = useMemo(() => {
    const map = new Map();
    displayedBlocks.forEach((block) => {
      const exportAnchor = [...block].reverse().find(isAssistantAnswer);
      if (exportAnchor?.message_id) {
        map.set(Number(exportAnchor.message_id), block);
      }
    });
    return map;
  }, [displayedBlocks]);

  const latestExportBlock = useMemo(() => {
    if (!displayedBlocks.length) return null;
    return displayedBlocks.find((block) => block.some(isAssistantAnswer)) || null;
  }, [displayedBlocks]);

  const selectedSessionLlmLabel = formatLlmLabel(selectedSession);
  const hasSessionPricing =
    Boolean(selectedSessionLlmLabel) ||
    Boolean(selectedSession?.cost_summary) ||
    selectedSession?.cost_summary?.input_usd_per_1m != null ||
    selectedSession?.cost_summary?.output_usd_per_1m != null;

  return (
    <>
    <div
      className={`admin-chat-history${
        selectedSession ? ' admin-chat-history--thread-open' : ''
      }`}
    >
      <div className="admin-chat-history-intro">
        <h2>Chat history</h2>
        <p className="admin-chat-history-hint admin-chat-history-hint--desktop">
          Left panel lists users (10 per page). Click a user to load their full message timeline
          (user + assistant) in the right pane. Press <kbd>Esc</kbd> to close the conversation.
        </p>
        <p className="admin-chat-history-hint admin-chat-history-hint--mobile">
          Tap a user row to open their full chat timeline. Use <strong>Back</strong> or the close
          control to return here.
        </p>
      </div>

      <div className={`admin-chat-content ${selectedSession ? 'has-selection' : ''}`}>
        <aside className="sessions-sidebar" aria-label="Users with chat history">
          <div className="sessions-list-header">
            <h3>Users</h3>
            {!loading && listTotal > 0 && (
              <span className="sessions-count" title="Total matching users">
                {listTotal}
              </span>
            )}
          </div>
          <div className="sessions-search-wrap">
            <label className="sessions-search-label" htmlFor="admin-chat-session-filter">
              Search
            </label>
            <input
              id="admin-chat-session-filter"
              type="search"
              className="sessions-search-input"
              placeholder="User name, phone, user id…"
              value={sessionQuery}
              onChange={(e) => setSessionQuery(e.target.value)}
              autoComplete="off"
            />
          </div>
          <div className="sessions-list">
            {loading ? (
              <div className="loading">Loading users…</div>
            ) : userRows.length === 0 ? (
              <div className="no-sessions">
                {listTotal === 0 && !debouncedQuery
                  ? 'No users found.'
                  : 'No users match your search.'}
              </div>
            ) : (
              renderMessageSidebar()
            )}
          </div>
          {!loading && listTotal > 0 && (
            <div className="sessions-pagination" role="navigation" aria-label="User list pages">
              <button
                type="button"
                className="sessions-page-btn"
                disabled={listPage <= 1}
                onClick={() => setListPage((p) => Math.max(1, p - 1))}
              >
                Previous
              </button>
              <span className="sessions-page-info">
                Page {listPage}
                {listTotalPages ? ` / ${listTotalPages}` : ''}
                <span className="sessions-page-range"> · {listRangeLabel}</span>
              </span>
              <button
                type="button"
                className="sessions-page-btn"
                disabled={!listHasMore}
                onClick={() => setListPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </aside>

        <div className="session-detail-pane">
          {selectedSession ? (
            <div className="session-details">
              <div className="session-header">
                <button
                  type="button"
                  className="session-back"
                  onClick={() => {
                    setSelectedSession(null);
                    setSelectedUserId(null);
                    setPricePanelExpanded(false);
                    setValuePanelExpanded(false);
                  }}
                  aria-label="Back to user list"
                >
                  <span className="session-back-icon" aria-hidden="true">
                    ←
                  </span>
                  <span className="session-back-label">Users</span>
                </button>
                <div className="session-header-center">
                  <h3 className="session-header-title">
                    <span className="session-header-title-text">{selectedSession.user_name || 'Conversation'}</span>
                    {selectedSession.user_phone && (
                      <span className="session-native-name">{selectedSession.user_phone}</span>
                    )}
                  </h3>
                  {msgCount > 0 && (
                    <span className="session-msg-count">
                      {msgCount} message{msgCount === 1 ? '' : 's'}
                    </span>
                  )}
                  <div className="session-header-actions">
                    {hasSessionPricing && (
                      <button
                        type="button"
                        className="session-panel-toggle"
                        onClick={() => setPricePanelExpanded((v) => !v)}
                        aria-expanded={pricePanelExpanded}
                      >
                        {pricePanelExpanded ? 'Hide pricing' : 'Show pricing'}
                      </button>
                    )}
                    {selectedSession?.view_mode === 'user_thread' && latestExportBlock && (
                      <button
                        type="button"
                        className="message-branch-btn"
                        onClick={() => downloadConversationPdf(latestExportBlock, selectedSession, 'latest-thread')}
                        disabled={pdfMessageId === 'latest-thread'}
                        title="Download the latest visible question-answer flow as PDF"
                      >
                        {pdfMessageId === 'latest-thread' ? 'Generating PDF…' : 'Download Latest PDF'}
                      </button>
                    )}
                  </div>
                  {pricePanelExpanded && (
                  <div className="session-meta-chips">
                    {selectedSessionLlmLabel && (
                      <span className="session-meta-chip" title="Provider and model ID from admin settings at answer time">
                        {selectedSessionLlmLabel}
                      </span>
                    )}
                    {typeof selectedSession?.cost_summary?.total_cost_inr_estimate === 'number' && (
                      <span
                        className="session-meta-chip session-meta-chip--accent"
                        title={selectedSession?.cost_summary?.note || 'Rough estimate'}
                      >
                        INR {selectedSession.cost_summary.total_cost_inr_estimate.toFixed(4)}
                      </span>
                    )}
                    {typeof selectedSession?.cost_summary?.input_cost_non_cached_inr_estimate === 'number' && (
                      <span className="session-meta-chip" title="Non-cached input cost estimate">
                        NC In INR {Number(selectedSession.cost_summary.input_cost_non_cached_inr_estimate).toFixed(4)}
                      </span>
                    )}
                    {typeof selectedSession?.cost_summary?.input_cost_cached_inr_estimate === 'number' && (
                      <span className="session-meta-chip" title="Cached input cost estimate">
                        C In INR {Number(selectedSession.cost_summary.input_cost_cached_inr_estimate).toFixed(4)}
                      </span>
                    )}
                    {typeof selectedSession?.cost_summary?.cache_setup_cost_inr_estimate === 'number' && (
                      <span className="session-meta-chip" title="Context cache setup input cost estimate">
                        Cache setup INR {Number(selectedSession.cost_summary.cache_setup_cost_inr_estimate).toFixed(4)}
                      </span>
                    )}
                    {typeof selectedSession?.cost_summary?.output_cost_inr_estimate === 'number' && (
                      <span className="session-meta-chip" title="Output token cost estimate">
                        Out INR {Number(selectedSession.cost_summary.output_cost_inr_estimate).toFixed(4)}
                      </span>
                    )}
                    {selectedSession?.cost_summary?.input_usd_per_1m != null && (
                      <span className="session-meta-chip" title="Input rate in USD per 1M tokens">
                        In ${Number(selectedSession.cost_summary.input_usd_per_1m || 0).toFixed(2)}/1M
                      </span>
                    )}
                    {selectedSession?.cost_summary?.output_usd_per_1m != null && (
                      <span className="session-meta-chip" title="Output rate in USD per 1M tokens">
                        Out ${Number(selectedSession.cost_summary.output_usd_per_1m || 0).toFixed(2)}/1M
                      </span>
                    )}
                    {selectedSession?.cost_summary?.pricing_tier && (
                      <span className="session-meta-chip" title="Pricing tier used for estimation">
                        {selectedSession.cost_summary.pricing_tier}
                      </span>
                    )}
                    {selectedSession?.cost_summary?.usd_to_inr_rate != null && (
                      <span className="session-meta-chip" title="USD to INR conversion rate">
                        USD/INR {Number(selectedSession.cost_summary.usd_to_inr_rate).toFixed(2)}
                      </span>
                    )}
                  </div>
                  )}
                </div>
                <button
                  type="button"
                  className="session-close"
                  onClick={() => {
                    setSelectedSession(null);
                    setSelectedUserId(null);
                    setPricePanelExpanded(false);
                    setValuePanelExpanded(false);
                  }}
                  aria-label="Close conversation"
                >
                  <span aria-hidden="true">×</span>
                </button>
              </div>

              {renderUserValueSnapshot()}

              {selectedUserId != null && sessionPagination && (
                <div className="session-messages-pagination" role="navigation" aria-label="Session message pages">
                  <button
                    type="button"
                    className="sessions-page-btn"
                    disabled={sessionMsgLoading || sessionPagination.page <= 1}
                    onClick={() =>
                      fetchSessionDetails(
                        selectedUserId,
                        Math.max(1, sessionPagination.page - 1)
                      )
                    }
                  >
                    Previous
                  </button>
                  <span className="sessions-page-info">
                    Page {sessionPagination.page}
                    {sessionPagination.total_pages ? ` / ${sessionPagination.total_pages}` : ''}
                    <span className="sessions-page-range"> · {sessionRangeLabel}</span>
                  </span>
                  <button
                    type="button"
                    className="sessions-page-btn"
                    disabled={sessionMsgLoading || !sessionPagination.has_more}
                    onClick={() =>
                      fetchSessionDetails(
                        selectedUserId,
                        sessionPagination.page + 1
                      )
                    }
                  >
                    Next
                  </button>
                </div>
              )}
              <div className="messages-container">
                {displayedMessages.map((message, index) => {
                  const parallelStages = Array.isArray(message.parallel_llm_usage?.stages)
                    ? message.parallel_llm_usage.stages
                    : [];
                  const hasParallelStages = parallelStages.length > 0;
                  const aggregatePromptChars = hasParallelStages
                    ? sumParallelStageField(parallelStages, 'input_chars')
                    : null;
                  const aggregateReplyChars = hasParallelStages
                    ? sumParallelStageField(parallelStages, 'output_chars')
                    : null;
                  const promptCharsForBadge =
                    aggregatePromptChars != null && aggregatePromptChars > 0
                      ? aggregatePromptChars
                      : Number(message.llm_prompt_chars) || 0;
                  const replyCharsForBadge =
                    aggregateReplyChars != null && aggregateReplyChars > 0
                      ? aggregateReplyChars
                      : Number(message.llm_response_chars) || 0;
                  const role =
                    message.sender === 'user'
                      ? 'user'
                      : message.sender === 'assistant'
                        ? 'assistant'
                        : 'assistant';
                  const exportBlock = Number.isFinite(Number(message.message_id))
                    ? exportableAssistantMessageIds.get(Number(message.message_id))
                    : null;
	                  const showPdfButton = role === 'assistant' && Array.isArray(exportBlock) && exportBlock.length > 0;
	                  const isInstantUsage = message.parallel_llm_usage?.kind === 'instant_chat_usage';
	                  const parallelModelInfo = hasParallelStages ? parallelModelSummary(message.parallel_llm_usage) : null;
	                  const parallelBranchPlan = hasParallelStages ? parallelBranchPlanSummary(message.parallel_llm_usage) : null;
	                  const answerModelLabel =
	                    role === 'assistant'
	                      ? formatLlmLabel(
	                          answerLlmSourceForMessage(message) || selectedSession || {},
	                        )
	                      : null;
	                  const hasPromptChars = Number.isFinite(promptCharsForBadge) && promptCharsForBadge > 0;
	                  const hasReplyChars =
	                    message.sender === 'assistant' &&
	                    Number.isFinite(replyCharsForBadge) &&
	                    replyCharsForBadge > 0;
	                  const hasCostEstimate = typeof message?.cost_estimate?.cost_inr_estimate === 'number';
	                  const hasUsageDetails =
	                    Boolean(answerModelLabel) ||
	                    Boolean(message.native_name) ||
	                    hasPromptChars ||
	                    hasReplyChars ||
	                    Number.isFinite(message.llm_input_tokens) ||
	                    Number.isFinite(message.llm_output_tokens) ||
	                    Number.isFinite(message.llm_cached_input_tokens) ||
	                    Number.isFinite(message.llm_non_cached_input_tokens) ||
	                    (Number.isFinite(message.llm_cache_setup_input_tokens) &&
	                      message.llm_cache_setup_input_tokens > 0) ||
	                    hasCostEstimate ||
	                    hasParallelStages;
	                  const label =
	                    message.sender === 'user'
	                      ? 'User'
	                      : message.sender === 'assistant'
                        ? 'Assistant'
                        : String(message.sender || 'Message').replace(/^\w/, (c) => c.toUpperCase());
                  return (
                <div key={index} className={`message message--${role}`}>
                    <div className="message-label">
                      {label}
                    </div>
                    <div
                      className="message-content"
                      dangerouslySetInnerHTML={{ __html: formatMessageContent(message.content) }}
                    />
                    <div className="message-meta">
                      {role === 'assistant' && Number.isFinite(Number(message.message_id)) && (
                        <button
                          type="button"
                          className="message-branch-btn message-qa-btn"
                          onClick={() => openResponseQa(message.message_id)}
                          title="Run senior jyotishi exam on this answer"
                        >
                          Astrology QA
                        </button>
                      )}
                      {role === 'assistant' && Number.isFinite(Number(message.message_id)) && !isInstantUsage && (
                        <button
                          type="button"
                          className="message-branch-btn"
                          onClick={() => openBranchAnalysis(message.message_id)}
                          title="Open specialist branch outputs"
                        >
                          Branch analysis
                        </button>
                      )}
                      {showPdfButton && (
                        <button
                          type="button"
                          className="message-branch-btn"
                          onClick={() => downloadConversationPdf(exportBlock, selectedSession, message.message_id)}
                          title="Download this question-answer flow as PDF"
                          disabled={pdfMessageId === message.message_id}
                        >
	                          {pdfMessageId === message.message_id ? 'Generating PDF…' : 'Download PDF'}
	                        </button>
	                      )}
	                      {hasUsageDetails && (
	                        <details className="message-usage-details">
	                          <summary className="message-usage-summary">
	                            <span>Usage & cost</span>
	                            {hasCostEstimate && (
	                              <span className="message-usage-summary-cost">
	                                INR {message.cost_estimate.cost_inr_estimate.toFixed(4)}
	                              </span>
	                            )}
	                          </summary>
	                          <div className="message-usage-content">
	                            <div className="message-usage-chips">
	                              {answerModelLabel && (
	                                <span
	                                  className="message-token-badge"
	                                  title={
	                                    parallelModelInfo?.mixed
	                                      ? `Final merge model for this answer. Branches used multiple models: ${parallelModelInfo.labels.join(' | ')}`
	                                      : 'Provider and model for this answer: merge stage from parallel usage when present, else session summary for this view'
	                                  }
	                                >
	                                  {parallelModelInfo?.mixed ? `Merge ${answerModelLabel}` : `Model ${answerModelLabel}`}
	                                </span>
	                              )}
	                              {parallelModelInfo?.mixed && (
	                                <span
	                                  className="message-token-badge"
	                                  title={`Parallel branch models used in this run: ${parallelModelInfo.labels.join(' | ')}`}
	                                >
	                                  Mixed branch models {parallelModelInfo.labels.length}
	                                </span>
	                              )}
	                              {parallelBranchPlan && parallelBranchPlan.selected.length > 0 && (
	                                <span
	                                  className="message-token-badge"
	                                  title={`Planner selected branches: ${parallelBranchPlan.selected.join(', ')}`}
	                                >
	                                  Planned branches {parallelBranchPlan.selected.length}
	                                </span>
	                              )}
	                              {parallelBranchPlan && parallelBranchPlan.confidence != null && (
	                                <span
	                                  className="message-token-badge"
	                                  title="Planner confidence for the selected branch set"
	                                >
	                                  Confidence {(parallelBranchPlan.confidence * 100).toFixed(0)}%
	                                </span>
	                              )}
	                              {message.native_name && (
	                                <span
	                                  className="message-native-badge"
	                                  title="Birth chart / Native"
	                                >
	                                  {message.native_name}
	                                </span>
	                              )}
	                              {hasPromptChars && (
	                                <span
	                                  className="message-char-badge message-char-badge--prompt"
	                                  title={
	                                    hasParallelStages
	                                      ? 'Total prompt characters for the parallel pipeline: sum of each LLM call prompt across all branches + merge (Σ Pr on stage rows).'
	                                      : message.sender === 'user'
	                                        ? 'Full prompt character count for the LLM call that answers this question (same as following assistant row)'
	                                        : 'Full prompt sent to the LLM (chart JSON + instructions + history + question)'
	                                  }
	                                >
	                                  Prompt {Number(promptCharsForBadge).toLocaleString()} chars
	                                </span>
	                              )}
	                              {hasReplyChars && (
	                                <span
	                                  className="message-char-badge message-char-badge--reply"
	                                  title={
	                                    hasParallelStages
	                                      ? 'Total raw output characters across all branch calls + merge (Σ Rp on stage rows).'
	                                      : 'Assistant reply text length after parsing (what the user sees)'
	                                  }
	                                >
	                                  Reply {Number(replyCharsForBadge).toLocaleString()} chars
	                                </span>
	                              )}
	                              {Number.isFinite(message.llm_input_tokens) && (
	                                <span
	                                  className="message-token-badge"
	                                  title={
	                                    message.parallel_llm_usage?.stages?.length
	                                      ? 'Sum of billed input tokens across all parallel branch calls plus merge (Σ In on stage rows). Same as timing.parallel_llm_usage.totals.input_tokens when stored.'
	                                      : message.sender === 'user'
	                                        ? 'API usage: prompt tokens for the assistant reply after this question'
	                                        : 'API usage: prompt (input) tokens for this completion'
	                                  }
	                                >
	                                  In {Number(message.llm_input_tokens).toLocaleString()}
	                                </span>
	                              )}
	                              {Number.isFinite(message.llm_output_tokens) && (
	                                <span
	                                  className="message-token-badge"
	                                  title={
	                                    message.parallel_llm_usage?.stages?.length
	                                      ? 'Sum of billed output tokens across all parallel branch calls plus merge (Σ Out on stage rows). Not the character length of the user-visible reply.'
	                                      : message.sender === 'user'
	                                        ? 'API usage: completion tokens for the assistant reply after this question'
	                                        : 'API usage: completion (output) tokens for this reply'
	                                  }
	                                >
	                                  Out {Number(message.llm_output_tokens).toLocaleString()}
	                                </span>
	                              )}
	                              {Number.isFinite(message.llm_cached_input_tokens) && (
	                                <span className="message-token-badge" title="Provider-reported cached prompt tokens">
	                                  Cached {Number(message.llm_cached_input_tokens).toLocaleString()}
	                                </span>
	                              )}
	                              {Number.isFinite(message.llm_non_cached_input_tokens) && (
	                                <span className="message-token-badge" title="Provider-reported non-cached prompt tokens">
	                                  Non-cached {Number(message.llm_non_cached_input_tokens).toLocaleString()}
	                                </span>
	                              )}
	                              {Number.isFinite(message.llm_cache_setup_input_tokens) &&
	                                message.llm_cache_setup_input_tokens > 0 && (
	                                  <span
	                                    className="message-token-badge"
	                                    title="Estimated input tokens spent while creating Gemini context cache"
	                                  >
	                                    Cache setup {Number(message.llm_cache_setup_input_tokens).toLocaleString()}
	                                  </span>
	                                )}
	                              {hasCostEstimate && (
	                                <span
	                                  className="message-cost-badge"
	                                  title={`Rough INR from pricing × ~${Number(message.cost_estimate?.tokens_estimate ?? 0).toLocaleString()} token estimate.${Number.isFinite(message.llm_input_tokens) ? ` API in ${Number(message.llm_input_tokens).toLocaleString()}.` : ''}${Number.isFinite(message.llm_output_tokens) ? ` API out ${Number(message.llm_output_tokens).toLocaleString()}.` : ''}${Number.isFinite(message.llm_prompt_chars) ? ` Prompt ${Number(message.llm_prompt_chars).toLocaleString()} chars.` : ''}`}
	                                >
	                                  INR {message.cost_estimate.cost_inr_estimate.toFixed(4)}
	                                </span>
	                              )}
	                            </div>
	                            {parallelBranchPlan && parallelBranchPlan.selected.length > 0 && (
	                              <details className="message-parallel-planner-details">
	                                <summary className="message-parallel-planner-summary">
	                                  <span>
	                                    Planned branches: {parallelBranchPlan.entries.map((entry) => entry.label).join(', ')}
	                                  </span>
	                                  {parallelBranchPlan.confidence != null && (
	                                    <span>
	                                      · Confidence {(parallelBranchPlan.confidence * 100).toFixed(0)}%
	                                    </span>
	                                  )}
	                                  {parallelBranchPlan.modelLabel && (
	                                    <span>
	                                      {' '}· Planner {parallelBranchPlan.modelLabel}
	                                    </span>
	                                  )}
	                                </summary>
	                                <div className="message-parallel-planner-content">
	                                  {parallelBranchPlan.entries.map((entry) => (
	                                    <div key={`planner-${message.message_id}-${entry.branch}`} className="message-parallel-planner-row">
	                                      <div className="message-parallel-planner-row-head">
	                                        <strong>{entry.label}</strong>
	                                        <span className="message-parallel-planner-role">
	                                          {entry.required ? 'Required' : entry.optional ? 'Optional' : 'Selected'}
	                                        </span>
	                                        {entry.score != null && (
	                                          <span className="message-parallel-planner-score">
	                                            score {(entry.score * 100).toFixed(0)}%
	                                          </span>
	                                        )}
	                                      </div>
	                                      {entry.reasoning && (
	                                        <div className="message-parallel-planner-reason">
	                                          {entry.reasoning}
	                                        </div>
	                                      )}
	                                    </div>
	                                  ))}
	                                </div>
	                              </details>
	                            )}
	                            {hasParallelStages && (
	                      <div
	                        className="message-parallel-stages"
	                        aria-label="Per-branch LLM usage (parallel chat)"
	                      >
	                        {(() => {
	                          const stages = message.parallel_llm_usage.stages;
	                          const blob = message.parallel_llm_usage.totals || {};
	                          const sumPr = sumParallelStageField(stages, 'input_chars');
	                          const sumRp = sumParallelStageField(stages, 'output_chars');
	                          const sumIn = sumParallelStageField(stages, 'input_tokens');
	                          const sumOut = sumParallelStageField(stages, 'output_tokens');
	                          const sumCachedIn = sumParallelStageField(stages, 'cached_tokens');
	                          const sumNonCachedIn = sumParallelStageField(stages, 'non_cached_input_tokens');
	                          const sumSt = sumParallelStageField(stages, 'static_chars');
	                          const sumDy = sumParallelStageField(stages, 'dynamic_chars');
	                          const blobPr =
	                            blob.input_chars != null ? Number(blob.input_chars) : null;
	                          const blobIn =
	                            blob.input_tokens != null ? Number(blob.input_tokens) : null;
	                          const blobOut =
	                            blob.output_tokens != null ? Number(blob.output_tokens) : null;
	                          const promptBadge = message.llm_prompt_chars;
	                          const inBadge = message.llm_input_tokens;
	                          const outBadge = message.llm_output_tokens;
	                          const stDyMismatch =
	                            stages.length > 0 &&
	                            sumSt > 0 &&
	                            sumDy > 0 &&
	                            sumSt + sumDy !== sumPr;
	                          const warn =
	                            stDyMismatch ||
	                            (blobPr != null && blobPr !== sumPr) ||
	                            (promptBadge != null &&
	                              Number.isFinite(Number(promptBadge)) &&
	                              Number(promptBadge) !== sumPr) ||
	                            (blobIn != null && blobIn !== sumIn) ||
	                            (inBadge != null &&
	                              Number.isFinite(Number(inBadge)) &&
	                              Number(inBadge) !== sumIn) ||
	                            (blobOut != null && blobOut !== sumOut) ||
	                            (outBadge != null &&
	                              Number.isFinite(Number(outBadge)) &&
	                              Number(outBadge) !== sumOut);
	                          const title = [
	                            'Σ = sum of all stage rows (7 branches + merge). Header Prompt/In/Out should match these sums.',
	                            blobPr != null ? `totals.input_chars (stored)=${blobPr}` : null,
	                            sumSt > 0 && sumDy > 0
	                              ? `Σ St+Dy = ${(sumSt + sumDy).toLocaleString()} (should equal Σ Pr)`
	                              : null,
	                            stDyMismatch ? 'Σ St + Σ Dy ≠ Σ Pr — check static/dynamic split' : null,
	                          ]
	                            .filter(Boolean)
	                            .join(' · ');
	                          return (
	                            <div
	                              className={`message-parallel-sum${warn ? ' message-parallel-sum--warn' : ''}`}
	                              title={title}
	                            >
	                              <span className="message-parallel-sum-label">Σ</span>
	                              Pr {sumPr.toLocaleString()}c · Rp {sumRp.toLocaleString()}c · In{' '}
	                              {sumIn.toLocaleString()} · Out {sumOut.toLocaleString()}
	                              {' · '}CIn {sumCachedIn.toLocaleString()} · NCIn {sumNonCachedIn.toLocaleString()}
	                              {sumSt > 0 && sumDy > 0 && (
	                                <>
	                                  {' '}
	                                  · St {sumSt.toLocaleString()}c · Dy {sumDy.toLocaleString()}c
	                                </>
	                              )}
	                              {warn && (
	                                <span className="message-parallel-sum-warn" title="Mismatch detail">
	                                  {' '}
	                                  ⚠
	                                </span>
	                              )}
	                            </div>
	                          );
	                        })()}
	                        {message.parallel_llm_usage.stages.map((st, si) => {
	                          const elapsedLabel = formatParallelElapsed(st.elapsed_ms);
	                          const hasStDy =
	                            st.static_chars != null &&
	                            Number.isFinite(Number(st.static_chars)) &&
	                            st.dynamic_chars != null &&
	                            Number.isFinite(Number(st.dynamic_chars));
	                          const titleParts = [
	                            formatParallelStageLabel(st.stage),
	                            elapsedLabel ? `time ${elapsedLabel}` : null,
	                            hasStDy
	                              ? `static ${Number(st.static_chars).toLocaleString()} chars · dynamic ${Number(
	                                  st.dynamic_chars,
	                                ).toLocaleString()} chars`
	                              : null,
	                            `prompt ${Number(st.input_chars || 0).toLocaleString()} chars · raw out ${Number(
	                              st.output_chars || 0,
	                            ).toLocaleString()} chars`,
	                          ].filter(Boolean);
	                          return (
	                          <span
	                            key={`${st.stage || 'stage'}-${si}`}
	                            className="message-parallel-stage-pill"
	                            title={titleParts.join(' — ')}
	                          >
	                            <span className="message-parallel-stage-name">
	                              {formatParallelStageLabel(st.stage)}
	                            </span>
	                            {elapsedLabel && (
	                              <span
	                                className="message-parallel-chip message-parallel-chip--time"
	                                title="LLM call duration (parallel branches: sum of attempts; merge: single synthesis call)"
	                              >
	                                {elapsedLabel}
	                              </span>
	                            )}
	                            {hasStDy && (
	                              <span
	                                className="message-parallel-chip message-parallel-chip--static"
	                                title="Static portion of the prompt (fixed instructions / role text)"
	                              >
	                                St {Number(st.static_chars).toLocaleString()}c
	                              </span>
	                            )}
	                            {hasStDy && (
	                              <span
	                                className="message-parallel-chip message-parallel-chip--dynamic"
	                                title="Dynamic portion (variable JSON, merge bundle, history slice, etc.)"
	                              >
	                                Dy {Number(st.dynamic_chars).toLocaleString()}c
	                              </span>
	                            )}
	                            <span className="message-parallel-stage-tokens">
	                              {' '}
	                              In {Number(st.input_tokens || 0).toLocaleString()}
	                              {' · '}
	                              Out {Number(st.output_tokens || 0).toLocaleString()}
	                              {' · '}
	                              CIn {Number(st.cached_tokens || 0).toLocaleString()}
	                              {' · '}
	                              NCIn {Number(st.non_cached_input_tokens || 0).toLocaleString()}
	                              {' · '}
	                              Pr {Number(st.input_chars || 0).toLocaleString()}c
	                              {' · '}
	                              Rp {Number(st.output_chars || 0).toLocaleString()}c
	                              {st.success === false ? ' ⚠' : ''}
	                            </span>
	                          </span>
	                          );
	                        })}
	                      </div>
	                            )}
	                          </div>
	                        </details>
	                      )}
	                      <span className="message-time">{formatDate(message.timestamp)}</span>
	                    </div>
	                  </div>
	                  );
	                })}
              </div>
            </div>
          ) : (
            <div className="session-detail-empty">
              <div className="session-detail-empty-inner">
                <span className="session-detail-empty-icon" aria-hidden="true">
                  💬
                </span>
                <p className="session-detail-empty-title">Select a user</p>
                <p className="session-detail-empty-text">
                  Choose a user on the left to open their full timeline: newest exchanges first, with
                  each question above its answer. Assistant replies use the full width for easier reading.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
    {branchModal.open && (
      <div className="admin-branch-modal-overlay" onClick={closeBranchModal}>
        <div className="admin-branch-modal" onClick={(e) => e.stopPropagation()}>
          <div className="admin-branch-modal-header">
            <h3>Branch analysis • Msg #{branchModal.messageId}</h3>
            <button type="button" className="admin-branch-modal-close" onClick={closeBranchModal}>
              ×
            </button>
          </div>
          <div className="admin-branch-modal-body">
            {branchModal.loading && <p>Loading branch analysis…</p>}
            {!branchModal.loading && branchModal.error && (
              <p className="admin-branch-modal-error">{branchModal.error}</p>
            )}
            {!branchModal.loading && !branchModal.error && !branchModal.payload && (
              <p>No branch analysis found for this message.</p>
            )}
            {!branchModal.loading && !branchModal.error && branchModal.payload && (
              <div className="admin-branch-sections">
                {['parashari', 'jaimini', 'nadi', 'nakshatra', 'kp', 'ashtakavarga', 'sudarshan'].map((key) => {
                  const node = branchModal.payload?.[key];
                  if (!node || typeof node !== 'object') return null;
                  const bullets = Array.isArray(node.bullets) ? node.bullets.filter(Boolean) : [];
                  const analysis = stripBranchNoise(node.analysis || '');
                  if (!analysis && bullets.length === 0) return null;
                  return (
                    <details key={key} className="admin-branch-section">
                      <summary>{getBranchTitle(key)}</summary>
                      {bullets.length > 0 && (
                        <ul className="admin-branch-bullets">
                          {bullets.slice(0, 12).map((b, i) => (
                            <li
                              key={`${key}-b-${i}`}
                              dangerouslySetInnerHTML={{
                                __html: formatMessageContent(stripBranchNoise(b)),
                              }}
                            />
                          ))}
                        </ul>
                      )}
                      {analysis && (
                        <div
                          className="admin-branch-analysis enhanced-formatting"
                          dangerouslySetInnerHTML={{ __html: formatMessageContent(analysis) }}
                        />
                      )}
                    </details>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    )}
    {qaModal.open && (
      <div className="admin-branch-modal-overlay" onClick={closeQaModal}>
        <div className="admin-branch-modal admin-qa-modal" onClick={(e) => e.stopPropagation()}>
          <div className="admin-branch-modal-header">
            <h3>Astrology QA exam • Msg #{qaModal.messageId}</h3>
            <button type="button" className="admin-branch-modal-close" onClick={closeQaModal}>
              ×
            </button>
          </div>
          <div className="admin-branch-modal-body">
            <p className="admin-qa-intro">
              Senior jyotishi exam on Gemini Pro with rebuilt generation context (chart/dasha/divisional spine),
              prior turns, and branch outputs. Checks technical claims against that context — not just narrative polish.
            </p>
            <label className="admin-qa-notes-label" htmlFor={`admin-qa-notes-${qaModal.messageId}`}>
              Examiner notes (optional)
            </label>
            <textarea
              id={`admin-qa-notes-${qaModal.messageId}`}
              className="admin-qa-notes"
              rows={3}
              value={qaModal.adminNotes}
              disabled={qaModal.loading}
              placeholder="e.g. User says July window was promised as offer; check drift vs Aug 28 rewrite"
              onChange={(e) =>
                setQaModal((prev) => ({
                  ...prev,
                  adminNotes: e.target.value,
                }))
              }
            />
            <div className="admin-qa-actions">
              <button
                type="button"
                className="message-branch-btn message-qa-btn"
                onClick={runResponseQa}
                disabled={qaModal.loading}
              >
                {qaModal.loading ? 'Examining…' : qaModal.result ? 'Re-run exam' : 'Run exam'}
              </button>
            </div>
            {qaModal.loading && (
              <p className="admin-qa-loading">
                {qaModal.phase === 'run'
                  ? 'Rebuilding generation context + running deterministic precheck + Gemini Pro examiner…'
                  : 'Loading saved exam…'}
              </p>
            )}
            {!qaModal.loading && qaModal.error && (
              <p className="admin-branch-modal-error">{qaModal.error}</p>
            )}
            {!qaModal.loading && !qaModal.error && !qaModal.result?.report && (
              <p className="admin-qa-intro" style={{ marginTop: 4 }}>
                No saved exam for this message yet. Click <strong>Run exam</strong> to generate one.
              </p>
            )}
            {!qaModal.loading && qaModal.result?.report && (
              <div className="admin-qa-report">
                {(() => {
                  const report = qaModal.result.report;
                  const findings = Array.isArray(report.findings) ? report.findings : [];
                  const layers = report.layers && typeof report.layers === 'object' ? report.layers : {};
                  const timing = report.timing_contract && typeof report.timing_contract === 'object'
                    ? report.timing_contract
                    : {};
                  const proposals = Array.isArray(report.prompt_rule_proposals)
                    ? report.prompt_rule_proposals
                    : [];
                  const preFlags = Array.isArray(report.deterministic_precheck?.flags)
                    ? report.deterministic_precheck.flags
                    : [];
                  return (
                    <>
                      <div className="admin-qa-score-row">
                        <span className={`admin-qa-grade ${gradeClass(report.overall_grade)}`}>
                          Grade {report.overall_grade || '—'}
                        </span>
                        <span className={`admin-qa-sev ${severityClass(report.trust_risk)}`}>
                          Trust risk: {report.trust_risk || '—'}
                        </span>
                        <span className="admin-qa-meta-chip">
                          Branches {qaModal.result.branch_analysis_found ? 'found' : 'missing'}
                        </span>
                        <span className="admin-qa-meta-chip">
                          Prior turns {qaModal.result.prior_turn_count ?? 0}
                        </span>
                        <span className="admin-qa-meta-chip">
                          Gen context{' '}
                          {qaModal.result.generation_context?.ok ||
                          report.evidence_available?.has_generation_context
                            ? `yes (${Math.round(
                                (qaModal.result.generation_context?.char_count ||
                                  report.evidence_available?.generation_context_chars ||
                                  0) / 1000,
                              )}k)`
                            : 'missing'}
                        </span>
                        {report.auditor_meta?.forced_pro && (
                          <span className="admin-qa-meta-chip">
                            Pro {report.auditor_meta?.requested_model || report.auditor_meta?.model || 'gemini'}
                          </span>
                        )}
                        {qaModal.result.stored && (
                          <span className="admin-qa-meta-chip" title={qaModal.result.stored_at || ''}>
                            Saved{qaModal.result.stored_at ? ` · ${formatDate(qaModal.result.stored_at)}` : ''}
                          </span>
                        )}
                      </div>
                      {qaModal.result.generation_context?.error && !qaModal.result.generation_context?.ok && (
                        <p className="admin-branch-modal-error">
                          Generation context rebuild failed: {qaModal.result.generation_context.error}
                        </p>
                      )}
                      {report.executive_summary && (
                        <div className="admin-qa-block">
                          <h4>Exam summary</h4>
                          <p>{report.executive_summary}</p>
                        </div>
                      )}
                      {report.corrected_executive_summary && (
                        <div className="admin-qa-block admin-qa-block--fix">
                          <h4>Corrected executive summary</h4>
                          <p>{report.corrected_executive_summary}</p>
                        </div>
                      )}
                      <div className="admin-qa-block">
                        <h4>Layer scores</h4>
                        <div className="admin-qa-layers">
                          {Object.entries(layers).map(([key, val]) => (
                            <div key={key} className="admin-qa-layer">
                              <div className="admin-qa-layer-title">
                                <strong>{key.replace(/_/g, ' ')}</strong>
                                <span className={`admin-qa-sev ${severityClass(val?.status === 'fail' ? 'high' : val?.status === 'warn' ? 'medium' : 'low')}`}>
                                  {val?.status || '—'}
                                </span>
                              </div>
                              {val?.notes ? <p>{val.notes}</p> : null}
                            </div>
                          ))}
                        </div>
                      </div>
                      {(timing.primary_window || timing.activation_window || timing.result_window || timing.consistency_with_prior) && (
                        <div className="admin-qa-block">
                          <h4>Timing contract</h4>
                          <ul className="admin-qa-list">
                            {timing.activation_window ? <li><strong>Activation:</strong> {timing.activation_window}</li> : null}
                            {timing.result_window ? <li><strong>Result:</strong> {timing.result_window}</li> : null}
                            {timing.primary_window ? <li><strong>Primary claimed:</strong> {timing.primary_window}</li> : null}
                            {timing.consistency_with_prior ? (
                              <li><strong>Vs prior:</strong> {timing.consistency_with_prior}</li>
                            ) : null}
                          </ul>
                        </div>
                      )}
                      {preFlags.length > 0 && (
                        <div className="admin-qa-block">
                          <h4>Deterministic precheck flags</h4>
                          <ul className="admin-qa-list">
                            {preFlags.map((f, i) => (
                              <li key={`pre-${i}`}>
                                <span className={`admin-qa-sev ${severityClass(f.severity)}`}>{f.severity}</span>{' '}
                                <strong>{f.category}</strong> — {f.note}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <div className="admin-qa-block">
                        <h4>Findings ({findings.length})</h4>
                        {findings.length === 0 ? (
                          <p>No findings returned.</p>
                        ) : (
                          <div className="admin-qa-findings">
                            {findings.map((f, i) => (
                              <details key={f.id || `f-${i}`} className="admin-qa-finding" open={i < 3}>
                                <summary>
                                  <span className={`admin-qa-sev ${severityClass(f.severity)}`}>{f.severity || '—'}</span>
                                  <strong>{f.category || 'finding'}</strong>
                                  {f.claim_in_answer ? ` — ${String(f.claim_in_answer).slice(0, 120)}` : ''}
                                </summary>
                                <div className="admin-qa-finding-body">
                                  {f.evidence_problem ? (
                                    <p><strong>Problem:</strong> {f.evidence_problem}</p>
                                  ) : null}
                                  {f.classical_correction ? (
                                    <p><strong>Classical correction:</strong> {f.classical_correction}</p>
                                  ) : null}
                                  {f.product_fix ? (
                                    <p><strong>Product fix:</strong> {f.product_fix}</p>
                                  ) : null}
                                </div>
                              </details>
                            ))}
                          </div>
                        )}
                      </div>
                      {proposals.length > 0 && (
                        <div className="admin-qa-block">
                          <h4>Prompt / rule proposals</h4>
                          <ul className="admin-qa-list">
                            {proposals.map((p, i) => (
                              <li key={`prop-${i}`}>{p}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {report.knowledge_test_notes && (
                        <div className="admin-qa-block">
                          <h4>Knowledge-test notes</h4>
                          <p>{report.knowledge_test_notes}</p>
                        </div>
                      )}
                      {qaModal.result.question && (
                        <details className="admin-qa-block">
                          <summary>Question under exam</summary>
                          <p className="admin-qa-mono">{qaModal.result.question}</p>
                        </details>
                      )}
                      {report.auditor_meta && (
                        <p className="admin-qa-footer-meta">
                          Examiner {report.auditor_meta.provider || '—'} / {report.auditor_meta.model || '—'}
                          {report.auditor_meta.elapsed_total_s != null
                            ? ` · ${report.auditor_meta.elapsed_total_s}s`
                            : ''}
                        </p>
                      )}
                    </>
                  );
                })()}
              </div>
            )}
          </div>
        </div>
      </div>
    )}
    </>
  );
};

export default AdminChatHistory;
