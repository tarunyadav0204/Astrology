import React, { useState, useEffect } from 'react';
import './AIInsightsTab.css';

// Format text with proper line breaks and bold formatting
const formatText = (text) => {
  if (!text) return '';
  
  // Handle bold text (**text**)
  let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Handle single asterisks (*text*)
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // Add line breaks after periods followed by capital letters (new sentences)
  formatted = formatted.replace(/\. ([A-Z])/g, '.\n$1');
  
  // Add line breaks before "According to" and similar phrases
  formatted = formatted.replace(/(According to|As per|The|This)/g, '\n$1');
  
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
  const [aiInsights, setAiInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [dots, setDots] = useState('');
  
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
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
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
    
    console.log('loadAIInsights called with forceRegenerate:', forceRegenerate);
    
    setLoading(true);
    setError(null);
    setCurrentStep(0);
    setDots('');
    
    // Set timeout to prevent infinite loading
    const timeoutId = setTimeout(() => {
      setError('Analysis timed out. Please try again.');
      setLoading(false);
    }, 120000); // 2 minutes timeout
    
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
      const timeoutSignal = setTimeout(() => controller.abort(), 120000);
      
      const response = await fetch('/api/wealth/ai-insights-enhanced', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal
      });
      
      clearTimeout(timeoutSignal);
      
      if (!response.ok) {
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
      }, 90000); // 1.5 minutes for stream
      
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
                  setLoading(false);
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

  useEffect(() => {
    loadAIInsights();
    
    // Cleanup function to handle component unmounting
    return () => {
      setLoading(false);
      setError(null);
    };
  }, [birthDetails]);
  
  // Add cleanup on component unmount
  useEffect(() => {
    return () => {
      // Clear any pending timeouts
      setLoading(false);
    };
  }, []);

  if (loading) {
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
            ✨ This comprehensive analysis takes 30-60 seconds to ensure accuracy.<br/>
            🎯 We're creating insights tailored specifically to your birth chart.
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ai-insights-tab">
        <div className="error-state">
          <h3>⚠️ Analysis Error</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry Analysis</button>
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

  // If we have enhanced wealth analysis, render structured Q&A format
  if (wealthAnalysis) {
    // Check if it's structured format (object) or raw text
    const isStructured = typeof wealthAnalysis === 'object' && wealthAnalysis.questions;
    
    return (
      <div className="ai-insights-tab">
        <div className="ai-header">
          <h3>💰 Enhanced Wealth Analysis</h3>
          <p>Comprehensive 9-question analysis using advanced astrological context</p>
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

        <div className="enhanced-wealth-content">
          {isStructured ? (
            <div className="structured-qa">
              {wealthAnalysis.summary && (
                <div className="wealth-summary">
                  <h4>📊 Quick Summary</h4>
                  <p>{wealthAnalysis.summary}</p>
                </div>
              )}
              
              <div className="questions-accordion">
                {wealthAnalysis.questions?.map((qa, index) => (
                  <AccordionPanel key={index} qa={qa} index={index} />
                ))}
              </div>
            </div>
          ) : (
            <div className="raw-content">
              <div dangerouslySetInnerHTML={{__html: typeof wealthAnalysis === 'string' ? wealthAnalysis : JSON.stringify(wealthAnalysis)}}></div>
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