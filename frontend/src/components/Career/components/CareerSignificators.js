import React from 'react';
import { CAREER_CONFIG } from '../../../config/career.config';

const CareerSignificators = ({ data, loading }) => {
  if (loading) {
    return <div className="analysis-loading">Analyzing Career Significators...</div>;
  }

  if (!data) {
    return <div className="analysis-error">Unable to load career significators</div>;
  }

  return (
    <div className="career-significators">
      <h3>🌟 Career Significator Planets</h3>
      
      <div className="significators-grid">
        {data.significators && data.significators.map((planet, index) => (
          <div key={index} className="significator-card">
            <div className="planet-header">
              <h4>{planet.name}</h4>
              <span className={`strength-badge strength-${planet.strength?.toLowerCase()}`}>
                {planet.strength}
              </span>
            </div>
            
            <div className="planet-details">
              <div className="detail-row">
                <span className="label">Position:</span>
                <span className="value">{planetary_signs && planetary_signs[planet.name] ? `${planetary_signs[planet.name].sign} (${planet.house}th House)` : `${planet.sign} (${planet.house}th House)`}</span>
              </div>
              <div className="detail-row">
                <span className="label">Degree:</span>
                <span className="value">{planet.degree}°</span>
              </div>
              {planet.retrograde && (
                <div className="detail-row">
                  <span className="retrograde-indicator">Retrograde</span>
                </div>
              )}
            </div>

            <div className="career-fields">
              <h5>Suitable Fields:</h5>
              <div className="fields-list">
                {CAREER_CONFIG.significators[planet.name]?.fields.map((field, idx) => (
                  <span key={idx} className="field-tag">{field}</span>
                ))}
              </div>
            </div>

            <div className="planet-interpretation">
              <p>{planet.interpretation}</p>
            </div>
          </div>
        ))}
      </div>

      {data.dominant_significator && (
        <div className="dominant-significator">
          <h4>🎯 Dominant Career Significator</h4>
          <div className="dominant-card">
            <h5>{data.dominant_significator.name}</h5>
            <p>{data.dominant_significator.reason}</p>
            <div className="recommended-fields">
              <strong>Primary Career Recommendations:</strong>
              <div className="fields-list">
                {data.dominant_significator.recommended_fields?.map((field, idx) => (
                  <span key={idx} className="field-tag primary">{field}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CareerSignificators;