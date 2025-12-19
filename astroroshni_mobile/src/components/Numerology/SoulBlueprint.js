import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS } from '../../utils/constants';

export default function SoulBlueprint({ data }) {
  if (!data) {
    return (
      <View style={styles.container}>
        <Text style={styles.noDataText}>No numerology data available</Text>
      </View>
    );
  }

  const { core_numbers, lo_shu_grid } = data;

  return (
    <View style={styles.container}>
      {/* Core Numbers */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Core Numbers</Text>
        <View style={styles.numbersGrid}>
          {core_numbers && Object.entries(core_numbers).map(([key, numberObj]) => {
            const displayValue = typeof numberObj === 'object' ? numberObj?.number : numberObj;
            const colors = {
              life_path: '#6366f1',
              expression: '#10b981', 
              soul_urge: '#f59e0b',
              personality: '#ef4444'
            };
            return (
              <View key={key} style={styles.numberCard}>
                <View style={[styles.numberContent, { backgroundColor: colors[key] || '#6b7280' }]}>
                  <Text style={styles.numberValue}>{displayValue}</Text>
                  <Text style={styles.numberLabel}>{key.replace(/_/g, ' ')}</Text>
                </View>
              </View>
            );
          })}
        </View>
      </View>

      {/* Lo Shu Grid */}
      {lo_shu_grid && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Lo Shu Grid</Text>
          <View style={styles.grid}>
              {[4, 9, 2, 3, 5, 7, 8, 1, 6].map((num, index) => {
                const count = lo_shu_grid.grid_counts?.[num] || 0;
                return (
                  <View key={index} style={[styles.gridCell, count > 0 && styles.filledCell]}>
                    <Text style={[styles.gridNumber, count > 0 && styles.activeGridNumber]}>{num}</Text>
                  </View>
                );
              })}
          </View>

          {/* Patterns */}
          {(lo_shu_grid.arrows_of_strength?.length > 0 || lo_shu_grid.missing_numbers?.length > 0) && (
            <View style={styles.patternsSection}>
              {lo_shu_grid.arrows_of_strength?.map((arrow, index) => (
                <View key={index} style={[styles.patternItem, arrow.type === 'Strength' ? styles.strengthPattern : styles.weaknessPattern]}>
                  <Text style={styles.patternName}>{typeof arrow === 'string' ? arrow : arrow?.name || 'Pattern'}</Text>
                  {arrow?.description && <Text style={styles.patternDescription}>{arrow.description}</Text>}
                </View>
              ))}
              
              {lo_shu_grid.missing_numbers?.map((missing, index) => (
                <View key={index} style={styles.missingItem}>
                  <View style={styles.missingHeader}>
                    <Text style={styles.missingNumber}>{missing.number}</Text>
                    <Text style={styles.missingEnergy}>{missing.missing_energy}</Text>
                  </View>
                  <Text style={styles.missingLesson}>{missing.lesson}</Text>
                </View>
              ))}
            </View>
          )}
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
  numbersGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 12,
  },
  numberCard: {
    width: '48%',
    marginBottom: 12,
  },
  numberContent: {
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  numberValue: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.white,
    marginBottom: 6,
  },
  numberLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    textTransform: 'capitalize',
    fontWeight: '500',
  },

  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 20,
    paddingHorizontal: 8,
    paddingTop: 18,
    paddingBottom: 0,
    justifyContent: 'space-between',
  },
  gridCell: {
    width: '31%',
    aspectRatio: 1,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    marginBottom: 14,
  },
  filledCell: {
    backgroundColor: 'rgba(17, 231, 243, 0.68)',
  },
  gridNumber: {
    fontSize: 18,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  activeGridNumber: {
    color: '#ffffff',
  },
  gridCount: {
    fontSize: 10,
    color: '#e0e7ff',
    fontWeight: '700',
    marginTop: 2,
  },
  patternsSection: {
    marginTop: 16,
  },
  patternItem: {
    padding: 14,
    borderRadius: 10,
    marginBottom: 10,
    borderLeftWidth: 3,
  },
  strengthPattern: {
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderLeftColor: '#10b981',
  },
  weaknessPattern: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderLeftColor: '#ef4444',
  },
  patternName: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 4,
  },
  patternDescription: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: 18,
  },
  missingItem: {
    backgroundColor: 'rgba(245, 158, 11, 0.1)',
    padding: 14,
    borderRadius: 10,
    marginBottom: 10,
    borderLeftWidth: 3,
    borderLeftColor: '#f59e0b',
  },
  missingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  missingNumber: {
    fontSize: 16,
    fontWeight: '700',
    color: '#fbbf24',
    marginRight: 8,
    width: 24,
  },
  missingEnergy: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
  },
  missingLesson: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: 18,
  },
});