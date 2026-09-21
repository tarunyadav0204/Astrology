import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform } from 'react-native';
import { useTheme } from '../../context/ThemeContext';

// Helper functions for actionable advice
const getActionableAdvice = (dayNumber) => {
  const advice = {
    1: "Start new projects, take leadership, make important decisions",
    2: "Collaborate, negotiate, focus on partnerships and teamwork", 
    3: "Communicate, create, network, express your ideas publicly",
    4: "Organize, plan, handle details, build systems and processes",
    5: "Explore opportunities, travel, try new approaches, be flexible",
    6: "Focus on family, home, help others, make improvements",
    7: "Research, analyze, study, reflect, work alone on important projects",
    8: "Handle business matters, make financial decisions, focus on career",
    9: "Complete projects, help others, focus on bigger picture goals"
  };
  return advice[dayNumber] || "Focus on balance and intuition";
};

const getMonthFocus = (monthNumber) => {
  const focus = {
    1: "New beginnings", 2: "Building relationships", 3: "Creative expression",
    4: "Hard work pays off", 5: "Change & freedom", 6: "Family & responsibility", 
    7: "Inner development", 8: "Material success", 9: "Completion & service"
  };
  return focus[monthNumber] || "Personal growth";
};

const getYearTheme = (yearNumber) => {
  const themes = {
    1: "Fresh starts & independence", 2: "Cooperation & patience", 3: "Creativity & social expansion",
    4: "Building foundations", 5: "Freedom & adventure", 6: "Love & responsibility",
    7: "Spiritual growth", 8: "Achievement & recognition", 9: "Humanitarian service"
  };
  return themes[yearNumber] || "Personal transformation";
};

const getPinnacleExplanation = (number, ageRange) => {
  const explanations = {
    1: `The number 1 is your Pinnacle Number for ages ${ageRange}. It represents leadership and independence.\n\nWhat it means: You're here to lead, innovate, and pioneer new paths\n\nCareer Success: Leadership roles, entrepreneurship, creative leadership\n\nHow to use this: Take initiative, trust your instincts, embrace leadership opportunities`,
    6: `The number 6 is your Pinnacle Number for ages ${ageRange}. It represents service and nurturing.\n\nWhat it means: You're here to nurture, heal, and create harmony\n\nCareer Success: Teaching, healthcare, counseling, family business\n\nHow to use this: Embrace roles where you can help and support others`,
    8: `The number 8 is your Pinnacle Number for ages ${ageRange}. It represents achievement and authority.\n\nWhat it means: You're here to achieve material success and use power wisely\n\nCareer Success: Business, finance, executive roles, material accomplishment\n\nHow to use this: Focus on ambitious goals and building lasting enterprises`
  };
  return explanations[number] || `Pinnacle ${number} energy for ages ${ageRange} - Focus on personal growth and development`;
};

const renderFormattedText = (text, accentColor) => {
  if (!text || typeof text !== 'string') return text;
  
  const parts = text.split(/\*\*(.*?)\*\*/g);
  return parts.map((part, index) => {
    if (index % 2 === 1) {
      return (
        <Text key={index} style={{ fontWeight: '700', color: accentColor }}>
          {part}
        </Text>
      );
    }
    return part;
  });
};

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
  const { colors } = useTheme();
  const [expandedPhase, setExpandedPhase] = useState(null);
  
  if (!data) {
    return (
      <View style={styles.container}>
        <Text style={[styles.noDataText, { color: colors.textSecondary }]}>No forecast data available</Text>
      </View>
    );
  }

  const { current_energy, life_timeline } = data;

  return (
    <View style={styles.container}>
      {current_energy && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>📅 Today's Energy Focus</Text>
          <View style={[styles.weatherCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
            <View style={styles.weatherContent}>
              <View style={styles.currentCycle}>
                <View style={[styles.cycleBadge, { backgroundColor: colors.primary }]}>
                  <Text style={[styles.cycleNumber, { color: colors.onPrimary }]}>{safeString(current_energy.personal_day?.number)}</Text>
                </View>
                <Text style={[styles.cycleLabel, { color: colors.text }]}>Personal Day {safeString(current_energy.personal_day?.number)}</Text>
                <Text style={[styles.cycleSubtext, { color: colors.textSecondary }]}>
                  Month {safeString(current_energy.personal_month?.number)} • Year {safeString(current_energy.personal_year?.number)}
                </Text>
              </View>
              
              <View style={[styles.actionSection, { backgroundColor: colors.surfaceMuted }]}>
                <Text style={[styles.actionTitle, { color: colors.primary }]}>Best Actions Today:</Text>
                <Text style={[styles.actionText, { color: colors.text }]}>
                  {getActionableAdvice(current_energy.personal_day?.number)}
                </Text>
              </View>
              
              <View style={styles.contextSection}>
                <View style={[styles.contextItem, { backgroundColor: colors.surfaceMuted }]}>
                  <Text style={[styles.contextLabel, { color: colors.textTertiary }]}>This Month:</Text>
                  <Text style={[styles.contextValue, { color: colors.text }]}>{getMonthFocus(current_energy.personal_month?.number)}</Text>
                </View>
                <View style={[styles.contextItem, { backgroundColor: colors.surfaceMuted }]}>
                  <Text style={[styles.contextLabel, { color: colors.textTertiary }]}>This Year:</Text>
                  <Text style={[styles.contextValue, { color: colors.text }]}>{getYearTheme(current_energy.personal_year?.number)}</Text>
                </View>
              </View>
              
              {current_energy.daily_guidance && (
                <View style={[styles.guidanceSection, { backgroundColor: colors.surfaceMuted, borderLeftColor: colors.primary }]}>
                  <Text style={[styles.guidanceTitle, { color: colors.primary }]}>Today's Guidance</Text>
                  <Text style={[styles.guidanceText, { color: colors.text }]}>
                    {renderFormattedText(safeString(current_energy.daily_guidance), colors.accent)}
                  </Text>
                </View>
              )}

              {current_energy.calculation_logic && (
                <View style={[styles.calculationSection, { backgroundColor: colors.backgroundTertiary || colors.surfaceMuted }]}>
                  <Text style={[styles.calculationTitle, { color: colors.textSecondary }]}>How it's calculated</Text>
                  <Text style={[styles.calculationText, { color: colors.textTertiary }]}>
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
          <Text style={[styles.sectionTitle, { color: colors.text }]}>🎯 Your Life Strategy Phases</Text>
          <Text style={[styles.sectionDescription, { color: colors.textSecondary }]}>Your life has 4 strategic phases. Each phase has specific goals and opportunities:</Text>
          
          {Object.entries(life_timeline.pinnacles).map(([key, phase], index) => {
            const phaseNames = {
              first: "Foundation Phase",
              second: "Growth Phase", 
              third: "Mastery Phase",
              fourth: "Wisdom Phase"
            };
            
            const phaseGoals = {
              first: "Develop skills, establish identity, create stability",
              second: "Explore opportunities, build network, gain experience", 
              third: "Maximize achievements, lead others, reach peak performance",
              fourth: "Mentor others, leave legacy, focus on meaning"
            };
            
            return (
              <View key={index} style={[styles.phaseCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
                <TouchableOpacity 
                  style={styles.phaseContent}
                  onPress={() => setExpandedPhase(expandedPhase === key ? null : key)}
                >
                  <View style={styles.phaseHeader}>
                    <View style={[styles.phaseNumber, { backgroundColor: colors.accent }]}>
                      <Text style={[styles.phaseNumberText, { color: colors.onAccent }]}>{safeString(phase.number)}</Text>
                    </View>
                    <View style={styles.phaseInfo}>
                      <Text style={[styles.phaseName, { color: colors.text }]}>{phaseNames[key]}</Text>
                      <Text style={[styles.phaseAge, { color: colors.textSecondary }]}>Age {safeString(phase.age_range)}</Text>
                    </View>
                  </View>
                  
                  <Text style={[styles.phaseGoals, { color: colors.textSecondary }]}>
                    <Text style={[styles.bold, { color: colors.text }]}>Goals:</Text> {phaseGoals[key]}
                  </Text>
                  
                  <Text style={[styles.phaseMeaning, { color: colors.textSecondary }]}>
                    <Text style={[styles.bold, { color: colors.text }]}>Pinnacle #{safeString(phase.number)}:</Text> {safeString(phase.description || phase.meaning)}
                  </Text>
                  
                  <Text style={[styles.expandHint, { color: colors.primary }]}>💡 Tap for detailed explanation</Text>
                </TouchableOpacity>
                
                {expandedPhase === key && (
                  <View style={[styles.explanationBox, { backgroundColor: colors.surfaceMuted, borderLeftColor: colors.primary }]}>
                    <Text style={[styles.explanationText, { color: colors.text }]}>
                      {getPinnacleExplanation(phase.number, phase.age_range)}
                    </Text>
                  </View>
                )}
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
  weatherCard: {
    borderRadius: 16,
    borderWidth: 1,
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
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  cycleNumber: {
    fontSize: 28,
    fontWeight: '700',
  },
  cycleLabel: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  cycleSubtext: {
    fontSize: 14,
  },
  guidanceSection: {
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 3,
    marginBottom: 16,
  },
  guidanceTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  guidanceText: {
    fontSize: 14,
    lineHeight: 20,
  },
  calculationSection: {
    padding: 12,
    borderRadius: 8,
  },
  calculationTitle: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 6,
  },
  calculationText: {
    fontSize: 12,
    lineHeight: 16,
    ...(Platform.OS === 'ios' ? { fontFamily: 'Courier' } : {}),
  },
  phaseCard: {
    borderRadius: 12,
    borderWidth: 1,
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
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  phaseNumberText: {
    fontSize: 20,
    fontWeight: '700',
  },
  phaseInfo: {
    flex: 1,
  },
  phaseName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  phaseAge: {
    fontSize: 13,
  },
  phaseMeaning: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 8,
  },
  actionSection: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  actionTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  actionText: {
    fontSize: 14,
    lineHeight: 20,
  },
  contextSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  contextItem: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  contextLabel: {
    fontSize: 11,
    marginBottom: 4,
  },
  contextValue: {
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  sectionDescription: {
    fontSize: 14,
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  phaseGoals: {
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 8,
  },
  bold: {
    fontWeight: '600',
  },
  expandHint: {
    fontSize: 11,
    textAlign: 'center',
    marginTop: 8,
  },
  explanationBox: {
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
    borderLeftWidth: 3,
  },
  explanationText: {
    fontSize: 12,
    lineHeight: 16,
  },
});
