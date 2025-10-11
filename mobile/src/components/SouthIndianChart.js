import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, Alert } from 'react-native';
import Svg, { Rect, Line, Text as SvgText, G, Defs, LinearGradient, Stop, Circle, TSpan } from 'react-native-svg';
import HouseAnalysisModal from './HouseAnalysisModal';

const SouthIndianChart = ({ chartData, birthData }) => {
  const [tooltip, setTooltip] = useState({ show: false, text: '' });
  const [contextMenu, setContextMenu] = useState({ show: false, houseNumber: null, signName: null });
  const [componentLayout, setComponentLayout] = useState({ width: 300, height: 320 });
  const [customAscendant, setCustomAscendant] = useState(null);
  const [aspectsHighlight, setAspectsHighlight] = useState({ show: false, houseNumber: null, aspectingPlanets: [] });
  const [houseAnalysisModal, setHouseAnalysisModal] = useState({ show: false, houseNumber: null, signName: null });
  
  const rashiNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

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

  const handleRashiPress = (houseNumber, signIndex) => {
    console.log('Rashi pressed: House', houseNumber, 'Sign', rashiNames[signIndex]);
    setTimeout(() => {
      setContextMenu({ show: true, houseNumber, signName: rashiNames[signIndex] });
    }, 200);
  };

  const findTouchedPlanet = (touchX, touchY) => {
    const svgX = (touchX / componentLayout.width) * 300;
    const svgY = (touchY / componentLayout.height) * 320;
    
    for (const pos of gridPositions) {
      if (pos.sign === -1) continue;
      const planetsInSign = getPlanetsInSign(pos.sign);
      const houseNumber = getHouseNumber(pos.sign);
      
      planetsInSign.forEach((planet, pIndex) => {
        const totalPlanets = planetsInSign.length;
        const isDoubleDigitHouse = houseNumber >= 10;
        let planetX, planetY;
        
        if (totalPlanets === 1) {
          planetX = pos.x + pos.width / 2;
          planetY = pos.y + pos.height / 2 + (isDoubleDigitHouse ? 8 : 5);
        } else {
          planetX = pos.x + pos.width / 2;
          const lineHeight = totalPlanets > 4 ? 10 : totalPlanets > 2 ? 12 : 13;
          const startY = pos.y + pos.height / 2 + (isDoubleDigitHouse ? 5 : 2) - ((totalPlanets - 1) * lineHeight / 2);
          planetY = startY + (pIndex * lineHeight);
        }
        
        const distance = Math.sqrt(Math.pow(svgX - planetX, 2) + Math.pow(svgY - planetY, 2));
        if (distance < 15) {
          console.log('Planet touched:', planet.name, 'at', planetX, planetY);
          return planet;
        }
      });
    }
    return null;
  };
  
  const findTouchedHouse = (touchX, touchY) => {
    const svgX = (touchX / componentLayout.width) * 300;
    const svgY = (touchY / componentLayout.height) * 320;
    
    for (const pos of gridPositions) {
      if (pos.sign === -1) continue;
      const houseNumber = getHouseNumber(pos.sign);
      
      const houseX = pos.x + 8;
      const houseY = pos.y + 18;
      
      const distance = Math.sqrt(Math.pow(svgX - houseX, 2) + Math.pow(svgY - houseY, 2));
      if (distance < 20) {
        console.log('House touched:', houseNumber, 'at', houseX, houseY);
        return { houseNumber, signIndex: pos.sign };
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

  const signs = ['Ar', 'Ta', 'Ge', 'Ca', 'Le', 'Vi', 'Li', 'Sc', 'Sa', 'Cp', 'Aq', 'Pi'];

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

  const getPlanetsInSign = (signIndex) => {
    if (!chartData.planets || signIndex === -1) return [];
    
    const planets = ['Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa', 'Ra', 'Ke', 'Gu', 'Ma'];
    
    return Object.entries(chartData.planets)
      .filter(([name, data]) => data.sign === signIndex)
      .map(([name, data]) => {
        const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi'];
        const planetIndex = planetNames.indexOf(name);
        return {
          symbol: planets[planetIndex] || name.substring(0, 2),
          name: name,
          degree: data.degree ? data.degree.toFixed(2) : '0.00'
        };
      });
  };

  const getHouseNumber = (signIndex) => {
    if (signIndex === -1) return '';
    
    let ascendantSign;
    if (customAscendant !== null) {
      ascendantSign = customAscendant;
    } else if (chartData.houses && chartData.houses[0]) {
      ascendantSign = Math.floor(chartData.houses[0].longitude / 30);
    } else {
      return '';
    }
    
    return ((signIndex - ascendantSign + 12) % 12) + 1;
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
        <Svg viewBox="0 0 300 320" style={styles.svg}>
        <Defs>
          <LinearGradient id="southChartGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <Stop offset="0%" stopColor="rgba(233, 30, 99, 0.1)" />
            <Stop offset="50%" stopColor="rgba(255, 111, 0, 0.1)" />
            <Stop offset="100%" stopColor="rgba(255, 255, 255, 0.2)" />
          </LinearGradient>
        </Defs>
        
        {/* Outer border */}
        <Rect x="0" y="0" width="300" height="300" 
              fill="url(#southChartGradient)" stroke="#e91e63" strokeWidth="3"/>
        
        {/* Grid divisions */}
        {/* Top row divisions */}
        <Line x1="75" y1="0" x2="75" y2="75" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="150" y1="0" x2="150" y2="75" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="225" y1="0" x2="225" y2="75" stroke="#ff8a65" strokeWidth="2"/>
        {/* Bottom row divisions */}
        <Line x1="75" y1="225" x2="75" y2="300" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="150" y1="225" x2="150" y2="300" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="225" y1="225" x2="225" y2="300" stroke="#ff8a65" strokeWidth="2"/>
        {/* Left column divisions */}
        <Line x1="0" y1="75" x2="75" y2="75" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="0" y1="150" x2="75" y2="150" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="0" y1="225" x2="75" y2="225" stroke="#ff8a65" strokeWidth="2"/>
        {/* Right column divisions */}
        <Line x1="225" y1="75" x2="300" y2="75" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="225" y1="150" x2="300" y2="150" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="225" y1="225" x2="300" y2="225" stroke="#ff8a65" strokeWidth="2"/>
        {/* Inner borders */}
        <Line x1="0" y1="75" x2="300" y2="75" stroke="#ff6f00" strokeWidth="3"/>
        <Line x1="0" y1="225" x2="300" y2="225" stroke="#ff6f00" strokeWidth="3"/>
        <Line x1="75" y1="0" x2="75" y2="300" stroke="#ff6f00" strokeWidth="3"/>
        <Line x1="225" y1="0" x2="225" y2="300" stroke="#ff6f00" strokeWidth="3"/>

        {/* Grid cells */}
        {gridPositions.map((pos, index) => {
          const planetsInSign = getPlanetsInSign(pos.sign);
          const houseNumber = getHouseNumber(pos.sign);
          
          return (
            <G key={index}>
              {pos.sign !== -1 && (
                <>
                  {/* House highlighting for aspects */}
                  {aspectsHighlight.show && aspectsHighlight.houseNumber === houseNumber && (
                    <Rect x={pos.x + 2} y={pos.y + 2} width={pos.width - 4} height={pos.height - 4}
                          fill="rgba(233, 30, 99, 0.2)" stroke="#e91e63" strokeWidth="2" strokeDasharray="5,5"/>
                  )}
                  
                  {/* House number */}
                  <SvgText x={pos.x + 8} y={pos.y + 18} 
                           fontSize="12" 
                           fill="#333" 
                           fontWeight="bold"
                           onTouchStart={(e) => {
                             e.stopPropagation();
                             console.log('House touched:', houseNumber);
                             handleRashiPress(houseNumber, pos.sign);
                           }}>
                    {houseNumber}
                  </SvgText>
                  
                  {/* Sign name */}
                  <SvgText x={pos.x + pos.width - 8} y={pos.y + 18} 
                           fontSize="10" fill="#666"
                           textAnchor="end">
                    {signs[pos.sign]}
                  </SvgText>
                  
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
                    
                    const aspectingPlanet = aspectsHighlight.show && aspectsHighlight.aspectingPlanets?.find(p => p.name === planet.name);
                    
                    return (
                      <G key={pIndex}>
                        {aspectingPlanet && (
                          <Circle cx={planetX} cy={planetY} r="10" 
                                  fill="none" 
                                  stroke={aspectingPlanet.isPositive ? '#4caf50' : '#f44336'} 
                                  strokeWidth="2" 
                                  strokeDasharray="3,2"/>
                        )}
                        <SvgText 
                          x={planetX} 
                          y={planetY} 
                          fontSize={totalPlanets > 4 ? "8" : totalPlanets > 2 ? "10" : totalPlanets > 1 ? "11" : "14"} 
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
                </>
              )}
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
        onRequestClose={() => setContextMenu({ show: false, houseNumber: null, signName: null })}
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
        getPlanetsInHouse={getPlanetsInSign}
        getRashiForHouse={(houseIndex) => {
          // For South Indian chart, we need to convert house to sign differently
          let ascendantSign;
          if (customAscendant !== null) {
            ascendantSign = customAscendant;
          } else if (chartData.houses && chartData.houses[0]) {
            ascendantSign = Math.floor(chartData.houses[0].longitude / 30);
          } else {
            return houseIndex;
          }
          return (ascendantSign + houseIndex) % 12;
        }}
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
    paddingHorizontal: 16,
  },
});

export default SouthIndianChart;