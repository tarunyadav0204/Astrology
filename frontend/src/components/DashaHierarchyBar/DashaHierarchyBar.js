import React from 'react';
import './DashaHierarchyBar.css';

const DashaHierarchyBar = ({ selectedDashas, transitDate }) => {
  const dashaLevels = [
    { key: 'maha', label: 'M', color: '#e91e63' },
    { key: 'antar', label: 'A', color: '#9c27b0' },
    { key: 'pratyantar', label: 'P', color: '#673ab7' },
    { key: 'sookshma', label: 'S', color: '#3f51b5' },
    { key: 'prana', label: 'Pr', color: '#2196f3' }
  ];
  
  const getShortPlanetName = (planetName) => {
    if (!planetName || planetName === '—') return '—';
    const shortNames = {
      'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me',
      'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa', 'Rahu': 'Ra', 'Ketu': 'Ke'
    };
    return shortNames[planetName] || planetName.slice(0, 2);
  };

  return (
    <div className="dasha-hierarchy-bar">
      <div className="hierarchy-levels">
        {dashaLevels.map((level, index) => {
          const dasha = selectedDashas[level.key];
          return (
            <div key={level.key} className="hierarchy-level">
              {index > 0 && <div className="hierarchy-arrow">→</div>}
              <div className={`hierarchy-item ${dasha ? 'active' : 'inactive'}`}>
                <div className="dasha-content">
                  <span className="level-label">{level.label}:</span>
                  <span className="planet-name">
                    {dasha ? (window.innerWidth <= 768 ? getShortPlanetName(dasha.planet) : dasha.planet) : '—'}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DashaHierarchyBar;