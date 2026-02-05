import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

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

  const renderTableRow = (zone, nakshatras, planets) => {
    const threat = getThreatLevel(planets);
    const planetNames = planets.map(p => p.planet).join(', ') || 'Empty';
    const zoneColor = getZoneColor(zone);
    
    return (
      <View key={zone} style={[styles.tableRow, { borderColor: colors.cardBorder }]}>
        <View style={[styles.zoneCell, { backgroundColor: zoneColor }]}>
          <Text style={[styles.zoneText, { color: '#ffffff' }]}>{zone}</Text>
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
    <View style={styles.container}>
      <Text style={[styles.title, { color: colors.text }]}>📊 Fortress Analysis Table</Text>
      
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
          {kotaData.fortress_map && Object.entries(kotaData.fortress_map).map(([zone, nakshatras]) => {
            const planets = kotaData.malefic_siege?.[zone] || [];
            return renderTableRow(zone, nakshatras, planets);
          })}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 20,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    textAlign: 'center',
  },
  table: {
    borderRadius: 8,
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