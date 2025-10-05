import React, { useState } from 'react';
import { useAstrology } from '../../context/AstrologyContext';
import { apiService } from '../../services/apiService';
import { PredictionsContainer, YearSelector, HouseGrid, HouseCard, MonthGrid, MonthCard, LoadingSpinner } from './PredictionsPage.styles';

const PredictionsPage = ({ onBack, currentView, setCurrentView }) => {
  const { birthData } = useAstrology();
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedHouse, setSelectedHouse] = useState(null);

  const generateYearOptions = () => {
    const currentYear = new Date().getFullYear();
    const years = [];
    for (let i = currentYear - 5; i <= currentYear + 10; i++) {
      years.push(i);
    }
    return years;
  };

  const fetchPredictions = async (year) => {
    if (!birthData) return;
    
    setLoading(true);
    try {
      const response = await apiService.predictYearEvents({
        birth_data: birthData,
        year: year
      });
      setPredictions(response);
    } catch (error) {
      console.error('Error fetching predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleYearChange = (year) => {
    setSelectedYear(year);
    setSelectedHouse(null);
    fetchPredictions(year);
  };

  const getProbabilityColor = (probability) => {
    switch (probability) {
      case 'High': return '#4CAF50';
      case 'Medium': return '#FF9800';
      case 'Low': return '#2196F3';
      case 'Very Low': return '#9E9E9E';
      default: return '#9E9E9E';
    }
  };

  const getStrengthColor = (strength) => {
    if (strength >= 75) return '#4CAF50';
    if (strength >= 60) return '#8BC34A';
    if (strength >= 45) return '#FF9800';
    return '#F44336';
  };

  if (!birthData) {
    return (
      <div>
        <PredictionsContainer>
          <h2>Please enter birth details first</h2>
        </PredictionsContainer>
      </div>
    );
  }

  return (
    <div>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.5rem 1.5rem',
        background: 'linear-gradient(135deg, #e91e63 0%, #ff6f00 100%)',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        margin: '0 0 0.5rem 0',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        height: '50px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button 
            onClick={onBack}
            style={{
              padding: '1rem 2rem',
              background: 'linear-gradient(135deg, #ff8a65 0%, #e91e63 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '50px',
              cursor: 'pointer',
              fontSize: '1rem',
              fontWeight: '700'
            }}
          >
            🏠 Back
          </button>
          <button 
            onClick={() => setCurrentView('dashboard')}
            style={{ 
              padding: '0.5rem 1rem',
              background: currentView === 'dashboard' ? 'rgba(255,255,255,0.3)' : 'transparent',
              color: 'white',
              border: '2px solid rgba(255,255,255,0.5)',
              borderRadius: '25px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            📊 Dashboard
          </button>
          <button 
            onClick={() => setCurrentView('predictions')}
            style={{ 
              padding: '0.5rem 1rem',
              background: currentView === 'predictions' ? 'rgba(255,255,255,0.3)' : 'transparent',
              color: 'white',
              border: '2px solid rgba(255,255,255,0.5)',
              borderRadius: '25px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            🔮 Predictions
          </button>
        </div>
        <h1 style={{
          margin: 0,
          color: 'white',
          fontSize: '1.5rem',
          fontWeight: '700',
          letterSpacing: '1px'
        }}>
          ✨ {birthData?.name} - Yearly Predictions
        </h1>
      </div>
      <PredictionsContainer>
        <h2>Yearly Predictions</h2>
      
      <YearSelector>
        <label>Select Year:</label>
        <select 
          value={selectedYear} 
          onChange={(e) => handleYearChange(parseInt(e.target.value))}
        >
          {generateYearOptions().map(year => (
            <option key={year} value={year}>{year}</option>
          ))}
        </select>
      </YearSelector>

      {loading && <LoadingSpinner>Loading predictions...</LoadingSpinner>}

      {predictions && !selectedHouse && (
        <div>
          <h3>Houses Overview for {selectedYear}</h3>
          <HouseGrid>
            {Object.entries(predictions.predictions).map(([houseKey, houseData]) => {
              const houseNum = parseInt(houseKey.split('_')[1]);
              const avgStrength = houseData.monthly_predictions.reduce((sum, month) => sum + month.strength, 0) / 12;
              
              return (
                <HouseCard 
                  key={houseKey}
                  onClick={() => setSelectedHouse(houseData)}
                  strength={avgStrength}
                >
                  <h4>House {houseNum}</h4>
                  <p>{houseData.house_info.name}</p>
                  <div className="strength-bar">
                    <div 
                      className="strength-fill"
                      style={{ 
                        width: `${avgStrength}%`,
                        backgroundColor: getStrengthColor(avgStrength)
                      }}
                    />
                  </div>
                  <span className="strength-text">{avgStrength.toFixed(1)}%</span>
                </HouseCard>
              );
            })}
          </HouseGrid>
        </div>
      )}

      {selectedHouse && (
        <div>
          <button onClick={() => setSelectedHouse(null)}>← Back to Houses</button>
          <h3>{selectedHouse.house_info.name} - Monthly Predictions {selectedYear}</h3>
          <p><strong>House Lord:</strong> {selectedHouse.house_info.lord}</p>
          <p><strong>Significations:</strong> {selectedHouse.house_info.significations.join(', ')}</p>
          
          {selectedHouse.calculation_methodology && (
            <details style={{ margin: '15px 0', padding: '10px', background: '#f8f9fa', borderRadius: '8px' }}>
              <summary style={{ cursor: 'pointer', fontWeight: '600', color: '#2c3e50' }}>🔬 Calculation Methodology</summary>
              <div style={{ padding: '10px 0', fontSize: '14px', lineHeight: '1.5' }}>
                <div><strong>Algorithm:</strong> {selectedHouse.calculation_methodology.algorithm_version}</div>
                <div style={{ margin: '8px 0' }}><strong>Strength Formula:</strong> {selectedHouse.calculation_methodology.strength_formula}</div>
                <div><strong>Factors Considered:</strong></div>
                <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                  {selectedHouse.calculation_methodology.factors_considered.map((factor, idx) => (
                    <li key={idx}>{factor}</li>
                  ))}
                </ul>
                <div><strong>Probability Ranges:</strong></div>
                <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                  {Object.entries(selectedHouse.calculation_methodology.probability_thresholds).map(([level, range]) => (
                    <li key={level}><strong>{level}:</strong> {range}</li>
                  ))}
                </ul>
              </div>
            </details>
          )}
          
          <MonthGrid>
            {selectedHouse.monthly_predictions.map((month) => (
              <MonthCard 
                key={month.month}
                probability={month.probability}
              >
                <h4>{month.month_name}</h4>
                <div className="probability-badge" style={{ backgroundColor: getProbabilityColor(month.probability) }}>
                  {month.probability}
                </div>
                <div className="strength">Strength: {month.strength}%</div>
                
                {month.active_dasha && (
                  <div className="dasha-info">
                    <strong>Dasha:</strong> {month.active_dasha}
                  </div>
                )}
                
                {month.transit_count > 0 && (
                  <div className="transit-info">
                    <strong>Transits:</strong> {month.transit_count}
                  </div>
                )}
                
                <div className="events">
                  <strong>Likely Events:</strong>
                  <ul>
                    {month.events.map((event, idx) => (
                      <li key={idx}>{event.replace(/_/g, ' ')}</li>
                    ))}
                  </ul>
                </div>
                
                <div className="description">
                  {month.description}
                </div>
                
                {month.comprehensive_analysis && (
                  <details style={{ marginTop: '10px', fontSize: '12px', color: '#2c3e50', border: '1px solid #ecf0f1', borderRadius: '6px', padding: '8px' }}>
                    <summary style={{ cursor: 'pointer', fontWeight: '600', color: '#e74c3c' }}>🔮 Comprehensive Analysis</summary>
                    <div style={{ padding: '10px 0', lineHeight: '1.6' }}>
                      
                      <div style={{ marginBottom: '10px' }}>
                        <strong style={{ color: '#2980b9' }}>All 5 Dashas:</strong>
                        <div style={{ marginLeft: '10px', color: '#7f8c8d', fontSize: '11px' }}>
                          Maha: {month.comprehensive_analysis.dasha_info?.maha || 'N/A'}, 
                          Antar: {month.comprehensive_analysis.dasha_info?.antar || 'N/A'}, 
                          Pratyantar: {month.comprehensive_analysis.dasha_info?.pratyantar || 'N/A'}, 
                          Sookshma: {month.comprehensive_analysis.dasha_info?.sookshma || 'N/A'}, 
                          Prana: {month.comprehensive_analysis.dasha_info?.prana || 'N/A'}
                        </div>
                        
                        <strong style={{ color: '#2980b9' }}>Activated Planets:</strong>
                        <div style={{ marginLeft: '10px', color: '#7f8c8d' }}>
                          {month.comprehensive_analysis.activated_planets?.join(', ') || 'None'}
                        </div>
                      </div>
                      
                      <div style={{ marginBottom: '10px' }}>
                        <strong style={{ color: '#2980b9' }}>Activated Houses:</strong>
                        <div style={{ marginLeft: '10px', color: '#7f8c8d' }}>
                          {month.comprehensive_analysis.activated_houses?.join(', ') || 'None'}
                        </div>
                      </div>
                      
                      <div style={{ marginBottom: '10px' }}>
                        <strong style={{ color: '#2980b9' }}>Solar Activation:</strong>
                        <div style={{ marginLeft: '10px', color: month.comprehensive_analysis.solar_activation?.active ? '#27ae60' : '#e74c3c', fontSize: '11px' }}>
                          {month.comprehensive_analysis.solar_activation?.description || 'No solar activation'}
                        </div>
                      </div>
                      
                      <div style={{ marginBottom: '10px' }}>
                        <strong style={{ color: '#2980b9' }}>Specific Results:</strong>
                        {month.comprehensive_analysis.detailed_results?.map((result, idx) => (
                          <div key={idx} style={{ 
                            marginLeft: '10px', 
                            color: result.includes('problem') || result.includes('concern') || result.includes('issue') ? '#e74c3c' : '#27ae60',
                            fontSize: '11px'
                          }}>
                            • {result}
                          </div>
                        )) || <div style={{ marginLeft: '10px', color: '#7f8c8d', fontSize: '11px' }}>No specific results</div>}
                      </div>
                      
                      <div style={{ marginBottom: '10px' }}>
                        <strong style={{ color: '#2980b9' }}>Analysis:</strong>
                        <div style={{ 
                          marginLeft: '10px', 
                          color: month.comprehensive_analysis.explanation?.includes('Positive') ? '#27ae60' : '#e74c3c',
                          fontWeight: '600',
                          fontSize: '11px'
                        }}>
                          {month.comprehensive_analysis.explanation || 'Standard analysis'}
                        </div>
                      </div>
                      
                      <details style={{ marginTop: '8px' }}>
                        <summary style={{ cursor: 'pointer', fontSize: '11px', color: '#95a5a6' }}>Mathematical Calculation</summary>
                        <div style={{ padding: '5px 0', fontSize: '10px', color: '#7f8c8d' }}>
                          <div><strong>Formula:</strong> {month.calculation_details.final_calculation}</div>
                          <div><strong>Factors:</strong> {JSON.stringify(month.calculation_details.astrological_factors.breakdown)}</div>
                        </div>
                      </details>
                      
                    </div>
                  </details>
                )}
              </MonthCard>
            ))}
          </MonthGrid>
        </div>
      )}
      </PredictionsContainer>
    </div>
  );
};

export default PredictionsPage;