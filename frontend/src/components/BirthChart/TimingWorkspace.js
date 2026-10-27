import React, { useEffect, useMemo, useState } from 'react';
import { apiErrorMessage, apiService } from '../../services/apiService';
import ChartWidget from '../Charts/ChartWidget';
import './TimingWorkspace.css';

const TOPIC_GROUPS = [
  {
    key: 'progeny', label: 'Progeny', topics: [
      { key: 'conception', label: 'Conception', houses: [5, 9, 11], varga: 'D7' },
      { key: 'delivery', label: 'Delivery', houses: [5, 9, 11], varga: 'D7' },
      { key: 'children', label: 'Child-related matters', houses: [2, 5, 9, 11], varga: 'D7' },
    ],
  },
  {
    key: 'relationships', label: 'Relationships', topics: [
      { key: 'relationship_meeting', label: 'Meeting / beginning', houses: [5, 7, 11], varga: 'D9' },
      { key: 'engagement', label: 'Engagement', houses: [2, 7, 9, 11], varga: 'D9' },
      { key: 'marriage', label: 'Marriage', houses: [2, 5, 7, 9, 11], varga: 'D9' },
    ],
  },
  {
    key: 'work', label: 'Work', topics: [
      { key: 'new_job', label: 'New Job', houses: [2, 6, 10, 11], varga: 'D10' },
      { key: 'job_change', label: 'Job Change', houses: [2, 3, 6, 10, 11], varga: 'D10' },
      { key: 'promotion', label: 'Promotion', houses: [2, 5, 10, 11], varga: 'D10' },
      { key: 'compensation', label: 'Pay Growth', houses: [2, 5, 6, 10, 11], varga: 'D10' },
      { key: 'work_disruption', label: 'Work Disruption', houses: [2, 6, 8, 10, 11, 12], varga: 'D10' },
    ],
  },
  {
    key: 'money', label: 'Money', topics: [
      { key: 'income_gain', label: 'Income / gains', houses: [2, 5, 9, 11], varga: 'D2' },
      { key: 'speculative_gain', label: 'Speculative trading', houses: [2, 5, 9, 11], varga: 'D2' },
    ],
  },
  {
    key: 'property', label: 'Property', topics: [
      { key: 'property_purchase', label: 'Purchase', houses: [2, 4, 8, 11], varga: 'D4' },
      { key: 'property_gain', label: 'Gain', houses: [2, 4, 11], varga: 'D4' },
      { key: 'relocation', label: 'Relocation', houses: [3, 4, 9, 11, 12], varga: 'D4' },
      { key: 'vehicle_purchase', label: 'Vehicle', houses: [2, 4, 11], varga: 'D4' },
    ],
  },
  {
    key: 'health', label: 'Health', topics: [
      { key: 'health', label: 'Health timing', houses: [1, 6, 8, 12], varga: 'D30' },
    ],
  },
  {
    key: 'learning', label: 'Learning', topics: [
      { key: 'education', label: 'Education', houses: [4, 5, 9, 11], varga: 'D24' },
    ],
  },
  {
    key: 'travel', label: 'Travel', topics: [
      { key: 'foreign_travel', label: 'Foreign Travel', houses: [3, 9, 11, 12], varga: 'D9' },
    ],
  },
];

const TOPICS = TOPIC_GROUPS.flatMap((group) => group.topics);

const formatDate = (value, options = { day: 'numeric', month: 'short' }) => {
  if (!value) return '—';
  const parsed = new Date(`${String(value).slice(0, 10)}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? String(value) : new Intl.DateTimeFormat('en-IN', options).format(parsed);
};

const dashaPath = (dasha) => [dasha?.mahadasha, dasha?.antardasha, dasha?.pratyantardasha]
  .filter(Boolean).join(' → ') || '—';

function relationLabel(value) {
  return String(value || '').replaceAll('_', ' ');
}

function dashaEvidence(window) {
  const seen = new Set();
  const rows = (window?.calculation_trace || [])
    .flatMap((step) => Array.isArray(step.evidence) ? step.evidence : []);
  const facts = rows.flatMap((row) => (row.natal_connections || []).map((connection) => ({
    house: row.house,
    planet: connection.planet,
    level: connection.level,
    relation: connection.relation,
  }))).filter((item) => {
    const key = `${item.house}:${item.planet}:${item.level}:${item.relation}`;
    if (!item.planet || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  if (!facts.length) return `Active Dasha: ${dashaPath(window?.dasha)}.`;
  return facts.map((item) => (
    `${item.planet}${item.level ? ` (${item.level})` : ''} opens House ${item.house}${item.relation ? ` by ${relationLabel(item.relation)}` : ''}`
  ));
}

function dashaConnections(window) {
  const seen = new Set();
  return (window?.calculation_trace || [])
    .flatMap((step) => Array.isArray(step.evidence) ? step.evidence : [])
    .flatMap((row) => (row.natal_connections || []).map((connection) => ({
      house: row.house,
      planet: connection.planet,
      level: connection.level,
      relation: connection.relation,
    })))
    .filter((item) => {
      const key = `${item.house}:${item.planet}:${item.level}:${item.relation}`;
      if (!item.planet || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

function transitEvidence(window) {
  const seen = new Set();
  const exact = (window?.calculation_trace || [])
    .find((step) => step.key === 'independent_confirmation')?.evidence?.exact_and_repetition_confirmations || [];
  const rows = (window?.calculation_trace || [])
    .flatMap((step) => Array.isArray(step.evidence) ? step.evidence : [])
    .filter(Boolean);
  const direct = rows
    .flatMap((row) => (row.transit_connections || []).filter((item) => item.timing_trigger).map((item) => ({
      planet: item.planet,
      house: row.house,
      transitHouse: item.transit_house,
      relations: item.relations || [],
      startDate: window?.start_date,
      endDate: window?.end_date,
    }))).filter((item) => {
      const key = `${item.planet}:${item.house}:${item.transitHouse}:${item.relations.join(',')}`;
      if (!item.planet || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  const exactItems = exact.map((item) => ({
    label: item.label || `${item.planet || 'Transit'} exact contact`,
    house: item.house,
    exactDate: item.exact_at ? String(item.exact_at).slice(0, 10) : null,
    startDate: item.start_at ? String(item.start_at).slice(0, 10) : null,
    endDate: item.end_at ? String(item.end_at).slice(0, 10) : null,
    orb: item.orb_degrees,
  })).filter((item) => {
    const key = `${item.label}:${item.house}:${item.exactDate}:${item.startDate}:${item.endDate}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  const short = rows.flatMap((row) => (row.timing_triggers || []).map((trigger) => ({ ...trigger, house: row.house })))
    .filter((item) => item.kind === 'sun_reinforcement' || item.kind === 'moon_peak')
    .filter((item) => {
      const key = `${item.kind}:${item.house}:${item.start_date}:${item.end_date}:${item.sun_house || item.moon_house}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  return { direct, exact: exactItems, short };
}

function formatRange(startDate, endDate) {
  if (!startDate && !endDate) return 'Recorded within this calculation slice';
  return `${formatDate(startDate)} – ${formatDate(endDate, { day: 'numeric', month: 'short', year: 'numeric' })}`;
}

function boundaryLabel(items, fallback) {
  if (!items?.length) return fallback;
  return items.map((item) => (
    typeof item === 'object' ? item.label || item.kind || 'Calculation boundary' : relationLabel(item)
  )).join(' · ');
}

function divisionalEvidence(window, fallbackChart) {
  const confirmation = (window?.calculation_trace || [])
    .find((step) => step.key === 'divisional_confirmation')?.evidence;
  const chart = confirmation?.chart || fallbackChart;
  const matches = confirmation?.matches || [];
  const details = matches.map((item) => (
    `${item.planet} carries ${chart} House ${item.house} by ${(item.relations || []).map(relationLabel).join(' / ')}`
  ));
  return {
    chart,
    passed: Boolean(confirmation?.passed),
    matches,
    details,
    explanation: confirmation?.explanation || `${chart} confirmation is unavailable for this period.`,
  };
}

function promiseTone(status) {
  return ({ supportive: 'supportive', mixed: 'mixed', pressured: 'challenging' })[status] || 'neutral';
}

function precisionSummary(window) {
  const precision = window?.precision;
  if (!precision) return { label: 'Timing resolution unavailable', date: null, explanation: 'The calculation did not return a precision ledger.' };
  return {
    label: precision.label || 'Timing resolution',
    date: precision.grade === 'date_trigger' ? (precision.date || window?.peak_date) : null,
    explanation: precision.explanation || 'No additional precision explanation was returned.',
  };
}

function addMonths(value, months) {
  const source = new Date(`${String(value).slice(0, 10)}T12:00:00`);
  const targetMonth = source.getMonth() + Number(months);
  const lastDay = new Date(source.getFullYear(), targetMonth + 1, 0).getDate();
  const target = new Date(source.getFullYear(), targetMonth, Math.min(source.getDate(), lastDay));
  return target.toISOString().slice(0, 10);
}

function rangePosition(value, start, end) {
  const date = new Date(`${String(value || '').slice(0, 10)}T00:00:00`);
  const rangeStart = new Date(`${String(start || '').slice(0, 10)}T00:00:00`);
  const rangeEnd = new Date(`${String(end || '').slice(0, 10)}T23:59:59`);
  if (Number.isNaN(date.getTime()) || Number.isNaN(rangeStart.getTime()) || Number.isNaN(rangeEnd.getTime()) || rangeEnd <= rangeStart) return 0;
  return ((date - rangeStart) / (rangeEnd - rangeStart)) * 100;
}

function windowStyle(window, rangeStart, rangeEnd) {
  const start = Math.max(0, rangePosition(window.start_date, rangeStart, rangeEnd));
  const end = Math.min(100, Math.max(start + 2, rangePosition(window.end_date, rangeStart, rangeEnd)));
  return { left: `${start}%`, width: `${Math.max(4, end - start)}%` };
}

function mergeDashaLanes(windows, level) {
  const keyByLevel = { MD: 'mahadasha', AD: 'antardasha', PD: 'pratyantardasha' };
  const key = keyByLevel[level];
  const sorted = [...windows].sort((a, b) => String(a.start_date).localeCompare(String(b.start_date)));
  return sorted.reduce((lanes, window) => {
    const planet = window.dasha?.[key];
    if (!planet) return lanes;
    const previous = lanes[lanes.length - 1];
    const previousEnd = new Date(`${previous?.end_date}T00:00:00`);
    const nextStart = new Date(`${window.start_date}T00:00:00`);
    const isContinuous = previousEnd instanceof Date && !Number.isNaN(previousEnd.getTime())
      && !Number.isNaN(nextStart.getTime())
      && nextStart.getTime() <= previousEnd.getTime() + 24 * 60 * 60 * 1000;
    if (previous && previous.planet === planet && isContinuous) {
      if (previous.end_date < window.end_date) previous.end_date = window.end_date;
      return lanes;
    }
    lanes.push({ window_id: `${level}-${window.window_id}`, planet, start_date: window.start_date, end_date: window.end_date, level });
    return lanes;
  }, []);
}

function transitLanes(windows) {
  const seen = new Set();
  return windows.flatMap((window) => {
    const evidence = transitEvidence(window);
    return [
      ...evidence.direct.map((item) => ({
        ...item,
        kind: 'direct',
        label: `${item.planet} → House ${item.house}`,
        windowId: window.window_id,
      })),
      ...evidence.exact.filter((item) => item.startDate && item.endDate).map((item) => ({
        ...item,
        kind: 'exact',
        planet: item.label.split(' ')[0] || 'Transit',
        label: item.house ? `Exact → House ${item.house}` : 'Exact return',
        windowId: window.window_id,
      })),
      ...evidence.short.map((item) => ({
        kind: 'short',
        planet: item.kind === 'sun_reinforcement' ? 'Sun' : 'Moon',
        house: item.house,
        startDate: item.start_date,
        endDate: item.end_date,
        label: `${item.kind === 'sun_reinforcement' ? 'Sun' : 'Moon'} → House ${item.house}`,
        windowId: window.window_id,
      })),
    ];
  }).filter((item) => {
    const key = `${item.kind}:${item.planet}:${item.house}:${item.startDate}:${item.endDate}`;
    if (!item.startDate || !item.endDate || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export default function TimingWorkspace({
  birthData,
  chartData,
  calculationProfile,
  activationResult,
  asOf,
  onInspectDate,
  onSelectMapDate,
}) {
  const [topicGroupKey, setTopicGroupKey] = useState('progeny');
  const [topicKey, setTopicKey] = useState('conception');
  const [year, setYear] = useState(() => Number(String(asOf || new Date().toISOString()).slice(0, 4)));
  const [rangeMode, setRangeMode] = useState('calendar');
  const [customStart, setCustomStart] = useState(() => String(asOf || new Date().toISOString()).slice(0, 10));
  const [customEnd, setCustomEnd] = useState(() => addMonths(String(asOf || new Date().toISOString()).slice(0, 10), 12));
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchedTopicKey, setSearchedTopicKey] = useState('conception');
  const [searchVersion, setSearchVersion] = useState(0);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedExactTriggerId, setSelectedExactTriggerId] = useState(null);
  const [selectedTransitLaneKey, setSelectedTransitLaneKey] = useState(null);
  const [selectedMapDate, setSelectedMapDate] = useState(null);
  const [showFastTriggers, setShowFastTriggers] = useState(false);
  const [chartInspection, setChartInspection] = useState(null);
  const [natalEvidenceOpen, setNatalEvidenceOpen] = useState(false);
  const [houseInsights, setHouseInsights] = useState([]);
  const [natalEvidenceLoading, setNatalEvidenceLoading] = useState(false);
  const [natalEvidenceError, setNatalEvidenceError] = useState('');
  const topicGroup = TOPIC_GROUPS.find((group) => group.key === topicGroupKey) || TOPIC_GROUPS[0];
  const topic = TOPICS.find((item) => item.key === topicKey) || topicGroup.topics[0];
  const chartId = birthData?.chart_id || birthData?.birth_chart_id || birthData?.id || null;

  useEffect(() => {
    const asOfDate = String(asOf || new Date().toISOString()).slice(0, 10);
    setYear(Number(asOfDate.slice(0, 4)));
    setCustomStart(asOfDate);
    setCustomEnd(addMonths(asOfDate, 12));
    setSelectedMapDate(asOfDate);
  }, [asOf]);

  const requestedHorizon = useMemo(() => {
    if (rangeMode === 'calendar') {
      return {
        start: `${year}-01-01`, end: `${year}-12-31`, label: `calendar year ${year}`, year,
      };
    }
    if (rangeMode === 'custom') {
      return { start: customStart, end: customEnd, label: `${formatDate(customStart, { day: 'numeric', month: 'short', year: 'numeric' })} – ${formatDate(customEnd, { day: 'numeric', month: 'short', year: 'numeric' })}`, year: null };
    }
    const months = Number(rangeMode);
    const end = new Date(`${addMonths(customStart, months)}T12:00:00`);
    end.setDate(end.getDate() - 1);
    return { start: customStart, end: end.toISOString().slice(0, 10), label: `next ${months} months`, year: null };
  }, [customEnd, customStart, rangeMode, year]);

  useEffect(() => {
    setNatalEvidenceOpen(false);
    setHouseInsights([]);
    setNatalEvidenceLoading(false);
    setNatalEvidenceError('');
  }, [topicKey]);

  useEffect(() => {
    if (!birthData || !natalEvidenceOpen) return undefined;
    let cancelled = false;
    setNatalEvidenceLoading(true);
    setNatalEvidenceError('');
    Promise.all(topic.houses.map((houseNum) => apiService.getHouseInsight({
      birthData,
      houseNum,
      chartId: 'lagna',
      transitDate: asOf,
      calculationProfile,
    }))).then((rows) => {
      if (!cancelled) setHouseInsights(rows.filter(Boolean));
    }).catch((requestError) => {
      if (!cancelled) setNatalEvidenceError(apiErrorMessage(requestError, 'Natal assessments could not be loaded.'));
    }).finally(() => {
      if (!cancelled) setNatalEvidenceLoading(false);
    });
    return () => { cancelled = true; };
  }, [asOf, birthData, calculationProfile, natalEvidenceOpen, topic]);

  useEffect(() => {
    if (!birthData || searchedTopicKey !== topic.key) return undefined;
    let cancelled = false;
    setLoading(true);
    setError('');
    setData(null);
    setSelectedId(null);
    setSelectedExactTriggerId(null);
    setSelectedTransitLaneKey(null);
    apiService.getEventWindows({
      birthChartId: chartId,
      birthData,
      eventKey: topic.key,
      year: requestedHorizon.year,
      startDate: requestedHorizon.year ? null : requestedHorizon.start,
      endDate: requestedHorizon.year ? null : requestedHorizon.end,
      includeDeveloping: true,
      calculationProfile,
    }).then((result) => {
      if (cancelled) return;
      setData(result);
      const initialWindow = result.windows?.find((item) => (
        item.start_date <= asOf && item.end_date >= asOf
      )) || result.windows?.find((item) => Number(item.peak_rank) >= 2) || result.windows?.[0];
      setSelectedId(initialWindow?.window_id || null);
    }).catch((requestError) => {
      if (!cancelled) setError(apiErrorMessage(requestError, 'Could not calculate timing windows.'));
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [birthData, calculationProfile, chartId, requestedHorizon.end, requestedHorizon.start, requestedHorizon.year, searchedTopicKey, searchVersion, topic.key]);

  const preciseWindows = useMemo(() => (
    (data?.windows || []).filter((item) => Number(item.peak_rank) >= 2)
  ), [data]);
  const broadWindows = useMemo(() => (
    (data?.windows || []).filter((item) => Number(item.peak_rank) < 2)
  ), [data]);
  const selectedWindow = useMemo(() => (
    preciseWindows.find((item) => item.window_id === selectedId)
      || broadWindows.find((item) => item.window_id === selectedId)
      || preciseWindows[0]
      || broadWindows[0]
      || null
  ), [broadWindows, preciseWindows, selectedId]);
  const exactTriggers = useMemo(() => preciseWindows.flatMap((window) => (
    transitEvidence(window).exact.map((item, index) => ({
      ...item,
      windowId: window.window_id,
      id: `${window.window_id}-${item.label}-${index}`,
      date: item.exactDate || window.peak_date,
    }))
  )), [preciseWindows]);
  const selectedExactTrigger = useMemo(() => (
    exactTriggers.find((trigger) => trigger.id === selectedExactTriggerId) || null
  ), [exactTriggers, selectedExactTriggerId]);
  useEffect(() => {
    if (exactTriggers.length && !exactTriggers.some((trigger) => trigger.id === selectedExactTriggerId)) {
      setSelectedExactTriggerId(exactTriggers[0].id);
    }
  }, [exactTriggers, selectedExactTriggerId]);
  const currentDasha = activationResult?.house_activations?.find((item) => (
    item.window?.start_date <= asOf && item.window?.end_date >= asOf
  ))?.window;
  const selectedDashaEvidence = dashaEvidence(selectedWindow);
  const selectedDashaConnections = dashaConnections(selectedWindow);
  const selectedTransitEvidence = transitEvidence(selectedWindow);
  const hasTransitTiming = selectedTransitEvidence.direct.length > 0
    || selectedTransitEvidence.exact.length > 0
    || selectedTransitEvidence.short.length > 0;
  const selectedDivisionalEvidence = divisionalEvidence(selectedWindow, topic.varga);
  const topicVargaConfirmation = selectedDivisionalEvidence;
  const eventNatalPromise = data?.natal_promise || null;
  const selectedPrecision = precisionSummary(selectedWindow);
  const verdict = preciseWindows.length
    ? `${preciseWindows.length} ${topic.label.toLowerCase()} activation period${preciseWindows.length === 1 ? '' : 's'} with ${exactTriggers.length || preciseWindows.length} date-level transit trigger${(exactTriggers.length || preciseWindows.length) === 1 ? '' : 's'} in the selected horizon.`
    : broadWindows.length
      ? `${broadWindows.length} ${topic.label.toLowerCase()} activation period${broadWindows.length === 1 ? '' : 's'} found in the selected horizon; no date-level transit trigger was isolated.`
      : `No activated ${topic.label.toLowerCase()} period was found in the selected horizon.`;
  const allWindows = useMemo(() => data?.windows || [], [data]);
  const dashaLanes = useMemo(() => {
    const raw = data?.timing_map?.dasha;
    if (!raw) return {
      MD: mergeDashaLanes(allWindows, 'MD'),
      AD: mergeDashaLanes(allWindows, 'AD'),
      PD: mergeDashaLanes(allWindows, 'PD'),
    };
    return Object.fromEntries(['MD', 'AD', 'PD'].map((level) => [level, (raw[level] || []).map((item, index) => ({
      window_id: `${level}-${item.start_date}-${index}`,
      planet: item[level],
      start_date: item.start_date,
      end_date: item.end_date,
      level,
    }))]));
  }, [allWindows, data]);
  const activeTransitLanes = useMemo(() => {
    const raw = data?.timing_map?.transits;
    if (!raw) return transitLanes(allWindows);
    return raw.map((item, index) => ({
      kind: 'direct',
      planet: item.planet,
      house: item.target_house,
      transitHouse: item.source_house,
      relations: item.relations || [],
      startDate: item.start_date,
      endDate: item.end_date,
      windowId: allWindows.find((window) => (
        window.start_date <= item.start_date && window.end_date >= item.start_date
      ))?.window_id,
      label: `${item.planet} · House ${item.source_house} → House ${item.target_house}`,
      key: `${item.planet}-${item.source_house}-${item.target_house}-${item.start_date}-${index}`,
    }));
  }, [allWindows, data]);
  const displayedTransitLanes = useMemo(() => activeTransitLanes.filter((lane) => (
    showFastTriggers || !['Moon', 'Sun'].includes(lane.planet)
  )), [activeTransitLanes, showFastTriggers]);
  const selectedTransitLane = useMemo(() => (
    displayedTransitLanes.find((lane, index) => (
      (lane.key || `${lane.kind}-${lane.planet}-${lane.house}-${lane.startDate}-${index}`)
      === selectedTransitLaneKey
    )) || null
  ), [displayedTransitLanes, selectedTransitLaneKey]);
  const windowInspectionDate = selectedWindow?.inspection_date || selectedWindow?.peak_date || selectedWindow?.start_date;
  const selectedDate = selectedMapDate || windowInspectionDate;
  const mapStart = data?.as_of || requestedHorizon.start;
  const mapEnd = data?.horizon_end || requestedHorizon.end;
  const selectedPosition = Math.min(100, Math.max(0, rangePosition(selectedDate, mapStart, mapEnd)));
  const dashaAtSelectedDate = useMemo(() => Object.fromEntries(
    ['MD', 'AD', 'PD'].map((level) => [level, dashaLanes[level]?.find((lane) => (
      lane.start_date <= selectedDate && lane.end_date >= selectedDate
    ))?.planet || null])
  ), [dashaLanes, selectedDate]);
  const activeHouseCounts = useMemo(() => {
    const counts = new Map(topic.houses.map((house) => [house, 0]));
    if (selectedTransitLane) {
      if (counts.has(selectedTransitLane.house)) counts.set(selectedTransitLane.house, 1);
      return counts;
    }
    [
      ...selectedDashaConnections,
      ...selectedTransitEvidence.direct,
      ...selectedTransitEvidence.exact,
      ...selectedTransitEvidence.short,
    ].forEach((item) => {
      if (counts.has(item.house)) counts.set(item.house, counts.get(item.house) + 1);
    });
    return counts;
  }, [selectedDashaConnections, selectedTransitEvidence, selectedTransitLane, topic.houses]);

  const inspectNatalEvidence = () => {
    if (natalEvidenceOpen) {
      setNatalEvidenceOpen(false);
      return;
    }
    setNatalEvidenceOpen(true);
  };

  const selectMapDate = (date, windowId = null) => {
    if (!date) return;
    setSelectedMapDate(date);
    if (windowId) setSelectedId(windowId);
    onSelectMapDate?.(date);
  };
  const openChartInspection = ({ date, label, house = null, planet = null }) => {
    if (!date || !chartData) return;
    setChartInspection({ date, label, house, planet });
  };

  useEffect(() => {
    if (!chartInspection) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setChartInspection(null);
    };
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [chartInspection]);

  return (
    <section className="timing-workspace" aria-label="Topic timing workspace">
      <div className="timing-topic-bar">
        <div className="timing-topic-tabs" role="tablist" aria-label="Timing category">
          {TOPIC_GROUPS.map((group) => (
            <button
              type="button"
              key={group.key}
              className={group.key === topicGroup.key ? 'is-active' : ''}
              aria-selected={group.key === topicGroup.key}
              onClick={() => {
                setTopicGroupKey(group.key);
                setTopicKey(group.topics[0].key);
                setSearchedTopicKey(group.topics[0].key);
                setData(null);
                setError('');
              }}
            >{group.label}</button>
          ))}
        </div>
        <div className="timing-horizon-picker" aria-label="Timing search horizon">
          <label>Horizon
            <select value={rangeMode} onChange={(event) => setRangeMode(event.target.value)}>
              <option value="calendar">Calendar year</option>
              <option value="3">Next 3 months</option>
              <option value="6">Next 6 months</option>
              <option value="12">Next 12 months</option>
              <option value="24">Next 24 months</option>
              <option value="custom">Custom range</option>
            </select>
          </label>
          {rangeMode === 'calendar' ? <label>Year
            <select value={year} onChange={(event) => setYear(Number(event.target.value))}>
              {[year - 1, year, year + 1].map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
          </label> : null}
          {rangeMode === 'custom' ? <>
            <label>From <input type="date" value={customStart} onChange={(event) => setCustomStart(event.target.value)} /></label>
            <label>To <input type="date" value={customEnd} min={customStart} onChange={(event) => setCustomEnd(event.target.value)} /></label>
          </> : null}
        </div>
      </div>

      <div className="timing-topic-subtabs" role="tablist" aria-label={`${topicGroup.label} timing tools`}>
        {topicGroup.topics.map((item) => (
          <button
            type="button"
            key={item.key}
            className={item.key === topic.key ? 'is-active' : ''}
            aria-selected={item.key === topic.key}
            onClick={() => { setTopicKey(item.key); setSearchedTopicKey(item.key); setData(null); setError(''); }}
          >{item.label}</button>
        ))}
      </div>

      <div className="timing-search-control">
        <p>Timing windows load for the selected horizon. Use a past custom range to validate known events; it does not rewrite the original calculation.</p>
        <button type="button" onClick={() => setSearchVersion((version) => version + 1)} disabled={!birthData || loading}>
          {loading && searchedTopicKey === topic.key ? 'Calculating…' : `Refresh ${topic.label} windows`}
        </button>
      </div>

      <section className="timing-context" aria-label="Current timing context">
        <div className={`timing-promise-verdict timing-promise-verdict--${promiseTone(eventNatalPromise?.status)}`}>
          <span>D1 natal event promise</span>
          <strong>{eventNatalPromise?.label || (loading ? 'Assessing natal promise…' : 'Natal promise unavailable')}</strong>
          {eventNatalPromise ? <p>{eventNatalPromise.interpretation}</p> : null}
          {eventNatalPromise?.houses?.length ? <div className="timing-natal-assessment-chips">{eventNatalPromise.houses.map((item) => <span key={`${item.role}-${item.house}`} className={`timing-natal-assessment-chip timing-natal-assessment-chip--${promiseTone(item.tone)}`}><b>House {item.house}{' '}</b><small>{item.role} · {item.tone}</small></span>)}</div> : null}
        </div>
        <div>
          <span>Dasha now</span>
          <strong>{dashaPath(currentDasha)}</strong>
        </div>
        <button type="button" onClick={inspectNatalEvidence}>{natalEvidenceOpen ? 'Hide house-by-house audit' : 'Inspect house-by-house audit'}</button>
      </section>

      {data?.calculation_context ? <section className="timing-calculation-context" aria-label="Timing calculation context">
        <div><span>Calculation basis</span><strong>{calculationProfile?.ayanamsha || 'lahiri'} ayanamsha · {calculationProfile?.node_type || 'mean'} nodes</strong></div>
        <div><span>Birth-chart timezone</span><strong>{data.calculation_context.birth_timezone || 'Not recorded'}</strong></div>
        <div><span>Precision boundary</span><p>{data.calculation_context.precision_policy}</p></div>
      </section> : null}

      {topicVargaConfirmation ? (
        <section className="timing-d7-confirmation" aria-label={`${topicVargaConfirmation.chart} ${topic.label} confirmation`}>
          <div className="timing-d7-confirmation__intro">
            <span>{topicVargaConfirmation.chart} divisional chart</span>
            <h3>{topic.label} confirmation</h3>
            <p>
              {selectedWindow
                ? `This checks whether an active Dasha lord connects with the relevant ${topicVargaConfirmation.chart} houses during the selected ${topic.label} window.`
                : `Choose a ${topic.label} timing window to check its ${topicVargaConfirmation.chart} confirmation.`}
            </p>
          </div>
          <div className={`timing-d7-confirmation__status ${selectedWindow && topicVargaConfirmation.passed ? 'is-confirmed' : ''}`}>
            <span>Window result</span>
            <strong>{selectedWindow ? (topicVargaConfirmation.passed ? `${topicVargaConfirmation.chart} confirmed` : `No direct ${topicVargaConfirmation.chart} confirmation`) : 'Awaiting a timing window'}</strong>
          </div>
          <div className="timing-d7-confirmation__evidence">
            <span>Active Dasha connection</span>
            {selectedWindow && topicVargaConfirmation.passed ? (
              <ul>
                {topicVargaConfirmation.matches.map((match, index) => (
                  <li key={`${match.planet}-${match.house}-${index}`}>
                    <b>{match.planet}</b> connects to {topicVargaConfirmation.chart} House {match.house} by {(match.relations || []).map(relationLabel).join(' / ')}.
                  </li>
                ))}
              </ul>
            ) : (
              <p>{selectedWindow ? topicVargaConfirmation.explanation : `${topicVargaConfirmation.chart} is assessed from the active Mahadasha, Antardasha and Pratyantardasha of the selected window.`}</p>
            )}
          </div>
          <button
            type="button"
            className="timing-d7-confirmation__action"
            disabled={!chartData}
            onClick={() => openChartInspection({
              date: selectedDate || asOf,
              label: `${topicVargaConfirmation.chart} — ${topic.label} confirmation`,
              house: topicVargaConfirmation.matches[0]?.house || topic.houses[0],
              planet: topicVargaConfirmation.matches[0]?.planet || null,
            })}
          >
            View {topicVargaConfirmation.chart} chart comparison
          </button>
        </section>
      ) : null}

      {natalEvidenceOpen ? (
        <section className="timing-natal-evidence" aria-label={`${topic.label} natal evidence`}>
          <header>
            <div><span>D1 natal evidence</span><h3>{topic.label} house-by-house judgment</h3></div>
            <p>These are the same natal house judgments available from the chart; Dasha and transits are not used to determine this verdict.</p>
          </header>
          {natalEvidenceLoading ? <p className="timing-evidence-state">Loading natal house judgments…</p> : null}
          {natalEvidenceError ? <p className="timing-evidence-state timing-evidence-state--error">{natalEvidenceError}</p> : null}
          {!natalEvidenceLoading && !natalEvidenceError ? (
            <div className="timing-natal-evidence-grid">
              {houseInsights.map((insight) => (
                <article key={insight.house_num}>
                  <div className="timing-natal-evidence-heading">
                    <strong>House {insight.house_num}</strong>
                    <span>{insight.verdict?.label || 'Natal assessment'}</span>
                  </div>
                  <p>{insight.interpretation || 'No interpretation was returned for this house.'}</p>
                  <div className="timing-natal-factor-columns">
                    <div><b>Supports</b>{(insight.support_factors || []).length ? <ul>{insight.support_factors.map((factor, index) => <li key={`${factor.label}-${index}`}>{factor.label}</li>)}</ul> : <small>No decisive supporting testimony.</small>}</div>
                    <div><b>Pressure</b>{(insight.stress_factors || []).length ? <ul>{insight.stress_factors.map((factor, index) => <li key={`${factor.label}-${index}`}>{factor.label}</li>)}</ul> : <small>No decisive pressure testimony.</small>}</div>
                  </div>
                </article>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      {searchedTopicKey === topic.key ? (
        <div className="timing-section-heading">
          <div><span>Timing assessment</span><h2>{verdict}</h2></div>
          <p>An exact transit trigger is a defined contact at its calculated moment. It narrows an activation period; it does not confirm that the life event occurs on that date.</p>
        </div>
      ) : null}

      {loading ? <div className="timing-state">Calculating natal, Dasha, transit and {topic.varga} evidence…</div> : null}
      {error ? <div className="timing-state timing-state--error" role="alert">{error}</div> : null}
      {!loading && !error && searchedTopicKey !== topic.key ? <div className="timing-state">No search has been run for this topic yet.</div> : null}
      {!loading && !error && data ? (
        <>
          {exactTriggers.length ? <section className="timing-exact-triggers" aria-label="Exact transit triggers">
            <div><span>Exact transit triggers</span><p>These are date-level contacts within an activation period. Select one to inspect the Dasha, natal promise and house context.</p></div>
            <div>{exactTriggers.map((trigger) => <div className="timing-exact-trigger" key={trigger.id}><button type="button" className={trigger.id === selectedExactTriggerId ? 'is-selected' : ''} onClick={() => { setSelectedExactTriggerId(trigger.id); setSelectedTransitLaneKey(null); selectMapDate(trigger.date, trigger.windowId); }}><b>{trigger.house ? `House ${trigger.house} · ` : ''}{trigger.label}</b><small>{trigger.date ? formatDate(trigger.date, { day: 'numeric', month: 'short', year: 'numeric' }) : 'Date recorded in selected slice'}</small></button><button type="button" className="timing-exact-trigger__chart" aria-label={`Open charts for ${trigger.label}`} title="Open chart comparison" onClick={() => openChartInspection({ date: trigger.date, label: trigger.label, house: trigger.house, planet: trigger.planet })}>⌑</button></div>)}</div>
          </section> : null}
          <section className="timing-map" aria-label={`${topic.label} timing map for ${requestedHorizon.label}`}>
            <div className="timing-map-key"><span><i className="timing-map-key--dasha" />Dasha permission</span><span><i className="timing-map-key--transit" />Transit activation</span><span><i className="timing-map-key--exact" />Exact trigger</span><label><input type="checkbox" checked={showFastTriggers} onChange={(event) => setShowFastTriggers(event.target.checked)} /> Show fast triggers (Sun / Moon)</label></div>
            <div className="timing-map-months"><span /><div className="timing-map-range-labels"><span>{formatDate(mapStart, { day: 'numeric', month: 'short', year: 'numeric' })}</span><span>{formatDate(mapEnd, { day: 'numeric', month: 'short', year: 'numeric' })}</span></div></div>
            {['MD', 'AD', 'PD'].map((level) => (
              <div className="timing-map-lane" key={level}>
                <strong>{level === 'MD' ? 'Mahadasha' : level === 'AD' ? 'Antardasha' : 'Pratyantardasha'}</strong>
                <div className="timing-map-track">
                  {dashaLanes[level].map((lane) => <span key={lane.window_id} className={`timing-map-bar timing-map-bar--dasha timing-map-bar--${level.toLowerCase()}`} style={windowStyle(lane, mapStart, mapEnd)} title={`${lane.planet}: ${formatRange(lane.start_date, lane.end_date)}`}><b>{lane.planet}</b><small className="timing-map-dasha-range">{formatRange(lane.start_date, lane.end_date)}</small></span>)}
                  {level === 'MD' && selectedDate ? <i className="timing-map-cursor" style={{ left: `${selectedPosition}%` }}><b>As of · {formatDate(selectedDate)}</b></i> : null}
                </div>
              </div>
            ))}
            <div className="timing-map-divider"><span>Transit timing</span></div>
            {displayedTransitLanes.map((lane, index) => {
              const laneKey = lane.key || `${lane.kind}-${lane.planet}-${lane.house}-${lane.startDate}-${index}`;
              return <div className="timing-map-lane" key={laneKey}>
                <div className="timing-map-lane-label"><strong>{lane.planet} transit</strong><button type="button" aria-label={`Open charts for ${lane.label}`} title="Open chart comparison" onClick={() => openChartInspection({ date: lane.startDate, label: lane.label, house: lane.house, planet: lane.planet })}>⌑</button></div>
                <div className="timing-map-track">
                  <button type="button" className={`timing-map-bar timing-map-bar--${lane.kind}${laneKey === selectedTransitLaneKey ? ' is-selected' : ''}`} style={windowStyle({ start_date: lane.startDate, end_date: lane.endDate }, mapStart, mapEnd)} onClick={() => { setSelectedTransitLaneKey(laneKey); selectMapDate(lane.startDate, lane.windowId); }} title={`${lane.label}: ${formatRange(lane.startDate, lane.endDate)}`}>{lane.label}</button>
                </div>
              </div>;
            })}
            {!displayedTransitLanes.length ? <p className="timing-map-empty">No slower-planet transit activation was found for these topic houses in this horizon.</p> : null}
            <div className="timing-house-rail">
              <div><span>Selected date</span><strong>{selectedDate ? formatDate(selectedDate, { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}</strong></div>
              <section aria-label="Activated topic houses">{topic.houses.map((house) => {
                const count = activeHouseCounts.get(house) || 0;
                return <div key={house} className={count ? 'is-active' : ''}><b>House {house}</b><small>{count ? `${count} active link${count === 1 ? '' : 's'}` : 'No active link'}</small></div>;
              })}</section>
            </div>
            <p className="timing-slice-note"><strong>How to read this map:</strong> the top three lanes show what the Dasha permits; the lower lanes show the separate transit activation and its actual duration. A transit contact narrows a period—it is not, by itself, an event outcome. Select a transit bar to inspect its house links and calculation slice.</p>
          </section>

          {selectedTransitLane ? (
            <section className="timing-window-detail">
              <article>
                <span className="timing-overline">Selected transit activation</span>
                <h3>{formatRange(selectedTransitLane.startDate, selectedTransitLane.endDate)}</h3>
                <p>This is the full duration of this raw transit contact. It is not an event verdict and does not inherit evidence from another calculation slice.</p>
                <div className="timing-slice-boundaries">
                  <span><b>Transit begins</b>{formatDate(selectedTransitLane.startDate, { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                  <span><b>Transit ends</b>{formatDate(selectedTransitLane.endDate, { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                </div>
                <div className="timing-evidence-list">
                  <div><i>1</i><span><strong>Dasha context at the selected date</strong>{['MD', 'AD', 'PD'].map((level) => dashaAtSelectedDate[level] ? `${level}: ${dashaAtSelectedDate[level]}` : null).filter(Boolean).join(' · ') || 'No Dasha row was available for the selected date.'}</span></div>
                  <div><i>2</i><span><strong>Transit house activation</strong><b>{selectedTransitLane.planet}</b> travels through House {selectedTransitLane.transitHouse} and activates House {selectedTransitLane.house} by {(selectedTransitLane.relations || []).map(relationLabel).join(' / ') || 'transit contact'}. <small>Active for the entire lane: {formatRange(selectedTransitLane.startDate, selectedTransitLane.endDate)}.</small></span></div>
                  <div><i>3</i><span><strong>Exact transit trigger</strong>No exact contact is implied by this duration lane. Exact contacts, if calculated, appear separately as date-level triggers.</span></div>
                </div>
              </article>
              <aside>
                <span className="timing-overline">Selected date</span>
                <strong>{selectedDate ? formatDate(selectedDate, { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}</strong>
                <p>Use the Activation Ledger to inspect the complete calculation state for this date.</p>
                <button type="button" className="timing-chart-inspect-button" onClick={() => openChartInspection({ date: selectedDate, label: selectedTransitLane.label, house: selectedTransitLane.house, planet: selectedTransitLane.planet })}>View natal, {topic.varga} and transit charts</button>
                <button type="button" onClick={() => onInspectDate?.(selectedDate)}>Inspect this date in Activation Ledger →</button>
              </aside>
            </section>
          ) : selectedWindow ? (
            <section className="timing-window-detail">
              <article>
                <span className="timing-overline">{hasTransitTiming ? 'Calculated Dasha + transit slice' : 'Calculated Dasha-led slice'}</span>
                <h3>{formatDate(selectedWindow.start_date)} – {formatDate(selectedWindow.end_date, { day: 'numeric', month: 'short', year: 'numeric' })}</h3>
                <p>This is the span during which the engine held the same Dasha stack and transit-state signature. It is a calculation boundary, not a claim that every transit lasts this long.</p>
                <div className="timing-slice-boundaries">
                  <span><b>Slice opened by</b>{boundaryLabel(selectedWindow.calculation_slice?.opened_by, 'the start of the requested horizon')}</span>
                  <span><b>Slice ended by</b>{boundaryLabel(selectedWindow.calculation_slice?.closed_by, 'the end of the requested horizon')}</span>
                </div>
                <div className="timing-evidence-list">
                  <div><i>1</i><span><strong>D1 natal promise</strong>{eventNatalPromise ? <>{eventNatalPromise.label}. {eventNatalPromise.interpretation}</> : 'Natal promise was unavailable for this calculation.'}</span></div>
                  <div><i>2</i><span><strong>Dasha permission</strong>{selectedDashaEvidence.join(' · ')}</span></div>
                  <div><i>3</i><span><strong>Transit house activation</strong>{selectedTransitEvidence.direct.length ? <div className="timing-transit-rows">{selectedTransitEvidence.direct.map((item, index) => <p key={`${item.planet}-${item.house}-${index}`}><b>{item.planet}:</b> from House {item.transitHouse || '—'} activates House {item.house} by {item.relations.map(relationLabel).join(' / ') || 'transit contact'}. <small>Active for this slice: {formatRange(item.startDate, item.endDate)}.</small></p>)}</div> : 'No Dasha-carrier transit directly activates a selected house in this slice.'}</span></div>
                  <div><i>4</i><span><strong>Exact or repeating transit trigger</strong>{selectedTransitEvidence.exact.length ? <div className="timing-transit-rows">{selectedTransitEvidence.exact.map((item, index) => <p key={`${item.label}-${index}`}><b>{item.house ? `House ${item.house}: ` : ''}</b>{item.label}. <small>{item.startDate && item.endDate ? `Orb window: ${formatRange(item.startDate, item.endDate)}${item.orb ? ` (±${item.orb}°)` : ''}.` : item.exactDate ? `Exact on ${formatDate(item.exactDate, { day: 'numeric', month: 'short', year: 'numeric' })}; recorded in this calculation slice.` : 'Recorded in this calculation slice.'}</small></p>)}</div> : 'No exact return or repeated natal contact was isolated in this slice.'}</span></div>
                  <div><i>5</i><span><strong>Short Sun / Moon reinforcement</strong>{selectedTransitEvidence.short.length ? <div className="timing-transit-rows">{selectedTransitEvidence.short.map((item, index) => <p key={`${item.kind}-${item.house}-${index}`}>{item.kind === 'sun_reinforcement' ? <>Sun in House {item.sun_house} reinforces active {item.activated_dasha_lords?.join(' / ')} for House {item.house}.</> : <>Moon in House {item.moon_house} activates House {item.house} by {(item.house_relations || []).map(relationLabel).join(' / ')}, while contacting natal {item.natal_carriers_contacted?.join(' / ')}.</>} <small>Duration: {formatRange(item.start_date, item.end_date)}.</small></p>)}</div> : 'No short Sun or Moon reinforcement was recorded in this slice.'}</span></div>
                  <div><i>6</i><span><strong>{selectedDivisionalEvidence.chart} confirmation</strong>{selectedDivisionalEvidence.passed ? selectedDivisionalEvidence.details.join(' · ') : selectedDivisionalEvidence.explanation}</span></div>
                  <div><i>7</i><span><strong>Counter-evidence / limits</strong>{selectedWindow.counter_evidence?.length ? <div className="timing-transit-rows">{selectedWindow.counter_evidence.map((item, index) => <p key={`${item.kind}-${index}`}><b>{item.label}.</b> <small>{item.detail}</small></p>)}</div> : 'No additional counter-evidence was identified by this event contract.'}</span></div>
                </div>
              </article>
              <aside>
                <span className="timing-overline">{selectedPrecision.label}</span>
                <strong>{selectedPrecision.date ? formatDate(selectedPrecision.date, { day: 'numeric', month: 'short', year: 'numeric' }) : 'No date isolated'}</strong>
                <p>{selectedPrecision.explanation}</p>
                <button type="button" className="timing-chart-inspect-button" onClick={() => openChartInspection({ date: selectedExactTrigger?.date || selectedWindow.inspection_date || selectedWindow.start_date, label: selectedExactTrigger?.label || `${topic.label} timing slice`, house: selectedExactTrigger?.house })}>View natal, {topic.varga} and transit charts</button>
                <button type="button" onClick={() => onInspectDate?.(selectedWindow.inspection_date || selectedWindow.start_date)}>Inspect this date in Activation Ledger →</button>
              </aside>
            </section>
          ) : null}
        </>
      ) : null}
      {chartInspection ? (
        <div className="timing-chart-drawer-backdrop" role="presentation" onMouseDown={() => setChartInspection(null)}>
          <section className="timing-chart-drawer" role="dialog" aria-modal="true" aria-labelledby="timing-chart-drawer-title" onMouseDown={(event) => event.stopPropagation()}>
            <header>
              <div>
                <span className="timing-overline">Chart comparison</span>
                <h2 id="timing-chart-drawer-title">{chartInspection.label}</h2>
                <p>Transit chart set to {formatDate(chartInspection.date, { day: 'numeric', month: 'short', year: 'numeric' })}.</p>
              </div>
              <button type="button" aria-label="Close chart comparison" onClick={() => setChartInspection(null)}>×</button>
            </header>
            <div className="timing-chart-drawer__grid">
              <article><div><strong>D1</strong><span>Natal chart</span></div><ChartWidget title="D1" chartType="lagna" chartData={chartData} birthData={birthData} defaultStyle="north" showFooterHint={false} embedInDashboard deskMode selectedHouseNumber={chartInspection.house} highlightedPlanets={chartInspection.planet ? [chartInspection.planet] : null} calculationProfile={calculationProfile} /></article>
              <article><div><strong>{topic.varga}</strong><span>{topic.label} confirmation</span></div><ChartWidget title={topic.varga} chartType={topic.varga === 'D9' ? 'navamsa' : 'divisional'} division={Number(topic.varga.slice(1))} chartData={chartData} birthData={birthData} defaultStyle="north" showFooterHint={false} embedInDashboard deskMode selectedHouseNumber={chartInspection.house} calculationProfile={calculationProfile} /></article>
              <article><div><strong>Transit D1</strong><span>As-of sky</span></div><ChartWidget key={`transit-${chartInspection.date}`} title="Transit" chartType="transit" transitDate={chartInspection.date} chartData={chartData} birthData={birthData} defaultStyle="north" showFooterHint={false} embedInDashboard deskMode selectedHouseNumber={chartInspection.house} highlightedPlanets={chartInspection.planet ? [chartInspection.planet] : null} calculationProfile={calculationProfile} /></article>
            </div>
          </section>
        </div>
      ) : null}
    </section>
  );
}
