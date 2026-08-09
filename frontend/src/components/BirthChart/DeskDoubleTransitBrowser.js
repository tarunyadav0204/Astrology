import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { apiService } from '../../services/apiService';
import './DeskDoubleTransitBrowser.css';

const AREA_HOUSES = {
  all: null,
  career: new Set([2, 6, 10, 11]),
  relationship: new Set([2, 7, 11]),
  wealth: new Set([2, 5, 8, 11]),
  children: new Set([2, 5, 9, 11]),
  property: new Set([4, 8, 11]),
  health: new Set([1, 6, 8, 12]),
  education: new Set([4, 5, 9]),
  travel: new Set([3, 9, 12]),
};

const SIGN_ABBR = {
  Aries: 'Ari', Taurus: 'Tau', Gemini: 'Gem', Cancer: 'Can',
  Leo: 'Leo', Virgo: 'Vir', Libra: 'Lib', Scorpio: 'Sco',
  Sagittarius: 'Sag', Capricorn: 'Cap', Aquarius: 'Aqu', Pisces: 'Pis',
};

const YEAR_OPTIONS = Array.from({ length: 600 }, (_, index) => 1800 + index);

function isoDay(value) {
  return String(value || '').slice(0, 10);
}

function birthYearFrom(value) {
  const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return null;
  const year = Number(match[1]);
  return Number.isInteger(year) && year >= 1 ? year : null;
}

function formatMoment(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return { date: String(value || '—'), time: '' };
  return {
    date: date.toLocaleDateString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
    }),
    time: date.toLocaleTimeString('en-GB', {
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      timeZoneName: 'short',
    }),
  };
}

function formatDuration(days) {
  const count = Number(days);
  if (!Number.isFinite(count)) return '';
  if (count >= 365) return `${(count / 365.2425).toFixed(1)} years`;
  if (count >= 60) return `${Math.round(count / 30.44)} months`;
  return `${Math.max(1, Math.round(count))} days`;
}

function ordinal(value) {
  const number = Number(value);
  if (number % 100 >= 11 && number % 100 <= 13) return `${number}th`;
  return `${number}${number % 10 === 1 ? 'st' : number % 10 === 2 ? 'nd' : number % 10 === 3 ? 'rd' : 'th'}`;
}

function windowDuration(window) {
  const start = Date.parse(window?.start_at);
  const end = Date.parse(window?.end_at);
  return Number.isFinite(start) && Number.isFinite(end) ? (end - start) / 86400000 : null;
}

function transitLine(label, planet) {
  if (!planet) return null;
  const sign = SIGN_ABBR[planet.sign_name] || planet.sign_name;
  const relation = planet.mode === 'occupies'
    ? `occupies H${planet.house}`
    : `${ordinal(planet.aspect_number)} aspect from H${planet.house}`;
  return `${label} · ${sign} · ${relation}`;
}

function DoubleTransitCard({ window, onSelect }) {
  const natal = window.natal || {};
  const occupants = natal.occupants?.length ? natal.occupants.join(', ') : 'none';
  const starts = formatMoment(window.start_at);
  const until = formatMoment(window.end_at);
  return (
    <article
      className={`desk-dt__card desk-dt__card--${window.status}${onSelect ? ' desk-dt__card--selectable' : ''}`}
      role={onSelect ? 'button' : undefined}
      tabIndex={onSelect ? 0 : undefined}
      aria-label={onSelect ? `Set desk as-of to the start of this House ${window.house} double-transit window` : undefined}
      onClick={onSelect ? () => onSelect(window) : undefined}
      onKeyDown={onSelect ? (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onSelect(window);
        }
      } : undefined}
    >
      <header className="desk-dt__card-head">
        <div>
          <span>
            <i>Starts</i>
            <time dateTime={window.start_at}><b>{starts.date}</b><small>{starts.time}</small></time>
          </span>
          <span>
            <i>Until</i>
            <time dateTime={window.end_at}><b>{until.date}</b><small>{until.time}</small></time>
          </span>
          <em>{formatDuration(windowDuration(window))}</em>
        </div>
        <strong>{window.status === 'full' ? 'Full double transit' : 'Aspect-only contact'}</strong>
      </header>

      <div className="desk-dt__house">
        <b>H{window.house}</b>
        <div>
          <strong>{window.house_title}</strong>
          <span>{window.themes}</span>
        </div>
      </div>

      <div className="desk-dt__planets">
        <span>{transitLine('Jupiter', window.jupiter)}</span>
        <span>{transitLine('Saturn', window.saturn)}</span>
      </div>

      <p className="desk-dt__summary">{window.activation_summary}</p>

      <div className="desk-dt__natal">
        <span>Natal H{window.house}</span>
        <strong>{natal.sign_name} · lord {natal.lord}</strong>
        <em>Occupants: {occupants}</em>
      </div>

      <p className="desk-dt__rule">
        <strong>Interpretation rule</strong>
        {window.manifestation_rule}
      </p>
    </article>
  );
}

export default function DeskDoubleTransitBrowser({ birthData, chartData, onJumpToDate }) {
  const currentYear = new Date().getFullYear();
  const birthYear = birthYearFrom(birthData?.date);
  const chartFingerprint = [
    birthData?.date,
    chartData?.ascendant,
    ...['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
      .map((planet) => chartData?.planets?.[planet]?.longitude),
  ].join('|');
  const [startYear, setStartYear] = useState(birthYear || currentYear);
  const [endYear, setEndYear] = useState(Math.min(currentYear + 15, (birthYear || currentYear) + 119));
  const [phase, setPhase] = useState('current');
  const [strength, setStrength] = useState('all');
  const [area, setArea] = useState('all');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const requestIdRef = useRef(0);
  const mobileEndYears = useMemo(() => {
    const from = Number(startYear);
    if (!Number.isInteger(from)) return [];
    return YEAR_OPTIONS.filter((year) => year >= from && year <= Math.min(2399, from + 119));
  }, [startYear]);

  const selectMobileStartYear = (value) => {
    const year = Number(value);
    setStartYear(year);
    setEndYear((previous) => Math.min(Math.max(Number(previous), year), Math.min(2399, year + 119)));
  };

  const calculate = useCallback(async (signal, requestedRange) => {
    const requestId = ++requestIdRef.current;
    setError('');
    setLoading(false);
    if (!birthYear) {
      setResult(null);
      setError('The saved chart has no valid birth date. No transit result was produced.');
      return;
    }
    if (typeof chartData?.ascendant !== 'number' || !Number.isFinite(chartData.ascendant)) {
      setResult(null);
      setError('The chart has no verified ascendant longitude. No transit result was produced.');
      return;
    }
    const from = Number(requestedRange?.from ?? startYear);
    const to = Number(requestedRange?.to ?? endYear);
    if (!Number.isInteger(from) || !Number.isInteger(to) || from < 1800 || to > 2399 || to < from || to - from >= 120) {
      setResult(null);
      setError('Choose a valid range within 1800–2399, spanning no more than 120 years.');
      return;
    }

    setResult(null);
    setLoading(true);
    try {
      const data = await apiService.getDoubleTransits({
        chartData,
        startDate: from === birthYear ? isoDay(birthData.date) : `${from}-01-01`,
        endDate: `${to}-12-31`,
        includeAspectOnly: true,
      });
      if (!signal?.cancelled && requestId === requestIdRef.current) setResult(data);
    } catch (requestError) {
      if (!signal?.cancelled && requestId === requestIdRef.current) {
        setResult(null);
        setError(requestError?.response?.data?.detail || 'The exact ephemeris calculation failed. No fallback result was produced.');
      }
    } finally {
      if (!signal?.cancelled && requestId === requestIdRef.current) setLoading(false);
    }
  }, [birthData?.date, birthYear, chartData, endYear, startYear]);

  useEffect(() => {
    const signal = { cancelled: false };
    const initialStart = birthYear || currentYear;
    const initialEnd = Math.min(currentYear + 15, initialStart + 119);
    setStartYear(initialStart);
    setEndYear(initialEnd);
    calculate(signal, { from: initialStart, to: initialEnd });
    return () => { signal.cancelled = true; };
  // Recalculate only when the native/chart changes, not while editing year fields.
  }, [chartFingerprint]);

  const windows = useMemo(() => {
    const now = new Date().toISOString();
    const houseSet = AREA_HOUSES[area];
    return (result?.windows || []).filter((window) => {
      const start = window.start_at;
      const end = window.end_at;
      if (phase === 'current' && !(start <= now && end > now)) return false;
      if (phase === 'future' && start <= now) return false;
      if (phase === 'past' && end > now) return false;
      if (strength !== 'all' && window.status !== strength) return false;
      if (houseSet && !houseSet.has(window.house)) return false;
      return true;
    }).sort((a, b) => (
      phase === 'past'
        ? String(b.start_at).localeCompare(String(a.start_at))
        : String(a.start_at).localeCompare(String(b.start_at))
    ));
  }, [area, phase, result, strength]);

  const counts = useMemo(() => {
    const now = new Date().toISOString();
    return (result?.windows || []).reduce((acc, window) => {
      const start = window.start_at;
      const end = window.end_at;
      if (start <= now && end > now) acc.current += 1;
      else if (start > now) acc.future += 1;
      else acc.past += 1;
      return acc;
    }, { current: 0, future: 0, past: 0 });
  }, [result]);

  const selectWindow = (window) => {
    if (!onJumpToDate) return;
    const start = new Date(window?.start_at);
    if (!Number.isNaN(start.getTime())) onJumpToDate(start);
  };

  return (
    <section className="desk-dt" aria-label="Double transit browser">
      <header className="desk-dt__intro">
        <div>
          <span className="desk-dt__eyebrow">Jupiter × Saturn</span>
          <h3>Double Transit Browser</h3>
          <p>Exact periods when both planets activate the same natal house.</p>
        </div>
        <div className="desk-dt__method" title="Calculation contract returned by the server">
          <strong>Lahiri · whole sign</strong>
          <span>Swiss Ephemeris · 1-second ingress boundary</span>
        </div>
      </header>

      <div className="desk-dt__controls">
        <label>
          <span>From year</span>
          <input className="desk-dt__year-input" type="number" value={startYear} min="1800" max="2399" onChange={(event) => setStartYear(event.target.value)} />
          <select className="desk-dt__year-select" value={startYear} onChange={(event) => selectMobileStartYear(event.target.value)} aria-label="From year">
            {YEAR_OPTIONS.map((year) => <option key={`from-${year}`} value={year}>{year}</option>)}
          </select>
        </label>
        <label>
          <span>Through year</span>
          <input className="desk-dt__year-input" type="number" value={endYear} min="1800" max="2399" onChange={(event) => setEndYear(event.target.value)} />
          <select className="desk-dt__year-select" value={endYear} onChange={(event) => setEndYear(Number(event.target.value))} aria-label="Through year">
            {mobileEndYears.map((year) => <option key={`through-${year}`} value={year}>{year}</option>)}
          </select>
        </label>
        <button type="button" onClick={() => calculate()} disabled={loading}>
          {loading ? 'Calculating…' : 'Calculate exact windows'}
        </button>
      </div>

      {error ? (
        <div className="desk-dt__error" role="alert">
          <strong>Double transit unavailable</strong>
          <span>{error}</span>
          <button type="button" onClick={() => calculate()}>Retry exact calculation</button>
        </div>
      ) : null}

      {result ? (
        <>
          <div className="desk-dt__tabs" role="tablist" aria-label="Transit period">
            {[
              ['current', 'Current', counts.current],
              ['future', 'Future', counts.future],
              ['past', 'Past', counts.past],
            ].map(([id, label, count]) => (
              <button key={id} type="button" role="tab" aria-selected={phase === id} className={phase === id ? 'is-active' : ''} onClick={() => setPhase(id)}>
                {label}<span>{count}</span>
              </button>
            ))}
          </div>

          <div className="desk-dt__filters">
            <label>
              <span>Contact</span>
              <select value={strength} onChange={(event) => setStrength(event.target.value)}>
                <option value="all">Full + aspect-only</option>
                <option value="full">Full double transits</option>
                <option value="aspect_only">Aspect-only contacts</option>
              </select>
            </label>
            <label>
              <span>Life area</span>
              <select value={area} onChange={(event) => setArea(event.target.value)}>
                <option value="all">All houses</option>
                <option value="career">Career</option>
                <option value="relationship">Relationships</option>
                <option value="wealth">Wealth</option>
                <option value="children">Children</option>
                <option value="property">Property</option>
                <option value="health">Health</option>
                <option value="education">Education</option>
                <option value="travel">Travel</option>
              </select>
            </label>
            <span className="desk-dt__shown">{windows.length} shown</span>
          </div>

          <div className="desk-dt__definition">
            <strong>Full</strong> Both activate one house and at least one occupies it.
            <strong>Aspect-only</strong> Both activate it by Parāśari graha dṛṣṭi without occupation.
            <span> Start is inclusive; “until” is exclusive. Times use your device timezone.</span>
          </div>

          <div className="desk-dt__list">
            {windows.length ? windows.map((window) => (
              <DoubleTransitCard key={window.id} window={window} onSelect={onJumpToDate ? selectWindow : undefined} />
            )) : (
              <div className="desk-dt__empty">
                <strong>No matching window</strong>
                <span>The exact calculation found no window for these filters and dates.</span>
              </div>
            )}
          </div>
        </>
      ) : loading ? (
        <div className="desk-dt__loading"><i /><span>Computing exact Jupiter and Saturn sign intervals…</span></div>
      ) : null}
    </section>
  );
}
