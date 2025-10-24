import React, { useState, useEffect } from 'react';
import { KP_CONFIG } from '../../../config/kpConfig';
import kpService from '../../../services/kpService';
import './RulingPlanets.css';

const RulingPlanets = ({ birthData, questionTime = null }) => {
  const [rulingPlanets, setRulingPlanets] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRulingPlanets();
  }, [birthData, questionTime]);

  const fetchRulingPlanets = async () => {
    try {
      setLoading(true);
      const data = await kpService.calculateRulingPlanets(birthData, questionTime);
      setRulingPlanets(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="ruling-loading">Loading ruling planets...</div>;
  }

  if (error) {
    return <div className="ruling-error">Error: {error}</div>;
  }

  if (!rulingPlanets) {
    return <div className="ruling-error">No ruling planets data</div>;
  }

  return (
    <div className="ruling-planets-container">
      <div className="ruling-header">
        <h3>Ruling Planets</h3>
        <div className="ruling-info">
          {questionTime ? 'For Horary Question' : 'At Birth Time'}
        </div>
      </div>
      
      <div className="ruling-grid">
        <div className="ruling-item">
          <div className="ruling-label">Ascendant Sub-Lord</div>
          <div 
            className="ruling-planet"
            style={{ color: KP_CONFIG.COLORS.RULING_PLANET }}
          >
            {rulingPlanets.ascendant_sub_lord}
          </div>
        </div>
        
        <div className="ruling-item">
          <div className="ruling-label">Moon Sign Sub-Lord</div>
          <div 
            className="ruling-planet"
            style={{ color: KP_CONFIG.COLORS.RULING_PLANET }}
          >
            {rulingPlanets.moon_sign_sub_lord}
          </div>
        </div>
        
        <div className="ruling-item">
          <div className="ruling-label">Moon Star Sub-Lord</div>
          <div 
            className="ruling-planet"
            style={{ color: KP_CONFIG.COLORS.RULING_PLANET }}
          >
            {rulingPlanets.moon_star_sub_lord}
          </div>
        </div>
        
        <div className="ruling-item">
          <div className="ruling-label">Day Lord</div>
          <div 
            className="ruling-planet"
            style={{ color: KP_CONFIG.COLORS.RULING_PLANET }}
          >
            {rulingPlanets.day_lord}
          </div>
        </div>
      </div>
      
      {rulingPlanets.combined_ruling && (
        <div className="combined-ruling">
          <h4>Combined Ruling Planets</h4>
          <div className="combined-list">
            {rulingPlanets.combined_ruling.map((planet, index) => (
              <span 
                key={index} 
                className="combined-planet"
                style={{ color: KP_CONFIG.COLORS.RULING_PLANET }}
              >
                {planet}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RulingPlanets;