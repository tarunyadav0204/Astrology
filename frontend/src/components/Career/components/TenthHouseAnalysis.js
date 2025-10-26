import React from 'react';

const TenthHouseAnalysis = ({ data, loading }) => {
  if (loading) {
    return <div className="analysis-loading">Analyzing 10th House...</div>;
  }

  if (!data) {
    return <div className="analysis-error">Unable to load 10th House analysis</div>;
  }

  return (
    <div className="tenth-house-analysis">
      <h3>🏢 10th House Analysis</h3>
      
      <div className="house-details">
        <div className="detail-item">
          <span className="label">House Sign:</span>
          <span className="value">{data.house_sign}</span>
        </div>
        <div className="detail-item">
          <span className="label">House Lord:</span>
          <span className="value">{data.house_lord}</span>
        </div>
        <div className="detail-item">
          <span className="label">Strength:</span>
          <span className={`value strength-${data.strength?.toLowerCase()}`}>
            {data.strength}
          </span>
        </div>
      </div>

      {data.planets_in_house && data.planets_in_house.length > 0 && (
        <div className="planets-section">
          <h4>Planets in 10th House</h4>
          <div className="planets-list">
            {data.planets_in_house.map((planet, index) => (
              <div key={index} className="planet-item">
                <span className="planet-name">{planet.name}</span>
                <span className="planet-effect">{planet.effect}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.aspects && data.aspects.length > 0 && (
        <div className="aspects-section">
          <h4>Aspects to 10th House</h4>
          <div className="aspects-list">
            {data.aspects.map((aspect, index) => (
              <div key={index} className="aspect-item">
                <span className="aspect-planet">{aspect.planet}</span>
                <span className="aspect-type">{aspect.type}</span>
                <span className="aspect-effect">{aspect.effect}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="interpretation">
        <h4>Career Implications</h4>
        <p>{data.interpretation}</p>
      </div>
    </div>
  );
};

export default TenthHouseAnalysis;