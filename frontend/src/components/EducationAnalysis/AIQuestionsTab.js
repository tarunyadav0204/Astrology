import React, { useState, useEffect } from 'react';
import { useCredits } from '../../context/CreditContext';
import CreditsModal from '../Credits/CreditsModal';
import jsPDF from 'jspdf';

const formatText = (text) => {
  if (!text) return '';
  
  // Decode HTML entities first
  let formatted = text.replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, '&');
  
  // Handle markdown headers (### -> h3)
  formatted = formatted.replace(/^### (.*$)/gm, '<h3 style="color: #2196f3; margin: 1rem 0 0.5rem 0;">$1</h3>');
  
  // Handle bold text (**text**)
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #2196f3; font-weight: bold;">$1</strong>');
  
  // Handle italic text (*text*)
  formatted = formatted.replace(/\*(.*?)\*/g, '<em style="color: #2196f3; font-style: italic;">$1</em>');
  
  // Handle bullet points (• text)
  formatted = formatted.replace(/^• (.*$)/gm, '<li style="margin: 0.25rem 0;">$1</li>');
  
  // Wrap consecutive list items in ul tags
  formatted = formatted.replace(/(<li.*?<\/li>\s*)+/gs, '<ul style="margin: 0.5rem 0; padding-left: 1.5rem;">$&</ul>');
  
  // Handle line breaks - convert double line breaks to paragraphs
  formatted = formatted.replace(/\n\n+/g, '</p><p>');
  
  // Wrap in paragraph tags if not already wrapped
  if (!formatted.startsWith('<h3>') && !formatted.startsWith('<ul>')) {
    formatted = '<p>' + formatted + '</p>';
  }
  
  // Clean up empty paragraphs
  formatted = formatted.replace(/<p><\/p>/g, '');
  
  return formatted;
};

const AccordionPanel = ({ qa, index }) => {
  const [isOpen, setIsOpen] = useState(index === 0);
  
  return (
    <div className="accordion-panel">
      <div 
        className={`accordion-header ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="question-info">
          <span className="question-number">{index + 1}</span>
          <h4 className="question-text">{qa.question}</h4>
        </div>
        <span className="accordion-icon">{isOpen ? '−' : '+'}</span>
      </div>
      
      {isOpen && (
        <div className="accordion-content">
          <div className="answer-section">
            <h5 className="section-title">📝 Answer</h5>
            <div 
              className="answer-text"
              dangerouslySetInnerHTML={{ __html: formatText(qa.answer) }}
            />
          </div>
          
          {qa.key_points && qa.key_points.length > 0 && (
            <div className="key-points-section">
              <h5 className="section-title">🔑 Key Points</h5>
              <ul className="key-points-list">
                {qa.key_points.map((point, idx) => (
                  <li key={idx} dangerouslySetInnerHTML={{ __html: formatText(point) }} />
                ))}
              </ul>
            </div>
          )}
          
          {qa.astrological_basis && (
            <div className="astrological-section">
              <h5 className="section-title">🪐 Astrological Basis</h5>
              <div 
                className="astrological-text"
                dangerouslySetInnerHTML={{ __html: formatText(qa.astrological_basis) }}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const AIQuestionsTab = ({ chartData, birthDetails }) => {
  const { credits, educationCost, loading: creditsLoading, fetchBalance } = useCredits();
  const [aiInsights, setAiInsights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [dots, setDots] = useState('');
  const [showCreditWarning, setShowCreditWarning] = useState(false);
  const [showCreditsModal, setShowCreditsModal] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const [showRegenerateConfirm, setShowRegenerateConfirm] = useState(false);
  
  const steps = [
    '🎓 Analyzing education houses',
    '🪐 Examining planetary positions',
    '📚 Calculating learning indicators',
    '🧠 Assessing intellectual capacity',
    '📈 Generating education timing'
  ];
  
  useEffect(() => {
    let stepInterval, dotsInterval;
    
    if (loading) {
      stepInterval = setInterval(() => {
        setCurrentStep(prev => prev < steps.length - 1 ? prev + 1 : prev);
      }, 8000);
      
      dotsInterval = setInterval(() => {
        setDots(prev => prev.length >= 3 ? '' : prev + '.');
      }, 500);
    }
    
    return () => {
      clearInterval(stepInterval);
      clearInterval(dotsInterval);
    };
  }, [loading]);

  useEffect(() => {
    const fetchPreviousAnalysis = async () => {
      if (!birthDetails) return;
      
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/education/get-analysis', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
          },
          body: JSON.stringify({
            name: birthDetails.name || birthDetails.place,
            date: birthDetails.date,
            time: birthDetails.time,
            place: birthDetails.place,
            latitude: birthDetails.latitude,
            longitude: birthDetails.longitude
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.analysis) {
            setAiInsights(data.analysis);
            setHasStarted(true);
          }
        }
      } catch (error) {
        console.error('Error fetching previous analysis:', error);
      }
    };
    
    fetchPreviousAnalysis();
  }, [birthDetails]);

  const loadAIInsights = async (forceRegenerate = false) => {
    if (!birthDetails) return;
    
    if (credits < educationCost) {
      setShowCreditWarning(true);
      return;
    }
    
    setLoading(true);
    setError(null);
    setCurrentStep(0);
    setDots('');
    
    const timeoutId = setTimeout(() => {
      setError('Analysis timed out. Please try again.');
      setLoading(false);
    }, 300000);
    
    try {
      const requestBody = {
        name: birthDetails.name || birthDetails.place,
        date: birthDetails.date,
        time: birthDetails.time,
        place: birthDetails.place,
        latitude: birthDetails.latitude,
        longitude: birthDetails.longitude,
        timezone: birthDetails.timezone,
        gender: birthDetails.gender,
        language: 'english',
        response_style: 'detailed'
      };
      
      const controller = new AbortController();
      const timeoutSignal = setTimeout(() => controller.abort(), 300000);
      
      const token = localStorage.getItem('token');
      const response = await fetch('/api/education/ai-analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal
      });
      
      clearTimeout(timeoutSignal);
      
      if (!response.ok) {
        if (response.status === 402) {
          const errorData = await response.json();
          const errorMessage = errorData.detail || 'Insufficient credits';
          setError(errorMessage);
          setShowCreditWarning(true);
          setLoading(false);
          return;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let hasReceivedFinalMessage = false;
      let streamTimeout = setTimeout(() => {
        if (!hasReceivedFinalMessage) {
          reader.cancel();
          throw new Error('Stream timeout - no response received');
        }
      }, 240000);
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          clearTimeout(streamTimeout);
          if (!hasReceivedFinalMessage) {
            throw new Error('Stream ended without final result');
          }
          break;
        }
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(line => line.trim());
        
        for (const line of lines) {
          if (line.trim() && line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6).trim();
              if (jsonStr) {
                const data = JSON.parse(jsonStr);
                
                if (data.status === 'processing') {
                  console.log('Processing:', data.message);
                } else if (data.status === 'complete') {
                  hasReceivedFinalMessage = true;
                  clearTimeout(streamTimeout);
                  clearTimeout(timeoutId);
                  setAiInsights(data.data);
                  setHasStarted(true);
                  setLoading(false);
                  // Refresh credits after successful analysis
                  fetchBalance();
                  return;
                } else if (data.status === 'error') {
                  hasReceivedFinalMessage = true;
                  clearTimeout(streamTimeout);
                  clearTimeout(timeoutId);
                  throw new Error(data.error);
                }
              }
            } catch (parseError) {
              console.warn('Failed to parse streaming data:', parseError);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error loading AI insights:', error);
      clearTimeout(timeoutId);
      setError(error.message || 'Failed to load analysis');
      setLoading(false);
    }
  };

  const startAnalysis = () => {
    setHasStarted(true);
    loadAIInsights();
  };

  const generatePDF = () => {
    if (!aiInsights) return;
    
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.width;
    const pageHeight = doc.internal.pageSize.height;
    const margin = 20;
    const maxWidth = pageWidth - 2 * margin;
    let yPosition = 30;
    
    const colors = {
      primary: [44, 62, 80],
      accent: [76, 175, 80],
      light: [248, 249, 250],
      text: [74, 85, 104],
      border: [226, 232, 240]
    };
    
    const addBackground = (x, y, width, height, color) => {
      doc.setFillColor(...color);
      doc.rect(x, y, width, height, 'F');
    };
    
    const addText = (text, fontSize = 12, isBold = false, color = colors.text, bgColor = null) => {
      doc.setFontSize(fontSize);
      doc.setFont('helvetica', isBold ? 'bold' : 'normal');
      doc.setTextColor(...color);
      
      const lines = doc.splitTextToSize(text, maxWidth - 10);
      const lineHeight = fontSize * 0.6;
      
      if (bgColor) {
        const totalHeight = lines.length * lineHeight + 10;
        if (yPosition + totalHeight <= pageHeight - 30) {
          addBackground(margin - 5, yPosition - 5, maxWidth + 10, totalHeight, bgColor);
        } else {
          doc.addPage();
          yPosition = 30;
          addBackground(margin - 5, yPosition - 5, maxWidth + 10, totalHeight, bgColor);
        }
      }
      
      for (let i = 0; i < lines.length; i++) {
        if (yPosition + lineHeight > pageHeight - 30) {
          doc.addPage();
          yPosition = 30;
        }
        
        doc.text(lines[i], margin, yPosition + 5);
        yPosition += lineHeight + 2;
      }
      
      yPosition += 5;
    };
    
    const addDivider = () => {
      doc.setDrawColor(...colors.border);
      doc.setLineWidth(0.5);
      doc.line(margin, yPosition, pageWidth - margin, yPosition);
      yPosition += 10;
    };
    
    const cleanText = (html) => {
      if (!html) return '';
      return html
        .replace(/<strong[^>]*>(.*?)<\/strong>/gi, '$1')
        .replace(/<em[^>]*>(.*?)<\/em>/gi, '$1')
        .replace(/<[^>]*>/g, '')
        .replace(/&nbsp;/g, ' ')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&#39;/g, "'")
        .replace(/&quot;/g, '"')
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/[ØÜÝÞß]/g, '')
        .replace(/[=<>]/g, '')
        .replace(/\s+/g, ' ')
        .replace(/\n\s*\n/g, '\n')
        .trim();
    };
    
    // Header
    addBackground(0, 0, pageWidth, 80, colors.primary);
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(28);
    doc.setFont('helvetica', 'bold');
    doc.text('AstroRoshni', margin, 25);
    
    doc.setFontSize(18);
    doc.text('Education Analysis Report', margin, 45);
    
    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.text(`Generated for: ${birthDetails?.name || 'User'}`, margin, 60);
    doc.text(`Date: ${new Date().toLocaleDateString()}`, margin, 70);
    
    yPosition = 90;
    
    // Disclaimer
    addText('IMPORTANT DISCLAIMER: This astrological education analysis is provided for educational and entertainment purposes only. It is not intended as academic or career advice. The information contained herein should not be used as a substitute for professional educational counseling. Always consult with qualified educational professionals for any academic concerns or before making any decisions related to your education or career.', 9, false, [150, 150, 150]);
    
    yPosition += 10;
    
    const educationAnalysis = aiInsights.education_analysis;
    const jsonResponse = educationAnalysis?.json_response;
    
    if (jsonResponse) {
      if (jsonResponse.quick_answer) {
        addText('Quick Education Overview', 18, true, colors.primary, colors.light);
        yPosition += 5;
        addText(cleanText(jsonResponse.quick_answer), 11, false, colors.text);
        addDivider();
      }
      
      if (jsonResponse.detailed_analysis && jsonResponse.detailed_analysis.length > 0) {
        addText('Detailed Analysis', 18, true, colors.primary, colors.light);
        yPosition += 5;
        
        jsonResponse.detailed_analysis.forEach((qa, index) => {
          addText(`${index + 1}. ${cleanText(qa.question)}`, 14, true, colors.primary);
          
          addText('Answer:', 12, true, colors.accent);
          addText(cleanText(qa.answer), 11, false, colors.text);
          
          if (qa.key_points && qa.key_points.length > 0) {
            addText('Key Points:', 12, true, colors.accent);
            qa.key_points.forEach(point => {
              addText(`• ${cleanText(point)}`, 11, false, colors.text);
            });
          }
          
          if (qa.astrological_basis) {
            addText('Astrological Basis:', 12, true, colors.accent);
            addText(cleanText(qa.astrological_basis), 11, false, colors.text);
          }
          
          if (index < jsonResponse.detailed_analysis.length - 1) {
            yPosition += 5;
            doc.setDrawColor(...colors.border);
            doc.setLineWidth(0.3);
            doc.line(margin + 10, yPosition, pageWidth - margin - 10, yPosition);
            yPosition += 10;
          }
        });
        
        addDivider();
      }
      
      if (jsonResponse.final_thoughts) {
        addText('Final Thoughts', 18, true, colors.primary, colors.light);
        yPosition += 5;
        addText(cleanText(jsonResponse.final_thoughts), 11, false, colors.text);
      }
    }
    
    // Footer
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      
      addBackground(0, pageHeight - 40, pageWidth, 40, colors.light);
      
      doc.setFontSize(10);
      doc.setTextColor(...colors.primary);
      doc.setFont('helvetica', 'bold');
      doc.text('AstroRoshni - Vedic Astrology Insights', margin, pageHeight - 30);
      
      doc.setFontSize(10);
      doc.setTextColor(...colors.text);
      doc.setFont('helvetica', 'normal');
      doc.text(`Page ${i} of ${pageCount}`, pageWidth - 40, pageHeight - 30);
      
      doc.setFontSize(7);
      doc.setTextColor(100, 100, 100);
      const disclaimerText = 'LEGAL DISCLAIMER: This report is for educational and entertainment purposes only. Not intended as academic advice. ' +
                            'Consult qualified educational professionals for academic concerns. AstroRoshni assumes no responsibility for decisions made based on this content.';
      const disclaimerLines = doc.splitTextToSize(disclaimerText, pageWidth - 2 * margin);
      doc.text(disclaimerLines, margin, pageHeight - 20);
    }
    
    const fileName = `Education_Analysis_${birthDetails?.name || 'Report'}_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(fileName);
  };

  if (showRegenerateConfirm) {
    return (
      <div className="ai-insights-tab education-theme">
        <div className="analysis-confirmation">
          <div className="confirmation-header">
            <h3>🔄 Regenerate Education Analysis</h3>
            <p>Generate a fresh analysis with updated insights</p>
          </div>
          
          <div className="cost-section">
            <div className="cost-info">
              <span className="cost-label">Analysis Cost:</span>
              <span className="cost-amount">{educationCost} credits</span>
            </div>
            <div className="balance-info">
              <span className="balance-label">Your Balance:</span>
              <span className={`balance-amount ${credits >= educationCost ? 'sufficient' : 'insufficient'}`}>
                {credits} credits
              </span>
            </div>
          </div>
          
          {credits >= educationCost ? (
            <div className="action-section">
              <button className="start-analysis-btn" onClick={() => {
                setShowRegenerateConfirm(false);
                loadAIInsights(true);
              }}>
                🔄 Regenerate Analysis ({educationCost} credits)
              </button>
              <button className="cancel-btn" onClick={() => setShowRegenerateConfirm(false)}>
                Cancel
              </button>
            </div>
          ) : (
            <div className="insufficient-credits">
              <p className="credit-warning-text">
                You need <strong>{educationCost} credits</strong> but have <strong>{credits} credits</strong>
              </p>
              <div className="action-section">
                <button className="add-credits-btn" onClick={() => setShowCreditsModal(true)}>
                  💳 Add Credits
                </button>
                <button className="cancel-btn" onClick={() => setShowRegenerateConfirm(false)}>
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
        
        <CreditsModal 
          isOpen={showCreditsModal} 
          onClose={() => setShowCreditsModal(false)} 
        />
      </div>
    );
  }
  
  if (!hasStarted && !aiInsights) {
    return (
      <div className="ai-insights-tab education-theme">
        <div className="analysis-confirmation">
          <div className="confirmation-header">
            <h3>🎓 AI Education Analysis 360°</h3>
            <p>Get comprehensive insights about your education, learning potential, and academic success from your birth chart</p>
          </div>
          
          <div className="analysis-preview">
            <h4>📊 What You'll Get:</h4>
            <ul className="preview-list">
              <li>✨ 7 Essential education questions with detailed answers</li>
              <li>🪐 Complete planetary analysis for learning indicators</li>
              <li>📚 Subject recommendations and academic strengths</li>
              <li>🧠 Intelligence and memory assessment</li>
              <li>📅 Education timing and favorable periods</li>
              <li>🔮 Study methods and learning environment guidance</li>
            </ul>
          </div>
          
          <div className="cost-section">
            <div className="cost-info">
              <span className="cost-label">Analysis Cost:</span>
              <span className="cost-amount">{educationCost} credits</span>
            </div>
            <div className="balance-info">
              <span className="balance-label">Your Balance:</span>
              <span className={`balance-amount ${credits >= educationCost ? 'sufficient' : 'insufficient'}`}>
                {credits} credits
              </span>
            </div>
          </div>
          
          {credits >= educationCost ? (
            <div className="action-section">
              <button className="start-analysis-btn" onClick={startAnalysis}>
                🚀 Start Analysis ({educationCost} credits)
              </button>
              <p className="analysis-note">
                ⏱️ Analysis takes 1-2 minutes • 🎯 Personalized to your birth chart
              </p>
            </div>
          ) : (
            <div className="insufficient-credits">
              <p className="credit-warning-text">
                You need <strong>{educationCost} credits</strong> but have <strong>{credits} credits</strong>
              </p>
              <button className="add-credits-btn" onClick={() => setShowCreditsModal(true)}>
                💳 Add Credits
              </button>
            </div>
          )}
        </div>
        
        <CreditsModal 
          isOpen={showCreditsModal} 
          onClose={() => setShowCreditsModal(false)} 
        />
      </div>
    );
  }
  
  if (showCreditWarning) {
    const creditMatch = error?.match(/You need (\d+) credits but have (\d+)/i);
    const neededCredits = creditMatch ? creditMatch[1] : educationCost;
    const currentCredits = creditMatch ? creditMatch[2] : credits;
    
    return (
      <div className="ai-insights-tab education-theme">
        <div className="credit-warning">
          <h3>💳 Insufficient Credits</h3>
          <p>You need <strong>{neededCredits} credits</strong> for education analysis but have <strong>{currentCredits} credits</strong>.</p>
          <p>Please purchase more credits or redeem a promo code to continue.</p>
          <div className="credit-actions">
            <button onClick={() => setShowCreditsModal(true)}>Add Credits</button>
            <button onClick={() => setShowCreditWarning(false)} className="secondary-btn">Cancel</button>
          </div>
        </div>
        
        <CreditsModal 
          isOpen={showCreditsModal} 
          onClose={() => {
            setShowCreditsModal(false);
            setTimeout(() => {
              if (credits >= educationCost) {
                setShowCreditWarning(false);
                loadAIInsights();
              }
            }, 500);
          }} 
        />
      </div>
    );
  }

  if (loading || creditsLoading) {
    return (
      <div className="ai-insights-tab education-theme">
        <div className="loading-state">
          <div className="ai-spinner"></div>
          <h3>💎 Generating Your Personalized Education Insights</h3>
          <div className="loading-steps">
            {steps.map((step, index) => (
              <div key={index} className={`step ${index <= currentStep ? 'active' : ''}`}>
                {index === currentStep ? `${step}${dots}` : index < currentStep ? `${step}...` : step}
              </div>
            ))}
          </div>
          <p className="loading-message">
            ✨ This comprehensive analysis takes 1-2 minutes to ensure accuracy.<br/>
            🎯 We're creating insights tailored specifically to your birth chart.
          </p>
        </div>
      </div>
    );
  }

  if (error && !showCreditWarning) {
    return (
      <div className="ai-insights-tab education-theme">
        <div className="error-state">
          <h3>⚠️ Analysis Error</h3>
          <p>{error}</p>
          <button onClick={() => loadAIInsights(true)}>Retry Analysis</button>
        </div>
      </div>
    );
  }

  if (!aiInsights) {
    return (
      <div className="ai-insights-tab education-theme">
        <div className="error-state">
          <h3>🎓 Analysis Failed</h3>
          <p>Could not generate education insights. Please try again.</p>
          <button onClick={() => loadAIInsights(true)}>🔄 Regenerate Analysis</button>
        </div>
      </div>
    );
  }

  const educationAnalysis = aiInsights.education_analysis;
  
  const hasContent = educationAnalysis && (
    educationAnalysis.json_response || 
    educationAnalysis.raw_response ||
    educationAnalysis.summary
  );
  
  if (!hasContent) {
    return (
      <div className="ai-insights-tab education-theme">
        <div className="error-state">
          <h3>🎓 Analysis Failed</h3>
          <p>Could not generate education insights. Please try again.</p>
          <button onClick={() => loadAIInsights(true)}>🔄 Regenerate Analysis</button>
        </div>
      </div>
    );
  }

  const jsonResponse = educationAnalysis.json_response;
  const rawResponse = educationAnalysis.raw_response;
  
  return (
    <div className="ai-insights-tab education-theme">
      <div className="ai-header-actions">
        <button 
          className="regenerate-btn corner-btn" 
          onClick={() => setShowRegenerateConfirm(true)}
          title="Generate fresh analysis"
        >
          Regenerate
        </button>
        
        <button 
          className="download-btn corner-btn"
          onClick={() => generatePDF()}
          title="Download PDF Report"
        >
          📄 Download PDF
        </button>
      </div>
      
      {aiInsights.cached && (
        <div className="cache-indicator">
          <span className="cache-badge">💾 Previously Generated</span>
        </div>
      )}

      <div className="enhanced-education-content">
        {jsonResponse && (
          <>
            {jsonResponse.quick_answer && (
              <div className="quick-answer-section">
                <h3>✨ Quick Answer</h3>
                <div className="quick-answer-card">
                  <div dangerouslySetInnerHTML={{__html: formatText(jsonResponse.quick_answer)}} />
                </div>
              </div>
            )}
            
            {jsonResponse.detailed_analysis && jsonResponse.detailed_analysis.length > 0 && (
              <div className="detailed-analysis-section">
                <h3>📊 Detailed Analysis</h3>
                <div className="questions-accordion">
                  {jsonResponse.detailed_analysis.map((qa, index) => (
                    <AccordionPanel key={index} qa={qa} index={index} />
                  ))}
                </div>
              </div>
            )}
            
            {jsonResponse.final_thoughts && (
              <div className="final-thoughts-section">
                <h3>💭 Final Thoughts</h3>
                <div className="final-thoughts-card">
                  <div dangerouslySetInnerHTML={{__html: formatText(jsonResponse.final_thoughts)}} />
                </div>
              </div>
            )}
            
            {jsonResponse.follow_up_questions && jsonResponse.follow_up_questions.length > 0 && (
              <div className="follow-up-section">
                <h3>🤔 Follow-up Questions</h3>
                <div className="follow-up-chips">
                  {jsonResponse.follow_up_questions.map((question, index) => (
                    <button key={index} className="follow-up-chip">
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
        
        {!jsonResponse && rawResponse && (
          <div className="raw-content">
            <div dangerouslySetInnerHTML={{__html: formatText(rawResponse)}} />
          </div>
        )}
        
        {!jsonResponse && !rawResponse && (
          <div className="raw-content">
            <div dangerouslySetInnerHTML={{__html: typeof educationAnalysis === 'string' ? educationAnalysis : JSON.stringify(educationAnalysis)}} />
          </div>
        )}
      </div>

      <div className="ai-footer">
        <p className="ai-disclaimer">
          <strong>Disclaimer:</strong> Education insights are for educational purposes only and not academic advice. 
          Always consult qualified educational professionals for academic concerns.
        </p>
      </div>
    </div>
  );
};

export default AIQuestionsTab;