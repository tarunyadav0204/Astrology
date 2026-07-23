import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import { useAstrology } from '../../context/AstrologyContext';
import { apiService } from '../../services/apiService';
import '../Analysis/AnalysisDetailPage.css';
import './ActivationExplorerPage.css';

const HOUSE_LABELS = {
  1: 'Self, body and direction',
  2: 'Savings, family, speech and face/mouth',
  3: 'Effort, skills and communication',
  4: 'Home, property and mother',
  5: 'Children, learning and creativity',
  6: 'Work, health and obligations',
  7: 'Partnership and agreements',
  8: 'Change and shared resources',
  9: 'Father, guidance and fortune',
  10: 'Career and public duty',
  11: 'Gains, networks and fulfilment',
  12: 'Expense, retreat and release',
};

const STATE_LABELS = {
  fully_reinforced: 'Strongly active',
  dasha_transit_activated: 'Active now',
  dasha_connected: 'Period connected',
  transit_only: 'Background influence',
  dormant: 'Not active',
};

const STATE_EXPLANATIONS = {
  fully_reinforced: 'Your birth chart, current period and transits all point to this house',
  dasha_transit_activated: 'Your current period and transits both activate this house',
  dasha_connected: 'Your current period connects here, but there is no strong transit trigger yet',
  transit_only: 'A transit is touching this house, but your current period does not strongly support an event',
  dormant: 'This house is not drawing significant attention now',
};

const OUTCOME_LABELS = {
  supportive: 'Constructive results are more likely',
  mixed: 'Both progress and pressure are possible',
  challenging: 'Pressure, delay or obstacles are more likely',
  neutral: 'The result direction is not yet clear',
};

const BAND_LABELS = {
  strong: 'Strong chart agreement',
  moderate: 'Moderate chart agreement',
  insufficient: 'Not enough chart support',
};

const SYNTHESIS_STRENGTH_LABELS = {
  high: 'Strong chart agreement',
  well_supported: 'Good chart agreement',
  moderate: 'Developing chart theme',
};

const subjectContextLabel = (subject) => (
  subject === 'self' ? 'For you' : `May involve your ${subject}`
);

const STATE_ORDER = {
  fully_reinforced: 5,
  dasha_transit_activated: 4,
  dasha_connected: 3,
  transit_only: 2,
  dormant: 1,
};

const localToday = () => {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
};

const formatDate = (value, options = { day: 'numeric', month: 'short' }) => {
  if (!value) return '—';
  const parsed = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  return Number.isNaN(parsed.getTime())
    ? String(value)
    : new Intl.DateTimeFormat('en-IN', options).format(parsed);
};

const sentence = (value) => String(value || '')
  .replaceAll('_', ' ')
  .replace(/\b\w/g, (letter) => letter.toUpperCase());

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
    compound_friendship_with_event_house_lord: `${planet} has a ${sentence(facts.compound_relation || 'declared')} relationship with the house lord ${facts.house_lord || '—'}.`,
    natal_conjunction_association: `${planet} is conjunct ${facts.associated_planet || 'another planet'} in the natal chart.`,
    natal_aspect_association: `${planet} receives the natal aspect of ${facts.associated_planet || 'another planet'}.`,
    badhaka_lord_active: `${planet}, the Badhaka lord, is active in the dasha.`,
    yogi_lord_active: `${planet}, the Yogi lord, is active in the dasha.`,
    avayogi_lord_active: `${planet}, the Avayogi lord, is active in the dasha.`,
    natal_gandanta: `${planet} is in Gandanta in the natal chart.`,
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

const unique = (items) => [...new Set(items.filter(Boolean))];

const chartIdFrom = (birthData) => birthData?.chart_id || birthData?.birth_chart_id || birthData?.id || null;

const ActivationExplorerPage = ({ user, onLogout, onAdminClick, onLogin }) => {
  const navigate = useNavigate();
  const { birthData, chartData } = useAstrology();
  const [showBirthModal, setShowBirthModal] = useState(false);
  const [asOf, setAsOf] = useState(localToday);
  const [draftDate, setDraftDate] = useState(localToday);
  const [horizonDays, setHorizonDays] = useState(90);
  const [draftHorizonDays, setDraftHorizonDays] = useState(90);
  const [result, setResult] = useState(null);
  const [selectedHouseNumber, setSelectedHouseNumber] = useState(null);
  const [selectedWindowStart, setSelectedWindowStart] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showOutcomeReasons, setShowOutcomeReasons] = useState(false);
  const [activeTab, setActiveTab] = useState('houses');
  const hasChart = Boolean(birthData && chartData);

  const loadExplorer = useCallback(async () => {
    if (!user || !birthData) return;
    setLoading(true);
    setError('');
    try {
      const data = await apiService.getActivationExplorer({
        birthChartId: chartIdFrom(birthData),
        birthData,
        asOf,
        horizonDays,
        trace: false,
      });
      setResult(data);
      setSelectedWindowStart(null);
    } catch (requestError) {
      setResult(null);
      setError(
        requestError?.response?.data?.detail
        || requestError?.message
        || 'We could not read this chart right now. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  }, [asOf, birthData, horizonDays, user]);

  useEffect(() => {
    loadExplorer();
  }, [loadExplorer]);

  const currentHouseRows = useMemo(() => {
    const rows = result?.house_activations || [];
    const containing = rows.filter((row) => row.window?.start_date <= asOf && row.window?.end_date >= asOf);
    if (containing.length) return containing;
    const firstStart = rows[0]?.window?.start_date;
    return firstStart ? rows.filter((row) => row.window?.start_date === firstStart) : [];
  }, [asOf, result]);

  useEffect(() => {
    if (!currentHouseRows.length) return;
    const currentSelectionExists = currentHouseRows.some((row) => row.house === selectedHouseNumber);
    if (currentSelectionExists) return;
    const strongest = [...currentHouseRows].sort((left, right) => {
      const stateDifference = (STATE_ORDER[right.state] || 0) - (STATE_ORDER[left.state] || 0);
      if (stateDifference) return stateDifference;
      return (right.activation?.independent_confirmations || 0) - (left.activation?.independent_confirmations || 0);
    })[0];
    setSelectedHouseNumber(strongest?.house || 1);
  }, [currentHouseRows, selectedHouseNumber]);

  const currentSelectedHouse = currentHouseRows.find((row) => row.house === selectedHouseNumber) || currentHouseRows[0];
  const selectedHouseWindows = useMemo(() => (result?.house_activations || [])
    .filter((row) => row.house === currentSelectedHouse?.house)
    .sort((left, right) => left.window.start_date.localeCompare(right.window.start_date)),
  [currentSelectedHouse?.house, result]);
  const selectedHouse = selectedHouseWindows.find((row) => row.window?.start_date === selectedWindowStart)
    || currentSelectedHouse;
  const gridReferenceDate = selectedWindowStart || asOf;
  const displayedHouseRows = useMemo(() => {
    if (!selectedWindowStart) return currentHouseRows;
    return (result?.house_activations || []).filter((row) => (
      row.window?.start_date <= gridReferenceDate && row.window?.end_date >= gridReferenceDate
    ));
  }, [currentHouseRows, gridReferenceDate, result, selectedWindowStart]);
  const natalPromise = (result?.natal_promises || []).find((row) => row.house === selectedHouse?.house);
  const currentWindow = selectedHouse?.window || currentHouseRows[0]?.window;

  const currentCandidates = useMemo(() => (result?.candidates || []).filter((candidate) => (
    candidate.window?.start_date === currentWindow?.start_date
    && candidate.window?.end_date === currentWindow?.end_date
  )), [currentWindow?.end_date, currentWindow?.start_date, result]);

  const selectedCandidates = useMemo(() => currentCandidates.filter((candidate) => (
    candidate.native_houses || []
  ).includes(selectedHouse?.house)), [currentCandidates, selectedHouse?.house]);

  const alternatives = useMemo(() => {
    const rows = selectedCandidates.flatMap((candidate) => candidate.resolution?.interpretation_alternatives || []);
    const seen = new Set();
    return rows.filter((row) => (
      row.focus_native_houses || row.native_houses || []
    ).includes(selectedHouse?.house)).filter((row) => {
      const key = `${row.subject}:${row.signature_key || row.label}:${(row.native_houses || []).join('-')}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    }).slice(0, 12);
  }, [selectedCandidates, selectedHouse?.house]);

  const manifestationGroups = useMemo(() => alternatives.reduce((groups, alternative) => {
    const existing = groups.find((group) => group.subject === alternative.subject);
    if (existing) existing.items.push(alternative);
    else groups.push({ subject: alternative.subject, items: [alternative] });
    return groups;
  }, []), [alternatives]);

  const chartManifestations = result?.chart_manifestations || [];

  const dashaWindows = useMemo(() => {
    const seen = new Set();
    return (result?.house_activations || []).filter((row) => {
      const key = `${row.window?.start_date}:${row.window?.end_date}:${row.window?.mahadasha}:${row.window?.antardasha}:${row.window?.pratyantardasha}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    }).map((row) => row.window);
  }, [result]);

  const predictiveCount = currentHouseRows.filter((row) => !['transit_only', 'dormant'].includes(row.state)).length;
  const carriers = selectedHouse?.activation?.carrier_planets || [];
  const levels = selectedHouse?.activation?.active_dasha_levels || [];
  const directDashaConnections = unique((selectedHouse?.natal_connections || []).map(
    (row) => `${row.planet} connects by natal ${String(row.relation || '').replaceAll('_', ' ')} during the ${row.level === 'MD' ? 'major period' : row.level === 'AD' ? 'sub-period' : 'sub-sub-period'}`
  ));
  const directDashaPlanets = new Set((selectedHouse?.natal_connections || []).map((row) => row.planet));
  const cooperativeCarriers = carriers.filter((planet) => !directDashaPlanets.has(planet));
  const repeatedDashaPlanets = unique((selectedHouse?.evidence || [])
    .filter((row) => row.provider === 'transit_natal_ledger' && row.facts?.same_planet_natal_repetition)
    .map((row) => row.planet));
  const timingTransitConnections = (selectedHouse?.transit_connections || [])
    .filter((row) => row.timing_trigger)
    .map((row) => {
      const relations = (row.relations || []).map((relation) => {
        if (relation === 'occupation') return `occupying H${selectedHouse?.house}`;
        const aspectNumber = ((Number(selectedHouse?.house) - Number(row.transit_house) + 12) % 12) + 1;
        const suffix = aspectNumber === 1 ? 'st' : aspectNumber === 2 ? 'nd' : aspectNumber === 3 ? 'rd' : 'th';
        return `${aspectNumber}${suffix} aspect`;
      }).join(' and ');
      return `Transit ${row.planet} is in H${row.transit_house} and connects by ${relations}`;
    });
  const moonTriggers = (selectedHouse?.timing_triggers || []).filter((row) => row.kind === 'moon_peak');
  const sunTriggers = (selectedHouse?.timing_triggers || []).filter((row) => row.kind === 'sun_reinforcement');

  const applyControls = () => {
    if (!draftDate) return;
    if (draftDate === asOf && draftHorizonDays === horizonDays) loadExplorer();
    else {
      setAsOf(draftDate);
      setHorizonDays(draftHorizonDays);
    }
  };

  return (
    <div className="analysis-detail-page activation-explorer-page">
      <NavigationHeader
        compact
        showZodiacSelector={false}
        user={user}
        onAdminClick={onAdminClick}
        onLogout={onLogout}
        onLogin={!user ? onLogin : undefined}
        showLoginButton={!user}
        birthData={birthData}
        onCreateBirthChart={() => navigate('/ai-kundli-generator')}
        onSelectBirthChart={user ? () => setShowBirthModal(true) : () => onLogin?.()}
      />

      <main className="activation-explorer-main">
        <header className="activation-explorer-header">
          <button type="button" className="activation-explorer-back" onClick={() => navigate('/charts-dashas')}>
            <span aria-hidden>←</span> Charts &amp; Dashas
          </button>
          <div className="activation-explorer-title-row">
            <div>
              <p className="activation-explorer-kicker">Your chart, explained step by step</p>
              <h1>What’s active in your chart?</h1>
              <p>
                Understand which parts of life are drawing attention now, what they may bring, and the astrology behind them.
              </p>
            </div>
            {birthData ? (
              <button type="button" className="activation-chart-identity" onClick={() => setShowBirthModal(true)}>
                <span>{birthData.name || 'Selected chart'}</span>
                <small>{String(birthData.date || '').slice(0, 10)} · {birthData.place || 'Birth place'}</small>
                <strong>Change chart</strong>
              </button>
            ) : null}
          </div>
        </header>

        {!user ? (
          <section className="activation-state-panel">
            <span className="activation-state-icon" aria-hidden>🔐</span>
            <h2>Sign in to see what’s active</h2>
            <p>Choose a saved birth chart and explore the life areas drawing attention now.</p>
            <button type="button" className="activation-primary-button" onClick={() => onLogin?.()}>Sign in</button>
          </section>
        ) : !hasChart ? (
          <section className="activation-state-panel">
            <span className="activation-state-icon" aria-hidden>🪐</span>
            <h2>Select a birth chart first</h2>
            <p>This reading needs your real birth details before it can explain what is active.</p>
            <button type="button" className="activation-primary-button" onClick={() => setShowBirthModal(true)}>Select chart</button>
          </section>
        ) : (
          <div className="activation-explorer-content">
            <section className="activation-controls" aria-label="Calculation controls">
              <label>
                <span>View the chart from</span>
                <input type="date" value={draftDate} onChange={(event) => setDraftDate(event.target.value)} />
              </label>
              <label>
                <span>Look ahead</span>
                <select value={draftHorizonDays} onChange={(event) => setDraftHorizonDays(Number(event.target.value))}>
                  <option value={30}>30 days</option>
                  <option value={90}>90 days</option>
                  <option value={180}>180 days</option>
                </select>
              </label>
              <button type="button" className="activation-primary-button" onClick={applyControls} disabled={loading || !draftDate}>
                {loading ? 'Calculating…' : 'Recalculate'}
              </button>
            </section>

            {error ? (
              <section className="activation-error" role="alert">
                <strong>Calculation could not be completed</strong>
                <p>{error}</p>
                <button type="button" onClick={loadExplorer}>Try again</button>
              </section>
            ) : null}

            {loading && !result ? (
              <section className="activation-loading" aria-live="polite">
                <div className="activation-spinner" aria-hidden />
                <strong>Reading the chart</strong>
                <span>We’re connecting the birth chart, current planetary period, transits and timing highlights.</span>
              </section>
            ) : null}

            {result ? (
              <>
                <section className="activation-dasha-summary">
                  <div>
                    <span>Your current timing cycle</span>
                    <strong>
                      {currentWindow?.mahadasha || '—'} major period <b>→</b> {currentWindow?.antardasha || '—'} sub-period <b>→</b> {currentWindow?.pratyantardasha || '—'} sub-sub-period
                    </strong>
                  </div>
                  <div className="activation-summary-meta">
                    <span>{formatDate(currentWindow?.start_date)} – {formatDate(currentWindow?.end_date, { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                    <span>{predictiveCount} houses active now</span>
                    <span>Based on the birth chart (D1)</span>
                  </div>
                </section>

                <nav className="activation-view-toggle" aria-label="Activation explorer view">
                  <button type="button" className={activeTab === 'houses' ? 'is-active' : ''} onClick={() => setActiveTab('houses')}>
                    House by House
                  </button>
                  <button type="button" className={activeTab === 'manifestations' ? 'is-active' : ''} onClick={() => setActiveTab('manifestations')}>
                    Combined Life Themes
                  </button>
                </nav>

                {activeTab === 'houses' ? (
                  <>
                <section className="activation-timeline-section">
                  <div className="activation-section-heading">
                    <div><span>How the timing changes</span><h2>Your upcoming chart periods</h2></div>
                    <p>{formatDate(result.as_of)} – {formatDate(result.horizon_end, { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                  </div>
                  <div className="activation-timeline">
                    {dashaWindows.map((window, index) => (
                      <div className={`activation-timeline-window${index === 0 ? ' is-current' : ''}`} key={`${window.start_date}-${window.transit_signature}`}>
                        <span>{formatDate(window.start_date)} – {formatDate(window.end_date)}</span>
                        <strong>{window.mahadasha} → {window.antardasha} → {window.pratyantardasha}</strong>
                      </div>
                    ))}
                  </div>
                </section>

                <div className="activation-workspace">
                  <section className="activation-house-panel">
                    <div className="activation-section-heading activation-section-heading--compact">
                      <div><span>House-by-house view</span><h2>Where life is drawing your attention</h2></div>
                    </div>
                    <div className="activation-house-grid">
                      {Array.from({ length: 12 }, (_, index) => index + 1).map((houseNumber) => {
                        const house = displayedHouseRows.find((row) => row.house === houseNumber);
                        const selected = houseNumber === selectedHouse?.house;
                        return (
                          <button
                            type="button"
                            key={houseNumber}
                            className={`activation-house activation-house--${house?.state || 'dormant'}${selected ? ' is-selected' : ''}`}
                            onClick={() => {
                              setSelectedHouseNumber(houseNumber);
                              setSelectedWindowStart(null);
                            }}
                            aria-pressed={selected}
                            aria-label={`House ${houseNumber}, ${HOUSE_LABELS[houseNumber]}, ${STATE_LABELS[house?.state] || 'Dormant'}`}
                          >
                            <strong>H{houseNumber}</strong>
                            <span>{STATE_LABELS[house?.state] || 'Dormant'}</span>
                            <i
                              className={`activation-outcome-dot activation-outcome--${house?.outcome?.tone || 'neutral'}`}
                              aria-hidden="true"
                            />
                          </button>
                        );
                      })}
                    </div>
                    <div className="activation-legend">
                      <strong>How clearly the house is activated</strong>
                      <span><i className="legend-full" />Strongly active</span>
                      <span><i className="legend-active" />Active now</span>
                      <span><i className="legend-connected" />Period connected</span>
                      <span><i className="legend-background" />Background influence</span>
                      <strong>What kind of experience it may bring</strong>
                      <span><i className="activation-outcome--supportive" />Constructive</span>
                      <span><i className="activation-outcome--mixed" />Mixed</span>
                      <span><i className="activation-outcome--challenging" />Pressure or obstacles</span>
                      <span><i className="activation-outcome--neutral" />Unclear</span>
                    </div>
                  </section>

                  {selectedHouse ? (
                    <section className="activation-house-detail">
                      <div className="activation-selected-heading">
                        <div>
                          <span>House {selectedHouse.house}</span>
                          <h2>{HOUSE_LABELS[selectedHouse.house]}</h2>
                          <p>{STATE_EXPLANATIONS[selectedHouse.state]} · {OUTCOME_LABELS[selectedHouse.outcome?.tone]}</p>
                        </div>
                        <div className={`activation-band activation-band--${selectedHouse.activation?.band}`}>
                          {BAND_LABELS[selectedHouse.activation?.band] || 'Chart agreement unavailable'}
                        </div>
                      </div>

                      {selectedHouseWindows.length > 1 ? (
                        <div className="activation-window-picker">
                          <strong>Inspect a timing window</strong>
                          <div>
                            {selectedHouseWindows.map((row) => {
                              const active = row.window.start_date === selectedHouse?.window?.start_date;
                              return (
                                <button
                                  type="button"
                                  className={active ? 'is-active' : ''}
                                  key={`${row.window.start_date}-${row.window.end_date}`}
                                  onClick={() => setSelectedWindowStart(row.window.start_date)}
                                >
                                  {formatDate(row.window.start_date)} – {formatDate(row.window.end_date)}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ) : null}

                      <div className="activation-why">
                        <h3>Why this house matters now</h3>
                        <div className="activation-causal-chain">
                          <article>
                            <span>1</span><strong>Birth-chart foundation</strong>
                            <p>
                              {natalPromise
                                ? `${natalPromise.lord} rules this house; planets placed here: ${natalPromise.occupants?.join(', ') || 'none'}; planets aspecting it: ${natalPromise.aspecting_planets?.join(', ') || 'none'}.`
                                : 'Natal promise evidence is unavailable.'}
                            </p>
                          </article>
                          <article className={levels.length ? 'is-confirmed' : ''}>
                            <span>2</span><strong>Connection to your current period</strong>
                            <p>
                              {levels.length
                                ? `${directDashaConnections.join('; ') || 'No direct connection'}.${cooperativeCarriers.length ? ` ${cooperativeCarriers.join(', ')} also participates because it has a natal relationship with the directly connected period planet.` : ''}`
                                : 'The current major and sub-period planets do not have a strong natal connection to this house, so it remains background context.'}
                            </p>
                          </article>
                          <article className={selectedHouse.activation?.transit_reinforced ? 'is-confirmed' : ''}>
                            <span>3</span><strong>What is triggering it now</strong>
                            <p>
                              {timingTransitConnections.length
                                ? selectedHouse.activation?.natal_position_reinforced
                                  ? `${timingTransitConnections.join('; ')}. ${repeatedDashaPlanets.join(', ') || 'The active period planet'} also returns to its natal position, strengthening the timing.`
                                  : `${timingTransitConnections.join('; ')}. These transits bring attention here, although the active period planet is not also repeating its natal position.`
                                : 'No strong transit trigger was found.'}
                            </p>
                          </article>
                        </div>
                      </div>

                      <div className="activation-promise-details">
                        <h3>What the chart suggests</h3>
                        <div className="activation-fact-row">
                          <span>House lord<strong>{selectedHouse.house_lord || natalPromise?.lord || '—'}</strong></span>
                          <span>Overall direction<strong>{OUTCOME_LABELS[selectedHouse.outcome?.tone] || 'Unclear'}</strong></span>
                          <span className="activation-factor-summary">
                            Planetary influences on the result
                            <strong>{selectedHouse.outcome?.supportive_factors || 0} helpful · {selectedHouse.outcome?.mixed_factors || 0} mixed · {selectedHouse.outcome?.challenging_factors || 0} pressure</strong>
                            <button type="button" onClick={() => setShowOutcomeReasons(true)}>See what helps or adds pressure</button>
                          </span>
                          <span>Planets connecting this house to the current period<strong>{carriers.join(', ') || 'None'}</strong></span>
                        </div>
                        {natalPromise?.yogas?.length || natalPromise?.cancellations?.length ? (
                          <p className="activation-rule-note">
                            {natalPromise.yogas?.length ? `Yogas: ${natalPromise.yogas.join(', ')}. ` : ''}
                            {natalPromise.cancellations?.length ? `Cancellations: ${natalPromise.cancellations.join(', ')}.` : ''}
                          </p>
                        ) : null}
                      </div>

                      <div className="activation-results">
                        <h3>What you may notice in life</h3>
                        {manifestationGroups.length ? (
                          <div className="activation-person-groups">
                            {manifestationGroups.map((group) => (
                              <section className="activation-person-group" key={group.subject}>
                                <h4>{sentence(group.subject)}</h4>
                                <div className="activation-alternative-list">
                                  {group.items.map((alternative, index) => (
                                    <article key={`${alternative.signature_key || alternative.label}-${index}`}>
                                      <div><strong>{alternative.label}</strong></div>
                                      <p>{alternative.tone_interpretation}</p>
                                      <ul>{(alternative.manifestations || []).map((item) => <li key={item}>{item}</li>)}</ul>
                                      {alternative.subject !== 'self' ? <small>Relative houses: {(alternative.relative_houses || []).map((house) => `H${house}`).join(' + ')}</small> : null}
                                    </article>
                                  ))}
                                </div>
                              </section>
                            ))}
                          </div>
                        ) : (
                          <p className="activation-empty-copy">
                            {selectedHouse.state === 'transit_only'
                              ? 'A transit is touching this area, but the current planetary period does not support a clear life event yet.'
                              : 'This house is active, but the chart does not narrow it to a clear real-life theme in this period.'}
                          </p>
                        )}
                      </div>

                      <div className="activation-when">
                        <h3>When it can become noticeable</h3>
                        <div className="activation-trigger-grid">
                          <article><span>Main period</span><strong>{formatDate(currentWindow?.start_date)} – {formatDate(currentWindow?.end_date)}</strong><p>The broader window in which this house can express itself.</p></article>
                          <article><span>Sun highlight</span><strong>{sunTriggers.length ? `${formatDate(sunTriggers[0].start_date)} – ${formatDate(sunTriggers[sunTriggers.length - 1].end_date)}` : 'No extra highlight'}</strong><p>The Sun can make an existing theme more visible during these dates.</p></article>
                          <article><span>Moon peak dates</span><strong>{moonTriggers.length ? moonTriggers.map((trigger) => formatDate(trigger.start_date)).join(', ') : 'No short peak found'}</strong><p>Short emotional or situational peaks inside the broader period.</p></article>
                        </div>
                      </div>
                    </section>
                  ) : null}
                </div>

                  </>
                ) : (
                  <section className="chart-manifestations">
                    <div className="activation-section-heading">
                      <div><span>Your chart’s bigger story</span><h2>Life themes coming into focus</h2></div>
                      <p>These themes appear when several active houses point toward the same area of life.</p>
                    </div>
                    {chartManifestations.length ? (
                      <div className="chart-manifestation-list">
                        {chartManifestations.map((item) => (
                          <article className={`chart-manifestation-card chart-manifestation-card--${item.outcome_tone}`} key={item.manifestation_id}>
                            <header>
                              <div>
                                <span>{subjectContextLabel(item.subject)} · {sentence(item.domain)}</span>
                                <h3>{sentence(item.label)}</h3>
                              </div>
                              <strong>{SYNTHESIS_STRENGTH_LABELS[item.synthesis_strength] || 'Combination evidence available'}</strong>
                            </header>
                            <div className="chart-manifestation-meta">
                              <span>{item.window?.start_date <= asOf && item.window?.end_date >= asOf ? 'Active on selected date' : 'Upcoming window'}</span>
                              <span>{formatDate(item.window?.start_date)} – {formatDate(item.window?.end_date, { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                              <span>{OUTCOME_LABELS[item.outcome_tone] || sentence(item.outcome_tone)}</span>
                            </div>
                            <div className="chart-manifestation-houses">
                              {(item.house_roles || []).map((role) => (
                                <div key={`${role.native_house}-${role.relative_house}`}>
                                  <strong>H{role.native_house}</strong>
                                  <span>{role.role}</span>
                                  {item.subject !== 'self' ? <small>For your {item.subject}, this is House {role.relative_house}</small> : null}
                                </div>
                              ))}
                            </div>
                            <div className="chart-manifestation-alternatives">
                              <h4>What you may notice</h4>
                              <p>{item.summary}</p>
                              <ul>{(item.possibilities || []).map((possibility) => <li key={possibility}>{possibility}</li>)}</ul>
                            </div>
                            <details>
                              <summary>Why your chart points to this</summary>
                              <div className="chart-manifestation-house-reasoning">
                                {(item.house_roles || []).map((role) => (
                                  <section key={`reason-${role.native_house}-${role.relative_house}`}>
                                    <h4>House {role.native_house}: {role.role}</h4>
                                    {(role.dasha_connections || []).map((reason) => <p key={reason}>{reason}.</p>)}
                                    {(role.transit_connections || []).map((reason) => <p key={reason}>{reason}.</p>)}
                                    <p><strong>This house suggests:</strong> {OUTCOME_LABELS[role.outcome_tone] || sentence(role.outcome_tone)}</p>
                                  </section>
                                ))}
                              </div>
                              <ul>{(item.rationale || []).map((reason) => <li key={reason}>{reason}</li>)}</ul>
                              <div className="chart-manifestation-factors">
                                {[
                                  ['What helps', item.helpful_reasons || []],
                                  ['Mixed signals', item.mixed_reasons || []],
                                  ['What adds pressure', item.pressure_reasons || []],
                                ].map(([label, reasons]) => reasons.length ? (
                                  <section key={label}>
                                    <h4>{label}</h4>
                                    {reasons.map((reason, index) => (
                                      <div key={reason.independent_key || `${label}-${index}`}>
                                        <strong>{reason.planet || 'Chart factor'} · H{reason.house || '—'}</strong>
                                        {(reason.components || []).filter((component) => component.polarity !== 'neutral' || component.is_modifier).map((component) => (
                                          <p key={component.independent_key}>{reasonDescription(component)}</p>
                                        ))}
                                      </div>
                                    ))}
                                  </section>
                                ) : null)}
                              </div>
                            </details>
                          </article>
                        ))}
                      </div>
                    ) : (
                      <div className="chart-manifestation-empty">
                        <strong>No combined life theme is clear in this period</strong>
                        <p>Some individual houses may still be active, but they do not yet join into one reliable real-life story.</p>
                      </div>
                    )}
                  </section>
                )}
              </>
            ) : null}

          </div>
        )}
      </main>

      {showOutcomeReasons && selectedHouse ? (
        <div className="activation-reasons-backdrop" role="presentation" onMouseDown={() => setShowOutcomeReasons(false)}>
          <section className="activation-reasons-dialog" role="dialog" aria-modal="true" aria-labelledby="activation-reasons-title" onMouseDown={(event) => event.stopPropagation()}>
            <header>
              <div>
                <p>House {selectedHouse.house} · {OUTCOME_LABELS[selectedHouse.outcome?.tone] || 'Unclear'}</p>
                <h2 id="activation-reasons-title">Why this result?</h2>
              </div>
              <button type="button" aria-label="Close reasons" onClick={() => setShowOutcomeReasons(false)}>×</button>
            </header>
            <div className="activation-reason-columns">
              {[
                ['supportive', 'What helps', selectedHouse.outcome?.supportive_reasons || []],
                ['mixed', 'Mixed signals', selectedHouse.outcome?.mixed_reasons || []],
                ['challenging', 'What adds pressure', selectedHouse.outcome?.challenging_reasons || []],
              ].map(([tone, title, reasons]) => (
                <section key={tone} className={`activation-reason-group activation-reason-group--${tone}`}>
                  <h3>{title} <span>{reasons.length}</span></h3>
                  {reasons.length ? reasons.map((reason, index) => (
                    <article key={reason.independent_key || `${tone}-${index}`}>
                      <div><strong>{reason.planet || sentence(reason.provider)}</strong><small>{tone === 'mixed' ? 'Helps in some ways and complicates others' : tone === 'supportive' ? 'Supports this result' : 'Adds pressure'}</small></div>
                      <ul className="activation-component-list">
                        {(reason.components || []).filter((component) => component.polarity !== 'neutral' || component.is_modifier).map((component) => (
                          <li key={component.independent_key}><span className={`activation-component-dot activation-outcome--${component.polarity || 'neutral'}`} />{reasonDescription(component)}</li>
                        ))}
                      </ul>
                    </article>
                  )) : <p className="activation-empty-copy">{tone === 'supportive'
                    ? 'No planet has a net helpful result; supportive influences may still appear within Mixed planets.'
                    : tone === 'mixed'
                      ? 'No planet has both helpful and pressure influences.'
                      : 'No planet has a net pressure result.'}</p>}
                </section>
              ))}
            </div>
            <p className="activation-reasons-note">Open each planet to see the birth-chart conditions behind its influence. Related conditions are grouped so the same planet is not counted repeatedly.</p>
          </section>
        </div>
      ) : null}

      {user ? (
        <BirthFormModal
          isOpen={showBirthModal}
          onClose={() => setShowBirthModal(false)}
          onSubmit={() => setShowBirthModal(false)}
          defaultActiveTab="saved"
          title="What’s active now? — Birth chart"
          description="Choose the birth chart you want to explore."
        />
      ) : null}
    </div>
  );
};

export default ActivationExplorerPage;
