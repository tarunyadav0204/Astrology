import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Svg, { Circle, Text as SvgText } from 'react-native-svg';

const FortressWheel = ({ kotaData, colors, onPlanetPress }) => {
  const getPlanetSymbol = (planet) => {
    const symbols = {
      'Sun': '☉',
      'Moon': '☽',
      'Mars': '♂',
      'Mercury': '☿',
      'Jupiter': '♃',
      'Venus': '♀',
      'Saturn': '♄',
      'Rahu': '☊',
      'Ketu': '☋'
    };
    return symbols[planet] || planet.charAt(0);
  };

  const getSectionColor = (section) => {
    switch (section) {
      case 'Stambha': return colors.error;
      case 'Madhya': return colors.warning;
      case 'Prakaara': return colors.primary;
      case 'Bahya': return colors.success;
      default: return colors.textSecondary;
    }
  };

  const getPlanetColor = (planetData, kotaData) => {
    const planetName = planetData.planet;
    
    // Kota Swami (fortress lord) - always gold/yellow (royal)
    if (planetName === kotaData.kota_swami) {
      return '#FFD700'; // Gold
    }
    
    // Kota Paala (fortress guard) - always blue (guardian)
    if (planetName === kotaData.kota_paala) {
      return '#4A90E2'; // Blue
    }
    
    // Regular benefics - green (protective)
    if (planetData.is_benefic) {
      return colors.success;
    }
    
    // Regular malefics - red (threatening)
    return colors.error;
  };

  const renderPlanetInSection = (planets, section, radius, centerX, centerY) => {
    return planets.map((planetData, index) => {
      // Position planets at angles to avoid vertical overlap with labels
      const baseAngle = section === 'Stambha' ? 45 : 
                       section === 'Madhya' ? 135 :
                       section === 'Prakaara' ? 225 : 315; // Different quadrants
      const angle = baseAngle + (index * 30); // 30° spacing between planets
      const radian = (angle * Math.PI) / 180;
      const x = centerX + radius * Math.cos(radian);
      const y = centerY + radius * Math.sin(radian);
      
      return (
        <TouchableOpacity
          key={`${section}-${index}`}
          style={[
            styles.planetIcon,
            {
              position: 'absolute',
              left: x - 15,
              top: y - 15,
              backgroundColor: getPlanetColor(planetData, kotaData),
              borderColor: getSectionColor(section),
              borderWidth: 3,
            }
          ]}
          onPress={() => onPlanetPress && onPlanetPress(planetData.planet)}
        >
          <Text style={styles.planetText}>
            {getPlanetSymbol(planetData.planet)}
          </Text>
          {planetData.motion === 'entering' && (
            <View style={styles.enteringIndicator} />
          )}
        </TouchableOpacity>
      );
    });
  };

  return (
    <View style={styles.container}>
      <Text style={[styles.title, { color: colors.text }]}>
        🏰 Fortress Layout
      </Text>
      
      <View style={styles.wheelContainer}>
        <Svg width={300} height={300} style={styles.svg}>
          {/* Bahya (Outer) */}
          <Circle
            cx={150}
            cy={150}
            r={140}
            fill="none"
            stroke={getSectionColor('Bahya')}
            strokeWidth={2}
            opacity={0.3}
          />
          
          {/* Prakaara */}
          <Circle
            cx={150}
            cy={150}
            r={110}
            fill="none"
            stroke={getSectionColor('Prakaara')}
            strokeWidth={2}
            opacity={0.4}
          />
          
          {/* Madhya */}
          <Circle
            cx={150}
            cy={150}
            r={80}
            fill="none"
            stroke={getSectionColor('Madhya')}
            strokeWidth={3}
            opacity={0.5}
          />
          
          {/* Stambha (Inner) */}
          <Circle
            cx={150}
            cy={150}
            r={50}
            fill={getSectionColor('Stambha')}
            opacity={0.2}
            stroke={getSectionColor('Stambha')}
            strokeWidth={3}
          />
          
          {/* Section Labels */}
          <SvgText
            x={150}
            y={30}
            textAnchor="middle"
            fontSize={12}
            fill={colors.text}
            fontWeight="600"
          >
            Bahya
          </SvgText>
          
          <SvgText
            x={150}
            y={60}
            textAnchor="middle"
            fontSize={12}
            fill={colors.text}
            fontWeight="600"
          >
            Prakaara
          </SvgText>
          
          <SvgText
            x={150}
            y={90}
            textAnchor="middle"
            fontSize={12}
            fill={colors.text}
            fontWeight="600"
          >
            Madhya
          </SvgText>
          
          <SvgText
            x={150}
            y={150}
            textAnchor="middle"
            fontSize={14}
            fill={colors.text}
            fontWeight="700"
          >
            Stambha
          </SvgText>
        </Svg>
        
        {/* Planet positions */}
        {kotaData.malefic_siege?.Stambha && 
          renderPlanetInSection(kotaData.malefic_siege.Stambha, 'Stambha', 50, 150, 150)}
        
        {kotaData.malefic_siege?.Madhya && 
          renderPlanetInSection(kotaData.malefic_siege.Madhya, 'Madhya', 80, 150, 150)}
        
        {kotaData.malefic_siege?.Prakaara && 
          renderPlanetInSection(kotaData.malefic_siege.Prakaara, 'Prakaara', 110, 150, 150)}
        
        {kotaData.malefic_siege?.Bahya && 
          renderPlanetInSection(kotaData.malefic_siege.Bahya, 'Bahya', 140, 150, 150)}
      </View>
      
      {/* Legend */}
      <View style={styles.legend}>
        <Text style={[styles.legendTitle, { color: colors.text }]}>Planet Colors:</Text>
        
        <View style={styles.legendRow}>
          <View style={[styles.legendColor, { backgroundColor: '#FFD700' }]} />
          <Text style={[styles.legendText, { color: colors.textSecondary }]}>
            Kota Swami (Lord)
          </Text>
        </View>
        
        <View style={styles.legendRow}>
          <View style={[styles.legendColor, { backgroundColor: '#4A90E2' }]} />
          <Text style={[styles.legendText, { color: colors.textSecondary }]}>
            Kota Paala (Guard)
          </Text>
        </View>
        
        <View style={styles.legendRow}>
          <View style={[styles.legendColor, { backgroundColor: colors.success }]} />
          <Text style={[styles.legendText, { color: colors.textSecondary }]}>
            Benefics (Protective)
          </Text>
        </View>
        
        <View style={styles.legendRow}>
          <View style={[styles.legendColor, { backgroundColor: colors.error }]} />
          <Text style={[styles.legendText, { color: colors.textSecondary }]}>
            Malefics (Threatening)
          </Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    marginVertical: 20,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  wheelContainer: {
    position: 'relative',
    width: 300,
    height: 300,
  },
  svg: {
    position: 'absolute',
  },
  planetIcon: {
    width: 30,
    height: 30,
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#ffffff',
  },
  planetText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  enteringIndicator: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ff0000',
  },
  legendTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
    width: '100%',
  },
  legend: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 20,
    gap: 16,
  },
  legendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  legendText: {
    fontSize: 12,
    fontWeight: '500',
  },
});

export default FortressWheel;