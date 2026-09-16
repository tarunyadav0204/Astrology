import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, LayoutAnimation, Platform, UIManager } from 'react-native';
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

const getRelativeEventTitle = (event) => {
  const title = String(event?.type || event?.event_family || '').trim();
  return title.includes('·') ? title.split('·').slice(1).join('·').trim() : title;
};

const getPhaseLabel = (phase, t) => ({
  result_window: t('monthlyAccordion.phaseOutcome', 'Outcome window'),
  developing: t('monthlyAccordion.phaseDeveloping', 'Developing'),
  preparatory: t('monthlyAccordion.phasePreparatory', 'Preparatory'),
  obstructed: t('monthlyAccordion.phaseObstructed', 'Obstructed'),
}[String(phase || '').toLowerCase()] || t('monthlyAccordion.phaseSecondary', 'Secondary possibility'));

const getSupportLabel = (event, t) => {
  if (event?.support_label) return String(event.support_label);
  return ({
    A: t('monthlyAccordion.strongIndication', 'Strong indication'),
    B: t('monthlyAccordion.moderateIndication', 'Moderate indication'),
    C: t('monthlyAccordion.weakIndication', 'Weak indication'),
  })[String(event?.support_grade || '').toUpperCase()] || '';
};

export default function MonthlyAccordion({ data, onChatPress, onDiveDeepPress, defaultExpanded = false, hideDiveDeep = false, relativeProfiles = [] }) {
  const [expanded, setExpanded] = useState(!!defaultExpanded);
  const [openReasons, setOpenReasons] = useState({});
  const [openScenarioReasons, setOpenScenarioReasons] = useState({});
  const [peopleExpanded, setPeopleExpanded] = useState(false);
  const [openPeopleSubjects, setOpenPeopleSubjects] = useState({});
  const [openPeopleReasons, setOpenPeopleReasons] = useState({});
  const [openSecondarySections, setOpenSecondarySections] = useState({});
  const [openBackgroundReasons, setOpenBackgroundReasons] = useState({});
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';

  const toggleExpand = () => {
    setExpanded(!expanded);
  };
  const toggleReason = (idx) => {
    setOpenReasons((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };
  const toggleScenarioReason = (eventIdx, scenarioIdx) => {
    const key = `${eventIdx}:${scenarioIdx}`;
    setOpenScenarioReasons((prev) => ({ ...prev, [key]: !prev[key] }));
  };
  const toggleSecondarySection = (key) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setOpenSecondarySections((prev) => ({ ...prev, [key]: !prev[key] }));
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
  const legacyBackgroundEvents = Array.isArray(data.background_candidates)
    ? data.background_candidates.filter((event) => event && typeof event === 'object')
    : [];
  const hasTieredBackground = [
    data.also_possible_candidates,
    data.ongoing_background_candidates,
    data.weak_signal_candidates,
  ].some(Array.isArray);
  const alsoPossibleEvents = hasTieredBackground && Array.isArray(data.also_possible_candidates)
    ? data.also_possible_candidates.filter((event) => event && typeof event === 'object')
    : legacyBackgroundEvents;
  const ongoingEvents = Array.isArray(data.ongoing_background_candidates)
    ? data.ongoing_background_candidates.filter((event) => event && typeof event === 'object')
    : [];
  const developingEvents = Array.isArray(data.annual_context_candidates)
    ? data.annual_context_candidates.filter((event) => event && typeof event === 'object')
    : [];
  const weakSignalEvents = Array.isArray(data.weak_signal_candidates)
    ? data.weak_signal_candidates.filter((event) => event && typeof event === 'object')
    : [];
  const secondaryCount = alsoPossibleEvents.length + ongoingEvents.length + developingEvents.length + weakSignalEvents.length;
  const secondarySections = [
    {
      key: 'alsoPossible',
      events: alsoPossibleEvents,
      title: t('monthlyAccordion.alsoPossible', { count: alsoPossibleEvents.length, defaultValue: `Also possible (${alsoPossibleEvents.length})` }),
      hint: t('monthlyAccordion.alsoPossibleHint', 'Credible alternatives, but less clear than the main possibilities this month.'),
    },
    {
      key: 'ongoingThemes',
      events: ongoingEvents,
      title: t('monthlyAccordion.ongoingThemes', { count: ongoingEvents.length, defaultValue: `Ongoing themes (${ongoingEvents.length})` }),
      hint: t('monthlyAccordion.ongoingThemesHint', 'These areas remain active, but this month is not a clear peak for an event.'),
    },
    {
      key: 'developingThemes',
      events: developingEvents,
      title: t('monthlyAccordion.developingThemes', { count: developingEvents.length, defaultValue: `Developing themes (${developingEvents.length})` }),
      hint: t('monthlyAccordion.developingThemesHint', 'These matters are relevant this year and may be building now, although stronger outcome timing appears in another month.'),
    },
    {
      key: 'weakSignals',
      events: weakSignalEvents,
      title: t('monthlyAccordion.weakSignals', { count: weakSignalEvents.length, defaultValue: `Weak signals (${weakSignalEvents.length})` }),
      hint: t('monthlyAccordion.weakSignalsHint', 'Incomplete or mixed support. Do not treat these as predictions.'),
    },
  ].filter((section) => section.events.length > 0);
  const peopleEvents = Array.isArray(data.people_candidates)
    ? data.people_candidates.filter((event) => event && typeof event === 'object')
    : [];
  const tieredPeopleLists = [
    data.people_also_possible_candidates,
    data.people_ongoing_background_candidates,
    data.people_annual_context_candidates,
    data.people_weak_signal_candidates,
  ];
  const hasTieredPeople = tieredPeopleLists.some(Array.isArray);
  const peopleOverflowEvents = hasTieredPeople
    ? tieredPeopleLists.flatMap((list) => Array.isArray(list) ? list : [])
      .filter((event) => event && typeof event === 'object')
    : (Array.isArray(data.people_background_candidates)
      ? data.people_background_candidates.filter((event) => event && typeof event === 'object')
      : []);
  const allPeopleEvents = [...peopleEvents, ...peopleOverflowEvents];
  const configuredPeople = [
    ...(Array.isArray(relativeProfiles) ? relativeProfiles : []),
    ...(Array.isArray(data.people_evaluations) ? data.people_evaluations : []),
  ]
    .filter((profile) => profile && profile.enabled !== false && profile.life_status !== 'deceased')
    .map((profile) => ({
      subjectKey: String(profile.subject_key || profile.key || ''),
      subjectLabel: profile.display_label || profile.subject_label || profile.label || t('monthlyAccordion.relative', 'Relative'),
    }))
    .filter((profile) => profile.subjectKey);
  const seededPeopleGroups = configuredPeople.reduce((groups, profile) => {
    groups[profile.subjectKey] = { ...profile, events: [] };
    return groups;
  }, {});
  const peopleGroups = Object.values(allPeopleEvents.reduce((groups, event) => {
    const subjectKey = String(event?.subject_key || 'relative');
    if (!groups[subjectKey]) {
      groups[subjectKey] = {
        subjectKey,
        subjectLabel: event?.subject_label || t('monthlyAccordion.relative', 'Relative'),
        events: [],
      };
    }
    groups[subjectKey].events.push(event);
    return groups;
  }, seededPeopleGroups)).map((group) => ({
    ...group,
    events: group.events.sort((a, b) => Number(b?.priority_score || 0) - Number(a?.priority_score || 0)),
  })).sort((a, b) => a.subjectLabel.localeCompare(b.subjectLabel));
  const peopleCount = allPeopleEvents.length;
  const personCount = peopleGroups.length;
  const backgroundLabels = ongoingEvents
    .map((event) => String(event?.type || event?.event_family || '').trim())
    .filter(Boolean);

  return (
    <View
      style={[
        styles.card,
        { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder },
        isDark ? styles.cardDarkFlat : styles.cardLightElevated,
      ]}
    >
      {/* Header row toggles expand; collapsed focus chips wrap within the card. */}
      <TouchableOpacity onPress={toggleExpand} activeOpacity={0.7}>
        <View style={styles.headerRow}>
          <Text style={[styles.monthName, { color: colors.accent }]}>{data.month}</Text>
          <View style={styles.headerActions}>
            {personCount > 0 ? (
              <View style={[styles.peopleCountBadge, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}>
                <Ionicons name="people-outline" size={12} color={colors.accent} />
                <Text style={[styles.backgroundCountText, { color: colors.textTertiary }]}>
                  {t('monthlyAccordion.peopleCount', { count: personCount, defaultValue: `People · ${personCount}` })}
                </Text>
              </View>
            ) : null}
            {secondaryCount > 0 ? (
              <View style={[styles.backgroundCountBadge, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}>
                <Text style={[styles.backgroundCountText, { color: colors.textTertiary }]}>
                  {t('monthlyAccordion.moreSignalsCount', {
                    count: secondaryCount,
                    defaultValue: `${secondaryCount} more`,
                  })}
                </Text>
              </View>
            ) : null}
            <Ionicons
              name={expanded ? "chevron-up" : "chevron-down"}
              size={20}
              color={colors.textSecondary}
            />
          </View>
        </View>
      </TouchableOpacity>
      {!expanded && tags.length > 0 && (
        <View style={styles.chipsRow}>
          <View style={styles.chipsContent}>
            {tags.map((tag, i) => (
              <View key={`chip-${i}`} style={[styles.miniTag, { backgroundColor: colors.surface }]}>
                <Text style={[styles.miniTagText, { color: colors.textSecondary }]}>{tag}</Text>
              </View>
            ))}
          </View>
        </View>
      )}
      {!expanded && backgroundLabels.length > 0 ? (
        <View style={[styles.backgroundPreview, { borderTopColor: colors.cardBorder }]}>
          <Text style={[styles.backgroundPreviewLabel, { color: colors.textTertiary }]}>
            {t('monthlyAccordion.backgroundThemes', 'BACKGROUND THEMES:')}
          </Text>
          <View style={styles.chipsContent}>
            {backgroundLabels.map((label, index) => (
              <View key={`background-chip-${index}`} style={[styles.backgroundMiniTag, { borderColor: colors.cardBorder }]}>
                <Text style={[styles.miniTagText, { color: colors.textTertiary }]}>{label}</Text>
              </View>
            ))}
          </View>
        </View>
      ) : null}

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
            {events.length > 0 ? (
              <Text style={[styles.sectionMeaning, { color: colors.textTertiary }]}>
                {t('monthlyAccordion.mainPossibilitiesHint', 'The clearest supported possibilities for this month—not guaranteed outcomes.')}
              </Text>
            ) : null}
            {events.length === 0 ? (
              <View style={[styles.quietMonthCard, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
                <Ionicons name="moon-outline" size={18} color={colors.textTertiary} />
                <Text style={[styles.quietMonthText, { color: colors.textSecondary }]}>
                  {secondaryCount > 0 || peopleCount > 0
                    ? t(
                      'monthlyAccordion.noHeadlineEvent',
                      'No single headline event stands out this month. Continuing, developing, and weaker possibilities are organized below so you can still see what may be taking shape.'
                    )
                    : t(
                      'monthlyAccordion.insufficientEvidence',
                      'This month has fewer clear event triggers. It is better suited to preparation, review, and ongoing matters than to one major predicted outcome.'
                    )}
                </Text>
              </View>
            ) : null}
            {events.map((event, index) => (
              <View key={index} style={styles.eventItem}>
                <View style={[styles.intensityDot, { backgroundColor: getIntensityColor(event.intensity) }]} />
                <View style={{flex: 1, minWidth: 0}}>
                  <View style={styles.eventTitleRow}>
                    <Text style={[styles.eventType, { color: colors.text }]}>{event.type}</Text>
                    {getSupportLabel(event, t) ? (
                      <View style={[styles.supportGradeBadge, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}>
                        <Text style={[styles.supportGradeText, { color: colors.textTertiary }]}>{getSupportLabel(event, t)}</Text>
                      </View>
                    ) : null}
                  </View>
                  <Text style={[styles.eventDesc, { color: colors.textSecondary }]}>{getDisplayPrediction(event)}</Text>
                  {getDisplayReason(event) ? (
                    <>
                      <TouchableOpacity
                        onPress={() => toggleReason(index)}
                        style={[styles.whyToggle, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}
                        activeOpacity={0.8}
                        accessibilityRole="button"
                        accessibilityState={{ expanded: !!openReasons[index] }}
                      >
                        <Text style={[styles.whyToggleText, { color: colors.accent }]}>
                          {openReasons[index] ? t('monthlyAccordion.hideWhy', 'Hide Why') : t('monthlyAccordion.showWhy', 'Show Why')}
                        </Text>
                        <Ionicons
                          name={openReasons[index] ? 'chevron-up' : 'chevron-down'}
                          size={14}
                          color={colors.accent}
                        />
                      </TouchableOpacity>
                      {openReasons[index] ? (
                        <View style={styles.reasonBlock}>
                          <Text style={[styles.reasonTitle, { color: colors.accent }]}>{t('monthlyAccordion.why', 'Why:')}</Text>
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
                          const scenarioReasonKey = `${index}:${idx}`;
                          const isScenarioReasonOpen = !!openScenarioReasons[scenarioReasonKey];
                          
                          return (
                            <View
                              key={idx}
                              style={[
                                styles.manifestationCard,
                                { backgroundColor: colors.surface, borderLeftColor: colors.accent },
                                isDark ? styles.manifestationCardDarkFlat : styles.manifestationCardLightElevated,
                              ]}
                            >
                              <View style={styles.manifestationHeader}>
                                <View style={[styles.scenarioNumber, { backgroundColor: colors.accent }]}>
                                  <Text style={[styles.scenarioNumberText, { color: colors.background }]}>{idx + 1}</Text>
                                </View>
                                <View style={{flex: 1, minWidth: 0}}>
                                  {scenario ? <Text style={[styles.manifestationText, { color: colors.text }]}>{scenario}</Text> : null}
                                  {reasoning && (
                                    <>
                                      <TouchableOpacity
                                        onPress={() => toggleScenarioReason(index, idx)}
                                        style={[styles.scenarioWhyToggle, { borderColor: colors.cardBorder }]}
                                        activeOpacity={0.8}
                                        accessibilityRole="button"
                                        accessibilityState={{ expanded: isScenarioReasonOpen }}
                                      >
                                        <Text style={[styles.scenarioWhyToggleText, { color: colors.accent }]}>
                                          {isScenarioReasonOpen ? t('monthlyAccordion.hideWhy', 'Hide Why') : t('monthlyAccordion.showWhy', 'Show Why')}
                                        </Text>
                                        <Ionicons
                                          name={isScenarioReasonOpen ? 'chevron-up' : 'chevron-down'}
                                          size={13}
                                          color={colors.accent}
                                        />
                                      </TouchableOpacity>
                                      {isScenarioReasonOpen ? (
                                        <View style={styles.reasoningContainer}>
                                          <Text style={[styles.reasoningLabel, { color: colors.accent }]}>{t('monthlyAccordion.why', 'Why:')}</Text>
                                          <Text style={[styles.reasoningText, { color: colors.textSecondary }]}>{reasoning}</Text>
                                        </View>
                                      ) : null}
                                    </>
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

          {personCount > 0 ? (
            <View style={[styles.peopleSection, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}>
              <TouchableOpacity
                onPress={() => {
                  LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
                  setPeopleExpanded((prev) => !prev);
                }}
                style={styles.peopleToggle}
                activeOpacity={0.75}
                accessibilityRole="button"
                accessibilityState={{ expanded: peopleExpanded }}
              >
                <View style={styles.peopleTitleRow}>
                  <Ionicons name="people-outline" size={18} color={colors.accent} />
                  <View style={styles.backgroundToggleCopy}>
                    <Text style={[styles.backgroundTitle, { color: colors.text }]}>
                      {t('monthlyAccordion.peopleAroundYou', { count: personCount, defaultValue: `People around you (${personCount})` })}
                    </Text>
                    <Text style={[styles.backgroundHint, { color: colors.textTertiary }]}>
                      {t('monthlyAccordion.peopleHint', 'Family developments calculated for each saved person. These are separate from your own events.')}
                    </Text>
                  </View>
                </View>
                <Ionicons name={peopleExpanded ? 'chevron-up' : 'chevron-down'} size={18} color={colors.textSecondary} />
              </TouchableOpacity>

              {peopleExpanded ? (
                <View style={[styles.peopleList, { borderTopColor: colors.cardBorder }]}>
                  {peopleGroups.map((group) => {
                    const subjectOpen = !!openPeopleSubjects[group.subjectKey];
                    const topEvent = group.events[0];
                    return (
                      <View key={group.subjectKey} style={[styles.personGroupCard, { borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}>
                        <TouchableOpacity
                          onPress={() => {
                            LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
                            setOpenPeopleSubjects((prev) => ({ ...prev, [group.subjectKey]: !prev[group.subjectKey] }));
                          }}
                          style={styles.personGroupHeader}
                          activeOpacity={0.75}
                          accessibilityRole="button"
                          accessibilityState={{ expanded: subjectOpen }}
                        >
                          <View style={[styles.personIcon, { backgroundColor: colors.surface }]}>
                            <Ionicons name="person-outline" size={17} color={colors.accent} />
                          </View>
                          <View style={styles.personGroupCopy}>
                            <View style={styles.personNameRow}>
                              <Text style={[styles.personLabel, { color: colors.text }]}>{group.subjectLabel}</Text>
                              <View style={[styles.personEventCount, { borderColor: colors.cardBorder }]}>
                                <Text style={[styles.backgroundCountText, { color: colors.textTertiary }]}>
                                  {t('monthlyAccordion.relativeEventCount', { count: group.events.length, defaultValue: `${group.events.length} events` })}
                                </Text>
                              </View>
                            </View>
                            <Text numberOfLines={1} style={[styles.personTopTheme, { color: colors.textTertiary }]}>
                              {topEvent
                                ? `${t('monthlyAccordion.topTheme', 'Top theme')}: ${getRelativeEventTitle(topEvent)}`
                                : t('monthlyAccordion.noClearRelativeEvent', 'No clearly timed event for this person this month')}
                            </Text>
                          </View>
                          <Ionicons name={subjectOpen ? 'chevron-up' : 'chevron-down'} size={18} color={colors.textSecondary} />
                        </TouchableOpacity>

                        {subjectOpen ? (
                          <View style={[styles.personEventsList, { borderTopColor: colors.cardBorder }]}>
                            {group.events.length === 0 ? (
                              <Text style={[styles.noRelativeEventText, { color: colors.textSecondary }]}>
                                {t('monthlyAccordion.noClearRelativeEventDetail', 'This person was evaluated, but no event passed the timing and support gates for this month.')}
                              </Text>
                            ) : group.events.map((event, eventIndex) => {
                              const reasonKey = event.candidate_id || `${group.subjectKey}-${eventIndex}`;
                              const reasonOpen = !!openPeopleReasons[reasonKey];
                              const manifestations = Array.isArray(event?.possible_manifestations) ? event.possible_manifestations : [];
                              return (
                                <View key={reasonKey} style={[styles.personEvent, { borderBottomColor: colors.cardBorder }]}>
                                  <View style={styles.eventTitleRow}>
                                    <Text style={[styles.eventType, { color: colors.text }]}>{getRelativeEventTitle(event)}</Text>
                                    {getSupportLabel(event, t) ? (
                                      <View style={[styles.supportGradeBadge, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}>
                                        <Text style={[styles.supportGradeText, { color: colors.textTertiary }]}>
                                          {getSupportLabel(event, t)}
                                        </Text>
                                      </View>
                                    ) : null}
                                  </View>
                                  <Text style={[styles.eventDesc, { color: colors.textSecondary }]}>{getDisplayPrediction(event)}</Text>
                                  {event?.display_explanation ? (
                                    <Text style={[styles.displayExplanation, { color: colors.textTertiary }]}>{event.display_explanation}</Text>
                                  ) : null}
                                  {getDisplayReason(event) ? (
                                    <>
                                      <TouchableOpacity
                                        onPress={() => setOpenPeopleReasons((prev) => ({ ...prev, [reasonKey]: !prev[reasonKey] }))}
                                        style={[styles.whyToggle, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}
                                        accessibilityRole="button"
                                        accessibilityState={{ expanded: reasonOpen }}
                                      >
                                        <Text style={[styles.whyToggleText, { color: colors.accent }]}>
                                          {reasonOpen ? t('monthlyAccordion.hideWhy', 'Hide Why') : t('monthlyAccordion.showWhy', 'Show Why')}
                                        </Text>
                                        <Ionicons name={reasonOpen ? 'chevron-up' : 'chevron-down'} size={14} color={colors.accent} />
                                      </TouchableOpacity>
                                      {reasonOpen ? <Text style={[styles.peopleReason, { color: colors.textTertiary }]}>{getDisplayReason(event)}</Text> : null}
                                    </>
                                  ) : null}
                                  {manifestations.length > 0 ? (
                                    <View style={styles.peopleScenarios}>
                                      {manifestations.map((item, scenarioIndex) => (
                                        <Text key={`${reasonKey}-scenario-${scenarioIndex}`} style={[styles.peopleScenarioText, { color: colors.textSecondary }]}>
                                          {'\u2022'} {typeof item === 'string' ? item : item?.scenario}
                                        </Text>
                                      ))}
                                    </View>
                                  ) : null}
                                </View>
                              );
                            })}
                          </View>
                        ) : null}
                      </View>
                    );
                  })}
                </View>
              ) : null}
            </View>
          ) : null}

          {secondarySections.map((section) => {
            const sectionOpen = !!openSecondarySections[section.key];
            return (
              <View key={section.key} style={[styles.backgroundSection, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}>
                <TouchableOpacity
                  onPress={() => toggleSecondarySection(section.key)}
                  style={styles.backgroundToggle}
                  activeOpacity={0.75}
                  accessibilityRole="button"
                  accessibilityState={{ expanded: sectionOpen }}
                >
                  <View style={styles.backgroundToggleCopy}>
                    <Text style={[styles.backgroundTitle, { color: colors.text }]}>{section.title}</Text>
                    <Text style={[styles.backgroundHint, { color: colors.textTertiary }]}>{section.hint}</Text>
                  </View>
                  <Ionicons name={sectionOpen ? 'chevron-up' : 'chevron-down'} size={18} color={colors.textSecondary} />
                </TouchableOpacity>

                {sectionOpen ? (
                  <View style={[styles.backgroundList, { borderTopColor: colors.cardBorder }]}>
                    {section.events.map((event, eventIndex) => {
                      const eventKey = event.candidate_id || `${section.key}-${eventIndex}`;
                      const reasonKey = `${section.key}:${eventKey}`;
                      const reasonOpen = !!openBackgroundReasons[reasonKey];
                      const manifestations = Array.isArray(event?.possible_manifestations) ? event.possible_manifestations : [];
                      return (
                        <View key={eventKey} style={[styles.backgroundEvent, { borderBottomColor: colors.cardBorder }]}>
                          <View style={styles.eventTitleRow}>
                            <Text style={[styles.eventType, { color: colors.text }]}>{event.type}</Text>
                            {getSupportLabel(event, t) ? (
                              <View style={[styles.supportGradeBadge, { borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}>
                                <Text style={[styles.supportGradeText, { color: colors.textTertiary }]}>{getSupportLabel(event, t)}</Text>
                              </View>
                            ) : null}
                            <View style={[styles.phaseBadge, { borderColor: colors.cardBorder }]}>
                              <Text style={[styles.phaseBadgeText, { color: colors.textTertiary }]}>{getPhaseLabel(event.manifestation_phase, t)}</Text>
                            </View>
                          </View>
                          <Text style={[styles.eventDesc, { color: colors.textSecondary }]}>{getDisplayPrediction(event)}</Text>
                          {event?.display_explanation ? (
                            <Text style={[styles.displayExplanation, { color: colors.textTertiary }]}>{event.display_explanation}</Text>
                          ) : null}
                          {getDisplayReason(event) ? (
                            <>
                              <TouchableOpacity
                                onPress={() => setOpenBackgroundReasons((prev) => ({ ...prev, [reasonKey]: !prev[reasonKey] }))}
                                style={[styles.whyToggle, { borderColor: colors.cardBorder, backgroundColor: colors.cardBackground }]}
                                activeOpacity={0.8}
                                accessibilityRole="button"
                                accessibilityState={{ expanded: reasonOpen }}
                              >
                                <Text style={[styles.whyToggleText, { color: colors.accent }]}>
                                  {reasonOpen ? t('monthlyAccordion.hideWhy', 'Hide Why') : t('monthlyAccordion.showWhy', 'Show Why')}
                                </Text>
                                <Ionicons name={reasonOpen ? 'chevron-up' : 'chevron-down'} size={14} color={colors.accent} />
                              </TouchableOpacity>
                              {reasonOpen ? (
                                <View style={styles.reasonBlock}>
                                  <Text style={[styles.reasonTitle, { color: colors.accent }]}>{t('monthlyAccordion.why', 'Why:')}</Text>
                                  <Text style={[styles.reasonBody, { color: colors.textTertiary }]}>{getDisplayReason(event)}</Text>
                                </View>
                              ) : null}
                            </>
                          ) : null}
                          {manifestations.length > 0 ? (
                            <View style={styles.peopleScenarios}>
                              {manifestations.map((item, scenarioIndex) => (
                                <Text key={`${eventKey}-scenario-${scenarioIndex}`} style={[styles.peopleScenarioText, { color: colors.textSecondary }]}>
                                  {'\u2022'} {typeof item === 'string' ? item : item?.scenario}
                                </Text>
                              ))}
                            </View>
                          ) : null}
                          {event.start_date && event.end_date ? (
                            <Text style={[styles.eventDates, { color: colors.accent }]}>
                              📅 {event.start_date} to {event.end_date}
                            </Text>
                          ) : null}
                        </View>
                      );
                    })}
                  </View>
                ) : null}
              </View>
            );
          })}

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
            <TouchableOpacity
              style={[
                styles.chatButton,
                { backgroundColor: colors.primary },
                isDark ? styles.chatButtonDarkFlat : styles.chatButtonLightElevated,
              ]}
              onPress={onChatPress}
            >
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
  },
  cardDarkFlat: {
    elevation: 0,
    shadowOpacity: 0,
  },
  cardLightElevated: {
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  headerActions: { flexDirection: 'row', alignItems: 'center', gap: 8, flexShrink: 0 },
  peopleCountBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, borderWidth: 1, borderRadius: 9, paddingHorizontal: 7, paddingVertical: 3 },
  backgroundCountBadge: { borderWidth: 1, borderRadius: 9, paddingHorizontal: 8, paddingVertical: 3 },
  backgroundCountText: { fontSize: 10, lineHeight: 14, fontWeight: '700' },
  monthName: { fontSize: 17, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5 },
  chipsRow: {
    paddingHorizontal: 16,
    paddingBottom: 12,
  },
  chipsContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 6,
  },
  miniTag: { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 8, maxWidth: '100%', flexShrink: 1 },
  miniTagText: { fontSize: 11, lineHeight: 16, fontWeight: '600', flexShrink: 1 },
  backgroundPreview: {
    marginHorizontal: 16,
    paddingTop: 9,
    paddingBottom: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  backgroundPreviewLabel: { fontSize: 10, lineHeight: 15, fontWeight: '700', letterSpacing: 0.45, marginBottom: 6 },
  backgroundMiniTag: { paddingHorizontal: 9, paddingVertical: 4, borderRadius: 8, borderWidth: 1, maxWidth: '100%', flexShrink: 1 },
  
  content: {
    padding: 16,
    paddingTop: 0,
    borderTopWidth: 1
  },
  themeRow: { flexDirection: 'row', alignItems: 'center', marginTop: 12, marginBottom: 12 },
  label: { fontSize: 11, fontWeight: '700', marginRight: 10, letterSpacing: 0.5 },
  expandedTagContainer: { flexDirection: 'row', gap: 8, flexWrap: 'wrap', flex: 1 },
  fullTag: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 10, maxWidth: '100%', flexShrink: 1 },
  fullTagText: { fontSize: 12, lineHeight: 17, fontWeight: '600', flexShrink: 1 },
  
  eventsList: { gap: 14 },
  sectionMeaning: { fontSize: 11, lineHeight: 16, marginBottom: 2 },
  quietMonthCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
  },
  quietMonthText: { flex: 1, fontSize: 13, lineHeight: 19 },
  eventItem: { flexDirection: 'row', gap: 10, alignItems: 'flex-start' },
  intensityDot: { width: 8, height: 8, borderRadius: 4, marginTop: 6 },
  eventTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8, flexWrap: 'wrap' },
  eventType: { fontSize: 14, fontWeight: '700', marginBottom: 4, letterSpacing: 0.3, flexShrink: 1 },
  supportGradeBadge: { borderWidth: 1, borderRadius: 8, paddingHorizontal: 7, paddingVertical: 2, marginBottom: 4 },
  supportGradeText: { fontSize: 10, fontWeight: '700', letterSpacing: 0.3 },
  eventDesc: { fontSize: 14, lineHeight: 20, marginBottom: 4 },
  displayExplanation: { fontSize: 11, lineHeight: 16, marginTop: 1, marginBottom: 4 },
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
  },
  manifestationCardDarkFlat: {
    elevation: 0,
    shadowOpacity: 0,
  },
  manifestationCardLightElevated: {
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
  manifestationText: { fontSize: 13, lineHeight: 19, fontWeight: '600', marginBottom: 6, flexShrink: 1 },
  scenarioWhyToggle: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  scenarioWhyToggleText: { fontSize: 11, fontWeight: '700', letterSpacing: 0.2 },
  reasoningContainer: { marginTop: 6, paddingTop: 8, borderTopWidth: 1, borderTopColor: 'rgba(255, 255, 255, 0.1)' },
  reasoningLabel: { fontSize: 11, fontWeight: '700', marginBottom: 4, letterSpacing: 0.5 },
  reasoningText: { fontSize: 12, lineHeight: 18, fontStyle: 'italic' },
  backgroundSection: {
    marginTop: 18,
    borderWidth: 1,
    borderRadius: 12,
    overflow: 'hidden',
  },
  peopleSection: { marginTop: 18, borderWidth: 1, borderRadius: 12, overflow: 'hidden' },
  peopleToggle: { minHeight: 58, paddingHorizontal: 12, paddingVertical: 10, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  peopleTitleRow: { flex: 1, minWidth: 0, flexDirection: 'row', alignItems: 'flex-start', gap: 9 },
  peopleList: { borderTopWidth: StyleSheet.hairlineWidth, padding: 10, gap: 9 },
  personGroupCard: { borderWidth: 1, borderRadius: 11, overflow: 'hidden' },
  personGroupHeader: { minHeight: 62, paddingHorizontal: 11, paddingVertical: 9, flexDirection: 'row', alignItems: 'center', gap: 9 },
  personIcon: { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  personGroupCopy: { flex: 1, minWidth: 0 },
  personNameRow: { flexDirection: 'row', alignItems: 'center', gap: 7, flexWrap: 'wrap' },
  personLabel: { fontSize: 14, lineHeight: 19, fontWeight: '800', flexShrink: 1 },
  personEventCount: { borderWidth: 1, borderRadius: 8, paddingHorizontal: 6, paddingVertical: 2 },
  personTopTheme: { fontSize: 11, lineHeight: 16, marginTop: 2 },
  personEventsList: { borderTopWidth: StyleSheet.hairlineWidth, paddingHorizontal: 11 },
  noRelativeEventText: { paddingVertical: 14, fontSize: 12, lineHeight: 18 },
  personEvent: { paddingVertical: 12, borderBottomWidth: StyleSheet.hairlineWidth },
  peopleReason: { marginTop: 7, fontSize: 12, lineHeight: 18, fontStyle: 'italic' },
  peopleScenarios: { marginTop: 8, gap: 4 },
  peopleScenarioText: { fontSize: 12, lineHeight: 18 },
  backgroundToggle: {
    minHeight: 54,
    paddingHorizontal: 12,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  backgroundToggleCopy: { flex: 1, minWidth: 0 },
  backgroundTitle: { fontSize: 13, lineHeight: 18, fontWeight: '700', flexShrink: 1 },
  backgroundHint: { fontSize: 11, lineHeight: 16, marginTop: 2, flexShrink: 1 },
  backgroundList: { borderTopWidth: 1, paddingHorizontal: 12 },
  backgroundEvent: { paddingVertical: 14, borderBottomWidth: StyleSheet.hairlineWidth },
  phaseBadge: { borderWidth: 1, borderRadius: 8, paddingHorizontal: 7, paddingVertical: 2, marginBottom: 4 },
  phaseBadgeText: { fontSize: 10, fontWeight: '600', letterSpacing: 0.2 },
  backgroundScenarios: { marginTop: 12, gap: 7 },
  backgroundScenario: { borderWidth: 1, borderRadius: 9, padding: 10 },
  backgroundScenarioText: { fontSize: 12, lineHeight: 18, fontWeight: '600', flexShrink: 1 },
  backgroundScenarioWhy: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 6, alignSelf: 'flex-start' },
  eventDates: { fontSize: 12, fontWeight: '600', marginTop: 6 },
  
  diveDeepButton: { marginTop: 18, marginBottom: 10 },
  chatButton: {
    flexDirection: 'row',
    padding: 14,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 16,
    gap: 8,
  },
  chatButtonDarkFlat: {
    elevation: 0,
    shadowOpacity: 0,
  },
  chatButtonLightElevated: {
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.12,
    shadowRadius: 6,
  },
  chatButtonText: { color: 'white', fontWeight: '700', fontSize: 15, letterSpacing: 0.3 }
});
