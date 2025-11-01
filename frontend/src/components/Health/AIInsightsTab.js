import React, { useState, useEffect } from 'react';
import './AIInsightsTab.css';

const AIInsightsTab = ({ chartData, birthDetails }) => {
  const [aiInsights, setAiInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [dots, setDots] = useState('');
  
  const steps = [
    '📊 Analyzing planetary positions',
    '🏠 Examining house strengths',
    '🌟 Calculating yogas and combinations',
    '🧘♀️ Determining constitutional balance',
    '⚕️ Generating health recommendations'
  ];
  
  // Function to parse markdown-style bold text
  const parseMarkdown = (text) => {
    if (!text) return text;
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
      const response = await fetch('/api/health/ai-insights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          birth_date: birthDetails.date || '1990-01-01',
          birth_time: birthDetails.time || '12:00',
          birth_place: birthDetails.place || 'New Delhi',
          latitude: birthDetails.latitude || 28.6139,
          longitude: birthDetails.longitude || 77.2090,
          timezone: birthDetails.timezone || 'UTC+5:30',
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
      setError(error.message || 'Failed to load AI insights');
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

  const insights = aiInsights.insights;
  
  // Debug: Log the insights structure
  console.log('Final insights object:', insights);
  
  // Check if AI response is empty
  const isEmpty = !insights.health_overview && 
                  !insights.constitutional_analysis && 
                  (!insights.key_health_areas || insights.key_health_areas.length === 0);
  
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
        <button 
          className="regenerate-btn" 
          onClick={() => loadAIInsights(true)}
          title="Generate fresh analysis"
        >
          🔄 Regenerate Analysis
        </button>
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