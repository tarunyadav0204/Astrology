import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS } from '../../utils/constants';

const safeString = (value) => {
  if (value === null || value === undefined) return 'N/A';
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  if (typeof value === 'object') {
    if (value.description) return value.description;
    if (value.name) return value.name;
    if (value.text) return value.text;
    return 'Loading...';
  }
  return String(value);
};

export default function CosmicWeather({ data }) {
  if (!data) {
    return (
      <View style={styles.container}>
        <Text style={styles.noDataText}>No forecast data available</Text>
      </View>
    );
  }

  const { current_energy, life_timeline } = data;

  return (
    <View style={styles.container}>
      {current_energy && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Today's Energy</Text>
          <View style={styles.weatherCard}>
            <View style={styles.weatherContent}>
              <View style={styles.currentCycle}>
                <View style={styles.cycleBadge}>
                  <Text style={styles.cycleNumber}>{safeString(current_energy.personal_day?.number)}</Text>
                </View>
                <Text style={styles.cycleLabel}>Personal Day {safeString(current_energy.personal_day?.number)}</Text>
                <Text style={styles.cycleSubtext}>
                  Month {safeString(current_energy.personal_month?.number)} • Year {safeString(current_energy.personal_year?.number)}
                </Text>
              </View>
              
              <Text style={styles.meaning}>
                {safeString(current_energy.personal_day?.description || current_energy.personal_day?.meaning)}
              </Text>
              
              {current_energy.daily_guidance && (
                <View style={styles.guidanceSection}>
                  <Text style={styles.guidanceTitle}>Today's Guidance</Text>
                  <Text style={styles.guidanceText}>
                    {safeString(current_energy.daily_guidance)}
                  </Text>
                </View>
              )}

              {current_energy.calculation_logic && (
                <View style={styles.calculationSection}>
                  <Text style={styles.calculationTitle}>How it's calculated</Text>
                  <Text style={styles.calculationText}>
                    {safeString(current_energy.calculation_logic)}
                  </Text>
                </View>
              )}
            </View>
          </View>
        </View>
      )}

      {life_timeline?.pinnacles && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Life Phases</Text>
          
          {Object.entries(life_timeline.pinnacles).map(([key, phase], index) => {
            const phaseNames = {
              first: "Foundation Phase",
              second: "Growth Phase", 
              third: "Mastery Phase",
              fourth: "Wisdom Phase"
            };
            
            return (
              <View key={index} style={styles.phaseCard}>
                <View style={styles.phaseContent}>
                  <View style={styles.phaseHeader}>
                    <View style={styles.phaseNumber}>
                      <Text style={styles.phaseNumberText}>{safeString(phase.number)}</Text>
                    </View>
                    <View style={styles.phaseInfo}>
                      <Text style={styles.phaseName}>{phaseNames[key]}</Text>
                      <Text style={styles.phaseAge}>Age {safeString(phase.age_range)}</Text>
                    </View>
                  </View>
                  
                  <Text style={styles.phaseMeaning}>
                    {safeString(phase.description || phase.meaning)}
                  </Text>
                </View>
              </View>
            );
          })}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingVertical: 10,
  },
  noDataText: {
    color: 'rgba(255, 255, 255, 0.6)',
    textAlign: 'center',
    fontSize: 16,
    marginTop: 40,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  weatherCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  weatherContent: {
    padding: 20,
  },
  currentCycle: {
    alignItems: 'center',
    marginBottom: 20,
  },
  cycleBadge: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#6366f1',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#6366f1',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  cycleNumber: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.white,
  },
  cycleLabel: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 4,
  },
  cycleSubtext: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  meaning: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 22,
  },
  guidanceSection: {
    backgroundColor: 'rgba(99, 102, 241, 0.1)',
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#6366f1',
    marginBottom: 16,
  },
  guidanceTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#a5b4fc',
    marginBottom: 8,
  },
  guidanceText: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    lineHeight: 20,
  },
  calculationSection: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    padding: 12,
    borderRadius: 8,
  },
  calculationTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: 6,
  },
  calculationText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    lineHeight: 16,
    fontFamily: 'monospace',
  },
  phaseCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    marginBottom: 12,
  },
  phaseContent: {
    padding: 16,
  },
  phaseHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  phaseNumber: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#10b981',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  phaseNumberText: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
  },
  phaseInfo: {
    flex: 1,
  },
  phaseName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 2,
  },
  phaseAge: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  phaseMeaning: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: 20,
  },
});