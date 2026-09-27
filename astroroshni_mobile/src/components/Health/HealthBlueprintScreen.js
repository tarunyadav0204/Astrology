import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, useWindowDimensions, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';

import { useTheme } from '../../context/ThemeContext';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import { chartAPI } from '../../services/api';
import { storage } from '../../services/storage';

const valueKey = (value) => String(value || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
const nativeKey = (birth) => String(
  birth?.id
  || birth?.birth_chart_id
  || [birth?.name, birth?.date, birth?.time, birth?.latitude, birth?.longitude].join('|')
);
const sentenceCase = (value) => {
  const characters = Array.from(String(value || '').trim());
  return characters.length ? `${characters[0].toUpperCase()}${characters.slice(1).join('')}` : '';
};
const ordinal = (value) => {
  const number = Number(value);
  const remainder100 = number % 100;
  if (remainder100 >= 11 && remainder100 <= 13) return `${number}th`;
  if (number % 10 === 1) return `${number}st`;
  if (number % 10 === 2) return `${number}nd`;
  if (number % 10 === 3) return `${number}rd`;
  return `${number}th`;
};

export default function HealthBlueprintScreen({ navigation, route }) {
  const { t, i18n } = useTranslation();
  const { colors } = useTheme();
  const { width: windowWidth } = useWindowDimensions();
  const isTablet = windowWidth >= 768;
  const [activeTab, setActiveTab] = useState(route?.params?.initialTab === 'timing' ? 'timing' : 'profile');
  const [birthData, setBirthData] = useState(route?.params?.birthData || null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(null);
  const [showConstitutionBasis, setShowConstitutionBasis] = useState(false);
  const [showVulnerabilityBasis, setShowVulnerabilityBasis] = useState(false);
  const [timingResult, setTimingResult] = useState(null);
  const [timingLoading, setTimingLoading] = useState(false);
  const [timingError, setTimingError] = useState('');
  const [selectedTimingDate, setSelectedTimingDate] = useState(null);
  const [selectedTimingFinding, setSelectedTimingFinding] = useState(null);
  const [timingRangeDays, setTimingRangeDays] = useState(180);
  const [showTimingTechnical, setShowTimingTechnical] = useState(false);
  const loadedNativeKeyRef = useRef(nativeKey(route?.params?.birthData));
  const profileRequestRef = useRef(0);
  const timingRequestRef = useRef(0);
  const activeTimingRequestKeyRef = useRef(null);

  const selectNative = useCallback(() => {
    navigation.navigate('SelectNative', {
      returnTo: 'HealthBlueprint',
      selectionReturnParams: {
        chartData: null,
        initialTab: activeTab,
      },
    });
  }, [activeTab, navigation]);

  const load = useCallback(async () => {
    const requestId = profileRequestRef.current + 1;
    profileRequestRef.current = requestId;
    setLoading(true);
    setError('');
    try {
      const birth = route?.params?.birthData || await storage.getBirthDetails();
      if (requestId !== profileRequestRef.current) return;
      if (!birth?.date || !birth?.time) {
        navigation.replace('BirthProfileIntro', { returnTo: 'HealthBlueprint' });
        return;
      }
      const nextNativeKey = nativeKey(birth);
      if (loadedNativeKeyRef.current !== nextNativeKey) {
        loadedNativeKeyRef.current = nextNativeKey;
        timingRequestRef.current += 1;
        activeTimingRequestKeyRef.current = null;
        setTimingResult(null);
        setTimingError('');
        setTimingLoading(false);
        setSelectedTimingDate(null);
        setSelectedTimingFinding(null);
        setShowTimingTechnical(false);
        setExpanded(null);
      }
      setBirthData(birth);
      const response = await chartAPI.getHealthBlueprint({ birthData: birth, chartData: route?.params?.chartData || null });
      if (requestId !== profileRequestRef.current || loadedNativeKeyRef.current !== nextNativeKey) return;
      setResult(response.data?.result || null);
    } catch (requestError) {
      if (requestId !== profileRequestRef.current) return;
      const detail = requestError?.response?.data?.detail;
      if (requestError?.response?.status === 403 && detail?.code === 'ASTROLOGER_LICENSE_REQUIRED') {
        navigation.replace('Credits', {
          focusSubscriptionFamily: 'astrologer',
          returnTo: 'HealthBlueprint',
          returnParams: { birthData: route?.params?.birthData },
        });
        return;
      }
      setError(i18n.language === 'english' && typeof detail === 'string' ? detail : t('healthBlueprint.errors.calculate'));
    } finally {
      if (requestId === profileRequestRef.current) setLoading(false);
    }
  }, [i18n.language, navigation, route?.params?.birthData, route?.params?.chartData, t]);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const loadTiming = useCallback(async () => {
    if (!birthData) return;
    const requestedNativeKey = nativeKey(birthData);
    const requestKey = `${requestedNativeKey}:${timingRangeDays}`;
    if (activeTimingRequestKeyRef.current === requestKey) return;
    const requestId = timingRequestRef.current + 1;
    timingRequestRef.current = requestId;
    activeTimingRequestKeyRef.current = requestKey;
    setTimingLoading(true);
    setTimingError('');
    try {
      const now = new Date();
      const startDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;
      const response = await chartAPI.getHealthTimingHeatmap({
        birthData,
        chartData: route?.params?.chartData || null,
        startDate,
        days: timingRangeDays,
      });
      if (requestId !== timingRequestRef.current || loadedNativeKeyRef.current !== requestedNativeKey) return;
      const timing = response.data?.result || null;
      setTimingResult(timing);
      const initialGroup = isTablet ? timing?.period_groups?.[0] || null : null;
      setSelectedTimingDate(initialGroup);
      setSelectedTimingFinding(initialGroup?.windows?.[0] || null);
    } catch (requestError) {
      if (requestId !== timingRequestRef.current || loadedNativeKeyRef.current !== requestedNativeKey) return;
      const detail = requestError?.response?.data?.detail;
      setTimingError(typeof detail === 'string' ? detail : t('healthBlueprint.timing.error'));
    } finally {
      if (requestId === timingRequestRef.current) {
        activeTimingRequestKeyRef.current = null;
        setTimingLoading(false);
      }
    }
  }, [birthData, isTablet, route?.params?.chartData, t, timingRangeDays]);

  useEffect(() => {
    if (activeTab === 'timing' && !timingResult && !timingLoading) loadTiming();
  }, [activeTab, loadTiming, timingLoading, timingResult]);

  const localizeSign = (value) => t(`signs.${value}`, value || '—');
  const localizePlanet = (value) => t(`home.planet_names.${value}`, value || '—');
  const isEnglish = i18n.language === 'english';
  const bodyFocus = useCallback((item) => isEnglish
    ? (item.body_zones || []).join(', ')
    : t(`healthBlueprint.systems.${valueKey(item.system)}`, t('healthBlueprint.systems.general')), [isEnglish, t]);
  const vulnerabilityTitle = useCallback((item) => {
    const stableId = item.stable_id || item.finding_id || '';
    const condition = String(stableId).replace('health.condition.', '');
    if (item.claim_type !== 'named_classical_susceptibility' || !condition) return sentenceCase(bodyFocus(item) || item.label);
    return sentenceCase(t(`healthBlueprint.conditions.${condition}.title`, item.label || bodyFocus(item)));
  }, [bodyFocus, t]);
  const gradeLabel = (value) => t(`healthBlueprint.grades.${valueKey(value)}`, value);
  const statusLabel = (value) => t(`healthBlueprint.protection.statuses.${valueKey(value)}`, value);
  const conditionLabel = (group, value) => t(`healthBlueprint.protection.${group}.${valueKey(value)}`, String(value || '—').replace(/_/g, ' '));
  const planetList = (values) => (values || []).map(localizePlanet).join(', ');
  const afflictionText = (detail) => {
    if (detail.type === 'joined_by_malefics') return t('healthBlueprint.constitution.afflictions.joined', { planets: planetList(detail.planets) });
    if (detail.type === 'aspected_by_malefics') return t('healthBlueprint.constitution.afflictions.aspected', { planets: planetList(detail.planets) });
    if (detail.type === 'difficult_house') return t('healthBlueprint.constitution.afflictions.difficultHouse', { house: detail.house });
    if (detail.type === 'debilitated') return t('healthBlueprint.constitution.afflictions.debilitated');
    if (detail.type === 'combust') return t('healthBlueprint.constitution.afflictions.combust');
    if (detail.type === 'inimical_sign') return t('healthBlueprint.constitution.afflictions.inimicalSign', { planet: localizePlanet(detail.dispositor) });
    if (detail.type === 'inimical_nakshatra_lord') return t('healthBlueprint.constitution.afflictions.inimicalNakshatraLord', {
      nakshatra: detail.nakshatra,
      planet: localizePlanet(detail.lord),
    });
    if (detail.type === 'waning_moon') return t('healthBlueprint.constitution.afflictions.waningMoon');
    return '';
  };
  const strengtheningText = (factor) => {
    if (factor.type === 'dignity') return t('healthBlueprint.constitution.strengthening.dignity', { dignity: conditionLabel('dignity', factor.value) });
    if (factor.type === 'divisional_reinforcement') return t('healthBlueprint.constitution.strengthening.divisional', { charts: (factor.charts || []).join(', ') });
    if (factor.type === 'vargottama_d1_d9') return t('healthBlueprint.constitution.strengthening.vargottama');
    if (factor.type === 'supportive_house_placement') return t('healthBlueprint.constitution.strengthening.supportiveHouse', {
      house: factor.house,
      group: t(`healthBlueprint.constitution.houseGroups.${factor.group}`),
    });
    if (factor.type === 'friendly_sign') return t('healthBlueprint.constitution.strengthening.friendlySign', { planet: localizePlanet(factor.dispositor) });
    if (factor.type === 'waxing_moon') return t('healthBlueprint.constitution.strengthening.waxingMoon');
    if (factor.type === 'nakshatra_lord_support') {
      const base = t(`healthBlueprint.constitution.strengthening.${factor.relationship === 'own' ? 'nakshatraOwn' : 'nakshatraFriendly'}`, {
        nakshatra: factor.nakshatra,
        planet: localizePlanet(factor.lord),
      });
      if (!factor.lord_affliction_details?.length) return base;
      const suffix = t(`healthBlueprint.constitution.strengthening.${factor.lord_retrograde ? 'nakshatraQualifiedRetrogradeSuffix' : 'nakshatraQualifiedSuffix'}`, {
        planet: localizePlanet(factor.lord),
      });
      return `${base} ${suffix}`;
    }
    if (factor.type === 'mutual_sign_exchange') {
      const hasOtherLordship = factor.partner_other_ruled_houses?.length > 0;
      const key = factor.partner_affliction_details?.length
        ? (factor.partner_retrograde
          ? (hasOtherLordship ? 'exchangeQualifiedRetrogradeOther' : 'exchangeQualifiedRetrograde')
          : (hasOtherLordship ? 'exchangeQualifiedOther' : 'exchangeQualified'))
        : 'exchange';
      return t(`healthBlueprint.constitution.strengthening.${key}`, {
        planet: localizePlanet(factor.planet),
        houses: (factor.houses || []).join(t('healthBlueprint.constitution.houseJoiner')),
        otherHouses: (factor.partner_other_ruled_houses || []).join(t('healthBlueprint.constitution.houseJoiner')),
      });
    }
    return '';
  };
  const planetDeliveryText = (context) => {
    const nakshatra = context?.nakshatra_context;
    if (!nakshatra) return t('healthBlueprint.evidence.planetDeliveryUnavailable', { planet: localizePlanet(context?.planet) });
    return t('healthBlueprint.evidence.planetDeliverySummary', {
      planet: localizePlanet(context.planet),
      nakshatra: nakshatra.nakshatra,
      lord: localizePlanet(nakshatra.lord),
      relationship: t(`healthBlueprint.constitution.nakshatraRelationships.${nakshatra.relationship}`),
    });
  };
  const neutralFactorText = (factor) => {
    if (factor.type === 'neutral_sign_relationship') return t('healthBlueprint.constitution.neutralFactors.rashi', {
      rashi: localizeSign(factor.sign_name),
      planet: localizePlanet(factor.dispositor),
    });
    if (factor.type === 'neutral_nakshatra_relationship') return t('healthBlueprint.constitution.neutralFactors.nakshatra', {
      nakshatra: factor.nakshatra,
      planet: localizePlanet(factor.lord),
    });
    if (factor.type === 'ungraded_nakshatra_relationship') return t('healthBlueprint.constitution.neutralFactors.nodeNakshatra', {
      nakshatra: factor.nakshatra,
      planet: localizePlanet(factor.lord),
    });
    return '';
  };
  const pillarFactorText = (factor, house) => t(`healthBlueprint.protection.pillarFactors.${factor.type}`, {
    planet: localizePlanet(factor.planet),
    house,
    relation: t(`healthBlueprint.protection.relations.${factor.relation}`),
    houses: (factor.houses || []).join(t('healthBlueprint.constitution.houseJoiner')),
  });
  const findingFactorText = (factor) => {
    const pillarTypes = new Set([
      'natural_benefic', 'supportive_lordship', 'natural_malefic', 'waning_moon',
      'challenging_lordship', 'mixed_lordship_support', 'mixed_lordship_pressure',
      'qualified_lordship', 'yogi_support', 'reversed_avayogi_support',
      'avayogi_pressure', 'tithi_dagdha',
    ]);
    if (pillarTypes.has(factor.type)) return pillarFactorText(factor, factor.house);
    if (['joined_by_malefics', 'aspected_by_malefics', 'difficult_house', 'debilitated', 'combust', 'inimical_sign', 'inimical_nakshatra_lord'].includes(factor.type)) {
      return `${localizePlanet(factor.planet)}: ${afflictionText(factor)}`;
    }
    if (factor.type === 'friendly_sign') return `${localizePlanet(factor.planet)}: ${strengtheningText(factor)}`;
    if (factor.type === 'nakshatra_lord_support') return `${localizePlanet(factor.planet)}: ${strengtheningText(factor)}`;
    if (factor.type === 'dignity_capacity') return t('healthBlueprint.evidence.modifiers.dignity', { planet: localizePlanet(factor.planet), dignity: conditionLabel('dignity', factor.value) });
    if (factor.type === 'vargottama_capacity') return t(`healthBlueprint.evidence.modifiers.vargottama_${factor.agenda || 'support'}`, { planet: localizePlanet(factor.planet) });
    if (factor.type === 'divisional_capacity') return t(`healthBlueprint.evidence.modifiers.divisional_${factor.status}`, {
      planet: localizePlanet(factor.planet),
      strong: (factor.strong_vargas || []).join(', ') || '—',
      weak: (factor.weak_vargas || []).join(', ') || '—',
    });
    if (factor.type === 'neecha_bhanga') return t('healthBlueprint.evidence.modifiers.neechaBhanga', { planet: localizePlanet(factor.planet) });
    if (factor.type === 'retrograde_intensification') return t('healthBlueprint.evidence.modifiers.retrograde', { planet: localizePlanet(factor.planet) });
    if (factor.type === 'mutual_exchange_capacity') return t('healthBlueprint.evidence.modifiers.mutualExchange', {
      planet: localizePlanet(factor.planet),
      partner: localizePlanet(factor.partner),
      houses: (factor.houses || []).join(t('healthBlueprint.constitution.houseJoiner')),
    });
    return `${localizePlanet(factor.planet)}: ${String(factor.type || '').replace(/_/g, ' ')}`;
  };
  const jupiterReachText = (reach) => t('healthBlueprint.protection.jupiterReach', {
    house: reach.house,
    mode: t(`healthBlueprint.protection.jupiterModes.${reach.mode}`),
    focus: t(`healthBlueprint.protection.jupiterHouseFocus.${reach.health_focus_key}`),
  });
  const dashaExplanationText = (row) => {
    const facts = [];
    if (row.direct_finding_planet) facts.push(t('healthBlueprint.timing.dashaFacts.direct'));
    if ((row.reasons || []).includes('occupies_relevant_house')) facts.push(t('healthBlueprint.timing.dashaFacts.occupies', { house: row.natal_house }));
    if (row.connected_houses?.length) facts.push(t('healthBlueprint.timing.dashaFacts.rules', { houses: row.connected_houses.join(t('healthBlueprint.constitution.houseJoiner')) }));
    if (row.aspected_relevant_houses?.length) facts.push(t('healthBlueprint.timing.dashaFacts.aspects', { houses: row.aspected_relevant_houses.join(t('healthBlueprint.constitution.houseJoiner')) }));
    return t('healthBlueprint.timing.dashaExplanation', {
      planet: localizePlanet(row.planet),
      effect: t(`healthBlueprint.timing.dashaEffects.${row.level}`),
      facts: facts.join(t('healthBlueprint.timing.factJoiner')),
    });
  };
  const transitHouseActivationText = (activation) => t(`healthBlueprint.timing.transitHouse.${activation.mode}`, {
    planet: localizePlanet(activation.transit_planet),
    transitHouse: activation.transit_house,
    targetHouse: activation.target_house,
    aspect: activation.aspect_number,
  }) + (activation.repeats_natal_house ? ` ${t('healthBlueprint.timing.transitHouse.natalRepeat', { planet: localizePlanet(activation.transit_planet), house: activation.transit_house })}` : '');
  const transitContactText = (contact) => {
    const key = contact.aspect_angle === 0 ? 'conjunction' : 'aspect';
    const aspectNumber = contact.aspect_number || (Number(contact.aspect_angle) / 30) + 1;
    const base = t(`healthBlueprint.timing.exactContact.${key}`, {
      transit: localizePlanet(contact.transit_planet),
      natal: localizePlanet(contact.natal_planet),
      transitHouse: contact.transit_house,
      natalHouse: contact.natal_house,
      aspect: aspectNumber,
      aspectOrdinal: ordinal(aspectNumber),
      orb: contact.orb,
    });
    return contact.returns_to_own_natal_position ? `${base} ${t('healthBlueprint.timing.exactContact.ownReturn', { planet: localizePlanet(contact.transit_planet) })}` : base;
  };
  const houseListText = (houses) => (houses || []).map((house) => t('healthBlueprint.timing.houseShort', { house })).join(', ');
  const dashaHouseActivatorText = (activator) => t(`healthBlueprint.timing.houseActivation.dasha.${activator.mode}`, {
    planet: localizePlanet(activator.planet),
    level: t(`healthBlueprint.timing.dashaLevels.${activator.level}`),
  });
  const transitHouseActivatorText = (activator) => t(`healthBlueprint.timing.houseActivation.transit.${activator.mode}`, {
    planet: localizePlanet(activator.planet),
    fromHouse: activator.from_house,
    aspect: activator.aspect_number,
  });
  const timingFindingTitle = (detail) => detail.manifestation_scope === 'body_system_activation'
    ? sentenceCase(t('healthBlueprint.timing.bodySystemSensitivity', { system: bodyFocus(detail) }))
    : vulnerabilityTitle(detail);
  const card = [styles.card, isTablet && styles.cardTablet, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }];

  const anatomicalVulnerabilities = useMemo(
    () => (result?.vulnerabilities || []).filter((item) => item.claim_type !== 'named_classical_susceptibility'),
    [result],
  );
  const diseaseIndications = useMemo(
    () => (result?.vulnerabilities || []).filter((item) => item.claim_type === 'named_classical_susceptibility'),
    [result],
  );
  const menstrualCycle = result?.female_health?.menstrual_cycle || null;
  const activeMenstrualFactors = menstrualCycle?.active_factor_groups
    || Object.entries(menstrualCycle?.factor_groups || {}).filter(([, active]) => active).map(([factor]) => factor);
  const vitalityAnchors = useMemo(() => {
    const grouped = new Map();
    (result?.constitutional_protection?.vitality_anchors || []).forEach((anchor) => {
      const key = anchor.planet || anchor.role;
      const current = grouped.get(key);
      if (current) current.roles.push(anchor.role);
      else grouped.set(key, { ...anchor, roles: [anchor.role] });
    });
    return [...grouped.values()];
  }, [result]);


  const renderFinding = (item) => {
    const isOpen = expanded === item.stable_id;
    const evidenceGrade = item.evidence_grade || item.support_grade;
    return (
      <TouchableOpacity key={item.stable_id} activeOpacity={0.88} onPress={() => setExpanded(isOpen ? null : item.stable_id)} style={[...card, isTablet && styles.vulnerabilityCardTablet]}>
        <View style={styles.row}>
          <View style={styles.grow}>
            <Text style={[styles.grade, isTablet && styles.gradeTablet, { color: evidenceGrade === 'strong' ? colors.primary : colors.textSecondary }]}>{gradeLabel(evidenceGrade)}</Text>
            <Text style={[styles.itemTitle, isTablet && styles.itemTitleTablet, { color: colors.text }]}>{vulnerabilityTitle(item)}</Text>
          </View>
          <Ionicons name={isOpen ? 'chevron-up' : 'chevron-down'} size={isTablet ? 24 : 20} color={colors.textSecondary} />
        </View>
        {!!item.delivery_balance && (
          <Text style={[styles.note, isTablet && styles.noteTablet, { color: colors.textSecondary }]}>{t(`healthBlueprint.evidence.deliveryBalances.${item.delivery_balance}`)}</Text>
        )}
        {item.body_zones?.length > 0 && (
          <View style={[styles.focusRow, isTablet && styles.focusRowTablet, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
            <Ionicons name="body-outline" size={isTablet ? 20 : 17} color={colors.primary} />
            <Text style={[styles.focusLabel, isTablet && styles.focusLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.bodyFocusLabel')}</Text>
            <Text style={[styles.focusValue, isTablet && styles.focusValueTablet, { color: colors.text }]}>{bodyFocus(item)}</Text>
          </View>
        )}
        {isOpen && (
          <View style={[styles.evidence, { borderTopColor: colors.cardBorder }]}>
            <Text style={[styles.evidenceTitle, isTablet && styles.evidenceTitleTablet, { color: colors.text }]}>{t('healthBlueprint.evidence.title')}</Text>
            {isEnglish
              ? (item.supporting_rules || []).map((rule, index) => <Text key={`${item.stable_id}-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {rule}</Text>)
              : <Text style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {t('healthBlueprint.evidence.localizedSummary', { grade: gradeLabel(evidenceGrade), focus: bodyFocus(item) })}</Text>}
            {item.mechanisms?.length > 0 && <Text style={[styles.note, isTablet && styles.noteTablet, { color: colors.textSecondary }]}>{isEnglish ? t('healthBlueprint.evidence.mechanisms', { mechanisms: item.mechanisms.join(', ') }) : t('healthBlueprint.evidence.mechanismsLocalized', { focus: bodyFocus(item) })}</Text>}
            {item.planetary_delivery?.length > 0 && (
              <View style={styles.factorBlock}>
                <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.evidence.planetDeliveryLabel')}</Text>
                {item.planetary_delivery.map((context) => (
                  <Text key={`delivery-${item.stable_id}-${context.planet}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {planetDeliveryText(context)}</Text>
                ))}
              </View>
            )}
            {item.protective_rules?.length > 0 && (
              <View style={styles.factorBlock}>
                <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.primary }]}>{t('healthBlueprint.evidence.protectionLabel')}</Text>
                {item.protective_rules.map((factor, index) => <Text key={`finding-support-${item.stable_id}-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {findingFactorText(factor)}</Text>)}
              </View>
            )}
            {item.contradicting_rules?.length > 0 && (
              <View style={styles.factorBlock}>
                <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.evidence.pressureLabel')}</Text>
                {item.contradicting_rules.map((factor, index) => <Text key={`finding-pressure-${item.stable_id}-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {findingFactorText(factor)}</Text>)}
              </View>
            )}
            {item.capacity_modifiers?.length > 0 && (
              <View style={styles.factorBlock}>
                <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.evidence.capacityLabel')}</Text>
                {item.capacity_modifiers.map((factor, index) => <Text key={`finding-capacity-${item.stable_id}-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {findingFactorText(factor)}</Text>)}
              </View>
            )}
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderProfile = () => (
    <ScrollView style={styles.reportScroll} contentContainerStyle={[styles.content, isTablet && styles.contentTablet]} showsVerticalScrollIndicator={false}>
      <View style={[styles.hero, isTablet && styles.heroTablet, { backgroundColor: colors.cosmicSurface || colors.headerSurface, borderColor: colors.cosmicLine || colors.cardBorder }]}>
        <Text style={[styles.eyebrow, isTablet && styles.eyebrowTablet, { color: colors.accent }]}>{t('healthBlueprint.heroEyebrow')}</Text>
        <Text style={[styles.heroTitle, isTablet && styles.heroTitleTablet, { color: colors.textInverse }]}>{t('healthBlueprint.heroTitle')}</Text>
        <Text style={[styles.heroBody, isTablet && styles.heroBodyTablet, { color: colors.textInverseMuted }]}>{t('healthBlueprint.heroBody')}</Text>
      </View>

      <Text style={[styles.listTitle, isTablet && styles.listTitleTablet, { color: colors.text }]}>{t('healthBlueprint.sections.constitution')}</Text>
      <View style={[...card, styles.constitutionSummaryCard, isTablet && styles.constitutionSummaryCardTablet, isTablet && styles.fullWidthCard]}>
        <Text style={[styles.eyebrow, isTablet && styles.eyebrowTablet, { color: colors.primary }]}>{t('healthBlueprint.constitution.vitalityLabel')}</Text>
        <Text style={[styles.sectionTitle, isTablet && styles.sectionTitleTablet, { color: colors.text }]}>{conditionLabel('resilience', result.constitutional_protection?.overall_resilience?.status)}</Text>
        <Text style={[styles.body, isTablet && styles.bodyTablet, { color: colors.textSecondary }]}>{t(`healthBlueprint.protection.resilienceExplanations.${result.constitutional_protection?.overall_resilience?.explanation || 'support_is_limited'}`)}</Text>
        <Text style={[styles.note, isTablet && styles.noteTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.constitution.vitalityBody')}</Text>
      </View>
      <View style={[styles.constitutionAnchorGrid, isTablet && styles.constitutionAnchorGridTablet]}>
        {vitalityAnchors.map((anchor) => (
          <View key={`constitution-${anchor.planet || anchor.role}`} style={[...card, styles.constitutionAnchorCard, isTablet && styles.constitutionAnchorCardTablet]}>
            <Text style={[styles.eyebrow, isTablet && styles.eyebrowTablet, { color: colors.primary }]}>
              {anchor.roles.map((role) => t(`healthBlueprint.constitution.anchorRoles.${role}`)).join(' · ')}
            </Text>
            <Text style={[styles.sectionTitle, isTablet && styles.sectionTitleTablet, { color: colors.text }]}>{localizePlanet(anchor.planet)}</Text>
            <View style={[styles.roleReasonBlock, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
              <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.constitution.whyPlanet')}</Text>
              {anchor.roles.map((role) => (
                <Text key={`reason-${anchor.planet}-${role}`} style={[styles.roleReason, isTablet && styles.roleReasonTablet, { color: colors.text }]}>
                  {t(`healthBlueprint.constitution.roleReasons.${role}`, {
                    planet: localizePlanet(anchor.planet),
                    sign: localizeSign(result.vitality_foundation.ascendant_sign),
                  })}
                </Text>
              ))}
            </View>
            <Text style={[styles.anchorVerdict, isTablet && styles.anchorVerdictTablet, { color: colors.text }]}>{conditionLabel('anchorStatuses', anchor.status)}</Text>
            <Text style={[styles.body, isTablet && styles.bodyTablet, { color: colors.textSecondary }]}>{t(`healthBlueprint.protection.anchorExplanations.${anchor.status}`)}</Text>
            <View style={[styles.factorBlock, { borderTopColor: colors.cardBorder }]}>
              <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.constitution.strengtheningLabel')}</Text>
              {anchor.strengthening_factors?.length
                ? anchor.strengthening_factors.map((factor, index) => <Text key={`strength-${anchor.planet}-${index}`} style={[styles.factorText, isTablet && styles.factorTextTablet, { color: colors.text }]}>• {strengtheningText(factor)}</Text>)
                : <Text style={[styles.factorText, isTablet && styles.factorTextTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.constitution.noDistinctStrengthening')}</Text>}
              <Text style={[styles.factorLabel, styles.factorLabelSpaced, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.constitution.weakeningLabel')}</Text>
              {anchor.affliction_details?.length
                ? anchor.affliction_details.map((detail, index) => <Text key={`affliction-${anchor.planet}-${index}`} style={[styles.factorText, isTablet && styles.factorTextTablet, { color: colors.text }]}>• {afflictionText(detail)}</Text>)
                : <Text style={[styles.factorText, isTablet && styles.factorTextTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.constitution.noWeakening')}</Text>}
              {anchor.neutral_factors?.length > 0 && (
                <>
                  <Text style={[styles.factorLabel, styles.factorLabelSpaced, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.constitution.neutralFactorsLabel')}</Text>
                  {anchor.neutral_factors.map((factor, index) => <Text key={`neutral-${anchor.planet}-${index}`} style={[styles.factorText, isTablet && styles.factorTextTablet, { color: colors.text }]}>• {neutralFactorText(factor)}</Text>)}
                </>
              )}
            </View>
          </View>
        ))}
      </View>
      <TouchableOpacity
        style={[styles.basisCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}
        onPress={() => setShowConstitutionBasis((value) => !value)}
        accessibilityRole="button"
        accessibilityState={{ expanded: showConstitutionBasis }}
      >
        <View style={styles.row}>
          <View style={styles.grow}>
            <Text style={[styles.basisTitle, isTablet && styles.basisTitleTablet, { color: colors.text }]}>{t('healthBlueprint.constitution.basisTitle')}</Text>
            <Text style={[styles.basisSummary, isTablet && styles.basisSummaryTablet, { color: colors.textSecondary }]}>
              {t('healthBlueprint.constitution.basisSummary', { sign: localizeSign(result.vitality_foundation.ascendant_sign), planet: localizePlanet(result.vitality_foundation.ascendant_lord) })}
            </Text>
          </View>
          <Ionicons name={showConstitutionBasis ? 'chevron-up' : 'chevron-down'} size={isTablet ? 24 : 20} color={colors.textSecondary} />
        </View>
        {showConstitutionBasis && (
          <View style={[styles.evidence, { borderTopColor: colors.cardBorder }]}>
            <Text style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.vitality.houses', { lagnaHouse: result.vitality_foundation.ascendant_lord_house || '—', sunHouse: result.vitality_foundation.sun_house || '—', moonHouse: result.vitality_foundation.moon_house || '—' })}</Text>
            <Text style={[styles.subsectionTitle, isTablet && styles.subsectionTitleTablet, { color: colors.text }]}>{t('healthBlueprint.protection.planetTitle')}</Text>
            <Text style={[styles.sectionIntro, isTablet && styles.sectionIntroTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.protection.planetIntro')}</Text>
            <View style={[styles.planetGrid, isTablet && styles.planetGridTablet]}>
              {Object.values(result.constitutional_protection?.planet_conditions || {}).map((planet) => (
                <View key={`condition-${planet.planet}`} style={[styles.planetRow, isTablet && styles.planetRowTablet, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
                  <Text style={[styles.planetName, isTablet && styles.planetNameTablet, { color: colors.text }]}>{localizePlanet(planet.planet)}</Text>
                  <Text style={[styles.planetMeta, isTablet && styles.planetMetaTablet, { color: colors.textSecondary }]}>{conditionLabel('functional', planet.functional_role?.classification)} · {conditionLabel('dignity', planet.dignity)} · {conditionLabel('delivery', planet.delivery_quality)}</Text>
                  <View style={styles.badgeRow}>
                    {planet.vargottama_d1_d9 && <Text style={[styles.badge, { color: colors.primary, borderColor: colors.primary }]}>{t('healthBlueprint.protection.vargottama')}</Text>}
                    {planet.combustion?.is_combust && <Text style={[styles.badge, { color: colors.textSecondary, borderColor: colors.cardBorder }]}>{t('healthBlueprint.protection.combust')}</Text>}
                    {planet.retrograde && <Text style={[styles.badge, { color: colors.textSecondary, borderColor: colors.cardBorder }]}>{t('healthBlueprint.protection.retrograde')}</Text>}
                    {(planet.special_roles || []).map((role) => <Text key={`${planet.planet}-${role}`} style={[styles.badge, { color: colors.textSecondary, borderColor: colors.cardBorder }]}>{conditionLabel('specialRoles', role)}</Text>)}
                  </View>
                </View>
              ))}
            </View>
          </View>
        )}
      </TouchableOpacity>

      <Text style={[styles.listTitle, isTablet && styles.listTitleTablet, { color: colors.text }]}>{t('healthBlueprint.sections.vulnerableAreas')}</Text>
      <Text style={[styles.sectionIntro, isTablet && styles.sectionIntroTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.sections.vulnerableAreasBody')}</Text>
      <TouchableOpacity
        style={[styles.basisCard, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}
        onPress={() => setShowVulnerabilityBasis((value) => !value)}
        accessibilityRole="button"
        accessibilityState={{ expanded: showVulnerabilityBasis }}
      >
        <View style={styles.row}>
          <View style={styles.grow}>
            <Text style={[styles.basisTitle, isTablet && styles.basisTitleTablet, { color: colors.text }]}>{t('healthBlueprint.sixth.basisTitle')}</Text>
            <Text style={[styles.basisSummary, isTablet && styles.basisSummaryTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.sixth.title', { sign: localizeSign(result.sixth_house_chain.sixth_house_sign), planet: localizePlanet(result.sixth_house_chain.sixth_lord) })}</Text>
          </View>
          <Ionicons name={showVulnerabilityBasis ? 'chevron-up' : 'chevron-down'} size={isTablet ? 24 : 20} color={colors.textSecondary} />
        </View>
        {showVulnerabilityBasis && (
          <View style={[styles.evidence, { borderTopColor: colors.cardBorder }]}>
            <Text style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.sixth.body', { sign: localizeSign(result.sixth_house_chain.sixth_lord_sign), house: result.sixth_house_chain.sixth_lord_house || '—', nakshatra: result.sixth_house_chain.sixth_lord_nakshatra || t('healthBlueprint.sixth.noNakshatra') })}</Text>
          </View>
        )}
      </TouchableOpacity>
      <View style={[styles.vulnerabilityGrid, isTablet && styles.vulnerabilityGridTablet]}>
        {anatomicalVulnerabilities.length ? anatomicalVulnerabilities.map(renderFinding) : <View style={[...card, isTablet && styles.fullWidthCard]}><Text style={[styles.body, isTablet && styles.bodyTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.noVulnerabilities')}</Text></View>}
      </View>

      {result.constitutional_protection && (
        <>
          <Text style={[styles.listTitle, isTablet && styles.listTitleTablet, { color: colors.text }]}>{t('healthBlueprint.sections.protectiveFactors')}</Text>
          <Text style={[styles.sectionIntro, isTablet && styles.sectionIntroTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.protection.intro')}</Text>
          <View style={[styles.summaryGrid, isTablet && styles.summaryGridTablet]}>
            <View style={[styles.summaryItem, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
              <Text style={[styles.focusLabel, isTablet && styles.focusLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.protection.kendraSummaryLabel')}</Text>
              <Text style={[styles.summaryValue, isTablet && styles.summaryValueTablet, { color: colors.text }]}>
                {t('healthBlueprint.protection.kendraSummary', {
                  protected: result.constitutional_protection.overall_resilience?.protected_pillars || 0,
                  mixed: result.constitutional_protection.overall_resilience?.mixed_pillars || 0,
                  pressured: result.constitutional_protection.overall_resilience?.pressured_pillars || 0,
                })}
              </Text>
            </View>
          </View>
          <View style={[styles.pillarGrid, isTablet && styles.pillarGridTablet]}>
            {(result.constitutional_protection.kendra_pillars || []).map((pillar) => (
              <View key={`pillar-${pillar.house}`} style={[...card, styles.pillarCard, isTablet && styles.pillarCardTablet]}>
                <Text style={[styles.grade, isTablet && styles.gradeTablet, { color: pillar.status === 'protected' ? colors.primary : colors.textSecondary }]}>{statusLabel(pillar.status)}</Text>
                <Text style={[styles.itemTitle, isTablet && styles.itemTitleTablet, { color: colors.text }]}>{t('healthBlueprint.protection.pillar', { house: pillar.house })}</Text>
                <Text style={[styles.note, isTablet && styles.noteTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.protection.factorCounts', { support: pillar.support_details?.length || 0, pressure: pillar.pressure_details?.length || 0 })}</Text>
                {pillar.support_details?.length > 0 && (
                  <>
                    <Text style={[styles.factorLabel, styles.factorLabelSpaced, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.protection.supportingFactorsLabel')}</Text>
                    {pillar.support_details.map((factor, index) => <Text key={`pillar-support-${pillar.house}-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {pillarFactorText(factor, pillar.house)}</Text>)}
                  </>
                )}
                {pillar.pressure_details?.length > 0 && (
                  <>
                    <Text style={[styles.factorLabel, styles.factorLabelSpaced, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.protection.pressureFactorsLabel')}</Text>
                    {pillar.pressure_details.map((factor, index) => <Text key={`pillar-pressure-${pillar.house}-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {pillarFactorText(factor, pillar.house)}</Text>)}
                  </>
                )}
              </View>
            ))}
          </View>
          <View style={[...card, styles.jupiterProtectionCard, isTablet && styles.jupiterProtectionCardTablet, isTablet && styles.fullWidthCard]}>
            <Text style={[styles.grade, isTablet && styles.gradeTablet, { color: colors.primary }]}>{conditionLabel('jupiterQuality', result.constitutional_protection.jupiter_protection?.quality)}</Text>
            <Text style={[styles.itemTitle, isTablet && styles.itemTitleTablet, { color: colors.text }]}>{t('healthBlueprint.protection.jupiterTitle')}</Text>
            <Text style={[styles.body, isTablet && styles.bodyTablet, { color: colors.textSecondary }]}>
              {t(`healthBlueprint.protection.jupiterConclusions.${result.constitutional_protection.jupiter_protection?.conclusion_key || result.constitutional_protection.jupiter_protection?.quality}`)}
            </Text>
            {result.constitutional_protection.jupiter_protection?.reach_details?.length > 0 && (
              <View style={styles.factorBlock}>
                <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.protection.jupiterWhereTitle')}</Text>
                {result.constitutional_protection.jupiter_protection.reach_details.map((reach) => (
                  <Text key={`jupiter-reach-${reach.house}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {jupiterReachText(reach)}</Text>
                ))}
              </View>
            )}
            {result.constitutional_protection.jupiter_protection?.support_factors?.length > 0 && (
              <View style={styles.factorBlock}>
                <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.primary }]}>{t('healthBlueprint.evidence.protectionLabel')}</Text>
                {result.constitutional_protection.jupiter_protection.support_factors.map((factor, index) => <Text key={`jupiter-support-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {findingFactorText(factor)}</Text>)}
              </View>
            )}
            {result.constitutional_protection.jupiter_protection?.pressure_factors?.length > 0 && (
              <View style={styles.factorBlock}>
                <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.evidence.pressureLabel')}</Text>
                {result.constitutional_protection.jupiter_protection.pressure_factors.map((factor, index) => <Text key={`jupiter-pressure-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {findingFactorText(factor)}</Text>)}
              </View>
            )}
            {result.constitutional_protection.jupiter_protection?.capacity_modifiers?.length > 0 && (
              <View style={styles.factorBlock}>
                <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.evidence.capacityLabel')}</Text>
                {result.constitutional_protection.jupiter_protection.capacity_modifiers.map((factor, index) => <Text key={`jupiter-capacity-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {findingFactorText(factor)}</Text>)}
              </View>
            )}
            {result.constitutional_protection.jupiter_protection?.first_house_expansion_tendency && <Text style={[styles.note, isTablet && styles.noteTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.protection.jupiterExpansion')}</Text>}
          </View>
        </>
      )}

      {menstrualCycle && (
        <>
          <Text style={[styles.listTitle, isTablet && styles.listTitleTablet, { color: colors.text }]}>{t('healthBlueprint.femaleHealth.sectionTitle')}</Text>
          <Text style={[styles.sectionIntro, isTablet && styles.sectionIntroTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.femaleHealth.sectionBody')}</Text>
          <TouchableOpacity
            activeOpacity={0.88}
            onPress={() => setExpanded(expanded === 'female-menstrual-cycle' ? null : 'female-menstrual-cycle')}
            style={[...card, isTablet && styles.fullWidthCard]}
          >
            <View style={styles.row}>
              <View style={styles.grow}>
                <Text style={[styles.grade, isTablet && styles.gradeTablet, { color: menstrualCycle.status === 'no_distinct_pattern' ? colors.textSecondary : colors.primary }]}>
                  {t(`healthBlueprint.femaleHealth.statuses.${menstrualCycle.status}`)}
                </Text>
                <Text style={[styles.itemTitle, isTablet && styles.itemTitleTablet, { color: colors.text }]}>{t('healthBlueprint.femaleHealth.menstrualTitle')}</Text>
              </View>
              <Ionicons name={expanded === 'female-menstrual-cycle' ? 'chevron-up' : 'chevron-down'} size={isTablet ? 24 : 20} color={colors.textSecondary} />
            </View>
            <Text style={[styles.body, isTablet && styles.bodyTablet, { color: colors.textSecondary }]}>{t(`healthBlueprint.femaleHealth.summaries.${menstrualCycle.status}`)}</Text>
            {expanded === 'female-menstrual-cycle' && (
              <View style={[styles.evidence, { borderTopColor: colors.cardBorder }]}> 
                <Text style={[styles.evidenceTitle, isTablet && styles.evidenceTitleTablet, { color: colors.text }]}>{t('healthBlueprint.femaleHealth.checkedTitle')}</Text>
                {activeMenstrualFactors.length > 0
                  ? activeMenstrualFactors.map((factor) => (
                    <Text key={`menstrual-${factor}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {t(`healthBlueprint.femaleHealth.factors.${factor}`)}</Text>
                  ))
                  : <Text style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {t('healthBlueprint.femaleHealth.noActiveFactors')}</Text>}
                {isEnglish && menstrualCycle.evidence?.length > 0 && (
                  <>
                    <Text style={[styles.factorLabel, styles.factorLabelSpaced, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.evidence.title')}</Text>
                    {menstrualCycle.evidence.map((line, index) => <Text key={`menstrual-evidence-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {line}</Text>)}
                  </>
                )}
                {menstrualCycle.protective_rules?.length > 0 && (
                  <View style={styles.factorBlock}>
                    <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.primary }]}>{t('healthBlueprint.evidence.protectionLabel')}</Text>
                    {menstrualCycle.protective_rules.map((factor, index) => <Text key={`menstrual-support-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {findingFactorText(factor)}</Text>)}
                  </View>
                )}
                {menstrualCycle.pressure_rules?.length > 0 && (
                  <View style={styles.factorBlock}>
                    <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.evidence.pressureLabel')}</Text>
                    {menstrualCycle.pressure_rules.map((factor, index) => <Text key={`menstrual-pressure-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {findingFactorText(factor)}</Text>)}
                  </View>
                )}
                {menstrualCycle.capacity_modifiers?.length > 0 && (
                  <View style={styles.factorBlock}>
                    <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.evidence.capacityLabel')}</Text>
                    {menstrualCycle.capacity_modifiers.map((factor, index) => <Text key={`menstrual-capacity-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {findingFactorText(factor)}</Text>)}
                  </View>
                )}
                <Text style={[styles.note, isTablet && styles.noteTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.femaleHealth.guidance')}</Text>
              </View>
            )}
          </TouchableOpacity>
        </>
      )}

      <Text style={[styles.listTitle, isTablet && styles.listTitleTablet, { color: colors.text }]}>{t('healthBlueprint.sections.diseaseIndications')}</Text>
      <Text style={[styles.sectionIntro, isTablet && styles.sectionIntroTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.sections.diseaseIndicationsBody')}</Text>
      <View style={[styles.vulnerabilityGrid, isTablet && styles.vulnerabilityGridTablet]}>
        {diseaseIndications.length ? diseaseIndications.map(renderFinding) : <View style={[...card, isTablet && styles.fullWidthCard]}><Text style={[styles.body, isTablet && styles.bodyTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.sections.noDiseaseIndications')}</Text></View>}
      </View>
    </ScrollView>
  );

  const renderTiming = () => {
    if (timingLoading) return <View style={[styles.center, isTablet && styles.centerTablet]}><ActivityIndicator size="large" color={colors.primary} /><Text style={[styles.centerText, isTablet && styles.centerTextTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.loading')}</Text></View>;
    if (timingError) return <View style={[styles.center, isTablet && styles.centerTablet]}><Text style={[styles.errorTitle, isTablet && styles.errorTitleTablet, { color: colors.text }]}>{t('healthBlueprint.timing.errorTitle')}</Text><Text style={[styles.centerText, isTablet && styles.centerTextTablet, { color: colors.textSecondary }]}>{timingError}</Text><TouchableOpacity style={[styles.retry, isTablet && styles.retryTablet, { backgroundColor: colors.primary }]} onPress={loadTiming}><Text style={[styles.retryText, isTablet && styles.retryTextTablet, { color: colors.onPrimary }]}>{t('healthBlueprint.actions.retry')}</Text></TouchableOpacity></View>;

    const groups = timingResult?.period_groups || [];
    const formatDate = (value, options = { dateStyle: 'medium' }) => new Intl.DateTimeFormat(undefined, options).format(new Date(`${value}T12:00:00`));
    const dateRange = (start, end) => start === end ? formatDate(start, { dateStyle: 'long' }) : t('healthBlueprint.timing.dateRange', { start: formatDate(start), end: formatDate(end) });
    const compactDateRange = (start, end) => {
      const startDate = new Date(`${start}T12:00:00`);
      const endDate = new Date(`${end}T12:00:00`);
      if (start === end) return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(startDate);
      if (startDate.getFullYear() === endDate.getFullYear() && startDate.getMonth() === endDate.getMonth()) {
        return `${new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(startDate)}–${new Intl.DateTimeFormat(undefined, { day: 'numeric' }).format(endDate)}`;
      }
      return `${new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(startDate)}–${new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(endDate)}`;
    };
    const chooseGroup = (group) => {
      setSelectedTimingDate(group);
      setSelectedTimingFinding(group?.windows?.[0] || null);
      setShowTimingTechnical(false);
    };
    const changeRange = (days) => {
      if (days === timingRangeDays) return;
      timingRequestRef.current += 1;
      activeTimingRequestKeyRef.current = null;
      setTimingRangeDays(days);
      setTimingResult(null);
      setSelectedTimingDate(null);
      setSelectedTimingFinding(null);
      setShowTimingTechnical(false);
    };

    const renderRangeSelector = () => <View style={[styles.rangeSelector, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
      {[90, 180, 365].map((days) => <TouchableOpacity key={`range-${days}`} onPress={() => changeRange(days)} style={[styles.rangeButton, timingRangeDays === days && { backgroundColor: colors.surfaceRaised, borderColor: colors.primary }]}><Text style={[styles.rangeButtonText, { color: timingRangeDays === days ? colors.primary : colors.textSecondary }]}>{t(`healthBlueprint.timing.ranges.${days}`)}</Text></TouchableOpacity>)}
    </View>;

    const renderTimeline = () => {
      if (!groups.length) return null;
      const rangeStart = new Date(`${timingResult.start_date}T12:00:00`);
      const rangeEnd = new Date(`${timingResult.end_date}T12:00:00`);
      const total = Math.max(1, rangeEnd - rangeStart);
      const monthLabels = [];
      const cursor = new Date(rangeStart.getFullYear(), rangeStart.getMonth(), 1, 12);
      while (cursor <= rangeEnd) {
        monthLabels.push({
          key: `${cursor.getFullYear()}-${cursor.getMonth()}`,
          label: new Intl.DateTimeFormat(undefined, { month: 'short' }).format(cursor),
          left: Math.max(0, Math.min(96, ((cursor - rangeStart) / total) * 100)),
        });
        cursor.setMonth(cursor.getMonth() + 1);
      }
      const labelStep = Math.max(1, Math.ceil(monthLabels.length / 6));
      return <View style={[styles.periodTimeline, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
        <Text style={[styles.factorLabel, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.timelineTitle')}</Text>
        <View style={styles.timelineMonths}>{monthLabels.filter((_, index) => index % labelStep === 0).map((month) => <Text key={month.key} style={[styles.timelineMonth, { left: `${month.left}%`, color: colors.textSecondary }]}>{month.label}</Text>)}</View>
        <View style={styles.timelineTracks}>{groups.map((group, index) => {
          const start = new Date(`${group.start_date}T12:00:00`);
          const end = new Date(`${group.end_date}T12:00:00`);
          const left = Math.max(0, ((start - rangeStart) / total) * 100);
          const width = Math.max(2.5, ((end - start + 86400000) / (total + 86400000)) * 100);
          const endPosition = Math.min(100, left + width);
          const labelPosition = Math.max(12, Math.min(88, left + (width / 2)));
          const selected = selectedTimingDate?.group_id === group.group_id;
          return <TouchableOpacity accessibilityLabel={dateRange(group.start_date, group.end_date)} accessibilityState={{ selected }} key={group.group_id} onPress={() => chooseGroup(group)} style={[styles.timelineTrack, { backgroundColor: colors.surfaceMuted, borderColor: selected ? colors.text : 'transparent' }]}>
            <View style={styles.timelineTrackHeader}><Text numberOfLines={1} style={[styles.timelineTrackLabel, { color: selected ? colors.text : colors.textSecondary }]}>{timingFindingTitle(group.windows[0].detail)}{group.finding_count > 1 ? ` · +${group.finding_count - 1}` : ''}</Text>{selected && <Ionicons name="checkmark-circle" size={16} color={colors.text} />}</View>
            <View style={styles.timelineRail}>
              <View style={[styles.timelineRailLine, { backgroundColor: colors.cardBorder }]} />
              <View style={[styles.timelineBar, { left: `${left}%`, width: `${Math.min(width, 100 - left)}%`, backgroundColor: colors.accent }]} />
              <View style={[styles.timelineDateMarker, { left: `${left}%`, backgroundColor: colors.text }]} />
              {group.start_date !== group.end_date && <View style={[styles.timelineDateMarker, { left: `${endPosition}%`, backgroundColor: colors.text }]} />}
              <Text numberOfLines={1} style={[styles.timelineDateLabel, { left: `${labelPosition}%`, color: colors.text, backgroundColor: colors.surfaceMuted }]}>{compactDateRange(group.start_date, group.end_date)}</Text>
            </View>
          </TouchableOpacity>;
        })}</View>
      </View>;
    };

    const renderPeriodList = () => <View style={styles.windowList}>
      {groups.map((group) => {
        const selected = selectedTimingDate?.group_id === group.group_id;
        const primary = group.windows[0];
        return <TouchableOpacity key={group.group_id} accessibilityState={{ selected }} onPress={() => chooseGroup(group)} style={[styles.windowCard, isTablet && styles.windowCardTabletList, { backgroundColor: selected ? colors.surfaceMuted : colors.surfaceRaised, borderColor: selected ? colors.text : colors.cardBorder }]}> 
          <View style={styles.row}><Text style={[styles.grade, { color: group.activation_level >= 3 ? colors.error : colors.primary }]}>{group.finding_count > 1 ? t('healthBlueprint.timing.overlappingPeriod') : t(`healthBlueprint.timing.windowPhases.${primary.phase}`)}</Text><Ionicons name="chevron-forward" size={18} color={colors.textSecondary} /></View>
          <Text style={[styles.windowDate, isTablet && styles.windowDateTablet, { color: colors.text }]}>{dateRange(group.start_date, group.end_date)}</Text>
          {group.windows.slice(0, 3).map((window) => <Text key={`${group.group_id}-${window.finding_id}`} style={[styles.windowFinding, isTablet && styles.windowFindingTablet, { color: colors.text }]}>{timingFindingTitle(window.detail)}</Text>)}
          {group.windows.length > 3 && <Text style={[styles.windowMarker, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.morePatterns', { count: group.windows.length - 3 })}</Text>}
        </TouchableOpacity>;
      })}
    </View>;

    const renderDetail = (group, selectedWindow, showBack) => {
      const detail = selectedWindow?.detail;
      if (!group || !detail) return <View style={[...card, styles.emptyDetail]}><Text style={[styles.body, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.selectPeriod')}</Text></View>;
      const conditionLink = detail.activation_summary?.condition_link || {};
      const conditionPlanets = (conditionLink.natal_planets || []).map(localizePlanet).join(', ');
      const conditionHouses = houseListText(conditionLink.natal_houses);
      const matchedDashas = (detail.dasha_chain || []).filter((row) => row.matched);
      const structuralContacts = (detail.transit_contacts || []).filter((contact) => !['Sun', 'Moon'].includes(contact.transit_planet));
      return <View>
        {showBack && <TouchableOpacity onPress={() => { setSelectedTimingDate(null); setSelectedTimingFinding(null); setShowTimingTechnical(false); }} style={styles.detailBack}><Ionicons name="arrow-back" size={20} color={colors.primary} /><Text style={[styles.detailBackText, { color: colors.primary }]}>{t('healthBlueprint.timing.allPeriods')}</Text></TouchableOpacity>}
        <View style={[...card, styles.timingDetailFocused]}>
          <Text style={[styles.grade, isTablet && styles.gradeTablet, { color: group.activation_level >= 3 ? colors.error : colors.primary }]}>{t(`healthBlueprint.timing.windowPhases.${selectedWindow.phase}`)}</Text>
          <Text style={[styles.itemTitle, isTablet && styles.itemTitleTablet, { color: colors.text }]}>{dateRange(selectedWindow.start_date, selectedWindow.end_date)}</Text>
          {group.windows.length > 1 && <View style={styles.findingSelector}>
            <Text style={[styles.factorLabel, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.concernsInPeriod')}</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.findingChips}>{group.windows.map((window) => {
              const active = selectedWindow.finding_id === window.finding_id;
              return <TouchableOpacity key={`finding-chip-${window.finding_id}`} onPress={() => { setSelectedTimingFinding(window); setShowTimingTechnical(false); }} style={[styles.findingChip, { backgroundColor: active ? colors.primary : colors.surfaceMuted, borderColor: active ? colors.primary : colors.cardBorder }]}><Text style={[styles.findingChipText, { color: active ? colors.onPrimary : colors.text }]}>{timingFindingTitle(window.detail)}</Text></TouchableOpacity>;
            })}</ScrollView>
          </View>}
          <Text style={[styles.factorLabel, styles.factorLabelSpaced, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.healthAreaFocus')}</Text>
          <Text style={[styles.timingFinding, isTablet && styles.timingFindingTablet, { color: colors.text }]}>{timingFindingTitle(detail)}</Text>

          <View style={[styles.conditionLink, { backgroundColor: colors.surfaceMuted, borderColor: colors.primary }]}> 
            <Text style={[styles.evidenceTitle, isTablet && styles.evidenceTitleTablet, { color: colors.text }]}>{t('healthBlueprint.timing.causalTitle')}</Text>
            <View style={styles.timingStep}>
              <Text style={[styles.timingStepLabel, { color: colors.primary }]}>{t('healthBlueprint.timing.natalStepLabel')}</Text>
              {isEnglish && conditionLink.natal_rules?.length > 0
                ? conditionLink.natal_rules.slice(0, 3).map((rule, index) => <Text key={`timing-natal-${index}`} style={[styles.timingStepText, isTablet && styles.bodyTablet, { color: colors.textSecondary }]}>• {rule}</Text>)
                : <Text style={[styles.timingStepText, isTablet && styles.bodyTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.natalStep', { condition: timingFindingTitle(detail), planets: conditionPlanets || '—', houses: conditionHouses || '—' })}</Text>}
            </View>
            <View style={[styles.timingStep, { borderTopColor: colors.cardBorder }]}>
              <Text style={[styles.timingStepLabel, { color: colors.primary }]}>{t('healthBlueprint.timing.dashaStepLabel')}</Text>
              {matchedDashas.map((row) => <Text key={`timing-main-dasha-${row.level}`} style={[styles.timingStepText, isTablet && styles.bodyTablet, { color: colors.textSecondary }]}>• {dashaExplanationText(row)}</Text>)}
            </View>
            <View style={[styles.timingStep, { borderTopColor: colors.cardBorder }]}>
              <Text style={[styles.timingStepLabel, { color: colors.primary }]}>{t('healthBlueprint.timing.transitStepLabel')}</Text>
              {structuralContacts.slice(0, 2).map((contact, index) => <Text key={`timing-main-transit-${index}`} style={[styles.timingStepText, isTablet && styles.bodyTablet, { color: colors.textSecondary }]}>• {transitContactText(contact)}</Text>)}
            </View>
            <Text style={[styles.causalConclusion, isTablet && styles.bodyTablet, { color: colors.text, borderTopColor: colors.cardBorder }]}>{t('healthBlueprint.timing.causalConclusion', { condition: timingFindingTitle(detail) })}</Text>
          </View>

          {(selectedWindow.sun_phases?.length > 0 || selectedWindow.moon_peak_dates?.length > 0) && <View style={styles.factorBlock}>
            <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.strongerWithinWindow')}</Text>
            {selectedWindow.sun_phases?.map((phase, index) => <Text key={`sun-phase-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {t('healthBlueprint.timing.sunPhase', { range: dateRange(phase.start_date, phase.end_date) })}</Text>)}
            {selectedWindow.moon_peak_dates?.map((value) => <Text key={`moon-peak-${value}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {t('healthBlueprint.timing.moonPeak', { date: formatDate(value, { dateStyle: 'long' }) })}</Text>)}
          </View>}

          <View style={styles.factorBlock}>
            <Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.houseByHouse')}</Text>
            {(detail.activation_summary?.houses || []).map((house) => <View key={`activated-house-${house.house}`} style={[styles.activatedHouseCard, { backgroundColor: colors.surfaceMuted, borderColor: house.confirmed_by_both ? colors.primary : colors.cardBorder }]}>
              <View style={styles.row}><Text style={[styles.activatedHouseTitle, { color: colors.text }]}>{t('healthBlueprint.timing.houseTitle', { house: house.house })}</Text>{house.confirmed_by_both && <Text style={[styles.confirmedBadge, { color: colors.primary }]}>{t('healthBlueprint.timing.confirmedByBoth')}</Text>}</View>
              {house.dasha_activators.length > 0 && <><Text style={[styles.houseSourceLabel, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.fromDasha')}</Text><Text style={[styles.houseSourceText, { color: colors.textSecondary }]}>{house.dasha_activators.map(dashaHouseActivatorText).join(' · ')}</Text></>}
              {house.transit_activators.length > 0 && <><Text style={[styles.houseSourceLabel, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.fromTransit')}</Text><Text style={[styles.houseSourceText, { color: colors.textSecondary }]}>{house.transit_activators.map(transitHouseActivatorText).join(' · ')}</Text></>}
              {isEnglish && house.natal_basis?.length > 0 && <Text style={[styles.houseBasis, { color: colors.textSecondary }]}>{house.natal_basis[0]}</Text>}
            </View>)}
          </View>
          {detail.protective_factors?.length > 0 && <View style={styles.factorBlock}><Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.primary }]}>{t('healthBlueprint.evidence.protectionLabel')}</Text>{detail.protective_factors.map((factor, index) => <Text key={`timing-protection-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {findingFactorText(factor)}</Text>)}</View>}
          <TouchableOpacity onPress={() => setShowTimingTechnical((value) => !value)} style={[styles.technicalToggle, { borderColor: colors.cardBorder }]}><Text style={[styles.technicalToggleText, { color: colors.primary }]}>{t(showTimingTechnical ? 'healthBlueprint.timing.hideTechnical' : 'healthBlueprint.timing.showTechnical')}</Text><Ionicons name={showTimingTechnical ? 'chevron-up' : 'chevron-down'} size={18} color={colors.primary} /></TouchableOpacity>
          {showTimingTechnical && <>
            <View style={styles.factorBlock}><Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.dashaChain')}</Text>{detail.dasha_chain.map((row) => <View key={`dasha-${row.level}`} style={styles.dashaRow}><View style={styles.grow}><Text style={[styles.dashaLevel, { color: colors.textSecondary }]}>{t(`healthBlueprint.timing.dashaLevels.${row.level}`)}{row.start && row.end ? ` · ${row.start} – ${row.end}` : ''}</Text>{row.matched && <Text style={[styles.dashaReason, { color: colors.textSecondary }]}>{dashaExplanationText(row)}</Text>}</View><Text style={[styles.dashaPlanet, { color: row.matched ? colors.primary : colors.textSecondary }]}>{localizePlanet(row.planet)}{row.matched ? ' ✓' : ''}</Text></View>)}</View>
            <View style={styles.factorBlock}><Text style={[styles.factorLabel, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.transitContacts')}</Text>{detail.transit_house_activations?.map((activation, index) => <Text key={`house-activation-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {transitHouseActivationText(activation)}</Text>)}{detail.transit_contacts?.length > 0 && <><Text style={[styles.factorLabel, styles.factorLabelSpaced, isTablet && styles.factorLabelTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.exactContactsTitle')}</Text>{detail.transit_contacts.map((contact, index) => <Text key={`contact-${index}`} style={[styles.evidenceRow, isTablet && styles.evidenceRowTablet, { color: colors.textSecondary }]}>• {transitContactText(contact)}</Text>)}</>}</View>
          </>}
          <Text style={[styles.note, isTablet && styles.noteTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.windowClaimNote')}</Text>
        </View>
      </View>;
    };

    if (!isTablet && selectedTimingDate) return <ScrollView style={styles.reportScroll} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>{renderDetail(selectedTimingDate, selectedTimingFinding || selectedTimingDate.windows?.[0], true)}</ScrollView>;

    return <ScrollView style={styles.reportScroll} contentContainerStyle={[styles.content, isTablet && styles.contentTablet]} showsVerticalScrollIndicator={false}>
      <View style={[styles.timingIntro, isTablet && styles.timingIntroTablet]}><Text style={[styles.timingTitle, isTablet && styles.timingTitleTablet, { color: colors.text }]}>{t('healthBlueprint.timing.title')}</Text><Text style={[styles.sectionIntro, isTablet && styles.sectionIntroTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.windowsBody')}</Text></View>
      {renderRangeSelector()}
      {renderTimeline()}
      {!groups.length ? <View style={[...card]}><Text style={[styles.body, isTablet && styles.bodyTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.timing.noWindows')}</Text></View> : isTablet ? <View style={styles.timingSplit}><View style={styles.timingMaster}>{renderPeriodList()}</View><View style={styles.timingDetailPane}>{renderDetail(selectedTimingDate, selectedTimingFinding || selectedTimingDate?.windows?.[0], false)}</View></View> : renderPeriodList()}
    </ScrollView>;
  };

  const tabNavigation = (
    <View style={[styles.tabs, isTablet && styles.tabsTablet, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
      {['profile', 'timing'].map((tab) => {
        const selected = activeTab === tab;
        return <TouchableOpacity key={tab} style={[styles.tab, isTablet && styles.tabTablet, selected && { backgroundColor: colors.surfaceRaised, borderColor: colors.primary }]} onPress={() => setActiveTab(tab)} accessibilityRole="tab" accessibilityState={{ selected }}><Ionicons name={tab === 'profile' ? 'body-outline' : 'time-outline'} size={isTablet ? 23 : 18} color={selected ? colors.primary : colors.textSecondary} /><Text style={[styles.tabText, isTablet && styles.tabTextTablet, { color: selected ? colors.primary : colors.textSecondary }]}>{t(`healthBlueprint.tabs.${tab}`)}</Text></TouchableOpacity>;
      })}
    </View>
  );

  return (
    <SafeAreaView style={[styles.screen, { backgroundColor: colors.background }]}>
      <View style={[styles.header, isTablet && styles.headerTablet, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cardBorder }]}>
        <TouchableOpacity style={[styles.headerButton, isTablet && styles.headerButtonTablet]} onPress={() => navigation.goBack()} accessibilityLabel={t('healthBlueprint.actions.back')}><Ionicons name="arrow-back" size={isTablet ? 28 : 22} color={colors.textInverse} /></TouchableOpacity>
        <View style={styles.headerCopy}>
          <Text style={[styles.headerTitle, isTablet && styles.headerTitleTablet, { color: colors.textInverse }]}>{t('healthBlueprint.headerTitle')}</Text>
          <NativeSelectorChip
            birthData={birthData}
            showIcon={false}
            onPress={selectNative}
            style={[
              styles.headerNativeChip,
              isTablet && styles.headerNativeChipTablet,
              { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine || colors.cardBorder },
            ]}
            textStyle={[styles.headerNativeChipText, isTablet && styles.headerNativeChipTextTablet, { color: colors.textInverse }]}
            iconColor={colors.accent}
          />
        </View>
        <TouchableOpacity style={[styles.headerButton, isTablet && styles.headerButtonTablet]} onPress={load} accessibilityLabel={t('healthBlueprint.actions.recalculate')}><Ionicons name="refresh" size={isTablet ? 26 : 20} color={colors.textInverse} /></TouchableOpacity>
      </View>
      {loading ? (
        <View style={[styles.center, isTablet && styles.centerTablet]}><ActivityIndicator size="large" color={colors.primary} /><Text style={[styles.centerText, isTablet && styles.centerTextTablet, { color: colors.textSecondary }]}>{t('healthBlueprint.loading')}</Text></View>
      ) : error ? (
        <View style={[styles.center, isTablet && styles.centerTablet]}><Text style={[styles.errorTitle, isTablet && styles.errorTitleTablet, { color: colors.text }]}>{t('healthBlueprint.errors.title')}</Text><Text style={[styles.centerText, isTablet && styles.centerTextTablet, { color: colors.textSecondary }]}>{error}</Text><TouchableOpacity style={[styles.retry, isTablet && styles.retryTablet, { backgroundColor: colors.primary }]} onPress={load}><Text style={[styles.retryText, isTablet && styles.retryTextTablet, { color: colors.onPrimary }]}>{t('healthBlueprint.actions.retry')}</Text></TouchableOpacity></View>
      ) : result ? (
        isTablet ? <View style={styles.tabletBody}>{tabNavigation}<View style={styles.tabletReport}>{activeTab === 'profile' ? renderProfile() : renderTiming()}</View></View> : <View style={styles.phoneBody}>{tabNavigation}{activeTab === 'profile' ? renderProfile() : renderTiming()}</View>
      ) : null}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 }, header: { minHeight: 76, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1, paddingHorizontal: 10 }, headerTablet: { minHeight: 98, paddingHorizontal: 24 }, headerButton: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' }, headerButtonTablet: { width: 58, height: 58 }, headerCopy: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 4 }, headerTitle: { fontSize: 17, fontWeight: '900' }, headerTitleTablet: { fontSize: 25 }, headerNativeChip: { minHeight: 28, paddingVertical: 2, paddingHorizontal: 11, borderRadius: 14, elevation: 0, shadowOpacity: 0, maxWidth: 190 }, headerNativeChipTablet: { minHeight: 34, paddingHorizontal: 15, borderRadius: 17, maxWidth: 280 }, headerNativeChipText: { fontSize: 11, fontWeight: '800' }, headerNativeChipTextTablet: { fontSize: 15 },
  phoneBody: { flex: 1 }, tabletBody: { flex: 1, flexDirection: 'row', width: '100%', maxWidth: 1360, alignSelf: 'center' }, tabletReport: { flex: 1 }, reportScroll: { flex: 1 },
  tabs: { flexDirection: 'row', margin: 12, padding: 4, borderWidth: 1, borderRadius: 16 }, tabsTablet: { width: 220, alignSelf: 'stretch', flexDirection: 'column', margin: 24, marginRight: 0, padding: 8, borderRadius: 20, gap: 8 }, tab: { flex: 1, minHeight: 43, borderWidth: 1, borderColor: 'transparent', borderRadius: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, paddingHorizontal: 10 }, tabTablet: { flex: 0, minHeight: 58, justifyContent: 'flex-start', paddingHorizontal: 16 }, tabText: { fontSize: 12, fontWeight: '900' }, tabTextTablet: { fontSize: 16 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 28, gap: 12 }, centerTablet: { padding: 48, gap: 18 }, centerText: { textAlign: 'center', fontSize: 13, lineHeight: 19 }, centerTextTablet: { maxWidth: 680, fontSize: 18, lineHeight: 27 }, errorTitle: { fontFamily: 'Georgia', fontSize: 24, fontWeight: '700' }, errorTitleTablet: { fontSize: 36, lineHeight: 44 }, retry: { paddingHorizontal: 20, paddingVertical: 11, borderRadius: 22 }, retryTablet: { paddingHorizontal: 28, paddingVertical: 15, borderRadius: 28 }, retryText: { fontWeight: '900' }, retryTextTablet: { fontSize: 16 },
  content: { padding: 14, paddingBottom: 48 }, contentTablet: { width: '100%', maxWidth: 1080, alignSelf: 'center', paddingHorizontal: 30, paddingTop: 24, paddingBottom: 72 }, hero: { borderWidth: 1, borderRadius: 22, padding: 22, marginBottom: 12 }, heroTablet: { borderRadius: 28, padding: 32, marginBottom: 18 }, eyebrow: { fontSize: 10, fontWeight: '900', letterSpacing: 1 }, eyebrowTablet: { fontSize: 13, letterSpacing: 1.3 }, heroTitle: { fontFamily: 'Georgia', fontSize: 29, fontWeight: '700', marginVertical: 7 }, heroTitleTablet: { fontSize: 42, lineHeight: 50, marginVertical: 10 }, heroBody: { fontSize: 13, lineHeight: 19 }, heroBodyTablet: { maxWidth: 850, fontSize: 18, lineHeight: 27 },
  card: { borderWidth: 1, borderRadius: 18, padding: 16, marginBottom: 11 }, cardTablet: { borderRadius: 22, padding: 24, marginBottom: 0 }, constitutionSummaryCard: { width: '100%', marginBottom: 12 }, constitutionSummaryCardTablet: { marginBottom: 16 }, constitutionAnchorGrid: { gap: 12, marginBottom: 12 }, constitutionAnchorGridTablet: { flexDirection: 'row', flexWrap: 'wrap', gap: 16, marginBottom: 16 }, constitutionAnchorCard: { marginBottom: 0 }, constitutionAnchorCardTablet: { flexBasis: '47%', flexGrow: 1, maxWidth: '49%' }, roleReasonBlock: { borderWidth: 1, borderRadius: 12, padding: 10, marginBottom: 11 }, roleReason: { fontSize: 11, lineHeight: 17, marginTop: 5 }, roleReasonTablet: { fontSize: 14, lineHeight: 22, marginTop: 7 }, anchorVerdict: { fontSize: 14, fontWeight: '900', marginBottom: 6 }, anchorVerdictTablet: { fontSize: 18, marginBottom: 9 }, factorBlock: { borderTopWidth: 1, marginTop: 12, paddingTop: 11 }, factorLabel: { fontSize: 9, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 0.5 }, factorLabelSpaced: { marginTop: 10 }, factorLabelTablet: { fontSize: 12, letterSpacing: 0.7 }, factorText: { fontSize: 11, lineHeight: 17, marginTop: 4 }, factorTextTablet: { fontSize: 14, lineHeight: 22, marginTop: 6 }, basisCard: { borderWidth: 1, borderRadius: 15, padding: 13, marginTop: 2, marginBottom: 12 }, basisTitle: { fontSize: 13, fontWeight: '900' }, basisTitleTablet: { fontSize: 17 }, basisSummary: { fontSize: 11, lineHeight: 16, marginTop: 3 }, basisSummaryTablet: { fontSize: 14, lineHeight: 21, marginTop: 5 }, sectionTitle: { fontFamily: 'Georgia', fontSize: 21, fontWeight: '700', marginVertical: 6 }, sectionTitleTablet: { fontSize: 28, lineHeight: 35, marginVertical: 10 }, subsectionTitle: { fontFamily: 'Georgia', fontSize: 20, fontWeight: '700', marginTop: 14, marginBottom: 8 }, subsectionTitleTablet: { fontSize: 27, marginTop: 22, marginBottom: 12 }, body: { fontSize: 13, lineHeight: 19 }, bodyTablet: { fontSize: 16, lineHeight: 25 }, note: { fontSize: 11, lineHeight: 16, marginTop: 7 }, noteTablet: { fontSize: 14, lineHeight: 22, marginTop: 10 }, listTitle: { fontFamily: 'Georgia', fontSize: 24, fontWeight: '700', marginTop: 22, marginBottom: 10 }, listTitleTablet: { fontSize: 32, lineHeight: 40, marginTop: 30, marginBottom: 14 }, sectionIntro: { fontSize: 12, lineHeight: 18, marginBottom: 12 }, sectionIntroTablet: { fontSize: 16, lineHeight: 24, marginBottom: 18 },
  pillarGrid: {}, pillarGridTablet: { flexDirection: 'row', flexWrap: 'wrap', gap: 16 }, pillarCard: {}, pillarCardTablet: { flexBasis: '47%', flexGrow: 1, maxWidth: '49%' }, jupiterProtectionCard: { marginTop: 12 }, jupiterProtectionCardTablet: { marginTop: 16 }, resilienceRow: { borderWidth: 1, borderRadius: 14, paddingHorizontal: 14, paddingVertical: 13, marginBottom: 12 }, resilienceValue: { fontSize: 18, fontWeight: '900', marginTop: 4 }, resilienceValueTablet: { fontSize: 23, marginTop: 7 }, resilienceExplanation: { fontSize: 11, lineHeight: 17, marginTop: 5 }, resilienceExplanationTablet: { fontSize: 15, lineHeight: 23, marginTop: 7 }, summaryGrid: { gap: 8, marginBottom: 12 }, summaryGridTablet: { flexDirection: 'row', gap: 14, marginBottom: 18 }, summaryItem: { flex: 1, borderWidth: 1, borderRadius: 14, padding: 12 }, summaryValue: { fontSize: 11, lineHeight: 17, fontWeight: '700', marginTop: 5 }, summaryValueTablet: { fontSize: 14, lineHeight: 22, marginTop: 7 }, anchorGrid: { gap: 8, marginBottom: 12 }, anchorGridTablet: { flexDirection: 'row', flexWrap: 'wrap', gap: 14, marginBottom: 18 }, anchorItem: { flex: 1, minWidth: '30%', borderWidth: 1, borderRadius: 14, padding: 11 }, anchorExplanation: { fontSize: 10, lineHeight: 15, marginTop: 5 }, anchorExplanationTablet: { fontSize: 13, lineHeight: 20, marginTop: 7 }, anchorTechnical: { fontSize: 9, lineHeight: 14, marginTop: 7 }, anchorTechnicalTablet: { fontSize: 12, lineHeight: 18, marginTop: 9 }, planetGrid: { gap: 8, marginBottom: 12 }, planetGridTablet: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 }, planetRow: { borderWidth: 1, borderRadius: 14, padding: 13 }, planetRowTablet: { flexBasis: '31%', flexGrow: 1, padding: 17, borderRadius: 18 }, planetName: { fontSize: 15, fontWeight: '900' }, planetNameTablet: { fontSize: 19 }, planetMeta: { fontSize: 11, lineHeight: 16, marginTop: 4 }, planetMetaTablet: { fontSize: 14, lineHeight: 21, marginTop: 6 }, badgeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 5, marginTop: 7 }, badge: { borderWidth: 1, borderRadius: 10, paddingHorizontal: 7, paddingVertical: 3, fontSize: 9, fontWeight: '900' },
  vulnerabilityGrid: {}, vulnerabilityGridTablet: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'flex-start', gap: 16 }, vulnerabilityCardTablet: { flexBasis: '47%', flexGrow: 1, maxWidth: '49%' }, fullWidthCard: { width: '100%' }, row: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 }, grow: { flex: 1 }, grade: { fontSize: 9, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 0.5 }, gradeTablet: { fontSize: 11, lineHeight: 16, letterSpacing: 0.7 }, itemTitle: { fontSize: 18, fontWeight: '900', marginVertical: 4 }, itemTitleTablet: { fontSize: 23, lineHeight: 30, marginVertical: 7 }, focusRow: { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 6, borderWidth: 1, borderRadius: 11, paddingHorizontal: 10, paddingVertical: 8, marginTop: 11 }, focusRowTablet: { gap: 8, borderRadius: 14, paddingHorizontal: 13, paddingVertical: 11, marginTop: 14 }, focusLabel: { fontSize: 10, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 0.5 }, focusLabelTablet: { fontSize: 12, letterSpacing: 0.7 }, focusValue: { flexShrink: 1, fontSize: 12, fontWeight: '800' }, focusValueTablet: { fontSize: 15, lineHeight: 21 }, evidence: { borderTopWidth: 1, marginTop: 12, paddingTop: 12 }, evidenceTitle: { fontSize: 12, fontWeight: '900', marginBottom: 5 }, evidenceTitleTablet: { fontSize: 16, marginBottom: 8 }, evidenceRow: { fontSize: 11, lineHeight: 16, marginBottom: 3 }, evidenceRowTablet: { fontSize: 14, lineHeight: 22, marginBottom: 5 },
  timingCard: { borderWidth: 1, borderRadius: 22, padding: 24, alignItems: 'center' }, timingCardTablet: { borderRadius: 28, padding: 38, alignItems: 'flex-start' }, timingIcon: { width: 58, height: 58, borderRadius: 19, alignItems: 'center', justifyContent: 'center', marginBottom: 16 }, timingIconTablet: { width: 72, height: 72, borderRadius: 23, marginBottom: 22 }, timingIntro: { marginBottom: 4 }, timingIntroTablet: { marginBottom: 8 }, timingTitle: { fontFamily: 'Georgia', fontSize: 25, fontWeight: '700', textAlign: 'left' }, timingTitleTablet: { fontSize: 36, textAlign: 'left' }, timingBody: { fontSize: 13, lineHeight: 20, textAlign: 'center', marginTop: 9 }, timingBodyTablet: { fontSize: 18, lineHeight: 28, textAlign: 'left', maxWidth: 820 }, timingRule: { borderTopWidth: 1, marginTop: 22, paddingTop: 20, width: '100%', alignItems: 'center' }, timingRuleTitle: { fontSize: 16, fontWeight: '900', textAlign: 'center' }, timingRuleTitleTablet: { fontSize: 22, textAlign: 'left' },
  windowList: { gap: 10 }, windowListTablet: { flexDirection: 'row', flexWrap: 'wrap', gap: 14 }, windowCard: { borderWidth: 1, borderRadius: 16, padding: 15 }, windowCardTablet: { flexBasis: '47%', flexGrow: 1, maxWidth: '49%', padding: 20 }, windowDate: { fontSize: 17, lineHeight: 23, fontWeight: '900', marginTop: 3 }, windowDateTablet: { fontSize: 22, lineHeight: 29 }, windowFinding: { fontSize: 14, lineHeight: 20, fontWeight: '700', marginTop: 7 }, windowFindingTablet: { fontSize: 18, lineHeight: 26 }, windowMarkers: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginTop: 9 }, windowMarker: { fontSize: 10, fontWeight: '700' }, timingDetail: { marginTop: 14 }, timingDetailTablet: { marginTop: 18 }, timingFinding: { fontSize: 16, fontWeight: '900', marginBottom: 7 }, timingFindingTablet: { fontSize: 21, marginBottom: 10 }, conditionLink: { borderWidth: 1, borderRadius: 14, padding: 13, marginTop: 14 }, conditionNatalRules: { marginTop: 8 }, timingStep: { borderTopWidth: 1, borderTopColor: 'transparent', paddingTop: 10, marginTop: 8 }, timingStepLabel: { fontSize: 9, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 0.5 }, timingStepText: { fontSize: 12, lineHeight: 18, marginTop: 3 }, causalConclusion: { borderTopWidth: 1, fontSize: 13, lineHeight: 20, fontWeight: '800', paddingTop: 11, marginTop: 11 }, timingConclusion: { borderWidth: 1, borderRadius: 14, padding: 13, marginTop: 14 }, activationAtGlance: { marginTop: 12, gap: 7 }, activationSummaryRow: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }, activationSummaryLabel: { fontSize: 10, fontWeight: '800' }, activationSummaryValue: { flex: 1, fontSize: 11, fontWeight: '900', textAlign: 'right' }, activatedHouseCard: { borderWidth: 1, borderRadius: 12, padding: 11, marginTop: 9 }, activatedHouseTitle: { fontSize: 14, fontWeight: '900' }, confirmedBadge: { marginLeft: 'auto', fontSize: 9, fontWeight: '900', textTransform: 'uppercase' }, houseSourceLabel: { fontSize: 9, fontWeight: '900', textTransform: 'uppercase', marginTop: 8 }, houseSourceText: { fontSize: 11, lineHeight: 17, marginTop: 2 }, houseBasis: { fontSize: 10, lineHeight: 15, fontStyle: 'italic', marginTop: 8 }, technicalToggle: { minHeight: 44, borderWidth: 1, borderRadius: 12, paddingHorizontal: 13, marginTop: 15, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }, technicalToggleText: { fontSize: 12, fontWeight: '900' }, dashaRow: { flexDirection: 'row', justifyContent: 'space-between', gap: 12, marginTop: 8 }, dashaLevel: { fontSize: 11 }, dashaPlanet: { fontSize: 11, fontWeight: '900' }, dashaReason: { fontSize: 9, lineHeight: 14, marginTop: 2 },
  rangeSelector: { flexDirection: 'row', borderWidth: 1, borderRadius: 14, padding: 3, marginBottom: 14 }, rangeButton: { flex: 1, minHeight: 38, borderWidth: 1, borderColor: 'transparent', borderRadius: 11, alignItems: 'center', justifyContent: 'center' }, rangeButtonText: { fontSize: 11, fontWeight: '900' }, periodTimeline: { borderWidth: 1, borderRadius: 16, padding: 14, marginBottom: 14 }, timelineMonths: { position: 'relative', height: 22, marginTop: 8 }, timelineMonth: { position: 'absolute', fontSize: 9, fontWeight: '800' }, timelineTracks: { gap: 7 }, timelineTrack: { minHeight: 64, borderWidth: 2, borderRadius: 9, paddingHorizontal: 8, paddingTop: 6, paddingBottom: 5 }, timelineTrackHeader: { minHeight: 18, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 }, timelineTrackLabel: { flex: 1, fontSize: 9, fontWeight: '800' }, timelineRail: { position: 'relative', height: 31, marginHorizontal: 2 }, timelineRailLine: { position: 'absolute', left: 0, right: 0, top: 20, height: 2, borderRadius: 1 }, timelineBar: { position: 'absolute', top: 17, height: 8, borderRadius: 4, opacity: 0.78 }, timelineDateMarker: { position: 'absolute', top: 14, width: 2, height: 15, marginLeft: -1, borderRadius: 1 }, timelineDateLabel: { position: 'absolute', top: 0, width: 100, marginLeft: -50, paddingHorizontal: 3, textAlign: 'center', fontSize: 9, lineHeight: 13, fontWeight: '900' }, timingSplit: { flexDirection: 'row', alignItems: 'flex-start', gap: 18 }, timingMaster: { width: '34%', minWidth: 250 }, timingDetailPane: { flex: 1 }, windowCardTabletList: { padding: 16 }, timingDetailFocused: { marginBottom: 0 }, emptyDetail: { minHeight: 240, alignItems: 'center', justifyContent: 'center' }, detailBack: { flexDirection: 'row', alignItems: 'center', gap: 8, minHeight: 44, marginBottom: 8 }, detailBackText: { fontSize: 13, fontWeight: '900' }, findingSelector: { marginTop: 13 }, findingChips: { gap: 8, paddingVertical: 8 }, findingChip: { borderWidth: 1, borderRadius: 18, paddingHorizontal: 12, paddingVertical: 8, maxWidth: 240 }, findingChipText: { fontSize: 11, fontWeight: '800' },
});
