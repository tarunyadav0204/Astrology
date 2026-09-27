import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  Modal,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../context/ThemeContext';
import { storage } from '../../services/storage';
import { yogaAPI } from '../../services/api';
import { typographyTokens } from '../../theme/tokens';
import NativeSelectorChip from '../Common/NativeSelectorChip';

const CATEGORY_ICONS = {
  raj_yogas: 'diamond-outline',
  dhana_yogas: 'wallet-outline',
  panch_mahapurusha_yogas: 'star-outline',
  nabhasa_yogas: 'planet-outline',
  parivartana_yogas: 'swap-horizontal-outline',
  major_doshas: 'warning-outline',
  chandra_yogas: 'moon-outline',
  surya_yogas: 'sunny-outline',
  marriage_yogas: 'heart-outline',
  health_yogas: 'pulse-outline',
  career_specific_yogas: 'briefcase-outline',
  education_yogas: 'book-outline',
  neecha_bhanga_yogas: 'trending-up-outline',
  gaja_kesari_yogas: 'shield-checkmark-outline',
  viparita_raja_yogas: 'sparkles-outline',
};

const PITRI_SHAPA_VERSES = Array.from({ length: 11 }, (_, index) => String(index + 20));

const formatCategoryLabel = (category, t) => {
  const fallback = category.replace(/_/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase());
  return t(`yogas.${category}`, fallback);
};

const YogaScreen = ({ navigation }) => {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const [yogas, setYogas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentNative, setCurrentNative] = useState(null);
  const [activeSection, setActiveSection] = useState('yogas');
  const [expandedCategories, setExpandedCategories] = useState(new Set());
  const [initialized, setInitialized] = useState(false);
  const [pitriInfoVisible, setPitriInfoVisible] = useState(false);
  const [mangalInfoVisible, setMangalInfoVisible] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useFocusEffect(
    React.useCallback(() => {
      loadInitialNative();
    }, [])
  );

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 420,
      useNativeDriver: true,
    }).start();
  }, [fadeAnim]);

  const categories = useMemo(() => {
    if (!yogas) return [];

    return Object.keys(yogas).filter((category) => category !== 'major_doshas').flatMap((category) => {
      if (category === 'nabhasa_yogas' || category === 'parivartana_yogas') {
        return Object.keys(yogas[category] || {}).map((subCategory) => ({
          key: `${category}_${subCategory}`,
          iconKey: category,
          items: yogas[category][subCategory],
        }));
      }
      const items = category === 'marriage_yogas'
        ? (yogas[category] || []).filter((item) => item?.name !== 'Mangal Dosha')
        : yogas[category];
      return [{ key: category, iconKey: category, items }];
    }).filter(({ items }) => Array.isArray(items) && items.length > 0);
  }, [yogas]);

  const doshaCategories = useMemo(() => {
    const mangal = yogas?.major_doshas?.mangal_dosha;
    const nodal = yogas?.major_doshas?.kaal_sarp_dosha;
    const pitri = yogas?.major_doshas?.pitra_dosha;
    const checks = [];
    if (mangal) checks.push({
      key: 'mangal_dosha', iconKey: 'major_doshas', items: [{
        name: t('premiumUi.yogasDoshas.mangalDosha', 'Mangal Dosha'),
        description: mangal.summary,
        displayStatus: mangal.status,
        planets: ['Mars'],
        houses: mangal.mars_house_lagna ? [mangal.mars_house_lagna] : [],
        classical_conditions: (mangal.evidence || [])
          .filter((row) => row.rule_id !== 'MS-DHANE-VARIANT' || row.material_difference)
          .map((row) => ({
          rule_id: row.rule_id,
          description: row.fact,
          matched: row.matched,
          })),
        source: mangal.source,
        textualNote: mangal.source?.textual_note,
        variantSource: mangal.textual_variants?.[0]?.material_difference
          ? mangal.textual_variants?.[0]?.source?.reference_label
          : null,
        variantMatched: !mangal.primary_reading?.matched && mangal.textual_variants?.some((row) => row.matched),
      }],
    });
    if (nodal) {
      const direction = nodal.direction_label || 'Rahu → Ketu';
      const contained = (nodal.contained_planets || []).join(', ') || '—';
      const outside = (nodal.outside_planets || []).join(', ') || '—';
      const boundary = (nodal.boundary_planets || []).map((row) => `${row.planet}–${row.node}`).join(', ') || '—';
      const summaries = {
        complete: t('premiumUi.yogasDoshas.nodalCompleteSummary', { direction }),
        boundary: t('premiumUi.yogasDoshas.nodalBoundarySummary', { direction, planets: boundary }),
        not_formed: t('premiumUi.yogasDoshas.nodalNotFormedSummary', { planets: outside }),
        unavailable: t('premiumUi.yogasDoshas.nodalUnavailableSummary'),
      };
      checks.push({
      key: 'nodal_enclosure', iconKey: 'major_doshas', items: [{
        name: t('premiumUi.yogasDoshas.nodalEnclosure', 'Rahu–Ketu nodal enclosure'),
        description: summaries[nodal.status] || nodal.summary,
        displayStatus: nodal.status,
        planets: ['Rahu', 'Ketu'],
        classical_conditions: [{
          rule_id: 'NODE-ENCLOSURE-EXACT',
          description: t('premiumUi.yogasDoshas.nodalEvidence', { direction, contained, outside }),
          matched: nodal.present,
        }, ...(nodal.boundary_planets?.length ? [{
          rule_id: 'NODE-BOUNDARY-EXACT',
          description: t('premiumUi.yogasDoshas.nodalBoundaryEvidence', { planets: boundary }),
          matched: true,
        }] : [])],
        source: nodal.source,
        textualNote: t('premiumUi.yogasDoshas.modernConventionNote', 'This is a later convention, not a verified rule from a named classical verse. No effects, severity, remedies, cancellations or named variants are inferred.'),
        basisTitle: t('premiumUi.yogasDoshas.methodBasis', 'Calculation basis'),
      }],
      });
    }
    if (pitri) {
      const matchedRules = pitri.matched_rules || [];
      const evidence = matchedRules.length
        ? matchedRules.flatMap((rule) => [
          {
            rule_id: rule.rule_id,
            description: `${rule.reference}: ${rule.description}`,
            matched: true,
          },
          ...(rule.conditions || []).map((condition) => ({
            rule_id: `${rule.rule_id}-${condition.key}`,
            description: condition.label,
            matched: condition.matched,
          })),
        ])
        : [{
          rule_id: 'BPHS-PS-NONE',
          description: t('premiumUi.yogasDoshas.pitriNoMatchEvidence', 'None of the eleven complete combinations in BPHS 83.20–30 matches this chart.'),
          matched: false,
        }];
      checks.push({
        key: 'pitri_shapa', iconKey: 'major_doshas', items: [{
          name: t('premiumUi.yogasDoshas.pitriShapa', 'Pitṛ-śāpa · progeny'),
          description: pitri.present
            ? t('premiumUi.yogasDoshas.pitriFormedSummary', { count: matchedRules.length })
            : t('premiumUi.yogasDoshas.pitriNotFormedSummary', 'None of the eleven complete BPHS Pitṛ-śāpa combinations matches this chart.'),
          displayStatus: pitri.status,
          planets: pitri.planets || [],
          houses: pitri.present ? [5] : [],
          classical_conditions: evidence,
          source: pitri.source,
          textualNote: t(
            'premiumUi.yogasDoshas.pitriScopeNote',
            'This classical check concerns progeny. A Sun–Rahu or Sun–Saturn conjunction, a node in House 9, or an afflicted ninth lord does not form it by itself.'
          ),
        }],
      });
    }
    return checks;
  }, [t, yogas]);

  const visibleCategories = activeSection === 'doshas' ? doshaCategories : categories;

  const totalYogas = useMemo(
    () => visibleCategories.reduce((total, category) => total + category.items.length, 0),
    [visibleCategories]
  );

  useEffect(() => {
    if (!initialized && visibleCategories.length > 0) {
      setExpandedCategories(new Set([visibleCategories[0].key]));
      setInitialized(true);
    }
  }, [initialized, visibleCategories]);

  const loadInitialNative = async () => {
    try {
      let birthData = await storage.getBirthDetails();
      if (!birthData) {
        const profiles = await storage.getBirthProfiles();
        if (profiles?.length) birthData = profiles.find((profile) => profile.relation === 'self') || profiles[0];
      }
      if (!birthData?.name) {
        navigation.replace('BirthProfileIntro', { returnTo: 'Yogas' });
        return;
      }
      if (!currentNative || currentNative.id !== birthData.id) {
        setCurrentNative(birthData);
        fetchYogas(birthData);
      }
    } catch (error) {
      console.error('Error loading initial native:', error);
      setLoading(false);
    }
  };

  const fetchYogas = async (birthData) => {
    try {
      setLoading(true);
      const response = await yogaAPI.getYogas(birthData);
      if (response.data?.status === 'success') {
        setYogas(response.data.yogas);
        setInitialized(false);
      }
    } catch (error) {
      console.error('Error fetching yogas:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (category) => {
    setExpandedCategories((previous) => {
      const next = new Set(previous);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  };

  const strengthTreatment = (strength) => {
    switch (strength?.toLowerCase()) {
      case 'high':
        return { color: colors.success, backgroundColor: colors.successSoft || colors.surfaceMuted };
      case 'medium':
        return { color: colors.warning, backgroundColor: colors.warningSoft || colors.surfaceMuted };
      case 'low':
        return { color: colors.error, backgroundColor: colors.errorSoft || colors.surfaceMuted };
      case 'formed':
        return { color: colors.error, backgroundColor: colors.errorSoft || colors.surfaceMuted };
      case 'protected':
        return { color: colors.success, backgroundColor: colors.successSoft || colors.surfaceMuted };
      case 'not_formed':
        return { color: colors.success, backgroundColor: colors.successSoft || colors.surfaceMuted };
      case 'unavailable':
        return { color: colors.warning, backgroundColor: colors.warningSoft || colors.surfaceMuted };
      case 'complete':
        return { color: colors.warning, backgroundColor: colors.warningSoft || colors.surfaceMuted };
      case 'boundary':
        return { color: colors.warning, backgroundColor: colors.warningSoft || colors.surfaceMuted };
      default:
        return { color: colors.textSecondary, backgroundColor: colors.surfaceMuted };
    }
  };

  const statusLabel = (status) => {
    if (!status) return null;
    return t(`premiumUi.yogasDoshas.${status}`, status.replace(/_/g, ' '));
  };

  const renderYogaItem = (yoga, index, isLast) => {
    const badgeValue = yoga.displayStatus || yoga.strength;
    const strengthStyle = strengthTreatment(badgeValue);
    return (
      <View
        key={`${yoga.name}-${index}`}
        style={[styles.yogaItem, !isLast && { borderBottomColor: colors.cardBorder, borderBottomWidth: StyleSheet.hairlineWidth }]}
      >
        <View style={styles.yogaItemHeader}>
          <View style={[styles.yogaOrdinal, { backgroundColor: colors.accentSoft, borderColor: colors.selectionBorder }]}>
            <Text style={[styles.yogaOrdinalText, { color: colors.primaryStrong }]}>{String(index + 1).padStart(2, '0')}</Text>
          </View>
          <Text style={[styles.yogaName, { color: colors.text }]}>{yoga.name}</Text>
          {badgeValue ? (
            <View style={[styles.strengthBadge, { backgroundColor: strengthStyle.backgroundColor }]}>
              <Text style={[styles.strengthText, { color: strengthStyle.color }]}>
                {yoga.displayStatus ? statusLabel(yoga.displayStatus) : yoga.strength}
              </Text>
            </View>
          ) : null}
        </View>

        {yoga.description ? (
          <Text style={[styles.yogaDescription, { color: colors.textSecondary }]}>{yoga.description}</Text>
        ) : null}

        {yoga.classical_conditions?.length > 0 ? (
          <View style={[styles.classicalBasis, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
            <Text style={[styles.classicalBasisTitle, { color: colors.text }]}>
              {yoga.basisTitle || t('premiumUi.yogas.classicalBasis', 'Classical basis')}
            </Text>
            {yoga.classical_conditions.map((condition) => (
              <View key={condition.rule_id} style={styles.classicalConditionRow}>
                <View style={[styles.classicalDot, { backgroundColor: condition.matched ? colors.success : colors.textSecondary }]} />
                <Text style={[styles.classicalConditionText, { color: colors.textSecondary }]}>
                  {condition.description}
                </Text>
              </View>
            ))}
            {yoga.classical_result ? (
              <View style={[styles.classicalResult, { borderTopColor: colors.cardBorder }]}>
                <Text style={[styles.classicalResultTitle, { color: colors.text }]}>
                  {t('premiumUi.yogas.classicalResult', 'What the classic says')}
                </Text>
                <Text style={[styles.classicalConditionText, { color: colors.textSecondary }]}>
                  {t(
                    'premiumUi.yogas.classicalResultBody',
                    'Phaladeepika describes this yoga in royal terms: power, status, fame and wealth.'
                  )}
                </Text>
              </View>
            ) : null}
            <View style={[styles.referenceRow, { borderTopColor: colors.cardBorder }]}>
              <Ionicons name="library-outline" size={14} color={colors.primaryStrong} />
              <Text style={[styles.referenceText, { color: colors.primaryStrong }]}>
                {t('premiumUi.yogas.reference', 'Reference')}: {yoga.source?.reference_label || yoga.references?.join(', ')}
              </Text>
            </View>
            {yoga.textualNote ? (
              <Text style={[styles.textualNote, { color: colors.textSecondary }]}>
                {t('premiumUi.yogas.textualNote', 'Textual note')}: {yoga.textualNote}
              </Text>
            ) : null}
            {yoga.variantSource ? (
              <Text style={[styles.textualNote, { color: colors.textSecondary }]}>
                {t('premiumUi.yogasDoshas.separateReading', 'Separate reading')}: {yoga.variantSource}
              </Text>
            ) : null}
            {yoga.variantMatched ? (
              <Text style={[styles.variantNote, { color: colors.warning }]}>
                {t('premiumUi.yogasDoshas.variantMatched', 'The separate second-house reading matches this chart.')}
              </Text>
            ) : null}
          </View>
        ) : null}

        {yoga.result_delivery?.channels?.length > 0 ? (
          <View style={[styles.resultDeliveryCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
            <Text style={[styles.resultDeliveryTitle, { color: colors.text }]}>
              {t('premiumUi.planetResultDelivery.yogaTitle', 'Where {{planet}} can deliver results', {
                planet: t(`planets.${yoga.planet}`, yoga.planet),
              })}
            </Text>
            <Text style={[styles.resultDeliveryBody, { color: colors.textSecondary }]}>
              {t('premiumUi.planetResultDelivery.neechaBhanga')}
            </Text>
            <View style={styles.resultDeliveryChannels}>
              {yoga.result_delivery.channels.map((channel) => (
                <View
                  key={`${yoga.planet}-yoga-delivery-${channel.house}`}
                  style={[styles.resultDeliveryChip, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}
                >
                  <Text style={[styles.resultDeliveryChipText, { color: colors.text }]}>
                    H{channel.house} · {t(`premiumUi.home.houseAreas.${channel.house}`, `House ${channel.house}`)}
                  </Text>
                </View>
              ))}
            </View>
            <Text style={[styles.resultDeliveryBoundary, { color: colors.textSecondary }]}>
              {t('premiumUi.planetResultDelivery.boundary')}
            </Text>
          </View>
        ) : null}

        {(yoga.planets?.length > 0 || yoga.houses?.length > 0) && (
          <View style={styles.metaRow}>
            {yoga.planets?.length > 0 ? (
              <View style={[styles.metaChip, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                <Ionicons name="planet-outline" size={13} color={colors.primary} />
                <Text style={[styles.metaText, { color: colors.textSecondary }]}>{yoga.planets.join(' · ')}</Text>
              </View>
            ) : null}
            {yoga.houses?.length > 0 ? (
              <View style={[styles.metaChip, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                <Ionicons name="grid-outline" size={13} color={colors.primary} />
                <Text style={[styles.metaText, { color: colors.textSecondary }]}>H{yoga.houses.join(', H')}</Text>
              </View>
            ) : null}
          </View>
        )}
      </View>
    );
  };

  const renderCategory = ({ key, iconKey, items }) => {
    const isExpanded = expandedCategories.has(key);
    return (
      <View key={key} style={[styles.categoryBlock, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
        <TouchableOpacity
          onPress={() => toggleCategory(key)}
          activeOpacity={0.76}
          style={styles.categoryRow}
          accessibilityRole="button"
          accessibilityState={{ expanded: isExpanded }}
        >
          <View style={[styles.categoryIcon, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
            <Ionicons name={CATEGORY_ICONS[iconKey] || 'sparkles-outline'} size={20} color={colors.selectionText} />
          </View>
          <View style={styles.categoryTextWrap}>
            <Text style={[styles.categoryTitle, { color: colors.text }]}>
              {key === 'mangal_dosha'
                ? t('premiumUi.yogasDoshas.mangalDosha', 'Mangal Dosha')
                : key === 'nodal_enclosure'
                  ? t('premiumUi.yogasDoshas.nodalEnclosure', 'Rahu–Ketu nodal enclosure')
                  : key === 'pitri_shapa'
                    ? t('premiumUi.yogasDoshas.pitriShapa', 'Pitṛ-śāpa · progeny')
                  : formatCategoryLabel(key, t)}
            </Text>
            <Text style={[styles.categoryCount, { color: colors.textSecondary }]}>
              {activeSection === 'doshas'
                ? t('premiumUi.yogasDoshas.doshaChecks', { count: items.length })
                : t('premiumUi.yogas.combinationsFound', { count: items.length })}
            </Text>
          </View>
          {key === 'pitri_shapa' || key === 'mangal_dosha' ? (
            <TouchableOpacity
              onPress={(event) => {
                event.stopPropagation?.();
                if (key === 'pitri_shapa') setPitriInfoVisible(true);
                else setMangalInfoVisible(true);
              }}
              activeOpacity={0.72}
              style={[styles.infoButton, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}
              accessibilityRole="button"
              accessibilityLabel={key === 'pitri_shapa'
                ? t('premiumUi.pitriShapaInfo.open', 'Read the complete classical Pitri-shapa rules')
                : t('premiumUi.mangalDoshaInfo.open', 'Read the complete classical Mangal Dosha rules')}
              hitSlop={8}
            >
              <Ionicons name="information-circle-outline" size={20} color={colors.primaryStrong} />
            </TouchableOpacity>
          ) : null}
          <View style={[styles.expandButton, { backgroundColor: isExpanded ? colors.primary : colors.surfaceMuted }]}>
            <Ionicons name={isExpanded ? 'remove' : 'add'} size={18} color={isExpanded ? colors.onPrimary : colors.textSecondary} />
          </View>
        </TouchableOpacity>
        {isExpanded ? <View style={[styles.yogasList, { borderTopColor: colors.cardBorder }]}>{items.map((yoga, index) => renderYogaItem(yoga, index, index === items.length - 1))}</View> : null}
      </View>
    );
  };

  const renderPitriInfoModal = () => {
    const pitri = yogas?.major_doshas?.pitra_dosha;
    const matchedRuleIds = new Set(pitri?.matched_rule_ids || []);

    return (
      <Modal
        visible={pitriInfoVisible}
        transparent
        animationType="slide"
        statusBarTranslucent
        onRequestClose={() => setPitriInfoVisible(false)}
      >
        <View style={styles.modalBackdrop}>
          <TouchableOpacity
            activeOpacity={1}
            style={StyleSheet.absoluteFill}
            onPress={() => setPitriInfoVisible(false)}
            accessibilityLabel={t('premiumUi.common.close', 'Close')}
          />
          <SafeAreaView edges={['top', 'bottom']} style={styles.modalSafeArea}>
            <View style={[styles.modalSheet, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
              <View style={[styles.modalHeader, { borderBottomColor: colors.cardBorder }]}>
                <View style={styles.modalHeaderCopy}>
                  <Text style={[styles.modalEyebrow, { color: colors.primaryStrong }]}>{t('premiumUi.pitriShapaInfo.verseRange')}</Text>
                  <Text style={[styles.modalTitle, { color: colors.text }]}>
                    {t('premiumUi.pitriShapaInfo.title', 'Complete classical Pitri-shapa rules')}
                  </Text>
                </View>
                <TouchableOpacity
                  onPress={() => setPitriInfoVisible(false)}
                  style={[styles.modalClose, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}
                  accessibilityRole="button"
                  accessibilityLabel={t('premiumUi.common.close', 'Close')}
                >
                  <Ionicons name="close" size={22} color={colors.text} />
                </TouchableOpacity>
              </View>

              <ScrollView contentContainerStyle={styles.modalContent} showsVerticalScrollIndicator={false}>
                <Text style={[styles.modalIntro, { color: colors.textSecondary }]}>
                  {t('premiumUi.pitriShapaInfo.intro')}
                </Text>

                <View style={[styles.scopeCard, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
                  <Ionicons name="people-outline" size={21} color={colors.selectionText} />
                  <View style={styles.scopeCopy}>
                    <Text style={[styles.scopeTitle, { color: colors.selectionText }]}>
                      {t('premiumUi.pitriShapaInfo.scopeTitle')}
                    </Text>
                    <Text style={[styles.scopeBody, { color: colors.textSecondary }]}>
                      {t('premiumUi.pitriShapaInfo.scopeBody')}
                    </Text>
                  </View>
                </View>

                <Text style={[styles.logicTitle, { color: colors.text }]}>
                  {t('premiumUi.pitriShapaInfo.formationTitle')}
                </Text>
                <Text style={[styles.logicBody, { color: colors.textSecondary }]}>
                  {t('premiumUi.pitriShapaInfo.formationBody')}
                </Text>

                <View style={styles.ruleList}>
                  {PITRI_SHAPA_VERSES.map((verse) => {
                    const ruleId = `BPHS-PS-${verse}`;
                    const matched = matchedRuleIds.has(ruleId);
                    return (
                      <View
                        key={ruleId}
                        style={[
                          styles.ruleCard,
                          {
                            backgroundColor: matched ? (colors.errorSoft || colors.surfaceMuted) : colors.surfaceMuted,
                            borderColor: matched ? colors.error : colors.cardBorder,
                          },
                        ]}
                      >
                        <View style={styles.ruleHeader}>
                          <Text style={[styles.ruleReference, { color: matched ? colors.error : colors.primaryStrong }]}>
                            {t('premiumUi.pitriShapaInfo.verseReference', { verse })}
                          </Text>
                          {matched ? (
                            <View style={[styles.matchBadge, { backgroundColor: colors.error }]}>
                              <Ionicons name="checkmark" size={12} color={colors.onPrimary} />
                              <Text style={[styles.matchBadgeText, { color: colors.onPrimary }]}>
                                {t('premiumUi.pitriShapaInfo.matchesChart')}
                              </Text>
                            </View>
                          ) : null}
                        </View>
                        <Text style={[styles.ruleText, { color: colors.text }]}>
                          {t(`premiumUi.pitriShapaInfo.rules.${verse}`)}
                        </Text>
                      </View>
                    );
                  })}
                </View>

                <Text style={[styles.logicTitle, { color: colors.text }]}>
                  {t('premiumUi.pitriShapaInfo.methodTitle')}
                </Text>
                {['malefics', 'verse20', 'verse23', 'verse26', 'verse30', 'nodeAspects'].map((note) => (
                  <View key={note} style={styles.methodRow}>
                    <View style={[styles.methodDot, { backgroundColor: colors.primaryStrong }]} />
                    <Text style={[styles.methodText, { color: colors.textSecondary }]}>
                      {t(`premiumUi.pitriShapaInfo.method.${note}`)}
                    </Text>
                  </View>
                ))}

                <View style={[styles.sourceCard, { borderColor: colors.cardBorder }]}>
                  <View style={styles.sourceHeadingRow}>
                    <Ionicons name="library-outline" size={17} color={colors.primaryStrong} />
                    <Text style={[styles.sourceTitle, { color: colors.text }]}>
                      {t('premiumUi.pitriShapaInfo.referenceTitle')}
                    </Text>
                  </View>
                  <Text style={[styles.sourceText, { color: colors.textSecondary }]}>
                    {t('premiumUi.pitriShapaInfo.referenceBody')}
                  </Text>
                  <Text style={[styles.editionNote, { color: colors.textSecondary }]}>
                    {t('premiumUi.pitriShapaInfo.editionNote')}
                  </Text>
                </View>
              </ScrollView>
            </View>
          </SafeAreaView>
        </View>
      </Modal>
    );
  };

  const renderMangalInfoModal = () => {
    const mangal = yogas?.major_doshas?.mangal_dosha || {};
    const variant = mangal.textual_variants?.[0] || {};
    const moonReference = mangal.supplementary_references?.moon || {};
    const venusReference = mangal.supplementary_references?.venus || {};
    const beneficRelations = mangal.benefic_condition?.relations_to_mars || [];
    const relationText = beneficRelations.length
      ? beneficRelations.map((row) => `${t(`planets.${row.planet}`, row.planet)} · ${t(`premiumUi.mangalDoshaInfo.relations.${row.relation}`, row.relation)}`).join(', ')
      : null;

    const referenceRows = [
      { key: 'lagna', label: t('premiumUi.mangalDoshaInfo.lagna'), house: mangal.mars_house_lagna, matched: mangal.primary_reading?.matched },
      { key: 'moon', label: t('premiumUi.mangalDoshaInfo.moon'), house: mangal.mars_house_moon, matched: moonReference.matched, supplementary: true },
      { key: 'venus', label: t('premiumUi.mangalDoshaInfo.venus'), house: mangal.mars_house_venus, matched: venusReference.matched, supplementary: true },
    ];

    return (
      <Modal
        visible={mangalInfoVisible}
        transparent
        animationType="slide"
        statusBarTranslucent
        onRequestClose={() => setMangalInfoVisible(false)}
      >
        <View style={styles.modalBackdrop}>
          <TouchableOpacity
            activeOpacity={1}
            style={StyleSheet.absoluteFill}
            onPress={() => setMangalInfoVisible(false)}
            accessibilityLabel={t('premiumUi.common.close', 'Close')}
          />
          <SafeAreaView edges={['top', 'bottom']} style={styles.modalSafeArea}>
            <View style={[styles.modalSheet, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
              <View style={[styles.modalHeader, { borderBottomColor: colors.cardBorder }]}>
                <View style={styles.modalHeaderCopy}>
                  <Text style={[styles.modalEyebrow, { color: colors.primaryStrong }]}>
                    {t('premiumUi.mangalDoshaInfo.verseReference')}
                  </Text>
                  <Text style={[styles.modalTitle, { color: colors.text }]}>
                    {t('premiumUi.mangalDoshaInfo.title', 'Complete classical Mangal Dosha rules')}
                  </Text>
                </View>
                <TouchableOpacity
                  onPress={() => setMangalInfoVisible(false)}
                  style={[styles.modalClose, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}
                  accessibilityRole="button"
                  accessibilityLabel={t('premiumUi.common.close', 'Close')}
                >
                  <Ionicons name="close" size={22} color={colors.text} />
                </TouchableOpacity>
              </View>

              <ScrollView contentContainerStyle={styles.modalContent} showsVerticalScrollIndicator={false}>
                <Text style={[styles.modalIntro, { color: colors.textSecondary }]}>
                  {t('premiumUi.mangalDoshaInfo.intro')}
                </Text>

                <View style={[styles.scopeCard, { backgroundColor: colors.selectionSurface, borderColor: colors.selectionBorder }]}>
                  <Ionicons name="checkmark-circle-outline" size={21} color={colors.selectionText} />
                  <View style={styles.scopeCopy}>
                    <Text style={[styles.scopeTitle, { color: colors.selectionText }]}>
                      {t('premiumUi.mangalDoshaInfo.formationTitle')}
                    </Text>
                    <Text style={[styles.scopeBody, { color: colors.textSecondary }]}>
                      {t('premiumUi.mangalDoshaInfo.formationBody')}
                    </Text>
                  </View>
                </View>

                <Text style={[styles.logicTitle, { color: colors.text }]}>
                  {t('premiumUi.mangalDoshaInfo.chartTitle')}
                </Text>
                <View style={[styles.mangalVerdictCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                  <View style={styles.mangalVerdictHeader}>
                    <Text style={[styles.mangalVerdictLabel, { color: colors.textSecondary }]}>
                      {t('premiumUi.mangalDoshaInfo.selectedVerdict')}
                    </Text>
                    <View style={[styles.strengthBadge, { backgroundColor: strengthTreatment(mangal.status).backgroundColor }]}>
                      <Text style={[styles.strengthText, { color: strengthTreatment(mangal.status).color }]}>
                        {statusLabel(mangal.status)}
                      </Text>
                    </View>
                  </View>
                  <Text style={[styles.mangalVerdictText, { color: colors.text }]}>
                    {t('premiumUi.mangalDoshaInfo.marsHouse', { house: mangal.mars_house_lagna ?? '—' })}
                  </Text>
                  <View style={styles.conditionLine}>
                    <Ionicons
                      name={mangal.primary_reading?.matched ? 'checkmark-circle' : 'close-circle-outline'}
                      size={18}
                      color={mangal.primary_reading?.matched ? colors.error : colors.success}
                    />
                    <Text style={[styles.conditionLineText, { color: colors.textSecondary }]}>
                      {mangal.primary_reading?.matched
                        ? t('premiumUi.mangalDoshaInfo.placementMatched')
                        : t('premiumUi.mangalDoshaInfo.placementNotMatched')}
                    </Text>
                  </View>
                  <View style={styles.conditionLine}>
                    <Ionicons
                      name={beneficRelations.length ? 'shield-checkmark' : 'remove-circle-outline'}
                      size={18}
                      color={beneficRelations.length ? colors.success : colors.textSecondary}
                    />
                    <Text style={[styles.conditionLineText, { color: colors.textSecondary }]}>
                      {beneficRelations.length
                        ? t('premiumUi.mangalDoshaInfo.beneficProtection', { relations: relationText })
                        : t('premiumUi.mangalDoshaInfo.noBeneficProtection')}
                    </Text>
                  </View>
                </View>

                <Text style={[styles.logicTitle, { color: colors.text }]}>
                  {t('premiumUi.mangalDoshaInfo.referenceCountsTitle')}
                </Text>
                <Text style={[styles.logicBody, { color: colors.textSecondary }]}>
                  {t('premiumUi.mangalDoshaInfo.referenceCountsBody')}
                </Text>
                <View style={styles.referenceCountList}>
                  {referenceRows.map((row) => (
                    <View key={row.key} style={[styles.referenceCountRow, { borderColor: colors.cardBorder }]}>
                      <View style={styles.referenceCountCopy}>
                        <Text style={[styles.referenceCountLabel, { color: colors.text }]}>{row.label}</Text>
                        <Text style={[styles.referenceCountHouse, { color: colors.textSecondary }]}>
                          {t('premiumUi.mangalDoshaInfo.houseFromReference', { house: row.house ?? '—' })}
                        </Text>
                      </View>
                      <Text style={[styles.referenceCountStatus, { color: row.matched ? colors.error : colors.success }]}>
                        {row.matched
                          ? t('premiumUi.mangalDoshaInfo.namedPlacement')
                          : t('premiumUi.mangalDoshaInfo.notNamedPlacement')}
                      </Text>
                    </View>
                  ))}
                </View>

                <Text style={[styles.logicTitle, { color: colors.text }]}>
                  {t('premiumUi.mangalDoshaInfo.variantTitle')}
                </Text>
                <Text style={[styles.logicBody, { color: colors.textSecondary }]}>
                  {t('premiumUi.mangalDoshaInfo.variantBody')}
                </Text>
                <View style={[styles.variantReadingCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
                  <Text style={[styles.variantReadingText, { color: colors.text }]}>
                    {t('premiumUi.mangalDoshaInfo.variantCurrent', {
                      house: mangal.mars_house_lagna ?? '—',
                      result: variant.matched
                        ? t('premiumUi.mangalDoshaInfo.namedPlacement')
                        : t('premiumUi.mangalDoshaInfo.notNamedPlacement'),
                    })}
                  </Text>
                  {variant.material_difference ? (
                    <Text style={[styles.variantDifference, { color: colors.warning }]}>
                      {t('premiumUi.mangalDoshaInfo.variantDifference')}
                    </Text>
                  ) : null}
                </View>

                <Text style={[styles.logicTitle, { color: colors.text }]}>
                  {t('premiumUi.mangalDoshaInfo.methodTitle')}
                </Text>
                {['benefics', 'moon', 'mercury', 'aspects', 'noIntensity', 'noD9', 'pair'].map((note) => (
                  <View key={note} style={styles.methodRow}>
                    <View style={[styles.methodDot, { backgroundColor: colors.primaryStrong }]} />
                    <Text style={[styles.methodText, { color: colors.textSecondary }]}>
                      {t(`premiumUi.mangalDoshaInfo.method.${note}`)}
                    </Text>
                  </View>
                ))}

                <View style={[styles.sourceCard, { borderColor: colors.cardBorder }]}>
                  <View style={styles.sourceHeadingRow}>
                    <Ionicons name="library-outline" size={17} color={colors.primaryStrong} />
                    <Text style={[styles.sourceTitle, { color: colors.text }]}>
                      {t('premiumUi.mangalDoshaInfo.referenceTitle')}
                    </Text>
                  </View>
                  <Text style={[styles.sourceText, { color: colors.textSecondary }]}>
                    {t('premiumUi.mangalDoshaInfo.primaryReference')}
                  </Text>
                  <Text style={[styles.sourceText, { color: colors.textSecondary }]}>
                    {t('premiumUi.mangalDoshaInfo.variantReference')}
                  </Text>
                  <Text style={[styles.sourceText, { color: colors.textSecondary }]}>
                    {t('premiumUi.mangalDoshaInfo.pairReference')}
                  </Text>
                  <Text style={[styles.editionNote, { color: colors.textSecondary }]}>
                    {t('premiumUi.mangalDoshaInfo.sourceNote')}
                  </Text>
                </View>
              </ScrollView>
            </View>
          </SafeAreaView>
        </View>
      </Modal>
    );
  };

  const renderHeader = () => (
    <View style={[styles.headerShell, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
      <SafeAreaView edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={[styles.headerButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]} accessibilityLabel={t('premiumUi.common.goBack')}>
            <Ionicons name="arrow-back" size={21} color={colors.textInverse} />
          </TouchableOpacity>
          <View style={styles.headerCopy}>
            <Text style={[styles.headerEyebrow, { color: colors.accent }]}>{t('premiumUi.yogas.chartPatterns')}</Text>
            <Text style={[styles.headerTitle, { color: colors.textInverse }]}>{t('premiumUi.yogasDoshas.title', 'Yogas & Doshas')}</Text>
          </View>
          <NativeSelectorChip
            birthData={currentNative}
            onPress={() => navigation.navigate('SelectNative', { returnTo: 'Yogas' })}
            maxLength={9}
            showIcon={false}
            style={{ backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }}
            textStyle={{ color: colors.textInverseMuted }}
            iconColor={colors.accent}
          />
        </View>
      </SafeAreaView>
    </View>
  );

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} />
        {renderHeader()}
        <View style={styles.loadingContainer}>
          <View style={[styles.loadingMark, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
            <ActivityIndicator size="small" color={colors.accent} />
          </View>
          <Text style={[styles.loadingTitle, { color: colors.text }]}>{t('premiumUi.yogas.readingPatterns')}</Text>
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('yogas.loading', 'Identifying planetary combinations…')}</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} />
      {renderHeader()}
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Animated.View style={{ opacity: fadeAnim }}>
          <View style={[styles.sectionTabs, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
            {['yogas', 'doshas'].map((section) => {
              const selected = activeSection === section;
              return (
                <TouchableOpacity
                  key={section}
                  style={[styles.sectionTab, selected && { backgroundColor: colors.cardBackground, borderColor: colors.selectionBorder }]}
                  onPress={() => {
                    setActiveSection(section);
                    setExpandedCategories(new Set());
                    setInitialized(false);
                  }}
                  accessibilityRole="tab"
                  accessibilityState={{ selected }}
                >
                  <Text style={[styles.sectionTabText, { color: selected ? colors.primaryStrong : colors.textSecondary }]}>
                    {t(`premiumUi.yogasDoshas.${section}`, section === 'yogas' ? 'Yogas' : 'Doshas')}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
          <View style={[styles.heroCard, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
            <View style={[styles.orbitLarge, { borderColor: colors.cosmicLine }]} />
            <View style={[styles.orbitSmall, { borderColor: colors.cosmicLine }]} />
            <Text style={[styles.heroEyebrow, { color: colors.accent }]}>{t('premiumUi.yogas.celestialSignature')}</Text>
            <Text style={[styles.heroTitle, { color: colors.textInverse }]}>
              {activeSection === 'doshas'
                ? t('premiumUi.yogasDoshas.doshaHeroTitle', 'Rules shown clearly.')
                : t('premiumUi.yogas.patternsPurpose')}
            </Text>
            <Text style={[styles.heroBody, { color: colors.textInverseMuted }]}>
              {activeSection === 'doshas'
                ? t('premiumUi.yogasDoshas.doshaHeroBody', 'Each check states whether it comes from a named classic or a later convention, and shows the exact rule or geometry used.')
                : t('yogas.intro', 'Planetary combinations in this chart that shape strengths, patterns, and life themes.')}
            </Text>
            <View style={[styles.heroMetrics, { borderTopColor: colors.cosmicLine }]}>
              <View style={styles.heroMetric}>
                <Text style={[styles.metricValue, { color: colors.accent }]}>{totalYogas}</Text>
                <Text style={[styles.metricLabel, { color: colors.textInverseMuted }]}>
                  {activeSection === 'doshas'
                    ? t('premiumUi.yogasDoshas.doshasChecked', 'Doshas checked')
                    : t('premiumUi.yogas.yogasFound')}
                </Text>
              </View>
              <View style={[styles.metricDivider, { backgroundColor: colors.cosmicLine }]} />
              <View style={styles.heroMetric}>
                <Text style={[styles.metricValue, { color: colors.accent }]}>{visibleCategories.length}</Text>
                <Text style={[styles.metricLabel, { color: colors.textInverseMuted }]}>{t('premiumUi.yogas.lifeThemes')}</Text>
              </View>
            </View>
          </View>

          <View style={styles.sectionHeader}>
            <View>
              <Text style={[styles.sectionEyebrow, { color: colors.primaryStrong }]}>{t('premiumUi.yogas.detected')}</Text>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>
                {activeSection === 'doshas'
                  ? t('premiumUi.yogasDoshas.exploreDoshas', 'Review classical Dosha checks')
                  : t('premiumUi.yogas.explore')}
              </Text>
            </View>
            {visibleCategories.length > 1 ? (
              <TouchableOpacity onPress={() => setExpandedCategories(expandedCategories.size === visibleCategories.length ? new Set() : new Set(visibleCategories.map((category) => category.key)))}>
                <Text style={[styles.expandAllText, { color: colors.primaryStrong }]}>{t(expandedCategories.size === visibleCategories.length ? 'premiumUi.yogas.collapse' : 'premiumUi.yogas.expandAll')}</Text>
              </TouchableOpacity>
            ) : null}
          </View>

          {visibleCategories.length > 0 ? visibleCategories.map(renderCategory) : (
            <View style={[styles.emptyCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
              <View style={[styles.emptyIcon, { backgroundColor: colors.accentSoft }]}>
                <Ionicons name="sparkles-outline" size={24} color={colors.primaryStrong} />
              </View>
              <Text style={[styles.emptyTitle, { color: colors.text }]}>{t('premiumUi.yogas.noCombinations')}</Text>
              <Text style={[styles.emptyBody, { color: colors.textSecondary }]}>{t('premiumUi.yogas.noDetails')}</Text>
            </View>
          )}
        </Animated.View>
      </ScrollView>
      {renderPitriInfoModal()}
      {renderMangalInfoModal()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  headerShell: { borderBottomWidth: StyleSheet.hairlineWidth },
  header: { minHeight: 72, paddingHorizontal: 18, paddingVertical: 10, flexDirection: 'row', alignItems: 'center', gap: 12 },
  headerButton: { width: 42, height: 42, borderRadius: 21, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  headerCopy: { flex: 1 },
  headerEyebrow: { ...typographyTokens.eyebrow, fontSize: 9, marginBottom: 3 },
  headerTitle: { ...typographyTokens.sectionTitle, fontSize: 25 },
  scrollView: { flex: 1 },
  scrollContent: { paddingHorizontal: 18, paddingTop: 18, paddingBottom: 48 },
  sectionTabs: { flexDirection: 'row', borderRadius: 16, borderWidth: 1, padding: 4, marginBottom: 14 },
  sectionTab: { flex: 1, minHeight: 42, borderRadius: 12, borderWidth: 1, borderColor: 'transparent', alignItems: 'center', justifyContent: 'center' },
  sectionTabText: { fontSize: 13, fontWeight: '800' },
  loadingContainer: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 28 },
  loadingMark: { width: 58, height: 58, borderRadius: 29, borderWidth: 1, alignItems: 'center', justifyContent: 'center', marginBottom: 18 },
  loadingTitle: { ...typographyTokens.sectionTitle, fontSize: 22, marginBottom: 6 },
  loadingText: { fontSize: 14, textAlign: 'center' },
  heroCard: { borderRadius: 28, borderWidth: 1, padding: 24, overflow: 'hidden', marginBottom: 28 },
  orbitLarge: { position: 'absolute', width: 176, height: 176, borderRadius: 88, borderWidth: 1, right: -74, top: -80 },
  orbitSmall: { position: 'absolute', width: 118, height: 118, borderRadius: 59, borderWidth: 1, right: -18, top: -58 },
  heroEyebrow: { ...typographyTokens.eyebrow, marginBottom: 14 },
  heroTitle: { ...typographyTokens.display, fontSize: 36, lineHeight: 40, maxWidth: 270, marginBottom: 12 },
  heroBody: { fontSize: 15, lineHeight: 23, maxWidth: 310 },
  heroMetrics: { flexDirection: 'row', borderTopWidth: StyleSheet.hairlineWidth, marginTop: 22, paddingTop: 18 },
  heroMetric: { flex: 1 },
  metricValue: { ...typographyTokens.sectionTitle, fontSize: 28, lineHeight: 31 },
  metricLabel: { ...typographyTokens.eyebrow, fontSize: 9, marginTop: 4 },
  metricDivider: { width: StyleSheet.hairlineWidth, marginHorizontal: 18 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', gap: 16, marginBottom: 14 },
  sectionEyebrow: { ...typographyTokens.eyebrow, fontSize: 9, marginBottom: 5 },
  sectionTitle: { ...typographyTokens.sectionTitle, fontSize: 23 },
  expandAllText: { fontSize: 12, fontWeight: '800', paddingVertical: 5 },
  categoryBlock: { borderRadius: 20, borderWidth: 1, marginBottom: 12, overflow: 'hidden' },
  categoryRow: { minHeight: 76, paddingHorizontal: 14, paddingVertical: 12, flexDirection: 'row', alignItems: 'center', gap: 12 },
  categoryIcon: { width: 44, height: 44, borderRadius: 15, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  categoryTextWrap: { flex: 1 },
  categoryTitle: { ...typographyTokens.sectionTitle, fontSize: 17, lineHeight: 21, marginBottom: 3 },
  categoryCount: { fontSize: 12, lineHeight: 16 },
  expandButton: { width: 30, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center' },
  infoButton: { width: 34, height: 34, borderRadius: 17, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  yogasList: { borderTopWidth: StyleSheet.hairlineWidth, paddingHorizontal: 16 },
  yogaItem: { paddingVertical: 17 },
  yogaItemHeader: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  classicalBasis: { borderWidth: 1, borderRadius: 14, padding: 13, marginTop: 13, gap: 8 },
  classicalBasisTitle: { ...typographyTokens.eyebrow, fontSize: 10 },
  classicalConditionRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  classicalDot: { width: 5, height: 5, borderRadius: 3, marginTop: 7 },
  classicalConditionText: { flex: 1, fontSize: 13, lineHeight: 19 },
  classicalResult: { borderTopWidth: StyleSheet.hairlineWidth, paddingTop: 9, gap: 4 },
  classicalResultTitle: { fontSize: 12, lineHeight: 17, fontWeight: '800' },
  referenceRow: { flexDirection: 'row', alignItems: 'center', gap: 7, borderTopWidth: StyleSheet.hairlineWidth, paddingTop: 9, marginTop: 2 },
  referenceText: { flex: 1, fontSize: 12, lineHeight: 17, fontWeight: '700' },
  textualNote: { fontSize: 11, lineHeight: 17 },
  variantNote: { fontSize: 11, lineHeight: 17, fontWeight: '700' },
  resultDeliveryCard: { borderWidth: 1, borderRadius: 14, padding: 13, marginTop: 13 },
  resultDeliveryTitle: { ...typographyTokens.sectionTitle, fontSize: 15, lineHeight: 20, marginBottom: 5 },
  resultDeliveryBody: { fontSize: 12, lineHeight: 18 },
  resultDeliveryChannels: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 10 },
  resultDeliveryChip: { minHeight: 31, maxWidth: '100%', borderWidth: 1, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 6, justifyContent: 'center' },
  resultDeliveryChipText: { fontSize: 11, lineHeight: 15, fontWeight: '700' },
  resultDeliveryBoundary: { fontSize: 10, lineHeight: 15, fontStyle: 'italic', marginTop: 9 },
  yogaOrdinal: { minWidth: 28, height: 28, borderRadius: 9, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  yogaOrdinalText: { fontSize: 9, fontWeight: '800', letterSpacing: 0.8 },
  yogaName: { flex: 1, ...typographyTokens.sectionTitle, fontSize: 17, lineHeight: 22, paddingTop: 2 },
  strengthBadge: { borderRadius: 999, paddingHorizontal: 9, paddingVertical: 5 },
  strengthText: { fontSize: 9, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.7 },
  yogaDescription: { fontSize: 14, lineHeight: 21, marginTop: 10, paddingLeft: 38 },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 12, paddingLeft: 38 },
  metaChip: { minHeight: 29, borderRadius: 999, borderWidth: 1, paddingHorizontal: 9, flexDirection: 'row', alignItems: 'center', gap: 5 },
  metaText: { fontSize: 11, fontWeight: '600' },
  emptyCard: { borderRadius: 20, borderWidth: 1, padding: 26, alignItems: 'center' },
  emptyIcon: { width: 50, height: 50, borderRadius: 25, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  emptyTitle: { ...typographyTokens.sectionTitle, fontSize: 19, marginBottom: 6 },
  emptyBody: { fontSize: 13, lineHeight: 19, textAlign: 'center' },
  modalBackdrop: { flex: 1, backgroundColor: 'rgba(18, 4, 11, 0.58)', justifyContent: 'flex-end', alignItems: 'center' },
  modalSafeArea: { width: '100%', maxWidth: 760, maxHeight: '94%', justifyContent: 'flex-end' },
  modalSheet: { maxHeight: '100%', borderTopLeftRadius: 28, borderTopRightRadius: 28, borderWidth: 1, overflow: 'hidden' },
  modalHeader: { minHeight: 82, paddingHorizontal: 20, paddingVertical: 15, flexDirection: 'row', alignItems: 'center', gap: 14, borderBottomWidth: StyleSheet.hairlineWidth },
  modalHeaderCopy: { flex: 1 },
  modalEyebrow: { ...typographyTokens.eyebrow, fontSize: 9, marginBottom: 4 },
  modalTitle: { ...typographyTokens.sectionTitle, fontSize: 22, lineHeight: 27 },
  modalClose: { width: 40, height: 40, borderRadius: 20, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  modalContent: { paddingHorizontal: 20, paddingTop: 18, paddingBottom: 30 },
  modalIntro: { fontSize: 14, lineHeight: 21, marginBottom: 15 },
  scopeCard: { borderWidth: 1, borderRadius: 16, padding: 14, flexDirection: 'row', alignItems: 'flex-start', gap: 11, marginBottom: 21 },
  scopeCopy: { flex: 1 },
  scopeTitle: { fontSize: 13, lineHeight: 18, fontWeight: '800', marginBottom: 3 },
  scopeBody: { fontSize: 13, lineHeight: 19 },
  logicTitle: { ...typographyTokens.sectionTitle, fontSize: 17, lineHeight: 22, marginBottom: 5 },
  logicBody: { fontSize: 13, lineHeight: 20, marginBottom: 13 },
  ruleList: { gap: 9, marginBottom: 22 },
  ruleCard: { borderWidth: 1, borderRadius: 14, paddingHorizontal: 13, paddingVertical: 12 },
  ruleHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 6 },
  ruleReference: { fontSize: 11, lineHeight: 15, fontWeight: '900', letterSpacing: 0.5 },
  matchBadge: { borderRadius: 999, minHeight: 23, paddingHorizontal: 8, flexDirection: 'row', alignItems: 'center', gap: 4 },
  matchBadgeText: { fontSize: 9, lineHeight: 12, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 0.4 },
  ruleText: { fontSize: 13, lineHeight: 20 },
  methodRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 9, marginTop: 8 },
  methodDot: { width: 5, height: 5, borderRadius: 3, marginTop: 7 },
  methodText: { flex: 1, fontSize: 13, lineHeight: 20 },
  sourceCard: { borderWidth: 1, borderRadius: 16, padding: 14, marginTop: 20 },
  sourceHeadingRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 7 },
  sourceTitle: { fontSize: 13, lineHeight: 18, fontWeight: '800' },
  sourceText: { fontSize: 12, lineHeight: 19 },
  editionNote: { fontSize: 11, lineHeight: 17, marginTop: 7 },
  mangalVerdictCard: { borderWidth: 1, borderRadius: 16, padding: 14, marginBottom: 22, gap: 10 },
  mangalVerdictHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  mangalVerdictLabel: { fontSize: 11, lineHeight: 15, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.5 },
  mangalVerdictText: { fontSize: 16, lineHeight: 22, fontWeight: '800' },
  conditionLine: { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  conditionLineText: { flex: 1, fontSize: 13, lineHeight: 19 },
  referenceCountList: { gap: 8, marginBottom: 22 },
  referenceCountRow: { minHeight: 62, borderWidth: 1, borderRadius: 14, paddingHorizontal: 13, paddingVertical: 10, flexDirection: 'row', alignItems: 'center', gap: 12 },
  referenceCountCopy: { flex: 1 },
  referenceCountLabel: { fontSize: 14, lineHeight: 19, fontWeight: '800', marginBottom: 2 },
  referenceCountHouse: { fontSize: 12, lineHeight: 17 },
  referenceCountStatus: { maxWidth: '43%', fontSize: 11, lineHeight: 16, textAlign: 'right', fontWeight: '800' },
  variantReadingCard: { borderWidth: 1, borderRadius: 14, padding: 13, marginBottom: 22 },
  variantReadingText: { fontSize: 13, lineHeight: 19 },
  variantDifference: { fontSize: 12, lineHeight: 18, fontWeight: '800', marginTop: 7 },
});

export default YogaScreen;
