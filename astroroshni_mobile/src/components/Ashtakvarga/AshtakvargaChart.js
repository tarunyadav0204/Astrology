import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useTheme } from '../../context/ThemeContext';
import { typographyTokens } from '../../theme/tokens';

const AshtakvargaChart = ({ chartData, ashtakvargaData, birthAshtakvargaData, onHousePress, cosmicTheme = true }) => {
  const { colors } = useTheme();

  const getStrength = (bindus) => {
    if (bindus >= 30) return { label: 'Strong', color: colors.success };
    if (bindus <= 25) return { label: 'Sensitive', color: colors.error };
    return { label: 'Steady', color: colors.warning };
  };

  const getSignName = (signIndex) => {
    const signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
    return signs[signIndex] || 'Unknown';
  };

  return (
    <View style={styles.container}>
      <View style={styles.grid}>
        {[1,2,3,4,5,6,7,8,9,10,11,12].map((houseNumber) => {
          const ashtakvargaHouseData = ashtakvargaData?.[houseNumber.toString()];
          const bindus = ashtakvargaHouseData?.bindus || 0;
          const signIndex = ashtakvargaHouseData?.sign || 0;
          const signName = getSignName(signIndex);
          const strength = getStrength(bindus);

          // Calculate difference from birth chart if available
          const birthBindus = birthAshtakvargaData?.[houseNumber.toString()]?.bindus || 0;
          const difference = birthAshtakvargaData ? bindus - birthBindus : null;

          return (
            <TouchableOpacity
              key={houseNumber}
              style={[styles.houseBox, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}
              onPress={() => onHousePress?.(houseNumber, bindus, signName)}
            >
              <View style={[styles.strengthRule, { backgroundColor: strength.color }]} />
              <View style={styles.houseHeading}>
                <Text style={[styles.houseNumber, { color: colors.textTertiary }]}>H{houseNumber}</Text>
                <Text style={[styles.strengthLabel, { color: strength.color }]}>{strength.label}</Text>
              </View>
              <View style={styles.bindusRow}>
                <Text style={[styles.bindus, { color: colors.text }]}>{bindus}</Text>
                {difference !== null && difference !== 0 && (
                  <Text style={[styles.difference, { color: difference > 0 ? colors.success : colors.error }]}>
                    ({difference > 0 ? '+' : ''}{difference})
                  </Text>
                )}
              </View>
              <Text style={[styles.signName, { color: colors.textSecondary }]} numberOfLines={1}>{signName}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 6,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  houseBox: {
    width: '30.6%',
    minHeight: 104,
    margin: '1.35%',
    borderRadius: 16,
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 11,
    borderWidth: 1,
    overflow: 'hidden',
  },
  strengthRule: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
  },
  houseHeading: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  houseNumber: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
  },
  strengthLabel: {
    fontSize: 8,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  bindusRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  bindus: {
    ...typographyTokens.display,
    fontSize: 30,
    lineHeight: 32,
    marginRight: 3,
  },
  difference: {
    fontSize: 10,
    fontWeight: '600',
  },
  signName: {
    fontSize: 11,
    fontWeight: '700',
  },
});

export default AshtakvargaChart;
