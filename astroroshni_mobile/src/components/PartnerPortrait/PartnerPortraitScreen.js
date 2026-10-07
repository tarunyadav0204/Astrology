import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  Image,
  Linking,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  useWindowDimensions,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useFocusEffect } from '@react-navigation/native';
import { useTranslation } from 'react-i18next';

import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import { storage } from '../../services/storage';
import { partnerPortraitAPI } from '../../services/api';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import PartnerPortraitShareModal from './PartnerPortraitShareModal';
import { trackEvent } from '../../utils/analytics';

const SAMPLE_MALE = require('../../../assets/partner-portrait/sample-example.jpg');
const SAMPLE_FEMALE = require('../../../assets/partner-portrait/sample-woman-pair.jpg');
const showsFemaleSample = (gender) => !['female', 'woman', 'f', 'girl'].includes(String(gender || '').trim().toLowerCase());
const GENERATING_PREVIEW = require('../../../assets/partner-portrait/generating-preview.jpg');
const AGE_BANDS = ['25-34', '35-44', '45-54', '55+'];
const CLOTHING = [
  ['contemporary', 'contemporary'],
  ['traditional_regional', 'traditionalRegional'],
  ['modern_formal', 'modernFormal'],
];
const VISUAL_CONTEXTS = [
  ['south_asian', 'southAsian'],
  ['east_southeast_asian', 'eastSoutheastAsian'],
  ['middle_eastern_north_african', 'middleEasternNorthAfrican'],
  ['sub_saharan_african', 'subSaharanAfrican'],
  ['european', 'european'],
  ['latin_american', 'latinAmerican'],
  ['north_american', 'northAmerican'],
  ['central_asian', 'centralAsian'],
  ['oceania', 'oceania'],
  ['global_mixed', 'globalMixed'],
];
const PROGRESS_INDEX = {
  queued: 0,
  reading_chart: 0,
  creating_portrait: 1,
  creating_full_body: 2,
  ready: 2,
};
const PROGRESS_RANK = {
  queued: 0,
  reading_chart: 1,
  creating_portrait: 2,
  creating_full_body: 3,
  ready: 4,
  failed: 4,
};
const laterProgressStage = (current, incoming) => {
  if (!incoming || PROGRESS_RANK[incoming] == null) return current;
  if (!current || PROGRESS_RANK[current] == null) return incoming;
  return PROGRESS_RANK[incoming] >= PROGRESS_RANK[current] ? incoming : current;
};
const PLACEMENT_SIGN_CHANNELS = new Set([
  'd1_seventh_lord',
  'd9_seventh_lord',
  'd9_d1_seventh_lord',
  'darakaraka',
  'venus',
  'spouse_karaka',
]);
const traitKey = (value = '') => value.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
const exactChartTime = (value) => {
  const raw = String(value || '').trim();
  return (raw.includes('T') ? raw.split('T')[1] : raw).slice(0, 8);
};
const chartVersionKey = (chart = {}) => JSON.stringify({
  date: String(chart?.date || '').split('T')[0],
  time: exactChartTime(chart?.time),
  latitude: Number(Number(chart?.latitude).toFixed(6)),
  longitude: Number(Number(chart?.longitude).toFixed(6)),
  gender: String(chart?.gender || '').trim().toLowerCase(),
});

const ChoiceRow = ({ options, value, onChange, colors }) => (
  <View style={styles.choiceRow}>
    {options.map((option) => {
      const key = Array.isArray(option) ? option[0] : option;
      const label = Array.isArray(option) ? option[1] : option;
      const active = key === value;
      return (
        <TouchableOpacity
          key={key}
          onPress={() => onChange(key)}
          style={[
            styles.choice,
            { backgroundColor: active ? colors.primary : colors.surfaceRaised, borderColor: active ? colors.primary : colors.cardBorder },
          ]}
        >
          <Text style={[styles.choiceText, { color: active ? colors.onPrimary : colors.text }]}>{label}</Text>
        </TouchableOpacity>
      );
    })}
  </View>
);

export default function PartnerPortraitScreen({ navigation }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const { width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const { credits, pricing, fetchBalance, fetchPricing } = useCredits();
  const [birthData, setBirthData] = useState(null);
  const [direction, setDirection] = useState(null);
  const [directionLoading, setDirectionLoading] = useState(false);
  const [directionIssue, setDirectionIssue] = useState(null);
  const [ageBand, setAgeBand] = useState('25-34');
  const [clothingStyle, setClothingStyle] = useState('contemporary');
  const [status, setStatus] = useState('setup');
  const [result, setResult] = useState(null);
  const [creatingVariation, setCreatingVariation] = useState(false);
  const [error, setError] = useState(null);
  const [available, setAvailable] = useState(true);
  const [featureAccess, setFeatureAccess] = useState(null);
  const [configuredCost, setConfiguredCost] = useState(null);
  const [jobPhase, setJobPhase] = useState('queued');
  const [workingStartedAt, setWorkingStartedAt] = useState(null);
  const [lastCheckedAt, setLastCheckedAt] = useState(null);
  const [shareOpen, setShareOpen] = useState(false);
  const [selectedAssetKind, setSelectedAssetKind] = useState('portrait');
  const [whyExpanded, setWhyExpanded] = useState(false);
  const [sourcesExpanded, setSourcesExpanded] = useState(false);
  const [workingClock, setWorkingClock] = useState(Date.now());
  const pollRef = useRef(null);
  const activeJobIdRef = useRef(null);
  const selectedChartIdRef = useRef(0);
  const selectedChartVersionRef = useRef('');
  const previewPulse = useRef(new Animated.Value(0.08)).current;
  const wide = width >= 760;
  // The feature config and the generation route both resolve this value from
  // Admin > Credit Management, including any user subscription discount.
  // Shared pricing is useful across discovery cards, but this purchase screen
  // waits for the feature-specific value before enabling generation.
  const cost = configuredCost;
  const selectedChartId = Number(birthData?.birth_chart_id || birthData?.id || 0);

  const copy = useCallback(
    (key, fallback, values = {}) => t(`partnerPortrait.${key}`, { defaultValue: fallback, ...values }),
    [t],
  );
  const localPlanet = useCallback((name) => t(`home.planet_names.${name}`, { defaultValue: name }), [t]);
  const localSign = useCallback((name) => t(`signs.${name}`, { defaultValue: name }), [t]);

  const stopPolling = useCallback(() => {
    if (pollRef.current) clearTimeout(pollRef.current);
    pollRef.current = null;
  }, []);

  const loadDirection = useCallback(async (chartId) => {
    setDirectionLoading(true);
    setDirection(null);
    setDirectionIssue(null);
    try {
      const response = await partnerPortraitAPI.getDirection(chartId);
      if (selectedChartIdRef.current !== chartId) return;
      setDirection(response?.data || null);
      setError(null);
      setDirectionIssue(null);
    } catch (requestError) {
      if (selectedChartIdRef.current !== chartId) return;
      const detail = requestError?.response?.data?.detail;
      const code = typeof detail === 'object' ? detail?.code : null;
      const message = typeof detail === 'object' ? detail?.message : detail;
      setDirectionIssue(code || 'DIRECTION_UNAVAILABLE');
      setError(code === 'GENDER_REQUIRED' ? null : (message || copy('directionFailed', 'Gender or birth country could not be resolved from this chart.')));
    } finally {
      if (selectedChartIdRef.current === chartId) setDirectionLoading(false);
    }
  }, [copy]);

  const loadChart = useCallback(async () => {
    const selected = await storage.getBirthDetails();
    if (!selected?.id && !selected?.birth_chart_id) {
      navigation.replace('BirthProfileIntro', { returnTo: 'PartnerPortrait' });
      return;
    }
    const selectedId = Number(selected?.birth_chart_id || selected?.id || 0);
    const nextVersion = chartVersionKey(selected);
    if (selectedChartIdRef.current && selectedId && (
      selectedChartIdRef.current !== selectedId || selectedChartVersionRef.current !== nextVersion
    )) {
      stopPolling();
      activeJobIdRef.current = null;
      setResult(null);
      setCreatingVariation(false);
      setError(null);
      setDirection(null);
      setDirectionIssue(null);
      setStatus('setup');
    }
    selectedChartIdRef.current = selectedId;
    selectedChartVersionRef.current = nextVersion;
    setBirthData(selected);
    await loadDirection(selectedId);
  }, [loadDirection, navigation, stopPolling]);

  useFocusEffect(useCallback(() => {
    let cancelled = false;
    setFeatureAccess(null);
    setConfiguredCost(null);
    (async () => {
      const pricingResult = await fetchPricing({ force: true });
      if (cancelled) return;
      const enabled = Boolean(pricingResult?.features?.partner_portrait_enabled);
      setFeatureAccess(enabled);
      if (!enabled) {
        stopPolling();
        navigation.replace('Home', { resetToGreeting: true });
        return;
      }
      await loadChart();
      if (cancelled) return;
      try {
        const response = await partnerPortraitAPI.getConfig();
        if (cancelled) return;
        const nextCost = Number(response?.data?.cost);
        if (!Number.isFinite(nextCost) || nextCost < 1) throw new Error('Invalid Partner Portrait price');
        setConfiguredCost(nextCost);
        setAvailable(response?.data?.available !== false);
      } catch (_) {
        if (cancelled) return;
        setConfiguredCost(null);
        setAvailable(false);
      }
    })();
    return () => { cancelled = true; };
  }, [fetchPricing, loadChart, navigation, stopPolling]));

  useEffect(() => () => {
    activeJobIdRef.current = null;
    stopPolling();
  }, [stopPolling]);

  useEffect(() => {
    if (status !== 'working') return undefined;
    if (!workingStartedAt) setWorkingStartedAt(Date.now());
    setWorkingClock(Date.now());
    const timer = setInterval(() => setWorkingClock(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [status, workingStartedAt]);

  useEffect(() => {
    if (status !== 'working' || jobPhase !== 'reading_chart') return undefined;
    // Image generation continues outside the browser. Persist the same
    // five-second transition used by the API in component state so a PWA is
    // not left visually stuck if a status request is delayed or throttled.
    const timer = setTimeout(() => {
      setJobPhase((current) => laterProgressStage(current, 'creating_portrait'));
    }, 5000);
    return () => clearTimeout(timer);
  }, [jobPhase, status]);

  useEffect(() => {
    if (status !== 'working') {
      previewPulse.stopAnimation();
      previewPulse.setValue(0.08);
      return undefined;
    }
    const animation = Animated.loop(Animated.sequence([
      Animated.timing(previewPulse, { toValue: 0.28, duration: 1100, useNativeDriver: true }),
      Animated.timing(previewPulse, { toValue: 0.08, duration: 1100, useNativeDriver: true }),
    ]));
    animation.start();
    return () => animation.stop();
  }, [previewPulse, status]);

  const readStatus = useCallback(async (id) => {
    const response = await partnerPortraitAPI.getStatus(id);
    const payload = response?.data || {};
    setLastCheckedAt(Date.now());
    if (payload.chart_matches_current_version === false) {
      stopPolling();
      activeJobIdRef.current = null;
      setResult(null);
      setCreatingVariation(false);
      setStatus('setup');
      return;
    }
    if (payload.progress_stage || payload.status === 'processing') {
      // `processing` means the background worker has claimed the request.
      // Chart preparation is a short prerequisite inside that worker; do not
      // leave web clients displaying "Reading your chart" throughout image
      // generation when an older/coarse API response still uses that label.
      const reportedStage = payload.status === 'processing' && payload.progress_stage === 'reading_chart'
        ? 'creating_portrait'
        : (payload.progress_stage || 'creating_portrait');
      setJobPhase((current) => laterProgressStage(current, reportedStage));
    }
    if (payload.status === 'completed') {
      const completedActiveGeneration = activeJobIdRef.current === id;
      stopPolling();
      activeJobIdRef.current = null;
      setResult(payload.data);
      setCreatingVariation(false);
      setStatus('completed');
      if (completedActiveGeneration) {
        trackEvent('partner_portrait_generation_completed', { birth_chart_id: selectedChartIdRef.current });
      }
      await fetchBalance();
    } else if (payload.status === 'failed') {
      stopPolling();
      activeJobIdRef.current = null;
      setError(payload.credits_refunded
        ? `${copy('failed', 'We could not create the portrait.')} ${copy('refunded', 'Your credits were returned automatically.')}`
        : (payload.error || copy('failed', 'We could not create the portrait.')));
      setStatus('failed');
      await fetchBalance();
    } else if (payload.status === 'pending' || payload.status === 'processing') {
      setStatus('working');
    }
  }, [copy, fetchBalance, stopPolling]);

  const beginPolling = useCallback((id) => {
    activeJobIdRef.current = id;
    stopPolling();
    const poll = async () => {
      try {
        await readStatus(id);
      } catch (_) {
        // The job is server-side and continues if a PWA briefly loses its
        // network connection. The next poll will reconnect to the same job.
      } finally {
        if (activeJobIdRef.current === id) {
          pollRef.current = setTimeout(poll, 3000);
        }
      }
    };
    poll();
  }, [readStatus, stopPolling]);

  useEffect(() => {
    if (featureAccess !== true || !selectedChartId) return undefined;
    let cancelled = false;
    (async () => {
      try {
        const response = await partnerPortraitAPI.getHistory();
        if (cancelled) return;
        const chartItems = (response?.data?.items || []).filter((item) => (
          Number(item.birth_chart_id) === selectedChartId && item.matches_current_chart !== false
        ));
        const active = chartItems.find((item) => item.status === 'pending' || item.status === 'processing');
        const latestCompleted = chartItems.find((item) => item.status === 'completed');
        if (active) {
          // This effect may rerun as context callbacks change. Never reset a
          // live poll back to the history endpoint's coarse "processing"
          // state after /status has already supplied a more precise phase.
          if (activeJobIdRef.current !== active.job_id) {
            setJobPhase(active.status === 'pending' ? 'queued' : 'creating_portrait');
            setWorkingStartedAt(Date.now());
            setStatus('working');
            beginPolling(active.job_id);
          }
        } else if (latestCompleted && !result && !creatingVariation) {
          await readStatus(latestCompleted.job_id);
        }
      } catch (_) {
        // A missing history must not block a new purchase.
      }
    })();
    return () => { cancelled = true; };
  }, [beginPolling, creatingVariation, featureAccess, readStatus, result, selectedChartId]);

  const generate = async () => {
    if (!Number.isFinite(cost) || cost < 1) {
      setError(copy('priceUnavailable', 'The current credit price could not be loaded. Please try again.'));
      return;
    }
    if (!direction) {
      setError(copy('directionFailed', 'Gender or birth country could not be resolved from this chart.'));
      return;
    }
    if (!available) {
      setError(copy('unavailable', 'Partner Portrait is temporarily unavailable. Please try again later.'));
      return;
    }
    if (credits < cost) {
      trackEvent('partner_portrait_credit_blocked', { cost, credits });
      navigation.navigate('Credits', { requiredCredits: cost, feature: 'partner_portrait' });
      return;
    }
    try {
      setError(null);
      setJobPhase('queued');
      setWorkingStartedAt(Date.now());
      setLastCheckedAt(null);
      setStatus('working');
      trackEvent('partner_portrait_generation_started', { birth_chart_id: selectedChartId, cost });
      const chartId = selectedChartId;
      const idempotencyKey = `portrait-${chartId}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const response = await partnerPortraitAPI.generate({
        birth_chart_id: chartId,
        age_band: ageBand,
        clothing_style: clothingStyle,
        idempotency_key: idempotencyKey,
      });
      const id = response?.data?.job_id;
      if (!id) throw new Error('No generation job was returned');
      // Attach to the accepted background job immediately. On web, a slow
      // balance refresh must never delay or prevent progress polling; a page
      // refresh appeared to fix the UI only because history reattached it.
      beginPolling(id);
      fetchBalance();
    } catch (requestError) {
      if (requestError?.response?.status === 402) {
        setStatus('setup');
        navigation.navigate('Credits', { requiredCredits: cost, feature: 'partner_portrait' });
        return;
      }
      const detail = requestError?.response?.data?.detail;
      const code = typeof detail === 'object' ? detail?.code : null;
      const message = typeof detail === 'object' ? detail?.message : detail;
      if (code === 'GENDER_REQUIRED') {
        setDirection(null);
        setDirectionIssue(code);
        setError(null);
        setStatus('setup');
        return;
      }
      setError(message || requestError.message || copy('failed', 'We could not create the portrait.'));
      setStatus('failed');
    }
  };

  const card = { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder };
  const assets = result?.assets || [];
  const appearance = Object.entries(result?.profile?.appearance || {})
    .map(([attribute, entry]) => ({ ...(entry?.primary || {}), attribute }))
    .filter((entry) => entry?.confidence === 'strong' || entry?.confidence === 'moderate' || ['hair', 'head_hair', 'complexion'].includes(entry?.attribute));
  const personality = (result?.profile?.personality || []).filter((entry) => entry?.confidence !== 'suggestive');
  const factors = result?.profile?.chart_factors || {};
  const factorReadings = result?.profile?.factor_readings || [];
  const resolvedSummary = result?.profile?.resolved_summary || {};
  const portraitInference = result?.profile?.portrait_inference || [];
  const summaryAppearance = (resolvedSummary.appearance || appearance)
    .filter((entry) => entry?.confidence === 'strong' || entry?.confidence === 'moderate' || ['hair', 'head_hair', 'complexion'].includes(entry?.attribute));
  // v2 exposes one modern, resolved description for both this screen and the
  // image prompt. Classical phrases remain available in the evidence section.
  const portraitAppearance = portraitInference.length ? portraitInference : summaryAppearance;
  const summaryPersonality = (resolvedSummary.personality || personality).slice(0, 4);
  const dominantFactors = resolvedSummary.dominant_factors?.length
    ? resolvedSummary.dominant_factors
    : factorReadings
      .filter((reading) => !reading.withheld && ((reading.appearance || []).length || (reading.personality || []).length))
      .map((reading) => ({
        factor: reading.factor,
        factor_type: reading.factor_type,
        appearance: reading.appearance || [],
        personality: reading.personality || [],
      }))
      .slice(0, 3);
  const secondaryFactors = resolvedSummary.secondary_factors || [];
  const resolvedConflicts = resolvedSummary.conflicts_resolved || [];
  const artDirection = result?.profile?.art_direction || {};
  const elapsedSeconds = workingStartedAt ? Math.max(0, Math.floor((workingClock - workingStartedAt) / 1000)) : 0;
  const checkedSeconds = lastCheckedAt ? Math.max(0, Math.floor((workingClock - lastCheckedAt) / 1000)) : null;
  // Older/coarse API responses can expose only "processing" while image
  // generation is already underway. Chart synthesis is short; after five
  // seconds keep the honest long-running state on portrait generation. The
  // full-body step still advances only when the backend confirms it.
  const displayedJobPhase = jobPhase;
  const progressStep = PROGRESS_INDEX[displayedJobPhase] ?? 0;
  const progressStages = [
    {
      key: 'reading_chart',
      icon: 'sparkles-outline',
      title: copy('stageChart', 'Reading your chart'),
      body: copy('stageChartBody', 'Finding the partner traits that repeat across the chart.'),
    },
    {
      key: 'creating_portrait',
      icon: 'person-outline',
      title: copy('stagePortrait', 'Creating the face portrait'),
      body: copy('stagePortraitBody', 'Turning the strongest appearance indications into a natural portrait.'),
    },
    {
      key: 'creating_full_body',
      icon: 'body-outline',
      title: copy('stageBody', 'Matching the full-body view'),
      body: copy('stageBodyBody', 'Keeping the same face, hair and overall appearance in both images.'),
    },
  ];
  const currentProgress = displayedJobPhase === 'queued'
    ? {
      icon: 'hourglass-outline',
      title: copy('stageQueued', 'Preparing your request'),
      body: copy('stageQueuedBody', 'Your portrait job is secured and waiting for the image studio.'),
    }
    : progressStages[progressStep];
  const factorLines = [
    factors.d1_seventh_house && copy('d1SeventhHouse', 'D1 seventh house: {{sign}} · lord {{lord}}', { sign: localSign(factors.d1_seventh_house.sign), lord: localPlanet(factors.d1_seventh_house.lord) }),
    factors.d1_seventh_lord?.planet && copy('d1SeventhLord', 'D1 seventh lord {{planet}}: {{sign}} · House {{house}}', { ...factors.d1_seventh_lord, planet: localPlanet(factors.d1_seventh_lord.planet), sign: localSign(factors.d1_seventh_lord.sign) }),
    factors.d9_seventh_house && copy('d9SeventhHouse', 'D9 seventh house: {{sign}} · lord {{lord}}', { sign: localSign(factors.d9_seventh_house.sign), lord: localPlanet(factors.d9_seventh_house.lord) }),
    factors.d9_seventh_lord?.planet && copy('d9SeventhLord', 'D9 seventh lord {{planet}}: {{sign}} · House {{house}}', { ...factors.d9_seventh_lord, planet: localPlanet(factors.d9_seventh_lord.planet), sign: localSign(factors.d9_seventh_lord.sign) }),
    factors.darakaraka?.planet && copy('darakaraka', 'Darakaraka: {{planet}} in {{sign}}', { planet: localPlanet(factors.darakaraka.planet), sign: localSign(factors.darakaraka.sign) }),
  ].filter(Boolean);

  const factorName = (reading) => reading.factor_type === 'sign'
    ? localSign(reading.factor)
    : localPlanet(reading.factor);
  const factorHeading = (reading) => {
    const channel = copy(`channels.${reading.channel}`, reading.channel);
    const factor = factorName(reading);
    if (reading.factor_type === 'sign' && PLACEMENT_SIGN_CHANNELS.has(reading.channel)) {
      return copy('factorInSign', '{{channel}} in {{sign}}', { channel, sign: factor });
    }
    return `${channel} · ${factor}`;
  };
  const localizedTrait = (value) => copy(`traits.${traitKey(value)}`, value);
  const shareTraits = [
    ...portraitAppearance.slice(0, 2).map((item) => item.description || localizedTrait(item.value)),
    ...personality.slice(0, 2).map((item) => localizedTrait(item.trait)),
  ].filter((value, index, values) => value && values.indexOf(value) === index).slice(0, 3);
  const portraitAsset = assets.find((asset) => asset.kind === 'portrait') || assets[0];
  const selectedAsset = assets.find((asset) => asset.kind === selectedAssetKind) || portraitAsset;

  const summaryTrait = (item) => {
    const value = item.description || localizedTrait(item.value || item.trait);
    if (['hair', 'head_hair'].includes(item.attribute)) return copy('hairLabel', 'Hair: {{value}}', { value });
    if (item.attribute === 'body_hair') return copy('bodyHairLabel', 'Body hair: {{value}}', { value });
    if (item.attribute === 'complexion') return copy('complexionLabel', 'Complexion: {{value}}', { value });
    return value;
  };

  const factorContribution = (factor) => {
    const values = [
      ...(factor.appearance || []).map((item) => localizedTrait(item.value)),
      ...(factor.personality || []).map(localizedTrait),
    ].filter((value, index, list) => value && list.indexOf(value) === index);
    return values.slice(0, 4).join(' · ');
  };

  if (featureAccess !== true) {
    return (
      <SafeAreaView style={[styles.screen, styles.accessLoading, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </SafeAreaView>
    );
  }

  return (
    <View style={[styles.screen, { backgroundColor: colors.background }]}>
      <SafeAreaView edges={['top', 'left', 'right']} style={{ backgroundColor: colors.headerSurface }}>
        <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cardBorder }]}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerButton}>
            <Ionicons name="arrow-back" size={23} color={colors.textInverse} />
          </TouchableOpacity>
          <View style={styles.headerCenter}>
            <Text style={[styles.headerTitle, { color: colors.textInverse }]}>{copy('title', 'Partner Portrait')}</Text>
            <NativeSelectorChip
              birthData={birthData}
              onPress={() => navigation.navigate('SelectNative', { returnTo: 'PartnerPortrait' })}
              showIcon={false}
              style={styles.nativeChip}
              textStyle={{ color: colors.textInverseMuted }}
            />
          </View>
          <TouchableOpacity onPress={() => navigation.navigate('Credits')} style={styles.creditChip}>
            <Text style={[styles.creditText, { color: colors.textInverse }]}>✦ {credits}</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>

      <ScrollView
        style={{ backgroundColor: colors.background }}
        contentContainerStyle={[
          styles.content,
          wide && styles.contentWide,
          {
            paddingLeft: (wide ? 28 : 16) + insets.left,
            paddingRight: (wide ? 28 : 16) + insets.right,
            paddingBottom: Math.max(44, insets.bottom + 28),
          },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {status === 'completed' ? (
          <>
            <Text style={[styles.resultEyebrow, { color: colors.primary }]}>{copy('resultEyebrow', 'YOUR KUNDALI, BROUGHT TO LIFE')}</Text>
            <Text style={[styles.heroTitle, { color: colors.text }]}>{copy('resultHeroTitle', 'Meet the person your Kundali describes')}</Text>
            <Text style={[styles.scope, { color: colors.textSecondary }]}>{copy('symbolic', 'Inspired by your birth chart · not an exact photograph')}</Text>
            {artDirection.presentation && artDirection.visual_context ? (
              <Text style={[styles.selectionSummary, { color: colors.textSecondary }]}>
                {copy('createdAs', 'Created as {{gender}} · {{region}}', {
                  gender: copy(artDirection.presentation, artDirection.presentation),
                  region: copy(VISUAL_CONTEXTS.find(([value]) => value === artDirection.visual_context)?.[1] || 'globalMixed', artDirection.visual_context),
                })}
              </Text>
            ) : null}
            {assets.length > 1 ? (
              <View style={[styles.assetTabs, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
                {assets.map((asset) => {
                  const active = selectedAsset?.kind === asset.kind;
                  return (
                    <TouchableOpacity
                      key={asset.kind}
                      onPress={() => setSelectedAssetKind(asset.kind)}
                      style={[styles.assetTab, active && { backgroundColor: colors.primary }]}
                    >
                      <Ionicons name={asset.kind === 'portrait' ? 'person-outline' : 'body-outline'} size={17} color={active ? colors.onPrimary : colors.textSecondary} />
                      <Text style={[styles.assetTabText, { color: active ? colors.onPrimary : colors.textSecondary }]}>
                        {asset.kind === 'portrait' ? copy('portrait', 'Face portrait') : copy('fullBody', 'Full-body view')}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            ) : null}
            <View style={[styles.resultHeroCard, card]}>
              <View style={[styles.resultHeroFrame, selectedAsset?.kind === 'full_body' ? styles.resultFullBody : styles.resultPortrait]}>
                <Image source={{ uri: selectedAsset?.url }} style={styles.resultImage} resizeMode="contain" />
              </View>
            </View>
            <Text style={[styles.artNote, { color: colors.textSecondary }]}>
              {copy('artNote', 'The listed traits come from the chart. Partner gender follows the saved chart, regional appearance follows the birth location, and unspecified visual details are artistic choices.')}
            </Text>
            {portraitAsset?.url ? (
              <TouchableOpacity
                style={[styles.shareCta, { backgroundColor: colors.primary }]}
                onPress={() => {
                  trackEvent('partner_portrait_share_opened', { source: 'result' });
                  setShareOpen(true);
                }}
              >
                <Ionicons name="share-social-outline" size={19} color={colors.onPrimary} />
                <View style={styles.shareCtaCopy}>
                  <Text style={[styles.shareCtaTitle, { color: colors.onPrimary }]}>{copy('shareResultCta', 'Share my Partner Portrait')}</Text>
                  <Text style={[styles.shareCtaBody, { color: colors.onPrimary }]}>{copy('shareResultBody', 'Create a private, branded Story or post—without birth details.')}</Text>
                </View>
                <Ionicons name="arrow-forward" size={18} color={colors.onPrimary} />
              </TouchableOpacity>
            ) : null}
            <View style={[styles.glanceCard, { backgroundColor: colors.surfaceInverse, borderColor: colors.cardBorder }]}>
              <Text style={[styles.glanceEyebrow, { color: colors.accent }]}>{copy('atGlanceEyebrow', 'YOUR PARTNER AT A GLANCE')}</Text>
              <Text style={[styles.glanceTitle, { color: colors.onSurfaceInverse || colors.textInverse }]}>{copy('atGlanceTitle', 'The strongest qualities in your chart')}</Text>
              <View style={styles.glanceColumns}>
                <View style={styles.glanceColumn}>
                  <Text style={[styles.glanceLabel, { color: colors.onSurfaceInverseMuted || colors.textInverseMuted }]}>{copy('atGlanceAppearance', 'Appearance')}</Text>
                  {portraitAppearance.slice(0, 5).map((item, index) => (
                    <View key={`${item.attribute}-${item.value}-${index}`} style={styles.glanceTraitRow}>
                      <Ionicons name="sparkles" size={13} color={colors.accent} />
                      <Text style={[styles.glanceTrait, { color: colors.onSurfaceInverse || colors.textInverse }]}>{summaryTrait(item)}</Text>
                    </View>
                  ))}
                </View>
                <View style={styles.glanceColumn}>
                  <Text style={[styles.glanceLabel, { color: colors.onSurfaceInverseMuted || colors.textInverseMuted }]}>{copy('atGlancePersonality', 'Personality')}</Text>
                  {summaryPersonality.map((item, index) => (
                    <View key={`${item.trait}-${index}`} style={styles.glanceTraitRow}>
                      <Ionicons name="sparkles" size={13} color={colors.accent} />
                      <Text style={[styles.glanceTrait, { color: colors.onSurfaceInverse || colors.textInverse }]}>{localizedTrait(item.trait)}</Text>
                    </View>
                  ))}
                </View>
              </View>
            </View>

            <View style={[styles.card, card]}>
              <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{copy('resolvedEyebrow', 'HOW TARA SHAPED THE PORTRAIT')}</Text>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>{copy('resolvedTitle', 'One clear interpretation of the strongest indications')}</Text>
              <Text style={[styles.factorIntro, { color: colors.textSecondary }]}>{copy('resolvedIntro', 'Tara compared every indication, gave priority to repeated and stronger testimony, and used one resolved direction for each visible trait.')}</Text>
              {dominantFactors.map((factor, index) => (
                <View key={`${factor.factor}-${index}`} style={[styles.influenceRow, index > 0 && { borderTopColor: colors.cardBorder, borderTopWidth: 1 }]}>
                  <View style={[styles.influenceRank, { backgroundColor: colors.accentSoft || colors.background }]}>
                    <Text style={[styles.influenceRankText, { color: colors.onAccent || colors.primary }]}>{index + 1}</Text>
                  </View>
                  <View style={styles.influenceCopy}>
                    <Text style={[styles.influenceTitle, { color: colors.text }]}>{factorName(factor)}</Text>
                    <Text style={[styles.influenceBody, { color: colors.textSecondary }]}>{factorContribution(factor)}</Text>
                  </View>
                </View>
              ))}
              {secondaryFactors.length ? (
                <View style={[styles.supportingStrip, { backgroundColor: colors.background, borderColor: colors.cardBorder }]}>
                  <Text style={[styles.supportingLabel, { color: colors.textSecondary }]}>{copy('supportingInfluences', 'Supporting influences')}</Text>
                  <Text style={[styles.supportingValues, { color: colors.text }]}>{secondaryFactors.map(factorName).join(' · ')}</Text>
                </View>
              ) : null}
              {resolvedConflicts.slice(0, 2).map((resolution) => (
                <View key={resolution.attribute} style={[styles.resolutionNote, { borderLeftColor: colors.primary }]}>
                  <Text style={[styles.resolutionTitle, { color: colors.text }]}>{copy('conflictResolved', 'How a mixed indication was resolved')}</Text>
                  <Text style={[styles.resolutionBody, { color: colors.textSecondary }]}>{copy(
                    'conflictResolutionBody',
                    '{{selected}} had stronger or more repeated support than {{alternative}}, so it guided the portrait.',
                    { selected: localizedTrait(resolution.selected), alternative: localizedTrait(resolution.alternative) },
                  )}</Text>
                </View>
              ))}
            </View>

            <View style={[styles.card, card]}>
              <TouchableOpacity style={styles.accordionHeader} onPress={() => setWhyExpanded((value) => !value)}>
                <View style={styles.accordionTitleCopy}>
                  <Text style={[styles.sectionTitle, styles.accordionTitle, { color: colors.text }]}>{copy('why', 'Why your chart shows this')}</Text>
                  <Text style={[styles.accordionHint, { color: colors.textSecondary }]}>{copy('whyCollapsedHint', 'See which planets and signs shaped the portrait')}</Text>
                </View>
                <Ionicons name={whyExpanded ? 'chevron-up' : 'chevron-down'} size={22} color={colors.primary} />
              </TouchableOpacity>
              {whyExpanded ? <>
              <Text style={[styles.factorIntro, { color: colors.textSecondary }]}>
                {copy('whyIntro', 'Each factor below contributes specific qualities described in BPHS.')}
              </Text>
              {factorReadings.length ? factorReadings.map((reading, index) => {
                const appearanceContributions = (reading.appearance || []).map((item) => localizedTrait(item.value));
                const natureContributions = (reading.personality || []).map(localizedTrait);
                return (
                  <View
                    key={`${reading.channel}-${reading.factor}-${reading.verse}`}
                    style={[styles.factorReading, index > 0 && { borderTopColor: colors.cardBorder, borderTopWidth: 1 }]}
                  >
                    <Text style={[styles.factorHeading, { color: colors.text }]}>{factorHeading(reading)}</Text>
                    {reading.withheld ? (
                      <Text style={[styles.factorMeaning, { color: colors.textSecondary }]}>
                        {copy(
                          'withheldDebilitation',
                          'Debilitated, and Phaladeepika 7.26–30 does not cancel it, so this graha’s ordinary appearance is not used.',
                        )}
                      </Text>
                    ) : null}
                    {reading.condition_state === 'debilitated' && !reading.withheld ? (
                      <Text style={[styles.factorMeaning, { color: colors.textSecondary }]}>
                        {copy(
                          'weakenedDebilitation',
                          'Debilitated, so this graha remains relevant but its contribution is given less prominence.',
                        )}
                      </Text>
                    ) : null}
                    {reading.condition_state === 'debilitation_cancelled' ? (
                      <Text style={[styles.factorMeaning, { color: colors.textSecondary }]}>
                        {copy(
                          'cancelledDebilitation',
                          'A classical Neecha Bhanga condition is present ({{source}}), so the debilitation is mitigated, not reversed.',
                          { source: reading.neecha_bhanga_source || 'Phaladeepika 7.26-30' },
                        )}
                      </Text>
                    ) : null}
                    {appearanceContributions.length ? (
                      <Text style={[styles.factorMeaning, { color: colors.textSecondary }]}>
                        <Text style={[styles.factorLabel, { color: colors.text }]}>{copy('contributesAppearance', 'Appearance: ')}</Text>
                        {appearanceContributions.join(' · ')}
                      </Text>
                    ) : null}
                    {natureContributions.length ? (
                      <Text style={[styles.factorMeaning, { color: colors.textSecondary }]}>
                        <Text style={[styles.factorLabel, { color: colors.text }]}>{copy('contributesNature', 'Nature: ')}</Text>
                        {natureContributions.join(' · ')}
                      </Text>
                    ) : null}
                    <Text style={[styles.factorReference, { color: colors.primary }]}>
                      {copy('bphsReference', 'BPHS {{verse}}', { verse: reading.verse })}
                    </Text>
                  </View>
                );
              }) : factorLines.map((line) => (
                <Text key={line} style={[styles.bullet, { color: colors.textSecondary }]}>• {line}</Text>
              ))}
              </> : null}
            </View>
            <View style={[styles.card, card]}>
              <TouchableOpacity style={styles.accordionHeader} onPress={() => setSourcesExpanded((value) => !value)}>
                <View style={styles.accordionTitleCopy}>
                  <Text style={[styles.sectionTitle, styles.accordionTitle, { color: colors.text }]}>{copy('sources', 'Classical basis')}</Text>
                  <Text style={[styles.accordionHint, { color: colors.textSecondary }]}>{copy('sourcesCollapsedHint', 'Read the BPHS and Phaladeepika references')}</Text>
                </View>
                <Ionicons name={sourcesExpanded ? 'chevron-up' : 'chevron-down'} size={22} color={colors.primary} />
              </TouchableOpacity>
              {sourcesExpanded ? <>
              {(result?.profile?.references || []).map((source) => (
                <TouchableOpacity key={source.source_id} onPress={() => source.url && Linking.openURL(source.url)}>
                  <Text style={[styles.source, { color: colors.primary }]}>
                    {source.work} · {copy('chapterVerses', 'Chapter {{chapter}}, verses {{verses}}', source)} ↗
                  </Text>
                </TouchableOpacity>
              ))}
              <Text style={[styles.methodNote, { color: colors.textMuted || colors.textSecondary }]}>
                {copy('methodNote', 'Classical descriptions are ranked by spouse relevance and independent repetition. The ranking is AstroRoshni’s declared method; it is not presented as a verse from the classics.')}
              </Text>
              </> : null}
            </View>

            <View style={[styles.card, card]}>
              <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{copy('continueEyebrow', 'CONTINUE THE DISCOVERY')}</Text>
              <Text style={[styles.sectionTitle, { color: colors.text }]}>{copy('continueTitle', 'Go beyond the portrait')}</Text>
              <TouchableOpacity
                style={[styles.nextStepRow, { borderColor: colors.cardBorder }]}
                onPress={() => navigation.navigate('Home', {
                  startPartnership: true,
                  partnershipNativeChart: birthData,
                })}
              >
                <View style={[styles.nextStepIcon, { backgroundColor: colors.accentSoft || colors.background }]}><Ionicons name="people-circle-outline" size={22} color={colors.primary} /></View>
                <View style={styles.nextStepCopy}>
                  <Text style={[styles.nextStepTitle, { color: colors.text }]}>{copy('partnershipChatTitle', 'Analyse both charts with Tara')}</Text>
                  <Text style={[styles.nextStepBody, { color: colors.textSecondary }]}>{copy('partnershipChatBody', 'Choose the other person’s chart and ask about your compatibility, strengths, challenges and relationship.')}</Text>
                </View>
                <Ionicons name="arrow-forward" size={18} color={colors.primary} />
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.nextStepRow, { borderColor: colors.cardBorder }]}
                onPress={() => navigation.navigate('Home', {
                  startChat: true,
                  initialMessage: copy('askTaraQuestion', 'What does my birth chart say about my future partner’s personality and our relationship dynamic?'),
                })}
              >
                <View style={[styles.nextStepIcon, { backgroundColor: colors.accentSoft || colors.background }]}><Ionicons name="chatbubbles-outline" size={21} color={colors.primary} /></View>
                <View style={styles.nextStepCopy}>
                  <Text style={[styles.nextStepTitle, { color: colors.text }]}>{copy('askTaraTitle', 'Ask Tara about your partner')}</Text>
                  <Text style={[styles.nextStepBody, { color: colors.textSecondary }]}>{copy('askTaraBody', 'Explore personality, relationship dynamics and the questions this portrait raises.')}</Text>
                </View>
                <Ionicons name="arrow-forward" size={18} color={colors.primary} />
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.nextStepRow, { borderColor: colors.cardBorder }]}
                onPress={() => navigation.navigate('AnalysisDetail', {
                  analysisType: 'marriage',
                  title: copy('marriageAnalysisTitle', 'Marriage and relationship analysis'),
                  cost: pricing?.marriage || 0,
                  returnTo: 'PartnerPortrait',
                })}
              >
                <View style={[styles.nextStepIcon, { backgroundColor: colors.accentSoft || colors.background }]}><Ionicons name="heart-outline" size={21} color={colors.primary} /></View>
                <View style={styles.nextStepCopy}>
                  <Text style={[styles.nextStepTitle, { color: colors.text }]}>{copy('marriageAnalysisTitle', 'Marriage and relationship analysis')}</Text>
                  <Text style={[styles.nextStepBody, { color: colors.textSecondary }]}>{copy('marriageAnalysisBody', 'Study your relationship promise, partner indications and important periods.')}</Text>
                </View>
                <Ionicons name="arrow-forward" size={18} color={colors.primary} />
              </TouchableOpacity>
              <TouchableOpacity style={[styles.nextStepRow, { borderColor: colors.cardBorder }]} onPress={() => navigation.navigate('RelationshipMatch')}>
                <View style={[styles.nextStepIcon, { backgroundColor: colors.accentSoft || colors.background }]}><Ionicons name="people-outline" size={21} color={colors.primary} /></View>
                <View style={styles.nextStepCopy}>
                  <Text style={[styles.nextStepTitle, { color: colors.text }]}>{copy('compatibilityTitle', 'Compare with someone you know')}</Text>
                  <Text style={[styles.nextStepBody, { color: colors.textSecondary }]}>{copy('compatibilityBody', 'When you have both birth charts, examine compatibility using the two real charts.')}</Text>
                </View>
                <Ionicons name="arrow-forward" size={18} color={colors.primary} />
              </TouchableOpacity>
            </View>
            <View style={[styles.variationCard, card]}>
              <View style={[styles.variationIcon, { backgroundColor: colors.background, borderColor: colors.cardBorder }]}>
                <Ionicons name="images-outline" size={22} color={colors.primary} />
              </View>
              <Text style={[styles.variationTitle, { color: colors.text }]}>
                {copy('anotherLookTitle', 'Want to explore another possible look?')}
              </Text>
              <Text style={[styles.variationBody, { color: colors.textSecondary }]}>
                {copy('anotherLookBody', 'The same chart indications can produce more than one visual interpretation. Create a different face and matching full-body portrait using the same astrological profile.')}
              </Text>
              <TouchableOpacity
                disabled={cost == null}
                style={[styles.secondaryCta, { borderColor: colors.primary, opacity: cost == null ? 0.55 : 1 }]}
                onPress={() => { setCreatingVariation(true); setError(null); setStatus('setup'); }}
              >
                <Text style={[styles.secondaryCtaText, { color: colors.primary }]}>
                  {cost == null
                    ? copy('loadingPrice', 'Loading current credit price…')
                    : copy('anotherLookCta', 'Create another look · {{cost}} credits', { cost })}
                </Text>
                <Ionicons name="arrow-forward" size={17} color={colors.primary} />
              </TouchableOpacity>
              <Text style={[styles.variationFootnote, { color: colors.textMuted || colors.textSecondary }]}>
                {copy('anotherLookFootnote', 'Your current portrait stays saved. You will review the options before credits are used.')}
              </Text>
            </View>
          </>
        ) : status === 'working' ? (
          <View style={[styles.workingCard, card]}>
            <View style={[styles.workingIcon, { backgroundColor: colors.background, borderColor: colors.cardBorder }]}>
              <ActivityIndicator size="large" color={colors.primary} />
            </View>
            <Text style={[styles.workingEyebrow, { color: colors.primary }]}>{copy('workingActive', 'CREATION IN PROGRESS')}</Text>
            <Text style={[styles.workingTitle, { color: colors.text }]}>{copy('working', 'Creating your Partner Portrait')}</Text>
            <View style={[styles.generatingPreview, { backgroundColor: colors.background, borderColor: colors.cardBorder }]}>
              <Image source={GENERATING_PREVIEW} style={styles.generatingPreviewImage} resizeMode="cover" />
              <Animated.View style={[styles.generatingPulse, { backgroundColor: colors.surfaceRaised, opacity: previewPulse }]} />
              <View style={styles.generatingPreviewContent}>
                <View style={styles.generatingPreviewBadge}>
                  <Ionicons name="sparkles" size={17} color="#F4D89B" />
                  <Text style={styles.generatingPreviewText}>{copy('takingShape', 'Your portrait is taking shape')}</Text>
                </View>
              </View>
            </View>
            <View style={[styles.currentStage, { backgroundColor: colors.background, borderColor: colors.cardBorder }]}>
              <Ionicons name={currentProgress.icon} size={24} color={colors.primary} />
              <View style={styles.currentStageCopy}>
                <Text style={[styles.currentStageTitle, { color: colors.text }]}>{currentProgress.title}</Text>
                <Text style={[styles.currentStageBody, { color: colors.textSecondary }]}>{currentProgress.body}</Text>
              </View>
            </View>
            <View style={styles.progressList}>
              {progressStages.map((stage, index) => {
                const complete = index < progressStep;
                const active = index === progressStep;
                return (
                  <View key={stage.key} style={styles.progressRow}>
                    <View style={[
                      styles.progressMarker,
                      {
                        backgroundColor: complete || active ? colors.primary : colors.background,
                        borderColor: complete || active ? colors.primary : colors.cardBorder,
                      },
                    ]}>
                      <Ionicons
                        name={complete ? 'checkmark' : active ? 'ellipsis-horizontal' : 'ellipse-outline'}
                        size={15}
                        color={complete || active ? colors.onPrimary : colors.textSecondary}
                      />
                    </View>
                    <Text style={[
                      styles.progressLabel,
                      { color: active ? colors.text : colors.textSecondary, fontWeight: active ? '800' : '600' },
                    ]}>{stage.title}</Text>
                    <Text style={[
                      styles.progressState,
                      { color: complete || active ? colors.primary : colors.textSecondary },
                    ]}>
                      {complete
                        ? copy('stageDone', 'Done')
                        : active
                          ? copy('stageInProgress', 'In progress')
                          : copy('stageNext', 'Next')}
                    </Text>
                  </View>
                );
              })}
            </View>
            <View style={[styles.liveStatus, { borderTopColor: colors.cardBorder }]}>
              <View style={[styles.liveDot, { backgroundColor: colors.primary }]} />
              <Text style={[styles.liveText, { color: colors.textSecondary }]}>
                {checkedSeconds === null
                  ? copy('connecting', 'Connecting to the portrait studio…')
                  : copy('checkedAgo', 'Job active · status checked {{seconds}}s ago', { seconds: checkedSeconds })}
              </Text>
            </View>
            <Text style={[styles.elapsedText, { color: colors.textSecondary }]}>
              {elapsedSeconds < 60
                ? copy('elapsedUnderMinute', 'Started less than a minute ago')
                : copy('elapsedMinutes', 'Creating for {{minutes}} min', { minutes: Math.floor(elapsedSeconds / 60) })}
            </Text>
            <Text style={[styles.centerText, { color: colors.textSecondary }]}>
              {elapsedSeconds >= 300
                ? copy('workingLonger', 'The image studio is taking a little longer, but the job is still active. You may leave this screen and return later.')
                : copy('workingBody', 'Detailed image creation can take a few minutes. You may leave this screen; the portrait will continue creating in the background.')}
            </Text>
          </View>
        ) : (
          <View style={wide ? styles.twoColumn : styles.sampleStack}>
            <View style={wide ? styles.column : undefined}>
              <Text style={[styles.resultEyebrow, { color: colors.primary }]}>{copy('resultEyebrow', 'YOUR KUNDALI, BROUGHT TO LIFE')}</Text>
              <Text style={[styles.heroTitle, { color: colors.text }]}>{copy('subtitle', 'See the partner your birth chart describes')}</Text>
              <Text style={[styles.sampleLead, { color: colors.textSecondary }]}>{copy('honestBody', 'A birth chart cannot reveal an exact face or identify a specific person. Your portrait brings the strongest repeated appearance traits in your chart to life.')}</Text>
              <View style={[styles.sampleHeroCard, card]}>
                <View style={[styles.sampleImageFrame, { aspectRatio: 2112 / 1402, backgroundColor: colors.backgroundSecondary || colors.background }]}>
                  <Image source={showsFemaleSample(birthData?.gender) ? SAMPLE_FEMALE : SAMPLE_MALE} style={styles.sampleImage} resizeMode="contain" />
                  <View style={styles.sampleWatermark}>
                    <Ionicons name="sparkles" size={13} color="#FFF8EB" />
                    <Text style={styles.sampleWatermarkText}>{copy('sampleWatermark', 'SAMPLE')}</Text>
                  </View>
                </View>
                <View style={styles.sampleCopy}>
                  <Text style={[styles.sectionTitle, { color: colors.text }]}>{copy('sampleTitle', 'Sample Partner Portrait')}</Text>
                  <Text style={[styles.body, { color: colors.textSecondary }]}>{copy('sampleBody', 'This fixed example shows the face and full-body views you receive. It is not calculated from your chart.')}</Text>
                </View>
              </View>

              <View style={[styles.card, card]}>
                <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{copy('includes', 'Your purchase includes')}</Text>
                <View style={styles.benefitGrid}>
                  {[
                    ['person-outline', 'includeFace'],
                    ['body-outline', 'includeBody'],
                    ['heart-outline', 'includeProfile'],
                    ['library-outline', 'includeSources'],
                  ].map(([icon, key]) => (
                    <View key={key} style={[styles.benefitTile, { backgroundColor: colors.background, borderColor: colors.cardBorder }]}>
                      <View style={[styles.benefitIcon, { backgroundColor: colors.accentSoft || colors.surfaceMuted }]}>
                        <Ionicons name={icon} size={20} color={colors.onAccent || colors.primary} />
                      </View>
                      <Text style={[styles.benefitText, { color: colors.text }]}>{copy(key, key)}</Text>
                    </View>
                  ))}
                </View>
              </View>

            </View>

            <View style={wide ? styles.column : undefined}>
              {creatingVariation && result ? (
                <View style={[styles.variationNotice, { backgroundColor: colors.surfaceRaised, borderColor: colors.primary }]}>
                  <View style={styles.variationNoticeTitleRow}>
                    <Ionicons name="images-outline" size={22} color={colors.primary} />
                    <Text style={[styles.variationNoticeTitle, { color: colors.text }]}>{copy('variationTitle', 'Create another possible look')}</Text>
                  </View>
                  <Text style={[styles.body, { color: colors.textSecondary }]}>
                    {copy('variationBody', 'This deliberately creates a different face from the same chart indications. The new result will become the portrait shown for this chart.')}
                  </Text>
                  <TouchableOpacity
                    style={[styles.keepPortraitButton, { borderColor: colors.cardBorder }]}
                    onPress={() => { setCreatingVariation(false); setError(null); setStatus('completed'); }}
                  >
                    <Ionicons name="arrow-back" size={17} color={colors.primary} />
                    <Text style={[styles.keepPortraitText, { color: colors.primary }]}>{copy('keepCurrent', 'Keep my current portrait')}</Text>
                  </TouchableOpacity>
                </View>
              ) : null}
              <View style={[styles.card, styles.setupCard, card]}>
                <Text style={[styles.sectionEyebrow, { color: colors.primary }]}>{copy('forChart', 'Reading for')} {birthData?.name || ''}</Text>
                <Text style={[styles.setupTitle, { color: colors.text }]}>{copy('derivedDirection', 'Determined from the birth chart')}</Text>
                {directionLoading ? <ActivityIndicator size="small" color={colors.primary} /> : direction ? (
                  <View style={[styles.directionBox, { backgroundColor: colors.background, borderColor: colors.cardBorder }]}>
                    <View style={styles.directionRow}>
                      <Text style={[styles.directionLabel, { color: colors.textSecondary }]}>{copy('partnerGender', 'Partner gender')}</Text>
                      <Text style={[styles.directionValue, { color: colors.text }]}>{copy(direction.presentation, direction.presentation)}</Text>
                    </View>
                    <View style={styles.directionRow}>
                      <Text style={[styles.directionLabel, { color: colors.textSecondary }]}>{copy('birthCountry', 'Birth country')}</Text>
                      <Text style={[styles.directionValue, { color: colors.text }]}>{direction.country_name}</Text>
                    </View>
                    <View style={styles.directionRow}>
                      <Text style={[styles.directionLabel, { color: colors.textSecondary }]}>{copy('regionalAppearance', 'Regional appearance')}</Text>
                      <Text style={[styles.directionValue, { color: colors.text }]}>{copy(VISUAL_CONTEXTS.find(([value]) => value === direction.visual_context)?.[1] || 'globalMixed', direction.visual_context)}</Text>
                    </View>
                  </View>
                ) : null}
                <Text style={[styles.fieldHelp, styles.derivedHelp, { color: colors.textSecondary }]}>
                  {copy('derivedHelp', 'Partner gender follows the saved chart gender. Regional appearance is selected from the birth coordinates.')}
                </Text>
                {directionIssue === 'GENDER_REQUIRED' ? (
                  <View style={[styles.missingFieldCard, { backgroundColor: colors.background, borderColor: colors.cardBorder }]}>
                    <View style={styles.missingFieldCopy}>
                      <Text style={[styles.missingFieldTitle, { color: colors.text }]}>{copy('genderRequiredTitle', 'Gender is missing from this chart')}</Text>
                      <Text style={[styles.fieldHelp, { color: colors.textSecondary }]}>{copy('genderRequiredBody', 'Add the native’s gender to determine the partner portrait correctly.')}</Text>
                    </View>
                    <TouchableOpacity
                      style={[styles.addFieldButton, { backgroundColor: colors.primary }]}
                      onPress={() => navigation.navigate('BirthForm', {
                        editProfile: { ...birthData, id: selectedChartId },
                        updateGender: true,
                        returnTo: 'PartnerPortrait',
                      })}
                    >
                      <Text style={[styles.addFieldButtonText, { color: colors.onPrimary }]}>{copy('addGender', 'Add gender')}</Text>
                    </TouchableOpacity>
                  </View>
                ) : null}
                <View style={[styles.setupDivider, { backgroundColor: colors.cardBorder }]} />
                <Text style={[styles.preferenceLabel, { color: colors.text }]}>{copy('age', 'Apparent age')}</Text>
                <ChoiceRow options={AGE_BANDS} value={ageBand} onChange={setAgeBand} colors={colors} />
                <Text style={[styles.preferenceLabel, { color: colors.text }]}>{copy('clothing', 'Clothing style')}</Text>
                <ChoiceRow options={CLOTHING.map(([value, key]) => [value, copy(key, key)])} value={clothingStyle} onChange={setClothingStyle} colors={colors} />
                {!available ? (
                  <Text style={[styles.error, { color: colors.error || '#b42318' }]}>
                    {copy('unavailable', 'Partner Portrait is temporarily unavailable. Please try again later.')}
                  </Text>
                ) : null}
                {error ? <Text style={[styles.error, { color: colors.error || '#b42318' }]}>{error}</Text> : null}
                <TouchableOpacity
                  disabled={!available || cost == null || directionLoading || !direction}
                  style={[styles.cta, styles.setupCta, { backgroundColor: colors.primary, opacity: available && cost != null && !directionLoading && direction ? 1 : 0.55 }]}
                  onPress={generate}
                >
                  <Text style={[styles.ctaText, { color: colors.onPrimary }]}>
                    {!available
                      ? copy('unavailableShort', 'Temporarily unavailable')
                      : cost == null
                      ? copy('loadingPrice', 'Loading current credit price…')
                      : directionLoading
                      ? copy('resolvingDirection', 'Checking birth chart details…')
                      : !direction
                      ? copy('directionUnavailable', 'Birth chart details required')
                      : credits >= cost
                      ? creatingVariation
                        ? copy('generateVariation', `Create another possible look · ${cost} credits`, { cost })
                        : copy('generate', `Create my Partner Portrait · ${cost} credits`, { cost })
                      : copy('needCredits', `Get ${Math.max(0, cost - credits)} more credits`, { count: Math.max(0, cost - credits) })}
                  </Text>
                  <Ionicons name="arrow-forward" size={20} color={colors.onPrimary} />
                </TouchableOpacity>
              </View>
              <View style={[styles.sampleMethodCard, { backgroundColor: colors.surfaceInverse, borderColor: colors.cardBorder }]}>
                <Text style={[styles.glanceEyebrow, { color: colors.accent }]}>{copy('methodTitle', 'How your portrait is created')}</Text>
                <Text style={[styles.sampleMethodTitle, { color: colors.onSurfaceInverse || colors.textInverse }]}>{copy('atGlanceTitle', 'The strongest qualities in your chart')}</Text>
                <Text style={[styles.sampleMethodBody, { color: colors.onSurfaceInverseMuted || colors.textInverseMuted }]}>{copy('methodBody', 'We compare several classical indicators of a partner’s appearance and personality. Only qualities that repeat across the chart guide the portrait.')}</Text>
              </View>
            </View>
          </View>
        )}
      </ScrollView>
      <PartnerPortraitShareModal
        visible={shareOpen}
        onClose={() => setShareOpen(false)}
        portraitUrl={portraitAsset?.url}
        traits={shareTraits}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  accessLoading: { alignItems: 'center', justifyContent: 'center' },
  header: { minHeight: 76, borderBottomWidth: 1, paddingHorizontal: 16, paddingVertical: 8, flexDirection: 'row', alignItems: 'center' },
  headerButton: { width: 44, height: 44, justifyContent: 'center', alignItems: 'center' },
  headerCenter: { flex: 1, alignItems: 'center' },
  headerTitle: { fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontSize: 22, fontWeight: '700' },
  nativeChip: { marginTop: 4, minHeight: 30, paddingVertical: 2, backgroundColor: 'rgba(255,255,255,.08)' },
  creditChip: { minWidth: 58, padding: 10, alignItems: 'center' },
  creditText: { fontWeight: '800' },
  content: { padding: 16, paddingBottom: 44, alignSelf: 'center', width: '100%', maxWidth: 1180 },
  contentWide: { padding: 28 },
  twoColumn: { flexDirection: 'row', gap: 20, alignItems: 'flex-start' },
  sampleStack: { gap: 16 },
  column: { flex: 1, minWidth: 0 },
  heroTitle: { fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontSize: 30, lineHeight: 38, fontWeight: '700', marginBottom: 8 },
  sampleLead: { fontSize: 15, lineHeight: 22, marginBottom: 16, maxWidth: 680 },
  resultEyebrow: { fontSize: 11, lineHeight: 16, fontWeight: '900', letterSpacing: 1.6, marginBottom: 7 },
  scope: { fontSize: 14, marginBottom: 18 },
  selectionSummary: { fontSize: 14, fontWeight: '700', marginTop: -10, marginBottom: 18 },
  artNote: { fontSize: 13, lineHeight: 20, marginTop: 12, marginBottom: 2 },
  shareCta: { minHeight: 66, borderRadius: 18, marginTop: 14, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', gap: 11 },
  shareCtaCopy: { flex: 1 },
  shareCtaTitle: { fontSize: 15, lineHeight: 20, fontWeight: '900' },
  shareCtaBody: { marginTop: 2, fontSize: 11, lineHeight: 15, opacity: 0.84 },
  assetTabs: { alignSelf: 'center', width: '100%', maxWidth: 720, minHeight: 48, borderWidth: 1, borderRadius: 16, padding: 4, flexDirection: 'row', gap: 4, marginBottom: 10 },
  assetTab: { flex: 1, minHeight: 40, borderRadius: 12, paddingHorizontal: 10, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  assetTabText: { fontSize: 13, lineHeight: 18, fontWeight: '800' },
  resultHeroCard: { width: '100%', maxWidth: 720, alignSelf: 'center', borderWidth: 1, borderRadius: 28, overflow: 'hidden' },
  resultHeroFrame: { width: '100%', overflow: 'hidden', backgroundColor: 'rgba(0,0,0,0.035)' },
  card: { borderWidth: 1, borderRadius: 22, padding: 20, marginTop: 16 },
  sampleCard: { width: '100%', maxWidth: '100%', alignSelf: 'stretch', borderWidth: 1, borderRadius: 22, overflow: 'hidden', marginTop: 12 },
  sampleHeroCard: { width: '100%', maxWidth: '100%', alignSelf: 'stretch', borderWidth: 1, borderRadius: 26, overflow: 'hidden' },
  sampleImageFrame: { width: '100%', maxWidth: '100%', overflow: 'hidden', position: 'relative' },
  sampleImage: { width: '100%', height: '100%', maxWidth: '100%' },
  sampleCopy: { padding: 18 },
  sampleWatermark: { position: 'absolute', top: 14, right: 14, minHeight: 31, borderRadius: 16, paddingHorizontal: 11, flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: 'rgba(45, 12, 28, 0.82)' },
  sampleWatermarkText: { color: '#FFF8EB', fontSize: 10, lineHeight: 15, fontWeight: '900', letterSpacing: 1.2 },
  benefitGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  benefitTile: { width: '48%', flexGrow: 1, minHeight: 112, borderWidth: 1, borderRadius: 17, padding: 14, justifyContent: 'space-between', gap: 12 },
  benefitIcon: { width: 38, height: 38, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  benefitText: { fontSize: 14, lineHeight: 19, fontWeight: '800' },
  sampleMethodCard: { borderWidth: 1, borderRadius: 24, padding: 22, marginTop: 16 },
  sampleMethodTitle: { fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontSize: 22, lineHeight: 29, fontWeight: '800', marginBottom: 9 },
  sampleMethodBody: { fontSize: 14, lineHeight: 22 },
  sectionTitle: { fontSize: 19, fontWeight: '800', lineHeight: 25, marginBottom: 8 },
  sectionEyebrow: { fontSize: 13, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 16 },
  glanceCard: { borderWidth: 1, borderRadius: 26, padding: 22, marginTop: 18 },
  glanceEyebrow: { fontSize: 11, lineHeight: 16, fontWeight: '900', letterSpacing: 1.5, marginBottom: 7 },
  glanceTitle: { fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontSize: 23, lineHeight: 30, fontWeight: '800', marginBottom: 20 },
  glanceColumns: { flexDirection: 'row', flexWrap: 'wrap', gap: 22 },
  glanceColumn: { flex: 1, minWidth: 240, gap: 9 },
  glanceLabel: { fontSize: 11, lineHeight: 16, fontWeight: '900', letterSpacing: 1.1, textTransform: 'uppercase', marginBottom: 2 },
  glanceTraitRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  glanceTrait: { flex: 1, fontSize: 15, lineHeight: 21, fontWeight: '700' },
  body: { fontSize: 15, lineHeight: 23 },
  divider: { height: 1, marginVertical: 18 },
  label: { fontSize: 14, fontWeight: '800', marginTop: 14, marginBottom: 9 },
  setupCard: { overflow: 'hidden' },
  setupTitle: { fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontSize: 23, lineHeight: 30, fontWeight: '800', marginTop: -7, marginBottom: 14 },
  derivedHelp: { marginTop: 13 },
  setupDivider: { height: 1, marginTop: 19, marginBottom: 2 },
  preferenceLabel: { fontSize: 14, lineHeight: 20, fontWeight: '900', marginTop: 16, marginBottom: 9 },
  setupCta: { marginTop: 22 },
  fieldHelp: { fontSize: 13, lineHeight: 19, marginTop: 12, marginBottom: 4 },
  directionBox: { borderWidth: 1, borderRadius: 15, paddingHorizontal: 14, paddingVertical: 8, gap: 2 },
  directionRow: { minHeight: 38, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  directionLabel: { flex: 1, fontSize: 13, lineHeight: 18 },
  directionValue: { flex: 1, fontSize: 14, lineHeight: 19, fontWeight: '800', textAlign: 'right' },
  missingFieldCard: { marginTop: 8, borderWidth: 1, borderRadius: 15, padding: 14, gap: 12 },
  missingFieldCopy: { gap: 4 },
  missingFieldTitle: { fontSize: 15, lineHeight: 21, fontWeight: '800' },
  addFieldButton: { minHeight: 42, borderRadius: 13, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 16 },
  addFieldButtonText: { fontSize: 14, fontWeight: '900' },
  choiceRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  choice: { minHeight: 42, borderWidth: 1, borderRadius: 14, paddingHorizontal: 13, paddingVertical: 10, justifyContent: 'center' },
  choiceText: { fontSize: 13, fontWeight: '700' },
  bullet: { fontSize: 15, lineHeight: 25 },
  traitRow: { marginBottom: 10 },
  traitValue: { fontSize: 15, lineHeight: 22, fontWeight: '700' },
  traitEvidence: { fontSize: 12, lineHeight: 18, marginLeft: 14, marginTop: 2 },
  factorIntro: { fontSize: 14, lineHeight: 21, marginBottom: 5 },
  factorReading: { paddingVertical: 14 },
  factorHeading: { fontSize: 15, lineHeight: 21, fontWeight: '800', marginBottom: 5 },
  factorMeaning: { fontSize: 14, lineHeight: 21, marginTop: 2 },
  factorLabel: { fontWeight: '800' },
  factorReference: { fontSize: 12, lineHeight: 18, fontWeight: '700', marginTop: 6 },
  influenceRow: { minHeight: 72, paddingVertical: 13, flexDirection: 'row', alignItems: 'center', gap: 12 },
  influenceRank: { width: 34, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
  influenceRankText: { fontSize: 13, fontWeight: '900' },
  influenceCopy: { flex: 1 },
  influenceTitle: { fontSize: 16, lineHeight: 22, fontWeight: '900' },
  influenceBody: { fontSize: 13, lineHeight: 19, marginTop: 2 },
  supportingStrip: { borderWidth: 1, borderRadius: 15, padding: 14, marginTop: 10 },
  supportingLabel: { fontSize: 11, lineHeight: 16, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.7 },
  supportingValues: { fontSize: 14, lineHeight: 20, fontWeight: '800', marginTop: 4 },
  resolutionNote: { borderLeftWidth: 3, paddingLeft: 13, marginTop: 17 },
  resolutionTitle: { fontSize: 14, lineHeight: 20, fontWeight: '900' },
  resolutionBody: { fontSize: 13, lineHeight: 20, marginTop: 3 },
  accordionHeader: { minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: 14 },
  accordionTitleCopy: { flex: 1 },
  accordionTitle: { marginBottom: 2 },
  accordionHint: { fontSize: 13, lineHeight: 18 },
  nextStepRow: { minHeight: 78, borderWidth: 1, borderRadius: 17, padding: 13, flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 10 },
  nextStepIcon: { width: 42, height: 42, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  nextStepCopy: { flex: 1 },
  nextStepTitle: { fontSize: 15, lineHeight: 21, fontWeight: '900' },
  nextStepBody: { fontSize: 12, lineHeight: 18, marginTop: 2 },
  cta: { minHeight: 58, borderRadius: 18, marginTop: 18, paddingHorizontal: 20, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9 },
  ctaText: { fontSize: 16, fontWeight: '900', textAlign: 'center' },
  secondaryCta: { minHeight: 52, borderWidth: 1.5, borderRadius: 17, marginTop: 16, paddingHorizontal: 15, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  secondaryCtaText: { fontSize: 15, fontWeight: '800' },
  variationCard: { borderWidth: 1, borderRadius: 22, marginTop: 18, padding: 20, alignItems: 'flex-start' },
  variationIcon: { width: 46, height: 46, borderRadius: 15, borderWidth: 1, alignItems: 'center', justifyContent: 'center', marginBottom: 13 },
  variationTitle: { fontSize: 19, lineHeight: 25, fontWeight: '900' },
  variationBody: { fontSize: 14, lineHeight: 21, marginTop: 7 },
  variationFootnote: { fontSize: 11, lineHeight: 17, marginTop: 9 },
  variationNotice: { borderWidth: 1.5, borderRadius: 20, padding: 18 },
  variationNoticeTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 9, marginBottom: 8 },
  variationNoticeTitle: { flex: 1, fontSize: 18, lineHeight: 24, fontWeight: '800' },
  keepPortraitButton: { alignSelf: 'flex-start', minHeight: 42, borderWidth: 1, borderRadius: 14, marginTop: 14, paddingHorizontal: 13, flexDirection: 'row', alignItems: 'center', gap: 7 },
  keepPortraitText: { fontSize: 14, fontWeight: '800' },
  workingCard: { width: '100%', maxWidth: 680, alignSelf: 'center', minHeight: 480, borderWidth: 1, borderRadius: 24, padding: 24, alignItems: 'center' },
  workingIcon: { width: 76, height: 76, borderRadius: 38, borderWidth: 1, alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
  workingEyebrow: { fontSize: 12, lineHeight: 17, fontWeight: '900', letterSpacing: 1.4, marginBottom: 6 },
  workingTitle: { fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontSize: 25, lineHeight: 32, fontWeight: '800', textAlign: 'center', marginBottom: 18 },
  generatingPreview: { width: '100%', height: 190, borderWidth: 1, borderRadius: 20, overflow: 'hidden', marginBottom: 16 },
  generatingPreviewImage: { ...StyleSheet.absoluteFillObject, width: '100%', height: '100%' },
  generatingPulse: { ...StyleSheet.absoluteFillObject },
  generatingPreviewContent: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center', padding: 16 },
  generatingPreviewBadge: { minHeight: 42, maxWidth: '90%', borderRadius: 22, paddingHorizontal: 15, paddingVertical: 10, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: 'rgba(42, 10, 27, .78)' },
  generatingPreviewText: { color: '#FFF8EB', fontSize: 14, lineHeight: 19, fontWeight: '800', textAlign: 'center' },
  currentStage: { width: '100%', borderWidth: 1, borderRadius: 18, padding: 16, flexDirection: 'row', alignItems: 'flex-start', gap: 13 },
  currentStageCopy: { flex: 1 },
  currentStageTitle: { fontSize: 17, lineHeight: 23, fontWeight: '800', marginBottom: 3 },
  currentStageBody: { fontSize: 14, lineHeight: 20 },
  progressList: { width: '100%', paddingVertical: 18, paddingHorizontal: 4, gap: 12 },
  progressRow: { flexDirection: 'row', alignItems: 'center', gap: 11 },
  progressMarker: { width: 27, height: 27, borderRadius: 14, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  progressLabel: { flex: 1, fontSize: 14, lineHeight: 20 },
  progressState: { fontSize: 10, lineHeight: 14, fontWeight: '900', textTransform: 'uppercase', letterSpacing: 0.45 },
  liveStatus: { width: '100%', borderTopWidth: 1, paddingTop: 15, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  liveDot: { width: 8, height: 8, borderRadius: 4 },
  liveText: { fontSize: 13, lineHeight: 18, fontWeight: '700' },
  elapsedText: { fontSize: 12, lineHeight: 17, marginTop: 5, marginBottom: 12 },
  centerText: { fontSize: 15, lineHeight: 23, textAlign: 'center', maxWidth: 540 },
  error: { fontSize: 14, lineHeight: 21, marginTop: 14, fontWeight: '600' },
  imageGrid: { width: '100%', maxWidth: '100%', gap: 14 },
  imageGridWide: { flexDirection: 'row', alignItems: 'flex-start' },
  resultImageCard: { flex: 1, minWidth: 0, maxWidth: '100%', borderWidth: 1, borderRadius: 22, overflow: 'hidden' },
  resultFrame: { width: '100%', overflow: 'hidden', backgroundColor: 'rgba(0,0,0,0.04)' },
  resultImage: { width: '100%', height: '100%' },
  resultPortrait: { aspectRatio: 4 / 5 },
  resultFullBody: { aspectRatio: 3 / 4 },
  resultCaption: { flexShrink: 0, minHeight: 58, justifyContent: 'center', paddingHorizontal: 16, paddingVertical: 14 },
  imageLabel: { fontSize: 16, lineHeight: 22, fontWeight: '800' },
  source: { fontSize: 14, lineHeight: 22, marginBottom: 6 },
  methodNote: { fontSize: 12, lineHeight: 19, marginTop: 12 },
});
