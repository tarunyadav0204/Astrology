import React from 'react';
import { KP_CONFIG } from '../../../config/kpConfig';
import kpService from '../../../services/kpService';
import './SubLordTable.css';

const SubLordTable = ({ subLords, birthData, compact }) => {
  if (!subLords || !subLords.planets) {
    return <div className="sublord-error">Sub-lord data not available</div>;
  }

  return (
    <div className={`sublord-table-container ${compact ? 'compact' : ''}`}>
      <div className="sublord-header">
        <h3>Sub-Lord Table</h3>
        <div className="table-info">
          <span>Stellar positions with sub-lords</span>
        </div>
      </div>
      
      <div className="sublord-table">
        <div className="table-header">
          <div className="col-planet">Planet</div>
          <div className="col-degree">Degree</div>
          <div className="col-sign">Sign Lord</div>
          <div className="col-nakshatra">Nakshatra Lord</div>
          <div className="col-sublord">Sub Lord</div>
          <div className="col-subsublord">Sub Sub Lord</div>
        </div>
        
        <div className="table-body">
          {subLords.planets.map(planet => {
            const nakshatraInfo = kpService.getNakshatraFromDegree(planet.longitude);
            const signLord = kpService.getSignLord(planet.longitude);
            
            return (
              <div key={planet.name} className="table-row">
                <div className="col-planet">
                  <span className="planet-symbol">{planet.symbol}</span>
                  <span className="planet-name">{planet.name}</span>
                </div>
                <div className="col-degree">
                  {kpService.formatDegree(planet.longitude)}
                </div>
                <div className="col-sign">
                  {signLord}
                </div>
                <div className="col-nakshatra">
                  {nakshatraInfo.lord}
                </div>
                <div className="col-sublord">
                  <span 
                    className="sublord-name"
                    style={{ color: KP_CONFIG.COLORS.SUB_LORD }}
                  >
                    {planet.sub_lord}
                  </span>
                </div>
                <div className="col-subsublord">
                  <span 
                    className="subsublord-name"
                    style={{ color: KP_CONFIG.COLORS.SUB_LORD }}
                  >
                    {planet.sub_sub_lord || 'N/A'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {!compact && (
        <div className="sublord-cusps">
          <h4>House Cusps</h4>
          <div className="cusps-grid">
            {subLords.cusps && subLords.cusps.map(cusp => (
              <div key={cusp.house} className="cusp-item">
                <span className="cusp-house">H{cusp.house}</span>
                <span className="cusp-degree">{kpService.formatDegree(cusp.longitude)}</span>
                <span className="cusp-sublord" style={{ color: KP_CONFIG.COLORS.SUB_LORD }}>
                  {cusp.sub_lord}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SubLordTable;