import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useTheme } from '../../context/ThemeContext';

const getCoreNumberExplanation = (type, number) => {
  const explanations = {
    life_path: {
      6: "Life Path 6 - Your life's main journey and lessons\n\nWhat it means: You're here to nurture, heal, and create harmony\n\nCareer direction: Teaching, healthcare, counseling, family business\n\nLife theme: Service to others, responsibility, creating stable homes/communities"
    },
    expression: {
      4: "Expression 4 - Your natural talents and how you approach tasks\n\nWhat it means: You're naturally organized, practical, and hardworking\n\nStrengths: Building systems, managing details, creating lasting results\n\nWork style: Methodical, reliable, prefers structure over chaos"
    },
    soul_urge: {
      9: "Soul Urge 9 - Your inner desires and what motivates you\n\nWhat it means: Deep down, you want to make the world better\n\nMotivation: Helping humanity, leaving a positive legacy\n\nFulfillment: Comes from serving causes bigger than yourself"
    }
  };
  return explanations[type]?.[number] || `${type.replace('_', ' ')} ${number} - Personal growth and development`;
};

export default function SoulBlueprint({ data }) {
  const { colors } = useTheme();
  const [expandedNumber, setExpandedNumber] = useState(null);
  
  if (!data) {
    return (
      <View style={styles.container}>
        <Text style={[styles.noDataText, { color: colors.textSecondary }]}>No numerology data available</Text>
      </View>
    );
  }

  const { core_numbers, lo_shu_grid } = data;
  const numberTones = {
    life_path: colors.primary,
    expression: colors.success,
    soul_urge: colors.warning,
    personality: colors.error,
  };

  return (
    <View style={styles.container}>
      {/* Core Numbers */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>Core Numbers</Text>
        <View style={styles.numbersGrid}>
          {core_numbers && Object.entries(core_numbers).map(([key, numberObj]) => {
            const displayValue = typeof numberObj === 'object' ? 
              (numberObj?.number || numberObj?.life_path_number) : numberObj;
            const tone = numberTones[key] || colors.secondary;
            return (
              <View key={key} style={styles.numberCard}>
                <TouchableOpacity 
                  style={[styles.numberContent, { backgroundColor: tone }]}
                  onPress={() => setExpandedNumber(expandedNumber === key ? null : key)}
                >
                  <Text style={[styles.numberValue, { color: colors.onPrimary }]}>{displayValue}</Text>
                  <Text style={[styles.numberLabel, { color: colors.onPrimary }]}>{key.replace(/_/g, ' ')}</Text>
                  <Text style={[styles.expandHint, { color: colors.onPrimary, opacity: 0.78 }]}>💡 Tap for details</Text>
                </TouchableOpacity>
                {expandedNumber === key && (
                  <View style={[styles.explanationBox, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                    <Text style={[styles.explanationText, { color: colors.text }]}>
                      {getCoreNumberExplanation(key, displayValue)}
                    </Text>
                  </View>
                )}
              </View>
            );
          })}
        </View>
      </View>

      {/* Lo Shu Grid */}
      {lo_shu_grid && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>Lo Shu Grid</Text>
          <View style={[styles.grid, { backgroundColor: colors.surfaceMuted }]}>
              {[4, 9, 2, 3, 5, 7, 8, 1, 6].map((num, index) => {
                const count = lo_shu_grid.grid_counts?.[num] || 0;
                const filled = count > 0;
                return (
                  <View
                    key={index}
                    style={[
                      styles.gridCell,
                      {
                        backgroundColor: filled ? colors.success : colors.cardBackground,
                        borderColor: colors.cardBorder,
                      },
                    ]}
                  >
                    <Text style={[
                      styles.gridNumber,
                      { color: filled ? colors.onPrimary : colors.textTertiary },
                    ]}>{num}</Text>
                  </View>
                );
              })}
          </View>

          {/* Patterns */}
          {(lo_shu_grid.arrows_of_strength?.length > 0 || lo_shu_grid.missing_numbers?.length > 0) && (
            <View style={styles.patternsSection}>
              {lo_shu_grid.arrows_of_strength?.map((arrow, index) => {
                const isStrength = arrow.type === 'Strength';
                return (
                <View
                  key={index}
                  style={[
                    styles.patternItem,
                    {
                      backgroundColor: colors.surfaceMuted,
                      borderLeftColor: isStrength ? colors.success : colors.error,
                    },
                  ]}
                >
                  <Text style={[styles.patternName, { color: colors.text }]}>{typeof arrow === 'string' ? arrow : arrow?.name || 'Pattern'}</Text>
                  {arrow?.description && <Text style={[styles.patternDescription, { color: colors.textSecondary }]}>{arrow.description}</Text>}
                </View>
                );
              })}
              
              {lo_shu_grid.missing_numbers?.map((missing, index) => (
                <View
                  key={index}
                  style={[
                    styles.missingItem,
                    { backgroundColor: colors.surfaceMuted, borderLeftColor: colors.warning },
                  ]}
                >
                  <View style={styles.missingHeader}>
                    <Text style={[styles.missingNumber, { color: colors.warning }]}>{missing.number}</Text>
                    <Text style={[styles.missingEnergy, { color: colors.text }]}>{missing.missing_energy}</Text>
                  </View>
                  <Text style={[styles.missingLesson, { color: colors.textSecondary }]}>{missing.lesson}</Text>
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
    marginBottom: 6,
  },
  numberLabel: {
    fontSize: 12,
    textAlign: 'center',
    textTransform: 'capitalize',
    fontWeight: '500',
  },
  expandHint: {
    fontSize: 10,
    textAlign: 'center',
    marginTop: 4,
  },
  explanationBox: {
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
    borderWidth: StyleSheet.hairlineWidth,
  },
  explanationText: {
    fontSize: 12,
    lineHeight: 16,
  },

  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
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
    marginBottom: 14,
    borderWidth: StyleSheet.hairlineWidth,
  },
  gridNumber: {
    fontSize: 18,
    fontWeight: '600',
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
  patternName: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  patternDescription: {
    fontSize: 13,
    lineHeight: 18,
  },
  missingItem: {
    padding: 14,
    borderRadius: 10,
    marginBottom: 10,
    borderLeftWidth: 3,
  },
  missingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  missingNumber: {
    fontSize: 16,
    fontWeight: '700',
    marginRight: 8,
    width: 24,
  },
  missingEnergy: {
    fontSize: 14,
    fontWeight: '600',
  },
  missingLesson: {
    fontSize: 13,
    lineHeight: 18,
  },
});
