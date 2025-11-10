import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Rect, Text as SvgText, G, Line } from 'react-native-svg';

const SouthIndianChart = ({ chartData }) => {
  // Fixed sign positions in South Indian chart
  const gridPositions = [
    { x: 0, y: 0, width: 85, height: 85, sign: 11 },     // Pisces
    { x: 85, y: 0, width: 85, height: 85, sign: 0 },     // Aries  
    { x: 170, y: 0, width: 85, height: 85, sign: 1 },    // Taurus
    { x: 255, y: 0, width: 85, height: 85, sign: 2 },    // Gemini
    { x: 0, y: 85, width: 85, height: 85, sign: 10 },    // Aquarius
    { x: 255, y: 85, width: 85, height: 85, sign: 3 },   // Cancer
    { x: 0, y: 170, width: 85, height: 85, sign: 9 },    // Capricorn
    { x: 255, y: 170, width: 85, height: 85, sign: 4 },  // Leo
    { x: 0, y: 255, width: 85, height: 85, sign: 8 },    // Sagittarius
    { x: 85, y: 255, width: 85, height: 85, sign: 7 },   // Scorpio
    { x: 170, y: 255, width: 85, height: 85, sign: 6 },  // Libra
    { x: 255, y: 255, width: 85, height: 85, sign: 5 }   // Virgo
  ];

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
          degree: data.degree ? data.degree.toFixed(1) : '0.0'
        };
      });
  };

  const getHouseNumber = (signIndex) => {
    if (signIndex === -1) return '';
    const ascendantSign = 4; // Leo
    return ((signIndex - ascendantSign + 12) % 12) + 1;
  };

  return (
    <View style={styles.container}>
      <Svg viewBox="0 0 340 340" style={styles.svg}>
        {/* Grid lines */}
        <Line x1="85" y1="0" x2="85" y2="85" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="170" y1="0" x2="170" y2="85" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="255" y1="0" x2="255" y2="85" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="85" y1="255" x2="85" y2="340" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="170" y1="255" x2="170" y2="340" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="255" y1="255" x2="255" y2="340" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="0" y1="85" x2="85" y2="85" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="0" y1="170" x2="85" y2="170" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="0" y1="255" x2="85" y2="255" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="255" y1="85" x2="340" y2="85" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="255" y1="170" x2="340" y2="170" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="255" y1="255" x2="340" y2="255" stroke="#ff8a65" strokeWidth="2"/>
        <Line x1="0" y1="85" x2="340" y2="85" stroke="#ff6f00" strokeWidth="3"/>
        <Line x1="0" y1="255" x2="340" y2="255" stroke="#ff6f00" strokeWidth="3"/>
        <Line x1="85" y1="0" x2="85" y2="340" stroke="#ff6f00" strokeWidth="3"/>
        <Line x1="255" y1="0" x2="255" y2="340" stroke="#ff6f00" strokeWidth="3"/>

        {/* Grid cells */}
        {gridPositions.map((pos, index) => {
          const planetsInSign = getPlanetsInSign(pos.sign);
          const houseNumber = getHouseNumber(pos.sign);
          
          return (
            <G key={index}>
              {/* House number */}
              <SvgText 
                x={pos.x + 8} 
                y={pos.y + 18} 
                fontSize="12" 
                fill={pos.sign === 4 ? "#e91e63" : "#333"} 
                fontWeight={pos.sign === 4 ? "900" : "bold"}>
                {houseNumber}
              </SvgText>
              
              {/* Planets */}
              {planetsInSign.map((planet, pIndex) => (
                <SvgText 
                  key={pIndex}
                  x={pos.x + pos.width / 2} 
                  y={pos.y + pos.height / 2 + (pIndex * 15)} 
                  fontSize="12" 
                  fill="#333"
                  fontWeight="bold"
                  textAnchor="middle">
                  {planet.symbol}
                </SvgText>
              ))}
            </G>
          );
        })}
      </Svg>
      
      <Text style={styles.instructionText}>
        South Indian Chart Style
      </Text>
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
  instructionText: {
    textAlign: 'center',
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
    marginTop: 8,
  },
});

export default SouthIndianChart;