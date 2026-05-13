/**
 * Admin web: build HTML + download PDF for event timeline (same content shape as mobile pdfGenerator).
 * Uses html2canvas + jsPDF image paging — jsPDF's html() often rasterizes blank for off-DOM / fixed nodes.
 */
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';

const COLORS_PRIMARY = '#f97316';

const EVENT_MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function escapeHtml(text) {
  if (text == null || text === '') return '';
  const s = String(text);
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function getEventMonthName(monthId) {
  const idx = Math.max(0, Math.min(Number(monthId) - 1, 11));
  return EVENT_MONTH_NAMES[idx] || 'Month';
}

function getIntensityColor(intensity) {
  switch ((intensity || '').toLowerCase()) {
    case 'high':
      return '#FF4444';
    case 'medium':
      return '#FFAA00';
    default:
      return '#4CAF50';
  }
}

/**
 * @param {{ year: number, nativeName?: string|null, monthlyData: object, logoSrc?: string|null, titleLine?: string }} p
 */
export function buildEventTimelineInnerHtml({
  year,
  nativeName,
  monthlyData,
  logoSrc = null,
  titleLine = null,
}) {
  const trends = monthlyData?.macro_trends || [];
  const monthly = monthlyData?.monthly_predictions || [];
  const isSingleMonth = monthly.length === 1;
  const defaultTitle = isSingleMonth
    ? `Monthly deep dive — ${getEventMonthName(monthly[0]?.month_id)} ${year}`
    : `Major Life Events — ${year}`;
  const title = titleLine || defaultTitle;

  const accordionsHtml = monthly
    .map((month) => {
      const monthName = getEventMonthName(month.month_id);
      const tags = month.focus_areas || [];
      const events = month.events || [];
      const tagsHtml = tags.length
        ? `<div class="event-tags">${tags.map((t) => `<span class="event-tag">${escapeHtml(t)}</span>`).join('')}</div>`
        : '';
      const eventsHtml = events
        .map((ev) => {
          const intensityColor = getIntensityColor(ev.intensity);
          const manifestations = ev.possible_manifestations || [];
          const manifestationsHtml = manifestations.length
            ? `<div class="manifestations">
              <div class="manifestations-title">Possible Scenarios (${manifestations.length})</div>
              ${manifestations
                .map((m, idx) => {
                  const scenario = typeof m === 'string' ? m : m?.scenario || '';
                  const reasoning = typeof m === 'object' && m != null ? m.reasoning : null;
                  return `<div class="manifestation-item">
                  <span class="manifestation-num">${idx + 1}</span>
                  <div>${scenario ? `<div class="manifestation-scenario">${escapeHtml(scenario)}</div>` : ''}${
                    reasoning
                      ? `<div class="manifestation-reasoning"><strong>Why:</strong> ${escapeHtml(reasoning)}</div>`
                      : ''
                  }</div>
                </div>`;
                })
                .join('')}
            </div>`
            : '';
          const datesHtml =
            ev.start_date && ev.end_date
              ? `<div class="event-dates">📅 ${escapeHtml(ev.start_date)} to ${escapeHtml(ev.end_date)}</div>`
              : '';
          const triggerHtml = ev.trigger_logic
            ? `<div class="event-trigger">🎯 ${escapeHtml(ev.trigger_logic)}</div>`
            : '';
          return `
          <div class="event-block">
            <span class="event-dot" style="background:${intensityColor}"></span>
            <div class="event-body">
              <div class="event-type">${escapeHtml(ev.type || '')}</div>
              <div class="event-prediction">${escapeHtml(ev.prediction || '')}</div>
              ${manifestationsHtml}
              ${datesHtml}
              ${triggerHtml}
            </div>
          </div>`;
        })
        .join('');
      return `
        <div class="accordion-section">
          <div class="accordion-month">${escapeHtml(monthName)}</div>
          ${tagsHtml}
          <div class="accordion-events">${eventsHtml}</div>
        </div>`;
    })
    .join('');

  const trendsHtml = trends.length
    ? `<div class="macro-section">
          <div class="macro-title">The Vibe of ${year}</div>
          <ul class="macro-list">${trends.map((t) => `<li>${escapeHtml(t)}</li>`).join('')}</ul>
        </div>`
    : '';

  const safeLogo = logoSrc ? String(logoSrc).replace(/"/g, '').replace(/'/g, '').replace(/[<>]/g, '') : '';
  const logoBlock = safeLogo
    ? `<img src="${safeLogo}" class="logo" alt="AstroRoshni" crossorigin="anonymous" />`
    : '<div class="logo-fallback">🔮</div>';

  return `
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      .container { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #fff; padding: 16px; color: #2c3e50; line-height: 1.55; font-size: 13px; max-width: 720px; }
      .header { text-align: center; margin-bottom: 18px; padding-bottom: 14px; border-bottom: 3px solid ${COLORS_PRIMARY}; }
      .logo { width: 48px; height: 48px; margin: 0 auto 8px; display: block; object-fit: contain; }
      .logo-fallback { font-size: 28px; margin-bottom: 6px; text-align: center; }
      .title { font-size: 18px; font-weight: 700; color: ${COLORS_PRIMARY}; margin-bottom: 4px; }
      .subtitle { font-size: 12px; color: #6b7280; }
      .macro-section { margin-bottom: 16px; padding: 14px; background: rgba(249, 115, 22, 0.08); border-radius: 10px; border-left: 4px solid ${COLORS_PRIMARY}; }
      .macro-title { font-size: 15px; font-weight: 700; color: ${COLORS_PRIMARY}; margin-bottom: 8px; }
      .macro-list { margin-left: 18px; font-size: 12px; }
      .macro-list li { margin: 4px 0; }
      .section-label { font-size: 14px; font-weight: 700; color: ${COLORS_PRIMARY}; margin: 16px 0 8px 0; }
      .accordion-section { margin-bottom: 14px; padding: 12px; background: #fef7f0; border-radius: 10px; border: 1px solid #fed7d7; }
      .accordion-month { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: ${COLORS_PRIMARY}; margin-bottom: 8px; }
      .event-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
      .event-tag { font-size: 11px; font-weight: 600; padding: 4px 8px; border-radius: 6px; background: #fff; color: #6b7280; }
      .accordion-events { display: flex; flex-direction: column; gap: 10px; }
      .event-block { display: flex; gap: 8px; align-items: flex-start; }
      .event-dot { width: 8px; height: 8px; border-radius: 4px; flex-shrink: 0; margin-top: 6px; }
      .event-body { flex: 1; }
      .event-type { font-size: 12px; font-weight: 700; margin-bottom: 4px; }
      .event-prediction { font-size: 12px; line-height: 1.5; margin-bottom: 6px; }
      .manifestations { margin-top: 8px; margin-bottom: 6px; }
      .manifestations-title { font-size: 11px; font-weight: 700; color: ${COLORS_PRIMARY}; margin-bottom: 6px; }
      .manifestation-item { display: flex; gap: 8px; padding: 8px; border-radius: 8px; border-left: 3px solid ${COLORS_PRIMARY}; background: #fff; margin-bottom: 6px; }
      .manifestation-num { width: 22px; height: 22px; border-radius: 11px; background: ${COLORS_PRIMARY}; color: white; font-size: 11px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
      .manifestation-scenario { font-size: 11px; font-weight: 600; margin-bottom: 4px; }
      .manifestation-reasoning { font-size: 10px; font-style: italic; color: #6b7280; }
      .event-dates { font-size: 11px; font-weight: 600; color: ${COLORS_PRIMARY}; margin-top: 4px; }
      .event-trigger { font-size: 10px; font-style: italic; color: #6b7280; margin-top: 4px; }
      .footer { margin-top: 20px; padding-top: 12px; border-top: 2px solid #f0f0f0; text-align: center; color: #6b7280; font-size: 10px; }
      .disclaimer-title { font-weight: 700; margin-bottom: 4px; }
      .disclaimer-text { font-size: 10px; line-height: 1.45; }
    </style>
    <div class="container">
      <div class="header">
        ${logoBlock}
        <div class="title">${escapeHtml(title)}</div>
        ${nativeName ? `<div class="subtitle">${escapeHtml(nativeName)}</div>` : ''}
        <div class="subtitle">${escapeHtml(new Date().toLocaleString())}</div>
      </div>
      ${trendsHtml}
      <div class="section-label">📅 ${isSingleMonth ? 'This month' : 'Monthly guide'}</div>
      ${accordionsHtml}
      <div class="footer">
        <div class="disclaimer-title">Important Disclaimer</div>
        <div class="disclaimer-text">
          This event timeline is based on traditional Vedic astrological analysis and is intended for spiritual insight and personal reflection only.
          It is <strong>not</strong> a substitute for professional medical, legal, psychological or financial advice.
        </div>
        <div style="margin-top: 16px;">Generated by AstroRoshni</div>
      </div>
    </div>
  `;
}

function safeFilePart(s) {
  return String(s || 'user')
    .replace(/[^a-z0-9-_]+/gi, '_')
    .replace(/_+/g, '_')
    .slice(0, 36);
}

/**
 * Renders timeline HTML to a PDF file download (browser).
 */
export async function downloadEventTimelinePdf({
  year,
  nativeName,
  monthlyData,
  fileNameBase = 'event-timeline',
  logoSrc = null,
}) {
  const wrap = document.createElement('div');
  wrap.style.position = 'fixed';
  wrap.style.left = '-12000px';
  wrap.style.top = '0';
  wrap.style.width = '720px';
  wrap.style.background = '#fff';
  wrap.innerHTML = buildEventTimelineInnerHtml({ year, nativeName, monthlyData, logoSrc });
  document.body.appendChild(wrap);

  const doc = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'portrait' });
  try {
    await doc.html(wrap, {
      margin: [8, 8, 8, 8],
      autoPaging: 'text',
      html2canvas: {
        scale: 0.62,
        useCORS: true,
        logging: false,
        letterRendering: true,
      },
      width: 186,
      windowWidth: 720,
      callback: (d) => {
        const name = `${safeFilePart(fileNameBase)}.pdf`;
        d.save(name);
      },
    });
  } finally {
    document.body.removeChild(wrap);
  }
}
