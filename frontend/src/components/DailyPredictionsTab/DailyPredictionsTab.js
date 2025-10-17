import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/apiService';
import ClassicalPrediction from '../ClassicalPrediction/ClassicalPrediction';

const DailyPredictionsTab = ({ chartData, birthData }) => {
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [isPremium] = useState(true); // Set to true for testing phase
  const [showDebugger, setShowDebugger] = useState(false);

  useEffect(() => {
    if (birthData) {
      fetchDailyPredictions();
    }
  }, [birthData, selectedDate]);

  const fetchDailyPredictions = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.getDailyPredictions({
        birth_data: birthData,
        target_date: selectedDate
      });
      setPredictions(response);
    } catch (err) {
      console.error('Failed to fetch daily predictions:', err);
      setError('Failed to load predictions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return '#4caf50';
    if (confidence >= 60) return '#ff9800';
    return '#f44336';
  };

  const isMobile = window.innerWidth <= 768;

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '60vh',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        <div style={{ 
          width: '40px', 
          height: '40px', 
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #e91e63',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
        <p style={{ color: '#666', fontSize: '16px' }}>Loading your daily guidance...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '2rem',
        color: '#f44336',
        backgroundColor: '#ffebee',
        borderRadius: '8px',
        margin: '1rem'
      }}>
        <h3>⚠️ Error</h3>
        <p>{error}</p>
        <button 
          onClick={fetchDailyPredictions}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#e91e63',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            marginTop: '1rem'
          }}
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: '1rem', maxHeight: '80vh', overflowY: 'auto' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        flexDirection: isMobile ? 'column' : 'row',
        justifyContent: 'space-between', 
        alignItems: isMobile ? 'stretch' : 'center',
        marginBottom: '1.5rem',
        gap: '1rem'
      }}>
        <h3 style={{ 
          color: '#e91e63', 
          fontSize: '1.4rem', 
          margin: 0,
          textAlign: isMobile ? 'center' : 'left'
        }}>
          🌟 Daily Guidance
        </h3>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <label style={{ fontSize: '14px', fontWeight: '600', color: '#666' }}>Date:</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            style={{
              padding: '0.5rem',
              border: '2px solid #e91e63',
              borderRadius: '6px',
              fontSize: '14px'
            }}
          />
          {predictions?.classical_prediction && (
            <button
              onClick={() => {
                console.log('Classical Prediction Data:', predictions.classical_prediction);
                setShowDebugger(true);
              }}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#667eea',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '12px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
🔮 Classical Prediction
            </button>
          )}
        </div>
      </div>

      {predictions && (
        <>
          {/* Date Display */}
          <div style={{
            backgroundColor: '#f8f9fa',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            textAlign: 'center'
          }}>
            <h4 style={{ color: '#e91e63', margin: '0 0 0.5rem 0' }}>
              {formatDate(predictions.date)}
            </h4>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              gap: '1rem',
              flexWrap: 'wrap'
            }}>
              <div style={{ fontSize: '14px', color: '#666' }}>
                <strong>Overall Confidence:</strong> 
                <span style={{ 
                  color: getConfidenceColor(predictions.total_confidence),
                  fontWeight: 'bold',
                  marginLeft: '0.5rem'
                }}>
                  {predictions.total_confidence}%
                </span>
              </div>
              {predictions.current_state?.maha_dasha && (
                <div style={{ fontSize: '14px', color: '#666' }}>
                  <strong>Current Dasha:</strong> {predictions.current_state.maha_dasha}
                </div>
              )}
              {predictions.current_state?.moon_nakshatra && (
                <div style={{ fontSize: '14px', color: '#666' }}>
                  <strong>Moon:</strong> {predictions.current_state.moon_nakshatra}
                </div>
              )}
            </div>
          </div>

          {/* Predictions */}
          {predictions.predictions && predictions.predictions.length > 0 ? (
            <div style={{ display: 'grid', gap: '1rem' }}>
              {predictions.predictions.map((prediction, index) => (
                <div key={prediction.rule_id} style={{
                  backgroundColor: 'white',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  borderLeft: `4px solid ${getConfidenceColor(prediction.confidence)}`
                }}>
                  {/* Prediction Header */}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: '1rem'
                  }}>
                    <div style={{
                      backgroundColor: getConfidenceColor(prediction.confidence),
                      color: 'white',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '15px',
                      fontSize: '12px',
                      fontWeight: 'bold'
                    }}>
                      {prediction.confidence}% Confidence
                    </div>
                    <div style={{ fontSize: '12px', color: '#666', textTransform: 'capitalize' }}>
                      {prediction.rule_type.replace('_', ' ')}
                    </div>
                  </div>

                  {/* Main Prediction */}
                  <div style={{ marginBottom: '1rem' }}>
                    <p style={{ 
                      fontSize: '16px', 
                      lineHeight: '24px', 
                      color: '#333',
                      margin: 0
                    }}>
                      {prediction.prediction}
                    </p>
                  </div>

                  {/* Additional Details */}
                  {(
                    <div style={{ 
                      display: 'grid', 
                      gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(200px, 1fr))',
                      gap: '1rem',
                      marginTop: '1rem',
                      paddingTop: '1rem',
                      borderTop: '1px solid #eee'
                    }}>
                      {prediction.life_areas && prediction.life_areas.length > 0 && (
                        <div>
                          <h5 style={{ color: '#e91e63', margin: '0 0 0.5rem 0', fontSize: '14px' }}>
                            🎯 Focus Areas
                          </h5>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                            {prediction.life_areas.map((area, i) => (
                              <span key={i} style={{
                                backgroundColor: '#e3f2fd',
                                color: '#1976d2',
                                padding: '0.25rem 0.5rem',
                                borderRadius: '12px',
                                fontSize: '12px',
                                textTransform: 'capitalize'
                              }}>
                                {area}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {prediction.timing_advice && (
                        <div>
                          <h5 style={{ color: '#e91e63', margin: '0 0 0.5rem 0', fontSize: '14px' }}>
                            ⏰ Best Timing
                          </h5>
                          <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
                            {prediction.timing_advice}
                          </p>
                        </div>
                      )}

                      {prediction.colors && prediction.colors.length > 0 && (
                        <div>
                          <h5 style={{ color: '#e91e63', margin: '0 0 0.5rem 0', fontSize: '14px' }}>
                            🌈 Lucky Colors
                          </h5>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            {prediction.colors.map((color, i) => (
                              <div key={i} style={{
                                width: '20px',
                                height: '20px',
                                backgroundColor: color,
                                borderRadius: '50%',
                                border: '2px solid #ddd',
                                title: color
                              }}></div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: '3rem',
              backgroundColor: '#f8f9fa',
              borderRadius: '8px',
              color: '#666'
            }}>
              <h4>No specific predictions for this date</h4>
              <p>Try selecting a different date or check back later as we add more prediction rules.</p>
            </div>
          )}
        </>
      )}

      {/* Classical Prediction */}
      {showDebugger && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            maxWidth: '90vw',
            maxHeight: '90vh',
            overflow: 'auto',
            position: 'relative'
          }}>
            <button
              onClick={() => setShowDebugger(false)}
              style={{
                position: 'absolute',
                top: '10px',
                right: '10px',
                background: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '50%',
                width: '30px',
                height: '30px',
                cursor: 'pointer',
                zIndex: 1001
              }}
            >
              ×
            </button>
            <ClassicalPrediction birthData={birthData} />
          </div>
        </div>
      )}

      {/* CSS for loading animation */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default DailyPredictionsTab;