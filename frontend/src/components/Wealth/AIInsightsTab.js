import React, { useState, useEffect } from 'react';
import './AIInsightsTab.css';

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
    
    setLoading(true);
    setError(null);
    setCurrentStep(0);
    setDots('');
    
    try {
      const response = await fetch('/api/wealth/ai-insights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          birth_date: birthDetails.date,
          birth_time: birthDetails.time,
          birth_place: birthDetails.place,
          latitude: birthDetails.latitude,
          longitude: birthDetails.longitude,
          timezone: birthDetails.timezone,
          force_regenerate: forceRegenerate
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Handle streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let hasReceivedFinalMessage = false;
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
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
                setAiInsights(data.data);
                setLoading(false);
                return;
              } else if (data.status === 'error') {
                hasReceivedFinalMessage = true;
                throw new Error(data.error);
              }
            } catch (parseError) {
              console.warn('Failed to parse streaming data:', parseError);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error loading AI insights:', error);
      setError(error.message);
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

  if (!aiInsights || !aiInsights.insights) {
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

  const insights = aiInsights.insights;
  
  // Check if AI response has content
  const hasContent = insights.wealth_overview || 
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
          onClick={() => loadAIInsights(true)}
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