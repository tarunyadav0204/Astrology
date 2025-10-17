import React, { useState, useEffect } from 'react';
import './ClassicalPrediction.css';

const ClassicalPrediction = ({ birthData }) => {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const fetchPrediction = async () => {
    if (!birthData) return;
    
    setLoading(true);
    try {
      const response = await fetch('/api/classical-prediction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          birth_data: birthData,
          prediction_date: selectedDate
        })
      });
      
      const data = await response.json();
      setPrediction(data);
    } catch (error) {
      console.error('Error fetching classical prediction:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrediction();
  }, [birthData]);

  useEffect(() => {
    if (birthData) {
      fetchPrediction();
    }
  }, [selectedDate]);

  if (!birthData) {
    return <div className="classical-prediction">Please select birth data first</div>;
  }

  return (
    <div className="classical-prediction">
      <div className="prediction-header">
        <h2>Classical Vedic Prediction</h2>
        <div className="date-selector">
          <label>Prediction Date:</label>
          <input 
            type="date" 
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
        </div>
      </div>

      {loading && (
        <div className="loading">
          <div className="loading-text">Calculating comprehensive classical prediction...</div>
          <div className="loading-details">
            Running 7-step analysis with advanced Vedic techniques
          </div>
        </div>
      )}

      {prediction && (
        <div className="prediction-content">
          {/* Main Prediction */}
          <div className="main-prediction">
            <h3>Classical Vedic Prediction for {new Date(selectedDate).toLocaleDateString()}</h3>
            <div className="prediction-text">
              {prediction.prediction?.text || 
               prediction.core_7_step_analysis?.step5_prediction?.prediction_text || 
               "Prediction analysis in progress..."}
            </div>
            <div className="prediction-meta">
              <div className="meta-row">
                <span className="tendency">
                  Overall Tendency: {prediction.analysis_summary?.overall_tendency || 
                                   prediction.core_7_step_analysis?.step5_prediction?.overall_tendency || 'Mixed'}
                </span>
                <span className="confidence">
                  Confidence: {Math.round((prediction.prediction?.confidence || 0.7) * 100)}%
                </span>
              </div>
              <div className="meta-row">
                <span className="themes">
                  Key Areas: {(prediction.analysis_summary?.dominant_themes || 
                              prediction.core_7_step_analysis?.step5_prediction?.dominant_themes || []).join(', ') || 'General'}
                </span>
                <span className="classical-strength">
                  Classical Strength: {Math.round((prediction.prediction?.classical_strength || 0.7) * 100)}%
                </span>
              </div>
              {prediction.analysis_summary?.yogakaraka_planet && (
                <div className="meta-row">
                  <span className="yogakaraka">
                    Yogakaraka: {prediction.analysis_summary.yogakaraka_planet}
                  </span>
                  {prediction.analysis_summary?.atmakaraka && (
                    <span className="atmakaraka">
                      Atmakaraka: {prediction.analysis_summary.atmakaraka}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Analysis Summary */}
          <div className="analysis-summary">
            <div className="summary-stats">
              <div className="stat-item">
                <span className="stat-label">Techniques Applied:</span>
                <span className="stat-value">{prediction.techniques_applied?.length || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Active Dashas:</span>
                <span className="stat-value">{(prediction.analysis_summary?.active_dasha_planets || []).length}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Activated Planets:</span>
                <span className="stat-value">{(prediction.analysis_summary?.activated_planets || []).length}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Activated Houses:</span>
                <span className="stat-value">{(prediction.analysis_summary?.activated_houses || []).length}</span>
              </div>
            </div>
          </div>

          {/* Toggle Details */}
          <button 
            className="toggle-details"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? 'Hide' : 'Show'} Complete Analysis Details
          </button>

          {/* Analysis Details */}
          {showDetails && (
            <div className="analysis-details">
              
              {/* Core 7-Step Analysis */}
              <div className="analysis-section">
                <h3>Core 7-Step Classical Analysis</h3>
                
                {/* Step 1: Active Dashas */}
                <div className="analysis-step">
                  <h4>Step 1: Active Dasha Planets</h4>
                  <div className="step-content">
                    {(prediction.analysis_summary?.active_dasha_planets || 
                      prediction.core_7_step_analysis?.step1_dasha_planets || []).map(planet => (
                      <span key={planet} className="planet-tag dasha">{planet}</span>
                    ))}
                    {prediction.core_7_step_analysis?.step1_dasha_details && (
                      <div className="step-details">
                        <div className="dasha-breakdown">
                          <strong>Current Dasha Levels:</strong>
                          {Object.entries(prediction.core_7_step_analysis.step1_dasha_details).map(([level, data]) => (
                            <span key={level} className="dasha-level">
                              {level}: {typeof data === 'object' ? data.planet || JSON.stringify(data) : data}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Step 2: Transit Activations */}
                <div className="analysis-step">
                  <h4>Step 2: Planets Activated by Transits</h4>
                  <div className="step-content">
                    {(prediction.analysis_summary?.activated_planets || 
                      prediction.core_7_step_analysis?.step2_activated_planets || []).map(planet => (
                      <span key={planet} className="planet-tag activated">{planet}</span>
                    ))}
                    {prediction.core_7_step_analysis?.step2_activation_reasons && (
                      <div className="step-details">
                        <strong>Activation Reasons:</strong>
                        {Object.entries(prediction.core_7_step_analysis.step2_activation_reasons).map(([planet, reasons]) => (
                          <div key={planet} className="activation-reason">
                            <span className="planet-name">{planet}:</span> {reasons.join(', ')}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Step 3: House Activations */}
                <div className="analysis-step">
                  <h4>Step 3: Houses Activated</h4>
                  <div className="step-content">
                    {(prediction.analysis_summary?.activated_houses || 
                      prediction.core_7_step_analysis?.step3_activated_houses || []).map(house => (
                      <span key={house} className="house-tag">House {house}</span>
                    ))}
                    {prediction.core_7_step_analysis?.step3_house_details && (
                      <div className="step-details">
                        <strong>House Activation Details:</strong>
                        {Object.entries(prediction.core_7_step_analysis.step3_house_details).map(([house, details]) => (
                          <div key={house} className="house-detail">
                            <span className="house-number">House {house}:</span>
                            <span className="house-score">Score: {details.score}</span>
                            <span className="house-factors">({details.factors?.join(', ')})</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Step 4: Planet Results */}
                <div className="analysis-step">
                  <h4>Step 4: Comprehensive Planet Result Analysis</h4>
                  <div className="step-content">
                    {prediction.core_7_step_analysis?.step4_planet_results && 
                     Object.entries(prediction.core_7_step_analysis.step4_planet_results).map(([planet, result]) => (
                      <div key={planet} className="planet-result-detailed">
                        <div className="planet-header">
                          <span className={`planet-name ${result.result?.toLowerCase()}`}>{planet}</span>
                          <span className={`result-type ${result.result?.toLowerCase()}`}>{result.result}</span>
                          <span className="result-score">Score: {result.score > 0 ? '+' : ''}{result.score}</span>
                        </div>
                        <div className="planet-factors">
                          <strong>Classical Factors:</strong>
                          <div className="factor-list">
                            {result.factors?.map((factor, idx) => (
                              <span key={idx} className="factor-tag">{factor}</span>
                            ))}
                          </div>
                        </div>
                        {result.detailed_analysis && (
                          <div className="detailed-breakdown">
                            <strong>Detailed Analysis:</strong>
                            {Object.entries(result.detailed_analysis).map(([key, value]) => (
                              <div key={key} className="analysis-item">
                                <span className="analysis-key">{key.replace(/_/g, ' ')}:</span>
                                <span className="analysis-value">{typeof value === 'object' ? JSON.stringify(value) : value}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Step 5: House-Based Predictions */}
                <div className="analysis-step">
                  <h4>Step 5: House-Based Prediction Breakdown</h4>
                  <div className="step-content">
                    {prediction.core_7_step_analysis?.step5_house_predictions && 
                     Object.entries(prediction.core_7_step_analysis.step5_house_predictions).map(([house, pred]) => (
                      <div key={house} className="house-prediction">
                        <div className="house-pred-header">
                          <span className="house-number">House {house}</span>
                          <span className={`house-tendency ${pred.tendency?.toLowerCase()}`}>{pred.tendency}</span>
                        </div>
                        <div className="house-pred-text">{pred.prediction}</div>
                        <div className="house-pred-factors">
                          <strong>Contributing Factors:</strong> {pred.factors?.join(', ')}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Advanced Classical Techniques */}
              <div className="analysis-section">
                <h3>Advanced Classical Techniques</h3>
                
                {/* Ashtakavarga */}
                {prediction.detailed_analysis?.ashtakavarga && (
                  <div className="analysis-step">
                    <h4>Ashtakavarga Analysis</h4>
                    <div className="step-content">
                      <div className="ashtakavarga-summary">
                        <span className="total-score">Total Score: {prediction.detailed_analysis.ashtakavarga.total_score}</span>
                        <span className="strongest-houses">
                          Strongest Houses: {prediction.detailed_analysis.ashtakavarga.strongest_houses?.join(', ')}
                        </span>
                      </div>
                      {prediction.detailed_analysis.ashtakavarga.house_scores && (
                        <div className="house-scores">
                          {Object.entries(prediction.detailed_analysis.ashtakavarga.house_scores).map(([house, score]) => (
                            <span key={house} className={`house-score ${score > 25 ? 'strong' : score < 20 ? 'weak' : 'average'}`}>
                              H{house}: {score}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Yogakaraka */}
                {prediction.detailed_analysis?.yogakaraka && (
                  <div className="analysis-step">
                    <h4>Yogakaraka Analysis</h4>
                    <div className="step-content">
                      {prediction.detailed_analysis.yogakaraka.primary_yogakaraka && (
                        <div className="yogakaraka-primary">
                          <span className="yk-planet">{prediction.detailed_analysis.yogakaraka.primary_yogakaraka.planet}</span>
                          <span className="yk-houses">Rules: {prediction.detailed_analysis.yogakaraka.primary_yogakaraka.houses?.join(', ')}</span>
                          <span className="yk-strength">Strength: {prediction.detailed_analysis.yogakaraka.primary_yogakaraka.strength}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Chara Karakas */}
                {prediction.detailed_analysis?.chara_karakas && (
                  <div className="analysis-step">
                    <h4>Chara Karaka System</h4>
                    <div className="step-content">
                      <div className="karaka-list">
                        {Object.entries(prediction.detailed_analysis.chara_karakas.chara_karakas || {}).map(([karaka, data]) => (
                          <div key={karaka} className="karaka-item">
                            <span className="karaka-name">{karaka}:</span>
                            <span className="karaka-planet">{data.planet}</span>
                            <span className="karaka-degree">({data.degree}°)</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Other Advanced Techniques */}
                <div className="analysis-step">
                  <h4>Additional Techniques Applied</h4>
                  <div className="step-content">
                    <div className="techniques-list">
                      {prediction.techniques_applied?.map(technique => (
                        <span key={technique} className="technique-tag">{technique}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Debug Information */}
              {prediction.debug_information && (
                <div className="analysis-section">
                  <h3>Calculation Debug Information</h3>
                  
                  <div className="analysis-step">
                    <h4>Execution Log</h4>
                    <div className="debug-info">
                      {prediction.debug_information.execution_log?.slice(-15).map((log, index) => (
                        <div key={index} className="debug-line">{log}</div>
                      ))}
                    </div>
                  </div>

                  {prediction.debug_information.core_debug && (
                    <div className="analysis-step">
                      <h4>Core Analysis Debug</h4>
                      <div className="debug-info">
                        {Array.isArray(prediction.debug_information.core_debug) ? 
                          prediction.debug_information.core_debug.slice(-10).map((debug, index) => (
                            <div key={index} className="debug-line">{debug}</div>
                          )) : 
                          <div className="debug-line">{JSON.stringify(prediction.debug_information.core_debug, null, 2)}</div>
                        }
                      </div>
                    </div>
                  )}

                  {prediction.debug_information.advanced_debug && (
                    <div className="analysis-step">
                      <h4>Advanced Techniques Debug</h4>
                      <div className="debug-info">
                        {Array.isArray(prediction.debug_information.advanced_debug) ? 
                          prediction.debug_information.advanced_debug.slice(-10).map((debug, index) => (
                            <div key={index} className="debug-line">{debug}</div>
                          )) : 
                          <div className="debug-line">{JSON.stringify(prediction.debug_information.advanced_debug, null, 2)}</div>
                        }
                      </div>
                    </div>
                  )}
                </div>
              )}

            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ClassicalPrediction;