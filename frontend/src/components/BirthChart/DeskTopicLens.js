import React, { useEffect, useMemo, useRef, useState } from 'react';
import { apiService } from '../../services/apiService';
import { formatTopicEvidence } from './topicEvidenceFormatters';
import './DeskTopicLens.css';

const SECTIONS = [
  ['overview', 'Overview'],
  ['promise', 'Natal promise'],
  ['timing', 'Timing'],
  ['why', 'Why'],
];

const chartIdFrom = (data) => data?.chart_id || data?.birth_chart_id || data?.id || null;
const isoDate = (value) => {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return new Date().toISOString().slice(0, 10);
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 10);
};
const humanize = (value) => String(value || '—').replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
const sentenceCase = (value) => {
  const text = String(value || '').replaceAll('_', ' ').trim();
  return text ? `${text.charAt(0).toUpperCase()}${text.slice(1)}` : '—';
};
const dateLabel = (value) => {
  if (!value) return '—';
  const parsed = new Date(`${String(value).slice(0, 10)}T12:00:00`);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
};
const dateRange = (start, end) => start === end ? dateLabel(start) : `${dateLabel(start)} – ${dateLabel(end)}`;
const periodStatus = (group, asOf) => {
  if (group.start_date <= asOf && group.end_date >= asOf) return 'Current period';
  return group.end_date < asOf ? 'Past period' : 'Upcoming period';
};
const initiallySelectedGroup = (groups, asOf) => {
  const current = groups.find((group) => group.start_date <= asOf && group.end_date >= asOf);
  if (current) return current;
  const upcoming = groups.find((group) => group.start_date > asOf);
  return upcoming || groups[groups.length - 1] || null;
};
const concentrationWithinGroup = (window, group) => (window?.key_concentration_phases || []).find(
  (phase) => phase.start_date <= group.end_date && phase.end_date >= group.start_date,
);
const ordinal = (value) => {
  const number = Number(value);
  if (number === 1) return '1st';
  if (number === 2) return '2nd';
  if (number === 3) return '3rd';
  return `${number}th`;
};
const dashaPermissionText = (rows = []) => rows.filter((row) => row.matched).map((row) => {
  const reasons = [];
  if (row.direct_finding_planet) reasons.push('carries this natal pattern');
  if (row.associated_finding_planets?.length) reasons.push(`is joined to ${row.associated_finding_planets.join(', ')}, which carries this pattern`);
  if (row.dispositor_finding_planets?.length) reasons.push(`acts through sign lord ${row.dispositor}, joined to ${row.dispositor_finding_planets.join(', ')}`);
  if (row.nakshatra_lord_finding_planets?.length) reasons.push(`acts through nakshatra lord ${row.nakshatra_lord}, linked with ${row.nakshatra_lord_finding_planets.join(', ')}`);
  if (row.connected_houses?.length) reasons.push(`rules ${row.connected_houses.map((house) => `H${house}`).join(', ')}`);
  if (row.aspected_relevant_houses?.length) reasons.push(`aspects ${row.aspected_relevant_houses.map((house) => `H${house}`).join(', ')}`);
  if (row.manifestation_houses?.length) reasons.push(`activates ${row.manifestation_houses.map((house) => `H${house}`).join(', ')} for treatment, intervention or recovery`);
  return `${row.planet} ${humanize(row.level)} ${reasons.join(' and ') || 'repeats the health pattern'}`;
}).join('. ');
const transitConfirmationText = (activation = {}) => {
  const houseParts = (activation.houses || []).flatMap((house) => (house.transit_activators || []).map((row) => (
    row.mode === 'occupation'
      ? `${row.planet} occupies H${house.house}`
      : `${row.planet} aspects H${house.house} by its ${ordinal(row.aspect_number)} aspect`
  )));
  const contactParts = (activation.decisive_contacts || []).map((row) => (
    `${row.transit_planet} ${row.aspect_number === 1 ? 'crosses' : `aspects by its ${ordinal(row.aspect_number)}`} natal ${row.natal_planet}`
  ));
  const bridgeParts = (activation.structural_bridges || []).map((row) => (
    row.aspect_number === 1
      ? `${row.structural_planet} joins transit ${row.trigger_planet} while ${row.trigger_planet} activates natal ${row.natal_planet}`
      : `${row.structural_planet} aspects transit ${row.trigger_planet} by its ${ordinal(row.aspect_number)} aspect while ${row.trigger_planet} activates natal ${row.natal_planet}`
  ));
  const refinementParts = (activation.refinement_transit_activations || []).map((row) => (
    `${row.transit_planet} is also transiting H${row.target_house}`
  ));
  const statements = [...houseParts, ...contactParts, ...bridgeParts, ...refinementParts];
  return statements.length ? `${statements.join('. ')}.` : 'The sustained transits repeat the natal health pattern.';
};
const shortPeriodText = (rows = []) => rows.filter((row) => row.matched).map((row) => {
  const links = [];
  if (row.natal_house) links.push(`is natally placed in H${row.natal_house}`);
  if (row.connected_houses?.length) links.push(`rules ${row.connected_houses.map((house) => `H${house}`).join(', ')}`);
  if (row.aspected_relevant_houses?.length) links.push(`aspects ${row.aspected_relevant_houses.map((house) => `H${house}`).join(', ')}`);
  return `${row.planet} ${humanize(row.level)} (${dateRange(row.start, row.end)}) ${links.join(' and ') || 'repeats this pattern'}`;
}).join('. ');
const d30ConfirmationText = (confirmation = {}) => [
  ...(confirmation.anatomical_links || []),
  ...(confirmation.intervention_markers || []),
  ...(confirmation.pressure_factors || []),
  ...(confirmation.protective_factors || []),
].map((row) => row.meaning).filter(Boolean).join(' ');

function EvidenceList({ title, items, tone = '' }) {
  if (!items?.length) return null;
  return (
    <section className={`dtl__evidence dtl__evidence--${tone}`}>
      <h4>{title}</h4>
      <ul>{items.map((item, index) => <li key={`${title}-${index}`}>{formatTopicEvidence(item)}</li>)}</ul>
    </section>
  );
}

function FindingCard({ finding, expanded, onToggle }) {
  return (
    <article className={`dtl__finding${expanded ? ' is-open' : ''}`}>
      <button type="button" className="dtl__finding-head" onClick={onToggle} aria-expanded={expanded}>
        <span>
          <em>{humanize(finding.evidence_grade)} evidence</em>
          <strong>{finding.title}</strong>
          <small>{finding.body_zones?.join(' · ') || finding.claim_type?.replaceAll('_', ' ')}</small>
        </span>
        <i aria-hidden>{expanded ? '−' : '+'}</i>
      </button>
      {expanded ? (
        <div className="dtl__finding-detail">
          <p>{finding.description}</p>
          <div className="dtl__facts">
            {finding.planets?.length ? <span><b>Planets</b>{finding.planets.join(', ')}</span> : null}
            {finding.houses?.length ? <span><b>Houses</b>{finding.houses.map((house) => `H${house}`).join(', ')}</span> : null}
            <span><b>Timing</b>{finding.eligible_for_timing ? 'Eligible natal pattern' : 'Natal context only'}</span>
          </div>
          <div className="dtl__factor-grid">
            <EvidenceList title="What establishes this" items={finding.supporting_rules} tone="support" />
            <EvidenceList title="Protective factors" items={finding.protective_rules} tone="protect" />
            <EvidenceList title="Pressure or qualification" items={finding.pressure_rules} tone="pressure" />
            <EvidenceList title="Capacity modifiers" items={finding.capacity_modifiers} />
            <EvidenceList
              title="D30 severity confirmation"
              items={[
                ...(finding.d30_confirmation?.anatomical_links || []),
                ...(finding.d30_confirmation?.pressure_factors || []),
                ...(finding.d30_confirmation?.protective_factors || []),
              ]}
            />
          </div>
        </div>
      ) : null}
    </article>
  );
}

function TimingDetail({ group, onInspectDate }) {
  const [selectedId, setSelectedId] = useState(group?.windows?.[0]?.finding_id || null);
  useEffect(() => setSelectedId(group?.windows?.[0]?.finding_id || null), [group]);
  if (!group) return <div className="dtl__empty">Choose a period to inspect its health pattern and activation chain.</div>;
  const window = group.windows?.find((row) => row.finding_id === selectedId) || group.windows?.[0];
  const detail = window?.detail || {};
  const activation = detail.activation_summary || {};
  const concentration = concentrationWithinGroup(window, group);
  return (
    <article className="dtl__timing-detail">
      <header>
        <div><em>{humanize(detail.judgment || window?.phase || 'active period')}</em><h3>{window?.label}</h3></div>
        <strong>{dateRange(window?.start_date, window?.end_date)}</strong>
      </header>
      {concentration ? <p className="dtl__peak-callout"><b>Key concentration</b>{dateRange(concentration.start_date, concentration.end_date)}</p> : null}
      {group.windows?.length > 1 ? (
        <div className="dtl__timing-finding-tabs">
          {group.windows.map((row) => <button type="button" key={row.finding_id} className={row.finding_id === window?.finding_id ? 'is-active' : ''} onClick={() => setSelectedId(row.finding_id)}>{row.label}</button>)}
        </div>
      ) : null}
      <section className="dtl__causal-chain">
        <h4>Why this pattern is active in this period</h4>
        <div className="dtl__causal-step"><b>1</b><span><strong>Why this health area</strong><small>{detail.natal_reasons?.[0] || `${window?.label} is already established in the natal Health judgment.`}</small></span></div>
        <div className="dtl__causal-step"><b>2</b><span><strong>MD–AD–PD permission</strong><small>{dashaPermissionText(detail.dasha_chain) || 'No matched chain supplied'}</small></span></div>
        <div className="dtl__causal-step"><b>3</b><span><strong>Transit confirmation</strong><small>{transitConfirmationText(activation)}</small></span></div>
        {d30ConfirmationText(detail.d30_confirmation) ? <div className="dtl__causal-step"><b>D30</b><span><strong>Severity and intervention confirmation</strong><small>{d30ConfirmationText(detail.d30_confirmation)}</small></span></div> : null}
        {(detail.refinement_dasha_chain || []).some((row) => row.matched) ? <div className="dtl__causal-step"><b>4</b><span><strong>What narrows it to these dates</strong><small>{shortPeriodText(detail.refinement_dasha_chain)}.</small></span></div> : null}
        {activation.specificity_reasons?.length ? <div className="dtl__causal-step dtl__causal-step--conclusion"><b>✓</b><span><strong>Why this becomes the leading indication</strong><small>{activation.specificity_reasons.map(sentenceCase).join(' · ')}</small></span></div> : null}
      </section>
      {(window?.lower_dasha_phases?.length || window?.sun_phases?.length || window?.active_dasha_transit_phases?.length || window?.moon_peak_dates?.length) ? (
        <section className="dtl__refinements">
          <h4>Stronger phases within this period</h4>
          {window.lower_dasha_phases?.map((phase, index) => <p key={`dasha-${phase.level}-${phase.planet}-${index}`}>{humanize(phase.level)} {phase.planet} concentrates the established pattern · {dateRange(phase.start_date, phase.end_date)}</p>)}
          {window.sun_phases?.map((phase, index) => <p key={`sun-${index}`}>Sun concentration · {dateRange(phase.start_date, phase.end_date)}</p>)}
          {window.active_dasha_transit_phases?.map((phase, index) => <p key={`dasha-transit-${index}`}>Active dasha planets make an exact natal contact · {dateRange(phase.start_date, phase.end_date)}</p>)}
          {window.moon_peak_dates?.map((day) => <p key={day}>Moon adds a brief daily trigger · {dateLabel(day)}</p>)}
        </section>
      ) : null}
      <details className="dtl__technical">
        <summary>Show house-by-house activation</summary>
        {(activation.houses || []).map((house) => (
          <div key={house.house}>
            <strong>H{house.house}{house.confirmed_by_both ? ' · confirmed by both' : ''}</strong>
            <span>{(house.dasha_activators || []).map((row) => `${row.planet} ${String(row.mode || '').replaceAll('_', ' ')}`).join(' · ')}</span>
            <span>{(house.transit_activators || []).map((row) => `${row.planet} ${String(row.mode || '').replaceAll('_', ' ')}`).join(' · ')}</span>
          </div>
        ))}
      </details>
      <button type="button" className="dtl__inspect" onClick={() => onInspectDate?.(new Date(`${window?.representative_date || window?.start_date}T12:00:00`))}>Inspect this period on the Desk</button>
    </article>
  );
}

export default function DeskTopicLens({
  topicId,
  birthData,
  chartData,
  asOfDate,
  calculationProfile,
  onInspectDate,
  compact = false,
}) {
  const [section, setSection] = useState('overview');
  const [judgment, setJudgment] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expandedFinding, setExpandedFinding] = useState(null);
  const [timingDays, setTimingDays] = useState(30);
  const [timingStartDate, setTimingStartDate] = useState(() => isoDate(asOfDate));
  const [timing, setTiming] = useState(null);
  const [timingLoading, setTimingLoading] = useState(false);
  const [timingError, setTimingError] = useState('');
  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [broadWindows, setBroadWindows] = useState(null);
  const [broadLoading, setBroadLoading] = useState(false);
  const [broadError, setBroadError] = useState('');
  const timingRequestRef = useRef(0);
  const birthChartId = chartIdFrom(birthData);
  const asOf = isoDate(asOfDate);
  const timingStart = timingStartDate || asOf;
  const timingContextKey = `${topicId || ''}:${birthChartId || ''}:${birthData?.date || ''}:${birthData?.time || ''}`;

  useEffect(() => {
    timingRequestRef.current += 1;
    setTimingStartDate(asOf);
    setTimingDays(30);
    setTiming(null);
    setTimingError('');
    setSelectedGroupId(null);
  }, [timingContextKey]);

  useEffect(() => {
    let cancelled = false;
    if (!topicId || topicId === 'whole_chart' || !birthData || !chartData) return undefined;
    setLoading(true);
    setError('');
    setJudgment(null);
    setTiming(null);
    setBroadWindows(null);
    setBroadError('');
    apiService.getParashariTopicJudgment({ topicId, birthChartId, birthData, chartData, asOf, calculationProfile })
      .then((result) => { if (!cancelled) setJudgment(result); })
      .catch((requestError) => {
        if (cancelled) return;
        const detail = requestError?.response?.data?.detail;
        setError(detail?.message || (typeof detail === 'string' ? detail : requestError?.message) || 'Topic Lens could not be calculated.');
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [topicId, birthChartId, birthData, chartData, asOf, calculationProfile]);

  const loadTiming = () => {
    if (timingLoading) return;
    const requestId = timingRequestRef.current + 1;
    timingRequestRef.current = requestId;
    setTimingLoading(true);
    setTimingError('');
    apiService.getParashariTopicTiming({ topicId, birthChartId, birthData, chartData, startDate: timingStart, days: timingDays, calculationProfile })
      .then((result) => {
        if (timingRequestRef.current !== requestId) return;
        setTiming(result);
        setSelectedGroupId(initiallySelectedGroup(result?.result?.period_groups || [], timingStart)?.group_id || null);
      })
      .catch((requestError) => {
        if (timingRequestRef.current !== requestId) return;
        const detail = requestError?.response?.data?.detail;
        setTimingError(detail?.message || (typeof detail === 'string' ? detail : requestError?.message) || 'Timing could not be calculated.');
      })
      .finally(() => setTimingLoading(false));
  };

  const changeTimingStart = (value) => {
    if (!value || value === timingStartDate) return;
    timingRequestRef.current += 1;
    setTimingStartDate(value);
    setTiming(null);
    setTimingError('');
    setSelectedGroupId(null);
  };

  const changeTimingRange = (days) => {
    if (days === timingDays) return;
    timingRequestRef.current += 1;
    setTimingDays(days);
    setTiming(null);
    setTimingError('');
    setSelectedGroupId(null);
  };

  const loadBroadWindows = () => {
    if (broadLoading) return;
    setBroadLoading(true);
    setBroadError('');
    apiService.getEventWindows({
      birthChartId,
      birthData,
      eventKey: 'health',
      year: Number(asOf.slice(0, 4)),
      includeDeveloping: false,
      calculationProfile,
    }).then(setBroadWindows).catch((requestError) => {
      const detail = requestError?.response?.data?.detail;
      setBroadError(detail?.message || (typeof detail === 'string' ? detail : requestError?.message) || 'Broader windows could not be calculated.');
    }).finally(() => setBroadLoading(false));
  };

  useEffect(() => {
    if (section === 'timing' && !timing && !timingLoading && judgment) loadTiming();
  }, [section, timing, timingLoading, judgment, timingDays, timingStart]);

  const groups = timing?.result?.period_groups || [];
  const selectedGroup = useMemo(() => groups.find((group) => group.group_id === selectedGroupId) || groups[0] || null, [groups, selectedGroupId]);
  const foundation = judgment?.raw_sections?.vitality_foundation || {};
  const sixth = judgment?.raw_sections?.sixth_house_chain || {};

  if (loading) return <div className="dtl__status"><span className="dtl__spinner" /><strong>Building the Health judgment</strong><small>Reading constitution, protection and established natal susceptibilities.</small></div>;
  if (error) return <div className="dtl__status dtl__status--error"><strong>Health Topic Lens is unavailable</strong><small>{error}</small></div>;
  if (!judgment) return null;

  return (
    <div className={`dtl${compact ? ' dtl--compact' : ''}`}>
      <header className="dtl__hero">
        <div>
          <em>Health · Topic Lens</em>
          <h2>{judgment.natal_promise?.headline}</h2>
          <p>{judgment.natal_promise?.summary}</p>
        </div>
        <div className="dtl__hero-stats">
          <span><b>{judgment.natal_promise?.finding_count || 0}</b> natal patterns</span>
          <span><b>{judgment.natal_promise?.timing_eligible_count || 0}</b> timing eligible</span>
        </div>
      </header>

      <nav className="dtl__nav" role="tablist" aria-label="Health judgment sections">
        {SECTIONS.map(([key, label]) => <button type="button" role="tab" aria-selected={section === key} className={section === key ? 'is-active' : ''} onClick={() => setSection(key)} key={key}>{label}</button>)}
      </nav>

      <div className="dtl__body">
        {section === 'overview' ? (
          <div className="dtl__overview">
            <section className="dtl__foundation">
              <em>Constitutional foundation</em>
              <h3>{foundation.ascendant_sign || '—'} Lagna · {foundation.ascendant_lord || '—'} is the Lagna lord</h3>
              <div className="dtl__facts">
                <span><b>Lagna lord</b>{foundation.ascendant_lord_house ? `House ${foundation.ascendant_lord_house}` : '—'}</span>
                <span><b>Sun</b>{foundation.sun_house ? `House ${foundation.sun_house}` : '—'}</span>
                <span><b>Moon</b>{foundation.moon_house ? `House ${foundation.moon_house}` : '—'}</span>
              </div>
              {sixth.sixth_house_sign ? <p>The sixth house contains {sixth.sixth_house_sign}, ruled by {sixth.sixth_lord || '—'}. Its sign, lord and related placements help identify the body areas shown below.</p> : null}
            </section>
            <div className="dtl__factor-grid dtl__factor-grid--summary">
              <EvidenceList title="Protection present" items={judgment.protective_factors} tone="protect" />
              <EvidenceList title="Pressure or qualification" items={judgment.obstructing_factors} tone="pressure" />
            </div>
            <section className="dtl__top-findings">
              <div className="dtl__section-heading"><div><em>Established natal patterns</em><h3>What deserves closer study</h3></div><button type="button" onClick={() => setSection('promise')}>View all</button></div>
              {(judgment.overview_body_areas || []).length ? <div className="dtl__overview-group"><h4>Body areas that may need extra care</h4>{judgment.overview_body_areas.slice(0, compact ? 1 : 2).map((finding) => <FindingCard key={finding.evidence_id} finding={finding} expanded={expandedFinding === finding.evidence_id} onToggle={() => setExpandedFinding((current) => current === finding.evidence_id ? null : finding.evidence_id)} />)}</div> : null}
              {(judgment.overview_named_patterns || []).length ? <div className="dtl__overview-group"><h4>Specific chart patterns</h4>{judgment.overview_named_patterns.slice(0, 2).map((finding) => <FindingCard key={finding.evidence_id} finding={finding} expanded={expandedFinding === finding.evidence_id} onToggle={() => setExpandedFinding((current) => current === finding.evidence_id ? null : finding.evidence_id)} />)}</div> : null}
              {!(judgment.overview_body_areas || []).length && !(judgment.overview_named_patterns || []).length ? (judgment.primary_contributors || []).slice(0, compact ? 3 : 4).map((finding) => <FindingCard key={finding.evidence_id} finding={finding} expanded={expandedFinding === finding.evidence_id} onToggle={() => setExpandedFinding((current) => current === finding.evidence_id ? null : finding.evidence_id)} />) : null}
            </section>
          </div>
        ) : null}

        {section === 'promise' ? (
          <section className="dtl__promise">
            <div className="dtl__section-heading"><div><em>Natal promise</em><h3>Susceptibilities timing is allowed to activate</h3></div></div>
            <p className="dtl__section-copy">These findings come from the natal chart. A Dasha or transit can concentrate an eligible pattern, but cannot introduce a new disease indication by itself.</p>
            {(judgment.possible_manifestations || []).map((finding) => <FindingCard key={finding.evidence_id} finding={finding} expanded={expandedFinding === finding.evidence_id} onToggle={() => setExpandedFinding((current) => current === finding.evidence_id ? null : finding.evidence_id)} />)}
          </section>
        ) : null}

        {section === 'timing' ? (
          <section className="dtl__timing">
            <header className="dtl__timing-toolbar">
              <div><em>Periods from a chosen date</em><h3>When an established pattern becomes active</h3><small>Choose any starting date, then calculate the following 30, 60 or 90 days.</small></div>
              <div className="dtl__timing-controls">
                <label className="dtl__date-control">
                  <span>Starting date</span>
                  <input type="date" value={timingStart} onChange={(event) => changeTimingStart(event.target.value)} aria-label="Health timing starting date" />
                </label>
                <div className="dtl__range-control" role="group" aria-label="Health timing range">
                  {[[30, '30 days'], [60, '60 days'], [90, '90 days']].map(([days, label]) => <button type="button" className={timingDays === days ? 'is-active' : ''} onClick={() => changeTimingRange(days)} key={days}>{label}</button>)}
                </div>
              </div>
            </header>
            {timingLoading ? <div className="dtl__status"><span className="dtl__spinner" /><strong>Calculating health periods</strong><small>Using only natal findings that passed the Health Blueprint timing gate.</small></div> : null}
            {timingError ? <div className="dtl__status dtl__status--error"><strong>Timing is unavailable</strong><small>{timingError}</small><button type="button" onClick={loadTiming}>Try again</button></div> : null}
            {!timingLoading && timing && !groups.length ? <div className="dtl__empty">No period in this range passed both three-level Dasha permission and sustained transit confirmation. The engine did not generate a fallback window.</div> : null}
            {!timingLoading && groups.length ? (
              <div className="dtl__timing-layout">
                <div className="dtl__period-list">{groups.map((group) => { const concentration = concentrationWithinGroup(group.windows?.[0], group); return <button type="button" key={group.group_id} className={selectedGroup?.group_id === group.group_id ? 'is-active' : ''} onClick={() => setSelectedGroupId(group.group_id)}><em>{periodStatus(group, asOf)} · {humanize(timing.result.legend?.[String(group.activation_level)])}</em><strong>{dateRange(group.start_date, group.end_date)}</strong>{concentration ? <b>Key concentration: {dateRange(concentration.start_date, concentration.end_date)}</b> : null}<span>{group.windows.map((row) => row.label).join(' · ')}</span></button>; })}</div>
                <TimingDetail group={selectedGroup} onInspectDate={onInspectDate} />
              </div>
            ) : null}
            {timing?.result?.claim_policy ? <p className="dtl__policy-note">The activation level describes astrological repetition, not the probability or severity of illness. MD–AD–PD establish permission; Sookshma and Prana may refine an existing window but cannot create one.</p> : null}
            <details className="dtl__broad-search">
              <summary>Advanced · broader health-attention window search</summary>
              <p>This reuses the Desk's event-window engine to find broader periods involving health attention, treatment, rest or recovery. It does not name a disease and remains separate from the condition-specific periods above.</p>
              {!broadWindows && !broadLoading ? <button type="button" onClick={loadBroadWindows}>Search {asOf.slice(0, 4)}</button> : null}
              {broadLoading ? <span>Evaluating the year's MD–AD–PD and transit windows…</span> : null}
              {broadError ? <span className="dtl__broad-error">{broadError}</span> : null}
              {broadWindows ? (
                <div className="dtl__broad-results">
                  <strong>{broadWindows.qualified_windows} broader {broadWindows.qualified_windows === 1 ? 'window' : 'windows'}</strong>
                  {(broadWindows.windows || []).map((window) => (
                    <button type="button" key={window.window_id} onClick={() => onInspectDate?.(new Date(`${window.inspection_date || window.start_date}T12:00:00`))}>
                      <span><b>{window.classification_label}</b><small>{dateRange(window.start_date, window.end_date)} · {window.dasha?.mahadasha} → {window.dasha?.antardasha} → {window.dasha?.pratyantardasha}</small></span><i>Inspect →</i>
                    </button>
                  ))}
                </div>
              ) : null}
            </details>
          </section>
        ) : null}

        {section === 'why' ? (
          <section className="dtl__why">
            <div className="dtl__section-heading"><div><em>Auditable basis</em><h3>How the judgment was formed</h3></div></div>
            {(judgment.rule_trace || []).map((trace) => (
              <details key={trace.evidence_id} className="dtl__rule">
                <summary><span><em>Finding</em><strong>{trace.title}</strong></span><i>+</i></summary>
                <div className="dtl__factor-grid">
                  <EvidenceList title="Rules and chart evidence" items={trace.supporting_rules} tone="support" />
                  <EvidenceList title="Protection" items={trace.protective_rules} tone="protect" />
                  <EvidenceList title="Pressure" items={trace.pressure_rules} tone="pressure" />
                  <EvidenceList title="Capacity modifiers" items={trace.capacity_modifiers} />
                </div>
              </details>
            ))}
            {judgment.source_references?.length ? <EvidenceList title="Classical references supplied by matched rules" items={judgment.source_references} /> : null}
            <section className="dtl__method">
              <h4>Method boundaries</h4>
              <p>Provider: {judgment.provider?.engine_version}</p>
              {(judgment.raw_sections?.limitations || []).map((line) => <p key={line}>{line}</p>)}
            </section>
          </section>
        ) : null}
      </div>
    </div>
  );
}
