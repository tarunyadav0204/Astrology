import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import './PredictionPopup.css';

const PredictionPopup = ({ isOpen, onClose, aspect, period, birthData, natalChart, dashaData }) => {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && aspect && period) {
      fetchPrediction();
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

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getIntensityColor = (intensity) => {
    if (intensity >= 2.0) return '#ff4444';
    if (intensity >= 1.5) return '#ff8800';
    if (intensity >= 1.0) return '#ffaa00';
    return '#888888';
  };

  if (!isOpen) return null;

  return createPortal(
    <div className="prediction-popup-overlay" onClick={onClose}>
      <div className="prediction-popup" onClick={e => e.stopPropagation()}>
        <div className="popup-header">
          <h3>Transit Prediction</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="popup-content">
          {loading && (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Generating prediction...</p>
            </div>
          )}

          {error && (
            <div className="error-state">
              <p>Error: {error}</p>
              <button onClick={fetchPrediction}>Retry</button>
            </div>
          )}

          {prediction && (
            <div className="prediction-content">
              <div className="aspect-summary">
                <h4>{prediction.aspect_summary}</h4>
                <div className="period-info">
                  <span className="period-dates">
                    {formatDate(prediction.period_info.start_date)} - {formatDate(prediction.period_info.end_date)}
                  </span>
                  {prediction.period_info.peak_date && (
                    <span className="peak-date">Peak: {formatDate(prediction.period_info.peak_date)}</span>
                  )}
                </div>
              </div>

              {prediction.is_gandanta_only ? (
                // Show only Gandanta explanation for Gandanta aspects
                prediction.gandanta_explanation && (
                  <div className="gandanta-explanation-section">
                    <h5>{prediction.gandanta_explanation.title}</h5>
                    <p className="gandanta-description">{prediction.gandanta_explanation.description}</p>
                    <p className="gandanta-significance">{prediction.gandanta_explanation.significance}</p>
                    <div className="gandanta-effects">
                      <strong>Key Effects:</strong>
                      <ul>
                        {prediction.gandanta_explanation.effects.map((effect, index) => (
                          <li key={index}>{effect}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="gandanta-advice">
                      <strong>Guidance:</strong> {prediction.gandanta_explanation.advice}
                    </div>
                  </div>
                )
              ) : prediction.is_nakshatra_only ? (
                // Show simplified view for nakshatra connections
                <div className="prediction-details">
                  <div className="theme-section">
                    <h5>Theme</h5>
                    <p>{prediction.theme}</p>
                  </div>
                  <div className="effects-section">
                    <h5>Effects</h5>
                    {prediction.effects.positive && (
                      <div className="effect positive">
                        <strong>Positive:</strong> {prediction.effects.positive}
                      </div>
                    )}
                    {prediction.effects.negative && (
                      <div className="effect negative">
                        <strong>Challenging:</strong> {prediction.effects.negative}
                      </div>
                    )}
                    {prediction.effects.neutral && (
                      <div className="effect neutral">
                        <strong>General:</strong> {prediction.effects.neutral}
                      </div>
                    )}
                  </div>
                </div>
              ) : (

              <div className="prediction-details">
                <div className="theme-section">
                  <h5>Theme</h5>
                  <p>{prediction.theme}</p>
                </div>

                {prediction.gandanta_explanation && (
                  <div className="gandanta-explanation-section">
                    <h5>{prediction.gandanta_explanation.title}</h5>
                    <p className="gandanta-description">{prediction.gandanta_explanation.description}</p>
                    <p className="gandanta-significance">{prediction.gandanta_explanation.significance}</p>
                    <div className="gandanta-effects">
                      <strong>Key Effects:</strong>
                      <ul>
                        {prediction.gandanta_explanation.effects.map((effect, index) => (
                          <li key={index}>{effect}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="gandanta-advice">
                      <strong>Guidance:</strong> {prediction.gandanta_explanation.advice}
                    </div>
                  </div>
                )}

                <div className="timing-intensity">
                  <div className="timing">
                    <h5>Timing</h5>
                    <p>{prediction.timing}</p>
                  </div>
                  <div className="intensity">
                    <h5>Intensity</h5>
                    <span 
                      className="intensity-value"
                      style={{ color: getIntensityColor(prediction.intensity) }}
                    >
                      {prediction.intensity}x
                    </span>
                    {prediction.dasha_hierarchy && (
                      <div className="dasha-hierarchy">
                        <span className="dasha-label">🎯</span>
                        <span className="dasha-chain">
                          {Object.entries(prediction.dasha_hierarchy).map(([level, dashaObj], index, arr) => {
                            const planet = dashaObj?.planet || dashaObj;
                            const isActive = prediction.activated_planets?.includes(planet);
                            return (
                              <span key={level}>
                                <span className={`dasha-planet ${isActive ? 'active-planet' : ''}`}>
                                  {planet}
                                </span>
                                {index < arr.length - 1 && <span className="dasha-arrow"> → </span>}
                              </span>
                            );
                          })}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {prediction.planetary_analysis && (
                  <div className="planetary-analysis-section">
                    <h5>Planetary Analysis</h5>
                    <div className="planets-grid">
                      <div className="planet-analysis natal-planet">
                        <h6>{prediction.planetary_analysis.natal_planet.name} (Receiving)</h6>
                        <div className="planet-details">
                          <span className="dignity-status">
                            {prediction.planetary_analysis.natal_planet.dignity.replace('_', ' ')}
                          </span>
                          <div className="benefic-analysis">
                            <span className="natural-nature">
                              Natural {prediction.planetary_analysis.natal_planet.benefic_analysis?.natural || 'neutral'}
                            </span>
                            <span className="functional-nature">
                              Functional {prediction.planetary_analysis.natal_planet.functional_nature}
                            </span>
                            {prediction.planetary_analysis.natal_planet.benefic_analysis?.temporal === 'benefic' && (
                              <span className="temporal-benefic">
                                Dasha Lord (Temporal Benefic)
                              </span>
                            )}
                          </div>
                          {prediction.planetary_analysis.natal_planet.combustion_status !== 'normal' && (
                            <span className={`combustion-status ${prediction.planetary_analysis.natal_planet.combustion_status}`}>
                              {prediction.planetary_analysis.natal_planet.combustion_status === 'combust' ? 'Combust' : 'Cazimi'}
                            </span>
                          )}
                          {prediction.planetary_analysis.natal_planet.retrograde_status !== 'direct' && (
                            <span className={`retrograde-status ${prediction.planetary_analysis.natal_planet.retrograde_status}`}>
                              {prediction.planetary_analysis.natal_planet.retrograde_status === 'retrograde' ? 'Retrograde' : 'Stationary'}
                            </span>
                          )}
                          <span className="strength-value">
                            Strength: {(prediction.planetary_analysis.natal_planet.combined_strength * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <div className="planet-analysis transiting-planet">
                        <h6>{prediction.planetary_analysis.transiting_planet.name} (Activating)</h6>
                        <div className="planet-details">
                          <span className="dignity-status">
                            {prediction.planetary_analysis.transiting_planet.dignity.replace('_', ' ')}
                          </span>
                          <div className="benefic-analysis">
                            <span className="natural-nature">
                              Natural {prediction.planetary_analysis.transiting_planet.benefic_analysis?.natural || 'neutral'}
                            </span>
                            <span className="functional-nature">
                              Functional {prediction.planetary_analysis.transiting_planet.functional_nature}
                            </span>
                            {prediction.planetary_analysis.transiting_planet.benefic_analysis?.temporal === 'benefic' && (
                              <span className="temporal-benefic">
                                Dasha Lord (Temporal Benefic)
                              </span>
                            )}
                          </div>
                          {prediction.planetary_analysis.transiting_planet.combustion_status !== 'normal' && (
                            <span className={`combustion-status ${prediction.planetary_analysis.transiting_planet.combustion_status}`}>
                              {prediction.planetary_analysis.transiting_planet.combustion_status === 'combust' ? 'Combust' : 'Cazimi'}
                            </span>
                          )}
                          {prediction.planetary_analysis.transiting_planet.retrograde_status !== 'direct' && (
                            <span className={`retrograde-status ${prediction.planetary_analysis.transiting_planet.retrograde_status}`}>
                              {prediction.planetary_analysis.transiting_planet.retrograde_status === 'retrograde' ? 'Retrograde' : 'Stationary'}
                            </span>
                          )}
                          <span className="strength-value">
                            Strength: {(prediction.planetary_analysis.transiting_planet.combined_strength * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {prediction.retrograde_effects && Object.keys(prediction.retrograde_effects).length > 0 && (
                  <div className="retrograde-effects-section">
                    <h5>Vakri Gati (Retrograde) Effects</h5>
                    {prediction.retrograde_effects.natal_planet && (
                      <div className="retrograde-planet-effects">
                        <h6>{prediction.planetary_analysis.natal_planet.name} Retrograde</h6>
                        <div className="retrograde-significations">
                          <div className="enhanced-qualities">
                            <strong>Enhanced:</strong> {prediction.retrograde_effects.natal_planet.enhanced.join(', ')}
                          </div>
                          <div className="modified-effects">
                            <strong>Modified:</strong> {prediction.retrograde_effects.natal_planet.modified.join(', ')}
                          </div>
                        </div>
                      </div>
                    )}
                    {prediction.retrograde_effects.transiting_planet && (
                      <div className="retrograde-planet-effects">
                        <h6>{prediction.planetary_analysis.transiting_planet.name} Retrograde</h6>
                        <div className="retrograde-significations">
                          <div className="enhanced-qualities">
                            <strong>Enhanced:</strong> {prediction.retrograde_effects.transiting_planet.enhanced.join(', ')}
                          </div>
                          <div className="modified-effects">
                            <strong>Modified:</strong> {prediction.retrograde_effects.transiting_planet.modified.join(', ')}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {prediction.nakshatra_analysis && Object.keys(prediction.nakshatra_analysis).length > 0 && (
                  <div className="nakshatra-analysis-section">
                    <h5>Nakshatra Analysis</h5>
                    <div className="nakshatra-summary">
                      <p className="summary-text">{prediction.nakshatra_analysis.summary}</p>
                    </div>
                    
                    <div className="nakshatra-details">
                      <div className="nakshatra-positions">
                        <div className="nakshatra-position">
                          <h6>Transiting Planet</h6>
                          <span className="nakshatra-name">
                            {prediction.nakshatra_analysis.transiting_nakshatra?.nakshatra_name}
                          </span>
                          <span className="pada-info">
                            Pada {prediction.nakshatra_analysis.transiting_nakshatra?.pada_number} 
                            (Lord: {prediction.nakshatra_analysis.transiting_nakshatra?.pada_lord})
                          </span>
                        </div>
                        <div className="nakshatra-position">
                          <h6>Natal Planet</h6>
                          <span className="nakshatra-name">
                            {prediction.nakshatra_analysis.natal_nakshatra?.nakshatra_name}
                          </span>
                          <span className="pada-info">
                            Pada {prediction.nakshatra_analysis.natal_nakshatra?.pada_number}
                            (Lord: {prediction.nakshatra_analysis.natal_nakshatra?.pada_lord})
                          </span>
                        </div>
                      </div>
                      
                      <div className="compatibility-score">
                        <span className="score-label">Nakshatra Compatibility:</span>
                        <span className="score-value" style={{
                          color: prediction.nakshatra_analysis.compatibility_score >= 0.75 ? '#4caf50' : 
                                 prediction.nakshatra_analysis.compatibility_score >= 0.5 ? '#ff9800' : '#f44336'
                        }}>
                          {(prediction.nakshatra_analysis.compatibility_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      
                      {prediction.nakshatra_analysis.timing_precision && (
                        <div className="timing-precision">
                          <h6>Pada Timing</h6>
                          <span className="timing-intensity">
                            Intensity: {prediction.nakshatra_analysis.timing_precision.timing_intensity}
                          </span>
                          <span className="timing-note">
                            {prediction.nakshatra_analysis.timing_precision.timing_note}
                          </span>
                        </div>
                      )}
                      
                      {prediction.nakshatra_analysis.nakshatra_effects && (
                        <div className="nakshatra-effects">
                          {prediction.nakshatra_analysis.nakshatra_effects.enhanced_qualities?.length > 0 && (
                            <div className="effect-group positive">
                              <strong>Enhanced Qualities:</strong>
                              <ul>
                                {prediction.nakshatra_analysis.nakshatra_effects.enhanced_qualities.map((quality, index) => (
                                  <li key={index}>{quality}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {prediction.nakshatra_analysis.nakshatra_effects.challenges?.length > 0 && (
                            <div className="effect-group negative">
                              <strong>Challenges:</strong>
                              <ul>
                                {prediction.nakshatra_analysis.nakshatra_effects.challenges.map((challenge, index) => (
                                  <li key={index}>{challenge}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {prediction.nakshatra_analysis.nakshatra_effects.opportunities?.length > 0 && (
                            <div className="effect-group neutral">
                              <strong>Opportunities:</strong>
                              <ul>
                                {prediction.nakshatra_analysis.nakshatra_effects.opportunities.map((opportunity, index) => (
                                  <li key={index}>{opportunity}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {prediction.nakshatra_analysis.nakshatra_effects.timing_advice && (
                            <div className="timing-advice">
                              <strong>Timing Advice:</strong> {prediction.nakshatra_analysis.nakshatra_effects.timing_advice}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="effects-section">
                  <h5>Effects</h5>
                  {prediction.effects.positive && (
                    <div className="effect positive">
                      <strong>Positive:</strong> {prediction.effects.positive}
                    </div>
                  )}
                  {prediction.effects.negative && (
                    <div className="effect negative">
                      <strong>Challenging:</strong> {prediction.effects.negative}
                    </div>
                  )}
                  {prediction.effects.neutral && (
                    <div className="effect neutral">
                      <strong>General:</strong> {prediction.effects.neutral}
                    </div>
                  )}
                </div>

                {prediction.house_wise_areas && Object.keys(prediction.house_wise_areas).length > 0 && (
                  <div className="affected-areas">
                    <h5>Life Areas by House</h5>
                    <div className="house-areas-list">
                      {Object.entries(prediction.house_wise_areas).map(([house, areas]) => {
                        const getOrdinal = (num) => {
                          const suffix = ['th', 'st', 'nd', 'rd'];
                          const v = num % 100;
                          return num + (suffix[(v - 20) % 10] || suffix[v] || suffix[0]);
                        };
                        return (
                          <div key={house} className="house-area-group" data-house={house}>
                            <span className="house-label">{getOrdinal(parseInt(house))} House:</span>
                            <div className="areas-list">
                              {areas.map((area, index) => (
                                <span key={index} className="area-tag">{area}</span>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {prediction.planetary_dignity && Object.keys(prediction.planetary_dignity).length > 0 && !prediction.planetary_analysis && (
                  <div className="dignity-section">
                    <h5>Planetary Strength ({prediction.activated_planets?.[1]})</h5>
                    <div className="dignity-info">
                      <div className="dignity-details">
                        <span className="dignity-status">
                          {prediction.activated_planets?.[1]} is {prediction.planetary_dignity.natal_planet_dignity?.replace('_', ' ')}
                        </span>
                        {prediction.planetary_dignity.functional_nature && (
                          <span className="functional-nature">
                            Functional {prediction.planetary_dignity.functional_nature}
                          </span>
                        )}
                      </div>
                      <span className="dignity-modifier">
                        Combined Strength: {(prediction.planetary_dignity.combined_modifier * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                )}

                <div className="activation-summary">
                  <div className="activated-planets">
                    <h5>Planets Activated</h5>
                    <div className="planet-list">
                      {prediction.activated_planets?.map((planet, index) => (
                        <span key={index} className="planet-tag">{planet}</span>
                      ))}
                    </div>
                  </div>
                  <div className="activated-houses">
                    <h5>Houses Activated</h5>
                    <div className="house-list">
                      {prediction.house_activations?.map((activation, index) => {
                        const getOrdinal = (num) => {
                          const suffix = ['th', 'st', 'nd', 'rd'];
                          const v = num % 100;
                          return num + (suffix[(v - 20) % 10] || suffix[v] || suffix[0]);
                        };
                        return (
                          <div key={index} className="house-activation">
                            <span className="house-tag">{getOrdinal(activation.house)}</span>
                            <span className="house-reasons">{activation.reasons.join(', ')}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {prediction.remedies && (
                  <div className="remedies-section">
                    <h5>Remedies</h5>
                    {prediction.remedies.planet_remedies?.mantras && (
                      <div className="remedy-group">
                        <strong>Mantras:</strong>
                        <ul>
                          {prediction.remedies.planet_remedies.mantras.map((mantra, index) => (
                            <li key={index}>{mantra}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {prediction.remedies.planet_remedies?.gemstones && (
                      <div className="remedy-group">
                        <strong>Gemstones:</strong> {prediction.remedies.planet_remedies.gemstones.join(', ')}
                      </div>
                    )}
                    {prediction.remedies.house_remedies?.length > 0 && (
                      <div className="remedy-group">
                        <strong>General:</strong> {prediction.remedies.house_remedies.slice(0, 3).join(', ')}
                      </div>
                    )}
                  </div>
                )}
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

export default PredictionPopup;