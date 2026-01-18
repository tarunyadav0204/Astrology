import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, LayoutAnimation, ScrollView } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../context/ThemeContext';

export default function MonthlyAccordion({ data, onChatPress }) {
  const [expanded, setExpanded] = useState(false);
  const { colors } = useTheme();

  const toggleExpand = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpanded(!expanded);
  };

  // Get all focus tags (no limit)
  const tags = data.focus_areas || [];

  return (
    <View style={[styles.card, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
      {/* Header (Always Visible) */}
      <TouchableOpacity onPress={toggleExpand} activeOpacity={0.7}>
        {/* Row 1: Month name + chevron */}
        <View style={styles.headerRow}>
          <Text style={[styles.monthName, { color: colors.accent }]}>{data.month}</Text>
          <Ionicons 
            name={expanded ? "chevron-up" : "chevron-down"} 
            size={20} 
            color={colors.textSecondary} 
          />
        </View>
        
        {/* Row 2: All chips in horizontal scroll (only when collapsed) */}
        {!expanded && tags.length > 0 && (
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            style={styles.chipsRow}
            contentContainerStyle={styles.chipsContent}
          >
            {tags.map((tag, i) => (
              <View key={`chip-${i}`} style={[styles.miniTag, { backgroundColor: colors.surface }]}>
                <Text style={[styles.miniTagText, { color: colors.textSecondary }]}>{tag}</Text>
              </View>
            ))}
          </ScrollView>
        )}
      </TouchableOpacity>

      {/* Expanded Content */}
      {expanded && (
        <View style={[styles.content, { borderTopColor: colors.cardBorder }]}>
          {/* Theme Header */}
          <View style={styles.themeRow}>
            <Text style={[styles.label, { color: colors.textTertiary }]}>FOCUS:</Text>
            <View style={styles.expandedTagContainer}>
              {tags.map((tag, i) => (
                <View key={i} style={[styles.fullTag, { backgroundColor: colors.surface }]}>
                  <Text style={[styles.fullTagText, { color: colors.textSecondary }]}>{tag}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Events List */}
          <View style={styles.eventsList}>
            {data.events?.map((event, index) => (
              <View key={index} style={styles.eventItem}>
                <View style={[styles.intensityDot, { backgroundColor: getIntensityColor(event.intensity) }]} />
                <View style={{flex: 1}}>
                  <Text style={[styles.eventType, { color: colors.text }]}>{event.type}</Text>
                  <Text style={[styles.eventDesc, { color: colors.textSecondary }]}>{event.prediction}</Text>
                  {event.possible_manifestations && event.possible_manifestations.length > 0 && (
                    <View style={styles.manifestationsContainer}>
                      <View style={styles.manifestationsHeader}>
                        <Ionicons name="git-network-outline" size={14} color={colors.accent} />
                        <Text style={[styles.manifestationsLabel, { color: colors.accent }]}>Possible Scenarios ({event.possible_manifestations.length})</Text>
                      </View>
                      <View style={styles.manifestationsList}>
                        {event.possible_manifestations.map((item, idx) => {
                          // Handle both old string format and new object format
                          const scenario = typeof item === 'string' ? item : item.scenario;
                          const reasoning = typeof item === 'object' ? item.reasoning : null;
                          
                          return (
                            <View key={idx} style={[styles.manifestationCard, { backgroundColor: colors.surface, borderLeftColor: colors.accent }]}>
                              <View style={styles.manifestationHeader}>
                                <View style={[styles.scenarioNumber, { backgroundColor: colors.accent }]}>
                                  <Text style={[styles.scenarioNumberText, { color: colors.background }]}>{idx + 1}</Text>
                                </View>
                                <View style={{flex: 1}}>
                                  <Text style={[styles.manifestationText, { color: colors.text }]} numberOfLines={0}>{scenario}</Text>
                                  {reasoning && (
                                    <View style={styles.reasoningContainer}>
                                      <Text style={[styles.reasoningLabel, { color: colors.accent }]}>Why:</Text>
                                      <Text style={[styles.reasoningText, { color: colors.textSecondary }]} numberOfLines={0}>{reasoning}</Text>
                                    </View>
                                  )}
                                </View>
                              </View>
                            </View>
                          );
                        })}
                      </View>
                    </View>
                  )}
                  {event.start_date && event.end_date && (
                    <Text style={[styles.eventDates, { color: colors.accent }]}>
                      📅 {event.start_date} to {event.end_date}
                    </Text>
                  )}
                  {event.trigger_logic && (
                    <Text style={[styles.triggerLogic, { color: colors.textTertiary }]}>
                      🎯 {event.trigger_logic}
                    </Text>
                  )}
                </View>
              </View>
            ))}
          </View>

          {/* CTA Button */}
          <TouchableOpacity style={[styles.chatButton, { backgroundColor: colors.primary }]} onPress={onChatPress}>
            <Ionicons name="chatbubbles-outline" size={18} color="white" />
            <Text style={styles.chatButtonText}>Analyze {data.month}</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const getIntensityColor = (intensity) => {
  switch(intensity?.toLowerCase()) {
    case 'high': return '#FF4444';
    case 'medium': return '#FFAA00';
    default: return '#4CAF50';
  }
};

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    marginBottom: 12,
    overflow: 'hidden',
    borderWidth: 1,
    elevation: 2
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  monthName: { fontSize: 17, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5 },
  chipsRow: {
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  chipsContent: {
    gap: 6,
  },
  miniTag: { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 8 },
  miniTagText: { fontSize: 11, fontWeight: '600' },
  
  content: {
    padding: 16,
    paddingTop: 0,
    borderTopWidth: 1
  },
  themeRow: { flexDirection: 'row', alignItems: 'center', marginTop: 12, marginBottom: 12 },
  label: { fontSize: 11, fontWeight: '700', marginRight: 10, letterSpacing: 0.5 },
  expandedTagContainer: { flexDirection: 'row', gap: 8, flexWrap: 'wrap', flex: 1 },
  fullTag: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 10 },
  fullTagText: { fontSize: 12, fontWeight: '600' },
  
  eventsList: { gap: 14 },
  eventItem: { flexDirection: 'row', gap: 10, alignItems: 'flex-start' },
  intensityDot: { width: 8, height: 8, borderRadius: 4, marginTop: 6 },
  eventType: { fontSize: 14, fontWeight: '700', marginBottom: 4, letterSpacing: 0.3 },
  eventDesc: { fontSize: 14, lineHeight: 20, marginBottom: 4 },
  manifestationsContainer: { marginTop: 12, marginBottom: 8 },
  manifestationsHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 10 },
  manifestationsLabel: { fontSize: 12, fontWeight: '700', letterSpacing: 0.5 },
  manifestationsList: { gap: 8 },
  manifestationCard: { 
    borderRadius: 10, 
    padding: 12, 
    borderLeftWidth: 3,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2
  },
  manifestationHeader: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  scenarioNumber: { 
    width: 22, 
    height: 22, 
    borderRadius: 11, 
    justifyContent: 'center', 
    alignItems: 'center',
    marginTop: 2,
    flexShrink: 0
  },
  scenarioNumberText: { fontSize: 11, fontWeight: '700' },
  manifestationText: { fontSize: 13, lineHeight: 19, fontWeight: '600', marginBottom: 6 },
  reasoningContainer: { marginTop: 6, paddingTop: 8, borderTopWidth: 1, borderTopColor: 'rgba(255, 255, 255, 0.1)' },
  reasoningLabel: { fontSize: 11, fontWeight: '700', marginBottom: 4, letterSpacing: 0.5 },
  reasoningText: { fontSize: 12, lineHeight: 18, fontStyle: 'italic' },
  eventDates: { fontSize: 12, fontWeight: '600', marginTop: 6 },
  triggerLogic: { fontSize: 11, fontStyle: 'italic', marginTop: 4, lineHeight: 16 },
  
  chatButton: {
    flexDirection: 'row',
    padding: 14,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 16,
    gap: 8,
    elevation: 2
  },
  chatButtonText: { color: 'white', fontWeight: '700', fontSize: 15, letterSpacing: 0.3 }
});