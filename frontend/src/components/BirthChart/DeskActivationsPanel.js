import React, { useEffect, useMemo, useState } from 'react';
import './DeskActivationsPanel.css';
import DeskDoubleTransitBrowser from './DeskDoubleTransitBrowser';

const PLANET_ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
};

const HOUSE_LABELS = {
  1: 'Self', 2: 'Wealth', 3: 'Effort', 4: 'Home',
  5: 'Creativity', 6: 'Service', 7: 'Partnership', 8: 'Transformation',
  9: 'Dharma', 10: 'Career', 11: 'Gains', 12: 'Release',
};

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

const PRESETS = [
  { id: 'career', label: 'Career', houses: [10, 6, 2], title: 'H10 · H6 · H2 — karma, service, resources' },
  { id: 'job', label: 'Job change', houses: [6, 10, 3], title: 'H6 · H10 · H3 — service, status, courage/effort' },
  { id: 'status', label: 'Status', houses: [10, 11], title: 'H10 · H11 — career recognition & gains' },
  { id: 'wealth', label: 'Wealth', houses: [2, 11, 5], title: 'H2 · H11 · H5 — accumulation & speculative gains' },
  { id: 'custom', label: 'Custom', houses: null, title: 'Pick houses H1–H12' },
];

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
  const [presetId, setPresetId] = useState('career');
  const [customHouses, setCustomHouses] = useState(() => new Set([6, 10, 3]));
  const [selected, setSelected] = useState(null); // { house, windowStart, windowEnd, transitSignature }
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailPercent, setDetailPercent] = useState(45);
  const [detailMaximized, setDetailMaximized] = useState(false);
  const [legendExpanded, setLegendExpanded] = useState(false);

  useEffect(() => {
    onLensChange?.(lens);
    setDetailMaximized(false);
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

  const asOf = asOfKey(asOfDate);
  const rows = result?.house_activations || [];

  const focusHouses = useMemo(() => {
    const preset = PRESETS.find((p) => p.id === presetId);
    if (preset?.houses) return preset.houses;
    return [...customHouses].sort((a, b) => a - b);
  }, [presetId, customHouses]);

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

  const focusTimeline = useMemo(() => {
    if (!focusHouses.length) return [];
    const focusSet = new Set(focusHouses);
    const relevant = rows.filter(
      (row) => focusSet.has(row.house) && row.state !== 'dormant'
    );
    const byWindow = new Map();
    relevant.forEach((row) => {
      const key = windowKey(row.window);
      if (!byWindow.has(key)) {
        byWindow.set(key, { window: enrichWindow(row.window, windows), houses: [] });
      }
      byWindow.get(key).houses.push(row);
    });
    return [...byWindow.values()]
      .map((entry) => ({
        ...entry,
        houses: sortHouses(entry.houses),
        isCurrent: entry.window.start_date <= asOf && entry.window.end_date >= asOf,
        isPast: entry.window.end_date < asOf,
        isFuture: entry.window.start_date > asOf,
      }))
      .sort((a, b) => String(a.window.start_date).localeCompare(String(b.window.start_date)));
  }, [rows, focusHouses, asOf, windows]);

  const focusUpcoming = useMemo(
    () => focusTimeline.filter((entry) => entry.isCurrent || entry.isFuture),
    [focusTimeline]
  );

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

  const toggleCustomHouse = (house) => {
    setCustomHouses((prev) => {
      const next = new Set(prev);
      if (next.has(house)) next.delete(house);
      else next.add(house);
      return next;
    });
    setPresetId('custom');
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

  if (lens !== 'double' && loading && !result) {
    return (
      <div className="desk-act desk-act--status">
        <strong>Reading activation ledger</strong>
        <span>MD → AD → PD natal links with transit triggers</span>
        <button type="button" className="desk-act__status-action" onClick={() => setLens('double')}>Open Double Transit</button>
      </div>
    );
  }

  if (lens !== 'double' && error) {
    return (
      <div className="desk-act desk-act--status desk-act--err">
        <strong>Activation ledger unavailable</strong>
        <span>{error}</span>
        <button type="button" className="desk-act__status-action" onClick={() => setLens('double')}>Open isolated Double Transit</button>
      </div>
    );
  }

  if (lens !== 'double' && !rows.length) {
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
      className={`desk-act${layout === 'focus' || layout === 'mobile' ? ' desk-act--focus' : ''}${layout === 'expanded' ? ' desk-act--expanded' : ''}${layout === 'mobile' ? ' desk-act--mobile' : ''}${detailMaximized && layout === 'focus' ? ' desk-act--detail-maximized' : ''}`}
      data-lens={lens}
      style={layout === 'focus' ? { '--da-detail-percent': `${detailPercent}%` } : undefined}
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
        {lens !== 'double' ? <div className="desk-act__meta">
          <span title="As-of date">{formatDay(asOf)}</span>
          <span title="Horizon end">{formatDay(result?.horizon_end)}</span>
          {onOpenFull ? (
            <button type="button" className="desk-act__full" onClick={onOpenFull} title="Full activation explorer">
              Full
            </button>
          ) : null}
        </div> : null}
      </div>

      {lens !== 'double' ? (
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

      {lens !== 'double' && currentWindow ? (
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
          <div className="desk-act__focus">
            <div className="desk-act__presets" role="group" aria-label="House focus">
              {PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  className={presetId === preset.id ? 'is-active' : ''}
                  title={preset.title}
                  onClick={() => setPresetId(preset.id)}
                >
                  {preset.label}
                </button>
              ))}
            </div>

            {presetId === 'custom' ? (
              <div className="desk-act__custom" role="group" aria-label="Custom houses">
                {Array.from({ length: 12 }, (_, i) => i + 1).map((house) => (
                  <button
                    key={house}
                    type="button"
                    className={customHouses.has(house) ? 'is-active' : ''}
                    onClick={() => toggleCustomHouse(house)}
                  >
                    {house}
                  </button>
                ))}
              </div>
            ) : (
              <div className="desk-act__focus-houses">
                {focusHouses.map((h) => (
                  <span key={h}>H{h} {HOUSE_LABELS[h]}</span>
                ))}
              </div>
            )}

            <div className="desk-act__list desk-act__list--focus">
              {focusUpcoming.length ? focusUpcoming.map(({ window, houses, isCurrent }) => (
                <button
                  key={`focus-${windowKey(window)}`}
                  type="button"
                  className={`desk-act__window${isCurrent ? ' is-current' : ''}${detailRow?.window?.start_date === window.start_date ? ' is-selected' : ''}`}
                  onClick={() => selectWindow(window, houses[0], { syncAsOf: Boolean(isCurrent) })}
                  title={`${dashaPath(window)} · ${formatRange(window.start_date, window.end_date)}`}
                >
                  <div className="desk-act__window-head">
                    <strong>
                      {isCurrent ? 'Now · ' : ''}
                      {formatRange(window.start_date, window.end_date)}
                    </strong>
                    <span>{dashaPath(window)}</span>
                  </div>
                  <BoundaryReasons
                    openedBy={window.opened_by}
                    closedBy={window.closed_by}
                    endDate={window.end_date}
                  />
                  <div className="desk-act__window-houses">
                    {houses.map((row) => (
                      <span
                        key={`${row.house}-${row.state}`}
                        className={`desk-act__pill desk-act__pill--${row.state} desk-act__pill--tone-${row.outcome?.tone || 'neutral'}`}
                      >
                        H{row.house}
                        <i>{STATE_META[row.state]?.short}</i>
                        <em>{TONE_META[row.outcome?.tone]?.short}</em>
                      </span>
                    ))}
                  </div>
                </button>
              )) : (
                <div className="desk-act__empty-note">
                  Selected houses stay quiet through this horizon
                </div>
              )}
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

      {lens !== 'double' && (layout === 'mobile' ? (
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
