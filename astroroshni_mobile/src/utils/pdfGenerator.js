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
              font-size: 12px;
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
            }
            
            .quick-answer-card {
              background: linear-gradient(135deg, rgba(249, 115, 22, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
              border-radius: 16px;
              padding: 20px;
              margin: 20px 0;
              border: 1px solid rgba(255, 215, 0, 0.3);
              box-shadow: 0 4px 12px rgba(255, 215, 0, 0.2);
            }
            
            .quick-answer-header {
              display: flex;
              align-items: center;
              margin-bottom: 12px;
            }
            
            .lightning {
              font-size: 20px;
              margin-right: 8px;
            }
            
            .card-title {
              font-size: 16px;
              font-weight: 700;
              color: #2c3e50;
            }
            
            .card-text {
              font-size: 14px;
              color: #2c3e50;
              line-height: 1.8;
            }
            
            .final-thoughts-card {
              background: linear-gradient(135deg, #E6F3FF 0%, #B0E0E6 100%);
              border-radius: 16px;
              padding: 20px;
              margin: 20px 0;
              border: 1px solid rgba(65, 105, 225, 0.3);
              box-shadow: 0 4px 12px rgba(65, 105, 225, 0.2);
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
              font-size: 17px;
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
              font-size: 15px;
              line-height: 1.6;
            }
            
            p {
              margin: 12px 0;
              font-size: 15px;
              line-height: 1.6;
            }
            
            strong, b {
              font-weight: 700;
              color: #1a1a1a;
            }
            
            em, i {
              font-style: italic;
            }
            
            .footer {
              margin-top: 40px;
              padding-top: 20px;
              border-top: 2px solid #f0f0f0;
              text-align: center;
              color: #6b7280;
              font-size: 12px;
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

    // Generate PDF without image first (image causes hanging)
    const htmlWithoutImage = html.replace(/<img[^>]*class="summary-image"[^>]*>/g, '');
    
    const { uri } = await Promise.race([
      Print.printToFileAsync({ html: htmlWithoutImage }),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('PDF generation timeout')), 30000)
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
  let listCounter = 0;
  
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
        <div class="quick-answer-card">
          <div class="quick-answer-header">
            <span class="lightning">⚡</span>
            <span class="card-title">Quick Answer</span>
          </div>
          <div class="card-text">${cleanContent}</div>
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
        <div class="final-thoughts-card">
          <div class="card-title">◆ Final Thoughts</div>
          <div class="card-text">${cleanContent}</div>
        </div>
      `;
    }
  );
  
  // Handle markdown headers (## and ###)
  formatted = formatted.replace(/^##\s+(.+)$/gm, (match, headerText) => {
    const symbol = getHeaderSymbol(headerText);
    return `
      <div class="section-header">
        <span class="section-icon">${symbol}</span>
        <span class="section-title">${headerText}</span>
      </div>
    `;
  });
  
  formatted = formatted.replace(/^###\s+(.+)$/gm, (match, headerText) => {
    const symbol = getHeaderSymbol(headerText);
    return `
      <div class="section-header">
        <span class="section-icon">${symbol}</span>
        <span class="section-title">${headerText}</span>
      </div>
    `;
  });
  
  // Handle bullet points
  formatted = formatted.replace(/^[•\-]\s+(.+)$/gm, (match, text) => {
    listCounter++;
    return `
      <div class="list-item">
        <div class="number-circle">${listCounter}</div>
        <div class="list-text">${text}</div>
      </div>
    `;
  });
  
  // Handle bold text
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Handle italic text
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Handle paragraphs
  formatted = formatted.replace(/\n\n+/g, '</p><p>');
  formatted = `<p>${formatted}</p>`;
  
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
