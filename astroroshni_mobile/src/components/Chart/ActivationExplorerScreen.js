import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  Platform,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { LinearGradient } from 'expo-linear-gradient';

import { useTheme } from '../../context/ThemeContext';
import { chartAPI } from '../../services/api';
import { storage } from '../../services/storage';

const HOUSE_LABELS = {
  1: 'Self, body and direction', 2: 'Savings, family, speech and face/mouth',
  3: 'Effort, skills and communication', 4: 'Home, property and mother',
  5: 'Children, learning and creativity', 6: 'Work, health and obligations',
  7: 'Partnership and agreements', 8: 'Change and shared resources',
  9: 'Father, guidance and fortune', 10: 'Career and public duty',
  11: 'Gains, networks and fulfilment', 12: 'Expense, retreat and release',
};

const STATE_LABELS = {
  fully_reinforced: 'Strongly active', dasha_transit_activated: 'Active now',
  dasha_connected: 'Period connected', transit_only: 'Background influence', dormant: 'Not active',
};
const STATE_EXPLANATIONS = {
  fully_reinforced: 'Your birth chart, current period and transits all point to this house',
  dasha_transit_activated: 'Your current period and transits both activate this house',
  dasha_connected: 'Your current period connects here, but there is no strong transit trigger yet',
  transit_only: 'A transit touches this house, but your current period does not strongly support an event',
  dormant: 'This house is not drawing significant attention now',
};
const OUTCOME_LABELS = {
  supportive: 'Constructive results are more likely', mixed: 'Both progress and pressure are possible',
  challenging: 'Pressure, delay or obstacles are more likely', neutral: 'The result direction is not yet clear',
};
const BAND_LABELS = {
  strong: 'Strong chart agreement', moderate: 'Moderate chart agreement',
  insufficient: 'Not enough chart support',
};
const STATE_ORDER = { fully_reinforced: 5, dasha_transit_activated: 4, dasha_connected: 3, transit_only: 2, dormant: 1 };
const OUTCOME_COLORS = { supportive: '#16a34a', mixed: '#f59e0b', challenging: '#dc2626', neutral: '#64748b' };
const SYNTHESIS_STRENGTH_LABELS = { high: 'Strong chart agreement', well_supported: 'Good chart agreement', moderate: 'Developing chart theme' };
const SYNTHESIS_STRENGTH_ORDER = { high: 0, well_supported: 1, moderate: 2 };
const subjectSectionLabel = (subject) => subject === 'self' ? 'For you' : `Your ${subject}`;

const localDate = (date = new Date()) => {
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 10);
};
const sentence = (value) => String(value || '—').replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
const reasonDescription = (reason) => {
  const facts = reason?.facts || {};
  const planet = reason?.planet || 'This factor';
  const targetHouse = facts.target_house || reason?.house;
  const placement = facts.placement_house ? `House ${facts.placement_house}` : 'its natal position';
  const dignity = sentence(facts.dignity || 'neutral').toLowerCase();
  const condition = `${dignity} dignity${facts.combustion && facts.combustion !== 'normal' ? ` and ${sentence(facts.combustion).toLowerCase()}` : ''}${facts.neecha_bhanga ? ', with debilitation cancellation' : ''}`;
  const naturalNature = String(facts.natural_nature || '').includes('benefic') ? 'natural benefic'
    : String(facts.natural_nature || '').includes('malefic') ? 'natural malefic'
      : String(facts.natural_nature || '').startsWith('waxing_moon') ? 'waxing Moon, treated as benefic'
        : String(facts.natural_nature || '').startsWith('waning_moon') ? 'waning Moon, treated as challenging'
          : String(facts.natural_nature || '').startsWith('associated_mercury') ? `Mercury conditioned as ${reason.polarity}`
            : 'natural neutral';
  const naturalResult = reason?.polarity === 'supportive'
    ? `supports the matters of House ${targetHouse}`
    : `adds pressure to the matters of House ${targetHouse}`;
  const ruledHouses = (facts.ruled_houses || []).map((house) => `House ${house}`).join(' and ');
  const naturalInfluence = planet === 'Mercury' && facts.malefic_associations?.length
    ? `Mercury is treated as challenging here because it is conjunct ${facts.malefic_associations.join(' and ')}, ${facts.malefic_associations.length === 1 ? 'a natural malefic' : 'natural malefics'}; this ${naturalResult}.`
    : planet === 'Mercury' && facts.benefic_associations?.length
      ? `Mercury is treated as supportive here because it is conjunct ${facts.benefic_associations.join(' and ')}, ${facts.benefic_associations.length === 1 ? 'a natural benefic' : 'natural benefics'}; this ${naturalResult}.`
      : `${planet} is ${['natural benefic', 'natural malefic', 'natural neutral'].includes(naturalNature) ? 'a ' : ''}${naturalNature}; this ${naturalResult}.`;
  const reversalHouses = (facts.reversal_houses || []).map((house) => `House ${house}`).join(' and ');
  const effectiveChallengeHouses = (facts.effective_challenging_houses || []).map((house) => `House ${house}`).join(' and ');
  const functionalReason = facts.reversal_houses?.length
    ? `${planet} rules ${ruledHouses}. Because ${planet} occupies a dusthana, its ${reversalHouses} lordship is evaluated through the separate reversal rule; ${effectiveChallengeHouses ? `${effectiveChallengeHouses} remains a direct pressure-bearing lordship` : 'no other challenging lordship remains'} for House ${targetHouse}.`
    : facts.yogakaraka
    ? `${planet} rules ${ruledHouses} and is Yogakaraka for this ascendant. Its placement in ${placement} is therefore a supportive functional factor for House ${targetHouse}.`
    : facts.supportive_houses?.length && facts.challenging_houses?.length
      ? `${planet} has mixed lordship: supportive through House ${facts.supportive_houses.join(', ')}, but challenging through House ${facts.challenging_houses.join(', ')}. Its placement in ${placement} can deliver both sides to House ${targetHouse}.`
      : facts.supportive_houses?.length
        ? `${planet} rules the supportive ${ruledHouses} and is placed in ${placement}, strengthening its contribution to House ${targetHouse}.`
        : `${planet} rules ${ruledHouses} and is placed in ${placement}; ${facts.ruled_houses?.length === 1 ? 'this lordship adds' : 'these lordships add'} functional pressure to House ${targetHouse}.`;
  const specialStatuses = (facts.statuses || []).map((status) => sentence(status.rule_id).replace('Rashi ', 'Rashi '));
  const directRelations = (facts.direct_relations || []).map((relation) => sentence(relation).toLowerCase()).join(', ');
  const nodeInfluencers = (facts.influencers || []).map((influencer) => {
    const roles = (influencer.roles || []).map((role) => (
      role === 'dispositor'
        ? `sign dispositor${influencer.planet === facts.dispositor ? ` in House ${facts.dispositor_house}` : ''}`
        : 'conjunct planet'
    )).join(' and ');
    const result = influencer.polarity === 'supportive' ? 'net helpful'
      : influencer.polarity === 'challenging' ? 'net pressure'
        : influencer.polarity === 'mixed' ? 'mixed' : 'neutral';
    return `${influencer.planet} (${roles}: ${result})`;
  }).join('; ');
  const nodeResult = facts.resolved_polarity === 'supportive' ? 'net helpful'
    : facts.resolved_polarity === 'challenging' ? 'net pressure'
      : facts.resolved_polarity === 'mixed' ? 'mixed' : 'neutral';
  const descriptions = {
    house_lord_condition: `${planet} rules House ${targetHouse || reason?.house}, is placed in ${placement}, and has ${condition}.`,
    occupant_functional_lordship: functionalReason,
    aspector_functional_lordship: functionalReason,
    occupant_natural_influence: `${planet} occupies House ${targetHouse}. ${naturalInfluence}`,
    aspector_natural_influence: `${planet} aspects House ${targetHouse} from ${placement}. ${naturalInfluence}`,
    occupant_condition: `${planet} occupies House ${targetHouse} and has ${condition}.`,
    aspector_condition: `${planet} aspects House ${targetHouse} from ${placement} and has ${condition}.`,
    final_dispositor_condition: `${planet} is the final dispositor of ${facts.origin || 'a house significator'} through ${(facts.chain || []).join(' → ') || 'the dispositor chain'}; it is placed in ${placement} with ${condition}.`,
    natural_karaka_condition: `${planet}, a natural significator of House ${facts.karaka_for_house || targetHouse}, is placed in ${placement} with ${condition}.`,
    activated_validated_yoga: `${facts.yoga_name || 'A validated yoga'} involving ${(facts.yoga_planets || []).join(', ') || planet} is active for this house.`,
    carrier_natal_dignity: `${planet}, an active dasha planet delivering House ${targetHouse}, has ${sentence(facts.dignity || 'neutral').toLowerCase()} natal dignity.`,
    carrier_natal_combustion: `${planet}, an active dasha planet delivering this house, is combust in the natal chart.`,
    placement_dispositor_relationship: `${planet} is placed in ${facts.placement_sign_name || `sign ${Number(facts.placement_sign) + 1}`}, ruled by ${facts.dispositor}. ${planet} is naturally ${sentence(facts.natural_relation).toLowerCase()} toward ${facts.dispositor}, while their chart-specific Panchadha relationship is ${sentence(facts.compound_relation).toLowerCase()}. This ${reason?.polarity === 'supportive' ? 'supports' : reason?.polarity === 'challenging' ? 'pressures' : 'qualifies'} ${planet}'s ability to deliver its influence to House ${targetHouse}.`,
    dusthana_reversal_mitigation: `${planet} rules ${(facts.reversed_lordships || []).map((house) => `House ${house}`).join(' and ')} and is placed in House ${facts.placement_house}, forming ${facts.classification === 'afflicted' ? 'an' : 'a'} ${facts.classification || 'qualified'} ${(facts.yoga_types || []).join(' / ')} reversal. This softens only the corresponding dusthana-lord pressure${facts.other_lordships?.length ? `; ${facts.other_lordships.map((house) => `House ${house}`).join(' and ')} lordship remains separate` : ''}.${facts.afflictions?.length ? ` It is limited by ${facts.afflictions.map((item) => sentence(item).toLowerCase()).join(' and ')}.` : ''} It does not erase the other conditions affecting ${planet}'s delivery to House ${targetHouse}.`,
    fivefold_friendship_with_house_lord: `${planet} has a direct ${directRelations || 'validated'} sambandha with ${facts.house_lord}, the lord of House ${targetHouse}. Their Panchadha relationship is ${sentence(facts.compound_relation).toLowerCase()}; this is a compatibility modifier, not a separate positive or negative vote.`,
    fivefold_friendship_with_nakshatra_lord: `${planet} occupies ${facts.nakshatra_name || `nakshatra ${facts.nakshatra_number}`} ruled by ${facts.nakshatra_lord}; their Panchadha relationship is ${sentence(facts.compound_relation).toLowerCase()}. This modifies ${planet}'s expression; it is not a separate vote.`,
    planet_gandanta: `${planet} is in ${facts.gandanta_name || 'Gandanta'} with ${String(facts.intensity || '').toLowerCase() || 'recorded'} intensity, ${facts.distance_from_junction ?? '—'}° from the junction. Because it is connected to House ${targetHouse}, this adds instability or transition pressure.`,
    lagna_gandanta: `The ascendant is in ${facts.gandanta_name || 'Gandanta'} with ${String(facts.intensity || '').toLowerCase() || 'recorded'} intensity, affecting House 1 promise.`,
    yogi_lord: `${planet} is the Yogi lord for this chart and is connected to House ${targetHouse}, adding support.`,
    avayogi_lord: facts.avayogi_tithi_shunya_overlap
      ? `${planet} is the Avayogi lord, but it is also the Tithi Shunya lord; the declared overlap rule modifies the obstruction to a mixed result.`
      : `${planet} is the Avayogi lord for this chart and is connected to House ${targetHouse}, adding obstruction.`,
    dagdha_rashi_lord: `${planet} is the lord of the Dagdha Rashi ${facts.special_sign_name || ''} and is connected to House ${targetHouse}, adding pressure.`,
    tithi_shunya_lord: facts.avayogi_tithi_shunya_overlap
      ? `${planet} is the Tithi Shunya lord and also the Avayogi lord; the overlap is treated as mixed rather than purely obstructive.`
      : `${planet} is the Tithi Shunya lord for this chart and is connected to House ${targetHouse}, adding pressure.`,
    planet_in_dagdha_rashi: `${planet} is placed in the Dagdha Rashi ${facts.dagdha_sign_name || ''}, weakening the connected House ${targetHouse} indication.`,
    planet_in_tithi_shunya_rashi: `${planet} is placed in the Tithi Shunya Rashi ${facts.tithi_shunya_sign_name || ''}, restricting the connected House ${targetHouse} indication.`,
    combined_special_status: `${planet}'s correlated special statuses—${specialStatuses.join(', ')}—are treated as one factor.${facts.avayogi_tithi_shunya_overlap ? ' The Avayogi–Tithi Shunya overlap modifies those two indications to mixed; any Dagdha pressure remains.' : ''}`,
    node_conditioned_influence: `${planet}'s natural-malefic baseline is evaluated together with ${nodeInfluencers || `${facts.dispositor}, its sign dispositor`}. After combining these influences once, ${planet}'s House ${targetHouse} result is ${nodeResult}.`,
  };
  return descriptions[reason?.rule_id] || `${planet}: ${sentence(reason?.rule_id)}.`;
};
const shortDate = (value) => {
  if (!value) return '—';
  const parsed = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
};
const chartIdFrom = (data) => data?.chart_id || data?.birth_chart_id || data?.id || null;
const unique = (items) => [...new Set(items.filter(Boolean))];

export default function ActivationExplorerScreen({ navigation, route }) {
  const { colors, theme, androidLightCardFixStyle } = useTheme();
  const isDark = theme === 'dark';
  const ui = {
    surface: isDark ? '#28143b' : '#ffffff',
    surfaceRaised: isDark ? '#321a48' : '#fffaf6',
    surfaceMuted: isDark ? 'rgba(255,255,255,0.055)' : '#f8f5f2',
    border: isDark ? 'rgba(255,255,255,0.11)' : 'rgba(28,25,23,0.09)',
    header: isDark ? '#1e0a30' : '#fffaf7',
  };
  const activationColors = {
    fully_reinforced: '#f97316',
    dasha_transit_activated: isDark ? '#c2410c' : '#fb923c',
    dasha_connected: isDark ? 'rgba(249,115,22,0.24)' : '#ffedd5',
    transit_only: isDark ? 'rgba(255,255,255,0.10)' : '#e7e5e4',
    dormant: isDark ? 'rgba(255,255,255,0.035)' : '#f5f5f4',
  };
  const activationTextColors = {
    fully_reinforced: '#ffffff',
    dasha_transit_activated: '#ffffff',
    dasha_connected: isDark ? '#fed7aa' : '#7c2d12',
    transit_only: isDark ? 'rgba(255,255,255,0.78)' : '#57534e',
    dormant: isDark ? 'rgba(255,255,255,0.42)' : '#a8a29e',
  };
  const [birthData, setBirthData] = useState(route?.params?.birthData || null);
  const [asOf, setAsOf] = useState(localDate);
  const [horizonDays, setHorizonDays] = useState(90);
  const [result, setResult] = useState(null);
  const [selectedHouseNumber, setSelectedHouseNumber] = useState(null);
  const [selectedWindowStart, setSelectedWindowStart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [licenseRequired, setLicenseRequired] = useState(false);
  const [showOutcomeReasons, setShowOutcomeReasons] = useState(false);
  const [activeTab, setActiveTab] = useState('houses');
  const [expandedManifestation, setExpandedManifestation] = useState(null);

  useEffect(() => {
    if (birthData) return;
    storage.getBirthDetails().then(setBirthData).catch(() => setBirthData(null));
  }, [birthData]);

  const loadExplorer = useCallback(async () => {
    if (!birthData) return;
    setLoading(true);
    setError('');
    setLicenseRequired(false);
    try {
      const response = await chartAPI.getActivationExplorer({
        birthChartId: chartIdFrom(birthData), birthData, asOf, horizonDays, trace: false,
      });
      setResult(response.data);
      setSelectedWindowStart(null);
    } catch (requestError) {
      setResult(null);
      const detail = requestError?.response?.data?.detail;
      if (detail?.code === 'ASTROLOGER_LICENSE_REQUIRED') {
        setLicenseRequired(true);
        setError(detail.message || 'An active Astrologer License is required for this professional tool.');
      } else {
        setError(typeof detail === 'string' ? detail : requestError?.message || 'We could not read this chart right now. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [asOf, birthData, horizonDays]);

  useEffect(() => { loadExplorer(); }, [loadExplorer]);

  const currentRows = useMemo(() => {
    const rows = result?.house_activations || [];
    const containing = rows.filter((row) => row.window?.start_date <= asOf && row.window?.end_date >= asOf);
    if (containing.length) return containing;
    const firstStart = rows[0]?.window?.start_date;
    return firstStart ? rows.filter((row) => row.window?.start_date === firstStart) : [];
  }, [asOf, result]);

  useEffect(() => {
    if (!currentRows.length || currentRows.some((row) => row.house === selectedHouseNumber)) return;
    const strongest = [...currentRows].sort((a, b) =>
      (STATE_ORDER[b.state] || 0) - (STATE_ORDER[a.state] || 0)
      || (b.activation?.independent_confirmations || 0) - (a.activation?.independent_confirmations || 0)
    )[0];
    setSelectedHouseNumber(strongest?.house || 1);
  }, [currentRows, selectedHouseNumber]);

  const currentSelectedHouse = currentRows.find((row) => row.house === selectedHouseNumber) || currentRows[0];
  const selectedHouseWindows = (result?.house_activations || []).filter((row) => row.house === currentSelectedHouse?.house).sort((left, right) => left.window.start_date.localeCompare(right.window.start_date));
  const selectedHouse = selectedHouseWindows.find((row) => row.window?.start_date === selectedWindowStart) || currentSelectedHouse;
  const gridReferenceDate = selectedWindowStart || asOf;
  const displayedHouseRows = selectedWindowStart
    ? (result?.house_activations || []).filter((row) => row.window?.start_date <= gridReferenceDate && row.window?.end_date >= gridReferenceDate)
    : currentRows;
  const promise = (result?.natal_promises || []).find((row) => row.house === selectedHouse?.house);
  const currentWindow = selectedHouse?.window || currentRows[0]?.window;
  const currentCandidates = (result?.candidates || []).filter((candidate) =>
    candidate.window?.start_date === currentWindow?.start_date && candidate.window?.end_date === currentWindow?.end_date
  );
  const selectedCandidates = currentCandidates.filter((candidate) => (candidate.native_houses || []).includes(selectedHouse?.house));
  const alternatives = selectedCandidates
    .flatMap((candidate) => candidate.resolution?.interpretation_alternatives || [])
    .filter((item) => (item.focus_native_houses || item.native_houses || []).includes(selectedHouse?.house))
    .filter((item, index, rows) => rows.findIndex((row) => `${row.subject}:${row.signature_key || row.label}:${(row.native_houses || []).join('-')}` === `${item.subject}:${item.signature_key || item.label}:${(item.native_houses || []).join('-')}`) === index)
    .slice(0, 10);
  const manifestationGroups = alternatives.reduce((groups, alternative) => {
    const existing = groups.find((group) => group.subject === alternative.subject);
    if (existing) existing.items.push(alternative);
    else groups.push({ subject: alternative.subject, items: [alternative] });
    return groups;
  }, []);
  const chartManifestations = result?.chart_manifestations || [];
  const chartManifestationGroups = useMemo(() => {
    const firstSubjectPosition = new Map();
    chartManifestations.forEach((item, index) => {
      if (!firstSubjectPosition.has(item.subject)) firstSubjectPosition.set(item.subject, index);
    });
    const ordered = [...chartManifestations].sort((left, right) => {
      const leftSubject = left.subject === 'self' ? -1 : firstSubjectPosition.get(left.subject);
      const rightSubject = right.subject === 'self' ? -1 : firstSubjectPosition.get(right.subject);
      if (leftSubject !== rightSubject) return leftSubject - rightSubject;
      const leftCurrent = left.window?.start_date <= asOf && left.window?.end_date >= asOf ? 0 : 1;
      const rightCurrent = right.window?.start_date <= asOf && right.window?.end_date >= asOf ? 0 : 1;
      if (leftCurrent !== rightCurrent) return leftCurrent - rightCurrent;
      const dateOrder = String(left.window?.start_date || '').localeCompare(String(right.window?.start_date || ''));
      if (dateOrder) return dateOrder;
      const strengthOrder = (SYNTHESIS_STRENGTH_ORDER[left.synthesis_strength] ?? 9)
        - (SYNTHESIS_STRENGTH_ORDER[right.synthesis_strength] ?? 9);
      if (strengthOrder) return strengthOrder;
      return String(left.label || '').localeCompare(String(right.label || ''));
    });
    return ordered.reduce((groups, item) => {
      const existing = groups.find((group) => group.subject === item.subject);
      if (existing) existing.items.push(item);
      else groups.push({ subject: item.subject, items: [item] });
      return groups;
    }, []);
  }, [asOf, chartManifestations]);
  const carriers = selectedHouse?.activation?.carrier_planets || [];
  const levels = selectedHouse?.activation?.active_dasha_levels || [];
  const directDashaConnections = unique((selectedHouse?.natal_connections || []).map((item) => `${item.planet} connects by natal ${String(item.relation || '').replaceAll('_', ' ')} during the ${item.level === 'MD' ? 'major period' : item.level === 'AD' ? 'sub-period' : 'sub-sub-period'}`));
  const directDashaPlanets = new Set((selectedHouse?.natal_connections || []).map((item) => item.planet));
  const cooperativeCarriers = carriers.filter((planet) => !directDashaPlanets.has(planet));
  const repeatedDashaPlanets = unique((selectedHouse?.evidence || []).filter((item) => item.provider === 'transit_natal_ledger' && item.facts?.same_planet_natal_repetition).map((item) => item.planet));
  const timingTransitConnections = (selectedHouse?.transit_connections || []).filter((item) => item.timing_trigger).map((item) => {
    const relations = (item.relations || []).map((relation) => {
      if (relation === 'occupation') return `occupying H${selectedHouse?.house}`;
      const aspectNumber = ((Number(selectedHouse?.house) - Number(item.transit_house) + 12) % 12) + 1;
      const suffix = aspectNumber === 1 ? 'st' : aspectNumber === 2 ? 'nd' : aspectNumber === 3 ? 'rd' : 'th';
      return `${aspectNumber}${suffix} aspect`;
    }).join(' and ');
    return `Transit ${item.planet} is in H${item.transit_house} and connects by ${relations}`;
  });
  const triggers = selectedHouse?.timing_triggers || [];

  const shiftDate = (days) => {
    const next = new Date(`${asOf}T12:00:00`);
    next.setDate(next.getDate() + days);
    setAsOf(localDate(next));
  };

  const card = [
    styles.card,
    { backgroundColor: ui.surface, borderColor: ui.border },
    !isDark && androidLightCardFixStyle,
  ];

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: colors.background }]}> 
      <LinearGradient colors={theme === 'dark' ? [colors.gradientStart, colors.gradientMid] : [colors.gradientStart, colors.gradientMid]} style={StyleSheet.absoluteFill} />
      <View style={[styles.header, { backgroundColor: ui.header, borderBottomColor: ui.border }]}>
        <TouchableOpacity style={[styles.headerButton, { backgroundColor: ui.surfaceMuted }]} onPress={() => navigation.goBack()} accessibilityLabel="Go back">
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <View style={styles.headerCopy}>
          <Text style={[styles.headerTitle, { color: colors.text }]}>What’s active now?</Text>
          <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]} numberOfLines={1}>{birthData?.name || 'Selected chart'} · your chart explained</Text>
        </View>
        <TouchableOpacity style={[styles.headerButton, { backgroundColor: ui.surfaceMuted }]} onPress={loadExplorer} accessibilityLabel="Recalculate">
          <Ionicons name="refresh" size={22} color={colors.text} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={[card, styles.controls]}>
          <View style={styles.dateControl}>
            <TouchableOpacity onPress={() => shiftDate(-1)} style={[styles.miniButton, { backgroundColor: ui.surfaceMuted }]}><Ionicons name="chevron-back" size={18} color={colors.text} /></TouchableOpacity>
            <View style={styles.controlCopy}><Text style={[styles.eyebrow, { color: colors.textSecondary }]}>VIEW FROM</Text><Text style={[styles.controlValue, { color: colors.text }]}>{new Date(`${asOf}T00:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</Text></View>
            <TouchableOpacity onPress={() => shiftDate(1)} style={[styles.miniButton, { backgroundColor: ui.surfaceMuted }]}><Ionicons name="chevron-forward" size={18} color={colors.text} /></TouchableOpacity>
          </View>
          <View style={styles.segmentRow}>
            {[30, 90, 180].map((days) => <TouchableOpacity key={days} onPress={() => setHorizonDays(days)} style={[styles.segment, { borderColor: horizonDays === days ? colors.primary : ui.border, backgroundColor: horizonDays === days ? colors.primary : ui.surfaceMuted }]}><Text style={[styles.segmentText, { color: horizonDays === days ? '#fff' : colors.textSecondary }]}>{days} days</Text></TouchableOpacity>)}
          </View>
        </View>

        {loading ? <View style={styles.state}><ActivityIndicator size="large" color={colors.primary} /><Text style={[styles.stateTitle, { color: colors.text }]}>Reading the chart</Text><Text style={[styles.stateText, { color: colors.textSecondary }]}>We’re connecting the birth chart, current planetary period, transits and timing highlights.</Text></View> : null}
        {!loading && error ? <View style={[card, styles.state]}>
          <Ionicons name={licenseRequired ? 'school-outline' : 'alert-circle-outline'} size={34} color={licenseRequired ? colors.primary : colors.error} />
          <Text style={[styles.stateTitle, { color: colors.text }]}>{licenseRequired ? 'Astrologer License required' : 'Calculation could not be completed'}</Text>
          <Text style={[styles.stateText, { color: colors.textSecondary }]}>{error}</Text>
          <TouchableOpacity
            onPress={licenseRequired
              ? () => navigation.navigate('Credits', {
                focusSubscriptionFamily: 'astrologer',
                returnTo: 'ActivationExplorer',
                returnParams: { birthData },
              })
              : loadExplorer}
            style={[styles.primaryButton, { backgroundColor: colors.primary }]}
          >
            <Text style={styles.primaryButtonText}>{licenseRequired ? 'View ₹100 monthly plan' : 'Try again'}</Text>
          </TouchableOpacity>
        </View> : null}

        {!loading && result ? <>
          <LinearGradient colors={isDark ? ['#3b1d52', '#28143b'] : ['#fff0e4', '#ffffff']} style={[styles.card, styles.dashaCard, { borderColor: ui.border }]}>
            <Text style={[styles.eyebrow, { color: colors.textSecondary }]}>YOUR CURRENT TIMING CYCLE</Text>
            <Text style={[styles.dashaChain, { color: colors.text }]}>{currentWindow?.mahadasha || '—'} <Text style={{ color: colors.primary }}>major →</Text> {currentWindow?.antardasha || '—'} <Text style={{ color: colors.primary }}>sub-period →</Text> {currentWindow?.pratyantardasha || '—'}</Text>
            <Text style={[styles.meta, { color: colors.textSecondary }]}>{shortDate(currentWindow?.start_date)} – {shortDate(currentWindow?.end_date)} · {currentRows.filter((row) => !['transit_only', 'dormant'].includes(row.state)).length} houses active now · based on D1</Text>
          </LinearGradient>

          <View style={[styles.viewTabs, { backgroundColor: ui.surfaceMuted, borderColor: ui.border }]}>
            {[['houses', 'House by House'], ['manifestations', 'Combined Life Themes']].map(([key, label]) => <TouchableOpacity key={key} onPress={() => setActiveTab(key)} style={[styles.viewTab, activeTab === key && { backgroundColor: colors.primary }]}><Text style={[styles.viewTabText, { color: activeTab === key ? '#fff' : colors.textSecondary }]}>{label}</Text></TouchableOpacity>)}
          </View>

          {activeTab === 'houses' ? <>
          <View style={card}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>Where life is drawing your attention</Text>
            <Text style={[styles.sectionIntro, { color: colors.textSecondary }]}>Tap any house to understand why it matters now and what you may notice.</Text>
            <View style={styles.houseGrid}>{Array.from({ length: 12 }, (_, index) => index + 1).map((houseNumber) => {
              const house = displayedHouseRows.find((row) => row.house === houseNumber);
              const selected = selectedHouse?.house === houseNumber;
              const stateColor = activationColors[house?.state || 'dormant'];
              const stateTextColor = activationTextColors[house?.state || 'dormant'];
              return <TouchableOpacity key={houseNumber} onPress={() => { setSelectedHouseNumber(houseNumber); setSelectedWindowStart(null); }} style={[styles.houseTile, { borderColor: selected ? colors.primary : ui.border, borderWidth: selected ? 2 : 1, backgroundColor: stateColor }]}><View style={[styles.outcomeDot, { backgroundColor: OUTCOME_COLORS[house?.outcome?.tone || 'neutral'] }]} /><Text style={[styles.houseNumber, { color: stateTextColor }]}>H{houseNumber}</Text><Text style={[styles.houseState, { color: stateTextColor }]} numberOfLines={2}>{STATE_LABELS[house?.state] || 'Not active'}</Text></TouchableOpacity>;
            })}</View>
            <View style={[styles.legendBlock, { backgroundColor: ui.surfaceMuted }]}><Text style={[styles.legendTitle, { color: colors.text }]}>Activation</Text><View style={styles.legendWrap}>{[['fully_reinforced', 'Strong'], ['dasha_transit_activated', 'Active'], ['dasha_connected', 'Period'], ['transit_only', 'Background']].map(([state, label]) => <View key={state} style={styles.legendItem}><View style={[styles.legendSwatch, { backgroundColor: activationColors[state] }]} /><Text style={[styles.legendText, { color: colors.textSecondary }]}>{label}</Text></View>)}</View><Text style={[styles.legendTitle, { color: colors.text }]}>Likely experience</Text><View style={styles.legendWrap}>{[['supportive', 'Constructive'], ['mixed', 'Mixed'], ['challenging', 'Pressure'], ['neutral', 'Unclear']].map(([tone, label]) => <View key={tone} style={styles.legendItem}><View style={[styles.legendDot, { backgroundColor: OUTCOME_COLORS[tone] }]} /><Text style={[styles.legendText, { color: colors.textSecondary }]}>{label}</Text></View>)}</View></View>
          </View>

          {selectedHouse ? <View style={card}>
            <View style={styles.detailHeading}><View style={{ flex: 1 }}><Text style={[styles.eyebrow, { color: colors.primary }]}>HOUSE {selectedHouse.house}</Text><Text style={[styles.sectionTitle, { color: colors.text }]}>{HOUSE_LABELS[selectedHouse.house]}</Text><Text style={[styles.meta, { color: colors.textSecondary }]}>{STATE_EXPLANATIONS[selectedHouse.state]} · {OUTCOME_LABELS[selectedHouse.outcome?.tone]}</Text></View><View style={[styles.band, { backgroundColor: `${colors.primary}18` }]}><Text style={{ color: colors.primary, fontWeight: '600', textAlign: 'center', fontSize: 11 }}>{BAND_LABELS[selectedHouse.activation?.band] || 'Chart agreement unavailable'}</Text></View></View>
            {selectedHouseWindows.length > 1 ? <View style={styles.windowPicker}><Text style={[styles.reasonTitle, { color: colors.text }]}>Inspect a timing window</Text><ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.windowPickerRow}>{selectedHouseWindows.map((row) => { const active = row.window.start_date === selectedHouse.window?.start_date; return <TouchableOpacity key={`${row.window.start_date}-${row.window.end_date}`} onPress={() => setSelectedWindowStart(row.window.start_date)} style={[styles.windowChip, { borderColor: active ? colors.primary : colors.cardBorder, backgroundColor: active ? colors.primary : colors.cardBackground }]}><Text style={[styles.windowChipText, { color: active ? '#fff' : colors.textSecondary }]}>{shortDate(row.window.start_date)} – {shortDate(row.window.end_date)}</Text></TouchableOpacity>; })}</ScrollView></View> : null}
            <Text style={[styles.subheading, { color: colors.text }]}>Why this house matters now</Text>
            {[
              ['1', 'Birth-chart foundation', promise ? `${promise.lord} rules this house; planets placed here: ${promise.occupants?.join(', ') || 'none'}; planets aspecting it: ${promise.aspecting_planets?.join(', ') || 'none'}.` : 'Birth-chart foundation is unavailable.'],
              ['2', 'Connection to your current period', levels.length ? `${directDashaConnections.join('; ') || 'No direct connection'}.${cooperativeCarriers.length ? ` ${cooperativeCarriers.join(', ')} also participates because it has a natal relationship with the directly connected period planet.` : ''}` : 'The current major and sub-period planets do not have a strong natal connection to this house, so it remains background context.'],
              ['3', 'What is triggering it now', timingTransitConnections.length ? selectedHouse.activation?.natal_position_reinforced ? `${timingTransitConnections.join('; ')}. ${repeatedDashaPlanets.join(', ') || 'The active period planet'} also returns to its natal position, strengthening the timing.` : `${timingTransitConnections.join('; ')}. These transits bring attention here, although the active period planet is not also repeating its natal position.` : 'No strong transit trigger was found.'],
            ].map(([number, title, body]) => <View key={number} style={[styles.reasonRow, { backgroundColor: ui.surfaceMuted }]}><View style={[styles.reasonNumber, { backgroundColor: `${colors.primary}1f` }]}><Text style={[styles.reasonNumberText, { color: colors.primary }]}>{number}</Text></View><View style={{ flex: 1 }}><Text style={[styles.reasonTitle, { color: colors.text }]}>{title}</Text><Text style={[styles.reasonBody, { color: colors.textSecondary }]}>{body}</Text></View></View>)}
            <View style={[styles.facts, { borderColor: ui.border, backgroundColor: ui.surfaceMuted }]}><Text style={[styles.fact, { color: colors.textSecondary }]}>House lord  <Text style={{ color: colors.text, fontWeight: '600' }}>{selectedHouse.house_lord || promise?.lord || '—'}</Text></Text><Text style={[styles.fact, { color: colors.textSecondary }]}>Overall direction  <Text style={{ color: colors.text, fontWeight: '600' }}>{OUTCOME_LABELS[selectedHouse.outcome?.tone] || 'Unclear'}</Text></Text><TouchableOpacity onPress={() => setShowOutcomeReasons(true)} accessibilityRole="button" accessibilityLabel="See what helps or adds pressure"><Text style={[styles.fact, { color: colors.textSecondary }]}>Planetary influences  <Text style={{ color: colors.text, fontWeight: '600' }}>{selectedHouse.outcome?.supportive_factors || 0} helpful · {selectedHouse.outcome?.mixed_factors || 0} mixed · {selectedHouse.outcome?.challenging_factors || 0} pressure</Text></Text><Text style={[styles.factorLink, { color: colors.primary }]}>See what helps or adds pressure  →</Text></TouchableOpacity><Text style={[styles.fact, { color: colors.textSecondary }]}>Planets connecting this house to the current period  <Text style={{ color: colors.text, fontWeight: '600' }}>{carriers.join(', ') || 'None'}</Text></Text></View>
            <Text style={[styles.subheading, { color: colors.text }]}>What you may notice in life</Text>
            {manifestationGroups.length ? manifestationGroups.map((group) => <View key={group.subject} style={styles.personGroup}><Text style={[styles.personHeading, { color: colors.primary }]}>{sentence(group.subject)}</Text>{group.items.map((item, index) => <View key={`${item.signature_key || item.label}-${index}`} style={[styles.manifestation, { borderColor: colors.cardBorder }]}><Text style={[styles.reasonTitle, { color: colors.text }]}>{item.label}</Text><Text style={[styles.reasonBody, { color: colors.textSecondary }]}>{item.tone_interpretation}</Text>{(item.manifestations || []).map((manifestation) => <Text key={manifestation} style={[styles.bullet, { color: colors.textSecondary }]}>• {manifestation}</Text>)}</View>)}</View>) : <Text style={[styles.stateText, { color: colors.textSecondary }]}>This house is active, but the chart does not narrow it to a clear real-life theme in this period.</Text>}
            <Text style={[styles.subheading, { color: colors.text }]}>When it can become noticeable</Text>
            <Text style={[styles.timing, { color: colors.text }]}>Core window: {shortDate(currentWindow?.start_date)} – {shortDate(currentWindow?.end_date)}</Text>
            <Text style={[styles.reasonBody, { color: colors.textSecondary }]}>{triggers.length ? `${triggers.length} shorter Sun or Moon timing highlights appear inside this period.` : 'No shorter Sun or Moon timing highlight appears inside this period.'}</Text>
          </View> : null}

          </> : <View style={[card, styles.manifestationSection]}>
            <Text style={[styles.eyebrow, { color: colors.primary }]}>YOUR CHART’S BIGGER STORY</Text>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>Life themes coming into focus</Text>
            <Text style={[styles.sectionIntro, { color: colors.textSecondary }]}>These themes appear when several active houses point toward the same area of life.</Text>
            {chartManifestationGroups.length ? chartManifestationGroups.map((group) => <View key={group.subject} style={styles.subjectSection}>
              <View style={[styles.subjectSectionHeader, { borderColor: ui.border }]}>
                <View style={[styles.subjectIcon, { backgroundColor: `${colors.primary}18` }]}>
                  <Ionicons name={group.subject === 'self' ? 'person-outline' : 'people-outline'} size={17} color={colors.primary} />
                </View>
                <Text style={[styles.subjectSectionTitle, { color: colors.text }]}>{subjectSectionLabel(group.subject)}</Text>
                <Text style={[styles.subjectCount, { color: colors.textSecondary }]}>{group.items.length} {group.items.length === 1 ? 'theme' : 'themes'}</Text>
              </View>
              {group.items.map((item) => {
              const expanded = expandedManifestation === item.manifestation_id;
              const toneColor = OUTCOME_COLORS[item.outcome_tone] || OUTCOME_COLORS.neutral;
              return <View key={item.manifestation_id} style={[styles.manifestationCard, { backgroundColor: ui.surfaceRaised, borderColor: ui.border, borderLeftColor: toneColor }]}>
                <View style={styles.manifestationHeading}><View style={{ flex: 1 }}><Text style={[styles.eyebrow, { color: colors.textSecondary }]}>{sentence(item.domain)}</Text><Text style={[styles.manifestationTitle, { color: colors.text }]}>{sentence(item.label)}</Text></View><View style={[styles.confidenceBadge, { backgroundColor: `${toneColor}16` }]}><Text style={[styles.confidence, { color: toneColor }]}>{SYNTHESIS_STRENGTH_LABELS[item.synthesis_strength] || 'Evidence available'}</Text></View></View>
                <View style={styles.manifestationChips}><Text style={[styles.manifestationChip, { color: toneColor, backgroundColor: `${toneColor}18` }]}>{OUTCOME_LABELS[item.outcome_tone] || sentence(item.outcome_tone)}</Text><Text style={[styles.manifestationChip, { color: colors.textSecondary, backgroundColor: `${toneColor}12` }]}>{item.window?.start_date <= asOf && item.window?.end_date >= asOf ? 'Active now' : 'Upcoming'} · {shortDate(item.window?.start_date)} – {shortDate(item.window?.end_date)}</Text></View>
                <View style={styles.manifestationHouses}>{(item.house_roles || []).map((role) => <View key={`${role.native_house}-${role.relative_house}`} style={[styles.manifestationHouse, { backgroundColor: ui.surfaceMuted, borderColor: ui.border }]}><Text style={[styles.comboHouses, { color: toneColor }]}>H{role.native_house}{item.subject !== 'self' ? ` · for your ${item.subject}, this is H${role.relative_house}` : ''}</Text><Text style={[styles.reasonBody, { color: colors.textSecondary }]}>{role.role}</Text></View>)}</View>
                <Text style={[styles.reasonTitle, { color: colors.text, marginTop: 14 }]}>What you may notice</Text>
                <Text style={[styles.reasonBody, { color: colors.text }]}>{item.summary}</Text>
                {(item.possibilities || []).map((possibility) => <Text key={possibility} style={[styles.bullet, { color: colors.textSecondary }]}>• {possibility}</Text>)}
                <TouchableOpacity onPress={() => setExpandedManifestation(expanded ? null : item.manifestation_id)} style={styles.explainButton}><Text style={[styles.factorLink, { color: colors.primary }]}>{expanded ? 'Hide chart explanation' : 'Why your chart points to this'}</Text><Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={16} color={colors.primary} /></TouchableOpacity>
                {expanded ? <View style={[styles.explanation, { borderColor: colors.cardBorder }]}>
                  {(item.house_roles || []).map((role) => <View key={`reason-${role.native_house}-${role.relative_house}`} style={[styles.manifestationFactors, { borderColor: colors.cardBorder }]}>
                    <Text style={[styles.reasonTitle, { color: colors.text }]}>House {role.native_house}: {role.role}</Text>
                    {(role.dasha_connections || []).map((reason) => <Text key={reason} style={[styles.reasonBody, { color: colors.textSecondary }]}>{reason}.</Text>)}
                    {(role.transit_connections || []).map((reason) => <Text key={reason} style={[styles.reasonBody, { color: colors.textSecondary }]}>{reason}.</Text>)}
                    <Text style={[styles.reasonBody, { color: colors.text }]}><Text style={{ fontWeight: '800' }}>This house suggests: </Text>{OUTCOME_LABELS[role.outcome_tone] || sentence(role.outcome_tone)}</Text>
                  </View>)}
                  {(item.rationale || []).map((reason) => <Text key={reason} style={[styles.bullet, { color: colors.textSecondary }]}>• {reason}</Text>)}
                  {[['What helps', item.helpful_reasons || []], ['Mixed signals', item.mixed_reasons || []], ['What adds pressure', item.pressure_reasons || []]].map(([label, reasons]) => reasons.length ? <View key={label} style={[styles.manifestationFactors, { borderColor: colors.cardBorder }]}>
                    <Text style={[styles.reasonTitle, { color: colors.text }]}>{label}</Text>
                    {reasons.map((reason, index) => <View key={reason.independent_key || `${label}-${index}`} style={styles.manifestationFactor}>
                      <Text style={[styles.reasonTitle, { color: colors.text }]}>{reason.planet || 'Chart factor'} · H{reason.house || '—'}</Text>
                      {(reason.components || []).filter((component) => component.polarity !== 'neutral' || component.is_modifier).map((component) => <Text key={component.independent_key} style={[styles.reasonBody, { color: colors.textSecondary }]}>{reasonDescription(component)}</Text>)}
                    </View>)}
                  </View> : null)}
                </View> : null}
              </View>;
            })}
            </View>) : <View style={styles.manifestationEmpty}><Text style={[styles.reasonTitle, { color: colors.text }]}>No combined life theme is clear in this period</Text><Text style={[styles.stateText, { color: colors.textSecondary }]}>Some individual houses may still be active, but they do not yet join into one reliable real-life story.</Text></View>}
          </View>}
        </> : null}

      </ScrollView>
      <Modal visible={showOutcomeReasons} transparent animationType="slide" onRequestClose={() => setShowOutcomeReasons(false)}>
        <View style={styles.modalBackdrop}>
          <SafeAreaView style={[styles.reasonSheet, { backgroundColor: isDark ? '#241333' : '#ffffff' }]}>
            <View style={[styles.reasonSheetHeader, { borderColor: colors.cardBorder }]}>
              <View style={{ flex: 1 }}><Text style={[styles.eyebrow, { color: colors.primary }]}>HOUSE {selectedHouse?.house || '—'}</Text><Text style={[styles.sectionTitle, { color: colors.text }]}>Why this result?</Text><Text style={[styles.meta, { color: colors.textSecondary }]}>{OUTCOME_LABELS[selectedHouse?.outcome?.tone] || 'Unclear'}</Text></View>
              <TouchableOpacity onPress={() => setShowOutcomeReasons(false)} style={styles.modalClose} accessibilityLabel="Close reasons"><Ionicons name="close" size={24} color={colors.text} /></TouchableOpacity>
            </View>
            <ScrollView contentContainerStyle={styles.reasonSheetContent}>
              {[
                ['supportive', 'What helps', selectedHouse?.outcome?.supportive_reasons || []],
                ['mixed', 'Mixed signals', selectedHouse?.outcome?.mixed_reasons || []],
                ['challenging', 'What adds pressure', selectedHouse?.outcome?.challenging_reasons || []],
              ].map(([tone, title, reasons]) => <View key={tone} style={[styles.reasonGroup, { borderColor: OUTCOME_COLORS[tone] }]}><Text style={[styles.reasonGroupTitle, { color: colors.text }]}>{title}  <Text style={{ color: OUTCOME_COLORS[tone] }}>{reasons.length}</Text></Text>{reasons.length ? reasons.map((reason, index) => <View key={reason.independent_key || `${tone}-${index}`} style={[styles.outcomeReason, { borderColor: colors.cardBorder }]}><View style={styles.outcomeReasonHeading}><Text style={[styles.reasonTitle, { color: colors.text }]}>{reason.planet || sentence(reason.provider)}</Text><Text style={[styles.reasonWeight, { color: colors.textSecondary }]}>{tone === 'mixed' ? 'Helps in some ways and complicates others' : tone === 'supportive' ? 'Supports this result' : 'Adds pressure'}</Text></View>{(reason.components || []).filter((component) => component.polarity !== 'neutral' || component.is_modifier).map((component) => <View key={component.independent_key} style={styles.componentRow}><View style={[styles.componentDot, { backgroundColor: OUTCOME_COLORS[component.polarity] || OUTCOME_COLORS.neutral }]} /><Text style={[styles.reasonBody, { color: colors.textSecondary, flex: 1 }]}>{reasonDescription(component)}</Text></View>)}</View>) : <Text style={[styles.reasonBody, { color: colors.textSecondary }]}>{tone === 'supportive' ? 'No planet is predominantly supportive; helpful influences may still appear under Mixed signals.' : tone === 'mixed' ? 'No planet has both helpful and pressuring influences.' : 'No planet is predominantly adding pressure.'}</Text>}</View>)}
              <Text style={[styles.reasonFootnote, { color: colors.textSecondary }]}>Open each planet to see the birth-chart conditions behind its influence. Related conditions are grouped so the same planet is not counted repeatedly.</Text>
            </ScrollView>
          </SafeAreaView>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  header: {
    minHeight: 72,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    gap: 12,
  },
  headerButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerCopy: { flex: 1, alignItems: 'flex-start' },
  headerTitle: { fontSize: 20, lineHeight: 25, fontWeight: '700', letterSpacing: -0.35 },
  headerSubtitle: { fontSize: 12, lineHeight: 17, marginTop: 1 },
  content: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 48,
    gap: 14,
    width: '100%',
    maxWidth: 900,
    alignSelf: 'center',
  },
  card: {
    borderWidth: 1,
    borderRadius: 22,
    padding: 18,
    ...Platform.select({
      ios: { shadowColor: '#13051f', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.10, shadowRadius: 16 },
      android: { elevation: 2 },
      default: { boxShadow: '0 6px 22px rgba(30, 10, 45, 0.08)' },
    }),
  },
  controls: { gap: 14 },
  dateControl: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  controlCopy: { flex: 1, alignItems: 'center' },
  eyebrow: { fontSize: 10, lineHeight: 14, fontWeight: '700', letterSpacing: 1.1 },
  controlValue: { fontSize: 16, lineHeight: 21, fontWeight: '600', marginTop: 3 },
  miniButton: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  segmentRow: { flexDirection: 'row', gap: 8 },
  segment: {
    flex: 1,
    minHeight: 40,
    borderRadius: 20,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  segmentText: { fontSize: 12, lineHeight: 16, fontWeight: '600' },
  viewTabs: {
    flexDirection: 'row',
    gap: 6,
    padding: 5,
    borderWidth: 1,
    borderRadius: 17,
  },
  viewTab: { flex: 1, minHeight: 44, borderRadius: 13, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 8 },
  viewTabText: { fontSize: 12, lineHeight: 16, fontWeight: '600', textAlign: 'center' },
  state: { alignItems: 'center', paddingVertical: 46, paddingHorizontal: 24, gap: 10 },
  stateTitle: { fontSize: 18, lineHeight: 24, fontWeight: '700', textAlign: 'center' },
  stateText: { fontSize: 14, lineHeight: 21, textAlign: 'center' },
  primaryButton: { borderRadius: 22, paddingHorizontal: 22, paddingVertical: 12, marginTop: 8 },
  primaryButtonText: { color: '#fff', fontSize: 14, fontWeight: '600' },
  dashaCard: { gap: 8, overflow: 'hidden' },
  dashaChain: { fontSize: Platform.OS === 'web' ? 21 : 19, lineHeight: 28, fontWeight: '700', letterSpacing: -0.3 },
  meta: { fontSize: 13, lineHeight: 19 },
  sectionTitle: { fontSize: 21, lineHeight: 27, fontWeight: '700', letterSpacing: -0.35 },
  sectionIntro: { fontSize: 14, lineHeight: 21, marginTop: 5, marginBottom: 17 },
  houseGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 9 },
  houseTile: {
    position: 'relative',
    width: '31.5%',
    minHeight: 86,
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 11,
    justifyContent: 'center',
  },
  outcomeDot: {
    position: 'absolute',
    top: 10,
    right: 10,
    width: 10,
    height: 10,
    borderRadius: 5,
    borderWidth: 1.5,
    borderColor: '#ffffff',
  },
  houseNumber: { fontSize: 19, lineHeight: 23, fontWeight: '700', letterSpacing: -0.2 },
  houseState: { fontSize: 11, lineHeight: 15, fontWeight: '500', marginTop: 6 },
  legendBlock: { marginTop: 16, gap: 9, padding: 13, borderRadius: 15 },
  legendTitle: { fontSize: 12, lineHeight: 16, fontWeight: '600', marginTop: 2 },
  legendWrap: { flexDirection: 'row', flexWrap: 'wrap', columnGap: 14, rowGap: 8 },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legendSwatch: { width: 11, height: 11, borderRadius: 4 },
  legendDot: { width: 9, height: 9, borderRadius: 5 },
  legendText: { fontSize: 11, lineHeight: 15 },
  detailHeading: { gap: 12 },
  band: { alignSelf: 'flex-start', maxWidth: 210, paddingHorizontal: 11, paddingVertical: 7, borderRadius: 999 },
  windowPicker: { marginTop: 18, gap: 9 },
  windowPickerRow: { gap: 8, paddingRight: 8 },
  windowChip: { borderWidth: 1, borderRadius: 999, paddingHorizontal: 13, paddingVertical: 9 },
  windowChipText: { fontSize: 12, lineHeight: 16, fontWeight: '600' },
  subheading: { fontSize: 17, lineHeight: 22, fontWeight: '700', marginTop: 26, marginBottom: 12, letterSpacing: -0.2 },
  reasonRow: { flexDirection: 'row', gap: 11, marginBottom: 10, padding: 13, borderRadius: 15 },
  reasonNumber: { width: 26, height: 26, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  reasonNumberText: { fontSize: 12, fontWeight: '700' },
  reasonTitle: { fontSize: 14, lineHeight: 19, fontWeight: '600' },
  reasonBody: { fontSize: 13, lineHeight: 20, marginTop: 4 },
  facts: { borderWidth: 1, borderRadius: 16, padding: 14, gap: 11, marginTop: 6 },
  fact: { fontSize: 13, lineHeight: 19 },
  factorLink: { marginTop: 5, fontSize: 13, lineHeight: 18, fontWeight: '600' },
  personGroup: { marginBottom: 14 },
  personHeading: { fontSize: 11, lineHeight: 15, fontWeight: '700', letterSpacing: 1, marginBottom: 8, textTransform: 'uppercase' },
  manifestation: { borderWidth: 1, borderRadius: 16, padding: 14, marginBottom: 9 },
  bullet: { fontSize: 13, lineHeight: 20, marginTop: 5 },
  timing: { fontSize: 14, lineHeight: 20, fontWeight: '600' },
  combo: { borderTopWidth: 1, paddingVertical: 12 },
  comboHouses: { fontSize: 11, lineHeight: 15, fontWeight: '700', marginBottom: 3, letterSpacing: 0.25 },
  manifestationSection: { gap: 3 },
  subjectSection: { marginTop: 18 },
  subjectSectionHeader: {
    minHeight: 44,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingBottom: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  subjectIcon: { width: 34, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
  subjectSectionTitle: { flex: 1, fontSize: 17, lineHeight: 22, fontWeight: '700', letterSpacing: -0.2 },
  subjectCount: { fontSize: 11, lineHeight: 15, fontWeight: '500' },
  manifestationCard: {
    borderWidth: 1,
    borderLeftWidth: 3,
    borderRadius: 20,
    padding: 17,
    marginTop: 13,
  },
  manifestationHeading: { gap: 12, alignItems: 'flex-start' },
  manifestationTitle: { fontSize: 20, lineHeight: 26, fontWeight: '700', marginTop: 4, letterSpacing: -0.3 },
  confidenceBadge: { alignSelf: 'flex-start', borderRadius: 999, paddingHorizontal: 9, paddingVertical: 6 },
  confidence: { fontSize: 11, lineHeight: 15, fontWeight: '600' },
  manifestationChips: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 12 },
  manifestationChip: { fontSize: 11, lineHeight: 15, fontWeight: '600', paddingHorizontal: 9, paddingVertical: 7, borderRadius: 999 },
  manifestationHouses: { gap: 8, marginTop: 14 },
  manifestationHouse: { borderWidth: 1, borderRadius: 14, padding: 12 },
  explainButton: { minHeight: 42, flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 12 },
  explanation: { borderTopWidth: 1, marginTop: 8, paddingTop: 2 },
  manifestationFactors: { borderTopWidth: 1, paddingTop: 12, marginTop: 14 },
  manifestationFactor: { marginTop: 11 },
  manifestationEmpty: { alignItems: 'center', gap: 8, paddingVertical: 30, paddingHorizontal: 12 },
  traceHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  copyButton: { borderWidth: 1, borderRadius: 10, paddingHorizontal: 10, paddingVertical: 8, flexDirection: 'row', alignItems: 'center', gap: 5 },
  json: { marginTop: 14, padding: 12, borderRadius: 12, fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace', fontSize: 9, lineHeight: 13 },
  modalBackdrop: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(15,5,25,0.78)' },
  reasonSheet: {
    width: '100%',
    maxHeight: '92%',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    overflow: 'hidden',
  },
  reasonSheetHeader: { flexDirection: 'row', alignItems: 'flex-start', paddingHorizontal: 20, paddingTop: 22, paddingBottom: 18, borderBottomWidth: 1 },
  modalClose: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center' },
  reasonSheetContent: { padding: 18, paddingBottom: 38, gap: 14 },
  reasonGroup: { borderTopWidth: 3, borderWidth: 1, borderRadius: 18, padding: 15 },
  reasonGroupTitle: { fontSize: 17, lineHeight: 22, fontWeight: '700', marginBottom: 8 },
  outcomeReason: { paddingVertical: 13, borderTopWidth: StyleSheet.hairlineWidth },
  outcomeReasonHeading: { gap: 4 },
  reasonWeight: { fontSize: 11, lineHeight: 15 },
  componentRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 9, marginTop: 8 },
  componentDot: { width: 7, height: 7, borderRadius: 4, marginTop: 8 },
  reasonFootnote: { fontSize: 12, lineHeight: 18 },
});
