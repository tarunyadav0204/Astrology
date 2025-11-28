import React, { useState, useEffect } from 'react';
import { PDFDownloadLink } from '@react-pdf/renderer';
import { HealthReportPDF } from '../PDF/HealthReportPDF';
import './AIInsightsTab.css';

const AIInsightsTab = ({ chartData, birthDetails }) => {
  const [aiInsights, setAiInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [dots, setDots] = useState('');
  const [openAccordions, setOpenAccordions] = useState({ 0: true }); // First accordion open by default
  
  const steps = [
    '📊 Analyzing planetary positions',
    '🏠 Examining house strengths',
    '🌟 Calculating yogas and combinations',
    '🧘♀️ Determining constitutional balance',
    '⚕️ Generating health recommendations'
  ];
  
  // Function to parse markdown-style bold text
  const parseMarkdown = (text) => {
    if (!text || typeof text !== 'string') return text;
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  };

  // Toggle accordion function
  const toggleAccordion = (index) => {
    setOpenAccordions(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
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
    
    setLoading(true);
    setError(null);
    setCurrentStep(0);
    setDots('');
    
    try {
      const response = await fetch('/api/health/ai-insights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          date: birthDetails.date || '1990-01-01',
          time: birthDetails.time || '12:00',
          place: birthDetails.place || 'New Delhi',
          latitude: birthDetails.latitude || 28.6139,
          longitude: birthDetails.longitude || 77.2090,
          timezone: birthDetails.timezone || 'UTC+5:30',
          name: birthDetails.name || 'User',
          gender: birthDetails.gender || 'male',
          language: 'english',
          response_style: 'detailed'
        })
      });
      
      if (!response.ok) {
        setLoading(false);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Handle streaming response with timeout
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let hasReceivedFinalMessage = false;
      
      // Add timeout to prevent infinite loading
      const timeout = setTimeout(() => {
        if (!hasReceivedFinalMessage) {
          reader.cancel();
          throw new Error('Request timeout - analysis taking too long');
        }
      }, 120000); // 2 minute timeout
      
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            clearTimeout(timeout);
            if (!hasReceivedFinalMessage) {
              throw new Error('Stream ended without final result');
            }
            break;
          }
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.status === 'processing') {
                  console.log('Processing:', data.message);
                } else if (data.status === 'complete') {
                  hasReceivedFinalMessage = true;
                  clearTimeout(timeout);
                  setAiInsights(data.data);
                  setLoading(false);
                  return;
                } else if (data.status === 'error') {
                  hasReceivedFinalMessage = true;
                  clearTimeout(timeout);
                  throw new Error(data.error || 'Analysis failed');
                }
              } catch (parseError) {
                console.warn('Failed to parse streaming data:', parseError);
                // Continue processing other lines
              }
            }
          }
        }
      } catch (streamError) {
        clearTimeout(timeout);
        throw streamError;
      }
    } catch (error) {
      console.error('Error loading AI insights:', error);
      setLoading(false);
      
      // Provide more specific error messages
      let errorMessage = 'Failed to load AI insights';
      if (error.message.includes('404')) {
        errorMessage = 'Health analysis service is currently unavailable. Please try again later.';
      } else if (error.message.includes('402')) {
        errorMessage = 'Insufficient credits for health analysis. Please check your account.';
      } else if (error.message.includes('500')) {
        errorMessage = 'Server error occurred. Please try again in a few moments.';
      } else if (error.message.includes('timeout')) {
        errorMessage = 'Analysis is taking longer than expected. Please try again.';
      } else {
        errorMessage = error.message || 'Failed to load AI insights';
      }
      
      setError(errorMessage);
    } finally {
      // Ensure loading is always set to false
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAIInsights();
  }, [birthDetails]);

  if (loading) {
    return (
      <div className="ai-insights-tab">
        <div className="loading-state">
          <div className="ai-spinner"></div>
          <h3>🔮 Generating Your Personalized Health Insights</h3>
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
          <h3>🌿 No Data Available</h3>
          <p>No health insights data received</p>
          <button onClick={() => window.location.reload()}>Retry Analysis</button>
        </div>
      </div>
    );
  }
  
  if (!aiInsights.insights) {
    return (
      <div className="ai-insights-tab">
        <div className="error-state">
          <h3>🌿 Analysis Structure Issue</h3>
          <p>Response received but insights missing</p>
          <div style={{background: '#f0f0f0', padding: '10px', margin: '10px 0', fontSize: '12px'}}>
            <strong>Debug:</strong> {JSON.stringify(aiInsights, null, 2)}
          </div>
          <button onClick={() => window.location.reload()}>Retry Analysis</button>
        </div>
      </div>
    );
  }

  // Handle both old format (insights object) and new format (direct health_analysis)
  const insights = aiInsights.insights || aiInsights;
  const healthAnalysis = aiInsights.health_analysis;
  
  // Debug: Log the insights structure
  console.log('Final insights object:', insights);
  console.log('aiInsights structure:', aiInsights);
  console.log('healthAnalysis:', healthAnalysis);
  console.log('Should show PDF button:', !!aiInsights);
  console.log('healthAnalysis exists?', !!healthAnalysis);
  console.log('Will use enhanced format?', !!healthAnalysis);
  
  // Check if AI response has content (enhanced format returns health_analysis as structured data)
  const hasContent = healthAnalysis || 
                     insights.health_overview || 
                     insights.constitutional_analysis || 
                     (insights.key_health_areas && insights.key_health_areas.length > 0) ||
                     (insights.lifestyle_recommendations && insights.lifestyle_recommendations.length > 0) ||
                     (insights.preventive_measures && insights.preventive_measures.length > 0) ||
                     insights.positive_indicators ||
                     insights.accident_surgery_possibilities ||
                     insights.health_timeline_2_years;
  
  const isEmpty = !hasContent;
  
  if (isEmpty) {
    return (
      <div className="ai-insights-tab">
        <div className="error-state">
          <h3>🌿 Analysis Failed</h3>
          <p>Could not generate health insights. Please try again.</p>
          <button onClick={() => loadAIInsights(true)}>🔄 Regenerate Analysis</button>
        </div>
      </div>
    );
  }

  // If we have enhanced health analysis, render structured format like wealth
  if (healthAnalysis) {
    const jsonResponse = healthAnalysis.json_response;
    
    return (
      <div className="ai-insights-tab">
        <div className="ai-header">
          <h3>🌿 Personalized Health Insights</h3>
          <p>Comprehensive health analysis based on your birth chart</p>
          {aiInsights.cached && (
            <div className="cache-indicator">
              <span className="cache-badge">💾 Previously Generated</span>
            </div>
          )}
          <div className="action-buttons">
            <button 
              className="regenerate-btn" 
              onClick={() => loadAIInsights(true)}
              title="Generate fresh analysis"
            >
              🔄 Regenerate Analysis
            </button>
            
            <button 
              className="download-btn"
              onClick={() => alert('PDF feature coming soon!')}
              title="Download PDF Report"
            >
              📄 Download PDF
            </button>
          </div>
        </div>

        <div className="enhanced-health-content">
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
                      <div key={index} className="accordion-panel">
                        <div 
                          className={`accordion-header ${openAccordions[index] ? 'open' : ''}`}
                          onClick={() => toggleAccordion(index)}
                        >
                          <div className="question-info">
                            <span className="question-number">{index + 1}</span>
                            <h4 className="question-text">{qa.question}</h4>
                          </div>
                          <span className="accordion-icon">{openAccordions[index] ? '−' : '+'}</span>
                        </div>
                        
                        {openAccordions[index] && (
                          <div className="accordion-content">
                            <div className="answer-section">
                              <h5 className="section-title">📝 Answer</h5>
                              <div className="answer-text" dangerouslySetInnerHTML={{ __html: qa.answer }} />
                            </div>
                            
                            {qa.key_points && qa.key_points.length > 0 && (
                              <div className="key-points-section">
                                <h5 className="section-title">🔑 Key Points</h5>
                                <ul className="key-points-list">
                                  {qa.key_points.map((point, idx) => (
                                    <li key={idx} dangerouslySetInnerHTML={{ __html: point }} />
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {qa.astrological_basis && (
                              <div className="astrological-section">
                                <h5 className="section-title">🪐 Astrological Basis</h5>
                                <div className="astrological-text" dangerouslySetInnerHTML={{ __html: qa.astrological_basis }} />
                              </div>
                            )}
                          </div>
                        )}
                      </div>
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
        </div>

        <div className="ai-footer">
          <p className="ai-disclaimer">
            <strong>Disclaimer:</strong> Health insights are for educational purposes only. 
            Consult healthcare professionals for medical advice.
          </p>
        </div>
      </div>
    );
  }

  // Fallback to old format for backward compatibility
  return (
    <div className="ai-insights-tab">
      <div className="ai-header">
        <h3>🌿 Personalized Health Insights</h3>
        <button onClick={() => alert('TEST BUTTON WORKS!')} style={{background: 'red', color: 'white', padding: '5px 10px', border: 'none', margin: '10px 0'}}>TEST PDF BUTTON</button>
        <p>Comprehensive health analysis based on your birth chart</p>
        <p style={{fontSize: '12px', color: 'red'}}>DEBUG: Using fallback format. healthAnalysis = {JSON.stringify(!!healthAnalysis)}</p>
        {aiInsights.cached && (
          <div className="cache-indicator">
            <span className="cache-badge">💾 Previously Generated</span>
          </div>
        )}
        <div className="action-buttons" style={{display: 'flex', gap: '10px', justifyContent: 'center', marginTop: '15px', flexWrap: 'wrap'}}>
          <button 
            className="regenerate-btn" 
            onClick={() => loadAIInsights(true)}
            title="Generate fresh analysis"
            style={{background: '#2c3e50', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '8px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px'}}
          >
            🔄 Regenerate Analysis
          </button>
          
          <button 
            onClick={() => alert('PDF feature coming soon!')}
            title="Download PDF Report"
            style={{background: '#e74c3c', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '8px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '14px', fontWeight: '500'}}
          >
            📄 Download PDF
          </button>
        </div>
      </div>
      


      <div className="insights-grid">
        {/* Health Overview */}
        <div className="insight-card overview-card">
          <div className="card-header">
            <div className="card-icon">🌟</div>
            <h4>Health Overview</h4>
          </div>
          <div className="card-content">
            <p dangerouslySetInnerHTML={{__html: parseMarkdown(insights.health_overview) || 'No health overview available'}}></p>
          </div>
        </div>

        {/* Constitutional Analysis */}
        <div className="insight-card constitution-card">
          <div className="card-header">
            <div className="card-icon">🧘♀️</div>
            <h4>Constitutional Analysis</h4>
          </div>
          <div className="card-content">
            <p dangerouslySetInnerHTML={{__html: parseMarkdown(insights.constitutional_analysis) || 'No constitutional analysis available'}}></p>
          </div>
        </div>

        {/* Key Health Areas */}
        <div className="insight-card health-areas-card">
          <div className="card-header">
            <div className="card-icon">⚕️</div>
            <h4>Key Health Areas</h4>
          </div>
          <div className="card-content">
            <ul className="insight-list">
              {insights.key_health_areas?.map((area, idx) => (
                <li key={idx} dangerouslySetInnerHTML={{__html: parseMarkdown(area)}}></li>
              ))}
            </ul>
          </div>
        </div>

        {/* Lifestyle Recommendations */}
        <div className="insight-card lifestyle-card">
          <div className="card-header">
            <div className="card-icon">🍃</div>
            <h4>Lifestyle Recommendations</h4>
          </div>
          <div className="card-content">
            <ul className="insight-list">
              {insights.lifestyle_recommendations?.map((rec, idx) => (
                <li key={idx} dangerouslySetInnerHTML={{__html: parseMarkdown(rec)}}></li>
              ))}
            </ul>
          </div>
        </div>

        {/* Preventive Measures */}
        <div className="insight-card preventive-card">
          <div className="card-header">
            <div className="card-icon">🔒</div>
            <h4>Preventive Measures</h4>
          </div>
          <div className="card-content">
            <ul className="insight-list">
              {insights.preventive_measures?.map((measure, idx) => (
                <li key={idx} dangerouslySetInnerHTML={{__html: parseMarkdown(measure)}}></li>
              ))}
            </ul>
          </div>
        </div>

        {/* Positive Indicators */}
        <div className="insight-card positive-card">
          <div className="card-header">
            <div className="card-icon">💎</div>
            <h4>Positive Health Indicators</h4>
          </div>
          <div className="card-content">
            <p dangerouslySetInnerHTML={{__html: parseMarkdown(insights.positive_indicators) || 'No positive indicators available'}}></p>
          </div>
        </div>

        {/* Accident & Surgery Possibilities */}
        {insights.accident_surgery_possibilities && (
          <div className="insight-card accident-card">
            <div className="card-header">
              <div className="card-icon">⚠️</div>
              <h4>Accident & Surgery Possibilities</h4>
            </div>
            <div className="card-content">
              {Array.isArray(insights.accident_surgery_possibilities) ? (
                <ul className="insight-list">
                  {insights.accident_surgery_possibilities.map((item, idx) => (
                    <li key={idx} dangerouslySetInnerHTML={{__html: parseMarkdown(typeof item === 'string' ? item : JSON.stringify(item))}}></li>
                  ))}
                </ul>
              ) : typeof insights.accident_surgery_possibilities === 'string' ? (
                <p dangerouslySetInnerHTML={{__html: parseMarkdown(insights.accident_surgery_possibilities)}}></p>
              ) : (
                <p>{JSON.stringify(insights.accident_surgery_possibilities)}</p>
              )}
            </div>
          </div>
        )}

        {/* Health Timeline */}
        {insights.health_timeline_2_years && (
          <div className="insight-card timeline-card">
            <div className="card-header">
              <div className="card-icon">📅</div>
              <h4>Health Timeline (Next 6 Months)</h4>
            </div>
            <div className="card-content">
              {Array.isArray(insights.health_timeline_2_years) ? (
                <ul className="insight-list">
                  {insights.health_timeline_2_years.map((item, idx) => (
                    <li key={idx} dangerouslySetInnerHTML={{__html: parseMarkdown(typeof item === 'string' ? item : JSON.stringify(item))}}></li>
                  ))}
                </ul>
              ) : typeof insights.health_timeline_2_years === 'string' ? (
                <p dangerouslySetInnerHTML={{__html: parseMarkdown(insights.health_timeline_2_years)}}></p>
              ) : (
                <p>{JSON.stringify(insights.health_timeline_2_years)}</p>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="ai-footer">
        <p className="ai-disclaimer">
          <strong>Disclaimer:</strong> Health insights are for educational purposes only. 
          Consult healthcare professionals for medical advice.
        </p>
      </div>
    </div>
  );
};

export default AIInsightsTab;