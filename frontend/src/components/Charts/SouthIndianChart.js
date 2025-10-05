import React, { useState, useEffect } from 'react';
import { CHART_CONFIG } from '../../config/dashboard.config';
import { apiService } from '../../services/apiService';

const SouthIndianChart = ({ chartData, birthData }) => {
  const { signs, planets } = CHART_CONFIG;
  const [tooltip, setTooltip] = useState({ show: false, x: 0, y: 0, text: '' });
  const [contextMenu, setContextMenu] = useState({ show: false, x: 0, y: 0, planet: null, rashi: null, type: null });
  const [friendshipData, setFriendshipData] = useState(null);
  const [highlightedPlanet, setHighlightedPlanet] = useState(null);
  const [highlightMode, setHighlightMode] = useState(null);
  const [customAscendant, setCustomAscendant] = useState(null);
  
  // South Indian chart - fixed 4x4 grid positions (signs don't rotate)
  const gridPositions = [
    // Row 1
    { x: 0, y: 0, width: 75, height: 75, sign: 11 },     // Pisces
    { x: 75, y: 0, width: 75, height: 75, sign: 0 },     // Aries  
    { x: 150, y: 0, width: 75, height: 75, sign: 1 },    // Taurus
    { x: 225, y: 0, width: 75, height: 75, sign: 2 },    // Gemini
    // Row 2
    { x: 0, y: 75, width: 75, height: 75, sign: 10 },    // Aquarius
    { x: 75, y: 75, width: 75, height: 75, sign: -1 },   // Empty
    { x: 150, y: 75, width: 75, height: 75, sign: -1 },  // Empty
    { x: 225, y: 75, width: 75, height: 75, sign: 3 },   // Cancer
    // Row 3
    { x: 0, y: 150, width: 75, height: 75, sign: 9 },    // Capricorn
    { x: 75, y: 150, width: 75, height: 75, sign: -1 },  // Empty
    { x: 150, y: 150, width: 75, height: 75, sign: -1 }, // Empty
    { x: 225, y: 150, width: 75, height: 75, sign: 4 },  // Leo
    // Row 4
    { x: 0, y: 225, width: 75, height: 75, sign: 8 },    // Sagittarius
    { x: 75, y: 225, width: 75, height: 75, sign: 7 },   // Scorpio
    { x: 150, y: 225, width: 75, height: 75, sign: 6 },  // Libra
    { x: 225, y: 225, width: 75, height: 75, sign: 5 }   // Virgo
  ];

  useEffect(() => {
    if (birthData) {
      loadFriendshipData();
    }
  }, [birthData]);

  useEffect(() => {
    const handleOutsideClick = () => {
      setContextMenu({ show: false, x: 0, y: 0, planet: null, rashi: null, type: null });
    };

    if (contextMenu.show) {
      document.addEventListener('click', handleOutsideClick);
      return () => document.removeEventListener('click', handleOutsideClick);
    }
  }, [contextMenu.show]);

  const loadFriendshipData = async () => {
    try {
      const data = await apiService.calculateFriendship(birthData);
      setFriendshipData(data);
    } catch (error) {
      console.error('Failed to load friendship data:', error);
    }
  };

  const isCombusted = (planet) => {
    if (planet.name === 'Sun' || !chartData.planets?.Sun) return false;
    
    const planetData = chartData.planets[planet.name];
    const sunData = chartData.planets.Sun;
    
    if (!planetData) return false;
    
    let distance = Math.abs(planetData.longitude - sunData.longitude);
    if (distance > 180) distance = 360 - distance;
    
    const combustionDistances = {
      'Moon': 12, 'Mars': 17, 'Mercury': 14, 'Jupiter': 11, 'Venus': 10, 'Saturn': 15
    };
    
    return distance <= (combustionDistances[planet.name] || 0);
  };

  const getPlanetStatus = (planet) => {
    if (isCombusted(planet)) return 'combusted';
    
    if (['Rahu', 'Ketu', 'Gulika', 'Mandi'].includes(planet.name)) {
      return 'normal';
    }
    
    const planetData = chartData.planets?.[planet.name];
    if (!planetData) return 'normal';
    
    const planetSign = planetData.sign;
    
    const exaltationSigns = {
      'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5, 'Jupiter': 3, 'Venus': 11, 'Saturn': 6
    };
    const debilitationSigns = {
      'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11, 'Jupiter': 9, 'Venus': 5, 'Saturn': 0
    };
    
    if (exaltationSigns[planet.name] === planetSign) return 'exalted';
    if (debilitationSigns[planet.name] === planetSign) return 'debilitated';
    return 'normal';
  };

  const getPlanetHighlight = (planetName) => {
    if (!highlightedPlanet || !friendshipData || highlightedPlanet === planetName) return null;
    
    if (highlightMode === 'friendship') {
      const relationship = friendshipData.friendship_matrix[highlightedPlanet][planetName];
      switch (relationship) {
        case 'great_friend': return '#00ff00';
        case 'friend': return '#90ee90';
        case 'enemy': return '#ff6b6b';
        case 'great_enemy': return '#ff0000';
        default: return null;
      }
    } else if (highlightMode === 'aspects') {
      const aspect = friendshipData.aspects_matrix[highlightedPlanet][planetName];
      if (aspect && aspect.type !== 'none') {
        switch (aspect.type) {
          case 'conjunction': return '#ff00ff';
          case 'trine': return '#00ff00';
          case 'sextile': return '#90ee90';
          case 'square': return '#ff6b6b';
          case 'opposition': return '#ff0000';
          default: return null;
        }
      }
    }
    return null;
  };

  const getPlanetColor = (planet) => {
    const highlight = getPlanetHighlight(planet.name);
    if (highlight) return highlight;
    
    const status = getPlanetStatus(planet);
    if (status === 'combusted') return '#ff8c00';
    if (status === 'exalted') return '#22c55e';
    if (status === 'debilitated') return '#ef4444';
    return '#2d3436';
  };

  const getPlanetSymbolWithStatus = (planet) => {
    const status = getPlanetStatus(planet);
    if (status === 'combusted') return planet.symbol + '(c)';
    if (status === 'exalted') return planet.symbol + '↑';
    if (status === 'debilitated') return planet.symbol + '↓';
    return planet.symbol;
  };

  const getNakshatra = (longitude) => {
    const nakshatras = [
      'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
      'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
      'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
      'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
      'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
    ];
    const nakshatraIndex = Math.floor(longitude / 13.333333);
    return nakshatras[nakshatraIndex] || 'Unknown';
  };

  const handlePlanetRightClick = (e, planet) => {
    e.preventDefault();
    const rect = e.currentTarget.closest('svg').getBoundingClientRect();
    setContextMenu({
      show: true,
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      planet: planet.name,
      rashi: null,
      type: 'planet'
    });
  };

  const handleRashiRightClick = (e, rashiIndex) => {
    e.preventDefault();
    const rect = e.currentTarget.closest('svg').getBoundingClientRect();
    const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
    setContextMenu({
      show: true,
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      planet: null,
      rashi: rashiIndex,
      rashiName: rashiNames[rashiIndex],
      type: 'rashi'
    });
  };

  const handleContextMenuAction = (action) => {
    if (contextMenu.type === 'planet') {
      setHighlightedPlanet(contextMenu.planet);
      setHighlightMode(action);
    } else if (contextMenu.type === 'rashi' && action === 'setAscendant') {
      setCustomAscendant(contextMenu.rashi);
    }
    setContextMenu({ show: false, x: 0, y: 0, planet: null, rashi: null, type: null });
  };

  const clearHighlight = () => {
    setHighlightedPlanet(null);
    setHighlightMode(null);
  };

  const resetAscendant = () => {
    setCustomAscendant(null);
  };

  const getPlanetsInSign = (signIndex) => {
    if (!chartData.planets || signIndex === -1) return [];
    
    return Object.entries(chartData.planets)
      .filter(([name, data]) => data.sign === signIndex)
      .map(([name, data]) => {
        const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi'];
        const planetIndex = planetNames.indexOf(name);
        return {
          symbol: planets[planetIndex] || name.substring(0, 2),
          name: name,
          degree: data.degree.toFixed(2),
          nakshatra: getNakshatra(data.longitude)
        };
      });
  };

  const getHouseNumber = (signIndex) => {
    if (!chartData.houses || !chartData.houses[0] || signIndex === -1) return '';
    const ascendantSign = customAscendant !== null ? customAscendant : Math.floor(chartData.houses[0].longitude / 30);
    return ((signIndex - ascendantSign + 12) % 12) + 1;
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {(highlightedPlanet || customAscendant !== null) && (
        <div style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 10, display: 'flex', gap: '4px' }}>
          {highlightedPlanet && (
            <button
              onClick={clearHighlight}
              style={{
                padding: '4px 8px',
                fontSize: '12px',
                background: '#e91e63',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Clear
            </button>
          )}
          {customAscendant !== null && (
            <button
              onClick={resetAscendant}
              style={{
                padding: '4px 8px',
                fontSize: '12px',
                background: '#ff6f00',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Reset
            </button>
          )}
        </div>
      )}
      <svg 
        width="300" 
        height="300" 
        viewBox="0 0 300 300"
        style={{ 
          width: '100%', 
          height: '100%',
          minHeight: '280px',
          maxWidth: '100%'
        }}
        preserveAspectRatio="xMidYMid meet"
      >
      {/* Gradient definitions */}
      <defs>
        <linearGradient id="southChartGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="rgba(233, 30, 99, 0.1)" />
          <stop offset="50%" stopColor="rgba(255, 111, 0, 0.1)" />
          <stop offset="100%" stopColor="rgba(255, 255, 255, 0.2)" />
        </linearGradient>
      </defs>
      
      {/* Outer border */}
      <rect x="0" y="0" width="300" height="300" 
            fill="url(#southChartGradient)" stroke="#e91e63" strokeWidth="3"/>
      
      {/* Outer house divisions - no center grid */}
      {/* Top row divisions */}
      <line x1="75" y1="0" x2="75" y2="75" stroke="#ff8a65" strokeWidth="2"/>
      <line x1="150" y1="0" x2="150" y2="75" stroke="#ff8a65" strokeWidth="2"/>
      <line x1="225" y1="0" x2="225" y2="75" stroke="#ff8a65" strokeWidth="2"/>
      {/* Bottom row divisions */}
      <line x1="75" y1="225" x2="75" y2="300" stroke="#ff8a65" strokeWidth="2"/>
      <line x1="150" y1="225" x2="150" y2="300" stroke="#ff8a65" strokeWidth="2"/>
      <line x1="225" y1="225" x2="225" y2="300" stroke="#ff8a65" strokeWidth="2"/>
      {/* Left column divisions */}
      <line x1="0" y1="75" x2="75" y2="75" stroke="#ff8a65" strokeWidth="2"/>
      <line x1="0" y1="150" x2="75" y2="150" stroke="#ff8a65" strokeWidth="2"/>
      <line x1="0" y1="225" x2="75" y2="225" stroke="#ff8a65" strokeWidth="2"/>
      {/* Right column divisions */}
      <line x1="225" y1="75" x2="300" y2="75" stroke="#ff8a65" strokeWidth="2"/>
      <line x1="225" y1="150" x2="300" y2="150" stroke="#ff8a65" strokeWidth="2"/>
      <line x1="225" y1="225" x2="300" y2="225" stroke="#ff8a65" strokeWidth="2"/>
      {/* Inner borders of outer houses */}
      <line x1="0" y1="75" x2="300" y2="75" stroke="#ff6f00" strokeWidth="3"/>
      <line x1="0" y1="225" x2="300" y2="225" stroke="#ff6f00" strokeWidth="3"/>
      <line x1="75" y1="0" x2="75" y2="300" stroke="#ff6f00" strokeWidth="3"/>
      <line x1="225" y1="0" x2="225" y2="300" stroke="#ff6f00" strokeWidth="3"/>

      {/* Grid cells */}
      {gridPositions.map((pos, index) => {
        const planetsInSign = getPlanetsInSign(pos.sign);
        const houseNumber = getHouseNumber(pos.sign);
        
        return (
          <g key={index}>
            {pos.sign !== -1 && (
              <>
                {/* House number */}
                <text x={pos.x + 8} y={pos.y + 18} 
                      fontSize="12" 
                      fill={customAscendant === pos.sign ? "#e91e63" : "#333"} 
                      fontWeight={customAscendant === pos.sign ? "900" : "bold"}
                      style={{ cursor: 'pointer' }}
                      onContextMenu={(e) => handleRashiRightClick(e, pos.sign)}>
                  {houseNumber}
                </text>
                
                {/* Sign name */}
                <text x={pos.x + pos.width - 8} y={pos.y + 18} 
                      fontSize="10" fill="#666"
                      textAnchor="end">
                  {signs[pos.sign]}
                </text>
                
                {/* Planets */}
                {planetsInSign.map((planet, pIndex) => {
                  const totalPlanets = planetsInSign.length;
                  const isDoubleDigitHouse = houseNumber >= 10;
                  let planetX, planetY;
                  
                  if (totalPlanets === 1) {
                    planetX = pos.x + pos.width / 2;
                    planetY = pos.y + pos.height / 2 + (isDoubleDigitHouse ? 8 : 5);
                  } else {
                    // Stack all multiple planets vertically
                    planetX = pos.x + pos.width / 2;
                    const lineHeight = totalPlanets > 4 ? 10 : totalPlanets > 2 ? 12 : 13;
                    const startY = pos.y + pos.height / 2 + (isDoubleDigitHouse ? 5 : 2) - ((totalPlanets - 1) * lineHeight / 2);
                    planetY = startY + (pIndex * lineHeight);
                  }
                  
                  return (
                    <text key={pIndex} 
                          x={planetX} 
                          y={planetY} 
                          fontSize={totalPlanets > 4 ? "8" : totalPlanets > 2 ? "10" : totalPlanets > 1 ? "11" : "14"} 
                          fill={getPlanetColor(planet)}
                          fontWeight="900"
                          textAnchor="middle"
                          style={{ cursor: 'pointer' }}
                          onMouseEnter={(e) => {
                            const tooltipText = `${planet.name}: ${planet.degree}° in ${planet.nakshatra}`;
                            const isRightSide = pos.x >= 150; // Right side houses (including middle-right)
                            const offsetX = isRightSide ? -120 : 10;
                            setTooltip({ show: true, x: planetX + offsetX, y: planetY - 12, text: tooltipText });
                          }}
                          onMouseLeave={() => setTooltip({ show: false, x: 0, y: 0, text: '' })}
                          onContextMenu={(e) => handlePlanetRightClick(e, planet)}>
                      {getPlanetSymbolWithStatus(planet)}
                    </text>
                  );
                })}
              </>
            )}
          </g>
        );
      })}
      </svg>
      
      {tooltip.show && (
        <div style={{
          position: 'absolute',
          left: tooltip.x,
          top: tooltip.y,
          background: 'linear-gradient(135deg, #e91e63 0%, #ff6f00 100%)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: '12px',
          fontSize: '13px',
          zIndex: 1000,
          pointerEvents: 'none',
          whiteSpace: 'nowrap',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
          border: '1px solid rgba(255,255,255,0.2)',
          backdropFilter: 'blur(10px)'
        }}>
          {tooltip.text}
        </div>
      )}
      
      {contextMenu.show && (
        <div style={{
          position: 'absolute',
          left: contextMenu.x,
          top: contextMenu.y,
          background: 'white',
          border: '2px solid #e91e63',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
          zIndex: 1001,
          minWidth: '140px'
        }}>
          {contextMenu.type === 'planet' ? (
            <>
              <div 
                onClick={() => handleContextMenuAction('friendship')}
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  borderBottom: '1px solid #eee',
                  fontSize: '12px',
                  color: '#333'
                }}
                onMouseEnter={(e) => e.target.style.background = '#f0f0f0'}
                onMouseLeave={(e) => e.target.style.background = 'white'}
              >
                🤝 Friendship
              </div>
              <div 
                onClick={() => handleContextMenuAction('aspects')}
                style={{
                  padding: '8px 12px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  color: '#333'
                }}
                onMouseEnter={(e) => e.target.style.background = '#f0f0f0'}
                onMouseLeave={(e) => e.target.style.background = 'white'}
              >
                📐 Aspects
              </div>
            </>
          ) : (
            <div 
              onClick={() => handleContextMenuAction('setAscendant')}
              style={{
                padding: '8px 12px',
                cursor: 'pointer',
                fontSize: '12px',
                color: '#333'
              }}
              onMouseEnter={(e) => e.target.style.background = '#f0f0f0'}
              onMouseLeave={(e) => e.target.style.background = 'white'}
            >
              🏠 Set {contextMenu.rashiName} as Ascendant
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SouthIndianChart;