import React, { useState, useEffect } from 'react';
import { useCredits } from '../../context/CreditContext';
import CreditsModal from '../Credits/CreditsModal';
import { PDFDownloadLink } from '@react-pdf/renderer';
import { WealthReportPDF } from '../PDF/WealthReportPDF';
import './AIInsightsTab.css';

// Format text with proper line breaks and bold formatting
const formatText = (text) => {
  if (!text) return '';
  
  // Decode HTML entities first
  let formatted = text.replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, '&');
  
  // Handle markdown headers (### -> h3)
  formatted = formatted.replace(/^### (.*$)/gm, '<h3 style="color: #ff9800; margin: 1rem 0 0.5rem 0;">$1</h3>');
  
  // Handle bold text (**text**)
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #ff9800; font-weight: bold;">$1</strong>');
  
  // Handle italic text (*text*)
  formatted = formatted.replace(/\*(.*?)\*/g, '<em style="color: #ff9800; font-style: italic;">$1</em>');
  
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
  const { credits, wealthCost, loading: creditsLoading, fetchBalance } = useCredits();
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
    '💰 Analyzing wealth houses',
    '🪐 Examining planetary positions',
    '🏛️ Calculating Dhana yogas',
    '💎 Determining prosperity indicators',
    '📈 Generating investment guidance'
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

  const loadAIInsights = async (forceRegenerate = false) => {
    if (!birthDetails) return;
    
    // Check credits before making request
    console.log('Credit check:', { credits, wealthCost, hasCredits: credits >= wealthCost });
    if (credits < wealthCost) {
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
        birth_date: birthDetails.date,
        birth_time: birthDetails.time,
        birth_place: birthDetails.place,
        latitude: birthDetails.latitude,
        longitude: birthDetails.longitude,
        timezone: birthDetails.timezone,
        force_regenerate: forceRegenerate
      };
      
      console.log('Request body:', requestBody);
      
      const controller = new AbortController();
      const timeoutSignal = setTimeout(() => controller.abort(), 300000);
      
      const token = localStorage.getItem('token');
      const response = await fetch('/api/wealth/ai-insights-enhanced', {
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
  

  
  // Check for cached data on mount
  useEffect(() => {
    const checkCachedData = async () => {
      if (!birthDetails) return;
      
      try {
        const requestBody = {
          birth_date: birthDetails.date,
          birth_time: birthDetails.time,
          birth_place: birthDetails.place,
          latitude: birthDetails.latitude,
          longitude: birthDetails.longitude,
          timezone: birthDetails.timezone
        };
        
        const token = localStorage.getItem('token');
        const response = await fetch('/api/wealth/check-cache', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
          },
          body: JSON.stringify(requestBody)
        });
        
        if (response.ok) {
          const result = await response.json();
          if (result.success && result.cached) {
            setAiInsights(result.data);
            setHasStarted(true);
            console.log('Loaded cached wealth analysis');
          } else {
            console.log('No cached analysis found');
          }
        }
      } catch (error) {
        console.log('Cache check failed:', error.message);
      }
    };
    
    checkCachedData();
  }, [birthDetails]);
  
  // Add cleanup on component unmount
  useEffect(() => {
    return () => {
      // Clear any pending timeouts
      setLoading(false);
    };
  }, []);

  // Show regenerate confirmation screen
  if (showRegenerateConfirm) {
    return (
      <div className="ai-insights-tab">
        <div className="analysis-confirmation">
          <div className="confirmation-header">
            <h3>🔄 Regenerate Wealth Analysis</h3>
            <p>Generate a fresh analysis with updated insights</p>
          </div>
          
          <div className="cost-section">
            <div className="cost-info">
              <span className="cost-label">Analysis Cost:</span>
              <span className="cost-amount">{wealthCost} credits</span>
            </div>
            <div className="balance-info">
              <span className="balance-label">Your Balance:</span>
              <span className={`balance-amount ${credits >= wealthCost ? 'sufficient' : 'insufficient'}`}>
                {credits} credits
              </span>
            </div>
          </div>
          
          {credits >= wealthCost ? (
            <div className="action-section">
              <button className="start-analysis-btn" onClick={() => {
                setShowRegenerateConfirm(false);
                loadAIInsights(true);
              }}>
                🔄 Regenerate Analysis ({wealthCost} credits)
              </button>
              <button className="cancel-btn" onClick={() => setShowRegenerateConfirm(false)}>
                Cancel
              </button>
            </div>
          ) : (
            <div className="insufficient-credits">
              <p className="credit-warning-text">
                You need <strong>{wealthCost} credits</strong> but have <strong>{credits} credits</strong>
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
            <h3>💰 AI Wealth Analysis</h3>
            <p>Get comprehensive insights about your financial prospects and wealth-building potential</p>
          </div>
          
          <div className="analysis-preview">
            <h4>📊 What You'll Get:</h4>
            <ul className="preview-list">
              <li>✨ 9 Essential wealth questions with detailed answers</li>
              <li>🪐 Complete planetary analysis from your birth chart</li>
              <li>🏛️ Dhana yogas and prosperity indicators</li>
              <li>📊 Investment guidance and timing predictions</li>
              <li>💼 Business vs job recommendations</li>
              <li>📈 Stock trading and speculation analysis</li>
            </ul>
          </div>
          
          <div className="cost-section">
            <div className="cost-info">
              <span className="cost-label">Analysis Cost:</span>
              <span className="cost-amount">{wealthCost} credits</span>
            </div>
            <div className="balance-info">
              <span className="balance-label">Your Balance:</span>
              <span className={`balance-amount ${credits >= wealthCost ? 'sufficient' : 'insufficient'}`}>
                {credits} credits
              </span>
            </div>
          </div>
          
          {credits >= wealthCost ? (
            <div className="action-section">
              <button className="start-analysis-btn" onClick={startAnalysis}>
                🚀 Start Analysis ({wealthCost} credits)
              </button>
              <p className="analysis-note">
                ⏱️ Analysis takes 1-2 minutes • 🎯 Personalized to your birth chart
              </p>
            </div>
          ) : (
            <div className="insufficient-credits">
              <p className="credit-warning-text">
                You need <strong>{wealthCost} credits</strong> but have <strong>{credits} credits</strong>
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
    const neededCredits = creditMatch ? creditMatch[1] : wealthCost;
    const currentCredits = creditMatch ? creditMatch[2] : credits;
    
    return (
      <div className="ai-insights-tab">
        <div className="credit-warning">
          <h3>💳 Insufficient Credits</h3>
          <p>You need <strong>{neededCredits} credits</strong> for wealth analysis but have <strong>{currentCredits} credits</strong>.</p>
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
              if (credits >= wealthCost) {
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
          <h3>💎 Generating Your Personalized Wealth Insights</h3>
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
          <h3>💰 Analysis Failed</h3>
          <p>Could not generate wealth insights. Please try again.</p>
          <button onClick={() => loadAIInsights(true)}>🔄 Regenerate Analysis</button>
        </div>
      </div>
    );
  }

  // Handle both old format (insights object) and new format (direct wealth_analysis)
  const insights = aiInsights.insights || aiInsights;
  const wealthAnalysis = aiInsights.wealth_analysis;
  
  // Check if AI response has content (enhanced format returns wealth_analysis as HTML)
  const hasContent = wealthAnalysis || 
                     insights.wealth_overview || 
                     insights.income_analysis || 
                     (insights.investment_guidance && insights.investment_guidance.length > 0) ||
                     (insights.business_prospects && insights.business_prospects.length > 0) ||
                     (insights.financial_challenges && insights.financial_challenges.length > 0) ||
                     insights.prosperity_indicators ||
                     (insights.wealth_timeline && insights.wealth_timeline.length > 0) ||
                     (insights.career_money && insights.career_money.length > 0);
  
  if (!hasContent) {
    return (
      <div className="ai-insights-tab">
        <div className="error-state">
          <h3>💰 Analysis Failed</h3>
          <p>Could not generate wealth insights. Please try again.</p>
          <button onClick={() => loadAIInsights(true)}>🔄 Regenerate Analysis</button>
        </div>
      </div>
    );
  }

  // If we have enhanced wealth analysis, render structured format
  if (wealthAnalysis) {
    const isStructured = typeof wealthAnalysis === 'object' && wealthAnalysis.questions;
    const parsedStructure = wealthAnalysis.parsed_structure;
    const jsonResponse = wealthAnalysis.json_response;
    const rawResponse = wealthAnalysis.raw_response;
    
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
              document={<WealthReportPDF data={aiInsights} userName={birthDetails?.name} />}
              fileName={`Wealth_Analysis_${birthDetails?.name || 'Report'}.pdf`}
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

        <div className="enhanced-wealth-content">
          {/* JSON Response Format */}
          {jsonResponse && (
            <>
              {/* Quick Answer Section */}
              {jsonResponse.quick_answer && (
                <div className="quick-answer-section">
                  <h3>✨ Quick Answer</h3>
                  <div className="quick-answer-card">
                    <div dangerouslySetInnerHTML={{__html: jsonResponse.quick_answer}} />
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
          
          {/* Fallback to old parsed structure format */}
          {!jsonResponse && parsedStructure && (
            <>
              {/* Quick Answer Section */}
              {parsedStructure?.quick_answer && (
                <div className="quick-answer-section">
                  <h3>✨ Quick Answer</h3>
                  <div className="quick-answer-card">
                    <div dangerouslySetInnerHTML={{__html: formatText(parsedStructure.quick_answer)}} />
                  </div>
                </div>
              )}
              
              {/* Detailed Analysis Accordion */}
              {isStructured && (
                <div className="detailed-analysis-section">
                  <h3>📊 Detailed Analysis</h3>
                  <div className="questions-accordion">
                    {wealthAnalysis.questions?.map((qa, index) => (
                      <AccordionPanel key={index} qa={qa} index={index} />
                    ))}
                  </div>
                </div>
              )}
              
              {/* Final Thoughts Section */}
              {parsedStructure?.final_thoughts && (
                <div className="final-thoughts-section">
                  <h3>💭 Final Thoughts</h3>
                  <div className="final-thoughts-card">
                    <div dangerouslySetInnerHTML={{__html: formatText(parsedStructure.final_thoughts)}} />
                  </div>
                </div>
              )}
              
              {/* Follow-up Questions */}
              {parsedStructure?.follow_up_questions?.length > 0 && (
                <div className="follow-up-section">
                  <h3>🤔 Follow-up Questions</h3>
                  <div className="follow-up-chips">
                    {parsedStructure.follow_up_questions.map((question, index) => (
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
          {!jsonResponse && !parsedStructure && rawResponse && (
            <div className="raw-content">
              <div dangerouslySetInnerHTML={{__html: formatText(rawResponse)}} />
            </div>
          )}
          
          {/* Final fallback */}
          {!jsonResponse && !parsedStructure && !rawResponse && (
            <div className="raw-content">
              <div dangerouslySetInnerHTML={{__html: typeof wealthAnalysis === 'string' ? wealthAnalysis : JSON.stringify(wealthAnalysis)}} />
            </div>
          )}
        </div>

        <div className="ai-footer">
          <p className="ai-disclaimer">
            <strong>Disclaimer:</strong> Wealth insights are for educational purposes only. 
            Consult financial advisors for investment decisions.
          </p>
        </div>
      </div>
    );
  }

  // Fallback to old format for backward compatibility
  return (
    <div className="ai-insights-tab">
      <div className="ai-header">
        <h3>💰 Personalized Wealth Insights</h3>
        <p>Comprehensive financial analysis based on your birth chart</p>
        {aiInsights.cached && (
          <div className="cache-indicator">
            <span className="cache-badge">💾 Previously Generated</span>
          </div>
        )}
        <button 
          className="regenerate-btn" 
          onClick={() => {
            console.log('Regenerate button clicked');
            loadAIInsights(true);
          }}
          title="Generate fresh analysis"
        >
          🔄 Regenerate Analysis
        </button>
      </div>

      <div className="insights-grid">
        {/* Wealth Overview */}
        <div className="insight-card overview-card">
          <div className="card-header">
            <div className="card-icon">💎</div>
            <h4>Wealth Overview</h4>
          </div>
          <div className="card-content">
            <p dangerouslySetInnerHTML={{__html: parseMarkdown(insights.wealth_overview)}}></p>
          </div>
        </div>

        {/* Income Analysis */}
        <div className="insight-card income-card">
          <div className="card-header">
            <div className="card-icon">💵</div>
            <h4>Income Analysis</h4>
          </div>
          <div className="card-content">
            <p dangerouslySetInnerHTML={{__html: parseMarkdown(insights.income_analysis)}}></p>
          </div>
        </div>

        {/* Investment Guidance */}
        <div className="insight-card investment-card">
          <div className="card-header">
            <div className="card-icon">📈</div>
            <h4>Investment Guidance</h4>
          </div>
          <div className="card-content">
            <ul className="insight-list">
              {insights.investment_guidance?.map((guidance, idx) => (
                <li key={idx} dangerouslySetInnerHTML={{__html: parseMarkdown(guidance)}}></li>
              ))}
            </ul>
          </div>
        </div>

        {/* Business Prospects */}
        <div className="insight-card business-card">
          <div className="card-header">
            <div className="card-icon">🏢</div>
            <h4>Business Prospects</h4>
          </div>
          <div className="card-content">
            <ul className="insight-list">
              {insights.business_prospects?.map((prospect, idx) => (
                <li key={idx} dangerouslySetInnerHTML={{__html: parseMarkdown(prospect)}}></li>
              ))}
            </ul>
          </div>
        </div>

        {/* Financial Challenges */}
        <div className="insight-card challenges-card">
          <div className="card-header">
            <div className="card-icon">⚠️</div>
            <h4>Financial Challenges</h4>
          </div>
          <div className="card-content">
            <ul className="insight-list">
              {insights.financial_challenges?.map((challenge, idx) => (
                <li key={idx} dangerouslySetInnerHTML={{__html: parseMarkdown(challenge)}}></li>
              ))}
            </ul>
          </div>
        </div>

        {/* Prosperity Indicators */}
        <div className="insight-card prosperity-card">
          <div className="card-header">
            <div className="card-icon">🌟</div>
            <h4>Prosperity Indicators</h4>
          </div>
          <div className="card-content">
            <p dangerouslySetInnerHTML={{__html: parseMarkdown(insights.prosperity_indicators)}}></p>
          </div>
        </div>

        {/* Wealth Timeline */}
        {insights.wealth_timeline && insights.wealth_timeline.length > 0 && (
          <div className="insight-card timeline-card">
            <div className="card-header">
              <div className="card-icon">📅</div>
              <h4>Wealth Timeline (Next 6 Months)</h4>
            </div>
            <div className="card-content">
              <ul className="insight-list">
                {insights.wealth_timeline.map((item, idx) => (
                  <li key={idx} dangerouslySetInnerHTML={{__html: parseMarkdown(item)}}></li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Career & Money */}
        {insights.career_money && insights.career_money.length > 0 && (
          <div className="insight-card career-card">
            <div className="card-header">
              <div className="card-icon">💼</div>
              <h4>Career & Money</h4>
            </div>
            <div className="card-content">
              <ul className="insight-list">
                {insights.career_money.map((item, idx) => (
                  <li key={idx} dangerouslySetInnerHTML={{__html: parseMarkdown(item)}}></li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      <div className="ai-footer">
        <p className="ai-disclaimer">
          <strong>Disclaimer:</strong> Wealth insights are for educational purposes only. 
          Consult financial advisors for investment decisions.
        </p>
      </div>
    </div>
  );
};

export default AIInsightsTab;