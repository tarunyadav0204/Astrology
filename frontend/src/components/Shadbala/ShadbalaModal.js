import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { apiService } from '../../services/apiService';
import './ShadbalaModal.css';

const ShadbalaModal = ({ chartData, birthData, onClose }) => {
  const [shadbalaData, setShadbalaData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedPlanet, setExpandedPlanet] = useState(null);

  useEffect(() => {
    const fetchShadbala = async () => {
      try {
        setLoading(true);
        const response = await apiService.calculateShadbala(chartData, birthData);
        setShadbalaData(response);
      } catch (err) {
        setError(err.message || 'Failed to calculate Shadbala');
      } finally {
        setLoading(false);
      }
    };

    fetchShadbala();
  }, [chartData, birthData]);

  const getGradeColor = (grade) => {
    switch (grade) {
      case 'Excellent': return '#4caf50';
      case 'Good': return '#8bc34a';
      case 'Average': return '#ff9800';
      case 'Weak': return '#f44336';
      default: return '#666';
    }
  };

  const componentNames = {
    sthana_bala: 'Sthana Bala (Positional)',
    dig_bala: 'Dig Bala (Directional)',
    kala_bala: 'Kala Bala (Temporal)',
    chesta_bala: 'Chesta Bala (Motional)',
    naisargika_bala: 'Naisargika Bala (Natural)',
    drik_bala: 'Drik Bala (Aspectual)'
  };

  const modalContent = (
    <div className="shadbala-modal-overlay" onClick={onClose}>
      <div className="shadbala-modal-content" onClick={e => e.stopPropagation()}>
        <div className="shadbala-modal-header">
          <h2>Shadbala (Planetary Strength)</h2>
          <button className="shadbala-close-btn" onClick={onClose}>×</button>
        </div>

        <div className="shadbala-modal-body">
          {loading && (
            <div className="shadbala-loading">
              <div className="loading-spinner"></div>
              <p>Calculating planetary strengths...</p>
            </div>
          )}

          {error && (
            <div className="shadbala-error">
              <p>Error: {error}</p>
            </div>
          )}

          {shadbalaData && (
            <>
              {/* Summary Section */}
              <div className="shadbala-summary">
                <div className="summary-card">
                  <h3>Strongest Planet</h3>
                  <div className="planet-highlight">
                    <span className="planet-name">{shadbalaData.summary.strongest[0]}</span>
                    <span className="planet-strength">{shadbalaData.summary.strongest[1].total_rupas} Rupas</span>
                    <span 
                      className="planet-grade"
                      style={{ color: getGradeColor(shadbalaData.summary.strongest[1].grade) }}
                    >
                      {shadbalaData.summary.strongest[1].grade}
                    </span>
                  </div>
                </div>
                <div className="summary-card">
                  <h3>Weakest Planet</h3>
                  <div className="planet-highlight">
                    <span className="planet-name">{shadbalaData.summary.weakest[0]}</span>
                    <span className="planet-strength">{shadbalaData.summary.weakest[1].total_rupas} Rupas</span>
                    <span 
                      className="planet-grade"
                      style={{ color: getGradeColor(shadbalaData.summary.weakest[1].grade) }}
                    >
                      {shadbalaData.summary.weakest[1].grade}
                    </span>
                  </div>
                </div>
              </div>

              {/* Detailed Strength Table */}
              <div className="shadbala-table-container">
                <table className="shadbala-table">
                  <thead>
                    <tr>
                      <th>Planet</th>
                      <th>Total Rupas</th>
                      <th>Grade</th>
                      <th>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(shadbalaData.shadbala).map(([planet, data]) => (
                      <React.Fragment key={planet}>
                        <tr className="planet-row">
                          <td className="planet-cell" style={{ textAlign: 'left' }}>
                            <div style={{ textAlign: 'left', width: '100%' }}>{planet}</div>
                          </td>
                          <td className="strength-cell">
                            <span className="rupas-value">{data.total_rupas}</span>
                            <span className="points-value">({data.total_points} pts)</span>
                          </td>
                          <td className="grade-cell">
                            <span 
                              className="grade-badge"
                              style={{ 
                                backgroundColor: getGradeColor(data.grade),
                                color: 'white'
                              }}
                            >
                              {data.grade}
                            </span>
                          </td>
                          <td className="details-cell">
                            <button
                              className="expand-btn"
                              onClick={() => setExpandedPlanet(
                                expandedPlanet === planet ? null : planet
                              )}
                            >
                              {expandedPlanet === planet ? '−' : '+'}
                            </button>
                          </td>
                        </tr>
                        {expandedPlanet === planet && (
                          <tr className="expanded-row">
                            <td colSpan="4">
                              <div className="component-breakdown">
                                <h4>Six-fold Strength Breakdown</h4>
                                <div className="components-grid">
                                  {Object.entries(data.components).map(([component, value]) => (
                                    <div key={component} className="component-item">
                                      <span className="component-name">
                                        {componentNames[component]}
                                      </span>
                                      <span className="component-value">{value}</span>
                                    </div>
                                  ))}
                                </div>
                                
                                {/* Formula Explanations */}
                                {data.formulas && (
                                  <div className="formulas-section">
                                    <h4>Classical Formulas & Calculations</h4>
                                    {Object.entries(data.formulas).map(([formulaType, formulaData]) => (
                                      <div key={formulaType} className="formula-card">
                                        <h5>{formulaType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h5>
                                        {typeof formulaData === 'object' ? (
                                          <div className="formula-details">
                                            {formulaData.formula && (
                                              <div className="formula-item">
                                                <strong>Formula:</strong> <code>{formulaData.formula}</code>
                                              </div>
                                            )}
                                            {formulaData.explanation && (
                                              <div className="formula-item">
                                                <strong>Explanation:</strong> {formulaData.explanation}
                                              </div>
                                            )}
                                            {formulaData.calculation && (
                                              <div className="formula-item">
                                                <strong>Calculation:</strong> {formulaData.calculation}
                                              </div>
                                            )}
                                            {formulaData.components && (
                                              <div className="formula-components">
                                                <strong>Components:</strong>
                                                {Object.entries(formulaData.components).map(([comp, details]) => (
                                                  <div key={comp} className="sub-formula">
                                                    <h6>{comp.replace('_', ' ').toUpperCase()}</h6>
                                                    {typeof details === 'object' && details.formula && (
                                                      <div><strong>Formula:</strong> <code>{details.formula}</code></div>
                                                    )}
                                                    {typeof details === 'object' && details.explanation && (
                                                      <div><strong>Explanation:</strong> {details.explanation}</div>
                                                    )}
                                                  </div>
                                                ))}
                                              </div>
                                            )}
                                          </div>
                                        ) : (
                                          <div>{formulaData}</div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Strength Guide */}
              <div className="shadbala-guide">
                <h3>Strength Grades</h3>
                <div className="grade-guide">
                  <div className="grade-item">
                    <span className="grade-color" style={{ backgroundColor: '#4caf50' }}></span>
                    <span>Excellent (6+ Rupas): Very strong, gives excellent results</span>
                  </div>
                  <div className="grade-item">
                    <span className="grade-color" style={{ backgroundColor: '#8bc34a' }}></span>
                    <span>Good (4.5-6 Rupas): Strong, gives good results</span>
                  </div>
                  <div className="grade-item">
                    <span className="grade-color" style={{ backgroundColor: '#ff9800' }}></span>
                    <span>Average (3-4.5 Rupas): Moderate strength, mixed results</span>
                  </div>
                  <div className="grade-item">
                    <span className="grade-color" style={{ backgroundColor: '#f44336' }}></span>
                    <span>Weak (&lt;3 Rupas): Weak, may need remedies</span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

export default ShadbalaModal;