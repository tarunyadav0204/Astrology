import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, Alert } from 'react-native';
import Svg, { Rect, Polygon, Line, Text as SvgText, G, Defs, LinearGradient, Stop, Circle, TSpan } from 'react-native-svg';
import HouseAnalysisModal from './HouseAnalysisModal';

const NorthIndianChart = ({ chartData, birthData }) => {
  const [tooltip, setTooltip] = useState({ show: false, text: '' });
  const [contextMenu, setContextMenu] = useState({ show: false, houseNumber: null, signName: null });
  const [componentLayout, setComponentLayout] = useState({ width: 400, height: 400 });
  const [customAscendant, setCustomAscendant] = useState(null);
  const [aspectsHighlight, setAspectsHighlight] = useState({ show: false, houseNumber: null, aspectingPlanets: [] });
  const [houseAnalysisModal, setHouseAnalysisModal] = useState({ show: false, houseNumber: null, signName: null });

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

  const handlePlanetPress = (planet) => {
    console.log('Planet pressed:', planet.name);
    const planetData = chartData.planets?.[planet.name];
    const nakshatra = planetData?.longitude ? getNakshatra(planetData.longitude) : 'Unknown';
    const tooltipText = `${planet.name}: ${planet.degree}° in ${nakshatra}`;
    setTooltip({ show: true, text: tooltipText });
    setTimeout(() => setTooltip({ show: false, text: '' }), 2000);
  };

  const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
  
  const handleRashiPress = (houseNumber, rashiIndex) => {
    console.log('Rashi pressed: House', houseNumber, 'Sign', rashiNames[rashiIndex]);
    setTimeout(() => {
      setContextMenu({ show: true, houseNumber, signName: rashiNames[rashiIndex] });
    }, 200);
  };

  const findTouchedPlanet = (touchX, touchY) => {
    // Touch coordinates are already in SVG coordinate system
    const svgX = touchX;
    const svgY = touchY;
    for (let houseNumber = 1; houseNumber <= 12; houseNumber++) {
      const houseIndex = houseNumber - 1;
      const planetsInHouse = getPlanetsInHouse(houseIndex);
      const houseData = getHouseData(houseNumber);
      
      for (let pIndex = 0; pIndex < planetsInHouse.length; pIndex++) {
        const planet = planetsInHouse[pIndex];
        const totalPlanets = planetsInHouse.length;
        let planetX, planetY;
        
        // Use exact same positioning logic as rendering
        if (totalPlanets === 1) {
          if (houseNumber === 1) {
            planetX = houseData.center.x;
            planetY = houseData.center.y + 20;
          } else if ([3, 4, 5].includes(houseNumber)) {
            planetX = houseData.center.x - 15;
            planetY = houseData.center.y + 5;
          } else if ([6, 7, 8].includes(houseNumber)) {
            planetX = houseData.center.x;
            planetY = houseData.center.y + 25;
          } else if ([9, 10, 11].includes(houseNumber)) {
            planetX = houseData.center.x + 15;
            planetY = houseData.center.y + 5;
          } else if (houseNumber === 12) {
            planetX = houseData.center.x;
            planetY = houseData.center.y + 15;
          } else {
            planetX = houseData.center.x;
            planetY = houseData.center.y - 15;
          }
        } else if (totalPlanets <= 4) {
          const row = Math.floor(pIndex / 2);
          const col = pIndex % 2;
          const spacing = 16;
          const rowSpacing = 18;
          
          if (houseNumber === 1) {
            planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
            planetY = houseData.center.y + 15 + (row * rowSpacing);
          } else if ([3, 4, 5].includes(houseNumber)) {
            planetX = houseData.center.x - 25 + (col === 0 ? -spacing : spacing);
            planetY = houseData.center.y + (row * rowSpacing);
          } else if ([6, 7, 8].includes(houseNumber)) {
            planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
            planetY = houseData.center.y + 20 + (row * rowSpacing);
          } else if ([9, 10, 11].includes(houseNumber)) {
            planetX = houseData.center.x + 20 + (col === 0 ? -spacing : spacing);
            planetY = houseData.center.y + (row * rowSpacing);
          } else if (houseNumber === 12) {
            planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
            planetY = houseData.center.y - 5 + (row * rowSpacing);
          } else {
            planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
            planetY = houseData.center.y - 30 + (row * rowSpacing);
          }
        } else {
          const row = Math.floor(pIndex / 3);
          const col = pIndex % 3;
          const spacing = 12;
          const rowSpacing = 15;
          
          if (houseNumber === 1) {
            planetX = houseData.center.x + (col - 1) * spacing;
            planetY = houseData.center.y + 10 + (row * rowSpacing);
          } else if ([3, 4, 5].includes(houseNumber)) {
            planetX = houseData.center.x - 30 + (col * spacing);
            planetY = houseData.center.y - 5 + (row * rowSpacing);
          } else if ([6, 7, 8].includes(houseNumber)) {
            planetX = houseData.center.x + (col - 1) * spacing;
            planetY = houseData.center.y + 15 + (row * rowSpacing);
          } else if ([9, 10, 11].includes(houseNumber)) {
            planetX = houseData.center.x + 15 + (col * spacing);
            planetY = houseData.center.y - 5 + (row * rowSpacing);
          } else if (houseNumber === 12) {
            planetX = houseData.center.x + (col - 1) * spacing;
            planetY = houseData.center.y - 10 + (row * rowSpacing);
          } else {
            planetX = houseData.center.x + (col - 1) * spacing;
            planetY = houseData.center.y - 35 + (row * rowSpacing);
          }
        }
        
        const distance = Math.sqrt(Math.pow(svgX - planetX, 2) + Math.pow(svgY - planetY, 2));
        if (distance < 20) {
          console.log('Planet touched:', planet.name, 'at', planetX, planetY);
          return planet;
        }
      }
    }
    return null;
  };
  
  const findTouchedRashi = (touchX, touchY) => {
    // Touch coordinates are already in SVG coordinate system
    const svgX = touchX;
    const svgY = touchY;
    for (let houseNumber = 1; houseNumber <= 12; houseNumber++) {
      const houseIndex = houseNumber - 1;
      const rashiIndex = getRashiForHouse(houseIndex);
      const houseData = getHouseData(houseNumber);
      
      // Use exact same positioning as rendering
      const rashiX = houseNumber === 1 ? houseData.center.x - 5 :
                     houseNumber === 3 ? houseData.center.x + 10 :
                     houseNumber === 4 ? houseData.center.x + 40 :
                     houseNumber === 5 ? houseData.center.x + 10 :
                     houseNumber === 6 ? houseData.center.x - 5 :
                     houseNumber === 7 ? houseData.center.x - 5 :
                     houseNumber === 8 ? houseData.center.x - 5 :
                     houseNumber === 9 ? houseData.center.x - 20 :
                     houseNumber === 10 ? houseData.center.x - 40 :
                     houseNumber === 11 ? houseData.center.x - 15 :
                     houseData.center.x - 5;
      
      const rashiY = houseNumber === 1 ? houseData.center.y - 5 :
                     houseNumber === 6 ? houseData.center.y - 10 :
                     houseNumber === 7 ? houseData.center.y - 10 :
                     houseNumber === 8 ? houseData.center.y - 10 :
                     [2, 12].includes(houseNumber) ? houseData.center.y + 35 : houseData.center.y + 5;
      
      const distance = Math.sqrt(Math.pow(svgX - rashiX, 2) + Math.pow(svgY - rashiY, 2));
      if (distance < 25) {
        console.log('Rashi touched:', houseNumber, rashiIndex, 'at', rashiX, rashiY);
        return { houseNumber, rashiIndex };
      }
    }
    return null;
  };

  const handleContextMenuAction = (action) => {
    setContextMenu({ show: false, houseNumber: null, signName: null });
    
    setTimeout(() => {
      if (action === 'makeAscendant') {
        const rashiIndex = rashiNames.indexOf(contextMenu.signName);
        setCustomAscendant(rashiIndex);
        Alert.alert('Chart Rotated', `${contextMenu.signName} is now the ascendant`);
      } else if (action === 'showAspects') {
        handleShowAspects(contextMenu.houseNumber, contextMenu.signName);
      } else if (action === 'significations') {
        const significations = {
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
        };
        Alert.alert(
          `House ${contextMenu.houseNumber} Significations (${contextMenu.signName})`,
          significations[contextMenu.houseNumber]
        );
      } else if (action === 'analysis') {
        setHouseAnalysisModal({ show: true, houseNumber: contextMenu.houseNumber, signName: contextMenu.signName });
      }
    }, 100);
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

  const getHouseData = (houseNum) => {
    const houseData = {
      1: { center: { x: 200, y: 110 } },
      2: { center: { x: 110, y: 70 } },
      3: { center: { x: 70, y: 110 } },
      4: { center: { x: 110, y: 200 } },
      5: { center: { x: 70, y: 290 } },
      6: { center: { x: 110, y: 330 } },
      7: { center: { x: 200, y: 290 } },
      8: { center: { x: 290, y: 330 } },
      9: { center: { x: 330, y: 290 } },
      10: { center: { x: 290, y: 200 } },
      11: { center: { x: 330, y: 110 } },
      12: { center: { x: 290, y: 70 } }
    };
    return houseData[houseNum];
  };

  const getRashiForHouse = (houseIndex) => {
    if (!chartData.houses || !chartData.houses[houseIndex]) return houseIndex;
    
    if (customAscendant !== null) {
      return (customAscendant + houseIndex) % 12;
    }
    
    return chartData.houses[houseIndex].sign;
  };

  const getPlanetStatus = (planet) => {
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

  const getPlanetColor = (planet) => {
    const status = getPlanetStatus(planet);
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
    if (status === 'exalted') symbol += '↑';
    if (status === 'debilitated') symbol += '↓';
    return symbol;
  };

  const getPlanetsInHouse = (houseIndex) => {
    if (!chartData.planets) return [];
    
    const rashiForThisHouse = getRashiForHouse(houseIndex);
    const planets = ['Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa', 'Ra', 'Ke', 'Gu', 'Ma'];
    
    return Object.entries(chartData.planets)
      .filter(([name, data]) => data.sign === rashiForThisHouse)
      .map(([name, data]) => {
        const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi'];
        const planetIndex = planetNames.indexOf(name);
        return {
          symbol: planets[planetIndex] || name.substring(0, 2),
          name: name,
          degree: data.degree ? data.degree.toFixed(2) : '0.00',
          longitude: data.longitude || 0
        };
      });
  };

  return (
    <View style={styles.container}>
      {(customAscendant !== null || aspectsHighlight.show) && (
        <View style={styles.buttonContainer}>
          {customAscendant !== null && (
            <TouchableOpacity 
              style={styles.resetButton}
              onPress={() => setCustomAscendant(null)}
            >
              <Text style={styles.resetButtonText}>Reset</Text>
            </TouchableOpacity>
          )}
          {aspectsHighlight.show && (
            <TouchableOpacity 
              style={styles.aspectsButton}
              onPress={() => setAspectsHighlight({ show: false, houseNumber: null, aspectingPlanets: [] })}
            >
              <Text style={styles.aspectsButtonText}>Clear Aspects</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
        <Svg viewBox="0 0 400 400" style={styles.svg}>
        <Defs>
          <LinearGradient id="chartGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <Stop offset="0%" stopColor="rgba(233, 30, 99, 0.1)" />
            <Stop offset="50%" stopColor="rgba(255, 111, 0, 0.1)" />
            <Stop offset="100%" stopColor="rgba(255, 255, 255, 0.2)" />
          </LinearGradient>
        </Defs>

        {/* Outer square border */}
        <Rect x="20" y="20" width="360" height="360" 
              fill="url(#chartGradient)" stroke="#e91e63" strokeWidth="3"/>
        
        {/* Inner diamond border */}
        <Polygon points="200,20 380,200 200,380 20,200" 
                 fill="none" stroke="#ff6f00" strokeWidth="3"/>
        
        {/* Diagonal lines creating 12 houses */}
        <Line x1="20" y1="20" x2="380" y2="380" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="380" y1="20" x2="20" y2="380" stroke="#ff8a65" strokeWidth="2"/>

        {/* Houses */}
        {[1,2,3,4,5,6,7,8,9,10,11,12].map((houseNumber) => {
          const houseIndex = houseNumber - 1;
          const rashiIndex = getRashiForHouse(houseIndex);
          const planetsInHouse = getPlanetsInHouse(houseIndex);
          const houseData = getHouseData(houseNumber);
          
          return (
            <G key={houseNumber}>
              {/* House highlighting for aspects */}
              {aspectsHighlight.show && aspectsHighlight.houseNumber === houseNumber && (
                <Circle cx={houseData.center.x} cy={houseData.center.y} r="35" 
                        fill="rgba(233, 30, 99, 0.2)" stroke="#e91e63" strokeWidth="3" strokeDasharray="5,5"/>
              )}
              
              {/* Rashi number */}
              <SvgText 
                x={houseNumber === 1 ? houseData.center.x - 5 :
                   houseNumber === 3 ? houseData.center.x + 10 :
                   houseNumber === 4 ? houseData.center.x + 40 :
                   houseNumber === 5 ? houseData.center.x + 10 :
                   houseNumber === 6 ? houseData.center.x - 5 :
                   houseNumber === 7 ? houseData.center.x - 5 :
                   houseNumber === 8 ? houseData.center.x - 5 :
                   houseNumber === 9 ? houseData.center.x - 20 :
                   houseNumber === 10 ? houseData.center.x - 40 :
                   houseNumber === 11 ? houseData.center.x - 15 :
                   houseData.center.x - 5} 
                y={houseNumber === 1 ? houseData.center.y - 5 :
                   houseNumber === 6 ? houseData.center.y - 10 :
                   houseNumber === 7 ? houseData.center.y - 10 :
                   houseNumber === 8 ? houseData.center.y - 10 :
                   [2, 12].includes(houseNumber) ? houseData.center.y + 35 : houseData.center.y + 5} 
                fontSize="18" 
                fill={customAscendant === rashiIndex ? "#e91e63" : "#333"} 
                fontWeight={customAscendant === rashiIndex ? "900" : "bold"}
                onTouchStart={(e) => {
                  e.stopPropagation();
                  console.log('Rashi touched:', rashiIndex + 1);
                  handleRashiPress(houseNumber, rashiIndex);
                }}>
                {rashiIndex + 1}
              </SvgText>
              
              {/* Planets */}
              {planetsInHouse.map((planet, pIndex) => {
                const totalPlanets = planetsInHouse.length;
                let planetX, planetY;
                
                if (totalPlanets === 1) {
                  if (houseNumber === 1) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y + 20;
                  } else if ([3, 4, 5].includes(houseNumber)) {
                    planetX = houseData.center.x - 15;
                    planetY = houseData.center.y + 5;
                  } else if ([6, 7, 8].includes(houseNumber)) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y + 25;
                  } else if ([9, 10, 11].includes(houseNumber)) {
                    planetX = houseData.center.x + 15;
                    planetY = houseData.center.y + 5;
                  } else if (houseNumber === 12) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y + 15;
                  } else {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y - 15;
                  }
                } else if (totalPlanets <= 4) {
                  const row = Math.floor(pIndex / 2);
                  const col = pIndex % 2;
                  const spacing = 16;
                  const rowSpacing = 18;
                  
                  if (houseNumber === 1) {
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y + 15 + (row * rowSpacing);
                  } else if ([3, 4, 5].includes(houseNumber)) {
                    planetX = houseData.center.x - 25 + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y + (row * rowSpacing);
                  } else if ([6, 7, 8].includes(houseNumber)) {
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y + 20 + (row * rowSpacing);
                  } else if ([9, 10, 11].includes(houseNumber)) {
                    planetX = houseData.center.x + 20 + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y + (row * rowSpacing);
                  } else if (houseNumber === 12) {
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y - 5 + (row * rowSpacing);
                  } else {
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    planetY = houseData.center.y - 30 + (row * rowSpacing);
                  }
                } else {
                  const row = Math.floor(pIndex / 3);
                  const col = pIndex % 3;
                  const spacing = 12;
                  const rowSpacing = 15;
                  
                  if (houseNumber === 1) {
                    planetX = houseData.center.x + (col - 1) * spacing;
                    planetY = houseData.center.y + 10 + (row * rowSpacing);
                  } else if ([3, 4, 5].includes(houseNumber)) {
                    planetX = houseData.center.x - 30 + (col * spacing);
                    planetY = houseData.center.y - 5 + (row * rowSpacing);
                  } else if ([6, 7, 8].includes(houseNumber)) {
                    planetX = houseData.center.x + (col - 1) * spacing;
                    planetY = houseData.center.y + 15 + (row * rowSpacing);
                  } else if ([9, 10, 11].includes(houseNumber)) {
                    planetX = houseData.center.x + 15 + (col * spacing);
                    planetY = houseData.center.y - 5 + (row * rowSpacing);
                  } else if (houseNumber === 12) {
                    planetX = houseData.center.x + (col - 1) * spacing;
                    planetY = houseData.center.y - 10 + (row * rowSpacing);
                  } else {
                    planetX = houseData.center.x + (col - 1) * spacing;
                    planetY = houseData.center.y - 35 + (row * rowSpacing);
                  }
                }
                
                const aspectingPlanet = aspectsHighlight.show && aspectsHighlight.aspectingPlanets?.find(p => p.name === planet.name);
                
                return (
                  <G key={pIndex}>
                    {aspectingPlanet && (
                      <Circle cx={planetX} cy={planetY} r="12" 
                              fill="none" 
                              stroke={aspectingPlanet.isPositive ? '#4caf50' : '#f44336'} 
                              strokeWidth="2" 
                              strokeDasharray="3,2"/>
                    )}
                    <SvgText 
                      x={planetX} 
                      y={planetY} 
                      fontSize={totalPlanets > 4 ? "10" : totalPlanets > 2 ? "12" : "14"} 
                      fill={getPlanetColor(planet)}
                      fontWeight="900"
                      textAnchor="middle"
                      onTouchStart={(e) => {
                        e.stopPropagation();
                        console.log('Planet touched:', planet.name);
                        handlePlanetPress(planet);
                      }}>
                      {getPlanetSymbolWithStatus(planet)}
                    </SvgText>
                  </G>
                );
              })}
            </G>
          );
        })}
        </Svg>
      
      {/* Planet Tooltip */}
      {tooltip.show && (
        <View style={styles.tooltip}>
          <Text style={styles.tooltipText}>{tooltip.text}</Text>
        </View>
      )}
      
      {/* Rashi Context Menu */}
      <Modal
        visible={contextMenu.show}
        transparent={true}
        animationType="fade"
      >
        <TouchableOpacity 
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setContextMenu({ show: false, houseNumber: null, signName: null })}
        >
          <TouchableOpacity 
            style={styles.contextMenu}
            activeOpacity={1}
            onPress={(e) => e.stopPropagation()}
          >
            <Text style={styles.contextMenuTitle}>
              House {contextMenu.houseNumber} ({contextMenu.signName})
            </Text>
            <TouchableOpacity 
              style={styles.contextMenuItem}
              onPress={() => handleContextMenuAction('makeAscendant')}
            >
              <Text style={styles.contextMenuText}>🔄 Make Ascendant</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.contextMenuItem}
              onPress={() => handleContextMenuAction('showAspects')}
            >
              <Text style={styles.contextMenuText}>👁️ Show Aspects</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.contextMenuItem}
              onPress={() => handleContextMenuAction('analysis')}
            >
              <Text style={styles.contextMenuText}>📊 House Analysis</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.contextMenuItem}
              onPress={() => handleContextMenuAction('significations')}
            >
              <Text style={styles.contextMenuText}>🌟 Significations</Text>
            </TouchableOpacity>
          </TouchableOpacity>
        </TouchableOpacity>
      </Modal>
      
      <HouseAnalysisModal
        isOpen={houseAnalysisModal.show}
        onClose={() => setHouseAnalysisModal({ show: false, houseNumber: null, signName: null })}
        houseNumber={houseAnalysisModal.houseNumber}
        signName={houseAnalysisModal.signName}
        chartData={chartData}
        birthData={birthData}
        getPlanetsInHouse={getPlanetsInHouse}
        getRashiForHouse={getRashiForHouse}
      />
      
      <Text style={styles.instructionText}>
        Touch planets to see Nakshatra and Degree. Touch signs to see more options.
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'white',
    marginHorizontal: 0,

  },
  svg: {
    width: '100%',
    height: '100%',
  },
  tooltip: {
    position: 'absolute',
    top: 20,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(233, 30, 99, 0.9)',
    padding: 12,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  tooltipText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  contextMenu: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    minWidth: 250,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 12,
  },
  contextMenuTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#e91e63',
    textAlign: 'center',
    marginBottom: 15,
  },
  contextMenuItem: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginVertical: 4,
    backgroundColor: '#f8f9fa',
  },
  contextMenuText: {
    fontSize: 14,
    color: '#333',
    fontWeight: '600',
  },
  resetButton: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: '#ff6f00',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    zIndex: 10,
  },
  resetButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  buttonContainer: {
    position: 'absolute',
    top: 10,
    right: 10,
    flexDirection: 'row',
    gap: 4,
    zIndex: 10,
  },
  aspectsButton: {
    backgroundColor: '#2196f3',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  aspectsButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  instructionText: {
    textAlign: 'center',
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
    marginTop: 8,
    paddingHorizontal: 0,
  },
});

export default NorthIndianChart;