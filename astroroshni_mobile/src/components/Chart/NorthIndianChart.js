import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, Alert } from 'react-native';
import Svg, { Rect, Polygon, Line, Text as SvgText, G, Defs, LinearGradient, Stop, Circle } from 'react-native-svg';

const NorthIndianChart = ({ chartData, birthData, showDegreeNakshatra = true }) => {
  
  const [tooltip, setTooltip] = useState({ show: false, text: '' });
  const [contextMenu, setContextMenu] = useState({ show: false, houseNumber: null, signName: null });
  const [customAscendant, setCustomAscendant] = useState(null);
  const [aspectsHighlight, setAspectsHighlight] = useState({ show: false, houseNumber: null, aspectingPlanets: [] });

  const handlePlanetPress = (planet) => {
    const tooltipText = `${planet.name}: ${planet.degree}° in ${planet.nakshatra}`;
    setTooltip({ show: true, text: tooltipText });
    setTimeout(() => setTooltip({ show: false, text: '' }), 2000);
  };

  const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
  
  const handleRashiPress = (houseNumber, rashiIndex) => {
    setTimeout(() => {
      setContextMenu({ show: true, houseNumber, signName: rashiNames[rashiIndex] });
    }, 200);
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
    
    if (customAscendant !== null) {
      // Recalculate house-rashi mapping based on custom ascendant
      return (customAscendant + houseIndex) % 12;
    }
    
    // Default: use original chart data
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
    
    const planets = ['Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa', 'Ra', 'Ke', 'Gu', 'Mn'];
    const rashiForThisHouse = getRashiForHouse(houseIndex);
    
    return Object.entries(chartData.planets)
      .filter(([name, data]) => data.sign === rashiForThisHouse)
      .map(([name, data]) => {
        const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi'];
        const planetIndex = planetNames.indexOf(name);
        return {
          symbol: planets[planetIndex] || name.substring(0, 2),
          name: name,
          degree: data.degree ? data.degree.toFixed(2) : '0.00',
          longitude: data.longitude || 0,
          nakshatra: getNakshatra(data.longitude || 0),
          shortNakshatra: getShortNakshatra(data.longitude || 0),
          formattedDegree: formatDegree(data.degree || 0)
        };
      });
  };

  return (
    <View style={styles.container}>
      <Svg viewBox="0 0 400 400" style={styles.svg}>
        <Defs>
          <LinearGradient id="chartGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <Stop offset="0%" stopColor="rgba(255, 255, 255, 0.9)" />
            <Stop offset="50%" stopColor="rgba(248, 250, 252, 0.95)" />
            <Stop offset="100%" stopColor="rgba(241, 245, 249, 0.9)" />
          </LinearGradient>
        </Defs>

        {/* Outer square border */}
        <Rect x="5" y="5" width="390" height="390" 
              fill="url(#chartGradient)" stroke="#e91e63" strokeWidth="3"/>
        
        {/* Inner diamond border */}
        <Polygon points="200,5 395,200 200,395 5,200" 
                 fill="none" stroke="#ff6f00" strokeWidth="3"/>
        
        {/* Diagonal lines creating 12 houses */}
        <Line x1="5" y1="5" x2="395" y2="395" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="395" y1="5" x2="5" y2="395" stroke="#ff8a65" strokeWidth="2"/>

        {/* Houses */}
        {[1,2,3,4,5,6,7,8,9,10,11,12].map((houseNumber) => {
          const houseIndex = houseNumber - 1;
          const rashiIndex = getRashiForHouse(houseIndex);
          const planetsInHouse = getPlanetsInHouse(houseIndex);
          const houseData = getHouseData(houseNumber);
          
          return (
            <G key={houseNumber}>
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
                fill={rashiIndex === chartData.houses[0].sign ? "#e91e63" : "#333"} 
                fontWeight={rashiIndex === chartData.houses[0].sign ? "900" : "bold"}
                onPress={() => handleRashiPress(houseNumber, rashiIndex)}>
                {rashiIndex + 1}
              </SvgText>
              

              
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
                    planetX = houseData.center.x + 25;
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
                      planetX = houseData.center.x + 45;
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
                    planetX = houseData.center.x + 35;
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
                
                return (
                  <G key={pIndex}>
                    <SvgText 
                      x={planetX} 
                      y={planetY - 8} 
                      fontSize={totalPlanets > 4 ? "10" : totalPlanets > 2 ? "12" : "14"} 
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
                        fill="#666"
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
        <View style={styles.tooltip}>
          <Text style={styles.tooltipText}>{tooltip.text}</Text>
        </View>
      )}
      

    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'white',
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
    backgroundColor: 'rgba(233, 30, 99, 0.9)',
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
  instructionText: {
    textAlign: 'center',
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
    marginTop: 8,
  },
});

export default NorthIndianChart;