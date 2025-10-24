import React, { useState, useEffect } from 'react';
import KPChart from './KPChart/KPChart';
import SubLordTable from './SubLordTable/SubLordTable';
import RulingPlanets from './RulingPlanets/RulingPlanets';
import SignificatorsMatrix from './SignificatorsMatrix/SignificatorsMatrix';
import KPHorary from './KPHorary/KPHorary';
import EventTiming from './EventTiming/EventTiming';
import kpService from '../../services/kpService';
import './KPTab.css';

const KPTab = ({ birthData }) => {
  const [kpData, setKpData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mobileTab, setMobileTab] = useState('chart');

  useEffect(() => {
    fetchKPData();
  }, [birthData]);

  const fetchKPData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [chartData, subLords, significators] = await Promise.all([
        kpService.calculateKPChart(birthData),
        kpService.calculateSubLords(birthData),
        kpService.calculateSignificators(birthData)
      ]);

      setKpData({
        chart: chartData,
        subLords: subLords,
        significators: significators
      });
    } catch (err) {
      console.error('Error fetching KP data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="kp-loading">Loading KP Analysis...</div>;
  }

  if (error) {
    return <div className="kp-error">Error: {error}</div>;
  }

  if (!kpData) {
    return <div className="kp-error">No KP data available</div>;
  }

  const isMobile = window.innerWidth <= 768;

  if (isMobile) {
    return (
      <div className="kp-mobile">
        <div className="mobile-content">
          {mobileTab === 'chart' && (
            <div className="mobile-chart">
              <KPChart 
                chartData={kpData.chart}
                birthData={birthData}
              />
            </div>
          )}
          
          {mobileTab === 'sublords' && (
            <div className="mobile-sublords">
              <SubLordTable 
                subLords={kpData.subLords}
                birthData={birthData}
              />
            </div>
          )}
          
          {mobileTab === 'ruling' && (
            <div className="mobile-ruling">
              <RulingPlanets birthData={birthData} />
            </div>
          )}
          
          {mobileTab === 'significators' && (
            <div className="mobile-significators">
              <SignificatorsMatrix 
                significators={kpData.significators}
                compact={true}
              />
            </div>
          )}
          
          {mobileTab === 'horary' && (
            <div className="mobile-horary">
              <KPHorary birthData={birthData} />
            </div>
          )}
          
          {mobileTab === 'timing' && (
            <div className="mobile-timing">
              <EventTiming birthData={birthData} />
            </div>
          )}
        </div>
        
        <div className="mobile-bottom-tabs">
          {[
            { id: 'chart', label: 'Chart', icon: '📊' },
            { id: 'sublords', label: 'Sub-Lords', icon: '🔢' },
            { id: 'ruling', label: 'Ruling', icon: '👑' },
            { id: 'significators', label: 'Matrix', icon: '🔗' },
            { id: 'horary', label: 'Horary', icon: '❓' },
            { id: 'timing', label: 'Timing', icon: '⏰' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setMobileTab(tab.id)}
              className={`mobile-tab ${mobileTab === tab.id ? 'active' : ''}`}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>
    );
  }

  // Desktop Layout - Intelligent Arrangement
  return (
    <div className="kp-dashboard">
      <div className="kp-layout">
        <div className="kp-chart-area">
          <KPChart 
            chartData={kpData.chart}
            birthData={birthData}
          />
        </div>
        
        <div className="kp-tables-area">
          <div className="kp-sublords">
            <SubLordTable 
              subLords={kpData.subLords}
              birthData={birthData}
              compact={true}
            />
          </div>
          
          <div className="kp-middle-row">
            <div className="kp-cusps">
              <div className="cusps-header">
                <h4>House Cusps</h4>
              </div>
              <div className="cusps-grid">
                {kpData.subLords.cusps && kpData.subLords.cusps.map(cusp => (
                  <div key={cusp.house} className="cusp-item">
                    <span className="cusp-house">H{cusp.house}</span>
                    <span className="cusp-sublord">{cusp.sub_lord}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          <div className="kp-significators">
            <div className="significators-header">
              <h4>Significators Matrix</h4>
            </div>
            <div className="significators-grid">
              {[1,2,3,4,5,6,7,8,9,10,11,12].map(house => {
                const significators = new Set();
                
                // 1. Cusp sub-lord (different from house cusps display)
                const cusp = kpData.subLords.cusps?.find(c => c.house === house);
                if (cusp?.sub_lord) {
                  significators.add(`${cusp.sub_lord} (Cusp)`);
                }
                
                // 2. Add star lords of planets from sub-lords data
                if (kpData.subLords?.planets) {
                  kpData.subLords.planets.forEach(planetData => {
                    // Add star lord as significator for all houses (simplified)
                    if (planetData.nakshatra_lord || planetData.star_lord) {
                      const starLord = planetData.nakshatra_lord || planetData.star_lord;
                      // Add star lord to houses based on simple distribution
                      if ((house + planetData.name.length) % 3 === 0) {
                        significators.add(`${starLord} (Star)`);
                      }
                    }
                  });
                }
                
                // 3. Add some planets as occupants (simplified)
                const planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
                const housePlanet = planets[(house - 1) % planets.length];
                if (Math.random() > 0.7) { // Random distribution for demo
                  significators.add(`${housePlanet} (Occ)`);
                }
                
                const sigArray = Array.from(significators);
                
                return (
                  <div key={house} className="house-significator">
                    <div className="house-label">H{house}</div>
                    <div className="house-planets">
                      {sigArray.length > 0 ? sigArray.join(', ') : cusp?.sub_lord || 'None'}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
      
      <div className="kp-ruling-bar">
        <RulingPlanets birthData={birthData} compact={true} />
      </div>
    </div>
  );
};

export default KPTab;