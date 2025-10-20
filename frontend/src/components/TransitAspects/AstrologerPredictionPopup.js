import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import './AstrologerPredictionPopup.css';

const AstrologerPredictionPopup = ({ isOpen, onClose, aspect, period, birthData, natalChart, dashaData }) => {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && aspect && period) {
      fetchPrediction();
      
      // Remove native title tooltips and speed up custom ones
      setTimeout(() => {
        const popup = document.querySelector('.astrologer-popup');
        if (popup) {
          // Remove all title attributes to disable native tooltips
          const elementsWithTitle = popup.querySelectorAll('[title]');
          elementsWithTitle.forEach(el => {
            el.setAttribute('data-original-title', el.getAttribute('title'));
            el.removeAttribute('title');
          });
          
          // Speed up custom tooltips by removing delays
          const style = document.createElement('style');
          style.textContent = `
            .astrologer-popup .tooltip { transition-delay: 0ms !important; }
            .astrologer-popup [data-tooltip] { transition-delay: 0ms !important; }
          `;
          document.head.appendChild(style);
        }
      }, 100);
    }
  }, [isOpen, aspect, period]);

  const fetchPrediction = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/vedic-transit-prediction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          birth_data: birthData,
          aspect_data: aspect,
          period_data: period,
          natal_chart: natalChart,
          dasha_data: dashaData
        })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch prediction');
      }

      const data = await response.json();
      setPrediction(data.prediction);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDegree = (longitude) => {
    const sign = Math.floor(longitude / 30);
    const degree = longitude % 30;
    const minutes = (degree % 1) * 60;
    return `${Math.floor(degree)}°${Math.floor(minutes)}'`;
  };

  const getSignName = (signNum) => {
    const signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'];
    return signs[signNum] || 'Unk';
  };

  const getDignityColor = (dignity) => {
    const colors = {
      'exalted': '#4caf50',
      'moolatrikona': '#8bc34a',
      'own_sign': '#2196f3',
      'friend_sign': '#03a9f4',
      'neutral_sign': '#9e9e9e',
      'enemy_sign': '#ff9800',
      'debilitated': '#f44336'
    };
    return colors[dignity] || '#9e9e9e';
  };

  const getStrengthBar = (strength) => {
    const percentage = Math.round(strength * 100);
    const color = percentage >= 75 ? '#4caf50' : percentage >= 50 ? '#ff9800' : '#f44336';
    return (
      <div className="strength-bar">
        <div className="strength-fill" style={{ width: `${percentage}%`, backgroundColor: color }}></div>
        <span className="strength-text">{percentage}%</span>
      </div>
    );
  };

  const formatOrdinal = (num) => {
    const suffixes = ['th', 'st', 'nd', 'rd'];
    const v = num % 100;
    return num + (suffixes[(v - 20) % 10] || suffixes[v] || suffixes[0]);
  };

  const getHouseWord = (num) => {
    const words = ['', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth'];
    return words[num] || `${num}th`;
  };

  if (!isOpen) return null;

  return createPortal(
    <div className="astrologer-popup-overlay" onClick={onClose}>
      <div className="astrologer-popup" onClick={e => e.stopPropagation()}>
        <div className="popup-header">
          <h3>Technical Analysis</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="popup-content">
          {loading && (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Calculating...</p>
            </div>
          )}

          {error && (
            <div className="error-state">
              <p>Error: {error}</p>
              <button onClick={fetchPrediction}>Retry</button>
            </div>
          )}

          {prediction && (
            <div className="astrologer-content">
              {/* Technical Header */}
              <div className="technical-header">
                <div className="aspect-formula">
                  <span className="transit-planet">{aspect.planet1}</span>
                  <span className="aspect-symbol">→</span>
                  <span className="natal-planet">{aspect.planet2}</span>
                  <span className="aspect-type">({getHouseWord(parseInt(aspect.aspect_type.replace(/\D/g, '')))} aspect)</span>
                </div>
                <div className="period-technical">
                  {period.start_date} to {period.end_date}
                  {prediction.intensity && (
                    <span className="intensity-badge">I: {prediction.intensity}x</span>
                  )}
                </div>
              </div>

              {/* Planetary Analysis Grid */}
              {prediction.planetary_analysis && (
                <div className="planetary-grid">
                  <div className="planet-card natal">
                    <div className="planet-header">
                      <h4>{prediction.planetary_analysis.natal_planet.name} (Natal)</h4>
                      <span className="house-position">H{natalChart?.planets?.[prediction.planetary_analysis.natal_planet.name]?.house}</span>
                    </div>
                    
                    <div className="technical-data">
                      <div className="longitude-data">
                        <span className="label">Long:</span>
                        <span className="value">
                          {natalChart?.planets?.[prediction.planetary_analysis.natal_planet.name]?.longitude && 
                            formatDegree(natalChart.planets[prediction.planetary_analysis.natal_planet.name].longitude)
                          } {getSignName(natalChart?.planets?.[prediction.planetary_analysis.natal_planet.name]?.sign)}
                        </span>
                      </div>
                      
                      <div className="dignity-row">
                        <span className="label">Dignity:</span>
                        <span 
                          className="dignity-badge"
                          style={{ backgroundColor: getDignityColor(prediction.planetary_analysis.natal_planet.dignity) }}
                        >
                          {prediction.planetary_analysis.natal_planet.dignity.replace('_', ' ')}
                        </span>
                      </div>

                      <div className="nature-row">
                        <span className="label">Nature:</span>
                        <div className="nature-badges">
                          <span className="nat-badge">N: {prediction.planetary_analysis.natal_planet.benefic_analysis?.natural}</span>
                          <span className="func-badge">F: {prediction.planetary_analysis.natal_planet.functional_nature}</span>
                          {prediction.planetary_analysis.natal_planet.benefic_analysis?.temporal === 'benefic' && (
                            <span className="temp-badge">T: Dasha Lord</span>
                          )}
                          {prediction.planetary_analysis.natal_planet.retrograde_status === 'stationary' && (
                            <span className="stat-badge">Stationary</span>
                          )}
                          {prediction.planetary_analysis.natal_planet.badhaka_status && (
                            <span className="badhaka-badge">Badhaka</span>
                          )}
                          {prediction.planetary_analysis.natal_planet.maraka_status && (
                            <span className="maraka-badge">Maraka</span>
                          )}
                        </div>
                      </div>

                      <div className="status-row">
                        {prediction.planetary_analysis.natal_planet.combustion_status !== 'normal' && (
                          <span className={`status-badge ${prediction.planetary_analysis.natal_planet.combustion_status}`}>
                            {prediction.planetary_analysis.natal_planet.combustion_status}
                          </span>
                        )}
                        {prediction.planetary_analysis.natal_planet.retrograde_status === 'retrograde' && (
                          <span className="status-badge retrograde">
                            Retrograde
                          </span>
                        )}
                      </div>

                      <div className="strength-row">
                        <span className="label">Strength:</span>
                        {getStrengthBar(prediction.planetary_analysis.natal_planet.combined_strength)}
                      </div>
                    </div>
                  </div>

                  <div className="planet-card transiting">
                    <div className="planet-header">
                      <h4>{prediction.planetary_analysis.transiting_planet.name} (Transit)</h4>
                      <span className="house-position">H{natalChart?.planets?.[prediction.planetary_analysis.transiting_planet.name]?.house}</span>
                    </div>
                    
                    <div className="technical-data">
                      <div className="longitude-data">
                        <span className="label">Long:</span>
                        <span className="value">
                          {natalChart?.planets?.[prediction.planetary_analysis.transiting_planet.name]?.longitude && 
                            formatDegree(natalChart.planets[prediction.planetary_analysis.transiting_planet.name].longitude)
                          } {getSignName(natalChart?.planets?.[prediction.planetary_analysis.transiting_planet.name]?.sign)}
                        </span>
                      </div>
                      
                      <div className="dignity-row">
                        <span className="label">Dignity:</span>
                        <span 
                          className="dignity-badge"
                          style={{ backgroundColor: getDignityColor(prediction.planetary_analysis.transiting_planet.dignity) }}
                        >
                          {prediction.planetary_analysis.transiting_planet.dignity.replace('_', ' ')}
                        </span>
                      </div>

                      <div className="nature-row">
                        <span className="label">Nature:</span>
                        <div className="nature-badges">
                          <span className="nat-badge">N: {prediction.planetary_analysis.transiting_planet.benefic_analysis?.natural}</span>
                          <span className="func-badge">F: {prediction.planetary_analysis.transiting_planet.functional_nature}</span>
                          {prediction.planetary_analysis.transiting_planet.benefic_analysis?.temporal === 'benefic' && (
                            <span className="temp-badge">T: Dasha Lord</span>
                          )}
                          {prediction.planetary_analysis.transiting_planet.retrograde_status === 'stationary' && (
                            <span className="stat-badge">Stationary</span>
                          )}
                          {prediction.planetary_analysis.transiting_planet.badhaka_status && (
                            <span className="badhaka-badge">Badhaka</span>
                          )}
                          {prediction.planetary_analysis.transiting_planet.maraka_status && (
                            <span className="maraka-badge">Maraka</span>
                          )}
                        </div>
                      </div>

                      <div className="status-row">
                        {prediction.planetary_analysis.transiting_planet.combustion_status !== 'normal' && (
                          <span className={`status-badge ${prediction.planetary_analysis.transiting_planet.combustion_status}`}>
                            {prediction.planetary_analysis.transiting_planet.combustion_status}
                          </span>
                        )}
                        {prediction.planetary_analysis.transiting_planet.retrograde_status === 'retrograde' && (
                          <span className="status-badge retrograde">
                            Retrograde
                          </span>
                        )}
                      </div>

                      <div className="strength-row">
                        <span className="label">Strength:</span>
                        {getStrengthBar(prediction.planetary_analysis.transiting_planet.combined_strength)}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Dasha Analysis */}
              {prediction.dasha_hierarchy && (
                <div className="dasha-section">
                  <h5>Dasha Context</h5>
                  <div className="dasha-chain">
                    {Object.entries(prediction.dasha_hierarchy).map(([level, dashaObj], index, arr) => {
                      const planet = dashaObj?.planet || dashaObj;
                      const isActive = prediction.activated_planets?.includes(planet);
                      return (
                        <span key={level} className="dasha-level">
                          <span className={`dasha-planet ${isActive ? 'active' : ''}`}>
                            {planet}
                          </span>
                          {index < arr.length - 1 && <span className="dasha-arrow">→</span>}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Nakshatra Analysis */}
              {prediction.nakshatra_analysis && (
                <div className="nakshatra-section">
                  <h5>Nakshatra Analysis</h5>
                  <div className="nakshatra-grid">
                    <div className="nak-position">
                      <h6>Transit:</h6>
                      <span className="nak-data">
                        {prediction.nakshatra_analysis.transiting_nakshatra?.nakshatra_name} 
                        P{prediction.nakshatra_analysis.transiting_nakshatra?.pada_number}
                        ({prediction.nakshatra_analysis.transiting_nakshatra?.pada_lord})
                      </span>
                    </div>
                    <div className="nak-position">
                      <h6>Natal:</h6>
                      <span className="nak-data">
                        {prediction.nakshatra_analysis.natal_nakshatra?.nakshatra_name} 
                        P{prediction.nakshatra_analysis.natal_nakshatra?.pada_number}
                        ({prediction.nakshatra_analysis.natal_nakshatra?.pada_lord})
                      </span>
                    </div>
                    <div className="nak-compatibility">
                      <h6>Compatibility:</h6>
                      <span className={`compat-score ${prediction.nakshatra_analysis.compatibility_score === 1.0 ? 'perfect' : ''}`}>
                        {(prediction.nakshatra_analysis.compatibility_score * 100).toFixed(0)}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* House Activations */}
              {prediction.house_activations && (
                <div className="house-section">
                  <h5>House Activations</h5>
                  <div className="house-hierarchy">
                    {prediction.house_activations.primary && prediction.house_activations.primary.length > 0 && (
                      <div className="activation-level">
                        <div className="level-header primary">Primary: Direct tenancy and lordship of main planets</div>
                        <div className="house-grid">
                          {prediction.house_activations.primary.map((activation, index) => (
                            <div key={index} className="house-activation primary">
                              <span className="house-num">H{activation.house}</span>
                              <span className="house-reasons">{activation.reasons.join(', ')}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {prediction.house_activations.secondary && prediction.house_activations.secondary.length > 0 && (
                      <div className="activation-level">
                        <div className="level-header secondary">Secondary: Conjunction-activated lordships (within 3-5°)</div>
                        <div className="house-grid">
                          {prediction.house_activations.secondary.map((activation, index) => (
                            <div key={index} className="house-activation secondary">
                              <span className="house-num">H{activation.house}</span>
                              <span className="house-reasons">{activation.reasons.join(', ')}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {prediction.house_activations.tertiary && prediction.house_activations.tertiary.length > 0 && (
                      <div className="activation-level">
                        <div className="level-header tertiary">Tertiary: Current dasha lord houses (if relevant)</div>
                        <div className="house-grid">
                          {prediction.house_activations.tertiary.map((activation, index) => (
                            <div key={index} className="house-activation tertiary">
                              <span className="house-num">H{activation.house}</span>
                              <span className="house-reasons">{activation.reasons.join(', ')}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Activated Yogas */}
              {prediction.activated_yogas && prediction.activated_yogas.length > 0 && (
                <div className="yoga-section">
                  <h5>Activated Yogas</h5>
                  <div className="yoga-grid">
                    {prediction.activated_yogas.map((yoga, index) => (
                      <div key={index} className={`yoga-card ${yoga.type} ${yoga.strength}`}>
                        <div className="yoga-header">
                          <h6 className="yoga-name">{yoga.name}</h6>
                          <span className={`yoga-strength ${yoga.strength}`}>{yoga.strength.toUpperCase()}</span>
                        </div>
                        <p className="yoga-description">{yoga.description}</p>
                        {yoga.activation_details && yoga.activation_details.length > 0 && (
                          <div className="yoga-activations">
                            <span className="activation-label">Activated by:</span>
                            <ul className="activation-list">
                              {yoga.activation_details.map((detail, idx) => (
                                <li key={idx} className="activation-item">{detail}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        <span className={`yoga-type ${yoga.type}`}>{yoga.type.toUpperCase()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
};

export default AstrologerPredictionPopup;