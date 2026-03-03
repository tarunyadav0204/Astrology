import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import * as FileSystem from 'expo-file-system';
import { COLORS } from './constants';

export const generatePDF = async (message) => {
  try {
    console.log('📄 [PDF] Starting generation...');
    console.log('📄 [PDF] Has summary_image:', !!message.summary_image);
    
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
              font-size: 32px;
              margin-bottom: 10px;
            }
            
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
              <div class="logo">🔮</div>
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
