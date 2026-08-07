import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { apiService } from '../../services/apiService';
import DeskSpecialPoints from './DeskSpecialPoints';
import './DeskDashaPanel.css';

const SYSTEMS = [
  { id: 'vimshottari', label: 'Vim', full: 'Vimshottari' },
  { id: 'yogini', label: 'Yog', full: 'Yogini' },
  { id: 'kalachakra', label: 'Kal', full: 'Kalachakra' },
  { id: 'chara', label: 'Cha', full: 'Chara' },
];

const PLANET_ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
};

const SIGN_ABBR = {
  Aries: 'Ar', Taurus: 'Ta', Gemini: 'Ge', Cancer: 'Cn',
  Leo: 'Le', Virgo: 'Vi', Libra: 'Li', Scorpio: 'Sc',
  Sagittarius: 'Sg', Capricorn: 'Cp', Aquarius: 'Aq', Pisces: 'Pi',
};

const YOGINI_ABBR = {
  Mangala: 'Mg', Pingala: 'Pi', Dhanya: 'Dh', Bhramari: 'Br',
  Bhadrika: 'Bd', Ulka: 'Ul', Siddha: 'Si', Sankata: 'Sk',
};

const VIM_LEVELS = [
  { key: 'maha', label: 'MD', full: 'Maha' },
  { key: 'antar', label: 'AD', full: 'Antar' },
  { key: 'pratyantar', label: 'PD', full: 'Pratyantar' },
  { key: 'sookshma', label: 'SD', full: 'Sookshma' },
  { key: 'prana', label: 'Pr', full: 'Prana' },
];

function abbr(name, system) {
  if (!name) return '—';
  if (PLANET_ABBR[name]) return PLANET_ABBR[name];
  if (system === 'chara' && SIGN_ABBR[name]) return SIGN_ABBR[name];
  if (system === 'yogini' && YOGINI_ABBR[name]) return YOGINI_ABBR[name];
  if (SIGN_ABBR[name]) return SIGN_ABBR[name];
  return String(name).slice(0, 2);
}

function formatShortDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: '2-digit' });
}

function formatLocalDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/** Parse API YYYY-MM-DD as local calendar date (avoid UTC off-by-one). */
function parsePeriodDate(value) {
  if (!value) return null;
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return new Date(value.getFullYear(), value.getMonth(), value.getDate(), 12, 0, 0, 0);
  }
  const str = String(value).split('T')[0];
  const [y, m, d] = str.split('-').map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d, 12, 0, 0, 0);
}

/**
 * Cascading API marks "current" with target_date at midnight.
 * Periods often start mid-day, so midnight on the start date is still inside
 * the previous period — jump to the next calendar day when the period allows.
 */
function jumpDateForPeriod(period) {
  const start = parsePeriodDate(period?.start);
  const end = parsePeriodDate(period?.end);
  if (!start) return null;
  if (!end || end.getTime() <= start.getTime()) return start;
  const nextDay = new Date(start);
  nextDay.setDate(nextDay.getDate() + 1);
  return nextDay.getTime() <= end.getTime() ? nextDay : start;
}

function progressPct(start, end, asOf) {
  const a = new Date(start).getTime();
  const b = new Date(end).getTime();
  const t = asOf.getTime();
  if (!(a < b)) return 0;
  if (t <= a) return 0;
  if (t >= b) return 100;
  return Math.round(((t - a) / (b - a)) * 100);
}

function remainingLabel(end, asOf) {
  const diff = new Date(end).getTime() - asOf.getTime();
  if (diff <= 0) return 'ended';
  const days = Math.ceil(diff / 86400000);
  const y = Math.floor(days / 365);
  const m = Math.floor((days % 365) / 30);
  if (y > 0) return `${y}y ${m}m left`;
  if (m > 0) return `${m}m ${days % 30}d left`;
  return `${days}d left`;
}

function inRange(start, end, asOf) {
  const t = parsePeriodDate(asOf);
  const a = parsePeriodDate(start);
  const b = parsePeriodDate(end);
  if (!t || !a || !b) return false;
  const tt = t.getTime();
  return tt >= a.getTime() && tt <= b.getTime();
}

function sameDay(a, b) {
  if (!a || !b) return false;
  return String(a).slice(0, 10) === String(b).slice(0, 10);
}

function birthPayload(birthData) {
  let dateStr = birthData.date || '';
  if (dateStr.includes('T')) dateStr = dateStr.split('T')[0];
  let timeStr = birthData.time || '12:00';
  if (String(timeStr).includes('T')) {
    try {
      timeStr = new Date(timeStr).toTimeString().slice(0, 5);
    } catch {
      timeStr = String(timeStr).slice(11, 16) || '12:00';
    }
  }
  return {
    name: birthData.name || 'Unknown',
    date: dateStr,
    time: timeStr,
    latitude: parseFloat(birthData.latitude),
    longitude: parseFloat(birthData.longitude),
    place: birthData.place || 'Unknown',
  };
}

function row(name, start, end, current) {
  return { name, start, end, current: Boolean(current) };
}

function normalizeVimshottari(data, asOf) {
  const map = {
    maha: data?.maha_dashas,
    antar: data?.antar_dashas,
    pratyantar: data?.pratyantar_dashas,
    sookshma: data?.sookshma_dashas,
    prana: data?.prana_dashas,
  };
  return {
    levels: VIM_LEVELS.map((level) => {
      const rows = (map[level.key] || []).map((d) =>
        row(d.planet, d.start, d.end, Boolean(d.current))
      );
      // If API left every row unmarked (midnight edge cases), recover from as-of day.
      if (rows.length && !rows.some((r) => r.current)) {
        rows.forEach((r) => {
          r.current = inRange(r.start, r.end, asOf);
        });
      }
      return { ...level, rows };
    }),
  };
}

function normalizeYogini(data, asOf) {
  const timeline = data?.timeline || [];
  const currentMaha = data?.current?.mahadasha;
  const currentAntar = data?.current?.antardasha;

  const mahaRows = timeline.map((d) =>
    row(
      d.name,
      d.start,
      d.end,
      currentMaha
        ? d.name === currentMaha.name && sameDay(d.start, currentMaha.start) && sameDay(d.end, currentMaha.end)
        : inRange(d.start, d.end, asOf)
    )
  );

  const currentOrAsOfMaha =
    timeline.find((d, i) => mahaRows[i]?.current) ||
    timeline.find((d) => inRange(d.start, d.end, asOf)) ||
    (currentMaha
      ? timeline.find(
          (d) =>
            d.name === currentMaha.name &&
            sameDay(d.start, currentMaha.start) &&
            sameDay(d.end, currentMaha.end)
        )
      : null);

  const antarSource = currentOrAsOfMaha?.sub_periods || [];

  // Prefer API current AD by name: balance-MD sub_periods often don't share exact
  // start/end strings with current.antardasha, so exact date match alone misses.
  const antarRows = antarSource.map((d) => {
    const byApiCurrent =
      !!currentAntar &&
      d.name === currentAntar.name &&
      (sameDay(d.start, currentAntar.start) ||
        antarSource.filter((x) => x.name === d.name).length === 1);
    return row(d.name, d.start, d.end, byApiCurrent || inRange(d.start, d.end, asOf));
  });

  return {
    levels: [
      { key: 'maha', label: 'MD', full: 'Maha', rows: mahaRows },
      { key: 'antar', label: 'AD', full: 'Antar', rows: antarRows },
    ],
  };
}

function normalizeKalachakra(data, asOf) {
  const mahas = data?.mahadashas || [];
  const mahaRows = mahas.map((d) => row(d.name, d.start, d.end, inRange(d.start, d.end, asOf)));
  const currentMaha = mahas.find((d) => inRange(d.start, d.end, asOf));
  const antarSource = (data?.all_antardashas || []).filter(
    (a) => currentMaha && a.maha_name === currentMaha.name
  );
  const antarRows = antarSource.map((d) => row(d.name, d.start, d.end, inRange(d.start, d.end, asOf)));

  return {
    levels: [
      { key: 'maha', label: 'MD', full: 'Maha', rows: mahaRows },
      { key: 'antar', label: 'AD', full: 'Antar', rows: antarRows },
    ],
    meta: data?.deha
      ? { deha: data.deha, jeeva: data.jeeva, direction: data.direction }
      : null,
  };
}

async function normalizeChara(data, birthData, asOf) {
  const periods = data?.periods || [];
  const mahaRows = periods.map((d) =>
    row(d.sign_name, d.start_date, d.end_date, inRange(d.start_date, d.end_date, asOf))
  );
  const currentIdx = periods.findIndex((d) => inRange(d.start_date, d.end_date, asOf));
  let antarRows = [];

  if (currentIdx >= 0) {
    const current = periods[currentIdx];
    let subs = current.sub_periods;
    if (!subs) {
      try {
        const payload = { ...birthPayload(birthData), maha_sign_id: current.sign_id };
        const response = await fetch('/api/chara-dasha/antardasha', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (response.ok) {
          const result = await response.json();
          if (result.status === 'success') subs = result.antar_periods;
        }
      } catch {
        subs = [];
      }
    }
    antarRows = (subs || []).map((d) =>
      row(d.sign, d.start_date, d.end_date, inRange(d.start_date, d.end_date, asOf))
    );
  }

  return {
    levels: [
      { key: 'maha', label: 'MD', full: 'Maha', rows: mahaRows },
      { key: 'antar', label: 'AD', full: 'Antar', rows: antarRows },
    ],
  };
}

/**
 * Working-desk dasha view with Vimshottari / Yogini / Kalachakra / Chara.
 * Click a period to jump the shared as-of clock.
 */
const DeskDashaPanel = ({ birthData, chartData, asOfDate, onJumpToDate, system, onSystemChange }) => {
  const [view, setView] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const listRefs = useRef({});
  const activeSystem = system || 'vimshottari';
  const setSystem = onSystemChange || (() => {});

  // Calendar day only — ignore clock drift from ±D/W/M navigators vs noon picker.
  const asOfKey = useMemo(
    () => (asOfDate instanceof Date && !Number.isNaN(asOfDate.getTime())
      ? formatLocalDate(asOfDate)
      : ''),
    [asOfDate]
  );

  const load = useCallback(async (signal) => {
    if (!birthData?.date || !asOfKey) {
      if (!signal?.aborted) setView(null);
      return;
    }
    if (!signal?.aborted) {
      setLoading(true);
      setError(null);
    }
    const target = asOfKey;
    const asOfNoon = parsePeriodDate(asOfKey);
    const payload = birthPayload(birthData);

    try {
      let next = null;
      if (activeSystem === 'vimshottari') {
        const data = await apiService.calculateCascadingDashas(birthData, target);
        if (signal?.aborted) return;
        next = normalizeVimshottari(data, asOfNoon);
      } else if (activeSystem === 'yogini') {
        const response = await fetch('/api/yogini-dasha', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...payload, years: 5, target_date: target }),
          signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        next = normalizeYogini(data, asOfNoon);
      } else if (activeSystem === 'kalachakra') {
        const response = await fetch('/api/calculate-kalchakra-dasha', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ birth_data: payload, target_date: target }),
          signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data.error) throw new Error(data.error);
        next = normalizeKalachakra(data, asOfNoon);
      } else if (activeSystem === 'chara') {
        const response = await fetch('/api/chara-dasha/calculate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data.status !== 'success') throw new Error(data.error || 'Chara failed');
        next = await normalizeChara(data, birthData, asOfNoon);
      }
      if (!signal?.aborted) setView(next);
    } catch (err) {
      if (err?.name === 'AbortError') return;
      if (!signal?.aborted) {
        setError(err?.message || 'Failed to load dashas');
        setView(null);
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [birthData, asOfKey, activeSystem]);

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const levels = view?.levels || [];
  const path = useMemo(
    () => levels.map((level) => level.rows.find((r) => r.current)).filter(Boolean),
    [levels]
  );

  useEffect(() => {
    levels.forEach((level) => {
      const el = listRefs.current[level.key];
      if (!el) return;
      const current = el.querySelector('[data-current="true"]');
      if (current) current.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    });
  }, [levels]);

  const handleSelect = (period) => {
    if (!onJumpToDate) return;
    const jump = jumpDateForPeriod(period);
    if (!jump) return;
    onJumpToDate(jump);
  };

  const systemMeta = SYSTEMS.find((s) => s.id === activeSystem);

  return (
    <div className="desk-dasha">
      <div className="desk-dasha__meta">
        <div className="desk-dasha__path" title={`Current ${systemMeta?.full || ''} stack at as-of`}>
          {path.length ? (
            path.map((p, i) => (
              <React.Fragment key={`${p.name}-${i}`}>
                {i > 0 ? <span className="desk-dasha__arrow">→</span> : null}
                <strong>{abbr(p.name, activeSystem)}</strong>
                <span className="desk-dasha__path-dates">
                  {formatShortDate(p.start)}–{formatShortDate(p.end)}
                </span>
              </React.Fragment>
            ))
          ) : (
            <span className="desk-dasha__muted">{loading ? 'Loading…' : 'No current stack'}</span>
          )}
          {view?.meta?.deha ? (
            <span className="desk-dasha__pillars">
              Deha {view.meta.deha} · Jeeva {view.meta.jeeva}
              {view.meta.direction ? ` · ${view.meta.direction}` : ''}
            </span>
          ) : null}
        </div>
        <div className="desk-dasha__right">
          {path[0] ? (
            <span className="desk-dasha__remain">{remainingLabel(path[0].end, asOfDate)}</span>
          ) : null}
          <div className="desk-dasha__systems" role="tablist" aria-label="Dasha system">
            {SYSTEMS.map((s) => (
              <button
                key={s.id}
                type="button"
                role="tab"
                aria-selected={activeSystem === s.id}
                className={activeSystem === s.id ? 'is-active' : ''}
                title={s.full}
                onClick={() => setSystem(s.id)}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error ? (
        <div className="desk-dasha__error">{error}</div>
      ) : (
        <div
          className={`desk-dasha__body${levels.length <= 2 ? ' desk-dasha__body--with-sp' : ''}`}
        >
          <div
            className="desk-dasha__cols"
            role="table"
            aria-label={`${systemMeta?.full || 'Dasha'} periods`}
            style={{
              gridTemplateColumns: `repeat(${Math.max(levels.length, 1)}, minmax(0, ${levels.length <= 2 ? '240px' : '1fr'}))`,
            }}
          >
            {levels.map((level) => (
              <div key={level.key} className="desk-dasha__col" role="rowgroup">
                <div className="desk-dasha__col-head" title={level.full}>
                  <span>{level.label}</span>
                  <em>{level.full}</em>
                </div>
                <div
                  className="desk-dasha__list"
                  ref={(node) => {
                    listRefs.current[level.key] = node;
                  }}
                >
                  {level.rows.length === 0 && !loading ? (
                    <div className="desk-dasha__empty">—</div>
                  ) : (
                    level.rows.map((period, index) => {
                      const isCurrent = Boolean(period.current);
                      const pct = isCurrent ? progressPct(period.start, period.end, asOfDate) : 0;
                      return (
                        <button
                          key={`${level.key}-${period.name}-${period.start}-${index}`}
                          type="button"
                          className={`desk-dasha__row${isCurrent ? ' is-current' : ''}`}
                          data-current={isCurrent ? 'true' : 'false'}
                          onClick={() => handleSelect(period)}
                          title={`Jump as-of to ${period.name} ${formatShortDate(period.start)}`}
                        >
                          <span className="desk-dasha__planet">{abbr(period.name, activeSystem)}</span>
                          <span className="desk-dasha__range">
                            {formatShortDate(period.start)}
                            <span aria-hidden="true">–</span>
                            {formatShortDate(period.end)}
                          </span>
                          {isCurrent ? (
                            <span className="desk-dasha__bar" aria-hidden="true">
                              <i style={{ width: `${pct}%` }} />
                            </span>
                          ) : null}
                        </button>
                      );
                    })
                  )}
                </div>
              </div>
            ))}
          </div>
          {levels.length <= 2 && chartData ? (
            <DeskSpecialPoints birthData={birthData} chartData={chartData} variant="panel" />
          ) : null}
        </div>
      )}
    </div>
  );
};

export default DeskDashaPanel;
