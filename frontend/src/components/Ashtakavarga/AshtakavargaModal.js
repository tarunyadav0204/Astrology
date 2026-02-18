import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import './AshtakavargaModal.css';
import { API_BASE_URL } from '../../config';

const AshtakavargaModal = ({ isOpen, onClose, birthData, chartType, transitDate }) => {
  const [ashtakavargaData, setAshtakavargaData] = useState(null);
  const [transitData, setTransitData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('sarva');
  const [viewMode, setViewMode] = useState('birth'); // 'birth', 'transit', 'comparison'
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [eventPredictions, setEventPredictions] = useState(null);
  const [selectedEventType, setSelectedEventType] = useState('marriage');

  const signNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

  useEffect(() => {
    if (isOpen && birthData) {
      fetchAshtakavarga();
      if (viewMode === 'transit' || viewMode === 'comparison') {
        fetchTransitAshtakavarga();
      }
      if (activeTab === 'events' && (viewMode === 'transit' || viewMode === 'comparison')) {
        fetchEventPredictions();
      }
    }
  }, [isOpen, birthData, chartType, viewMode, selectedDate, activeTab, selectedEventType]);

  const fetchAshtakavarga = async () => {
    setLoading(true);
    const apiUrl = API_BASE_URL.includes('/api') 
      ? `${API_BASE_URL}/calculate-ashtakavarga`
      : `${API_BASE_URL}/api/calculate-ashtakavarga`;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: birthData,
          chart_type: chartType,
          transit_date: transitDate
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setAshtakavargaData(data);
    } catch (error) {
      console.error('Error fetching Ashtakavarga:', error);
      setAshtakavargaData(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchTransitAshtakavarga = async () => {
    const apiUrl = API_BASE_URL.includes('/api') 
      ? `${API_BASE_URL}/ashtakavarga/transit-analysis`
      : `${API_BASE_URL}/api/ashtakavarga/transit-analysis`;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: birthData,
          transit_date: selectedDate
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setTransitData(data);
      
      // Fetch event predictions if on events tab
      if (activeTab === 'events') {
        fetchEventPredictions();
      }
    } catch (error) {
      console.error('Error fetching Transit Ashtakavarga:', error);
      setTransitData(null);
    }
  };

  const fetchEventPredictions = async () => {
    const apiUrl = API_BASE_URL.includes('/api') 
      ? `${API_BASE_URL}/ashtakavarga/predict-specific-event`
      : `${API_BASE_URL}/api/ashtakavarga/predict-specific-event`;
    try {
      const token = localStorage.getItem('token');
      const currentYear = new Date().getFullYear();
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: birthData,
          event_type: selectedEventType,
          start_year: currentYear,
          end_year: currentYear + 5
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setEventPredictions(data);
    } catch (error) {
      console.error('Error fetching Event Predictions:', error);
      setEventPredictions(null);
    }
  };

  const getTabsForChartType = () => {
    const baseTabs = [
      { id: 'sarva', label: 'Sarvashtakavarga' },
      { id: 'individual', label: 'Individual Charts' }
    ];

    if (viewMode === 'transit' || viewMode === 'comparison') {
      baseTabs.push({ id: 'recommendations', label: 'Transit Timing' });
      baseTabs.push({ id: 'events', label: 'Event Predictions' });
    }

    if (chartType === 'lagna') {
      return [...baseTabs, { id: 'analysis', label: 'Life Analysis' }];
    } else if (chartType === 'navamsa') {
      return [...baseTabs, { id: 'analysis', label: 'Marriage Analysis' }];
    } else if (chartType === 'transit') {
      return [...baseTabs, { id: 'analysis', label: 'Timing Analysis' }];
    }
    
    return [...baseTabs, { id: 'analysis', label: 'General Analysis' }];
  };

  const renderSarvashtakavarga = () => {
    if (viewMode === 'birth' && !ashtakavargaData) return null;
    if ((viewMode === 'transit' || viewMode === 'comparison') && !transitData) return null;

    if (viewMode === 'comparison' && ashtakavargaData && transitData) {
      return renderComparison();
    }

    const data = viewMode === 'transit' ? transitData.transit_ashtakavarga : ashtakavargaData.ashtakavarga;
    const { sarvashtakavarga, total_bindus } = data;
    const title = viewMode === 'transit' ? `Transit Sarvashtakavarga (${selectedDate})` : 'Birth Sarvashtakavarga';

    return (
      <div className="sarva-chart">
        <h3>{title} ({total_bindus} total bindus)</h3>
        <div className="bindu-grid">
          {signNames.map((sign, index) => (
            <div key={index} className={`bindu-cell ${sarvashtakavarga[index] >= 30 ? 'strong' : sarvashtakavarga[index] <= 25 ? 'weak' : 'average'}`}>
              <div className="sign-name">{sign}</div>
              <div className="bindu-count">{sarvashtakavarga[index]}</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderComparison = () => {
    if (!ashtakavargaData || !transitData) return null;

    const birthData = ashtakavargaData.ashtakavarga.sarvashtakavarga;
    const transitAV = transitData.transit_ashtakavarga.sarvashtakavarga;
    const comparison = transitData.birth_transit_comparison;
    
    // Handle both old and new comparison format
    const comparisonData = comparison.summary ? comparison : 
      Object.keys(comparison).reduce((acc, sign) => {
        if (typeof comparison[sign] === 'object' && comparison[sign].birth_points !== undefined) {
          acc[sign] = comparison[sign];
        }
        return acc;
      }, {});

    return (
      <div className="comparison-chart">
        <h3>Birth vs Transit Comparison ({selectedDate})</h3>
        <div className="comparison-grid">
          {signNames.map((sign, index) => {
            const signData = comparisonData[sign] || comparison[sign];
            if (!signData) return null;
            
            const status = signData.status.includes('significantly') ? 
              signData.status : 
              signData.difference > 0 ? 'enhanced' : 
              signData.difference < 0 ? 'reduced' : 'stable';
            
            return (
              <div key={index} className={`comparison-cell ${status}`}>
                <div className="sign-name">{sign}</div>
                <div className="birth-count">B: {signData.birth_points}</div>
                <div className="transit-count">T: {signData.transit_points}</div>
                <div className={`difference ${status}`}>
                  {signData.difference > 0 ? '+' : ''}{signData.difference}
                  {signData.percentage_change !== 0 && (
                    <span className="percentage">({signData.percentage_change}%)</span>
                  )}
                </div>
                <div className="strength-category">{signData.strength_category}</div>
              </div>
            );
          })}
        </div>
        <div className="legend">
          <span className="significantly_enhanced">■ Significantly Enhanced</span>
          <span className="enhanced">■ Enhanced</span>
          <span className="stable">■ Stable</span>
          <span className="reduced">■ Reduced</span>
          <span className="significantly_reduced">■ Significantly Reduced</span>
        </div>
        {comparison.summary && (
          <div className="comparison-summary">
            <h4>Analysis Summary</h4>
            <div className="summary-stats">
              <span>Stability Index: {comparison.summary.stability_index}%</span>
              <span>Enhanced Signs: {comparison.summary.enhanced_signs}</span>
              <span>Reduced Signs: {comparison.summary.reduced_signs}</span>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderTransitRecommendations = () => {
    if (!transitData) return null;

    const { recommendations, birth_transit_comparison } = transitData;

    return (
      <div className="transit-recommendations">
        <h3>Personalized Transit Analysis</h3>
        <div className="strength-indicator">
          <span className={`strength-badge ${recommendations.transit_strength}`}>
            {recommendations.transit_strength.toUpperCase()} PERIOD
          </span>
          {birth_transit_comparison?.summary && (
            <div className="transit-summary">
              <span className="change-indicator">
                Energy Redistribution: {birth_transit_comparison.summary.distribution_shift} bindus shifted 
                ({birth_transit_comparison.summary.distribution_percentage}% of total energy)
              </span>
            </div>
          )}
        </div>
        
        {recommendations.favorable_activities.length > 0 && (
          <div className="favorable-section">
            <h4 style={{color: '#4caf50'}}>✓ Favorable Activities</h4>
            <ul>
              {recommendations.favorable_activities.map((activity, index) => (
                <li key={index}>{activity}</li>
              ))}
            </ul>
          </div>
        )}
        
        {recommendations.avoid_activities.length > 0 && (
          <div className="avoid-section">
            <h4 style={{color: '#f44336'}}>⚠ Activities to Avoid</h4>
            <ul>
              {recommendations.avoid_activities.map((activity, index) => (
                <li key={index}>{activity}</li>
              ))}
            </ul>
          </div>
        )}
        
        {recommendations.best_timing && recommendations.best_timing.length > 0 && (
          <div className="timing-section">
            <h4 style={{color: '#2196f3'}}>⏰ Best Timing</h4>
            <ul>
              {recommendations.best_timing.map((timing, index) => (
                <li key={index}>{timing}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderEventPredictions = () => {
    const payload = eventPredictions && (eventPredictions.data != null ? eventPredictions.data : eventPredictions);
    const predictions = (payload && Array.isArray(payload.predictions)) ? payload.predictions : [];

    if (!eventPredictions) {
      return (
        <div className="event-predictions">
          <h3>Event Predictions</h3>
          <div className="event-type-selector">
            <label>Select Event Type:</label>
            <select 
              value={selectedEventType} 
              onChange={(e) => {
                setSelectedEventType(e.target.value);
                setTimeout(fetchEventPredictions, 100);
              }}
            >
              <option value="marriage">Marriage</option>
              <option value="career">Career Change</option>
              <option value="children">Children</option>
              <option value="property">Property</option>
              <option value="education">Education</option>
              <option value="health">Health</option>
              <option value="travel">Travel</option>
              <option value="spirituality">Spirituality</option>
            </select>
          </div>
          <div className="loading">Loading predictions...</div>
        </div>
      );
    }

    return (
      <div className="event-predictions">
        <h3>{selectedEventType.charAt(0).toUpperCase() + selectedEventType.slice(1)} Predictions</h3>
        
        <div className="event-type-selector">
          <label>Event Type:</label>
          <select 
            value={selectedEventType} 
            onChange={(e) => {
              setSelectedEventType(e.target.value);
              setTimeout(fetchEventPredictions, 100);
            }}
          >
            <option value="marriage">Marriage</option>
            <option value="career">Career Change</option>
            <option value="children">Children</option>
            <option value="property">Property</option>
            <option value="education">Education</option>
            <option value="health">Health</option>
            <option value="travel">Travel</option>
            <option value="spirituality">Spirituality</option>
          </select>
        </div>

        <div className="predictions-list">
          {predictions.map((prediction, index) => {
            if (!prediction || typeof prediction !== 'object') return null;
            const prob = (prediction.probability || '').toString().toLowerCase().replace(/\s+/g, '-');
            const bestMonths = Array.isArray(prediction.best_months) ? prediction.best_months : [];
            return (
              <div key={index} className={`prediction-card ${prob || 'unknown'}`}>
                <div className="prediction-header">
                  <span className="year">{prediction.year ?? '—'}</span>
                  <span className={`probability ${prob || 'unknown'}`}>
                    {prediction.probability ?? '—'}
                  </span>
                </div>
                <div className="prediction-details">
                  <div className="strength-bar">
                    <div 
                      className="strength-fill" 
                      style={{ width: `${Math.min(100, ((prediction.strength ?? 0) / 360) * 100)}%` }}
                    />
                  </div>
                  <p>{prediction.analysis ?? ''}</p>
                  {bestMonths.length > 0 && (
                    <div className="best-months">
                      <strong>Best Months:</strong> {bestMonths.join(', ')}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderIndividualCharts = () => {
    if (!ashtakavargaData) return null;

    const { individual_charts } = ashtakavargaData.ashtakavarga;

    return (
      <div className="individual-charts">
        <h3>Individual Planet Charts</h3>
        {Object.entries(individual_charts).map(([planet, data]) => (
          <div key={planet} className="planet-chart">
            <h4>{planet} ({data.total} bindus)</h4>
            <div className="bindu-row">
              {signNames.map((sign, index) => {
                const count = data.bindus[index];
                let className = 'mini-bindu ';
                if (count >= 4) className += 'high-bindu';
                else if (count >= 2) className += 'medium-bindu';
                else className += 'low-bindu';
                
                return (
                  <div key={index} className={className}>
                    <span className="mini-sign">{sign.slice(0, 3)}</span>
                    <span className="mini-count">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
        <div style={{ height: '120px' }}></div>
      </div>
    );
  };

  const renderAnalysis = () => {
    if (!ashtakavargaData) return null;

    const { analysis } = ashtakavargaData;

    return (
      <div className="analysis-content">
        <h3>Analysis</h3>
        {analysis.strongest_sign && (
          <div className="strength-analysis">
            <div className="strong-sign">
              <strong>Strongest Sign:</strong> {analysis.strongest_sign.name} ({analysis.strongest_sign.bindus} bindus)
            </div>
            <div className="weak-sign">
              <strong>Weakest Sign:</strong> {analysis.weakest_sign.name} ({analysis.weakest_sign.bindus} bindus)
            </div>
          </div>
        )}
        
        {analysis.recommendations && (
          <div className="recommendations">
            <h4>Recommendations:</h4>
            <ul>
              {analysis.recommendations.map((rec, index) => (
                <li key={index}>{rec}</li>
              ))}
            </ul>
          </div>
        )}

        {analysis.focus && (
          <div className="focus-area">
            <h4>Focus Area:</h4>
            <p>{analysis.focus}</p>
            <p>{analysis.analysis}</p>
          </div>
        )}
        <div style={{ height: '120px' }}></div>
      </div>
    );
  };

  if (!isOpen) return null;

  return createPortal(
    <div className="ashtakavarga-modal-overlay" onClick={onClose}>
      <div className="ashtakavarga-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Ashtakavarga Analysis - {chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart</h2>
          <div className="header-controls">
            <div className="view-mode-toggle">
              <button 
                className={viewMode === 'birth' ? 'active' : ''}
                onClick={() => setViewMode('birth')}
              >
                Birth
              </button>
              <button 
                className={viewMode === 'transit' ? 'active' : ''}
                onClick={() => setViewMode('transit')}
              >
                Transit
              </button>
              <button 
                className={viewMode === 'comparison' ? 'active' : ''}
                onClick={() => setViewMode('comparison')}
              >
                Compare
              </button>
            </div>
            {(viewMode === 'transit' || viewMode === 'comparison') && (
              <input 
                type="date" 
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="date-picker"
              />
            )}
            <button className="close-btn" onClick={onClose}>×</button>
          </div>
        </div>

        <div className="modal-tabs">
          {getTabsForChartType().map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="modal-content">
          {loading ? (
            <div className="loading">Calculating Ashtakavarga...</div>
          ) : !ashtakavargaData ? (
            <div className="loading">
              <p>Failed to load Ashtakavarga data. Please try again.</p>
              <p style={{fontSize: '0.8rem', color: '#666', marginTop: '10px'}}>
                Debug: Check browser console for errors
              </p>
            </div>
          ) : (
            <>
              {activeTab === 'sarva' && renderSarvashtakavarga()}
              {activeTab === 'individual' && renderIndividualCharts()}
              {activeTab === 'recommendations' && renderTransitRecommendations()}
        {activeTab === 'events' && renderEventPredictions()}
              {activeTab === 'analysis' && renderAnalysis()}
            </>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
};

export default AshtakavargaModal;