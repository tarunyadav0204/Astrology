import React, { useEffect, useMemo, useState } from 'react';
import './DeskActivationsPanel.css';
import DeskDoubleTransitBrowser from './DeskDoubleTransitBrowser';
import { apiService } from '../../services/apiService';

const PLANET_ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
};

const HOUSE_LABELS = {
  1: 'Self', 2: 'Wealth', 3: 'Effort', 4: 'Home',
  5: 'Creativity', 6: 'Service', 7: 'Partnership', 8: 'Transformation',
  9: 'Dharma', 10: 'Career', 11: 'Gains', 12: 'Release',
};

const EVENT_FOCUS_META = {
  job_change: {
    label: 'Job change',
    intro: 'Requires career + transition activation in the same dasha period. Natal wiring never vetoes the event.',
    loading: 'Calculating one strict year of dasha, transit, D10 and exact-return evidence…',
  },
  health: {
    label: 'Health',
    intro: 'Looks for health attention plus pressure, treatment or rest indicators, then assesses recovery support. This is an astrological timing aid—not a diagnosis or substitute for medical care.',
    loading: 'Calculating one strict year of dasha, transit, D30 and exact-return evidence…',
  },
};

const EVENT_HOUSE_MEANINGS = {
  job_change: {
    2: 'Salary, accumulated resources and financial continuity after the transition.',
    3: 'Initiative, applications, interviews, negotiation, movement or transfer.',
    6: 'Employment, service, duties, colleagues and the day-to-day working environment.',
    8: 'A break in continuity, restructuring, uncertainty or transformation of the existing role.',
    10: 'Profession, responsibility, authority, public role and career status.',
    11: 'Gain, fulfilment, recognition and the benefit received from the change.',
    12: 'Release, resignation, separation, remote/foreign movement or leaving the present arrangement.',
  },
  health: {
    1: 'The body, vitality and overall physical condition.',
    5: 'Recovery support and release from sixth-house difficulty.',
    6: 'Illness, treatment, health routines and the effort required to overcome a problem.',
    8: 'Acute change, chronic concern, investigation or deeper intervention.',
    11: 'Improvement, support and fulfilment of treatment.',
    12: 'Rest, withdrawal, hospitalization, isolation or sustained recovery time.',
  },
};

const HEALTH_HOUSE_LABELS = {
  1: 'Body & vitality',
  5: 'Recovery',
  6: 'Health & treatment',
  8: 'Deep intervention',
  11: 'Improvement',
  12: 'Rest & retreat',
};

function eventHouseLabel(eventKey, house) {
  return eventKey === 'health' ? (HEALTH_HOUSE_LABELS[house] || HOUSE_LABELS[house]) : HOUSE_LABELS[house];
}

const STATE_META = {
  fully_reinforced: {
    short: 'Strong',
    rank: 5,
    hint: 'Self-contact / Sun on dasha lord',
    meaning: 'House in a dasha lord’s natal portfolio, with that lord self-contacted (transit→own natal) or Sun on that lord’s natal/transit seat',
  },
  dasha_transit_activated: {
    short: 'Active',
    rank: 4,
    hint: 'Natal dasha house + transit hit',
    meaning: 'House is in a dasha lord’s natal portfolio, and that lord also occupies/aspects it in transit (without full self/Sun wake-up)',
  },
  dasha_connected: {
    short: 'Period',
    rank: 3,
    hint: 'Natal dasha portfolio only',
    meaning: 'House opened by a dasha lord’s natal portfolio (lordship / occupation / aspect) without a transit hit on the house',
  },
  transit_only: {
    short: 'Transit',
    rank: 2,
    hint: 'Transit without dasha lord',
    meaning: 'Legacy: transit contact without a dasha lord opening the house',
  },
  dormant: {
    short: 'Quiet',
    rank: 1,
    hint: 'No dasha lord opens it',
    meaning: 'No dasha lord opens this house',
  },
};

const STATE_LEGEND = [
  'fully_reinforced',
  'dasha_transit_activated',
  'dasha_connected',
  'dormant',
];

const TONE_META = {
  supportive: { short: 'Supportive', rank: 4 },
  mixed: { short: 'Mixed', rank: 3 },
  challenging: { short: 'Challenging', rank: 2 },
  neutral: { short: 'Neutral', rank: 1 },
};

const PREDICTIVE = new Set(['fully_reinforced', 'dasha_transit_activated', 'dasha_connected']);

function abbr(planet) {
  return PLANET_ABBR[planet] || String(planet || '').slice(0, 2);
}

function formatDay(value) {
  if (!value) return '—';
  const d = new Date(`${String(value).slice(0, 10)}T12:00:00`);
  if (Number.isNaN(d.getTime())) return String(value).slice(0, 10);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
}

function formatRange(start, end) {
  return `${formatDay(start)}–${formatDay(end)}`;
}

function formatMoment(value) {
  if (!value) return '';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString('en-GB', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  });
}

function confirmationMeta(row) {
  if (row.kind === 'exact_degree_return') {
    return [
      `±${row.orb_degrees}° orb`,
      `exact ${formatMoment(row.exact_at)}`,
      row.pass_sequence,
    ].filter(Boolean).join(' · ');
  }
  if (row.kind === 'exact_nakshatra_return') {
    return `${row.nakshatra_lord} ruled · natal pada ${row.natal_pada} · transit pada ${row.transit_pada}`;
  }
  if (row.kind === 'repeated_natal_relationship') {
    const suffix = row.aspect_number === 1 ? 'st' : row.aspect_number === 2 ? 'nd' : row.aspect_number === 3 ? 'rd' : 'th';
    return `Natal H${row.natal_house} → ${row.aspect_number === 1 ? 'conjunction' : `${row.aspect_number}${suffix} aspect`} → ${row.target_planet}`;
  }
  if (row.natal_house != null && row.transit_house != null) {
    return `Natal H${row.natal_house} · transit H${row.transit_house}`;
  }
  return '';
}

function boundaryLabels(changes, { hideHorizon = true } = {}) {
  return (changes || [])
    .filter((change) => {
      if (!change?.label) return false;
      if (hideHorizon && (change.kind === 'horizon_start' || change.kind === 'horizon_end')) {
        return false;
      }
      return true;
    })
    .map((change) => change.label);
}

function BoundaryReasons({ openedBy, closedBy, endDate }) {
  const opens = boundaryLabels(openedBy, { hideHorizon: true });
  const closes = boundaryLabels(closedBy, { hideHorizon: true });
  if (!opens.length && !closes.length) return null;
  return (
    <div className="desk-act__why">
      {opens.length ? (
        <span title="Why this timing slice opened">
          <em>Opens</em>
          {opens.join(' · ')}
        </span>
      ) : null}
      {closes.length ? (
        <span title={`What changes after ${formatDay(endDate)} — why this slice ends`}>
          <em>Ends after {formatDay(endDate)}</em>
          {closes.join(' · ')}
        </span>
      ) : null}
    </div>
  );
}

function asOfKey(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return '';
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function parseJumpDate(isoDay, asOfDate) {
  const [y, m, d] = String(isoDay).slice(0, 10).split('-').map(Number);
  if (!y || !m || !d) return null;
  const jump = new Date(y, m - 1, d, 12, 0, 0, 0);
  if (asOfDate instanceof Date && !Number.isNaN(asOfDate.getTime())) {
    jump.setHours(asOfDate.getHours(), asOfDate.getMinutes(), 0, 0);
  }
  return jump;
}

function dashaPath(window) {
  if (!window) return '—';
  return [window.mahadasha, window.antardasha, window.pratyantardasha]
    .filter(Boolean)
    .map(abbr)
    .join(' → ');
}

/** Calendar + dasha identity for grouping houses into one Next/Focus tile.
 *  Omit transit_signature: per-house merge hashes that differently even when
 *  start/end/MD/AD/PD match, which split e.g. H7 off an H2/H8 card. */
function windowKey(window) {
  return [
    window?.start_date,
    window?.end_date,
    window?.mahadasha,
    window?.antardasha,
    window?.pratyantardasha,
  ].join('|');
}

function stateRank(state) {
  return STATE_META[state]?.rank || 0;
}

function sortHouses(rows) {
  return [...rows].sort((a, b) => {
    const sr = stateRank(b.state) - stateRank(a.state);
    if (sr) return sr;
    const tr = (TONE_META[b.outcome?.tone]?.rank || 0) - (TONE_META[a.outcome?.tone]?.rank || 0);
    if (tr) return tr;
    return a.house - b.house;
  });
}

function nextDayIso(isoDay) {
  const [y, m, d] = String(isoDay || '').slice(0, 10).split('-').map(Number);
  if (!y || !m || !d) return '';
  const dt = new Date(y, m - 1, d + 1, 12, 0, 0, 0);
  return asOfKey(dt);
}

/** Prefer window object that carries boundary reasons; fill closed_by from next slice if needed. */
function enrichWindow(window, allWindows) {
  if (!window) return window;
  const opened = window.opened_by || [];
  let closed = window.closed_by || [];
  if (!boundaryLabels(closed).length) {
    const following = allWindows.find(
      (w) => w.start_date === nextDayIso(window.end_date)
    );
    if (following && boundaryLabels(following.opened_by).length) {
      closed = following.opened_by;
    }
  }
  return { ...window, opened_by: opened, closed_by: closed };
}

function uniqueWindows(rows) {
  const byKey = new Map();
  rows.forEach((row) => {
    if (!row.window) return;
    const key = windowKey(row.window);
    const existing = byKey.get(key);
    if (!existing) {
      byKey.set(key, row.window);
      return;
    }
    // Prefer richer boundary metadata; keep a stable transit_signature for
    // enrichment lookups (houses are matched by calendar+dasha, not signature).
    const score = (w) => (
      (w.opened_by?.length || 0) + (w.closed_by?.length || 0)
    );
    if (score(row.window) > score(existing)) byKey.set(key, row.window);
  });
  const list = [...byKey.values()].sort((a, b) => (
    String(a.start_date).localeCompare(String(b.start_date)
    ) || String(a.end_date).localeCompare(String(b.end_date))
  ));
  return list.map((window) => enrichWindow(window, list));
}

function housesInWindow(rows, window) {
  const key = windowKey(window);
  // One house can appear once per calendar+dasha tile; if merge left multiple
  // signatures for the same span, keep the strongest state.
  const bestByHouse = new Map();
  rows.forEach((row) => {
    if (!row.window || windowKey(row.window) !== key) return;
    const prev = bestByHouse.get(row.house);
    if (!prev || stateRank(row.state) > stateRank(prev.state)) {
      bestByHouse.set(row.house, row);
    }
  });
  return sortHouses([...bestByHouse.values()]);
}

function relationLabel(relation) {
  return String(relation || '').replaceAll('_', ' ');
}

function outcomeWeightSummary(outcome) {
  if (!outcome) return null;
  const buckets = [
    ...(outcome.supportive_reasons || []),
    ...(outcome.mixed_reasons || []),
    ...(outcome.challenging_reasons || []),
  ];
  if (!buckets.length) return null;
  let support = 0;
  let challenge = 0;
  const planets = buckets.map((row) => {
    const up = Number(row.supportive_weight) || 0;
    const down = Number(row.challenging_weight) || 0;
    support += up;
    challenge += down;
    return {
      planet: row.planet,
      polarity: row.polarity || 'neutral',
      up,
      down,
    };
  });
  return {
    support,
    challenge,
    planets,
  };
}

function EvidenceList({ items, empty }) {
  if (!items?.length) return <span className="desk-act__event-evidence-empty">{empty}</span>;
  return (
    <ul className="desk-act__event-evidence-list">
      {items.map((item, index) => <li key={`${String(item)}-${index}`}>{item}</li>)}
    </ul>
  );
}

function HouseGroupEvidence({ rows, eventKey }) {
  if (!rows?.length) {
    return <span className="desk-act__event-evidence-empty">No qualifying house in this group.</span>;
  }
  return (
    <div className="desk-act__event-house-evidence">
      {rows.map((row) => {
        const natal = (row.natal_connections || []).map((link) => (
          `${link.level || 'Dasha'} ${abbr(link.planet)} · ${relationLabel(link.relation)}`
        ));
        const transits = (row.transit_connections || [])
          .filter((link) => link.timing_trigger)
          .map((link) => (
            `${abbr(link.planet)} ${relationLabel(link.relation)}${link.transit_house ? ` from H${link.transit_house}` : ''}`
          ));
        return (
          <article key={`${row.house}-${row.state}`}>
            <header>
              <strong>H{row.house} {eventHouseLabel(eventKey, row.house)}</strong>
              <span>{STATE_META[row.state]?.short || relationLabel(row.state)}</span>
            </header>
            <p className="desk-act__event-house-meaning">{EVENT_HOUSE_MEANINGS[eventKey]?.[row.house]}</p>
            <p className="desk-act__event-state-meaning">
              <strong>Why {STATE_META[row.state]?.short || 'active'}:</strong>{' '}
              {STATE_META[row.state]?.meaning || 'This house participates in the event window.'}
            </p>
            <div className="desk-act__event-evidence-tags">
              {(row.carriers || []).map((planet) => <b key={planet}>{abbr(planet)} carrier</b>)}
              {(row.dasha_levels || []).map((level) => <i key={level}>{level}</i>)}
            </div>
            <div className="desk-act__event-evidence-columns">
              <div><em>Dasha connection</em><EvidenceList items={natal} empty="No direct natal portfolio link" /></div>
              <div><em>Transit timing</em><EvidenceList items={transits} empty="Opened by dasha; no direct transit hit" /></div>
            </div>
          </article>
        );
      })}
    </div>
  );
}

function CalculationEvidence({ step, eventKey }) {
  const evidence = step.evidence || {};
  if (Array.isArray(evidence)) return <HouseGroupEvidence rows={evidence} eventKey={eventKey} />;

  if (step.key === 'dasha_permission') {
    const levelMeaning = {
      MD: 'The long chapter and broad life agenda.',
      AD: 'The active sub-period that channels the chapter.',
      PD: 'The shorter delivery period used to narrow timing.',
    };
    return (
      <div className="desk-act__event-dasha-evidence">
        {['MD', 'AD', 'PD'].map((level) => (
          <span key={level}>
            <em>{level}</em><strong>{evidence[level] || '—'}</strong><small>{levelMeaning[level]}</small>
          </span>
        ))}
      </div>
    );
  }

  if (step.key === 'divisional_confirmation') {
    return (
      <div className="desk-act__event-confirmation-evidence">
        <p>{evidence.explanation}</p>
        <EvidenceList
          items={(evidence.matches || []).map((match) => (
            `${match.planet} connects to ${evidence.chart || 'the divisional chart'} H${match.house}${EVENT_HOUSE_MEANINGS[eventKey]?.[match.house] ? ` (${EVENT_HOUSE_MEANINGS[eventKey][match.house]})` : ''} by ${(match.relations || []).map(relationLabel).join(', ')}.`
          ))}
          empty={`No active dasha lord directly carries the selected ${evidence.chart || 'divisional'} houses.`}
        />
      </div>
    );
  }

  if (step.key === 'independent_confirmation') {
    const double = evidence.double_transit || {};
    const exact = evidence.exact_and_repetition_confirmations || [];
    const boundaries = evidence.dasha_boundaries || [];
    const doublePlanetLines = double.planets ? ['Jupiter', 'Saturn'].map((planet) => {
      const row = double.planets[planet] || {};
      const contacts = row.contacted_focus_houses || row.contacted_career_houses || [];
      const focusHouses = Object.keys(EVENT_HOUSE_MEANINGS[eventKey] || {}).map(Number);
      return contacts.length
        ? `${planet} from H${row.transit_house} contacts ${contacts.map((house) => `H${house}`).join(' and ')}.`
        : `${planet} from H${row.transit_house || '—'} does not contact ${focusHouses.map((house) => `H${house}`).join('/')}.`;
    }) : [];
    return (
      <div className="desk-act__event-confirmation-grid">
        <article className={evidence.transit_reinforced ? 'is-confirmed' : ''}>
          <strong>Dasha-lord transit</strong>
          <span>{evidence.transit_reinforced ? 'A required event house receives a direct timing hit.' : 'No direct timing hit in this slice.'}</span>
        </article>
        <article className={double.passed ? 'is-confirmed' : ''}>
          <strong>Jupiter–Saturn</strong>
          <span>{double.explanation || 'No double-transit evidence.'}</span>
          <EvidenceList items={doublePlanetLines} empty="Planet contact details are unavailable." />
        </article>
        <article className={boundaries.length ? 'is-confirmed' : ''}>
          <strong>Dasha boundary</strong>
          <EvidenceList items={boundaries.map((row) => row.label)} empty="No MD/AD/PD boundary opens this slice." />
        </article>
        <article className={exact.length ? 'is-confirmed' : ''}>
          <strong>Exact and repeated contacts</strong>
          <EvidenceList items={exact.map((row) => row.label)} empty="No exact return or repeated natal relationship in this slice." />
        </article>
      </div>
    );
  }

  return <span className="desk-act__event-evidence-empty">No additional evidence rows.</span>;
}

function TimingBoundaryEvidence({ slices }) {
  return (
    <div className="desk-act__event-slice-list">
      {(slices || []).map((slice, index) => {
        const opens = boundaryLabels(slice.opened_by, { hideHorizon: false });
        const closes = boundaryLabels(slice.closed_by, { hideHorizon: false });
        return (
          <article key={`${slice.start_date}-${slice.end_date}-${index}`}>
            <header><strong>{formatRange(slice.start_date, slice.end_date)}</strong><b>{slice.score}/100</b></header>
            {opens.length ? <span><em>Opens</em>{opens.join(' · ')}</span> : null}
            {closes.length ? <span><em>Ends</em>{closes.join(' · ')}</span> : null}
          </article>
        );
      })}
    </div>
  );
}

/**
 * Desk activations: Now / Next timeline, focus house sets, H1–12 map.
 * Pure house-activation ledger (dasha + transit) from prediction engine.
 */
export default function DeskActivationsPanel({
  result,
  loading,
  error,
  birthData,
  chartData,
  asOfDate,
  onJumpToDate,
  onOpenFull,
  onLensChange,
  layout = 'dock', // dock | focus | expanded | mobile
}) {
  const [lens, setLens] = useState('timeline'); // timeline | focus | map | double
  const [selected, setSelected] = useState(null); // { house, windowStart, windowEnd, transitSignature }
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailPercent, setDetailPercent] = useState(45);
  const [detailMaximized, setDetailMaximized] = useState(false);
  const [legendExpanded, setLegendExpanded] = useState(false);
  const [eventKey, setEventKey] = useState('job_change');
  const [eventYear, setEventYear] = useState(() => (asOfDate || new Date()).getFullYear());
  const [includeDeveloping, setIncludeDeveloping] = useState(false);
  const [eventResult, setEventResult] = useState(null);
  const [eventLoading, setEventLoading] = useState(false);
  const [eventError, setEventError] = useState('');
  const [eventFullScreen, setEventFullScreen] = useState(false);

  useEffect(() => {
    onLensChange?.(lens);
    setDetailMaximized(false);
    if (lens !== 'focus') setEventFullScreen(false);
  }, [lens, onLensChange]);

  useEffect(() => {
    if (layout !== 'mobile' || !detailOpen) return undefined;
    const previousOverflow = document.body.style.overflow;
    const onKeyDown = (event) => {
      if (event.key === 'Escape') setDetailOpen(false);
    };
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [detailOpen, layout]);

  useEffect(() => {
    if (!eventFullScreen) return undefined;
    const previousOverflow = document.body.style.overflow;
    const onKeyDown = (event) => {
      if (event.key === 'Escape') setEventFullScreen(false);
    };
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [eventFullScreen]);

  useEffect(() => {
    setEventResult(null);
    setEventError('');
  }, [birthData?.chart_id, birthData?.birth_chart_id, birthData?.id, birthData?.date, birthData?.time]);

  const asOf = asOfKey(asOfDate);
  const rows = result?.house_activations || [];

  const windows = useMemo(() => uniqueWindows(rows), [rows]);

  const currentRows = useMemo(() => {
    if (!rows.length || !asOf) return [];
    const containing = rows.filter(
      (row) => row.window?.start_date <= asOf && row.window?.end_date >= asOf
    );
    if (containing.length) return sortHouses(containing);
    const first = rows[0]?.window?.start_date;
    return first ? sortHouses(rows.filter((row) => row.window?.start_date === first)) : [];
  }, [rows, asOf]);

  const currentPredictive = useMemo(
    () => currentRows.filter((row) => PREDICTIVE.has(row.state)),
    [currentRows]
  );

  const nextWindows = useMemo(() => {
    if (!asOf) return [];
    return windows
      .filter((w) => w.start_date > asOf)
      .map((w) => {
        const houseRows = housesInWindow(rows, w).filter((row) => PREDICTIVE.has(row.state));
        return { window: w, houses: houseRows };
      })
      .filter((entry) => entry.houses.length > 0);
  }, [windows, rows, asOf]);

  const selectedRow = useMemo(() => {
    if (!selected) return null;
    return rows.find((row) => (
      row.house === selected.house
      && row.window?.start_date === selected.windowStart
      && (!selected.windowEnd || row.window?.end_date === selected.windowEnd)
      && (
        !selected.transitSignature
        || row.window?.transit_signature === selected.transitSignature
      )
    )) || null;
  }, [rows, selected]);

  const detailRow = selectedRow || currentPredictive[0] || null;

  const detailWindow = useMemo(() => {
    if (!detailRow?.window) return null;
    return enrichWindow(detailRow.window, windows);
  }, [detailRow, windows]);

  const detailWindowHouses = useMemo(() => {
    if (!detailWindow) return [];
    return housesInWindow(rows, detailWindow).filter((row) => PREDICTIVE.has(row.state));
  }, [rows, detailWindow]);

  const jump = (isoDay) => {
    if (!onJumpToDate) return;
    const next = parseJumpDate(isoDay, asOfDate);
    if (next) onJumpToDate(next);
  };

  const runEventFocus = async () => {
    if (!birthData || eventLoading) return;
    setEventLoading(true);
    setEventError('');
    try {
      const data = await apiService.getEventWindows({
        birthChartId: birthData.chart_id || birthData.birth_chart_id || birthData.id || null,
        birthData,
        eventKey,
        year: Number(eventYear),
        includeDeveloping,
      });
      setEventResult(data);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setEventResult(null);
      setEventError(
        typeof detail === 'string'
          ? detail
          : err?.message || 'Could not calculate event windows'
      );
    } finally {
      setEventLoading(false);
    }
  };

  const eventMeta = EVENT_FOCUS_META[eventKey] || EVENT_FOCUS_META.job_change;

  const selectRow = (row, { syncAsOf = false } = {}) => {
    setSelected({
      house: row.house,
      windowStart: row.window?.start_date,
      windowEnd: row.window?.end_date,
      transitSignature: row.window?.transit_signature,
    });
    if (layout === 'mobile') setDetailOpen(true);
    if (layout === 'focus') setDetailPercent((current) => Math.max(current, 45));
    if (syncAsOf) jump(row.window?.start_date);
  };

  const selectWindow = (window, houseRow, { syncAsOf = false } = {}) => {
    const row = houseRow || housesInWindow(rows, window).find((r) => PREDICTIVE.has(r.state));
    if (row) selectRow(row, { syncAsOf });
    else if (syncAsOf) jump(window.start_date);
  };

  const resizeDetail = (event) => {
    if (layout !== 'focus' || detailMaximized) return;
    event.preventDefault();
    const workspace = event.currentTarget.parentElement;
    const bounds = workspace.getBoundingClientRect();
    const previousCursor = document.body.style.cursor;
    const previousUserSelect = document.body.style.userSelect;
    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';

    const onMove = (moveEvent) => {
      const percent = ((bounds.bottom - moveEvent.clientY) / bounds.height) * 100;
      setDetailPercent(Math.min(70, Math.max(30, percent)));
    };
    const onUp = () => {
      document.body.style.cursor = previousCursor;
      document.body.style.userSelect = previousUserSelect;
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('pointercancel', onUp);
    };
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    window.addEventListener('pointercancel', onUp);
  };

  const resizeDetailWithKeyboard = (event) => {
    if (event.key !== 'ArrowUp' && event.key !== 'ArrowDown') return;
    event.preventDefault();
    setDetailPercent((current) => Math.min(
      70,
      Math.max(30, current + (event.key === 'ArrowUp' ? 5 : -5))
    ));
  };

  if (lens !== 'double' && lens !== 'focus' && loading && !result) {
    return (
      <div className="desk-act desk-act--status">
        <strong>Reading activation ledger</strong>
        <span>MD → AD → PD natal links with transit triggers</span>
        <button type="button" className="desk-act__status-action" onClick={() => setLens('double')}>Open Double Transit</button>
      </div>
    );
  }

  if (lens !== 'double' && lens !== 'focus' && error) {
    return (
      <div className="desk-act desk-act--status desk-act--err">
        <strong>Activation ledger unavailable</strong>
        <span>{error}</span>
        <button type="button" className="desk-act__status-action" onClick={() => setLens('double')}>Open isolated Double Transit</button>
      </div>
    );
  }

  if (lens !== 'double' && lens !== 'focus' && !rows.length) {
    return (
      <div className="desk-act desk-act--status">
        <strong>No activation windows</strong>
        <span>Extend horizon or verify dasha/transit calculation for this chart</span>
        <button type="button" className="desk-act__status-action" onClick={() => setLens('double')}>Open Double Transit</button>
      </div>
    );
  }

  const currentWindow = enrichWindow(currentRows[0]?.window, windows);
  const detailOutcomeWeights = outcomeWeightSummary(detailRow?.outcome);

  const detailAside = detailRow && detailWindow ? (
        <aside className="desk-act__detail" aria-label="Activation window detail">
          <header className="desk-act__detail-window">
            <div className="desk-act__detail-window-top">
              <em>Timing window</em>
              <strong>{formatRange(detailWindow.start_date, detailWindow.end_date)}</strong>
              <span>{dashaPath(detailWindow)}</span>
              <div className="desk-act__detail-actions">
                {onJumpToDate && detailWindow.start_date && detailWindow.start_date !== asOf ? (
                  <button
                    type="button"
                    className="desk-act__asof"
                    onClick={() => jump(detailWindow.start_date)}
                    title={`Set desk as-of to ${detailWindow.start_date}`}
                  >
                    Set as-of
                  </button>
                ) : null}
                {layout === 'focus' ? (
                  <button
                    type="button"
                    className="desk-act__detail-expand"
                    onClick={() => setDetailMaximized((current) => !current)}
                    title={detailMaximized ? 'Return to the activation timeline' : 'Use the full activation column for timing details'}
                  >
                    {detailMaximized ? '← Back to timeline' : 'Expand details'}
                  </button>
                ) : null}
              </div>
            </div>
            <BoundaryReasons
              openedBy={detailWindow.opened_by}
              closedBy={detailWindow.closed_by}
              endDate={detailWindow.end_date}
            />
            {detailWindowHouses.length > 1 ? (
              <div className="desk-act__house-switch" role="tablist" aria-label="Houses in this window">
                <em>Houses in window</em>
                {detailWindowHouses.map((row) => (
                  <button
                    key={`switch-${row.house}`}
                    type="button"
                    role="tab"
                    aria-selected={detailRow.house === row.house}
                    className={detailRow.house === row.house ? 'is-active' : ''}
                    onClick={() => selectRow(row, { syncAsOf: false })}
                  >
                    H{row.house}
                    <i>{STATE_META[row.state]?.short}</i>
                  </button>
                ))}
              </div>
            ) : null}
          </header>

          <header className="desk-act__detail-head">
            <strong>H{detailRow.house}</strong>
            <span>{HOUSE_LABELS[detailRow.house]}</span>
            <i
              className={`desk-act__state desk-act__state--${detailRow.state}`}
              title={STATE_META[detailRow.state]?.meaning}
            >
              {STATE_META[detailRow.state]?.short}
            </i>
            <b className={`desk-act__tone desk-act__tone--${detailRow.outcome?.tone || 'neutral'}`}>
              {TONE_META[detailRow.outcome?.tone]?.short}
            </b>
            {STATE_META[detailRow.state]?.hint ? (
              <span className="desk-act__state-hint" title={STATE_META[detailRow.state]?.meaning}>
                {STATE_META[detailRow.state].hint}
              </span>
            ) : null}
          </header>

          <div className="desk-act__detail-dasha">
            <em>Vimśottari</em>
            <strong>{dashaPath(detailWindow)}</strong>
            <span>
              {[detailWindow.mahadasha, detailWindow.antardasha, detailWindow.pratyantardasha]
                .filter(Boolean)
                .join(' → ')}
            </span>
          </div>

          {(detailRow.natal_connections || []).length ? (
            <div className="desk-act__detail-block">
              <em>Dasha → H{detailRow.house}</em>
              <ul>
                {detailRow.natal_connections.map((conn) => (
                  <li key={`${conn.level}-${conn.planet}-${conn.relation}`}>
                    <strong>{conn.level}</strong> {abbr(conn.planet)} · {relationLabel(conn.relation)}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {(detailRow.transit_connections || []).filter((t) => t.timing_trigger).length ? (
            <div className="desk-act__detail-block">
              <em>Transit triggers on H{detailRow.house}</em>
              <ul>
                {detailRow.transit_connections.filter((t) => t.timing_trigger).map((t) => (
                  <li key={`${t.planet}-${t.relation}-${t.transit_house}`}>
                    <strong>{abbr(t.planet)}</strong>
                    {' '}
                    {relationLabel(t.relation)}
                    {t.transit_house != null ? ` from H${t.transit_house}` : ''}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {(detailRow.transit_confirmations || []).length ? (
            <div className="desk-act__detail-block desk-act__confirmations">
              <em>Transit confirmations</em>
              <ul>
                {detailRow.transit_confirmations.map((row, index) => (
                  <li key={`${row.kind}-${row.planet}-${row.target_planet || ''}-${row.exact_at || index}`}>
                    <span className={`desk-act__confirmation-icon desk-act__confirmation-icon--${row.kind}`} aria-hidden="true">✓</span>
                    <span>
                      <strong>{row.label}</strong>
                      {confirmationMeta(row) ? <small>{confirmationMeta(row)}</small> : null}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="desk-act__detail-outcome">
            <em>Result direction for H{detailRow.house}</em>
            <div className="desk-act__outcome-head">
              <strong className={`desk-act__tone desk-act__tone--${detailRow.outcome?.tone || 'neutral'}`}>
                {TONE_META[detailRow.outcome?.tone]?.short || 'Neutral'}
              </strong>
              <span className="desk-act__outcome-note" title="Tone follows total weighted strength. Mixed planets contribute both support and challenge weight.">
                by weighted strength
              </span>
            </div>

            {detailOutcomeWeights ? (
              <>
                <div
                  className="desk-act__outcome-meter"
                  role="img"
                  aria-label={`Support ${detailOutcomeWeights.support.toFixed(1)}, challenge ${detailOutcomeWeights.challenge.toFixed(1)}`}
                >
                  <i
                    className="desk-act__outcome-meter-support"
                    style={{ flexGrow: Math.max(detailOutcomeWeights.support, 0.01) }}
                  />
                  <i
                    className="desk-act__outcome-meter-challenge"
                    style={{ flexGrow: Math.max(detailOutcomeWeights.challenge, 0.01) }}
                  />
                </div>
                <div className="desk-act__outcome-totals">
                  <span className="is-support">+{detailOutcomeWeights.support.toFixed(1)} support</span>
                  <span className="is-challenge">−{detailOutcomeWeights.challenge.toFixed(1)} challenge</span>
                </div>
                <ul className="desk-act__outcome-planets">
                  {detailOutcomeWeights.planets.map((row) => (
                    <li key={`${row.planet}-${row.polarity}`}>
                      <strong>{abbr(row.planet)}</strong>
                      <i className={`desk-act__tone desk-act__tone--${row.polarity}`}>
                        {row.polarity}
                      </i>
                      <span className="desk-act__outcome-planet-weights">
                        {row.up > 0 ? <b className="is-support">+{row.up.toFixed(1)}</b> : null}
                        {row.down > 0 ? <b className="is-challenge">−{row.down.toFixed(1)}</b> : null}
                      </span>
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <div className="desk-act__outcome-totals desk-act__outcome-totals--empty">
                <span>No directional weight yet</span>
              </div>
            )}
          </div>

          {(detailRow.activation?.carrier_planets || []).length ? (
            <div className="desk-act__carriers">
              {(detailRow.activation.carrier_planets || []).map((p) => (
                <span key={p}>{abbr(p)}</span>
              ))}
            </div>
          ) : null}
        </aside>
  ) : null;

  return (
    <div
      className={`desk-act${layout === 'focus' || layout === 'mobile' ? ' desk-act--focus' : ''}${layout === 'expanded' ? ' desk-act--expanded' : ''}${layout === 'mobile' ? ' desk-act--mobile' : ''}${detailMaximized && layout === 'focus' ? ' desk-act--detail-maximized' : ''}${eventFullScreen ? ' desk-act--event-fullscreen' : ''}`}
      data-lens={lens}
      style={layout === 'focus' ? { '--da-detail-percent': `${detailPercent}%` } : undefined}
      role={eventFullScreen ? 'dialog' : undefined}
      aria-modal={eventFullScreen ? 'true' : undefined}
      aria-label={eventFullScreen ? 'Full-screen event focus' : undefined}
    >
      <div className="desk-act__toolbar">
        <div className="desk-act__lenses" role="tablist" aria-label="Activation lens">
          {[
            { id: 'timeline', label: 'Timeline', icon: '↝' },
            { id: 'focus', label: 'Focus', icon: '◎' },
            { id: 'map', label: 'Map', icon: '▦' },
            { id: 'double', label: 'Double Transit', mobileLabel: 'Double', icon: '♃♄' },
          ].map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={lens === item.id}
              className={lens === item.id ? 'is-active' : ''}
              onClick={() => setLens(item.id)}
            >
              {layout === 'mobile' ? (
                <>
                  <span className="desk-act__lens-icon" aria-hidden>{item.icon}</span>
                  <span className="desk-act__lens-label">{item.mobileLabel || item.label}</span>
                </>
              ) : item.label}
            </button>
          ))}
        </div>
        {!['double', 'focus'].includes(lens) ? <div className="desk-act__meta">
          <span title="As-of date">{formatDay(asOf)}</span>
          <span title="Horizon end">{formatDay(result?.horizon_end)}</span>
          {onOpenFull ? (
            <button type="button" className="desk-act__full" onClick={onOpenFull} title="Full activation explorer">
              Full
            </button>
          ) : null}
        </div> : null}
      </div>

      {!['double', 'focus'].includes(lens) ? (
        <div className={`desk-act__state-key${legendExpanded ? ' is-expanded' : ''}`} aria-label="Activation state meanings">
          <div className="desk-act__state-key-summary">
            <div className="desk-act__state-key-items">
              {STATE_LEGEND.map((state) => (
                <span key={state} title={STATE_META[state].meaning}>
                  <i className={`desk-act__swatch desk-act__swatch--${state}`} />
                  <strong>{STATE_META[state].short}</strong>
                </span>
              ))}
            </div>
            <button
              type="button"
              className="desk-act__state-key-toggle"
              aria-expanded={legendExpanded}
              onClick={() => setLegendExpanded((current) => !current)}
            >
              {legendExpanded ? 'Hide meanings' : 'What do these mean?'}
              <i aria-hidden>{legendExpanded ? '⌃' : '⌄'}</i>
            </button>
          </div>
          {legendExpanded ? (
            <div className="desk-act__state-key-details">
              {STATE_LEGEND.map((state) => (
                <span key={`meaning-${state}`}>
                  <i className={`desk-act__swatch desk-act__swatch--${state}`} />
                  <strong>{STATE_META[state].short}</strong>
                  <em>{STATE_META[state].hint}</em>
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      {!['double', 'focus'].includes(lens) && currentWindow ? (
        <div className="desk-act__dasha" title="Current Vimśottari stack at as-of">
          <em>Now</em>
          <strong>{dashaPath(currentWindow)}</strong>
          <span>{formatRange(currentWindow.start_date, currentWindow.end_date)}</span>
          {(boundaryLabels(currentWindow.opened_by).length
            || boundaryLabels(currentWindow.closed_by).length) ? (
            <BoundaryReasons
              openedBy={currentWindow.opened_by}
              closedBy={currentWindow.closed_by}
              endDate={currentWindow.end_date}
            />
          ) : null}
        </div>
      ) : null}

      <div className="desk-act__workspace">
      <div className="desk-act__body">
        {lens === 'timeline' ? (
          <div className="desk-act__split">
            <section className="desk-act__col" aria-label="Current activations">
              <header className="desk-act__col-head">
                <span>Now</span>
                <em>{currentPredictive.length} houses</em>
              </header>
              <div className="desk-act__list">
                {currentPredictive.length ? currentPredictive.map((row) => (
                  <button
                    key={`now-${row.house}-${row.window?.start_date}`}
                    type="button"
                    className={`desk-act__row desk-act__row--${row.state} desk-act__row--tone-${row.outcome?.tone || 'neutral'}${detailRow?.house === row.house && detailRow?.window?.start_date === row.window?.start_date ? ' is-selected' : ''}`}
                    onClick={() => selectRow(row, { syncAsOf: true })}
                  >
                    <span className="desk-act__row-main">
                      <strong>H{row.house}</strong>
                      <span className="desk-act__house-label">{HOUSE_LABELS[row.house]}</span>
                    </span>
                    <span className="desk-act__row-badges">
                      <i
                        className={`desk-act__state desk-act__state--${row.state}`}
                        title={STATE_META[row.state]?.meaning}
                      >
                        {STATE_META[row.state]?.short}
                      </i>
                      <b className={`desk-act__tone desk-act__tone--${row.outcome?.tone || 'neutral'}`}>
                        {TONE_META[row.outcome?.tone]?.short || 'Neutral'}
                      </b>
                    </span>
                  </button>
                )) : (
                  <div className="desk-act__empty-note">No dasha-connected houses at this as-of</div>
                )}
              </div>
            </section>

            <section className="desk-act__col" aria-label="Next activations">
              <header className="desk-act__col-head">
                <span>Next</span>
                <em>{nextWindows.length} windows</em>
              </header>
              <div className="desk-act__list">
                {nextWindows.length ? nextWindows.map(({ window, houses }) => {
                  const isSelected = detailWindow
                    && windowKey(detailWindow) === windowKey(window);
                  return (
                  <div
                    key={`next-${windowKey(window)}`}
                    className={`desk-act__window${isSelected ? ' is-current' : ''}`}
                    role="button"
                    tabIndex={0}
                    onClick={() => selectWindow(window, houses[0], { syncAsOf: false })}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        selectWindow(window, houses[0], { syncAsOf: false });
                      }
                    }}
                    title={`${dashaPath(window)} · ${formatRange(window.start_date, window.end_date)} · ${houses.map((h) => `H${h.house}`).join(', ')}`}
                  >
                    <div className="desk-act__window-head">
                      <strong>{formatRange(window.start_date, window.end_date)}</strong>
                      <span>{dashaPath(window)}</span>
                    </div>
                    <BoundaryReasons
                      openedBy={window.opened_by}
                      closedBy={window.closed_by}
                      endDate={window.end_date}
                    />
                    <div className="desk-act__window-houses">
                      {houses.map((row) => (
                        <button
                          key={`${row.house}-${row.state}`}
                          type="button"
                          className={`desk-act__pill desk-act__pill--${row.state} desk-act__pill--tone-${row.outcome?.tone || 'neutral'}${detailRow?.house === row.house && isSelected ? ' is-active' : ''}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            selectRow(row, { syncAsOf: false });
                          }}
                        >
                          H{row.house}
                          <i>{STATE_META[row.state]?.short}</i>
                          <em>{TONE_META[row.outcome?.tone]?.short?.[0] || 'N'}</em>
                        </button>
                      ))}
                    </div>
                  </div>
                  );
                }) : (
                  <div className="desk-act__empty-note">No further predictive windows in horizon</div>
                )}
              </div>
            </section>
          </div>
        ) : null}

        {lens === 'focus' ? (
          <div className="desk-act__focus desk-act__event-focus">
            <div className="desk-act__event-controls">
              <label>
                <span>Life event</span>
                <select
                  value={eventKey}
                  onChange={(e) => {
                    setEventKey(e.target.value);
                    setEventResult(null);
                    setEventError('');
                  }}
                >
                  <option value="job_change">Job change</option>
                  <option value="health">Health</option>
                </select>
              </label>
              <label>
                <span>Year</span>
                <select value={eventYear} onChange={(e) => setEventYear(Number(e.target.value))}>
                  {Array.from({ length: 201 }, (_, index) => 1900 + index).map((year) => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </label>
              <label className="desk-act__event-developing">
                <input
                  type="checkbox"
                  checked={includeDeveloping}
                  onChange={(e) => setIncludeDeveloping(e.target.checked)}
                />
                <span>Include developing</span>
              </label>
              <button
                type="button"
                className="desk-act__event-expand"
                onClick={() => setEventFullScreen((open) => !open)}
                title={eventFullScreen ? 'Close full view (Esc)' : 'Open Focus in full view'}
              >
                {eventFullScreen ? '✕ Close full view' : '⛶ Full view'}
              </button>
              <button type="button" className="desk-act__event-run" onClick={runEventFocus} disabled={eventLoading}>
                {eventLoading ? 'Calculating…' : 'Find windows'}
              </button>
            </div>

            <div className="desk-act__event-intro">
              <strong>{eventMeta.label} · dynamic event search</strong>
              <span>{eventMeta.intro}</span>
            </div>

            <div className="desk-act__event-results">
              {eventError ? <div className="desk-act__event-error">{eventError}</div> : null}
              {eventLoading ? (
                <div className="desk-act__event-empty">{eventMeta.loading}</div>
              ) : null}
              {!eventLoading && eventResult ? (
                <>
                  <header className="desk-act__event-summary">
                    <div>
                      <strong>{eventResult.qualified_windows} qualified windows</strong>
                      <span>{eventResult.evaluated_windows} timing slices evaluated · {eventResult.definition_version}</span>
                    </div>
                    <span className="desk-act__event-signature" title={eventResult.evidence_signature}>Trace {String(eventResult.evidence_signature || '').slice(0, 8)}</span>
                  </header>
                  {eventResult.windows?.length ? eventResult.windows.map((window) => (
                    <article key={window.window_id} className={`desk-act__event-card desk-act__event-card--${window.strength}`}>
                      <header>
                        <div>
                          <em>{window.strength}</em>
                          <strong>{formatRange(window.start_date, window.end_date)}</strong>
                          <span>{abbr(window.dasha?.mahadasha)} → {abbr(window.dasha?.antardasha)} → {abbr(window.dasha?.pratyantardasha)}</span>
                        </div>
                        <b>{window.score}/{window.maximum_score}</b>
                      </header>
                      <h4>{window.classification_label}</h4>
                      <p>{window.summary}</p>
                      <div className="desk-act__event-houses">
                        {(window.activated_houses || []).map((house) => <span key={house}>H{house} {eventHouseLabel(eventKey, house)}</span>)}
                      </div>
                      {!eventFullScreen ? (
                        <div className="desk-act__event-actions">
                          <button type="button" onClick={() => jump(window.inspection_date || window.peak_date || window.start_date)}>
                            Set as-of · {formatDay(window.inspection_date || window.peak_date || window.start_date)}
                          </button>
                        </div>
                      ) : null}
                      <details className="desk-act__event-trace">
                        <summary>Show full calculation</summary>
                        <div className="desk-act__event-calculation-overview">
                          <div>
                            <em>Why this qualified</em>
                            <strong>{window.classification_label}</strong>
                            <p>{window.qualification_summary || window.summary}</p>
                          </div>
                          <dl>
                            <div>
                              <dt>Rule completion</dt>
                              <dd>{window.score}/{window.maximum_score}</dd>
                              <small>A transparent rule score—not a statistical probability.</small>
                            </div>
                            <div>
                              <dt>Timing precision</dt>
                              <dd>{window.peak_date ? formatDay(window.peak_date) : 'Broad window'}</dd>
                              <small>{window.peak_reason || 'No exact peak was isolated.'}</small>
                            </div>
                          </dl>
                        </div>
                        <div className="desk-act__event-trace-meta">
                          <span>
                            <b>{window.timing_slices?.length || 1} timing slices</b> mean that transit, nakṣatra or dasha facts changed inside one continuous event window.
                          </span>
                        </div>
                        <details className="desk-act__event-slices">
                          <summary>Show why the timing boundaries changed</summary>
                          <TimingBoundaryEvidence slices={window.timing_slices} />
                        </details>
                        {(window.calculation_trace || []).map((step) => (
                          <section key={step.key} className={step.passed ? 'is-passed' : 'is-not-passed'}>
                            <header>
                              <strong>{step.label}</strong>
                              <span>{step.passed ? 'Passed' : (step.required ? 'Required · not met' : 'Not present')}</span>
                              <b>+{step.score}/{step.maximum_score}</b>
                            </header>
                            <p>{step.description}</p>
                            <CalculationEvidence step={step} eventKey={eventKey} />
                          </section>
                        ))}
                        <details className="desk-act__event-technical">
                          <summary>Technical reference</summary>
                          <span>Window ID <b>{window.window_id}</b></span>
                          <span>This stable identifier lets the same calculated window be audited across views.</span>
                        </details>
                      </details>
                    </article>
                  )) : (
                    <div className="desk-act__event-empty">
                      <strong>No qualified {String(eventResult.event_label || eventMeta.label).toLowerCase()} window in {eventResult.year}</strong>
                      <span>The engine did not weaken the rules or generate a fallback result.</span>
                    </div>
                  )}
                </>
              ) : null}
              {!eventLoading && !eventResult && !eventError ? (
                <div className="desk-act__event-empty">Choose a year and run {eventMeta.label} to evaluate the complete event algorithm.</div>
              ) : null}
            </div>
          </div>
        ) : null}

        {lens === 'map' ? (
          <div className="desk-act__map-wrap">
            <div className="desk-act__map" role="list" aria-label="House activation map at as-of">
              {Array.from({ length: 12 }, (_, i) => i + 1).map((houseNum) => {
                const row = currentRows.find((r) => r.house === houseNum);
                const state = row?.state || 'dormant';
                const tone = row?.outcome?.tone || 'neutral';
                return (
                  <button
                    key={houseNum}
                    type="button"
                    role="listitem"
                    className={`desk-act__cell desk-act__cell--${state}${detailRow?.house === houseNum ? ' is-selected' : ''}`}
                    onClick={() => {
                      if (row) selectRow(row, { syncAsOf: true });
                      else {
                        setSelected({ house: houseNum, windowStart: currentWindow?.start_date });
                        if (layout === 'mobile') setDetailOpen(true);
                      }
                    }}
                    title={`H${houseNum} ${HOUSE_LABELS[houseNum]} · ${STATE_META[state]?.short}: ${STATE_META[state]?.meaning || ''} · ${TONE_META[tone]?.short}`}
                  >
                    <strong>H{houseNum}</strong>
                    <span>{STATE_META[state]?.short}</span>
                    <i className={`desk-act__dot desk-act__dot--${tone}`} aria-hidden />
                  </button>
                );
              })}
            </div>
            <div className="desk-act__legend" aria-hidden>
              {STATE_LEGEND.map((state) => (
                <span key={state} title={STATE_META[state].meaning}>
                  <i className={`desk-act__swatch desk-act__swatch--${state}`} />
                  {STATE_META[state].short}
                </span>
              ))}
              <span><i className="desk-act__dot desk-act__dot--supportive" />Supportive</span>
              <span><i className="desk-act__dot desk-act__dot--challenging" />Challenging</span>
            </div>
          </div>
        ) : null}

        {lens === 'double' ? (
          <DeskDoubleTransitBrowser
            birthData={birthData}
            chartData={chartData}
            onJumpToDate={layout === 'mobile' ? undefined : onJumpToDate}
          />
        ) : null}
      </div>

      {!['double', 'focus'].includes(lens) && (layout === 'mobile' ? (
        detailOpen && detailAside ? (
          <div className="desk-act__sheet" role="dialog" aria-modal="true" aria-label="Activation details">
            <button
              type="button"
              className="desk-act__sheet-backdrop"
              aria-label="Close activation details"
              onClick={() => setDetailOpen(false)}
            />
            <div className="desk-act__sheet-card">
              <header className="desk-act__sheet-head">
                <span aria-hidden />
                <strong>Activation details</strong>
                <button type="button" onClick={() => setDetailOpen(false)} aria-label="Close activation details">
                  Close
                </button>
              </header>
              {detailAside}
            </div>
          </div>
        ) : null
      ) : detailAside ? (
        <>
          {layout === 'focus' ? (
            <div
              className="desk-act__detail-resizer"
              role="separator"
              aria-label="Resize timing window details"
              aria-orientation="horizontal"
              aria-valuemin="30"
              aria-valuemax="70"
              aria-valuenow={Math.round(detailPercent)}
              tabIndex={detailMaximized ? -1 : 0}
              onPointerDown={resizeDetail}
              onKeyDown={resizeDetailWithKeyboard}
              onDoubleClick={() => setDetailPercent(45)}
              title="Drag to resize · Double-click to reset"
            >
              <span aria-hidden />
            </div>
          ) : null}
          {detailAside}
        </>
      ) : null)}
      </div>
    </div>
  );
}
