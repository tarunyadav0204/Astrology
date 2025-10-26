import React from 'react';

const SuitableFields = ({ data, loading }) => {
  if (loading) {
    return <div className="analysis-loading">Analyzing Suitable Career Fields...</div>;
  }

  if (!data) {
    return <div className="analysis-error">Unable to load suitable fields analysis</div>;
  }

  return (
    <div className="suitable-fields">
      <h3>💼 Suitable Career Fields</h3>
      
      {data.primary_fields && (
        <div className="fields-section">
          <h4>🎯 Primary Recommendations</h4>
          <div className="fields-grid">
            {data.primary_fields.map((field, index) => (
              <div key={index} className="field-card primary">
                <div className="field-header">
                  <h5>{field.name}</h5>
                  <span className="compatibility-score">{field.compatibility}%</span>
                </div>
                <div className="field-details">
                  <p className="field-description">{field.description}</p>
                  <div className="supporting-factors">
                    <strong>Supporting Factors:</strong>
                    <ul>
                      {field.supporting_factors?.map((factor, idx) => (
                        <li key={idx}>{factor}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.secondary_fields && (
        <div className="fields-section">
          <h4>⭐ Secondary Options</h4>
          <div className="fields-grid">
            {data.secondary_fields.map((field, index) => (
              <div key={index} className="field-card secondary">
                <div className="field-header">
                  <h5>{field.name}</h5>
                  <span className="compatibility-score">{field.compatibility}%</span>
                </div>
                <div className="field-details">
                  <p className="field-description">{field.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.business_vs_job && (
        <div className="work-type-analysis">
          <h4>🏢 Business vs Job Suitability</h4>
          <div className="work-type-grid">
            <div className="work-type-card">
              <h5>Business/Entrepreneurship</h5>
              <div className="suitability-meter">
                <div 
                  className="meter-fill business" 
                  style={{ width: `${data.business_vs_job.business_score}%` }}
                ></div>
                <span className="score">{data.business_vs_job.business_score}%</span>
              </div>
              <p>{data.business_vs_job.business_analysis}</p>
            </div>
            
            <div className="work-type-card">
              <h5>Job/Service</h5>
              <div className="suitability-meter">
                <div 
                  className="meter-fill job" 
                  style={{ width: `${data.business_vs_job.job_score}%` }}
                ></div>
                <span className="score">{data.business_vs_job.job_score}%</span>
              </div>
              <p>{data.business_vs_job.job_analysis}</p>
            </div>
          </div>
        </div>
      )}

      {data.foreign_opportunities && (
        <div className="foreign-opportunities">
          <h4>🌍 Foreign Career Opportunities</h4>
          <div className="opportunity-card">
            <div className="opportunity-score">
              <span className="score-value">{data.foreign_opportunities.score}%</span>
              <span className="score-label">Likelihood</span>
            </div>
            <div className="opportunity-details">
              <p>{data.foreign_opportunities.analysis}</p>
              {data.foreign_opportunities.favorable_directions && (
                <div className="favorable-directions">
                  <strong>Favorable Directions:</strong>
                  <div className="directions-list">
                    {data.foreign_opportunities.favorable_directions.map((direction, idx) => (
                      <span key={idx} className="direction-tag">{direction}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SuitableFields;