import React, { useState, useEffect, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { CHART_CONFIG } from '../../config/dashboard.config';
import { apiService } from '../../services/apiService';
import HouseContextMenu from './HouseContextMenu';
import HouseAnalysisModal from './HouseAnalysisModal';
import HouseInsightPopup from './HouseInsightPopup';
import ChartOverlayActions from './ChartOverlayActions';
import { resolveChartId } from '../../utils/chartIds';
import { chartActivationFill } from './chartActivationTheme';

const SouthIndianChart = ({
  chartData,
  birthData,
  chartType = 'lagna',
  division,
  showDegreeNakshatra = true,
  chartRefHighlight = null,
  showFooterHint = true,
  deskMode = false,
  onHouseSelect = null,
  selectedHouseNumber = null,
  highlightedPlanets = null,
  highlightedHouseNumbers = null,
  activationHouseStates = null,
}) => {
  const { signs, planets } = CHART_CONFIG;
  const chartId = resolveChartId(chartType, division);
  const [tooltip, setTooltip] = useState({ show: false, x: 0, y: 0, text: '' });
  const [contextMenu, setContextMenu] = useState({ show: false, x: 0, y: 0, planet: null, rashi: null, type: null });
  const [houseContextMenu, setHouseContextMenu] = useState({ show: false, x: 0, y: 0, houseNumber: null, signName: null });
  const [friendshipData, setFriendshipData] = useState(null);
  const [highlightedPlanet, setHighlightedPlanet] = useState(null);
  const [highlightMode, setHighlightMode] = useState(null);
  const [customAscendant, setCustomAscendant] = useState(null);
  const [isTouchDevice, setIsTouchDevice] = useState(false);
  const [houseAnalysisModal, setHouseAnalysisModal] = useState({ show: false, houseNumber: null, signName: null });
  const [aspectsHighlight, setAspectsHighlight] = useState({ show: false, houseNumber: null });
  const [houseStrengthModal, setHouseStrengthModal] = useState({ show: false, houseNumber: null, signName: null });
  const [chartRefHighlightState, setChartRefHighlightState] = useState(null);
  const [houseInsight, setHouseInsight] = useState({
    show: false,
    houseNumber: null,
    signName: null,
    rashiIndex: null,
  });
  
  const highlightedPlanetSet = useMemo(() => {
    if (!highlightedPlanets?.length) return null;
    return new Set(highlightedPlanets.map((name) => String(name).toLowerCase()));
  }, [highlightedPlanets]);

  const highlightedHouseSet = useMemo(() => {
    if (!highlightedHouseNumbers?.length) return null;
    return new Set(highlightedHouseNumbers.map((n) => Number(n)));
  }, [highlightedHouseNumbers]);

  // Handle chart reference highlighting from chat
  useEffect(() => {
    if (chartRefHighlight) {
      setChartRefHighlightState(chartRefHighlight);
      // Auto-clear after 3 seconds
      const timer = setTimeout(() => setChartRefHighlightState(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [chartRefHighlight]);
  
  // South Indian chart - fixed 4x4 grid positions (signs don't rotate)
  const gridPositions = [
    // Row 1
    { x: 0, y: 0, width: 85, height: 85, sign: 11 },     // Pisces
    { x: 85, y: 0, width: 85, height: 85, sign: 0 },     // Aries  
    { x: 170, y: 0, width: 85, height: 85, sign: 1 },    // Taurus
    { x: 255, y: 0, width: 85, height: 85, sign: 2 },    // Gemini
    // Row 2
    { x: 0, y: 85, width: 85, height: 85, sign: 10 },    // Aquarius
    { x: 85, y: 85, width: 85, height: 85, sign: -1 },   // Empty
    { x: 170, y: 85, width: 85, height: 85, sign: -1 },  // Empty
    { x: 255, y: 85, width: 85, height: 85, sign: 3 },   // Cancer
    // Row 3
    { x: 0, y: 170, width: 85, height: 85, sign: 9 },    // Capricorn
    { x: 85, y: 170, width: 85, height: 85, sign: -1 },  // Empty
    { x: 170, y: 170, width: 85, height: 85, sign: -1 }, // Empty
    { x: 255, y: 170, width: 85, height: 85, sign: 4 },  // Leo
    // Row 4
    { x: 0, y: 255, width: 85, height: 85, sign: 8 },    // Sagittarius
    { x: 85, y: 255, width: 85, height: 85, sign: 7 },   // Scorpio
    { x: 170, y: 255, width: 85, height: 85, sign: 6 },  // Libra
    { x: 255, y: 255, width: 85, height: 85, sign: 5 }   // Virgo
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
    
    if (['Rahu', 'Ketu', 'Gulika', 'Mandi', 'InduLagna'].includes(planet.name)) {
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
    // InduLagna has special purple color
    if (planet.name === 'InduLagna') return '#9c27b0';
    
    const highlight = getPlanetHighlight(planet.name);
    if (highlight) return highlight;
    
    const status = getPlanetStatus(planet);
    if (status === 'combusted') return '#ff8c00';
    if (status === 'exalted') return '#22c55e';
    if (status === 'debilitated') return '#ef4444';
    return 'var(--color-chart-text, var(--color-text))';
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
    return Math.floor(degree) + '°';
  };

  const formatDegreeDMS = (degree) => {
    const deg = Math.floor(degree);
    const minFloat = (degree - deg) * 60;
    const min = Math.floor(minFloat);
    const sec = Math.floor((minFloat - min) * 60);
    return `${deg}°${min}'${sec}"`;
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

  const openHouseInsight = (rashiIndex, houseNumber) => {
    const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
    setHouseContextMenu({ show: false, x: 0, y: 0, houseNumber: null, signName: null });
    if (typeof onHouseSelect === 'function') {
      onHouseSelect({
        houseNumber,
        rashiIndex,
        signName: rashiNames[rashiIndex],
        chartId,
      });
      return;
    }
    setHouseInsight({
      show: true,
      houseNumber,
      signName: rashiNames[rashiIndex],
      rashiIndex,
    });
  };

  const handleRashiClick = (e, rashiIndex, houseNumber) => {
    e.stopPropagation();
    if (e.type === 'contextmenu') {
      e.preventDefault();
    }
    const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

    if (e.type === 'click' || e.type === 'touchstart') {
      e.preventDefault();
      openHouseInsight(rashiIndex, houseNumber);
      return;
    }

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
    const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
    const rashiIndex = rashiNames.indexOf(signName);
    openHouseInsight(rashiIndex >= 0 ? rashiIndex : 0, houseNumber);
  };

  const handleHouseStrength = (houseNumber, signName) => {
    setHouseStrengthModal({ show: true, houseNumber, signName });
  };

  const getNakshatraPada = (longitude) => {
    const lon = ((longitude % 360) + 360) % 360;
    return Math.floor((lon % 13.333333) / 3.333333) + 1;
  };

  const getPlanetsInSign = (signIndex) => {
    if (!chartData.planets || signIndex === -1) return [];
    
    const planetsInSign = [];
    const useHousePlacement = Object.values(chartData.planets).some(
      (data) => data && typeof data.house === 'number'
    );
    
    // Add regular planets (exclude InduLagna as it's handled separately)
    Object.entries(chartData.planets)
      .filter(([name, data]) => {
        if (!data || name === 'InduLagna') return false;
        if (useHousePlacement && typeof data.house === 'number') {
          // Place in the South-Indian sign cell of this Placidus house's cusp
          const cuspSign = chartData.houses?.[data.house - 1]?.sign;
          return cuspSign === signIndex;
        }
        return data.sign === signIndex;
      })
      .forEach(([name, data]) => {
        const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi'];
        const planetIndex = planetNames.indexOf(name);
        planetsInSign.push({
          symbol: planets[planetIndex] || name.substring(0, 2),
          name: name,
          degree: data.degree ? data.degree.toFixed(2) : '0.00',
          nakshatra: getNakshatra(data.longitude),
          shortNakshatra: getShortNakshatra(data.longitude),
          formattedDegree: formatDegreeDMS(data.degree || 0),
          retrograde: !!data.retrograde,
          pada: getNakshatraPada(data.longitude || 0),
        });
      });
    
    // Add InduLagna if it's in this sign
    if (chartData.planets?.InduLagna) {
      const indu = chartData.planets.InduLagna;
      let induHere = false;
      if (useHousePlacement && typeof indu.house === 'number') {
        induHere = chartData.houses?.[indu.house - 1]?.sign === signIndex;
      } else {
        induHere = indu.sign === signIndex;
      }
      if (induHere) {
        planetsInSign.push({
          symbol: 'IL',
          name: 'InduLagna',
          degree: indu.degree ? indu.degree.toFixed(2) : '0.00',
          nakshatra: getNakshatra(indu.longitude || 0),
          shortNakshatra: getShortNakshatra(indu.longitude || 0),
          formattedDegree: formatDegreeDMS(indu.degree || 0),
          retrograde: !!indu.retrograde,
          pada: getNakshatraPada(indu.longitude || 0),
        });
      }
    }
    
    return planetsInSign;
  };

  const getHouseNumber = (signIndex) => {
    if (!chartData.houses || !chartData.houses[0] || signIndex === -1) return '';
    const ascendantSign = customAscendant !== null ? customAscendant : Math.floor(chartData.houses[0].longitude / 30);
    return ((signIndex - ascendantSign + 12) % 12) + 1;
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <ChartOverlayActions
        deskMode={deskMode}
        highlightedPlanet={highlightedPlanet}
        onClearHighlight={clearHighlight}
        customAscendant={customAscendant}
        onResetAscendant={resetAscendant}
        aspectsHighlight={aspectsHighlight}
        onClearAspects={() => setAspectsHighlight({ show: false, houseNumber: null })}
      />
      <svg 
        viewBox={deskMode || !showFooterHint ? '0 0 340 340' : '0 0 340 360'}
        data-selected-house={selectedHouseNumber || undefined}
        style={deskMode ? {
          width: '100%',
          height: '100%',
          minHeight: 0,
          maxWidth: '100%',
          maxHeight: '100%',
          display: 'block',
        } : { 
          width: '100%', 
          height: window.innerWidth <= 768 ? 'auto' : '100%',
          minHeight: window.innerWidth <= 768 ? '380px' : '320px',
          maxWidth: '100%',
          aspectRatio: window.innerWidth <= 768 ? '340/360' : 'auto'
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
      <rect x="0" y="0" width="340" height="340" 
            fill="url(#southChartGradient)" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1.5"/>
      
      {/* Outer house divisions - no center grid */}
      {/* Top row divisions */}
      <line x1="85" y1="0" x2="85" y2="85" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1"/>
      <line x1="170" y1="0" x2="170" y2="85" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1"/>
      <line x1="255" y1="0" x2="255" y2="85" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1"/>
      {/* Bottom row divisions */}
      <line x1="85" y1="255" x2="85" y2="340" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1"/>
      <line x1="170" y1="255" x2="170" y2="340" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1"/>
      <line x1="255" y1="255" x2="255" y2="340" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1"/>
      {/* Left column divisions */}
      <line x1="0" y1="85" x2="85" y2="85" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1"/>
      <line x1="0" y1="170" x2="85" y2="170" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1"/>
      <line x1="0" y1="255" x2="85" y2="255" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1"/>
      {/* Right column divisions */}
      <line x1="255" y1="85" x2="340" y2="85" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1"/>
      <line x1="255" y1="170" x2="340" y2="170" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1"/>
      <line x1="255" y1="255" x2="340" y2="255" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1"/>
      {/* Inner borders of outer houses */}
      <line x1="0" y1="85" x2="340" y2="85" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1.5"/>
      <line x1="0" y1="255" x2="340" y2="255" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1.5"/>
      <line x1="85" y1="0" x2="85" y2="340" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1.5"/>
      <line x1="255" y1="0" x2="255" y2="340" stroke="var(--color-chart-line, var(--color-text))" strokeWidth="1.5"/>

      {/* Instruction text */}
      {showFooterHint ? (
        <text x="170" y="350" fontSize="9" fill="var(--color-chart-text-muted, var(--color-text-muted))" textAnchor="middle" fontStyle="italic">
          Click any house for insights · Hover planets for degree
        </text>
      ) : null}
      
      {/* Grid cells */}
      {gridPositions.map((pos, index) => {
        const planetsInSign = getPlanetsInSign(pos.sign);
        const houseNumber = getHouseNumber(pos.sign);
        
        return (
          <g key={index}>
            {pos.sign !== -1 && (
              <>
                {/* Full-cell hit area */}
                <rect
                  x={pos.x}
                  y={pos.y}
                  width={pos.width}
                  height={pos.height}
                  fill="transparent"
                  style={{ cursor: 'pointer' }}
                  onClick={(e) => handleRashiClick(e, pos.sign, houseNumber)}
                  onContextMenu={(e) => handleRashiClick(e, pos.sign, houseNumber)}
                />

                {chartActivationFill(activationHouseStates?.[houseNumber]) ? (
                  <rect
                    x={pos.x + 1}
                    y={pos.y + 1}
                    width={pos.width - 2}
                    height={pos.height - 2}
                    fill={chartActivationFill(activationHouseStates[houseNumber])}
                    stroke="none"
                    style={{ pointerEvents: 'none' }}
                  />
                ) : null}

                {highlightedHouseSet?.has(houseNumber) ? (
                  <rect
                    x={pos.x + 2}
                    y={pos.y + 2}
                    width={pos.width - 4}
                    height={pos.height - 4}
                    fill="rgba(159, 18, 57, 0.07)"
                    stroke="none"
                    style={{ pointerEvents: 'none' }}
                  />
                ) : null}

                {/* Chart reference highlighting from chat */}
                {chartRefHighlightState?.type === 'house' && parseInt(chartRefHighlightState.value) === houseNumber && (
                  <rect x={pos.x + 2} y={pos.y + 2} width={pos.width - 4} height={pos.height - 4}
                        fill="rgba(76, 175, 80, 0.3)" stroke="#4caf50" strokeWidth="3" strokeDasharray="6,3"
                        style={{ pointerEvents: 'none' }}>
                    <animate attributeName="opacity" values="0.8;0.4;0.8" dur="2s" repeatCount="indefinite"/>
                  </rect>
                )}
                
                {chartRefHighlightState?.type === 'sign' && pos.sign === parseInt(chartRefHighlightState.value) - 1 && (
                  <rect x={pos.x + 2} y={pos.y + 2} width={pos.width - 4} height={pos.height - 4}
                        fill="rgba(156, 39, 176, 0.3)" stroke="#9c27b0" strokeWidth="3" strokeDasharray="4,2"
                        style={{ pointerEvents: 'none' }}>
                    <animate attributeName="opacity" values="0.7;0.3;0.7" dur="1.8s" repeatCount="indefinite"/>
                  </rect>
                )}
                {/* House number */}
                <text x={pos.x + 8} y={pos.y + 18} 
                      fontSize="12" 
                      fill={customAscendant === pos.sign ? 'var(--color-brand)' : 'var(--color-chart-text-muted, var(--color-text-muted))'}
                      fontWeight={customAscendant === pos.sign ? "900" : "bold"}
                      style={{ pointerEvents: 'none' }}>
                  {houseNumber}
                </text>
                
                {/* Ascendant marker for house 1 */}
                {houseNumber === 1 && (
                  <g style={{ pointerEvents: 'none' }}>
                    <text x={pos.x + pos.width - 8} y={pos.y + pos.height - 20} 
                          fontSize="9" fill="#e91e63" fontWeight="900" textAnchor="end">
                      ASC
                    </text>
                    {chartData.ascendant && (
                      <text x={pos.x + pos.width - 8} y={pos.y + pos.height - 8} 
                            fontSize="7" fill="var(--color-chart-text-muted, var(--color-text-muted))" fontWeight="500" textAnchor="end">
                        {formatDegreeDMS(chartData.ascendant % 30)} {getShortNakshatra(chartData.ascendant)}
                      </text>
                    )}
                  </g>
                )}
                
                {/* Sign name */}
                <text x={pos.x + pos.width - 8} y={pos.y + 18} 
                      fontSize="10" fill="var(--color-chart-text-muted, var(--color-text-muted))"
                      textAnchor="end"
                      style={{ pointerEvents: 'none' }}>
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
                    // Stack all multiple planets vertically with increased spacing for 2-line layout
                    planetX = pos.x + pos.width / 2;
                    const lineHeight = totalPlanets > 4 ? 22 : totalPlanets > 2 ? 24 : 26;
                    const startY = pos.y + pos.height / 2 + (isDoubleDigitHouse ? 5 : 2) - ((totalPlanets - 1) * lineHeight / 2);
                    planetY = startY + (pIndex * lineHeight);
                  }
                  
                  const aspectingPlanet = aspectsHighlight.show && aspectsHighlight.aspectingPlanets?.find(p => p.name === planet.name);
                  
                  return (
                    <g key={pIndex}>
                      {aspectingPlanet && (
                        <circle cx={planetX} cy={planetY} r="8" 
                                fill="none" 
                                stroke={aspectingPlanet.isPositive ? '#4caf50' : '#f44336'} 
                                strokeWidth="1.5" 
                                strokeDasharray="2,1"
                                style={{ pointerEvents: 'none' }}/>
                      )}
                      
                      {/* Chart reference planet highlighting */}
                      {chartRefHighlightState?.type === 'planet' && 
                       planet.name.toLowerCase() === chartRefHighlightState.value.toLowerCase() && (
                        <circle cx={planetX} cy={planetY} r="12" 
                                fill="rgba(255, 107, 53, 0.4)" 
                                stroke="#ff6b35" 
                                strokeWidth="2" 
                                strokeDasharray="3,1"
                                style={{ pointerEvents: 'none' }}>
                          <animate attributeName="r" values="10;15;10" dur="1.5s" repeatCount="indefinite"/>
                          <animate attributeName="opacity" values="0.8;0.3;0.8" dur="1.5s" repeatCount="indefinite"/>
                        </circle>
                      )}
                      {(() => {
                        const isLit = highlightedPlanetSet?.has(planet.name.toLowerCase());
                        const fontPx = totalPlanets > 4 ? 8 : totalPlanets > 2 ? 10 : totalPlanets > 1 ? 12 : 14;
                        if (!isLit) return null;
                        return (
                          <rect
                            x={planetX - fontPx * 0.85}
                            y={planetY - 5}
                            width={fontPx * 1.7}
                            height={2}
                            rx={1}
                            fill="#9f1239"
                            opacity={0.85}
                            style={{ pointerEvents: 'none' }}
                          />
                        );
                      })()}
                      {/* Planet symbol */}
                      <text x={planetX} 
                            y={planetY - 8} 
                            fontSize={totalPlanets > 4 ? "8" : totalPlanets > 2 ? "10" : totalPlanets > 1 ? "12" : "14"} 
                            fill={highlightedPlanetSet?.has(planet.name.toLowerCase()) ? '#9f1239' : getPlanetColor(planet)}
                            fontWeight="900"
                            textAnchor="middle"
                            style={{ cursor: 'pointer' }}
                          onMouseEnter={(e) => {
                            if (isTouchDevice) return;
                            const tooltipText = `${planet.name}: ${formatDegreeDMS(parseFloat(planet.degree))} in ${planet.nakshatra}`;
                            const isRightSide = pos.x >= 150;
                            const offsetX = isRightSide ? -120 : 10;
                            const fontSize = totalPlanets > 4 ? 7 : totalPlanets > 2 ? 9 : totalPlanets > 1 ? 10 : 13;
                            const offsetY = fontSize + 2;
                            setTooltip({ show: true, x: planetX + offsetX, y: planetY - offsetY, text: tooltipText });
                          }}
                          onMouseLeave={() => {
                            if (isTouchDevice) return;
                            setTooltip({ show: false, x: 0, y: 0, text: '' });
                          }}
                          onClick={(e) => handleRashiClick(e, pos.sign, houseNumber)}
                          onTouchStart={(e) => {
                            setIsTouchDevice(true);
                            handleRashiClick(e, pos.sign, houseNumber);
                          }}
                          onContextMenu={(e) => handleRashiClick(e, pos.sign, houseNumber)}>
                        {getPlanetSymbolWithStatus(planet)}
                      </text>
                      {/* Degree and Nakshatra combined */}
                      {showDegreeNakshatra && (
                        <text x={planetX} 
                              y={planetY + 8} 
                              fontSize={totalPlanets > 4 ? "6" : totalPlanets > 2 ? "7" : totalPlanets > 1 ? "8" : "9"} 
                              fill="var(--color-chart-text-muted, var(--color-text-muted))"
                              fontWeight="500"
                              textAnchor="middle"
                              style={{ cursor: 'pointer' }}
                            onClick={(e) => handleRashiClick(e, pos.sign, houseNumber)}
                            onContextMenu={(e) => handleRashiClick(e, pos.sign, houseNumber)}>
                          {planet.formattedDegree} {planet.shortNakshatra}
                        </text>
                      )}
                    </g>
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
      
      <HouseContextMenu
        isOpen={houseContextMenu.show}
        position={{ x: houseContextMenu.x, y: houseContextMenu.y }}
        houseNumber={houseContextMenu.houseNumber}
        signName={houseContextMenu.signName}
        onClose={() => setHouseContextMenu({ show: false, x: 0, y: 0, houseNumber: null, signName: null })}
        onMakeAscendant={handleMakeAscendant}
        onShowAspects={handleShowAspects}
        onHouseAnalysis={handleHouseAnalysis}
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
        getPlanetsInHouse={(houseIndex) => {
          const signIndex = gridPositions.find(p => getHouseNumber(p.sign) === houseIndex + 1)?.sign || -1;
          return getPlanetsInSign(signIndex);
        }}
        getRashiForHouse={(houseIndex) => {
          return gridPositions.find(p => getHouseNumber(p.sign) === houseIndex + 1)?.sign || -1;
        }}
      />

      <HouseInsightPopup
        isOpen={houseInsight.show}
        onClose={() => setHouseInsight({ show: false, houseNumber: null, signName: null, rashiIndex: null })}
        houseNumber={houseInsight.houseNumber}
        signName={houseInsight.signName}
        rashiIndex={houseInsight.rashiIndex}
        chartData={chartData}
        birthData={birthData}
        chartId={chartId}
        planetsInHouse={
          houseInsight.rashiIndex != null
            ? getPlanetsInSign(houseInsight.rashiIndex)
            : []
        }
        onMakeAscendant={handleMakeAscendant}
      />

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
            <p><strong>Occupancy:</strong> {getPlanetsInSign(gridPositions.find(p => getHouseNumber(p.sign) === houseStrengthModal.houseNumber)?.sign || -1).length} planets</p>
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

export default SouthIndianChart;
