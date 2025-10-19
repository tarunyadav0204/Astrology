import React, { useState } from 'react';
import TimelinePicker from './TimelinePicker';
import TimelineNavigation from './TimelineNavigation';

const NadiAspectsTable = ({ aspects, natalPlanets, onTimelineClick }) => {
  const [aspectTimelines, setAspectTimelines] = useState({});
  
  console.log('NadiAspectsTable received aspects:', aspects);
  console.log('Aspects involving Sun:', aspects?.filter(a => a.planet1 === 'Sun' || a.planet2 === 'Sun'));

  const handleTimelineLoad = (aspect, timeline) => {
    const aspectKey = `${aspect.planet1}-${aspect.planet2}-${aspect.aspect_type}`;
    setAspectTimelines(prev => ({
      ...prev,
      [aspectKey]: timeline
    }));
  };
  const formatPosition = (longitude) => {
    const degree = longitude % 30;
    const sign = Math.floor(longitude / 30);
    const signs = ['Ar', 'Ta', 'Ge', 'Cn', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi'];
    return `${degree.toFixed(1)}° ${signs[sign]}`;
  };

  const getStrengthColor = (strength) => {
    const colors = {
      'VERY_STRONG': '#00ff00',
      'STRONG': '#90ee90', 
      'MODERATE': '#ffff00',
      'WEAK': '#ffa500',
      'VERY_WEAK': '#ff0000'
    };
    return colors[strength] || '#cccccc';
  };

  return (
    <div className="nadi-aspects-table">
      <table>
        <thead>
          <tr>
            <th>Planet</th>
            <th>Position</th>
            <th>Aspects To</th>
            <th>Time Periods</th>
            <th>Strength</th>
          </tr>
        </thead>
        <tbody>
          {aspects?.map((aspect, index) => (
            <tr key={index}>
              <td className="planet-name">{aspect.planet1}</td>
              <td className="planet-position">
                {formatPosition(aspect.planet1_longitude)}
              </td>
              <td className="aspect-details">
                <span className="target-planet">{aspect.planet2}</span>
                <span className="aspect-type">
                  ({aspect.aspect_type} {aspect.actual_degree.toFixed(1)}°)
                </span>
                <span className="orb">
                  [±{aspect.orb.toFixed(1)}°]
                </span>
              </td>
              <td className="timeline-periods">
                <TimelineNavigation 
                  aspect={aspect}
                  natalPlanets={natalPlanets}
                  onTimelineLoad={handleTimelineLoad}
                />
                <TimelinePicker 
                  timeline={aspectTimelines[`${aspect.planet1}-${aspect.planet2}-${aspect.aspect_type}`] || []}
                  onTimeClick={onTimelineClick}
                />
              </td>
              <td className="aspect-strength">
                <span 
                  className="strength-indicator"
                  style={{ color: getStrengthColor(aspect.strength) }}
                >
                  {aspect.strength.replace('_', ' ')}
                </span>
              </td>
            </tr>
          )) || <tr><td colSpan="5">No aspects found</td></tr>}
        </tbody>
      </table>
    </div>
  );
};

export default NadiAspectsTable;