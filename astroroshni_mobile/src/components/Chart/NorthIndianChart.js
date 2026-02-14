import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, Alert } from 'react-native';
import Svg, { Rect, Polygon, Line, Text as SvgText, G, Defs, LinearGradient, Stop, Circle } from 'react-native-svg';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';

const NorthIndianChart = ({ chartData, birthData, showDegreeNakshatra = true, cosmicTheme = false, rotatedAscendant = null, onRotate, showKarakas = false, karakas = null, highlightHouse = null, glowAnimation = null, hideInstructions = false }) => {
  const { theme, colors } = useTheme();
  const { t } = useTranslation();
  
  // console.log('NorthIndianChart - showKarakas:', showKarakas, 'karakas:', karakas ? Object.keys(karakas) : 'null');
  
  const [tooltip, setTooltip] = useState({ show: false, text: '' });
  const [contextMenu, setContextMenu] = useState({ show: false, rashiIndex: null, signName: null });
  const [aspectsHighlight, setAspectsHighlight] = useState({ show: false, houseNumber: null, aspectingPlanets: [] });

  const handlePlanetPress = (planet) => {
    const tooltipText = `${planet.name}: ${planet.degree}° in ${planet.nakshatra}`;
    setTooltip({ show: true, text: tooltipText });
    setTimeout(() => setTooltip({ show: false, text: '' }), 2000);
  };

  const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
  
  const handleRashiPress = (rashiIndex) => {
    setContextMenu({ show: true, rashiIndex, signName: rashiNames[rashiIndex] });
  };

  const getHouseGlowColor = (houseNum) => {
    if (highlightHouse !== houseNum) return null;
    return cosmicTheme ? 'rgba(255, 215, 0, 0.6)' : 'rgba(255, 107, 53, 0.6)';
  };

  const getHouseData = (houseNum) => {
    // North Indian chart layout: counter-clockwise from ascendant at top
    const houseData = {
      1: { center: { x: 200, y: 110 } },  // Top center diamond (Ascendant)
      2: { center: { x: 110, y: 70 } },   // Top-left triangle
      3: { center: { x: 70, y: 110 } },   // Left-top triangle
      4: { center: { x: 110, y: 200 } },  // Left center diamond (IC)
      5: { center: { x: 70, y: 290 } },   // Left-bottom triangle
      6: { center: { x: 110, y: 330 } },  // Bottom-left triangle
      7: { center: { x: 200, y: 290 } },  // Bottom center diamond (Descendant)
      8: { center: { x: 290, y: 330 } },  // Bottom-right triangle
      9: { center: { x: 330, y: 290 } },  // Right-bottom triangle
      10: { center: { x: 290, y: 200 } }, // Right center diamond (MC)
      11: { center: { x: 330, y: 110 } }, // Right-top triangle
      12: { center: { x: 290, y: 70 } }   // Top-right triangle
    };
    return houseData[houseNum];
  };

  const getRashiForHouse = (houseIndex) => {
    if (!chartData.houses || !chartData.houses[houseIndex]) return houseIndex;
    
    if (rotatedAscendant !== null) {
      return (rotatedAscendant + houseIndex) % 12;
    }
    
    return chartData.houses[houseIndex].sign;
  };

  const getHouseForRashi = (rashiIndex) => {
    if (!chartData.houses) return null;
    
    // Find which house contains this rashi
    for (let i = 0; i < chartData.houses.length; i++) {
      if (chartData.houses[i].sign === rashiIndex) {
        return i + 1; // Return house number (1-12)
      }
    }
    return null;
  };

  // Get the actual ascendant sign from chart data
  const getAscendantSign = () => {
    if (!chartData || !chartData.houses || !chartData.houses[0]) {
      return 4; // Fallback to Leo
    }
    // First house sign is the ascendant
    return chartData.houses[0].sign;
  };

  const getPlanetStatus = (planet) => {
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

  const getPlanetColor = (planet) => {
    // InduLagna has special purple color
    if (planet.name === 'InduLagna') return '#9c27b0';
    
    const status = getPlanetStatus(planet);
    if (status === 'exalted') return '#22c55e';
    if (status === 'debilitated') return '#ef4444';
    
    // Use theme colors for normal planets
    return cosmicTheme ? (theme === 'dark' ? 'rgba(255, 255, 255, 0.95)' : 'rgba(0, 0, 0, 0.9)') : (theme === 'dark' ? '#fff' : '#2d3436');
  };

  const getPlanetSymbolWithStatus = (planet) => {
    const status = getPlanetStatus(planet);
    const planetData = chartData.planets?.[planet.name];
    const isRetrograde = planetData?.retrograde;
    
    let symbol = planet.symbol;
    // Don't show (R) for Rahu and Ketu as they are always retrograde
    if (isRetrograde && planet.name !== 'Rahu' && planet.name !== 'Ketu') symbol += '(R)';
    if (status === 'exalted') symbol += '↑';
    if (status === 'debilitated') symbol += '↓';
    
    // Add Karaka abbreviation if showKarakas is true
    if (showKarakas && karakas && typeof karakas === 'object') {
      const karaka = Object.entries(karakas).find(([_, data]) => data?.planet === planet.name);
      if (karaka) {
        const karakaAbbr = {
          'Atmakaraka': 'AK',
          'Amatyakaraka': 'AmK',
          'Bhratrukaraka': 'BK',
          'Matrukaraka': 'MK',
          'Putrakaraka': 'PK',
          'Gnatikaraka': 'GK',
          'Darakaraka': 'DK'
        }[karaka[0]];
        if (karakaAbbr) symbol += `(${karakaAbbr})`;
      }
    }
    
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
    const planetsInHouse = [];
    
    // Add regular planets (exclude InduLagna as it's handled separately)
    Object.entries(chartData.planets)
      .filter(([name, data]) => data.sign === rashiForThisHouse && name !== 'InduLagna')
      .forEach(([name, data]) => {
        planetsInHouse.push({
          symbol: t(`planets.${name}`, name.substring(0, 2)),
          name: name,
          degree: data.degree ? data.degree.toFixed(2) : '0.00',
          longitude: data.longitude || 0,
          nakshatra: getNakshatra(data.longitude || 0),
          shortNakshatra: getShortNakshatra(data.longitude || 0),
          formattedDegree: formatDegree(data.degree || 0)
        });
      });
    
    // Add InduLagna if it's in this house
    if (chartData.planets?.InduLagna && chartData.planets.InduLagna.sign === rashiForThisHouse) {
      planetsInHouse.push({
        symbol: t('planets.InduLagna', 'IL'),
        name: 'InduLagna',
        degree: chartData.planets.InduLagna.degree ? chartData.planets.InduLagna.degree.toFixed(2) : '0.00',
        longitude: chartData.planets.InduLagna.longitude || 0,
        nakshatra: getNakshatra(chartData.planets.InduLagna.longitude || 0),
        shortNakshatra: getShortNakshatra(chartData.planets.InduLagna.longitude || 0),
        formattedDegree: formatDegree(chartData.planets.InduLagna.degree || 0)
      });
    }
    
    return planetsInHouse;
  };

  return (
    <View style={styles.container}>
      <Svg viewBox="0 0 400 400" style={styles.svg}>
        <Defs>
          <LinearGradient id="chartGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            {cosmicTheme ? (
              theme === 'dark' ? [
                <Stop key="0" offset="0%" stopColor="rgba(255, 255, 255, 0.15)" />,
                <Stop key="50" offset="50%" stopColor="rgba(255, 255, 255, 0.08)" />,
                <Stop key="100" offset="100%" stopColor="rgba(255, 255, 255, 0.12)" />
              ] : [
                <Stop key="0" offset="0%" stopColor="rgba(249, 115, 22, 0.15)" />,
                <Stop key="50" offset="50%" stopColor="rgba(249, 115, 22, 0.08)" />,
                <Stop key="100" offset="100%" stopColor="rgba(249, 115, 22, 0.12)" />
              ]
            ) : [
                <Stop key="0" offset="0%" stopColor="rgba(255, 255, 255, 0.9)" />,
                <Stop key="50" offset="50%" stopColor="rgba(248, 250, 252, 0.95)" />,
                <Stop key="100" offset="100%" stopColor="rgba(241, 245, 249, 0.9)" />
              ]}
          </LinearGradient>
        </Defs>

        {/* Outer square border */}
        <Rect x="5" y="5" width="390" height="390" 
              fill="transparent" 
              stroke={cosmicTheme ? "rgba(255, 107, 53, 0.9)" : "#e91e63"} 
              strokeWidth={cosmicTheme ? "2" : "3"}
              rx={cosmicTheme ? "16" : "0"}
              ry={cosmicTheme ? "16" : "0"}/>
        
        {cosmicTheme && (
          <Rect x="5" y="5" width="390" height="390" 
                fill="none" 
                stroke="rgba(255, 255, 255, 0.3)" 
                strokeWidth="1"
                rx="16"
                ry="16"/>
        )}
        
        {/* Inner diamond border */}
        <Polygon points="200,5 395,200 200,395 5,200" 
                 fill="none" 
                 stroke={cosmicTheme ? "rgba(255, 215, 0, 0.8)" : "#ff6f00"} 
                 strokeWidth={cosmicTheme ? "2" : "3"}/>
        
        {/* Diagonal lines creating 12 houses */}
        <Line x1="10" y1="10" x2="390" y2="390" 
              stroke={cosmicTheme ? "rgba(255, 138, 101, 0.6)" : "#ff8a65"} 
              strokeWidth="2"/>
        <Line x1="390" y1="10" x2="10" y2="390" 
              stroke={cosmicTheme ? "rgba(255, 138, 101, 0.6)" : "#ff8a65"} 
              strokeWidth="2"/>

        {/* Houses */}
        {[1,2,3,4,5,6,7,8,9,10,11,12].map((houseNumber) => {
          const houseIndex = houseNumber - 1;
          const rashiIndex = getRashiForHouse(houseIndex);
          const planetsInHouse = getPlanetsInHouse(houseIndex);
          const houseData = getHouseData(houseNumber);
          
          return (
            <G key={houseNumber}>
              {/* House glow effect */}
              {highlightHouse === houseNumber && glowAnimation && (
                <Circle
                  cx={houseData.center.x}
                  cy={houseData.center.y}
                  r="60"
                  fill={getHouseGlowColor(houseNumber)}
                  opacity={glowAnimation}
                />
              )}
              
              {/* Rashi number */}
              <SvgText 
                x={houseNumber === 1 ? houseData.center.x - 5 :
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
                fill={cosmicTheme ? 
                  (rashiIndex === chartData.houses[0].sign ? "#ff6b35" : (theme === 'dark' ? "rgba(255, 255, 255, 0.9)" : "rgba(0, 0, 0, 0.8)")) :
                  (rashiIndex === chartData.houses[0].sign ? "#e91e63" : (theme === 'dark' ? "#fff" : "#333"))} 
                fontWeight={rashiIndex === chartData.houses[0].sign ? "900" : "bold"}
                onPress={() => handleRashiPress(rashiIndex)}>
                {rashiIndex + 1}
              </SvgText>
              
              {/* Ascendant marker for house 1 */}
              {houseNumber === 1 && (
                <G>
                  <SvgText 
                    x={houseData.center.x + 25} 
                    y={houseData.center.y + 35} 
                    fontSize="12" 
                    fill={cosmicTheme ? "#ff6b35" : "#e91e63"} 
                    fontWeight="900" 
                    textAnchor="middle">
                    ASC
                  </SvgText>
                  {chartData.ascendant && (
                    <SvgText 
                      x={houseData.center.x + 25} 
                      y={houseData.center.y + 50} 
                      fontSize="8" 
                      fill={cosmicTheme ? (theme === 'dark' ? "rgba(255, 255, 255, 0.7)" : "rgba(0, 0, 0, 0.6)") : (theme === 'dark' ? "rgba(255, 255, 255, 0.7)" : "#666")} 
                      fontWeight="500" 
                      textAnchor="middle">
                      {formatDegree(chartData.ascendant % 30)} {getShortNakshatra(chartData.ascendant)}
                    </SvgText>
                  )}
                </G>
              )}
              

              
              {/* Planets */}
              {planetsInHouse.map((planet, pIndex) => {
                const totalPlanets = planetsInHouse.length;
                let planetX, planetY;
                
                if (totalPlanets === 1) {
                  if (houseNumber === 12) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y - 10;
                  } else if (houseNumber === 1) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y - 15;
                  } else if ([3, 4, 5].includes(houseNumber)) {
                    planetX = houseData.center.x - 35;
                    planetY = houseData.center.y + 10;
                  } else if ([6, 7, 8].includes(houseNumber)) {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y + 30;
                  } else if (houseNumber === 9) {
                    planetX = houseData.center.x + 25;
                    planetY = houseData.center.y - 10;
                  } else if (houseNumber === 10) {
                    planetX = houseData.center.x + 15;
                    planetY = houseData.center.y - 20;
                  } else if (houseNumber === 11) {
                    planetX = houseData.center.x + 15;
                    planetY = houseData.center.y - 5;
                  } else if (houseNumber === 2) {
                    planetX = houseData.center.x - 10;
                    planetY = houseData.center.y - 15;
                  } else {
                    planetX = houseData.center.x;
                    planetY = houseData.center.y - 10;
                  }
                } else if (totalPlanets === 2) {
                  if (houseNumber === 12) {
                    planetX = houseData.center.x + (pIndex === 0 ? -20 : 20);
                    planetY = houseData.center.y - 20;
                  } else if ([3, 5, 9, 11].includes(houseNumber)) {
                    const rowSpacing = 35;
                    if (houseNumber === 3) {
                      planetX = houseData.center.x - 35;
                      planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                    } else if (houseNumber === 5) {
                      planetX = houseData.center.x - 25;
                      planetY = houseData.center.y - 20 + (pIndex * rowSpacing);
                    } else if (houseNumber === 9) {
                      planetX = houseData.center.x + 45;
                      planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                    } else if (houseNumber === 11) {
                      planetX = houseData.center.x + 35;
                      planetY = houseData.center.y - 45 + (pIndex * rowSpacing);
                    }
                  } else {
                    const spacing = 25;
                    if (houseNumber === 2) {
                      planetX = houseData.center.x - 15 + (pIndex === 0 ? -spacing : spacing);
                      planetY = houseData.center.y - 25;
                    } else {
                      planetX = houseData.center.x + (pIndex === 0 ? -spacing : spacing);
                      if (houseNumber === 1) {
                        planetY = houseData.center.y - 20;
                      } else if (houseNumber === 4) {
                        planetY = houseData.center.y + 5;
                      } else if (houseNumber === 6) {
                        planetY = houseData.center.y + 35;
                      } else if (houseNumber === 7) {
                        planetY = houseData.center.y + 25;
                      } else if (houseNumber === 8) {
                        planetY = houseData.center.y + 35;
                      } else if (houseNumber === 10) {
                        planetY = houseData.center.y - 25;
                      } else {
                        planetY = houseData.center.y - 25;
                      }
                    }
                  }
                } else if (totalPlanets === 3) {
                  if (houseNumber === 12) {
                    if (pIndex < 2) {
                      planetX = houseData.center.x + (pIndex === 0 ? -20 : 20);
                      planetY = houseData.center.y - 25;
                    } else {
                      planetX = houseData.center.x;
                      planetY = houseData.center.y;
                    }
                  } else if ([3, 5, 9, 11].includes(houseNumber)) {
                    const rowSpacing = 35;
                    if (houseNumber === 3) {
                      planetX = houseData.center.x - 35;
                      planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                    } else if (houseNumber === 5) {
                      planetX = houseData.center.x - 25;
                      planetY = houseData.center.y - 20 + (pIndex * rowSpacing);
                    } else if (houseNumber === 9) {
                      planetX = houseData.center.x + 45;
                      planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                    } else if (houseNumber === 11) {
                      planetX = houseData.center.x + 35;
                      planetY = houseData.center.y - 45 + (pIndex * rowSpacing);
                    }
                  } else {
                    const row = Math.floor(pIndex / 2);
                    const col = pIndex % 2;
                    const spacing = 25;
                    const rowSpacing = 32;
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    if (houseNumber === 1) {
                      planetY = houseData.center.y - 20 + (row * rowSpacing);
                    } else if (houseNumber === 4) {
                      planetY = houseData.center.y + 5 + (row * rowSpacing);
                    } else if (houseNumber === 6) {
                      planetY = houseData.center.y + 25 + (row * rowSpacing);
                    } else if (houseNumber === 7) {
                      planetY = houseData.center.y - 10 + (row * rowSpacing);
                    } else if (houseNumber === 8) {
                      planetY = houseData.center.y + 25 + (row * rowSpacing);
                    } else if (houseNumber === 10) {
                      planetY = houseData.center.y - 25 + (row * rowSpacing);
                    } else if (houseNumber === 2) {
                      planetY = houseData.center.y - 30 + (row * rowSpacing);
                    } else {
                      planetY = houseData.center.y - 25 + (row * rowSpacing);
                    }
                  }
                } else if (totalPlanets === 4) {
                  if (houseNumber === 12) {
                    const row = Math.floor(pIndex / 2);
                    const col = pIndex % 2;
                    planetX = houseData.center.x + (col === 0 ? -20 : 20);
                    planetY = houseData.center.y - 30 + (row * 25);
                  } else if ([3, 5, 9, 11].includes(houseNumber)) {
                    const rowSpacing = 35;
                    if (houseNumber === 3) {
                      planetX = houseData.center.x - 35;
                      planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                    } else if (houseNumber === 5) {
                      planetX = houseData.center.x - 35;
                      planetY = houseData.center.y - 40 + (pIndex * rowSpacing);
                    } else if (houseNumber === 9) {
                      planetX = houseData.center.x + 45;
                      planetY = houseData.center.y - 30 + (pIndex * rowSpacing);
                    } else if (houseNumber === 11) {
                      planetX = houseData.center.x + 35;
                      planetY = houseData.center.y - 45 + (pIndex * rowSpacing);
                    }
                  } else {
                    const row = Math.floor(pIndex / 2);
                    const col = pIndex % 2;
                    const spacing = 25;
                    const rowSpacing = 32;
                    if (houseNumber === 10) {
                      planetX = houseData.center.x + 10 + (col === 0 ? -spacing : spacing);
                      planetY = houseData.center.y - 25 + (row * rowSpacing);
                    } else {
                      planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                      if (houseNumber === 1) {
                        planetY = houseData.center.y - 20 + (row * rowSpacing);
                      } else if (houseNumber === 4) {
                        planetY = houseData.center.y + 5 + (row * rowSpacing);
                      } else if (houseNumber === 6) {
                        planetY = houseData.center.y + 25 + (row * rowSpacing);
                      } else if (houseNumber === 7) {
                        planetY = houseData.center.y - 10 + (row * rowSpacing);
                      } else if (houseNumber === 8) {
                        planetY = houseData.center.y + 25 + (row * rowSpacing);
                      } else if (houseNumber === 2) {
                        planetY = houseData.center.y - 30 + (row * rowSpacing);
                      } else {
                        planetY = houseData.center.y - 25 + (row * rowSpacing);
                      }
                    }
                  }
                } else if (totalPlanets === 5) {
                  if (houseNumber === 12) {
                    if (pIndex < 3) {
                      planetX = houseData.center.x - 30 + (pIndex * 30);
                      planetY = houseData.center.y - 30;
                    } else {
                      const col = pIndex - 3;
                      planetX = houseData.center.x + (col === 0 ? -20 : 20);
                      planetY = houseData.center.y - 5;
                    }
                  } else if ([3, 5, 9, 11].includes(houseNumber)) {
                    const rowSpacing = 28;
                    if (houseNumber === 3) {
                      planetX = houseData.center.x - 35;
                      planetY = houseData.center.y - 40 + (pIndex * rowSpacing);
                    } else if (houseNumber === 5) {
                      planetX = houseData.center.x - 35;
                      planetY = houseData.center.y - 40 + (pIndex * rowSpacing);
                    } else if (houseNumber === 9) {
                      planetX = houseData.center.x + 45;
                      planetY = houseData.center.y - 40 + (pIndex * rowSpacing);
                    } else if (houseNumber === 11) {
                      planetX = houseData.center.x + 35;
                      planetY = houseData.center.y - 50 + (pIndex * rowSpacing);
                    }
                  } else {
                    const row = Math.floor(pIndex / 2);
                    const col = pIndex % 2;
                    const spacing = 25;
                    const rowSpacing = 26;
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    if (houseNumber === 1) {
                      planetY = houseData.center.y - 25 + (row * rowSpacing);
                    } else if (houseNumber === 4) {
                      planetY = houseData.center.y + 0 + (row * rowSpacing);
                    } else if ([6, 7, 8].includes(houseNumber)) {
                      planetY = houseData.center.y + 20 + (row * rowSpacing);
                    } else if (houseNumber === 10) {
                      planetY = houseData.center.y - 30 + (row * rowSpacing);
                    } else if (houseNumber === 2) {
                      planetY = houseData.center.y - 30 + (row * rowSpacing);
                    } else {
                      planetY = houseData.center.y - 30 + (row * rowSpacing);
                    }
                  }
                } else if (totalPlanets === 6) {
                  if (houseNumber === 12) {
                    const row = Math.floor(pIndex / 3);
                    const col = pIndex % 3;
                    planetX = houseData.center.x - 30 + (col * 30);
                    planetY = houseData.center.y - 35 + (row * 25);
                  } else if ([3, 5, 9, 11].includes(houseNumber)) {
                    const rowSpacing = 24;
                    if (houseNumber === 3) {
                      planetX = houseData.center.x - 35;
                      planetY = houseData.center.y - 45 + (pIndex * rowSpacing);
                    } else if (houseNumber === 5) {
                      planetX = houseData.center.x - 35;
                      planetY = houseData.center.y - 35 + (pIndex * rowSpacing);
                    } else if (houseNumber === 9) {
                      planetX = houseData.center.x + 45;
                      planetY = houseData.center.y - 45 + (pIndex * rowSpacing);
                    } else if (houseNumber === 11) {
                      planetX = houseData.center.x + 35;
                      planetY = houseData.center.y - 55 + (pIndex * rowSpacing);
                    }
                  } else {
                    const row = Math.floor(pIndex / 2);
                    const col = pIndex % 2;
                    const spacing = 25;
                    const rowSpacing = 24;
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    if (houseNumber === 1) {
                      planetY = houseData.center.y - 30 + (row * rowSpacing);
                    } else if (houseNumber === 4) {
                      planetY = houseData.center.y - 5 + (row * rowSpacing);
                    } else if (houseNumber === 6) {
                      planetY = houseData.center.y + 15 + (row * rowSpacing);
                    } else if (houseNumber === 7) {
                      planetY = houseData.center.y - 15 + (row * rowSpacing);
                    } else if (houseNumber === 8) {
                      planetY = houseData.center.y + 15 + (row * rowSpacing);
                    } else if (houseNumber === 10) {
                      planetY = houseData.center.y - 35 + (row * rowSpacing);
                    } else if (houseNumber === 2) {
                      planetY = houseData.center.y - 35 + (row * rowSpacing);
                    } else {
                      planetY = houseData.center.y - 35 + (row * rowSpacing);
                    }
                  }
                } else {
                  // 7+ planets
                  if (houseNumber === 12) {
                    const spacing = 30;
                    const rowSpacing = 24;
                    if (pIndex < 3) {
                      planetX = houseData.center.x - 30 + (pIndex * spacing);
                      planetY = houseData.center.y - 35;
                    } else {
                      const row = Math.floor((pIndex - 3) / 2) + 1;
                      const col = (pIndex - 3) % 2;
                      planetX = houseData.center.x + (col === 0 ? -20 : 20);
                      planetY = houseData.center.y - 35 + (row * rowSpacing);
                    }
                  } else if ([3, 5, 9, 11].includes(houseNumber)) {
                    const rowSpacing = 22;
                    if (houseNumber === 3) {
                      planetX = houseData.center.x - 35;
                      planetY = houseData.center.y - 50 + (pIndex * rowSpacing);
                    } else if (houseNumber === 5) {
                      planetX = houseData.center.x - 35;
                      planetY = houseData.center.y - 40 + (pIndex * rowSpacing);
                    } else if (houseNumber === 9) {
                      planetX = houseData.center.x + 45;
                      planetY = houseData.center.y - 50 + (pIndex * rowSpacing);
                    } else if (houseNumber === 11) {
                      planetX = houseData.center.x + 35;
                      planetY = houseData.center.y - 60 + (pIndex * rowSpacing);
                    }
                  } else {
                    const row = Math.floor(pIndex / 2);
                    const col = pIndex % 2;
                    const spacing = 25;
                    const rowSpacing = 22;
                    planetX = houseData.center.x + (col === 0 ? -spacing : spacing);
                    if (houseNumber === 1) {
                      planetY = houseData.center.y - 35 + (row * rowSpacing);
                    } else if (houseNumber === 4) {
                      planetY = houseData.center.y - 10 + (row * rowSpacing);
                    } else if (houseNumber === 6) {
                      planetY = houseData.center.y + 10 + (row * rowSpacing);
                    } else if (houseNumber === 7) {
                      planetY = houseData.center.y - 20 + (row * rowSpacing);
                    } else if (houseNumber === 8) {
                      planetY = houseData.center.y + 10 + (row * rowSpacing);
                    } else if (houseNumber === 10) {
                      planetY = houseData.center.y - 40 + (row * rowSpacing);
                    } else if (houseNumber === 2) {
                      planetY = houseData.center.y - 35 + (row * rowSpacing);
                    } else {
                      planetY = houseData.center.y - 40 + (row * rowSpacing);
                    }
                  }
                }
                
                return (
                  <G key={pIndex}>
                    <SvgText 
                      x={planetX} 
                      y={planetY - 8} 
                      fontSize={showKarakas ? (totalPlanets > 4 ? "8" : totalPlanets > 2 ? "10" : "11") : (totalPlanets > 4 ? "10" : totalPlanets > 2 ? "12" : "14")} 
                      fill={getPlanetColor(planet)}
                      fontWeight="900"
                      textAnchor="middle"
                      onPress={() => handlePlanetPress(planet)}>
                      {getPlanetSymbolWithStatus(planet)}
                    </SvgText>
                    {showDegreeNakshatra && (
                      <SvgText 
                        x={planetX} 
                        y={planetY + 8} 
                        fontSize={totalPlanets > 4 ? "7" : totalPlanets > 2 ? "9" : "10"} 
                        fill={cosmicTheme ? (theme === 'dark' ? "rgba(255, 255, 255, 0.7)" : "rgba(0, 0, 0, 0.6)") : (theme === 'dark' ? "rgba(255, 255, 255, 0.7)" : "#666")}
                        fontWeight="500"
                        textAnchor="middle"
                        onPress={() => handlePlanetPress(planet)}>
                        {planet.formattedDegree} {planet.shortNakshatra}
                      </SvgText>
                    )}
                  </G>
                );
              })}
            </G>
          );
        })}
      </Svg>
      
      {/* Planet Tooltip */}
      {tooltip.show && (
        <View style={[styles.tooltip, { backgroundColor: theme === 'dark' ? 'rgba(233, 30, 99, 0.9)' : 'rgba(249, 115, 22, 0.9)' }]}>
          <Text style={styles.tooltipText}>{tooltip.text}</Text>
        </View>
      )}
      
      {/* Context Menu Modal */}
      <Modal
        visible={contextMenu.show}
        transparent
        animationType="fade"
        onRequestClose={() => setContextMenu({ show: false, rashiIndex: null, signName: null })}
      >
        <TouchableOpacity 
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setContextMenu({ show: false, rashiIndex: null, signName: null })}
        >
          <View style={[styles.contextMenuContainer, { backgroundColor: theme === 'dark' ? '#1a1a1a' : 'white' }]}>
            <Text style={[styles.contextMenuTitle, { color: theme === 'dark' ? '#ff6b35' : '#e91e63' }]}>{contextMenu.signName}</Text>
            <TouchableOpacity
              style={[styles.contextMenuItem, { backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : '#f5f5f5' }]}
              onPress={() => {
                onRotate?.(contextMenu.rashiIndex);
                setContextMenu({ show: false, rashiIndex: null, signName: null });
              }}
            >
              <Text style={styles.contextMenuIcon}>🔄</Text>
              <Text style={[styles.contextMenuText, { color: colors.text }]}>Make Ascendant</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
      
      {!hideInstructions && (
        <Text style={[styles.instructionText, { color: theme === 'dark' ? (cosmicTheme ? 'rgba(255, 255, 255, 0.7)' : '#666') : (cosmicTheme ? 'rgba(0, 0, 0, 0.6)' : '#666') }]}>
          Touch any sign to make it ascendant
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    width: '100%',
    aspectRatio: 1,
  },
  svg: {
    width: '100%',
    height: '100%',
    aspectRatio: 1,
  },
  tooltip: {
    position: 'absolute',
    top: 20,
    left: 20,
    right: 20,
    padding: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  tooltipText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  contextMenuContainer: {
    borderRadius: 16,
    padding: 20,
    minWidth: 200,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  contextMenuTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 16,
    textAlign: 'center',
  },
  contextMenuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    gap: 12,
  },
  contextMenuIcon: {
    fontSize: 20,
  },
  contextMenuText: {
    fontSize: 16,
    fontWeight: '600',
  },
  instructionText: {
    textAlign: 'center',
    fontSize: 12,
    fontStyle: 'italic',
    marginTop: 8,
  },
});

export default NorthIndianChart;