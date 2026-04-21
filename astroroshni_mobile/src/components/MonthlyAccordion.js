import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, LayoutAnimation, Platform, UIManager } from 'react-native';
import { ScrollView as GHScrollView } from 'react-native-gesture-handler';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../context/ThemeContext';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

const stripBhavaTags = (text) => String(text || '')
  .replace(/\[BHAVA-DISAMBIG:[^\]]*\]/g, '')
  .replace(/\s{2,}/g, ' ')
  .trim();

const getPrimaryScenario = (event) => {
  const list = event?.possible_manifestations;
  if (!Array.isArray(list) || list.length === 0) return '';
  const first = list[0];
  return typeof first === 'string' ? first : (first?.scenario || '');
};

const getDisplayPrediction = (event) => {
  const raw = stripBhavaTags(event?.prediction || '');
  const scenario = stripBhavaTags(getPrimaryScenario(event));
  const hasTechnicalNoise = /\b(BHAVA|Karaka|Varga|Threads=|Afflicter|Lord)\b/i.test(raw);
  if (!raw || hasTechnicalNoise) {
    if (scenario) return scenario;
    return '';
  }
  return raw;
};

const getDisplayReason = (event) => {
  const activation = String(event?.activation_reasoning || '').trim();
  const trigger = String(event?.trigger_logic || '').trim();
  return activation || trigger || '';
};

export default function MonthlyAccordion({ data, onChatPress, onDiveDeepPress, defaultExpanded = false, hideDiveDeep = false }) {
  const [expanded, setExpanded] = useState(!!defaultExpanded);
  const [openReasons, setOpenReasons] = useState({});
  const { t } = useTranslation();
  const { theme, colors } = useTheme();

  const toggleExpand = () => {
    setExpanded(!expanded);
  };
  const toggleReason = (idx) => {
    setOpenReasons((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  // Safety checks
  if (!data) return null;
  
  // Get all focus tags (no limit)
  // Some months may carry malformed payloads from upstream (object/string instead of array).
  // Keep rendering resilient so one bad month does not crash the whole yearly screen.
  const tags = Array.isArray(data.focus_areas)
    ? data.focus_areas.filter((x) => x != null).map((x) => String(x))
    : [];
  const events = Array.isArray(data.events) ? data.events : [];

  return (
    <View style={[styles.card, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
      {/* Header row toggles expand; chips scroll is outside TouchableOpacity so horizontal pan works */}
      <TouchableOpacity onPress={toggleExpand} activeOpacity={0.7}>
        <View style={styles.headerRow}>
          <Text style={[styles.monthName, { color: colors.accent }]}>{data.month}</Text>
          <Ionicons
            name={expanded ? "chevron-up" : "chevron-down"}
            size={20}
            color={colors.textSecondary}
          />
        </View>
      </TouchableOpacity>
      {!expanded && tags.length > 0 && (
        <GHScrollView
          horizontal
          nestedScrollEnabled
          showsHorizontalScrollIndicator={false}
          style={styles.chipsRow}
          contentContainerStyle={styles.chipsContent}
        >
          {tags.map((tag, i) => (
            <View key={`chip-${i}`} style={[styles.miniTag, { backgroundColor: colors.surface }]}>
              <Text style={[styles.miniTagText, { color: colors.textSecondary }]}>{tag}</Text>
            </View>
          ))}
        </GHScrollView>
      )}

      {/* Expanded Content */}
      {expanded && (
        <View style={[styles.content, { borderTopColor: colors.cardBorder }]}>
          {/* Theme Header */}
          <View style={styles.themeRow}>
            <Text style={[styles.label, { color: colors.textTertiary }]}>{t('monthlyAccordion.focus', 'FOCUS:')}</Text>
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
            {events.map((event, index) => (
              <View key={index} style={styles.eventItem}>
                <View style={[styles.intensityDot, { backgroundColor: getIntensityColor(event.intensity) }]} />
                <View style={{flex: 1}}>
                  <Text style={[styles.eventType, { color: colors.text }]}>{event.type}</Text>
                  <Text style={[styles.eventDesc, { color: colors.textSecondary }]}>{getDisplayPrediction(event)}</Text>
                  {getDisplayReason(event) ? (
                    <>
                      <TouchableOpacity
                        onPress={() => toggleReason(index)}
                        style={[styles.whyToggle, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}
                        activeOpacity={0.8}
                      >
                        <Text style={[styles.whyToggleText, { color: colors.accent }]}>
                          {openReasons[index] ? 'Hide Why' : 'Show Why'}
                        </Text>
                        <Ionicons
                          name={openReasons[index] ? 'chevron-up' : 'chevron-down'}
                          size={14}
                          color={colors.accent}
                        />
                      </TouchableOpacity>
                      {openReasons[index] ? (
                        <View style={styles.reasonBlock}>
                          <Text style={[styles.reasonTitle, { color: colors.accent }]}>Why:</Text>
                          <Text style={[styles.reasonBody, { color: colors.textTertiary }]}>{getDisplayReason(event)}</Text>
                        </View>
                      ) : null}
                    </>
                  ) : null}
                  {Array.isArray(event?.possible_manifestations) && event.possible_manifestations.length > 0 && (
                    <View style={styles.manifestationsContainer}>
                      <View style={styles.manifestationsHeader}>
                        <Ionicons name="git-network-outline" size={14} color={colors.accent} />
                        <Text style={[styles.manifestationsLabel, { color: colors.accent }]}>{t('monthlyAccordion.possibleScenarios', { count: event.possible_manifestations.length, defaultValue: `Possible Scenarios (${event.possible_manifestations.length})` })}</Text>
                      </View>
                      <View style={styles.manifestationsList}>
                        {event.possible_manifestations.map((item, idx) => {
                          // Handle both old string format and new object format
                          const scenario = typeof item === 'string' ? item : (item?.scenario || '');
                          const reasoning = typeof item === 'object' && item !== null ? item.reasoning : null;
                          
                          return (
                            <View key={idx} style={[styles.manifestationCard, { backgroundColor: colors.surface, borderLeftColor: colors.accent }]}>
                              <View style={styles.manifestationHeader}>
                                <View style={[styles.scenarioNumber, { backgroundColor: colors.accent }]}>
                                  <Text style={[styles.scenarioNumberText, { color: colors.background }]}>{idx + 1}</Text>
                                </View>
                                <View style={{flex: 1}}>
                                  {scenario ? <Text style={[styles.manifestationText, { color: colors.text }]}>{scenario}</Text> : null}
                                  {reasoning && (
                                    <View style={styles.reasoningContainer}>
                                      <Text style={[styles.reasoningLabel, { color: colors.accent }]}>{t('monthlyAccordion.why', 'Why:')}</Text>
                                      <Text style={[styles.reasoningText, { color: colors.textSecondary }]}>{reasoning}</Text>
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
                </View>
              </View>
            ))}
          </View>

          {/* CTA Buttons */}
          {onDiveDeepPress && !hideDiveDeep && (
            <TouchableOpacity
              style={[styles.chatButton, styles.diveDeepButton, { backgroundColor: colors.accent }]}
              onPress={() => onDiveDeepPress(data)}
            >
              <Ionicons name="arrow-down-circle-outline" size={18} color={theme === 'dark' ? colors.background : '#1a1a1a'} />
              <Text style={[styles.chatButtonText, { color: theme === 'dark' ? colors.background : '#1a1a1a' }]}>{t('monthlyAccordion.diveDeep', 'Dive deep into this month')}</Text>
            </TouchableOpacity>
          )}
          {onChatPress ? (
            <TouchableOpacity style={[styles.chatButton, { backgroundColor: colors.primary }]} onPress={onChatPress}>
              <Ionicons name="chatbubbles-outline" size={18} color="white" />
              <Text style={styles.chatButtonText}>{t('monthlyAccordion.askQuestions', 'Ask Questions')}</Text>
            </TouchableOpacity>
          ) : null}
        </View>
      )}
    </View>
  );
}

const getIntensityColor = (intensity) => {
  const normalized = String(intensity ?? '').toLowerCase();
  switch(normalized) {
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
    flexDirection: 'row',
    alignItems: 'center',
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
  whyToggle: {
    marginTop: 4,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  whyToggleText: { fontSize: 12, fontWeight: '700', letterSpacing: 0.2 },
  reasonBlock: {
    marginTop: 4,
    marginBottom: 6,
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderLeftWidth: 2,
    borderLeftColor: 'rgba(255, 255, 255, 0.18)'
  },
  reasonTitle: { fontSize: 11, fontWeight: '700', marginBottom: 2, letterSpacing: 0.4 },
  reasonBody: { fontSize: 12, lineHeight: 17, fontStyle: 'italic' },
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
  
  diveDeepButton: { marginTop: 0, marginBottom: 10 },
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