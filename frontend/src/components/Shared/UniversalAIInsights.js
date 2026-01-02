import React, { useState, useEffect } from 'react';
import { useCredits } from '../../context/CreditContext';
import CreditsModal from '../Credits/CreditsModal';
import { PDFDownloadLink } from '@react-pdf/renderer';
import './UniversalAIInsights.css';

// Analysis type configurations
const ANALYSIS_CONFIG = {
  wealth: {
    title: '💰 AI Wealth Analysis',
    icon: '💰',
    endpoint: '/api/wealth/ai-insights-enhanced',
    cacheEndpoint: '/api/wealth/check-cache',
    requestFormat: 'birth_details', // Use birth_date, birth_time, birth_place format
    description: 'Get comprehensive insights about your financial prospects and wealth-building potential',
    steps: [
      '💰 Analyzing wealth houses',
      '🪐 Examining planetary positions',
      '🏛️ Calculating Dhana yogas',
      '💎 Determining prosperity indicators',
      '📈 Generating investment guidance'
    ],
    preview: [
      '✨ 9 Essential wealth questions with detailed answers',
      '🪐 Complete planetary analysis from your birth chart',
      '🏛️ Dhana yogas and prosperity indicators',
      '📊 Investment guidance and timing predictions',
      '💼 Business vs job recommendations',
      '📈 Stock trading and speculation analysis'
    ],
    disclaimer: 'Wealth insights are for educational purposes only. Consult financial advisors for investment decisions.'
  },
  career: {
    title: '💼 AI Career Analysis',
    icon: '💼',
    endpoint: '/api/career/ai-insights',
    cacheEndpoint: '/api/career/check-cache',
    description: 'Discover your ideal career path and professional growth opportunities',
    steps: [
      '💼 Analyzing career houses',
      '🌟 Examining professional indicators',
      '🎯 Calculating success yogas',
      '📈 Determining growth potential',
      '🚀 Generating career guidance'
    ],
    preview: [
      '✨ Career path recommendations',
      '🎯 Professional strengths analysis',
      '📈 Growth timing predictions',
      '💼 Leadership potential assessment',
      '🌟 Success indicators',
      '🚀 Career change guidance'
    ],
    disclaimer: 'Career insights are for guidance purposes only. Consider professional counseling for major decisions.'
  },
  health: {
    title: '🏥 AI Health Analysis',
    icon: '🏥',
    endpoint: '/api/health/analyze',
    cacheEndpoint: '/api/health/get-analysis',
    description: 'Understand your health patterns and wellness recommendations',
    steps: [
      '🏥 Analyzing health houses',
      '🌿 Examining body constitution',
      '⚕️ Calculating health indicators',
      '💊 Determining wellness factors',
      '🧘 Generating health guidance'
    ],
    preview: [
      '✨ Health vulnerability analysis',
      '🌿 Constitutional assessment',
      '⚕️ Disease susceptibility patterns',
      '💊 Preventive care recommendations',
      '🧘 Wellness and lifestyle guidance',
      '📅 Health timing predictions'
    ],
    disclaimer: 'Health insights are for educational purposes only. Always consult qualified medical professionals.'
  },
  marriage: {
    title: '💕 AI Marriage Analysis',
    icon: '💕',
    endpoint: '/api/marriage/analyze',
    cacheEndpoint: '/api/marriage/check-cache',
    description: 'Explore your relationship patterns and marriage compatibility',
    steps: [
      '💕 Analyzing relationship houses',
      '💖 Examining love indicators',
      '👫 Calculating compatibility factors',
      '💍 Determining marriage timing',
      '🌹 Generating relationship guidance'
    ],
    preview: [
      '✨ Marriage timing predictions',
      '💖 Relationship compatibility analysis',
      '👫 Partner characteristics',
      '💍 Wedding timing recommendations',
      '🌹 Love life insights',
      '🏠 Marital harmony factors'
    ],
    disclaimer: 'Marriage insights are for guidance purposes only. Relationships require mutual understanding and effort.'
  },
  education: {
    title: '🎓 AI Education Analysis',
    icon: '🎓',
    endpoint: '/api/education/ai-analyze',
    cacheEndpoint: '/api/education/get-analysis',
    description: 'Discover your learning potential and academic success factors',
    steps: [
      '🎓 Analyzing education houses',
      '📚 Examining learning indicators',
      '🧠 Calculating intellectual capacity',
      '🏆 Determining academic success',
      '📖 Generating study guidance'
    ],
    preview: [
      '✨ Academic strengths analysis',
      '📚 Learning style recommendations',
      '🧠 Intellectual capacity assessment',
      '🏆 Success in different fields',
      '📖 Study timing guidance',
      '🎯 Skill development areas'
    ],
    disclaimer: 'Education insights are for guidance purposes only. Academic success depends on effort and dedication.'
  }
};

// Format text with proper line breaks, bold formatting, and clickable terms
const formatText = (text, terms = null, glossary = null, onTermClick = null) => {
  if (!text) return '';
  
  // Decode HTML entities first
  let formatted = text.replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, '&');
  
  // Handle <term> tags first if we have terms and glossary
  if (terms && glossary && onTermClick) {
    formatted = formatted.replace(/<term id="([^"]+)">([^<]+)<\/term>/g, (match, termId, termText) => {
      if (glossary[termId]) {
        return `<span class="clickable-term" data-term-id="${termId}" data-term-text="${termText}">${termText}</span>`;
      }
      return termText;
    });
  }
  
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
const AccordionPanel = ({ qa, index, terms, glossary, onTermClick }) => {
  const [isOpen, setIsOpen] = useState(index === 0); // First panel open by default
  
  const handleContentClick = (e) => {
    if (e.target.classList.contains('clickable-term')) {
      const termId = e.target.getAttribute('data-term-id');
      const termText = e.target.getAttribute('data-term-text');
      if (glossary && glossary[termId] && onTermClick) {
        onTermClick(termText, glossary[termId]);
      }
    }
  };
  
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
        <div className="accordion-content" onClick={handleContentClick}>
          <div className="answer-section">
            <h5 className="universal-section-title">📝 Answer</h5>
            <div 
              className="answer-text"
              dangerouslySetInnerHTML={{ __html: formatText(qa.answer, terms, glossary, onTermClick) }}
            />
          </div>
          
          {qa.key_points && qa.key_points.length > 0 && (
            <div className="key-points-section">
              <h5 className="universal-section-title">🔑 Key Points</h5>
              <ul className="key-points-list">
                {qa.key_points.map((point, idx) => (
                  <li key={idx} dangerouslySetInnerHTML={{ __html: formatText(point, terms, glossary, onTermClick) }} />
                ))}
              </ul>
            </div>
          )}
          
          {qa.astrological_basis && (
            <div className="astrological-section">
              <h5 className="universal-section-title">🪐 Astrological Basis</h5>
              <div 
                className="astrological-text"
                dangerouslySetInnerHTML={{ __html: formatText(qa.astrological_basis, terms, glossary, onTermClick) }}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const UniversalAIInsights = ({ analysisType, chartData, birthDetails, PDFComponent }) => {
  const config = ANALYSIS_CONFIG[analysisType];
  const { credits, loading: creditsLoading, fetchBalance, wealthCost, careerCost, healthCost, marriageCost, educationCost } = useCredits();
  const [aiInsights, setAiInsights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [dots, setDots] = useState('');
  const [showCreditWarning, setShowCreditWarning] = useState(false);
  const [showCreditsModal, setShowCreditsModal] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const [showRegenerateConfirm, setShowRegenerateConfirm] = useState(false);
  const [tooltipModal, setTooltipModal] = useState({ show: false, term: '', definition: '' });
  
  // Get the appropriate cost based on analysis type
  const analysisCost = {
    wealth: wealthCost || 15,
    career: careerCost || 15,
    health: healthCost || 15,
    marriage: marriageCost || 15,
    education: educationCost || 15
  }[analysisType] || 15;
  
  // Handle term clicks to show tooltip
  const handleTermClick = (term, definition) => {
    setTooltipModal({ show: true, term, definition });
  };
  
  // Handle clicks on formatted content to detect term clicks
  const handleContentClick = (e) => {
    if (e.target.classList.contains('clickable-term')) {
      const termId = e.target.getAttribute('data-term-id');
      const termText = e.target.getAttribute('data-term-text');
      const insights = aiInsights?.insights || aiInsights;
      const analysis = aiInsights?.[`${analysisType}_analysis`] || aiInsights?.analysis;
      const jsonResponse = analysis?.json_response || analysis;
      const glossary = jsonResponse?.glossary || {};
      
      console.log('Term clicked:', { termId, termText, glossary });
      
      if (glossary[termId]) {
        handleTermClick(termText, glossary[termId]);
      }
    }
  };

  useEffect(() => {
    let stepInterval, dotsInterval;
    
    if (loading) {
      stepInterval = setInterval(() => {
        setCurrentStep(prev => prev < config.steps.length - 1 ? prev + 1 : prev);
      }, 8000);
      
      dotsInterval = setInterval(() => {
        setDots(prev => prev.length >= 3 ? '' : prev + '.');
      }, 500);
    }
    
    return () => {
      clearInterval(stepInterval);
      clearInterval(dotsInterval);
    };
  }, [loading, config.steps.length]);

  const loadAIInsights = async (forceRegenerate = false) => {
    if (!birthDetails) return;
    
    if (credits < analysisCost) {
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
      const requestBody = config.requestFormat === 'birth_details' ? {
        birth_date: birthDetails?.date || '',
        birth_time: birthDetails?.time || '',
        birth_place: birthDetails?.place || '',
        latitude: birthDetails?.latitude || 0,
        longitude: birthDetails?.longitude || 0,
        timezone: birthDetails?.timezone || 'UTC+0',
        language: 'english',
        force_regenerate: forceRegenerate
      } : {
        name: birthDetails?.name || 'User',
        date: birthDetails?.date || '',
        time: birthDetails?.time || '',
        place: birthDetails?.place || '',
        latitude: birthDetails?.latitude || 0,
        longitude: birthDetails?.longitude || 0,
        timezone: birthDetails?.timezone || 'UTC+0',
        gender: birthDetails?.gender || '',
        language: 'english',
        response_style: 'detailed',
        force_regenerate: forceRegenerate
      };
      
      console.log('🔍 Frontend sending request:', { forceRegenerate, requestBody });
      
      const controller = new AbortController();
      const timeoutSignal = setTimeout(() => controller.abort(), 300000);
      
      const token = localStorage.getItem('token');
      const response = await fetch(config.endpoint, {
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
      
      // Handle streaming response
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
      if (!birthDetails || !config.cacheEndpoint) return;
      
      try {
        const requestBody = config.requestFormat === 'birth_details' ? {
          birth_date: birthDetails?.date || '',
          birth_time: birthDetails?.time || '',
          birth_place: birthDetails?.place || '',
          latitude: birthDetails?.latitude || 0,
          longitude: birthDetails?.longitude || 0,
          timezone: birthDetails?.timezone || 'UTC+0',
          language: 'english'
        } : {
          name: birthDetails?.name || 'User',
          date: birthDetails?.date || '',
          time: birthDetails?.time || '',
          place: birthDetails?.place || '',
          latitude: birthDetails?.latitude || 0,
          longitude: birthDetails?.longitude || 0,
          timezone: birthDetails?.timezone || 'UTC+0',
          gender: birthDetails?.gender || '',
          language: 'english',
          response_style: 'detailed'
        };
        
        const token = localStorage.getItem('token');
        const response = await fetch(config.cacheEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
          },
          body: JSON.stringify(requestBody)
        });
        
        if (response.ok) {
          const result = await response.json();
          if (result.analysis) {
            result.analysis.cached = true;
            setAiInsights(result.analysis);
            setHasStarted(true);
          }
        }
      } catch (error) {
        console.log('Cache check failed:', error.message);
      }
    };
    
    checkCachedData();
  }, [birthDetails, config.cacheEndpoint]);

  // Show regenerate confirmation screen
  if (showRegenerateConfirm) {
    return (
      <div className="universal-ai-insights">
        <div className="analysis-confirmation">
          <div className="confirmation-header">
            <h3>🔄 Regenerate {config.title}</h3>
            <p>Generate a fresh analysis with updated insights</p>
          </div>
          
          <div className="cost-section">
            <div className="cost-info">
              <span className="cost-label">Analysis Cost:</span>
              <span className="cost-amount">{analysisCost} credits</span>
            </div>
            <div className="balance-info">
              <span className="balance-label">Your Balance:</span>
              <span className={`balance-amount ${credits >= analysisCost ? 'sufficient' : 'insufficient'}`}>
                {credits} credits
              </span>
            </div>
          </div>
          
          {credits >= analysisCost ? (
            <div className="action-section">
              <button className="start-analysis-btn" onClick={() => {
                setShowRegenerateConfirm(false);
                loadAIInsights(true);
              }}>
                🔄 Regenerate Analysis ({analysisCost} credits)
              </button>
              <button className="cancel-btn" onClick={() => setShowRegenerateConfirm(false)}>
                Cancel
              </button>
            </div>
          ) : (
            <div className="insufficient-credits">
              <p className="credit-warning-text">
                You need <strong>{analysisCost} credits</strong> but have <strong>{credits} credits</strong>
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
      <div className="universal-ai-insights">
        <div className="analysis-confirmation">
          <div className="confirmation-header">
            <h3>{config.title}</h3>
            <p>{config.description}</p>
          </div>
          
          <div className="analysis-preview">
            <h4>📊 What You'll Get:</h4>
            <ul className="preview-list">
              {config.preview.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
          
          <div className="cost-section">
            <div className="cost-info">
              <span className="cost-label">Analysis Cost:</span>
              <span className="cost-amount">{analysisCost} credits</span>
            </div>
            <div className="balance-info">
              <span className="balance-label">Your Balance:</span>
              <span className={`balance-amount ${credits >= analysisCost ? 'sufficient' : 'insufficient'}`}>
                {credits} credits
              </span>
            </div>
          </div>
          
          {credits >= analysisCost ? (
            <div className="action-section">
              <button className="start-analysis-btn" onClick={startAnalysis}>
                🚀 Start Analysis ({analysisCost} credits)
              </button>
              <p className="analysis-note">
                ⏱️ Analysis takes 1-2 minutes • 🎯 Personalized to your birth chart
              </p>
            </div>
          ) : (
            <div className="insufficient-credits">
              <p className="credit-warning-text">
                You need <strong>{analysisCost} credits</strong> but have <strong>{credits} credits</strong>
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
    const creditMatch = error?.match(/You need (\d+) credits but have (\d+)/i);
    const neededCredits = creditMatch ? creditMatch[1] : analysisCost;
    const currentCredits = creditMatch ? creditMatch[2] : credits;
    
    return (
      <div className="universal-ai-insights">
        <div className="credit-warning">
          <h3>💳 Insufficient Credits</h3>
          <p>You need <strong>{neededCredits} credits</strong> for {analysisType} analysis but have <strong>{currentCredits} credits</strong>.</p>
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
              if (credits >= analysisCost) {
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
      <div className="universal-ai-insights">
        <div className="loading-state">
          <div className="ai-spinner"></div>
          <h3>💎 Generating Your Personalized {config.title.split(' ')[1]} Insights</h3>
          <div className="loading-steps">
            {config.steps.map((step, index) => (
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
      <div className="universal-ai-insights">
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
      <div className="universal-ai-insights">
        <div className="error-state">
          <h3>{config.icon} Analysis Failed</h3>
          <p>Could not generate {analysisType} insights. Please try again.</p>
          <button onClick={() => loadAIInsights(true)}>🔄 Regenerate Analysis</button>
        </div>
      </div>
    );
  }

  // Handle both old format (insights object) and new format (direct analysis)
  const insights = aiInsights.insights || aiInsights;
  const analysis = aiInsights.analysis || aiInsights[`${analysisType}_analysis`];
  
  console.log('DEBUG aiInsights:', aiInsights);
  console.log('DEBUG analysis:', analysis);
  console.log('DEBUG condition check:', analysis || (aiInsights && Object.keys(aiInsights).length > 0));
  
  // Always render if we have analysis data
  if (analysis || (aiInsights && Object.keys(aiInsights).length > 0)) {
    const jsonResponse = analysis.json_response || analysis;
    
    console.log('Rendering analysis:', { analysis, jsonResponse });
    
    return (
      <div className="universal-ai-insights">
        <div className="ai-header-actions">
          <button 
            className="regenerate-btn corner-btn" 
            onClick={() => setShowRegenerateConfirm(true)}
            title="Generate fresh analysis"
          >
            Regenerate
          </button>
          
          {jsonResponse && PDFComponent && (
            <PDFDownloadLink
              document={<PDFComponent data={aiInsights} userName={birthDetails?.name} />}
              fileName={`${analysisType}_Analysis_${birthDetails?.name || 'Report'}.pdf`}
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

        <div className="enhanced-content">
          {/* Quick Answer Section */}
          {jsonResponse.quick_answer && (
            <div className="quick-answer-section">
              <h3>✨ Quick Answer</h3>
              <div className="quick-answer-card" onClick={handleContentClick}>
                <div dangerouslySetInnerHTML={{__html: formatText(jsonResponse.quick_answer, jsonResponse.terms, jsonResponse.glossary, handleTermClick)}} />
              </div>
            </div>
          )}
          
          {/* Detailed Analysis Accordion */}
          {jsonResponse.detailed_analysis && jsonResponse.detailed_analysis.length > 0 && (
            <div className="detailed-analysis-section">
              <h3>📊 Detailed Analysis</h3>
              <div className="questions-accordion">
                {jsonResponse.detailed_analysis.map((qa, index) => {
                  const question = qa.question || qa.title || `Analysis ${index + 1}`;
                  const answer = qa.answer;
                  return (
                    <AccordionPanel 
                      key={index} 
                      qa={{question, answer, key_points: qa.key_points, astrological_basis: qa.astrological_basis}} 
                      index={index}
                      terms={jsonResponse.terms}
                      glossary={jsonResponse.glossary}
                      onTermClick={handleTermClick}
                    />
                  );
                })}
              </div>
            </div>
          )}
          
          {/* Final Thoughts Section */}
          {jsonResponse.final_thoughts && (
            <div className="final-thoughts-section">
              <h3>💭 Final Thoughts</h3>
              <div className="final-thoughts-card" onClick={handleContentClick}>
                <div dangerouslySetInnerHTML={{__html: formatText(jsonResponse.final_thoughts, jsonResponse.terms, jsonResponse.glossary, handleTermClick)}} />
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
        </div>

        <div className="ai-footer">
          <p className="ai-disclaimer">
            <strong>Disclaimer:</strong> {config.disclaimer}
          </p>
        </div>
        
        {/* Tooltip Modal */}
        {tooltipModal.show && (
          <div className="tooltip-modal-overlay" onClick={() => setTooltipModal({ show: false, term: '', definition: '' })}>
            <div className="tooltip-modal-container" onClick={(e) => e.stopPropagation()}>
              <div className="tooltip-modal-content">
                <h4 className="tooltip-modal-title">{tooltipModal.term}</h4>
                <p className="tooltip-modal-text">{tooltipModal.definition}</p>
                <button 
                  className="tooltip-modal-close"
                  onClick={() => setTooltipModal({ show: false, term: '', definition: '' })}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Fallback for unsupported format
  return (
    <div className="universal-ai-insights">
      <div className="error-state">
        <h3>{config.icon} Analysis Format Not Supported</h3>
        <p>This analysis format is not yet supported by the universal component.</p>
        <button onClick={() => loadAIInsights(true)}>🔄 Regenerate Analysis</button>
      </div>
    </div>
  );
};

export default UniversalAIInsights;