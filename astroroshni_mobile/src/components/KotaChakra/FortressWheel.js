import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, useWindowDimensions } from 'react-native';
import Svg, { Circle, Text as SvgText } from 'react-native-svg';
import { typographyTokens } from '../../theme/tokens';

const FortressWheel = ({ kotaData, colors, onPlanetPress }) => {
  const { width } = useWindowDimensions();
  const wheelSize = Math.min(300, Math.max(250, width - 60));
  const wheelScale = wheelSize / 300;
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

    if (planetName === kotaData.kota_swami) {
      return colors.accent;
    }

    if (planetName === kotaData.kota_paala) {
      return colors.info;
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
              borderWidth: 2,
            }
          ]}
          onPress={() => onPlanetPress && onPlanetPress(planetData.planet)}
        >
          <Text style={[styles.planetText, { color: planetData.planet === kotaData.kota_swami ? colors.onAccent : colors.textInverse }]}>
            {getPlanetSymbol(planetData.planet)}
          </Text>
          {planetData.motion === 'entering' && (
            <View style={[styles.enteringIndicator, { backgroundColor: colors.primary, borderColor: colors.surfaceRaised }]} />
          )}
        </TouchableOpacity>
      );
    });
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
      <View style={styles.heading}>
        <Text style={[styles.eyebrow, { color: colors.primary }]}>PLANETARY SIEGE MAP</Text>
        <Text style={[styles.title, { color: colors.text }]}>The four defensive zones</Text>
        <Text style={[styles.subtitle, { color: colors.textSecondary }]}>Tap a planet to understand its role and current effect.</Text>
      </View>

      <View style={[styles.wheelContainer, { width: wheelSize, height: wheelSize, borderRadius: wheelSize / 2, backgroundColor: colors.chartSurface, borderColor: colors.chartLine }]}>
        <Svg width={wheelSize} height={wheelSize} viewBox="0 0 300 300" style={styles.svg}>
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
          renderPlanetInSection(kotaData.malefic_siege.Stambha, 'Stambha', 50 * wheelScale, wheelSize / 2, wheelSize / 2)}

        {kotaData.malefic_siege?.Madhya &&
          renderPlanetInSection(kotaData.malefic_siege.Madhya, 'Madhya', 80 * wheelScale, wheelSize / 2, wheelSize / 2)}

        {kotaData.malefic_siege?.Prakaara &&
          renderPlanetInSection(kotaData.malefic_siege.Prakaara, 'Prakaara', 110 * wheelScale, wheelSize / 2, wheelSize / 2)}

        {kotaData.malefic_siege?.Bahya &&
          renderPlanetInSection(kotaData.malefic_siege.Bahya, 'Bahya', 130 * wheelScale, wheelSize / 2, wheelSize / 2)}
      </View>

      {/* Legend */}
      <View style={styles.legend}>
        <Text style={[styles.legendTitle, { color: colors.text }]}>Planet roles</Text>

        <View style={styles.legendRow}>
          <View style={[styles.legendColor, { backgroundColor: colors.accent }]} />
          <Text style={[styles.legendText, { color: colors.textSecondary }]}>
            Kota Swami (Lord)
          </Text>
        </View>

        <View style={styles.legendRow}>
          <View style={[styles.legendColor, { backgroundColor: colors.info }]} />
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
    marginBottom: 14,
    borderWidth: 1,
    borderRadius: 22,
    padding: 16,
  },
  heading: {
    width: '100%',
    marginBottom: 14,
  },
  eyebrow: {
    ...typographyTokens.eyebrow,
    marginBottom: 5,
  },
  title: {
    ...typographyTokens.sectionTitle,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 13,
    lineHeight: 19,
    fontWeight: '500',
  },
  wheelContainer: {
    position: 'relative',
    borderWidth: 1,
    overflow: 'hidden',
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
  },
  planetText: {
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
    borderWidth: 1,
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
    marginTop: 18,
    gap: 12,
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
