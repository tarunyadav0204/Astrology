import React from 'react';
import './ColorLegend.css';

const ColorLegend = () => {
  return (
    <div className="color-legend">
      <h4>Auspiciousness Guide</h4>
      <div className="legend-items">
        <div className="legend-item">
          <div className="legend-color auspicious"></div>
          <span>Auspicious - Good for new beginnings, ceremonies</span>
        </div>
        <div className="legend-item">
          <div className="legend-color inauspicious"></div>
          <span>Inauspicious - Avoid important activities</span>
        </div>
        <div className="legend-item">
          <div className="legend-color neutral"></div>
          <span>Neutral - Mixed results</span>
        </div>
      </div>
    </div>
  );
};

export default ColorLegend;