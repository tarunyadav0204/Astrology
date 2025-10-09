import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Svg, { Rect, Polygon, Line, Circle, Text as SvgText, Defs, LinearGradient, Stop } from 'react-native-svg';

export default function NorthIndianChart({ chartData, onHousePress }) {
  const planets = ['☉', '☽', '♂', '☿', '♃', '♀', '♄', '☊', '☋', 'Gu', 'Ma'];
  
  const getHouseData = (houseNumber) => {
    const centers = {
      1: { x: 200, y: 110 },
      2: { x: 290, y: 110 },
      3: { x: 290, y: 200 },
      4: { x: 290, y: 290 },
      5: { x: 200, y: 290 },
      6: { x: 110, y: 290 },
      7: { x: 110, y: 200 },
      8: { x: 110, y: 110 },
      9: { x: 110, y: 110 },
      10: { x: 200, y: 110 },
      11: { x: 290, y: 110 },
      12: { x: 290, y: 200 }
    };
    return centers[houseNumber] || { x: 200, y: 200 };
  };

  const getPlanetsInHouse = (houseIndex) => {
    if (!chartData?.planets) return [];
    
    return Object.entries(chartData.planets)
      .filter(([name, data]) => data.house === houseIndex + 1)
      .map(([name, data], index) => {
        const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi'];
        const planetIndex = planetNames.indexOf(name);
        return {
          symbol: planets[planetIndex] || name.substring(0, 2),
          name: name,
          degree: data.degree?.toFixed(2) || '0.00'
        };
      });
  };

  return (
    <View style={styles.container}>
      <Svg width="100%" height="400" viewBox="0 0 400 400">
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
          const planetsInHouse = getPlanetsInHouse(houseIndex);
          const houseData = getHouseData(houseNumber);
          
          return (
            <React.Fragment key={houseNumber}>
              {/* House number */}
              <SvgText 
                x={houseData.x} 
                y={houseData.y} 
                fontSize="18" 
                fill="#333" 
                fontWeight="bold"
                textAnchor="middle"
              >
                {houseNumber}
              </SvgText>
              
              {/* Planets in house */}
              {planetsInHouse.map((planet, pIndex) => (
                <SvgText
                  key={`${houseNumber}-${pIndex}`}
                  x={houseData.x + (pIndex % 2 === 0 ? -15 : 15)}
                  y={houseData.y + 20 + Math.floor(pIndex / 2) * 15}
                  fontSize="14"
                  fill="#e91e63"
                  fontWeight="bold"
                  textAnchor="middle"
                >
                  {planet.symbol}
                </SvgText>
              ))}
            </React.Fragment>
          );
        })}
      </Svg>
      
      {/* House buttons for interaction */}
      <View style={styles.houseButtons}>
        {[1,2,3,4,5,6,7,8,9,10,11,12].map((houseNumber) => (
          <TouchableOpacity
            key={houseNumber}
            style={styles.houseButton}
            onPress={() => onHousePress?.(houseNumber)}
          >
            <Text style={styles.houseButtonText}>H{houseNumber}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 10,
    margin: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  houseButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 10,
  },
  houseButton: {
    backgroundColor: '#f0f0f0',
    borderRadius: 6,
    padding: 8,
    margin: 2,
    minWidth: 40,
    alignItems: 'center',
  },
  houseButtonText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
  },
});