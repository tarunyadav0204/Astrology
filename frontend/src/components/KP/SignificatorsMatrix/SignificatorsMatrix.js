import React from 'react';
import { KP_CONFIG } from '../../../config/kpConfig';
import './SignificatorsMatrix.css';

const SignificatorsMatrix = ({ significators, compact = false }) => {
  if (!significators) {
    return <div className="significators-error">Significators data not available</div>;
  }
  
  // Handle different data structures
  let housesData = [];
  if (significators.houses) {
    housesData = significators.houses;
  } else if (typeof significators === 'object') {
    // Convert object format {1: [...], 2: [...]} to array format
    housesData = Object.keys(significators).map(houseNum => ({
      number: parseInt(houseNum),
      significators: significators[houseNum] || []
    }));
  }
  
  if (housesData.length === 0) {
    return <div className="significators-error">No significators data available</div>;
  }

  const getSignificatorTypeColor = (type) => {
    switch (type) {
      case KP_CONFIG.SIGNIFICATOR_TYPES.OWNER:
        return '#e91e63';
      case KP_CONFIG.SIGNIFICATOR_TYPES.OCCUPANT:
        return '#2196f3';
      case KP_CONFIG.SIGNIFICATOR_TYPES.ASPECT:
        return '#4caf50';
      case KP_CONFIG.SIGNIFICATOR_TYPES.SUB_LORD:
        return '#ff9800';
      default:
        return '#666';
    }
  };

  const getSignificatorTypeLabel = (type) => {
    switch (type) {
      case KP_CONFIG.SIGNIFICATOR_TYPES.OWNER:
        return 'O';
      case KP_CONFIG.SIGNIFICATOR_TYPES.OCCUPANT:
        return 'Oc';
      case KP_CONFIG.SIGNIFICATOR_TYPES.ASPECT:
        return 'A';
      case KP_CONFIG.SIGNIFICATOR_TYPES.SUB_LORD:
        return 'SL';
      default:
        return type;
    }
  };

  return (
    <div className={`significators-container ${compact ? 'compact' : ''}`}>
      <div className="significators-header">
        <h3>Significators Matrix</h3>
        <div className="matrix-info">
          Planets connected to each house
        </div>
      </div>
      
      <div className="significators-matrix">
        {housesData.map(house => (
          <div key={house.number} className="house-significators">
            <div className="house-label">
              House {house.number}
            </div>
            <div className="significators-list">
              {house.significators && house.significators.length > 0 ? (
                house.significators.map((sig, index) => {
                  // Handle both string and object formats
                  const planetName = typeof sig === 'string' ? sig.split(' (')[0] : (sig.planet || sig);
                  const sigType = typeof sig === 'string' ? 'SUB_LORD' : (sig.type || 'SUB_LORD');
                  
                  return (
                    <div key={index} className="significator-item">
                      <span className="planet-name">{planetName}</span>
                      <span 
                        className="significator-type"
                        style={{ 
                          color: getSignificatorTypeColor(sigType),
                          backgroundColor: `${getSignificatorTypeColor(sigType)}20`
                        }}
                      >
                        {getSignificatorTypeLabel(sigType)}
                      </span>
                    </div>
                  );
                })
              ) : (
                <span className="no-significators">No significators</span>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="significators-legend">
        <div className="legend-title">Legend:</div>
        <div className="legend-items">
          <div className="legend-item">
            <span 
              className="legend-color" 
              style={{ backgroundColor: getSignificatorTypeColor(KP_CONFIG.SIGNIFICATOR_TYPES.OWNER) }}
            ></span>
            <span>Owner (O)</span>
          </div>
          <div className="legend-item">
            <span 
              className="legend-color" 
              style={{ backgroundColor: getSignificatorTypeColor(KP_CONFIG.SIGNIFICATOR_TYPES.OCCUPANT) }}
            ></span>
            <span>Occupant (Oc)</span>
          </div>
          <div className="legend-item">
            <span 
              className="legend-color" 
              style={{ backgroundColor: getSignificatorTypeColor(KP_CONFIG.SIGNIFICATOR_TYPES.ASPECT) }}
            ></span>
            <span>Aspect (A)</span>
          </div>
          <div className="legend-item">
            <span 
              className="legend-color" 
              style={{ backgroundColor: getSignificatorTypeColor(KP_CONFIG.SIGNIFICATOR_TYPES.SUB_LORD) }}
            ></span>
            <span>Sub-Lord (SL)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignificatorsMatrix;