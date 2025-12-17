import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Rect, Text as SvgText, G, Line } from 'react-native-svg';

const SouthIndianChart = ({ chartData, showDegreeNakshatra = true }) => {
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

  const getPlanetsInSign = (signIndex) => {
    if (!chartData.planets || signIndex === -1) return [];
    const planets = ['Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa', 'Ra', 'Ke', 'Gu', 'Mn'];
    const planetsInSign = [];
    
    // Add regular planets (exclude InduLagna as it's handled separately)
    Object.entries(chartData.planets)
      .filter(([name, data]) => data.sign === signIndex && name !== 'InduLagna')
      .forEach(([name, data]) => {
        const planetNames = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi'];
        const planetIndex = planetNames.indexOf(name);
        planetsInSign.push({
          symbol: planets[planetIndex] || name.substring(0, 2),
          name: name,
          degree: data.degree ? data.degree.toFixed(2) : '0.00',
          longitude: data.longitude || 0,
          nakshatra: getNakshatra(data.longitude || 0),
          shortNakshatra: getShortNakshatra(data.longitude || 0),
          formattedDegree: formatDegree(data.degree || 0)
        });
      });
    
    // Add InduLagna if it's in this sign
    if (chartData.planets?.InduLagna && chartData.planets.InduLagna.sign === signIndex) {
      planetsInSign.push({
        symbol: 'IL',
        name: 'InduLagna',
        degree: chartData.planets.InduLagna.degree ? chartData.planets.InduLagna.degree.toFixed(2) : '0.00',
        longitude: chartData.planets.InduLagna.longitude || 0,
        nakshatra: getNakshatra(chartData.planets.InduLagna.longitude || 0),
        shortNakshatra: getShortNakshatra(chartData.planets.InduLagna.longitude || 0),
        formattedDegree: formatDegree(chartData.planets.InduLagna.degree || 0)
      });
    }
    
    return planetsInSign;
  };

  const getHouseNumber = (signIndex) => {
    if (!chartData.houses || signIndex === -1) return '';
    
    // Find which house contains this sign
    for (let i = 0; i < chartData.houses.length; i++) {
      if (chartData.houses[i].sign === signIndex) {
        return i + 1; // Return house number (1-12)
      }
    }
    return '';
  };

  return (
    <View style={styles.container}>
      <Svg viewBox="0 0 340 340" style={styles.svg}>
        {/* Outer border */}
        <Rect x="0" y="0" width="340" height="340" fill="none" stroke="#ff6f00" strokeWidth="3"/>
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
                fill={houseNumber === 1 ? "#e91e63" : "#333"} 
                fontWeight={houseNumber === 1 ? "900" : "bold"}>
                {houseNumber}
              </SvgText>
              
              {/* Ascendant marker for house 1 */}
              {houseNumber === 1 && (
                <G>
                  <SvgText 
                    x={pos.x + pos.width - 8} 
                    y={pos.y + pos.height - 20} 
                    fontSize="9" 
                    fill="#e91e63" 
                    fontWeight="900" 
                    textAnchor="end">
                    ASC
                  </SvgText>
                  {chartData.ascendant && (
                    <SvgText 
                      x={pos.x + pos.width - 8} 
                      y={pos.y + pos.height - 8} 
                      fontSize="7" 
                      fill="#666" 
                      fontWeight="500" 
                      textAnchor="end">
                      {formatDegree(chartData.ascendant % 30)} {getShortNakshatra(chartData.ascendant)}
                    </SvgText>
                  )}
                </G>
              )}
              
              {/* Planets */}
              {planetsInSign.map((planet, pIndex) => (
                <G key={pIndex}>
                  <SvgText 
                    x={pos.x + pos.width / 2} 
                    y={pos.y + 20 + (pIndex * 20)} 
                    fontSize="12" 
                    fill="#333"
                    fontWeight="bold"
                    textAnchor="middle">
                    {planet.symbol}
                  </SvgText>
                  {showDegreeNakshatra && (
                    <SvgText 
                      x={pos.x + pos.width / 2} 
                      y={pos.y + 31 + (pIndex * 20)} 
                      fontSize="8" 
                      fill="#666"
                      fontWeight="500"
                      textAnchor="middle">
                      {planet.formattedDegree} {planet.shortNakshatra}
                    </SvgText>
                  )}
                </G>
              ))}
            </G>
          );
        })}
      </Svg>
      

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