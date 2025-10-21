import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { CHART_CONFIG } from '../../config/dashboard.config';
import { apiService } from '../../services/apiService';
import HouseContextMenu from './HouseContextMenu';
import HouseAnalysisModal from './HouseAnalysisModal';

/**
 * NORTH INDIAN CHART POSITIONING REFERENCE
 * ========================================
 * 
 * Chart Structure: 400x400 SVG viewBox, 12 houses (8 triangular + 4 diamond)
 * Geometry: outer square + inner diamond + 2 diagonals
 * 
 * HOUSE CENTERS:
 * House 1: (200, 110) - Top diamond
 * House 2: (110, 70) - Top-left triangle  
 * House 3: (70, 110) - Left triangle
 * House 4: (110, 200) - Left diamond
 * House 5: (70, 290) - Left triangle
 * House 6: (110, 330) - Bottom-left triangle
 * House 7: (200, 290) - Bottom diamond
 * House 8: (290, 330) - Bottom-right triangle
 * House 9: (330, 290) - Right triangle
 * House 10: (290, 200) - Right diamond
 * House 11: (330, 110) - Right triangle
 * House 12: (290, 70) - Top-right triangle
 * 
 * RASHI POSITIONING (X, Y offsets from center):
 * House 1: (-5, -5) - moved up
 * House 2: (-5, +35) - bottom of inverted triangle
 * House 3: (+10, +5) - moved right
 * House 4: (+40, +5) - moved far right
 * House 5: (+10, +5) - moved right
 * House 6: (-5, -10) - moved up
 * House 7: (-5, -10) - moved up
 * House 8: (-5, -10) - moved up
 * House 9: (-20, +5) - moved left
 * House 10: (-40, +5) - moved far left
 * House 11: (-15, +5) - moved left
 * House 12: (-5, +35) - bottom of inverted triangle
 * 
 * PLANET POSITIONING RULES:
 * - Houses 2,12: Inverted triangles - planets above rashi
 * - Houses 3,4,5: Left side - planets left of rashi  
 * - Houses 9,10,11: Right side - planets right of rashi
 * - Houses 1,6,7,8: Standard - planets below rashi
 * - Spacing: Use (col === 0 ? -spacing : spacing) NOT (col * spacing)
 * - 2-4 planets: 16px horizontal, 18px vertical spacing
 * - 5+ planets: 3-column grid, 12px horizontal, 15px vertical
 * 
 * See: docs/NORTH_INDIAN_CHART_POSITIONING.md for complete reference
 */

const NorthIndianChart = ({ chartData, birthData, showDegreeNakshatra = true }) => {
  const { signs, planets } = CHART_CONFIG;
  const [tooltip, setTooltip] = useState({ show: false, x: 0, y: 0, text: '' });
  const [contextMenu, setContextMenu] = useState({ show: false, x: 0, y: 0, planet: null, rashi: null, type: null });
  const [houseContextMenu, setHouseContextMenu] = useState({ show: false, x: 0, y: 0, houseNumber: null, signName: null });
  const [friendshipData, setFriendshipData] = useState(null);
  const [highlightedPlanet, setHighlightedPlanet] = useState(null);
  const [highlightMode, setHighlightMode] = useState(null);
  const [customAscendant, setCustomAscendant] = useState(null);
  const [isTouchDevice, setIsTouchDevice] = useState(false);
  const [houseAnalysisModal, setHouseAnalysisModal] = useState({ show: false, houseNumber: null, signName: null });
  const [houseSignificationsModal, setHouseSignificationsModal] = useState({ show: false, houseNumber: null, signName: null });
  const [aspectsHighlight, setAspectsHighlight] = useState({ show: false, houseNumber: null });
  const [houseStrengthModal, setHouseStrengthModal] = useState({ show: false, houseNumber: null, signName: null });

  

  
  // House positions and shapes within the existing North Indian chart structure
  const getHouseData = (houseNum) => {
    const houseData = {
      1: { center: { x: 200, y: 110 } },  // Top center diamond
      2: { center: { x: 110, y: 70 } },   // Top-left triangle
      3: { center: { x: 70, y: 110 } },   // Left-top triangle
      4: { center: { x: 110, y: 200 } },  // Left center diamond
      5: { center: { x: 70, y: 290 } },   // Left-bottom triangle
      6: { center: { x: 110, y: 330 } },  // Bottom-left triangle
      7: { center: { x: 200, y: 290 } },  // Bottom center diamond
      8: { center: { x: 290, y: 330 } },  // Bottom-right triangle
      9: { center: { x: 330, y: 290 } },  // Right-bottom triangle
      10: { center: { x: 290, y: 200 } }, // Right center diamond
      11: { center: { x: 330, y: 110 } }, // Right-top triangle
      12: { center: { x: 290, y: 70 } }   // Top-right triangle
    };
    return houseData[houseNum];
  };

  const getRashiForHouse = (houseIndex) => {
    if (!chartData.houses || !chartData.houses[houseIndex]) return houseIndex;
    
    if (customAscendant !== null) {
      // Recalculate house-rashi mapping based on custom ascendant
      return (customAscendant + houseIndex) % 12;
    }
    
    // Default: use original chart data
    return chartData.houses[houseIndex].sign;
  };

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

  const handlePlanetRightClick = (e, planet) => {
    e.preventDefault();
    setContextMenu({
      show: true,
      x: e.clientX,
      y: e.clientY,
      planet: planet.name,
      rashi: null,
      type: 'planet'
    });
  };

  const handleRashiClick = (e, rashiIndex, houseNumber) => {
    e.stopPropagation();
    if (e.type === 'contextmenu') {
      e.preventDefault();
    }
    const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
    
    // For mobile, use touch coordinates; for desktop, use mouse coordinates
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    
    const isMobile = window.innerWidth <= 768;
    const relativeX = Math.min(clientX, window.innerWidth - 220);
    const relativeY = isMobile ? Math.max(200, clientY) : Math.max(50, clientY);
    
    setHouseContextMenu({
      show: true,
      x: relativeX,
      y: relativeY,
      houseNumber: houseNumber,
      signName: rashiNames[rashiIndex]
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

  const handleMakeAscendant = (houseNumber, signName) => {
    const rashiIndex = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'].indexOf(signName);
    setCustomAscendant(rashiIndex);
  };

  const handleShowAspects = (houseNumber, signName) => {
    const aspectingPlanets = [];
    
    // Find planets that aspect this house
    Object.entries(chartData.planets || {}).forEach(([planetName, planetData]) => {
      const planetSign = planetData.sign;
      const ascendantSign = chartData.houses?.[0]?.sign || 0;
      const planetHouse = ((planetSign - ascendantSign + 12) % 12) + 1;
      
      let isAspecting = false;
      let aspectType = '';
      
      // 7th aspect (all planets)
      const seventhAspect = (planetHouse + 6) % 12 || 12;
      if (seventhAspect === houseNumber) {
        isAspecting = true;
        aspectType = '7th';
      }
      
      // Special aspects
      if (planetName === 'Mars') {
        const marsAspects = [(planetHouse + 3) % 12 || 12, (planetHouse + 7) % 12 || 12];
        if (marsAspects.includes(houseNumber)) {
          isAspecting = true;
          aspectType = marsAspects[0] === houseNumber ? '4th' : '8th';
        }
      } else if (planetName === 'Jupiter') {
        const jupiterAspects = [(planetHouse + 4) % 12 || 12, (planetHouse + 8) % 12 || 12];
        if (jupiterAspects.includes(houseNumber)) {
          isAspecting = true;
          aspectType = jupiterAspects[0] === houseNumber ? '5th' : '9th';
        }
      } else if (planetName === 'Saturn') {
        const saturnAspects = [(planetHouse + 2) % 12 || 12, (planetHouse + 9) % 12 || 12];
        if (saturnAspects.includes(houseNumber)) {
          isAspecting = true;
          aspectType = saturnAspects[0] === houseNumber ? '3rd' : '10th';
        }
      } else if (['Rahu', 'Ketu'].includes(planetName)) {
        const rahuKetuAspects = [(planetHouse + 2) % 12 || 12, (planetHouse + 10) % 12 || 12];
        if (rahuKetuAspects.includes(houseNumber)) {
          isAspecting = true;
          aspectType = rahuKetuAspects[0] === houseNumber ? '3rd' : '11th';
        }
      }
      
      if (isAspecting) {
        const isNaturalBenefic = ['Jupiter', 'Venus', 'Moon'].includes(planetName);
        aspectingPlanets.push({
          name: planetName,
          house: planetHouse,
          aspectType,
          isPositive: isNaturalBenefic
        });
      }
    });
    
    setAspectsHighlight({ 
      show: true, 
      houseNumber, 
      aspectingPlanets
    });
  };

  const handleHouseAnalysis = (houseNumber, signName) => {
    setHouseAnalysisModal({ show: true, houseNumber, signName });
  };

  const handleHouseSignifications = (houseNumber, signName) => {
    setHouseSignificationsModal({ show: true, houseNumber, signName });
  };

  const handleHouseStrength = (houseNumber, signName) => {
    setHouseStrengthModal({ show: true, houseNumber, signName });
  };

  const isCombusted = (planet) => {
    if (planet.name === 'Sun' || !chartData.planets?.Sun) return false;
    
    const planetData = chartData.planets[planet.name];
    const sunData = chartData.planets.Sun;
    
    if (!planetData) return false;
    
    // Calculate angular distance
    let distance = Math.abs(planetData.longitude - sunData.longitude);
    if (distance > 180) distance = 360 - distance;
    
    // Combustion distances in degrees
    const combustionDistances = {
      'Moon': 12, 'Mars': 17, 'Mercury': 14, 'Jupiter': 11, 'Venus': 10, 'Saturn': 15
    };
    
    return distance <= (combustionDistances[planet.name] || 0);
  };

  const getPlanetStatus = (planet) => {
    // Check combustion first
    if (isCombusted(planet)) return 'combusted';
    
    // Only main planets have exaltation/debilitation - exclude Rahu, Ketu, Gulika, Mandi
    if (['Rahu', 'Ketu', 'Gulika', 'Mandi'].includes(planet.name)) {
      return 'normal';
    }
    
    // Get the actual sign from chartData
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
    const planetData = chartData.planets?.[planet.name];
    const isRetrograde = planetData?.retrograde;
    

    
    let symbol = planet.symbol;
    if (isRetrograde) symbol += '(R)';
    if (status === 'combusted') symbol += '(c)';
    if (status === 'exalted') symbol += '↑';
    if (status === 'debilitated') symbol += '↓';
    return symbol;
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

  const getShortNakshatra = (longitude) => {
    const shortNakshatras = [
      'Ash', 'Bha', 'Kri', 'Roh', 'Mri', 'Ard',
      'Pun', 'Pus', 'Asl', 'Mag', 'PPh', 'UPh',
      'Has', 'Chi', 'Swa', 'Vis', 'Anu', 'Jye',
      'Mul', 'PAs', 'UAs', 'Shr', 'Dha', 'Sha',
      'PBh', 'UBh', 'Rev'
    ];
    const nakshatraIndex = Math.floor(longitude / 13.333333);
    return shortNakshatras[nakshatraIndex] || 'Unk';
  };

  const formatDegree = (degree) => {
    return degree.toFixed(2) + '°';
  };

  const getPlanetsInHouse = (houseIndex) => {
    if (!chartData.planets) return [];
    
    const rashiForThisHouse = getRashiForHouse(houseIndex);
    
    return Object.entries(chartData.planets)
      .filter(([name, data]) => {
        return data.sign === rashiForThisHouse;
      })
      .map(([name, data]) => {
        const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi'];
        const planetIndex = planetNames.indexOf(name);
        return {
          symbol: planets[planetIndex] || name.substring(0, 2),
          name: name,
          degree: data.degree ? data.degree.toFixed(2) : '0.00',
          nakshatra: getNakshatra(data.longitude),
          shortNakshatra: getShortNakshatra(data.longitude),
          formattedDegree: formatDegree(data.degree || 0)
        };
      });
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'visible', zIndex: 1 }}>
      {(highlightedPlanet || customAscendant !== null || aspectsHighlight.show) && (
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
          {aspectsHighlight.show && (
            <button
              onClick={() => setAspectsHighlight({ show: false, houseNumber: null })}
              style={{
                padding: '4px 8px',
                fontSize: '12px',
                background: '#2196f3',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Clear Aspects
            </button>
          )}
        </div>
      )}
      <svg 
        viewBox="0 0 400 440" 
        style={{ 
          width: '100%', 
          height: window.innerWidth <= 768 ? 'auto' : '100%',
          minHeight: window.innerWidth <= 768 ? '350px' : '280px',
          maxWidth: '100%',
          aspectRatio: '1/1'
        }}
        preserveAspectRatio="xMidYMid meet"
      >
      {/* Outer square border */}
      <rect x="5" y="5" width="390" height="390" 
            fill="url(#chartGradient)" stroke="#e91e63" strokeWidth="3"/>
      
      {/* Inner diamond border */}
      <polygon points="200,5 395,200 200,395 5,200" 
               fill="none" stroke="#ff6f00" strokeWidth="3"/>
      
      {/* Diagonal lines creating 12 houses */}
      <line x1="5" y1="5" x2="395" y2="395" stroke="#ff8a65" strokeWidth="2"/>
      <line x1="395" y1="5" x2="5" y2="395" stroke="#ff8a65" strokeWidth="2"/>
      

      




      

      

      

      
      {/* Gradient definitions */}
      <defs>
        <linearGradient id="chartGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="rgba(233, 30, 99, 0.1)" />
          <stop offset="50%" stopColor="rgba(255, 111, 0, 0.1)" />
          <stop offset="100%" stopColor="rgba(255, 255, 255, 0.2)" />
        </linearGradient>
      </defs>


      
      {/* Instruction text */}
      <text x="200" y="405" fontSize="12" fill="#666" textAnchor="middle" fontStyle="italic">
        {aspectsHighlight.show ? 'Pink: Selected House | Green Circles: Benefic Aspects | Red Circles: Malefic Aspects' : 'Hover or touch planets to see Nakshatra and degree'}
      </text>
      <text x="200" y="420" fontSize="12" fill="#666" textAnchor="middle" fontStyle="italic">
        {aspectsHighlight.show ? '' : 'Right click any sign to see more options'}
      </text>
      
      {/* Houses */}
      {[1,2,3,4,5,6,7,8,9,10,11,12].map((houseNumber) => {
        const houseIndex = houseNumber - 1;
        const rashiIndex = getRashiForHouse(houseIndex);
        const planetsInHouse = getPlanetsInHouse(houseIndex);
        const houseData = getHouseData(houseNumber);
        
        const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b', '#eb4d4b',
                        '#6c5ce7', '#a29bfe', '#fd79a8', '#00b894', '#00cec9', '#74b9ff'];
        
        return (
          <g key={houseNumber}>


            
            {/* House highlighting for aspects */}
            {aspectsHighlight.show && aspectsHighlight.houseNumber === houseNumber && (
              <circle cx={houseData.center.x} cy={houseData.center.y} r="35" 
                      fill="rgba(233, 30, 99, 0.2)" stroke="#e91e63" strokeWidth="3" strokeDasharray="5,5"/>
            )}
            
            {/* Rashi number (Aries=1, Taurus=2, etc.) */}
            <text x={houseNumber === 1 ? houseData.center.x - 5 :
                     houseNumber === 2 ? houseData.center.x - 10 :
                     houseNumber === 3 ? houseData.center.x + 10 :
                     houseNumber === 4 ? houseData.center.x + 40 :
                     houseNumber === 5 ? houseData.center.x + 10 :
                     houseNumber === 6 ? houseData.center.x - 15 :
                     houseNumber === 7 ? houseData.center.x - 5 :
                     houseNumber === 8 ? houseData.center.x - 5 :
                     houseNumber === 9 ? houseData.center.x - 20 :
                     houseNumber === 10 ? houseData.center.x - 50 :
                     houseNumber === 11 ? houseData.center.x - 25 :
                     houseData.center.x - 5} 
                  y={houseNumber === 1 ? houseData.center.y + 55 :
                     houseNumber === 2 ? houseData.center.y + 25 :
                     houseNumber === 6 ? houseData.center.y - 10 :
                     houseNumber === 7 ? houseData.center.y - 40 :
                     houseNumber === 8 ? houseData.center.y - 10 :
                     houseNumber === 12 ? houseData.center.y + 20 : 
                     houseNumber === 5 ? houseData.center.y + 10 : houseData.center.y + 5} 
                  fontSize="18" 
                  fill={customAscendant === rashiIndex ? "#e91e63" : "#333"} 
                  fontWeight={customAscendant === rashiIndex ? "900" : "bold"}
                  style={{ cursor: 'pointer' }}
                  onContextMenu={(e) => handleRashiClick(e, rashiIndex, houseNumber)}
                  onClick={(e) => {
                    if (window.innerWidth <= 768) {
                      handleRashiClick(e, rashiIndex, houseNumber);
                    }
                  }}>
              {rashiIndex + 1}
            </text>
            

            {/* Planets */}
            {planetsInHouse.map((planet, pIndex) => {
              const totalPlanets = planetsInHouse.length;
              let planetX, planetY;
              
              if (totalPlanets === 1) {
                if (houseNumber === 1) {
                  planetX = houseData.center.x;
                  planetY = houseData.center.y - 15;
                } else if ([3, 4, 5].includes(houseNumber)) {
                  planetX = houseData.center.x - 15;
                  planetY = houseData.center.y + 10;
                } else if ([6, 7, 8].includes(houseNumber)) {
                  planetX = houseData.center.x;
                  planetY = houseData.center.y + 30;
                } else if (houseNumber === 9) {
                  planetX = houseData.center.x + 15;
                  planetY = houseData.center.y - 10;
                } else if (houseNumber === 10) {
                  planetX = houseData.center.x + 15;
                  planetY = houseData.center.y - 20;
                } else if (houseNumber === 11) {
                  planetX = houseData.center.x + 15;
                  planetY = houseData.center.y - 5;
                } else if (houseNumber === 12) {
                  planetX = houseData.center.x;
                  planetY = houseData.center.y - 25;
                } else if (houseNumber === 2) {
                  planetX = houseData.center.x;
                  planetY = houseData.center.y - 35;
                } else {
                  planetX = houseData.center.x;
                  planetY = houseData.center.y - 10;
                }
              } else if (totalPlanets <= 4) {
                // Houses 3, 5, 9, 11: Vertical arrangement (single column)
                if ([3, 5, 9, 11].includes(houseNumber)) {
                  const rowSpacing = 35;
                  if (houseNumber === 3) {
                    planetX = houseData.center.x - 35;
                    planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                  } else if (houseNumber === 5) {
                    planetX = houseData.center.x - 25;
                    planetY = houseData.center.y - 20 + (pIndex * rowSpacing);
                  } else if (houseNumber === 9) {
                    planetX = houseData.center.x + 35;
                    planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                  } else if (houseNumber === 11) {
                    planetX = houseData.center.x + 35;
                    planetY = houseData.center.y - 45 + (pIndex * rowSpacing);
                  }
                } else {
                  // Other houses: 2-column arrangement
                  const row = Math.floor(pIndex / 2);
                  const col = pIndex % 2;
                  const spacing = 25;
                  const rowSpacing = 32;
                  
                  if (houseNumber === 1) {
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y - 20 + (row * rowSpacing);
                  } else if (houseNumber === 4) {
                    planetX = houseData.center.x - 25 + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y + 5 + (row * rowSpacing);
                  } else if ([6, 7, 8].includes(houseNumber)) {
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y + 25 + (row * rowSpacing);
                  } else if (houseNumber === 10) {
                    planetX = houseData.center.x + 15 + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y - 25 + (row * rowSpacing);
                  } else if (houseNumber === 12) {
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y - 15 + (row * rowSpacing);
                  } else if (houseNumber === 2) {
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y - 40 + (row * rowSpacing);
                  } else {
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y - 25 + (row * rowSpacing);
                  }
                }
              } else {
                // For 5+ planets - arrange in single column
                const rowSpacing = 26;
                
                if (houseNumber === 1) {
                  planetX = houseData.center.x;
                  planetY = houseData.center.y - 25 + (pIndex * rowSpacing);
                } else if ([3, 4, 5].includes(houseNumber)) {
                  planetX = houseData.center.x - 25;
                  planetY = houseData.center.y + 0 + (pIndex * rowSpacing);
                } else if ([6, 7, 8].includes(houseNumber)) {
                  planetX = houseData.center.x;
                  planetY = houseData.center.y + 20 + (pIndex * rowSpacing);
                } else if (houseNumber === 9) {
                  planetX = houseData.center.x + 25;
                  planetY = houseData.center.y - 20 + (pIndex * rowSpacing);
                } else if (houseNumber === 10) {
                  planetX = houseData.center.x + 15;
                  planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                } else if (houseNumber === 11) {
                  planetX = houseData.center.x + 25;
                  planetY = houseData.center.y - 15 + (pIndex * rowSpacing);
                } else if (houseNumber === 12) {
                  planetX = houseData.center.x;
                  planetY = houseData.center.y - 5 + (pIndex * rowSpacing);
                } else if (houseNumber === 2) {
                  planetX = houseData.center.x;
                  planetY = houseData.center.y - 35 + (pIndex * rowSpacing);
                } else {
                  planetX = houseData.center.x;
                  planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                }
              }
              const tooltipText = `${planet.name}: ${planet.degree}° in ${planet.nakshatra}`;
              const aspectingPlanet = aspectsHighlight.show && aspectsHighlight.aspectingPlanets?.find(p => p.name === planet.name);
              
              return (
                <g key={pIndex}>
                  {aspectingPlanet && (
                    <circle cx={planetX} cy={planetY} r="12" 
                            fill="none" 
                            stroke={aspectingPlanet.isPositive ? '#4caf50' : '#f44336'} 
                            strokeWidth="2" 
                            strokeDasharray="3,2"/>
                  )}
                  {/* Planet symbol */}
                  <text x={planetX} 
                        y={planetY - 8} 
                        fontSize={totalPlanets >= 4 ? "10" : totalPlanets > 2 ? "13" : "15"} 
                        fill={getPlanetColor(planet)}
                        fontWeight="900"
                        textAnchor="middle"
                        style={{ cursor: 'pointer' }}
                      onMouseEnter={(e) => {
                        if (isTouchDevice) return;
                        const rect = e.currentTarget.closest('svg').getBoundingClientRect();
                        const isRightSide = [8, 9, 10, 11, 12].includes(houseNumber);
                        const offsetX = isRightSide ? -120 : 10;
                        setTooltip({ show: true, x: planetX + offsetX, y: planetY - 30, text: tooltipText });
                      }}
                      onMouseLeave={(e) => {
                        if (isTouchDevice) return;
                        setTooltip({ show: false, x: 0, y: 0, text: '' });
                      }}
                      onTouchStart={(e) => {
                        setIsTouchDevice(true);
                        const rect = e.currentTarget.closest('svg').getBoundingClientRect();
                        const isRightSide = [8, 9, 10, 11, 12].includes(houseNumber);
                        const offsetX = isRightSide ? -120 : 10;
                        setTooltip({ show: true, x: e.touches[0].clientX - rect.left + offsetX, y: e.touches[0].clientY - rect.top - 30, text: tooltipText });
                        setTimeout(() => setTooltip({ show: false, x: 0, y: 0, text: '' }), 2000);
                      }}
                      onContextMenu={(e) => handlePlanetRightClick(e, planet)}>
                    {getPlanetSymbolWithStatus(planet)}
                  </text>
                  {/* Degree and Nakshatra combined */}
                  {showDegreeNakshatra && (
                    <text x={planetX} 
                          y={planetY + 8} 
                          fontSize={totalPlanets >= 4 ? "7" : totalPlanets > 2 ? "9" : "10"} 
                          fill="#666"
                          fontWeight="500"
                          textAnchor="middle"
                          style={{ cursor: 'pointer' }}
                        onContextMenu={(e) => handlePlanetRightClick(e, planet)}>
                      {planet.formattedDegree} {planet.shortNakshatra}
                    </text>
                  )}
                </g>
              );
            })}
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
      
      <HouseContextMenu
        isOpen={houseContextMenu.show}
        position={{ x: houseContextMenu.x, y: houseContextMenu.y }}
        houseNumber={houseContextMenu.houseNumber}
        signName={houseContextMenu.signName}
        onClose={() => setHouseContextMenu({ show: false, x: 0, y: 0, houseNumber: null, signName: null })}
        onMakeAscendant={handleMakeAscendant}
        onShowAspects={handleShowAspects}
        onHouseAnalysis={handleHouseAnalysis}
        onHouseSignifications={handleHouseSignifications}
        onHouseStrength={handleHouseStrength}
      />
      
      {contextMenu.show && createPortal(
        <div style={{
          position: 'fixed',
          left: contextMenu.x,
          top: contextMenu.y,
          background: 'white',
          border: '2px solid #e91e63',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
          zIndex: 2147483647,
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
        </div>,
        document.body
      )}
      
      <HouseAnalysisModal
        isOpen={houseAnalysisModal.show}
        onClose={() => setHouseAnalysisModal({ show: false, houseNumber: null, signName: null })}
        houseNumber={houseAnalysisModal.houseNumber}
        signName={houseAnalysisModal.signName}
        chartData={chartData}
        getPlanetsInHouse={getPlanetsInHouse}
        getRashiForHouse={getRashiForHouse}
      />

      {/* House Significations Modal */}
      {houseSignificationsModal.show && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 10000,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }} onClick={() => setHouseSignificationsModal({ show: false, houseNumber: null, signName: null })}>
          <div style={{
            backgroundColor: 'white', borderRadius: '12px', padding: '20px',
            maxWidth: '500px', width: '90%', maxHeight: '80vh', overflow: 'auto'
          }} onClick={e => e.stopPropagation()}>
            <h3>House {houseSignificationsModal.houseNumber} Significations ({houseSignificationsModal.signName})</h3>
            <p>{{
              1: "Self, personality, appearance, health, vitality, general well-being",
              2: "Wealth, family, speech, food, values, accumulated resources",
              3: "Siblings, courage, communication, short journeys, skills",
              4: "Mother, home, property, education, happiness, emotional foundation",
              5: "Children, creativity, intelligence, romance, speculation",
              6: "Enemies, diseases, debts, service, obstacles, daily work",
              7: "Spouse, partnerships, business, public relations, marriage",
              8: "Longevity, transformation, occult, inheritance, sudden events",
              9: "Father, guru, dharma, fortune, higher learning, spirituality",
              10: "Career, reputation, authority, social status, achievements",
              11: "Gains, friends, elder siblings, aspirations, income",
              12: "Losses, expenses, foreign lands, spirituality, liberation"
            }[houseSignificationsModal.houseNumber]}</p>
            <button onClick={() => setHouseSignificationsModal({ show: false, houseNumber: null, signName: null })} 
                    style={{ marginTop: '15px', padding: '8px 16px', backgroundColor: '#e91e63', color: 'white', border: 'none', borderRadius: '6px' }}>Close</button>
          </div>
        </div>
      )}

      {/* House Strength Modal */}
      {houseStrengthModal.show && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 10000,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }} onClick={() => setHouseStrengthModal({ show: false, houseNumber: null, signName: null })}>
          <div style={{
            backgroundColor: 'white', borderRadius: '12px', padding: '20px',
            maxWidth: '500px', width: '90%', maxHeight: '80vh', overflow: 'auto'
          }} onClick={e => e.stopPropagation()}>
            <h3>House {houseStrengthModal.houseNumber} Strength ({houseStrengthModal.signName})</h3>
            <p><strong>Occupancy:</strong> {getPlanetsInHouse(houseStrengthModal.houseNumber - 1).length} planets</p>
            <p><strong>Aspects:</strong> Analyzing planetary aspects...</p>
            <p><strong>House Lord:</strong> {['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'][houseStrengthModal.houseNumber - 1]} strength analysis</p>
            <button onClick={() => setHouseStrengthModal({ show: false, houseNumber: null, signName: null })} 
                    style={{ marginTop: '15px', padding: '8px 16px', backgroundColor: '#e91e63', color: 'white', border: 'none', borderRadius: '6px' }}>Close</button>
          </div>
        </div>
      )}

    </div>
  );
};

export default NorthIndianChart;