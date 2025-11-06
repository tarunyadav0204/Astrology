import React from 'react';
import { SIGN_NAMES, PLANET_NAMES } from '../config/panchangConfig';

const PlanetaryPositions = ({ planetaryData }) => {
  if (!planetaryData || !planetaryData.planets) {
    throw new Error('Planetary data is required');
  }

  const getPlanetIcon = (planet) => {
    const icons = {
      'Sun': '☉',
      'Moon': '☽',
      'Mars': '♂',
      'Mercury': '☿',
      'Jupiter': '♃',
      'Venus': '♀',
      'Saturn': '♄',
      'Rahu': '☊',
      'Ketu': '☋'
    };
    return icons[planet];
  };

  const getPlanetStrength = (planet, sign, degree, retrograde) => {
    let strength = 50; // Base strength
    
    // Exaltation/Debilitation
    const exaltationSigns = {
      'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 
      'Jupiter': 3, 'Venus': 11, 'Saturn': 6
    };
    const debilitationSigns = {
      'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11, 
      'Jupiter': 9, 'Venus': 5, 'Saturn': 0
    };
    
    if (exaltationSigns[planet] === sign) strength += 30;
    else if (debilitationSigns[planet] === sign) strength -= 30;
    
    // Own sign strength
    const ownSigns = {
      'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
      'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
    };
    if (ownSigns[planet] && ownSigns[planet].includes(sign)) strength += 20;
    
    // Retrograde effect
    if (retrograde && planet !== 'Sun' && planet !== 'Moon') strength += 10;
    
    // Degree-based strength (0-30 degrees)
    if (degree >= 5 && degree <= 25) strength += 10; // Avoid gandanta
    
    return Math.max(0, Math.min(100, strength));
  };

  const getSignTransitions = () => {
    return Object.entries(planetaryData.planets)
      .filter(([planet, data]) => data.sign_transition_date)
      .map(([planet, data]) => ({
        planet,
        from_sign: data.current_sign,
        to_sign: data.next_sign,
        transition_date: data.sign_transition_date
      }));
  };

  const getCombustionStatus = (planet, sunLongitude, planetLongitude) => {
    if (planet === 'Sun') return false;
    
    const combustionOrbs = {
      'Moon': 12, 'Mars': 17, 'Mercury': 14, 
      'Jupiter': 11, 'Venus': 10, 'Saturn': 15
    };
    
    const orb = combustionOrbs[planet];
    if (!orb) return false;
    
    const difference = Math.abs(sunLongitude - planetLongitude);
    const adjustedDiff = difference > 180 ? 360 - difference : difference;
    
    return adjustedDiff <= orb;
  };

  const sunLongitude = planetaryData.planets.Sun.longitude;
  const signTransitions = getSignTransitions();

  return (
    <div className="planetary-positions">
      <div className="ayanamsa-info">
        Ayanamsa: {planetaryData.ayanamsa.toFixed(2)}°
      </div>

      <div className="planets-grid">
        {PLANET_NAMES.map(planet => {
          const planetData = planetaryData.planets[planet];
          if (!planetData) return null;

          const isCombust = getCombustionStatus(planet, sunLongitude, planetData.longitude);

          return (
            <div key={planet} className="planet-card-compact" style={{height: '110px', maxHeight: '110px', padding: '4px', overflow: 'hidden', lineHeight: '1.1', fontSize: '14px', background: 'white', border: '1px solid #e9ecef', borderRadius: '4px', textAlign: 'center', position: 'relative', minWidth: '0'}}>
              <div className="status-badges">
                {planetData.retrograde && <span className="badge retrograde">R</span>}
                {isCombust && <span className="badge combust">C</span>}
              </div>
              <div className="planet-header">
                <span className="planet-icon">{getPlanetIcon(planet)}</span>
                <span className="planet-name">{planet}</span>
              </div>
              <div className="planet-info">
                <span className="sign">{SIGN_NAMES[planetData.sign]}</span>
                <span className="degree">{planetData.degree.toFixed(1)}°</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="planetary-summary">
        <div className="summary-item">
          <h4>Retrograde</h4>
          <div className="summary-content">
            {PLANET_NAMES
              .filter(planet => planetaryData.planets[planet]?.retrograde)
              .map(planet => (
                <span key={planet} className="planet-tag">
                  {getPlanetIcon(planet)} {planet}
                </span>
              ))
            }
            {PLANET_NAMES.filter(planet => planetaryData.planets[planet]?.retrograde).length === 0 && (
              <span className="no-status">None</span>
            )}
          </div>
        </div>

        <div className="summary-item">
          <h4>Combust</h4>
          <div className="summary-content">
            {PLANET_NAMES
              .filter(planet => planet !== 'Sun')
              .filter(planet => getCombustionStatus(planet, sunLongitude, planetaryData.planets[planet].longitude))
              .map(planet => (
                <span key={planet} className="planet-tag">
                  {getPlanetIcon(planet)} {planet}
                </span>
              ))
            }
            {PLANET_NAMES
              .filter(planet => planet !== 'Sun')
              .every(planet => !getCombustionStatus(planet, sunLongitude, planetaryData.planets[planet].longitude)) && (
              <span className="no-status">None</span>
            )}
          </div>
        </div>
      </div>

    </div>
  );
};

export default PlanetaryPositions;