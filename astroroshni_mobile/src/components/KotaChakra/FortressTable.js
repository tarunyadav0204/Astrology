import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { typographyTokens } from '../../theme/tokens';

const FortressTable = ({ kotaData, colors }) => {
  const getThreatLevel = (planets) => {
    const malefics = planets.filter(p => !p.is_benefic && ['Saturn', 'Mars', 'Rahu', 'Ketu'].includes(p.planet));
    const benefics = planets.filter(p => p.is_benefic);

    if (malefics.length > 0 && benefics.length === 0) return { level: 'High', color: colors.error };
    if (malefics.length > 0 && benefics.length > 0) return { level: 'Moderate', color: colors.warning };
    if (benefics.length > 0) return { level: 'Protected', color: colors.success };
    return { level: 'Clear', color: colors.textSecondary };
  };

  const getZoneEffects = (zone, planets) => {
    const effects = {
      'Stambha': 'Health, Legal, Core Self',
      'Madhya': 'Resources, Family, Stability',
      'Prakaara': 'Social Image, Reputation',
      'Bahya': 'External Relations, Travel'
    };
    return effects[zone] || '';
  };

  const getZoneColor = (zone) => {
    switch (zone) {
      case 'Stambha': return colors.error;
      case 'Madhya': return colors.warning;
      case 'Prakaara': return colors.primary;
      case 'Bahya': return colors.success;
      default: return colors.textSecondary;
    }
  };

  const getZoneTextColor = (zone) => {
    if (zone === 'Madhya') return colors.onAccent;
    if (zone === 'Prakaara') return colors.onPrimary;
    return colors.textInverse;
  };

  const renderTableRow = (zone, nakshatras, planets, index) => {
    const threat = getThreatLevel(planets);
    const planetNames = planets.map(p => p.planet).join(', ') || 'Empty';
    const zoneColor = getZoneColor(zone);

    return (
      <View key={zone} style={[styles.tableRow, { backgroundColor: index % 2 === 0 ? colors.surfaceRaised : colors.backgroundSecondary, borderColor: colors.cardBorder }]}>
        <View style={[styles.zoneCell, { backgroundColor: zoneColor }]}>
          <Text style={[styles.zoneText, { color: getZoneTextColor(zone) }]}>{zone}</Text>
        </View>

        <View style={styles.nakshatraCell}>
          <Text style={[styles.nakshatraText, { color: colors.textSecondary }]}>
            {nakshatras.join(', ')}
          </Text>
        </View>

        <View style={styles.planetCell}>
          <Text style={[styles.planetText, { color: colors.text }]}>{planetNames}</Text>
        </View>

        <View style={styles.threatCell}>
          <Text style={[styles.threatText, { color: threat.color }]}>{threat.level}</Text>
        </View>

        <View style={styles.effectCell}>
          <Text style={[styles.effectText, { color: colors.textSecondary }]}>
            {getZoneEffects(zone, planets)}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
      <Text style={[styles.eyebrow, { color: colors.primary }]}>ZONE DETAIL</Text>
      <Text style={[styles.title, { color: colors.text }]}>Fortress analysis</Text>
      <Text style={[styles.subtitle, { color: colors.textSecondary }]}>Nakshatras, visiting planets and the life areas influenced in each layer.</Text>

      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={styles.table}>
          {/* Header */}
          <View style={[styles.headerRow, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
            <View style={styles.zoneCell}>
              <Text style={[styles.headerText, { color: colors.text }]}>Zone</Text>
            </View>
            <View style={styles.nakshatraCell}>
              <Text style={[styles.headerText, { color: colors.text }]}>Nakshatras</Text>
            </View>
            <View style={styles.planetCell}>
              <Text style={[styles.headerText, { color: colors.text }]}>Current Planets</Text>
            </View>
            <View style={styles.threatCell}>
              <Text style={[styles.headerText, { color: colors.text }]}>Threat Level</Text>
            </View>
            <View style={styles.effectCell}>
              <Text style={[styles.headerText, { color: colors.text }]}>Life Areas</Text>
            </View>
          </View>

          {/* Data Rows */}
          {kotaData.fortress_map && Object.entries(kotaData.fortress_map).map(([zone, nakshatras], index) => {
            const planets = kotaData.malefic_siege?.[zone] || [];
            return renderTableRow(zone, nakshatras, planets, index);
          })}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 14,
    borderWidth: 1,
    borderRadius: 22,
    padding: 16,
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
    marginBottom: 14,
  },
  table: {
    borderRadius: 14,
    overflow: 'hidden',
  },
  headerRow: {
    flexDirection: 'row',
    borderWidth: 1,
    borderBottomWidth: 2,
  },
  tableRow: {
    flexDirection: 'row',
    borderWidth: 1,
    borderTopWidth: 0,
  },
  zoneCell: {
    width: 80,
    padding: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  nakshatraCell: {
    width: 200,
    padding: 8,
    justifyContent: 'center',
  },
  planetCell: {
    width: 100,
    padding: 8,
    justifyContent: 'center',
  },
  threatCell: {
    width: 80,
    padding: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  effectCell: {
    width: 140,
    padding: 8,
    justifyContent: 'center',
  },
  headerText: {
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
  },
  zoneText: {
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  nakshatraText: {
    fontSize: 10,
    lineHeight: 14,
  },
  planetText: {
    fontSize: 11,
    fontWeight: '500',
    textAlign: 'center',
  },
  threatText: {
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'center',
  },
  effectText: {
    fontSize: 10,
    lineHeight: 14,
  },
});

export default FortressTable;
