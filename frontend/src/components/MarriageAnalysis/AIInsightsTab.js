import React, { useState, useEffect } from 'react';
import { useCredits } from '../../context/CreditContext';
import CreditsModal from '../Credits/CreditsModal';
import { PDFDownloadLink } from '@react-pdf/renderer';
import { MarriageReportPDF } from '../PDF/MarriageReportPDF';
import './AIInsightsTab.css';

// Format text with proper line breaks and bold formatting
const formatText = (text) => {
  if (!text) return '';
  
  // Decode HTML entities first
  let formatted = text.replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, '&');
  
  // Handle markdown headers (### -> h3)
  formatted = formatted.replace(/^### (.*$)/gm, '<h3>$1</h3>');
  
  // Handle bold text (**text**)
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Handle italic text (*text*)
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Handle bullet points (• text)
  formatted = formatted.replace(/^• (.*$)/gm, '<li>$1</li>');
  
  // Wrap consecutive list items in ul tags
  formatted = formatted.replace(/(<li>.*<\/li>\s*)+/gs, '<ul>$&</ul>');
  
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

// Accordion Panel Component
const AccordionPanel = ({ qa, index }) => {
  const [isOpen, setIsOpen] = useState(index === 0); // First panel open by default
  
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

const AIInsightsTab = ({ chartData, birthDetails }) => {
  const { credits, marriageCost, loading: creditsLoading, fetchBalance } = useCredits();
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
    '💍 Analyzing marriage houses',
    '🪐 Examining planetary positions',
    '🏛️ Calculating marriage yogas',
    '💎 Determining spouse characteristics',
    '📈 Generating marriage timing'
  ];
  
  // Function to parse markdown-style bold text
  const parseMarkdown = (text) => {
    if (!text || typeof text !== 'string') return text;
    return formatText(text);
  };

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

  // Fetch previous analysis on mount
  useEffect(() => {
    const fetchPreviousAnalysis = async () => {
      if (!birthDetails) return;
      
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/marriage/get-analysis', {
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
    
    // Check credits before making request
    console.log('Credit check:', { credits, marriageCost, hasCredits: credits >= marriageCost });
    if (credits < marriageCost) {
      console.log('Insufficient credits, showing warning');
      setShowCreditWarning(true);
      return;
    }
    console.log('Credits sufficient, proceeding with analysis');
    
    console.log('loadAIInsights called with forceRegenerate:', forceRegenerate);
    
    setLoading(true);
    setError(null);
    setCurrentStep(0);
    setDots('');
    
    // Set timeout to prevent infinite loading
    const timeoutId = setTimeout(() => {
      setError('Analysis timed out. Please try again.');
      setLoading(false);
    }, 300000); // 5 minutes timeout
    
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
      
      console.log('Request body:', requestBody);
      
      const controller = new AbortController();
      const timeoutSignal = setTimeout(() => controller.abort(), 300000);
      
      const token = localStorage.getItem('token');
      const response = await fetch('/api/marriage/analyze', {
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
        // Handle 402 Payment Required specifically
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
      
      // Handle streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let hasReceivedFinalMessage = false;
      let streamTimeout = setTimeout(() => {
        if (!hasReceivedFinalMessage) {
          reader.cancel();
          throw new Error('Stream timeout - no response received');
        }
      }, 240000); // 4 minutes for stream
      
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
                  setHasStarted(true); // Mark as started when we have insights
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

  // Show regenerate confirmation screen
  if (showRegenerateConfirm) {
    return (
      <div className="ai-insights-tab">
        <div className="analysis-confirmation">
          <div className="confirmation-header">
            <h3>🔄 Regenerate Marriage Analysis</h3>
            <p>Generate a fresh analysis with updated insights</p>
          </div>
          
          <div className="cost-section">
            <div className="cost-info">
              <span className="cost-label">Analysis Cost:</span>
              <span className="cost-amount">{marriageCost} credits</span>
            </div>
            <div className="balance-info">
              <span className="balance-label">Your Balance:</span>
              <span className={`balance-amount ${credits >= marriageCost ? 'sufficient' : 'insufficient'}`}>
                {credits} credits
              </span>
            </div>
          </div>
          
          {credits >= marriageCost ? (
            <div className="action-section">
              <button className="start-analysis-btn" onClick={() => {
                setShowRegenerateConfirm(false);
                loadAIInsights(true);
              }}>
                🔄 Regenerate Analysis ({marriageCost} credits)
              </button>
              <button className="cancel-btn" onClick={() => setShowRegenerateConfirm(false)}>
                Cancel
              </button>
            </div>
          ) : (
            <div className="insufficient-credits">
              <p className="credit-warning-text">
                You need <strong>{marriageCost} credits</strong> but have <strong>{credits} credits</strong>
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
  
  // Show initial confirmation screen if analysis hasn't started
  if (!hasStarted && !aiInsights) {
    return (
      <div className="ai-insights-tab">
        <div className="analysis-confirmation">
          <div className="confirmation-header">
            <h3>💍 AI Marriage Analysis</h3>
            <p>Get comprehensive insights about your marriage prospects and spouse characteristics</p>
          </div>
          
          <div className="analysis-preview">
            <h4>📊 What You'll Get:</h4>
            <ul className="preview-list">
              <li>✨ 9 Essential marriage questions with detailed answers</li>
              <li>🪐 Complete planetary analysis from your birth chart</li>
              <li>🏛️ Marriage yogas and dosha analysis</li>
              <li>💎 Spouse characteristics and compatibility</li>
              <li>📅 Marriage timing and favorable periods</li>
              <li>🔮 Remedies for marriage delays or problems</li>
            </ul>
          </div>
          
          <div className="cost-section">
            <div className="cost-info">
              <span className="cost-label">Analysis Cost:</span>
              <span className="cost-amount">{marriageCost} credits</span>
            </div>
            <div className="balance-info">
              <span className="balance-label">Your Balance:</span>
              <span className={`balance-amount ${credits >= marriageCost ? 'sufficient' : 'insufficient'}`}>
                {credits} credits
              </span>
            </div>
          </div>
          
          {credits >= marriageCost ? (
            <div className="action-section">
              <button className="start-analysis-btn" onClick={startAnalysis}>
                🚀 Start Analysis ({marriageCost} credits)
              </button>
              <p className="analysis-note">
                ⏱️ Analysis takes 1-2 minutes • 🎯 Personalized to your birth chart
              </p>
            </div>
          ) : (
            <div className="insufficient-credits">
              <p className="credit-warning-text">
                You need <strong>{marriageCost} credits</strong> but have <strong>{credits} credits</strong>
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
  
  // Show credit warning if insufficient credits during analysis
  if (showCreditWarning) {
    // Parse error message to extract credit amounts
    const creditMatch = error?.match(/You need (\d+) credits but have (\d+)/i);
    const neededCredits = creditMatch ? creditMatch[1] : marriageCost;
    const currentCredits = creditMatch ? creditMatch[2] : credits;
    
    return (
      <div className="ai-insights-tab">
        <div className="credit-warning">
          <h3>💳 Insufficient Credits</h3>
          <p>You need <strong>{neededCredits} credits</strong> for marriage analysis but have <strong>{currentCredits} credits</strong>.</p>
          <p>Please purchase more credits or redeem a promo code to continue.</p>
          <div className="credit-actions">
            <button onClick={() => setShowCreditsModal(true)}>Add Credits</button>
            <button onClick={() => setShowCreditWarning(false)} className="secondary-btn">Cancel</button>
          </div>
        </div>
        
        {/* Credits Modal */}
        <CreditsModal 
          isOpen={showCreditsModal} 
          onClose={() => {
            setShowCreditsModal(false);
            // Refresh credits after modal closes
            setTimeout(() => {
              if (credits >= marriageCost) {
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
      <div className="ai-insights-tab">
        <div className="loading-state">
          <div className="ai-spinner"></div>
          <h3>💎 Generating Your Personalized Marriage Insights</h3>
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
      <div className="ai-insights-tab">
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
      <div className="ai-insights-tab">
        <div className="error-state">
          <h3>💍 Analysis Failed</h3>
          <p>Could not generate marriage insights. Please try again.</p>
          <button onClick={() => loadAIInsights(true)}>🔄 Regenerate Analysis</button>
        </div>
      </div>
    );
  }

  // Handle marriage analysis response
  const marriageAnalysis = aiInsights.marriage_analysis;
  
  // Check if AI response has content
  const hasContent = marriageAnalysis && (
    marriageAnalysis.json_response || 
    marriageAnalysis.raw_response ||
    marriageAnalysis.summary
  );
  
  if (!hasContent) {
    return (
      <div className="ai-insights-tab">
        <div className="error-state">
          <h3>💍 Analysis Failed</h3>
          <p>Could not generate marriage insights. Please try again.</p>
          <button onClick={() => loadAIInsights(true)}>🔄 Regenerate Analysis</button>
        </div>
      </div>
    );
  }

  // Render structured marriage analysis
  const jsonResponse = marriageAnalysis.json_response;
  const rawResponse = marriageAnalysis.raw_response;
  
  return (
    <div className="ai-insights-tab">
      <div className="ai-header-actions">
        <button 
          className="regenerate-btn corner-btn" 
          onClick={() => {
            console.log('Regenerate button clicked');
            setShowRegenerateConfirm(true);
          }}
          title="Generate fresh analysis"
        >
          Regenerate
        </button>
        
        {jsonResponse && (
          <PDFDownloadLink
            document={<MarriageReportPDF data={aiInsights} userName={birthDetails?.name} />}
            fileName={`Marriage_Analysis_${birthDetails?.name || 'Report'}.pdf`}
            className="pdf-download-link"
          >
            {({ loading }) => (
              <button 
                className="pdf-download-btn corner-btn"
                disabled={loading}
                title="Download PDF Report"
              >
                {loading ? '📄 Preparing...' : '📄 Download PDF'}
              </button>
            )}
          </PDFDownloadLink>
        )}
      </div>
      
      {aiInsights.cached && (
        <div className="cache-indicator">
          <span className="cache-badge">💾 Previously Generated</span>
        </div>
      )}

      <div className="enhanced-marriage-content">
        {/* JSON Response Format */}
        {jsonResponse && (
          <>
            {/* Quick Answer Section */}
            {jsonResponse.quick_answer && (
              <div className="quick-answer-section">
                <h3>✨ Quick Answer</h3>
                <div className="quick-answer-card">
                  <div dangerouslySetInnerHTML={{__html: parseMarkdown(jsonResponse.quick_answer)}} />
                </div>
              </div>
            )}
            
            {/* Detailed Analysis Accordion */}
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
            
            {/* Final Thoughts Section */}
            {jsonResponse.final_thoughts && (
              <div className="final-thoughts-section">
                <h3>💭 Final Thoughts</h3>
                <div className="final-thoughts-card">
                  <div dangerouslySetInnerHTML={{__html: jsonResponse.final_thoughts}} />
                </div>
              </div>
            )}
            
            {/* Follow-up Questions */}
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
        
        {/* Fallback for raw response */}
        {!jsonResponse && rawResponse && (
          <div className="raw-content">
            <div dangerouslySetInnerHTML={{__html: formatText(rawResponse)}} />
          </div>
        )}
        
        {/* Final fallback */}
        {!jsonResponse && !rawResponse && (
          <div className="raw-content">
            <div dangerouslySetInnerHTML={{__html: typeof marriageAnalysis === 'string' ? marriageAnalysis : JSON.stringify(marriageAnalysis)}} />
          </div>
        )}
      </div>

      <div className="ai-footer">
        <p className="ai-disclaimer">
          <strong>Disclaimer:</strong> Marriage insights are for educational purposes only. 
          Consult qualified astrologers for important life decisions.
        </p>
      </div>
    </div>
  );
};

export default AIInsightsTab;