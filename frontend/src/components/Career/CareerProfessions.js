import React from 'react';

const CareerProfessions = ({ careerData }) => {
  if (!careerData?.suitable_professions) return <div>Loading professions...</div>;
  
  const professions = careerData.suitable_professions;
  
  return (
    <div className="suitable-professions">
      <h3>💼 Recommended Career Fields</h3>
      
      <div className="soul-calling">
        <h4>🎯 Your Soul's Career Calling</h4>
        <p>{professions.soul_calling}</p>
      </div>
      
      <div className="primary-recommendations">
        <h4>🏆 Top Recommendations</h4>
        {professions.primary_recommendations.map((rec, index) => (
          <div key={index} className="profession-rec">
            <div className="rec-header">
              <span className="rank">#{rec.rank}</span>
              <strong>{rec.planet}</strong>
              <span className="strength">{rec.strength_score} strength</span>
            </div>
            <p>{rec.profession_category}</p>
            <span className="suitability">{rec.suitability} suitability</span>
          </div>
        ))}
      </div>
      
      <div className="detailed-fields">
        <h4>📋 Specific Career Options</h4>
        {professions.detailed_fields.map((field, index) => (
          <div key={index} className="field-category">
            <h5>{field.planet} Fields (Strength: {field.strength_score})</h5>
            <div className="field-list">
              {field.specific_fields.map((profession, idx) => (
                <span key={idx} className="profession-tag">{profession}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CareerProfessions;