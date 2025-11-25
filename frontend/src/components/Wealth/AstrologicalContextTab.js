import React, { useState, useEffect } from 'react';
import './AstrologicalContextTab.css';

const AstrologicalContextTab = ({ birthDetails, user }) => {
  const [contextData, setContextData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadContext = async () => {
    if (!birthDetails) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/wealth/astrological-context', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_date: birthDetails.date,
          birth_time: birthDetails.time,
          birth_place: birthDetails.place,
          latitude: birthDetails.latitude,
          longitude: birthDetails.longitude,
          timezone: birthDetails.timezone,
          user_role: user?.role
        })
      });
      
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Admin access required');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setContextData(data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading context:', error);
      setError(error.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContext();
  }, [birthDetails]);

  const [selectedPlanet, setSelectedPlanet] = useState(null);

  const PlanetaryAnalysisCard = ({ planet, analysis }) => {
    return (
      <div className="analysis-card">
        <h4 className="analysis-planet">{planet}</h4>
        <div className="analysis-details">
          <div><strong>Dignity:</strong> {analysis.dignity_analysis?.dignity}</div>
          <div><strong>Strength:</strong> {analysis.strength_analysis?.shadbala_grade}</div>
          <div><strong>House:</strong> {analysis.house_position_analysis?.house_number}</div>
          <div><strong>Overall Score:</strong> {analysis.overall_assessment?.overall_strength_score}</div>
          <div><strong>Grade:</strong> {analysis.overall_assessment?.classical_grade}</div>
        </div>
        <button 
          className="expand-btn" 
          onClick={() => setSelectedPlanet({ planet, analysis })}
        >
          View Complete Analysis
        </button>
      </div>
    );
  };

  const PlanetaryModal = ({ planetData, onClose }) => {
    if (!planetData) return null;
    
    const { planet, analysis } = planetData;
    
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <h3>{planet} - Complete Analysis</h3>
            <button className="modal-close" onClick={onClose}>×</button>
          </div>
          <div className="modal-body">
            <div className="analysis-section">
              <h4>Basic Information</h4>
              <div className="info-grid">
                <div><strong>Sign:</strong> {analysis.basic_info?.sign_name}</div>
                <div><strong>House:</strong> {analysis.basic_info?.house}</div>
                <div><strong>Degree:</strong> {analysis.basic_info?.degree?.toFixed(2)}°</div>
                <div><strong>Nakshatra:</strong> {analysis.basic_info?.nakshatra}</div>
              </div>
            </div>
            
            <div className="analysis-section">
              <h4>Dignity & Strength</h4>
              <div className="info-grid">
                <div><strong>Dignity:</strong> {analysis.dignity_analysis?.dignity}</div>
                <div><strong>Functional Nature:</strong> {analysis.dignity_analysis?.functional_nature}</div>
                <div><strong>Shadbala Grade:</strong> {analysis.strength_analysis?.shadbala_grade}</div>
                <div><strong>Shadbala Points:</strong> {analysis.strength_analysis?.shadbala_points}</div>
              </div>
            </div>
            
            <div className="analysis-section">
              <h4>House Analysis</h4>
              <div className="info-grid">
                <div><strong>House Types:</strong> {analysis.house_position_analysis?.house_types?.join(', ')}</div>
                <div><strong>House Strength:</strong> {analysis.house_position_analysis?.house_strength}</div>
                <div><strong>Significance:</strong> {analysis.house_position_analysis?.house_significance}</div>
              </div>
            </div>
            
            {analysis.conjunctions?.has_conjunctions && (
              <div className="analysis-section">
                <h4>Conjunctions</h4>
                <div className="conjunctions-list">
                  {analysis.conjunctions.conjunctions?.map((conj, idx) => (
                    <div key={idx} className="conjunction-item">
                      <strong>{conj.planet}:</strong> {conj.effect} (Orb: {conj.orb?.toFixed(2)}°)
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="analysis-section">
              <h4>Overall Assessment</h4>
              <div className="info-grid">
                <div><strong>Strength Score:</strong> {analysis.overall_assessment?.overall_strength_score}</div>
                <div><strong>Classical Grade:</strong> {analysis.overall_assessment?.classical_grade}</div>
              </div>
              {analysis.overall_assessment?.key_strengths?.length > 0 && (
                <div><strong>Key Strengths:</strong> {analysis.overall_assessment.key_strengths.join(', ')}</div>
              )}
              {analysis.overall_assessment?.key_weaknesses?.length > 0 && (
                <div><strong>Key Weaknesses:</strong> {analysis.overall_assessment.key_weaknesses.join(', ')}</div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const formatContextData = (contextData) => {
    if (!contextData || !contextData.context) return null;
    
    const data = contextData.context;
    
    return (
      <div className="structured-context">
        {/* Birth Details */}
        <div className="context-section">
          <h3 className="section-header">🎂 Birth Details</h3>
          <div className="info-grid">
            <div className="info-item">
              <span className="label">Date:</span>
              <span className="value">{data.birth_details?.date}</span>
            </div>
            <div className="info-item">
              <span className="label">Time:</span>
              <span className="value">{data.birth_details?.time}</span>
            </div>
            <div className="info-item">
              <span className="label">Place:</span>
              <span className="value">{data.birth_details?.place}</span>
            </div>
            <div className="info-item">
              <span className="label">Coordinates:</span>
              <span className="value">{data.birth_details?.latitude}°, {data.birth_details?.longitude}°</span>
            </div>
          </div>
        </div>

        {/* Ascendant Info */}
        {data.ascendant_info && (
          <div className="context-section">
            <h3 className="section-header">🌅 Ascendant Information</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="label">Sign:</span>
                <span className="value">{data.ascendant_info.sign_name}</span>
              </div>
              <div className="info-item">
                <span className="label">Degree:</span>
                <span className="value">{data.ascendant_info.exact_degree_in_sign?.toFixed(2)}°</span>
              </div>
              <div className="info-item">
                <span className="label">Formatted:</span>
                <span className="value">{data.ascendant_info.formatted}</span>
              </div>
            </div>
          </div>
        )}

        {/* Planetary Positions */}
        {data.d1_chart?.planets && (
          <div className="context-section">
            <h3 className="section-header">🪐 Planetary Positions (D1 Chart)</h3>
            <div className="planets-grid">
              {Object.entries(data.d1_chart.planets).map(([planet, info]) => (
                <div key={planet} className="planet-card">
                  <div className="planet-name">{planet}</div>
                  <div className="planet-details">
                    <div>Sign: {['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'][info.sign]}</div>
                    <div>House: {info.house}</div>
                    <div>Degree: {info.degree?.toFixed(2)}°</div>
                    {info.retrograde && <div className="retrograde">Retrograde</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Planetary Analysis */}
        {data.planetary_analysis && (
          <div className="context-section">
            <h3 className="section-header">🌌 Planetary Analysis</h3>
            <div className="analysis-grid">
              {Object.entries(data.planetary_analysis).map(([planet, analysis]) => (
                <PlanetaryAnalysisCard key={planet} planet={planet} analysis={analysis} />
              ))}
            </div>
            <PlanetaryModal planetData={selectedPlanet} onClose={() => setSelectedPlanet(null)} />
          </div>
        )}

        {/* Chara Karakas */}
        {data.chara_karakas?.chara_karakas && (
          <div className="context-section">
            <h3 className="section-header">👑 Chara Karakas (Jaimini System)</h3>
            <div className="karakas-grid">
              {Object.entries(data.chara_karakas.chara_karakas).map(([karaka, info]) => (
                <div key={karaka} className="karaka-card">
                  <div className="karaka-title">{karaka}</div>
                  <div className="karaka-planet">{info.planet}</div>
                  <div className="karaka-description">{info.title}</div>
                  <div className="karaka-areas">
                    {info.life_areas?.map((area, idx) => (
                      <span key={idx} className="life-area">{area}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Nakshatras */}
        {data.planetary_analysis && (
          <div className="context-section">
            <h3 className="section-header">⭐ Planetary Nakshatras</h3>
            <div className="nakshatras-grid">
              {Object.entries(data.planetary_analysis).map(([planet, analysis]) => (
                analysis.basic_info?.nakshatra && (
                  <div key={planet} className="nakshatra-card">
                    <div className="nakshatra-planet">{planet}</div>
                    <div className="nakshatra-name">{analysis.basic_info.nakshatra}</div>
                    <div className="nakshatra-details">
                      <div>Sign: {analysis.basic_info.sign_name}</div>
                      <div>Degree: {analysis.basic_info.degree?.toFixed(2)}°</div>
                    </div>
                  </div>
                )
              ))}
            </div>
          </div>
        )}

        {/* Current Dashas */}
        {data.current_dashas && (
          <div className="context-section">
            <h3 className="section-header">⏰ Current Dasha Periods</h3>
            <div className="dasha-info">
              <div className="dasha-item">
                <span className="dasha-level">Mahadasha:</span>
                <span className="dasha-planet">{data.current_dashas.mahadasha?.planet}</span>
              </div>
              <div className="dasha-item">
                <span className="dasha-level">Antardasha:</span>
                <span className="dasha-planet">{data.current_dashas.antardasha?.planet}</span>
              </div>
              <div className="dasha-item">
                <span className="dasha-level">Pratyantardasha:</span>
                <span className="dasha-planet">{data.current_dashas.pratyantardasha?.planet}</span>
              </div>
            </div>
          </div>
        )}

        {/* Yogas */}
        {data.yogas && (
          <div className="context-section">
            <h3 className="section-header">🔮 Yogas & Combinations</h3>
            <div className="yogas-container">
              {Object.entries(data.yogas).map(([yogaType, yogas]) => {
                if (!yogas || (Array.isArray(yogas) && yogas.length === 0)) return null;
                return (
                  <div key={yogaType} className="yoga-category">
                    <h4 className="yoga-type">{yogaType.replace(/_/g, ' ').toUpperCase()}</h4>
                    <div className="yoga-list">
                      {Array.isArray(yogas) ? yogas.map((yoga, idx) => (
                        <div key={idx} className="yoga-item">
                          <div className="yoga-name">{yoga.name}</div>
                          <div className="yoga-desc">{yoga.description}</div>
                          {yoga.strength && <div className="yoga-strength">Strength: {yoga.strength}</div>}
                        </div>
                      )) : (
                        <div className="yoga-item">
                          <div className="yoga-desc">{JSON.stringify(yogas)}</div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Divisional Charts */}
        {data.divisional_charts && (
          <div className="context-section">
            <h3 className="section-header">📊 Divisional Charts</h3>
            <div className="divisional-charts">
              {Object.entries(data.divisional_charts).map(([chartName, chartData]) => (
                <div key={chartName} className="chart-summary">
                  <h4 className="chart-name">{chartData.chart_name || chartName}</h4>
                  <div className="chart-info">
                    <div>Division: D{chartData.division_number}</div>
                    <div>Planets: {Object.keys(chartData.divisional_chart?.planets || {}).length}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All Other Sections */}
        {Object.entries(data).filter(([key]) => !['birth_details', 'ascendant_info', 'd1_chart', 'divisional_charts', 'chara_karakas', 'current_dashas', 'yogas', 'planetary_analysis'].includes(key)).map(([key, value]) => {
          const icons = {
            special_points: '✨',
            relationships: '🔗',
            advanced_analysis: '🔬',
            kalchakra_dasha: '⏳',
            house_lordships: '🏠',
            house_significations: '📚',
            transit_data_availability: '🚀'
          };
          
          return (
            <div key={key} className="context-section">
              <h3 className="section-header">{icons[key] || '📊'} {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
              <div className="generic-content">
                {typeof value === 'object' ? (
                  <div className="object-display">
                    {Object.entries(value).map(([subKey, subValue]) => (
                      <div key={subKey} className="object-item">
                        <strong>{subKey.replace(/_/g, ' ')}:</strong>
                        <span>{typeof subValue === 'object' ? JSON.stringify(subValue, null, 2) : String(subValue)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="simple-value">{String(value)}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="context-tab">
        <div className="loading-state">
          <div className="spinner"></div>
          <h3>🔍 Loading Astrological Context</h3>
          <p>Gathering comprehensive birth chart data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="context-tab">
        <div className="error-state">
          <h3>⚠️ Error Loading Context</h3>
          <p>{error}</p>
          <button onClick={loadContext}>Retry</button>
        </div>
      </div>
    );
  }

  if (!contextData) {
    return (
      <div className="context-tab">
        <div className="error-state">
          <h3>📊 No Context Available</h3>
          <p>Could not load astrological context.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="context-tab">
      <div className="context-header">
        <h3>🪐 Astrological Context</h3>
        <p>Complete birth chart data sent to AI for analysis</p>
        <div className="context-stats">
          <span className="stat">📏 {contextData.context_length} characters</span>
        </div>
      </div>

      <div className="context-content">
        {formatContextData(contextData)}
      </div>
    </div>
  );
};

export default AstrologicalContextTab;