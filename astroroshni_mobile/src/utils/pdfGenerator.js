import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import * as FileSystem from 'expo-file-system';
import { Asset } from 'expo-asset';
import { COLORS } from './constants';

const logoCacheByModuleId = new Map();

/**
 * Load logo as data URI from a required asset (e.g. require('../../assets/logo.png')).
 * Call from a component so the require path resolves correctly; pass result to generatePDF / generateEventTimelinePDF.
 */
export async function getLogoDataUriForModule(assetModule) {
  const id = typeof assetModule === 'number' ? assetModule : (assetModule?.uri ?? assetModule);
  if (logoCacheByModuleId.get(id)) return logoCacheByModuleId.get(id);
  try {
    const asset = Asset.fromModule(assetModule);
    await asset.downloadAsync();
    let base64 = null;
    if (asset.localUri) {
      base64 = await FileSystem.readAsStringAsync(asset.localUri, {
        encoding: FileSystem.EncodingType.Base64,
      });
    }
    const dataUri = base64 ? `data:image/png;base64,${base64}` : null;
    if (dataUri) logoCacheByModuleId.set(id, dataUri);
    return dataUri;
  } catch (e) {
    console.warn('Could not load logo for PDF:', e?.message);
    return null;
  }
}

export const generatePDF = async (message, options = {}) => {
  try {
    console.log('📄 [PDF] Starting generation...');
    console.log('📄 [PDF] Has summary_image:', !!message.summary_image);
    const logoDataUri = options.logoDataUri ?? null;

    // Clean and format the content
    const cleanContent = message.content
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&amp;/g, '&')
      .replace(/&#39;/g, "'")
      .replace(/&nbsp;/g, ' ');

    console.log('📄 [PDF] Content cleaned, length:', cleanContent.length);

    // Create HTML with exact same styling as mobile app
    const html = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            * {
              margin: 0;
              padding: 0;
              box-sizing: border-box;
            }
            
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              background: linear-gradient(135deg, #fefcfb 0%, #fef7f0 100%);
              padding: 20px;
              color: #2c3e50;
              line-height: 1.6;
              font-size: 22px;
            }
            
            .container {
              max-width: 800px;
              margin: 0 auto;
              background: white;
              border-radius: 20px;
              padding: 30px;
              box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            }
            
            .header {
              text-align: center;
              margin-bottom: 30px;
              padding-bottom: 20px;
              border-bottom: 3px solid ${COLORS.primary};
            }
            
            .logo {
              width: 56px;
              height: 56px;
              margin: 0 auto 10px;
              display: block;
              object-fit: contain;
            }
            .logo-fallback { font-size: 32px; margin-bottom: 10px; text-align: center; }
            
            .title {
              font-size: 24px;
              font-weight: 700;
              color: ${COLORS.primary};
              margin-bottom: 5px;
            }
            
            .timestamp {
              font-size: 18px;
              color: #6b7280;
            }
            
            .summary-image {
              width: 100%;
              max-width: 500px;
              height: auto;
              margin: 20px auto;
              display: block;
              border-radius: 12px;
              box-shadow: 0 4px 16px rgba(0,0,0,0.15);
            }
            
            .content {
              margin-top: 20px;
              font-size: 22px;
            }
            
            .content div {
              font-size: 22px;
            }
            
            .content span {
              font-size: 22px;
            }
            
            .quick-answer-card {
              background-color: #FFF9E6 !important;
              border-radius: 16px;
              padding: 20px;
              margin: 20px 0;
              border: 2px solid #FFD700;
              box-shadow: 0 4px 12px rgba(255, 215, 0, 0.2);
            }
            
            .quick-answer-header {
              display: flex;
              align-items: center;
              margin-bottom: 12px;
              background: transparent !important;
            }
            
            .lightning {
              font-size: 20px;
              margin-right: 8px;
            }
            
            .card-title {
              font-size: 22px;
              font-weight: 700;
              color: #2c3e50;
              background: transparent !important;
            }
            
            .card-text {
              font-size: 22px;
              color: #2c3e50;
              line-height: 1.8;
              background: transparent !important;
            }
            
            .final-thoughts-card {
              background-color: #E6F3FF !important;
              border-radius: 16px;
              padding: 20px;
              margin: 20px 0;
              border: 2px solid #B0E0E6;
              box-shadow: 0 4px 12px rgba(176, 224, 230, 0.3);
            }
            
            .section-header {
              display: flex;
              align-items: center;
              margin: 24px 0 12px 0;
              padding: 12px 16px;
              background: rgba(255, 107, 53, 0.08);
              border-radius: 12px;
              border-left: 4px solid ${COLORS.primary};
            }
            
            .section-icon {
              font-size: 20px;
              margin-right: 10px;
            }
            
            .section-title {
              font-size: 22px;
              font-weight: 700;
              color: ${COLORS.primary};
            }
            
            .list-item {
              display: flex;
              align-items: flex-start;
              margin: 12px 0;
            }
            
            .number-circle {
              width: 24px;
              height: 24px;
              border-radius: 12px;
              background: ${COLORS.primary};
              color: white;
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 12px;
              font-weight: 700;
              margin-right: 12px;
              flex-shrink: 0;
              margin-top: 2px;
            }
            
            .list-text {
              flex: 1;
              font-size: 22px;
              line-height: 1.8;
            }
            
            p {
              margin: 12px 0;
              font-size: 22px;
              line-height: 1.8;
              background: transparent;
            }
            
            .quick-answer-card p,
            .quick-answer-card div,
            .quick-answer-card span {
              background: transparent !important;
            }
            
            .final-thoughts-card p,
            .final-thoughts-card div,
            .final-thoughts-card span {
              background: transparent !important;
            }
            
            strong, b {
              font-weight: 700;
              color: #1a1a1a;
              font-size: 22px;
            }
            
            em, i {
              font-style: italic;
              font-size: 22px;
            }
            
            .footer {
              margin-top: 40px;
              padding-top: 20px;
              border-top: 2px solid #f0f0f0;
              text-align: center;
              color: #6b7280;
              font-size: 18px;
            }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              ${logoDataUri ? `<img src="${logoDataUri}" class="logo" alt="AstroRoshni" />` : '<div class="logo-fallback">🔮</div>'}
              <div class="title">AstroRoshni Prediction</div>
              <div class="timestamp">${new Date(message.timestamp).toLocaleString()}</div>
            </div>
            
            ${message.summary_image ? `<img src="${message.summary_image}" class="summary-image" alt="Analysis Summary" />` : ''}
            
            <div class="content">
              ${formatContentForPDF(cleanContent)}
            </div>
            
            <div class="footer">
              Generated by AstroRoshni App<br>
              Your Personal Vedic Astrology Guide
            </div>
          </div>
        </body>
      </html>
    `;

    console.log('📄 [PDF] HTML generated, length:', html.length);
    console.log('📄 [PDF] Calling Print.printToFileAsync...');

    // Generate PDF with image included
    const { uri } = await Promise.race([
      Print.printToFileAsync({ 
        html,
        base64: false
      }),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('PDF generation timeout')), 45000)
      )
    ]);
    
    console.log('✅ [PDF] Generated successfully:', uri);
    return uri;
  } catch (error) {
    console.error('❌ [PDF] Generation error:', error);
    throw error;
  }
};

const formatContentForPDF = (content) => {
  let formatted = content;
  
  // Handle Quick Answer cards
  formatted = formatted.replace(
    /<div class="quick-answer-card">(.*?)<\/div>/gs,
    (match, cardContent) => {
      const cleanContent = cardContent
        .replace(/<[^>]*>/g, '')
        .replace(/Quick Answer/g, '')
        .replace(/^:\s*/, '')
        .trim();
      return `
        <div style="background-color: #FFF9E6; border-radius: 16px; padding: 20px; margin: 20px 0; border: 2px solid #FFD700;">
          <div style="display: flex; align-items: center; margin-bottom: 12px; background: transparent;">
            <span style="font-size: 20px; margin-right: 8px;">⚡</span>
            <span style="font-size: 22px; font-weight: 700; color: #2c3e50;">Quick Answer</span>
          </div>
          <div style="font-size: 22px; color: #2c3e50; line-height: 1.8; background: transparent;">${cleanContent}</div>
        </div>
      `;
    }
  );
  
  // Handle Final Thoughts cards
  formatted = formatted.replace(
    /<div class="final-thoughts-card">(.*?)<\/div>/gs,
    (match, cardContent) => {
      const cleanContent = cardContent
        .replace(/<[^>]*>/g, '')
        .replace(/Final Thoughts/g, '')
        .trim();
      return `
        <div style="background-color: #E6F3FF; border-radius: 16px; padding: 20px; margin: 20px 0; border: 2px solid #B0E0E6;">
          <div style="font-size: 22px; font-weight: 700; color: #2c3e50; margin-bottom: 8px;">◆ Final Thoughts</div>
          <div style="font-size: 22px; color: #2c3e50; line-height: 1.8; background: transparent;">${cleanContent}</div>
        </div>
      `;
    }
  );
  
  // Handle markdown headers and bullet points with section-based counter reset
  let sectionCounter = {};
  let currentSection = 'default';
  
  // Replace headers and track sections
  formatted = formatted.replace(/^(####|###|##)\s+(.+)$/gm, (match, level, headerText) => {
    const symbol = getHeaderSymbol(headerText);
    currentSection = headerText;
    sectionCounter[currentSection] = 0;
    return `
      <div class="section-header" data-section="${currentSection}">
        <span class="section-icon">${symbol}</span>
        <span class="section-title">${headerText}</span>
      </div>
    `;
  });
  
  // Handle bullet points with section-aware counter
  formatted = formatted.replace(/^[•\-]\s+(.+)$/gm, (match, text, offset) => {
    // Find the last section header before this bullet
    const beforeText = formatted.substring(0, offset);
    const lastSectionMatch = beforeText.match(/data-section="([^"]+)"/g);
    
    if (lastSectionMatch) {
      const lastSection = lastSectionMatch[lastSectionMatch.length - 1].match(/data-section="([^"]+)"/)[1];
      if (!sectionCounter[lastSection]) sectionCounter[lastSection] = 0;
      sectionCounter[lastSection]++;
      const num = sectionCounter[lastSection];
      
      return `
      <div class="list-item">
        <div class="number-circle">${num}</div>
        <div class="list-text">${text}</div>
      </div>
    `;
    } else {
      if (!sectionCounter['default']) sectionCounter['default'] = 0;
      sectionCounter['default']++;
      return `
      <div class="list-item">
        <div class="number-circle">${sectionCounter['default']}</div>
        <div class="list-text">${text}</div>
      </div>
    `;
    }
  });
  
  // Handle bold text
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Handle italic text
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Handle paragraphs - use div instead of p to avoid white background issues
  formatted = formatted.replace(/\n\n+/g, '</div><div style="margin: 12px 0; font-size: 22px; line-height: 1.8;">');
  formatted = `<div style="margin: 12px 0; font-size: 22px; line-height: 1.8;">${formatted}</div>`;
  
  return formatted;
};

const getHeaderSymbol = (headerText) => {
  const text = headerText.toLowerCase();
  if (text.includes('life stage') || text.includes('context')) return '🌱';
  if (text.includes('astrological analysis') || text.includes('analysis')) return '🔍';
  if (text.includes('career') || text.includes('profession')) return '💼';
  if (text.includes('nakshatra') || text.includes('star')) return '⭐';
  if (text.includes('timing') && text.includes('guidance')) return '⏰';
  if (text.includes('timing') || text.includes('time')) return '🕐';
  if (text.includes('guidance') || text.includes('advice')) return '🌟';
  if (text.includes('final thoughts') || text.includes('thoughts')) return '💭';
  if (text.includes('relationship') || text.includes('love') || text.includes('marriage')) return '💕';
  if (text.includes('health') || text.includes('wellness')) return '🌿';
  if (text.includes('finance') || text.includes('money') || text.includes('wealth')) return '💰';
  return '✨';
};

const EVENT_MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const getEventMonthName = (monthId) => {
  const idx = Math.max(0, Math.min(Number(monthId) - 1, 11));
  return EVENT_MONTH_NAMES[idx] || 'Month';
};

const getIntensityColor = (intensity) => {
  switch ((intensity || '').toLowerCase()) {
    case 'high': return '#FF4444';
    case 'medium': return '#FFAA00';
    default: return '#4CAF50';
  }
};

/**
 * Generate PDF for Event Screen timeline (year + macro trends + all monthly accordions).
 * @param {{ year: number, nativeName: string, monthlyData: { macro_trends?: string[], monthly_predictions?: Array<{ month_id: number, focus_areas?: string[], events?: any[] }> } }} params
 */
export const generateEventTimelinePDF = async ({ year, nativeName, monthlyData, logoDataUri: optionLogoUri } = {}) => {
  try {
    const logoDataUri = optionLogoUri ?? null;
    const trends = monthlyData?.macro_trends || [];
    const monthly = monthlyData?.monthly_predictions || [];

    const accordionsHtml = monthly.map((month) => {
      const monthName = getEventMonthName(month.month_id);
      const tags = month.focus_areas || [];
      const events = month.events || [];
      const tagsHtml = tags.length
        ? `<div class="event-tags">${tags.map((t) => `<span class="event-tag">${escapeHtml(t)}</span>`).join('')}</div>`
        : '';
      const eventsHtml = events.map((ev) => {
        const intensityColor = getIntensityColor(ev.intensity);
        const manifestations = ev.possible_manifestations || [];
        const manifestationsHtml = manifestations.length
          ? `<div class="manifestations">
              <div class="manifestations-title">Possible Scenarios (${manifestations.length})</div>
              ${manifestations.map((m, idx) => {
                const scenario = typeof m === 'string' ? m : (m?.scenario || '');
                const reasoning = typeof m === 'object' && m != null ? m.reasoning : null;
                return `<div class="manifestation-item">
                  <span class="manifestation-num">${idx + 1}</span>
                  <div>${scenario ? `<div class="manifestation-scenario">${escapeHtml(scenario)}</div>` : ''}${reasoning ? `<div class="manifestation-reasoning"><strong>Why:</strong> ${escapeHtml(reasoning)}</div>` : ''}</div>
                </div>`;
              }).join('')}
            </div>`
          : '';
        const datesHtml = ev.start_date && ev.end_date ? `<div class="event-dates">📅 ${escapeHtml(ev.start_date)} to ${escapeHtml(ev.end_date)}</div>` : '';
        const triggerHtml = ev.trigger_logic ? `<div class="event-trigger">🎯 ${escapeHtml(ev.trigger_logic)}</div>` : '';
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
      }).join('');
      return `
        <div class="accordion-section">
          <div class="accordion-month">${escapeHtml(monthName)}</div>
          ${tagsHtml}
          <div class="accordion-events">${eventsHtml}</div>
        </div>`;
    }).join('');

    const trendsHtml = trends.length
      ? `<div class="macro-section">
          <div class="macro-title">The Vibe of ${year}</div>
          <ul class="macro-list">${trends.map((t) => `<li>${escapeHtml(t)}</li>`).join('')}</ul>
        </div>`
      : '';

    const html = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #fefcfb; padding: 20px; color: #2c3e50; line-height: 1.6; font-size: 20px; }
            .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 20px; padding: 30px; box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 3px solid ${COLORS.primary}; }
            .logo { width: 64px; height: 64px; margin: 0 auto 12px; display: block; object-fit: contain; }
            .logo-fallback { font-size: 36px; margin-bottom: 8px; text-align: center; }
            .title { font-size: 26px; font-weight: 700; color: ${COLORS.primary}; margin-bottom: 4px; }
            .subtitle { font-size: 20px; color: #6b7280; }
            .macro-section { margin-bottom: 24px; padding: 20px; background: rgba(249, 115, 22, 0.08); border-radius: 12px; border-left: 4px solid ${COLORS.primary}; }
            .macro-title { font-size: 22px; font-weight: 700; color: ${COLORS.primary}; margin-bottom: 12px; }
            .macro-list { margin-left: 24px; font-size: 20px; }
            .macro-list li { margin: 8px 0; }
            .section-label { font-size: 22px; font-weight: 700; color: ${COLORS.primary}; margin: 24px 0 12px 0; }
            .accordion-section { margin-bottom: 24px; padding: 20px; background: #fef7f0; border-radius: 16px; border: 1px solid #fed7d7; }
            .accordion-month { font-size: 22px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: ${COLORS.primary}; margin-bottom: 12px; }
            .event-tags { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px; }
            .event-tag { font-size: 16px; font-weight: 600; padding: 8px 14px; border-radius: 10px; background: #fff; color: #6b7280; }
            .accordion-events { display: flex; flex-direction: column; gap: 16px; }
            .event-block { display: flex; gap: 12px; align-items: flex-start; }
            .event-dot { width: 10px; height: 10px; border-radius: 5px; flex-shrink: 0; margin-top: 8px; }
            .event-body { flex: 1; }
            .event-type { font-size: 19px; font-weight: 700; margin-bottom: 6px; }
            .event-prediction { font-size: 19px; line-height: 1.55; margin-bottom: 8px; }
            .manifestations { margin-top: 12px; margin-bottom: 10px; }
            .manifestations-title { font-size: 18px; font-weight: 700; color: ${COLORS.primary}; margin-bottom: 10px; }
            .manifestation-item { display: flex; gap: 12px; padding: 14px; border-radius: 10px; border-left: 3px solid ${COLORS.primary}; background: #fff; margin-bottom: 10px; }
            .manifestation-num { width: 28px; height: 28px; border-radius: 14px; background: ${COLORS.primary}; color: white; font-size: 15px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
            .manifestation-scenario { font-size: 18px; font-weight: 600; margin-bottom: 6px; }
            .manifestation-reasoning { font-size: 17px; font-style: italic; color: #6b7280; }
            .event-dates { font-size: 17px; font-weight: 600; color: ${COLORS.primary}; margin-top: 8px; }
            .event-trigger { font-size: 16px; font-style: italic; color: #6b7280; margin-top: 6px; }
            .footer { margin-top: 32px; padding-top: 20px; border-top: 2px solid #f0f0f0; text-align: center; color: #6b7280; font-size: 20px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              ${logoDataUri ? `<img src="${logoDataUri}" class="logo" alt="AstroRoshni" />` : '<div class="logo-fallback">🔮</div>'}
              <div class="title">Major Life Events — ${year}</div>
              ${nativeName ? `<div class="subtitle">${escapeHtml(nativeName)}</div>` : ''}
              <div class="subtitle">${new Date().toLocaleString()}</div>
            </div>
            ${trendsHtml}
            <div class="section-label">📅 Monthly Guide</div>
            ${accordionsHtml}
            <div class="footer">Generated by AstroRoshni App — Your Personal Vedic Astrology Guide</div>
          </div>
        </body>
      </html>`;

    const { uri } = await Promise.race([
      Print.printToFileAsync({ html, base64: false }),
      new Promise((_, reject) => setTimeout(() => reject(new Error('PDF generation timeout')), 45000)),
    ]);
    return uri;
  } catch (error) {
    console.error('Event timeline PDF error:', error);
    throw error;
  }
};

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

export const sharePDFOnWhatsApp = async (pdfUri) => {
  try {
    const isAvailable = await Sharing.isAvailableAsync();
    if (!isAvailable) {
      throw new Error('Sharing is not available on this device');
    }

    await Sharing.shareAsync(pdfUri, {
      mimeType: 'application/pdf',
      dialogTitle: 'Share AstroRoshni Prediction',
      UTI: 'com.adobe.pdf',
    });
  } catch (error) {
    console.error('PDF sharing error:', error);
    throw error;
  }
};
