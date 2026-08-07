import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BirthFormModal from '../BirthForm/BirthFormModal';
import KPChart from '../KP/KPChart/KPChart';
import { useAstrology } from '../../context/AstrologyContext';
import { apiService } from '../../services/apiService';
import './KPDeskPage.css';

const NAKSHATRAS = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
  'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
  'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
  'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
  'Uttara Bhadrapada', 'Revati',
];

const SHORT = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me', Jupiter: 'Ju',
  Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke', Ascendant: 'Asc',
};

const RP_ROLE_SHORT = {
  day_lord: 'Day',
  moon_sign_lord: 'Mo SL',
  moon_star_lord: 'Mo NL',
  asc_sign_lord: 'Asc SL',
  asc_star_lord: 'Asc NL',
  asc_sub_lord: 'Asc SB',
  moon_sub_lord: 'Mo SB',
};

const PLANET_ORDER = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];

function shortPlanet(name) {
  if (!name) return '—';
  return SHORT[name] || String(name).slice(0, 2);
}

function formatLocalDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function formatLocalTime(d) {
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

function normalizeBirthClock(birthData) {
  const birthDate = String(birthData?.date || '').split('T')[0];
  let birthTime = String(birthData?.time || '');
  if (birthTime.includes('T')) birthTime = birthTime.split('T')[1];
  birthTime = birthTime.slice(0, 5);
  return { birthDate, birthTime };
}

function natalPayload(birthData) {
  const { birthDate, birthTime } = normalizeBirthClock(birthData);
  return {
    birth_date: birthDate,
    birth_time: birthTime,
    latitude: birthData.latitude,
    longitude: birthData.longitude,
    timezone: birthData.timezone || '',
  };
}

/** Mobile pattern: explore sky/significators by substituting moment into birth_date/time. */
function momentChartPayload(birthData, asOfDate, asOfTime) {
  return {
    birth_date: asOfDate,
    birth_time: asOfTime,
    latitude: birthData.latitude,
    longitude: birthData.longitude,
    timezone: birthData.timezone || '',
  };
}

function nakInfo(longitude) {
  const lon = ((Number(longitude) || 0) % 360 + 360) % 360;
  const nakIndex = Math.floor(lon / 13.333333) % 27;
  const pada = Math.floor((lon % 13.333333) / 3.333333) + 1;
  return { name: NAKSHATRAS[nakIndex] || '—', pada };
}

function buildPlanetRows(raw) {
  const positions = raw?.planet_positions || {};
  const lords = raw?.planet_lords || {};
  const keys = PLANET_ORDER.filter((p) => positions[p] != null);
  Object.keys(positions).forEach((p) => { if (!keys.includes(p)) keys.push(p); });
  return keys.map((planet) => ({
    planet,
    longitude: Number(positions[planet]) || 0,
    ...(lords[planet] || {}),
  }));
}

function buildCuspRows(raw) {
  const cusps = raw?.house_cusps || {};
  const lords = raw?.cusp_lords || {};
  return Array.from({ length: 12 }, (_, i) => {
    const key = String(i + 1);
    return {
      cusp: key,
      longitude: Number(cusps[key] ?? cusps[i + 1]) || 0,
      ...(lords[key] || lords[i + 1] || {}),
    };
  });
}

function buildChartWidgetData(raw) {
  const houses = [];
  const planets = [];
  const houseCusps = raw?.house_cusps || {};
  const planetPositions = raw?.planet_positions || {};
  for (let i = 1; i <= 12; i += 1) {
    houses.push({ number: i, cusp_longitude: Number(houseCusps[i] ?? houseCusps[String(i)]) || 0 });
  }
  Object.entries(planetPositions).forEach(([name, longitude]) => {
    planets.push({ name, longitude: Number(longitude) || 0 });
  });
  return { houses, planets };
}

function asList(value) {
  return Array.isArray(value) ? value : [];
}

function dashaPlanet(node) {
  if (!node) return '';
  if (typeof node === 'string') return node;
  return node.planet || node.lord || '';
}

function KPDeskPage({ user, onLogin }) {
  const navigate = useNavigate();
  const { birthData, setBirthData } = useAstrology();
  const [showBirthModal, setShowBirthModal] = useState(false);
  /** birth = natal chart/tables/sigs; asof = sky at as-of for chart/tables/sigs + predictions */
  const [viewMode, setViewMode] = useState('birth');
  const [asOfDate, setAsOfDate] = useState(() => formatLocalDate(new Date()));
  const [asOfTime, setAsOfTime] = useState(() => formatLocalTime(new Date()));
  const [natalRaw, setNatalRaw] = useState(null);
  const [momentRaw, setMomentRaw] = useState(null);
  const [rulingPlanets, setRulingPlanets] = useState(null);
  const [momentRulingPlanets, setMomentRulingPlanets] = useState(null);
  const [fruct, setFruct] = useState(null);
  const [fructLoading, setFructLoading] = useState(false);
  const [fructScope, setFructScope] = useState('today'); // today | hour
  const [expandedHouse, setExpandedHouse] = useState(null);
  const [calcOpen, setCalcOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedPlanet, setSelectedPlanet] = useState('Moon');
  const [sigPanel, setSigPanel] = useState('house');

  const hasChart = Boolean(
    birthData?.date && birthData?.time && birthData?.latitude != null && birthData?.longitude != null
  );

  const activeRaw = viewMode === 'asof' && momentRaw ? momentRaw : natalRaw;
  const planets = useMemo(() => buildPlanetRows(activeRaw), [activeRaw]);
  const cusps = useMemo(() => buildCuspRows(activeRaw), [activeRaw]);
  const chartWidget = useMemo(() => buildChartWidgetData(activeRaw), [activeRaw]);
  const significators = activeRaw?.significators || {};
  const planetSignificators = activeRaw?.planet_significators || {};
  const fourStep = activeRaw?.four_step_theory || {};
  const selectedSteps = fourStep[selectedPlanet] || null;
  const activeRp = viewMode === 'asof' && momentRulingPlanets ? momentRulingPlanets : rulingPlanets;

  const loadNatal = useCallback(async () => {
    if (!hasChart) return;
    setLoading(true);
    setError('');
    try {
      const payload = natalPayload(birthData);
      const [chartRes, rpRes] = await Promise.all([
        apiService.getKpChart(payload),
        apiService.getKpRulingPlanets(payload),
      ]);
      if (!(chartRes?.success && chartRes?.data)) {
        throw new Error(chartRes?.detail || 'Failed to load KP chart.');
      }
      setNatalRaw(chartRes.data);
      if (rpRes?.success && rpRes?.data) setRulingPlanets(rpRes.data);
      const keys = Object.keys(chartRes.data.planet_positions || {});
      setSelectedPlanet((prev) => (keys.includes(prev) ? prev : keys[1] || keys[0] || 'Moon'));
    } catch (e) {
      setNatalRaw(null);
      setError(e?.response?.data?.detail || e.message || 'Failed to load KP desk.');
    } finally {
      setLoading(false);
    }
  }, [birthData, hasChart]);

  const loadAsOf = useCallback(async () => {
    if (!hasChart || !asOfDate || !asOfTime) return;
    setFructLoading(true);
    try {
      const natal = natalPayload(birthData);
      const moment = momentChartPayload(birthData, asOfDate, asOfTime);
      const requests = [
        apiService.getKpFructification({
          ...natal,
          as_of_date: asOfDate,
          as_of_time: asOfTime,
          language: 'en',
          synthesize: true,
        }),
      ];
      if (viewMode === 'asof') {
        requests.push(
          apiService.getKpChart(moment),
          apiService.getKpRulingPlanets(moment),
        );
      }
      const [fructRes, chartRes, rpRes] = await Promise.all(requests);
      if (fructRes?.success && fructRes?.data) {
        setFruct(fructRes.data);
        setError('');
      } else {
        setFruct(null);
        setError(fructRes?.detail || 'Failed to load day/hour predictions.');
      }
      if (viewMode === 'asof') {
        if (chartRes?.success && chartRes?.data) setMomentRaw(chartRes.data);
        else setMomentRaw(null);
        if (rpRes?.success && rpRes?.data) setMomentRulingPlanets(rpRes.data);
        else setMomentRulingPlanets(null);
      }
    } catch (e) {
      setFruct(null);
      if (viewMode === 'asof') {
        setMomentRaw(null);
        setMomentRulingPlanets(null);
      }
      setError(e?.response?.data?.detail || e.message || 'Failed to load as-of data.');
    } finally {
      setFructLoading(false);
    }
  }, [asOfDate, asOfTime, birthData, hasChart, viewMode]);

  useEffect(() => {
    if (!user || !hasChart) return undefined;
    loadNatal();
    return undefined;
  }, [user, hasChart, loadNatal]);

  useEffect(() => {
    if (!user || !hasChart || !natalRaw) return undefined;
    const timer = setTimeout(() => { loadAsOf(); }, 180);
    return () => clearTimeout(timer);
  }, [user, hasChart, natalRaw, asOfDate, asOfTime, viewMode, loadAsOf]);

  useEffect(() => {
    setExpandedHouse(null);
    setCalcOpen(false);
  }, [fructScope, asOfDate, asOfTime]);

  const shiftAsOf = (days) => {
    const [y, m, d] = asOfDate.split('-').map(Number);
    const next = new Date(y, m - 1, d, 12, 0, 0, 0);
    next.setDate(next.getDate() + days);
    setAsOfDate(formatLocalDate(next));
    setViewMode('asof');
  };

  const setNow = () => {
    const now = new Date();
    setAsOfDate(formatLocalDate(now));
    setAsOfTime(formatLocalTime(now));
    setViewMode('asof');
  };

  const todayBlock = fruct?.today;
  const hourBlock = fruct?.hour;
  const scopeBlock = fructScope === 'hour' ? hourBlock : todayBlock;
  const dasha = fruct?.dasha || {};
  const asOfRps = scopeBlock?.ruling_planets_used || fruct?.ruling_planets || {};
  const rpAsc = activeRp?.ascendant || {};
  const rpMoon = activeRp?.moon || {};
  const dayLord = activeRp?.day_lord || asOfRps.day_lord;
  const viewLabel = viewMode === 'asof' ? 'As-of sky' : 'Natal';
  const primaryHouses = asList(scopeBlock?.houses_giving_results);
  const secondaryHouses = asList(scopeBlock?.houses_secondary);
  const manifestations = asList(scopeBlock?.manifestations);
  const calc = scopeBlock?.calculation || {};
  const gate = scopeBlock?.dasha_gate || {};

  const themeGroups = useMemo(() => {
    const order = ['self', 'spouse', 'mother', 'father'];
    const groups = [];
    manifestations.forEach((item) => {
      const subject = item.subject || 'self';
      const existing = groups.find((g) => g.subject === subject);
      if (existing) existing.items.push(item);
      else groups.push({ subject, items: [item] });
    });
    groups.sort((a, b) => {
      const ai = order.indexOf(a.subject);
      const bi = order.indexOf(b.subject);
      return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi);
    });
    return groups;
  }, [manifestations]);

  const subjectLabel = (subject) => (subject === 'self' ? 'For you' : `Your ${subject}`);
  const toneLabel = (tone) => (
    ({ supportive: 'Favourable', mixed: 'Mixed', challenging: 'Pressure', neutral: 'Steady' })[tone] || 'Steady'
  );

  return (
    <div className="kp-desk">
      <header className="kp-desk-bar">
        <div className="kp-desk-bar__left">
          <button type="button" className="kp-desk-bar__back" onClick={() => navigate('/charts-dashas')}>← Charts</button>
          <strong className="kp-desk-bar__brand">KP Desk</strong>
          <span className="kp-desk-bar__native">
            {birthData?.name || 'No native'}
            {birthData?.date ? ` · ${String(birthData.date).split('T')[0]}` : ''}
          </span>
        </div>
        <div className="kp-desk-bar__center">
          <div className="kp-desk-toggle" role="group" aria-label="Chart moment">
            <button type="button" className={viewMode === 'birth' ? 'is-active' : ''} onClick={() => setViewMode('birth')}>Birth</button>
            <button type="button" className={viewMode === 'asof' ? 'is-active' : ''} onClick={() => setViewMode('asof')}>As-of</button>
          </div>
          <div className="kp-desk-nav" aria-label="As-of date navigation">
            <button type="button" onClick={() => shiftAsOf(-1)} title="Previous day">‹D</button>
            <label className="kp-desk-field">
              <span>Date</span>
              <input
                type="date"
                value={asOfDate}
                onChange={(e) => {
                  setAsOfDate(e.target.value);
                  setViewMode('asof');
                }}
              />
            </label>
            <label className="kp-desk-field">
              <span>Time</span>
              <input
                type="time"
                value={asOfTime}
                onChange={(e) => {
                  setAsOfTime(e.target.value);
                  setViewMode('asof');
                }}
              />
            </label>
            <button type="button" onClick={() => shiftAsOf(1)} title="Next day">D›</button>
          </div>
          <button type="button" className="kp-desk-bar__now" onClick={setNow}>Now</button>
          <button
            type="button"
            className="kp-desk-bar__now kp-desk-bar__now--ghost"
            onClick={() => { loadNatal(); }}
            disabled={loading}
          >
            {loading ? '…' : 'Refresh'}
          </button>
        </div>
        <div className="kp-desk-bar__right">
          <button type="button" onClick={() => (user ? setShowBirthModal(true) : onLogin?.())}>Change native</button>
          {!user ? <button type="button" className="kp-desk-bar__primary" onClick={onLogin}>Sign in</button> : null}
        </div>
      </header>

      {!user ? (
        <div className="kp-desk-empty">
          <h2>Sign in for the KP desk</h2>
          <p>One-screen workspace for planets, cusps, significators and fructification.</p>
          <button type="button" className="kp-desk-bar__primary" onClick={onLogin}>Sign in</button>
        </div>
      ) : !hasChart ? (
        <div className="kp-desk-empty">
          <h2>Select a birth chart</h2>
          <p>Load a native to open the full KP desk.</p>
          <button type="button" className="kp-desk-bar__primary" onClick={() => setShowBirthModal(true)}>Select chart</button>
        </div>
      ) : (
        <>
          <div className="kp-desk-rp">
            <div className="kp-desk-rp__group">
              <span className="kp-desk-rp__label">Asc · {viewMode === 'asof' ? 'as-of' : 'birth'}</span>
              <b>SL {shortPlanet(rpAsc.sign_lord)}</b>
              <b>NL {shortPlanet(rpAsc.star_lord)}</b>
              <b>SB {shortPlanet(rpAsc.sub_lord)}</b>
            </div>
            <div className="kp-desk-rp__group">
              <span className="kp-desk-rp__label">Moon</span>
              <b>SL {shortPlanet(rpMoon.sign_lord)}</b>
              <b>NL {shortPlanet(rpMoon.star_lord)}</b>
              <b>SB {shortPlanet(rpMoon.sub_lord)}</b>
            </div>
            <div className="kp-desk-rp__group">
              <span className="kp-desk-rp__label">Day</span>
              <b>{shortPlanet(dayLord)}</b>
            </div>
            <div className="kp-desk-rp__group kp-desk-rp__group--dasha">
              <span className="kp-desk-rp__label">Dasha @ as-of</span>
              <b>
                {shortPlanet(dashaPlanet(dasha.mahadasha))}
                →{shortPlanet(dashaPlanet(dasha.antardasha))}
                →{shortPlanet(dashaPlanet(dasha.pratyantardasha))}
                →{shortPlanet(dashaPlanet(dasha.sookshma))}
                {dashaPlanet(dasha.prana) ? `→${shortPlanet(dashaPlanet(dasha.prana))}` : ''}
              </b>
            </div>
            {fructLoading ? <span className="kp-desk-rp__muted">Loading predictions…</span> : null}
            {error ? <span className="kp-desk-rp__error">{error}</span> : null}
          </div>

          <div className="kp-desk-grid">
            <section className="kp-desk-panel kp-desk-panel--chart">
              <header className="kp-desk-panel__head"><h2>KP Chart</h2><span>{viewLabel}</span></header>
              <div className="kp-desk-chart">
                {chartWidget.houses.length ? (
                  <KPChart chartData={chartWidget} birthData={birthData} deskMode />
                ) : (
                  <div className="kp-desk-muted">{loading || fructLoading ? 'Loading…' : 'No chart'}</div>
                )}
              </div>
            </section>

            <section className="kp-desk-panel kp-desk-panel--planets">
              <header className="kp-desk-panel__head">
                <h2>Planets</h2>
                <span>{viewLabel} · click → 4-step</span>
              </header>
              <div className="kp-desk-table-wrap">
                <table className="kp-desk-table">
                  <thead>
                    <tr>
                      <th>Pl</th><th>Deg</th><th>Star</th><th>Pd</th><th>SL</th><th>NL</th><th>SB</th><th>SS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {planets.map((row) => {
                      const nak = nakInfo(row.longitude);
                      return (
                        <tr
                          key={row.planet}
                          className={row.planet === selectedPlanet ? 'is-active' : ''}
                          onClick={() => { setSelectedPlanet(row.planet); setSigPanel('steps'); }}
                        >
                          <td className="kp-desk-table__planet">{shortPlanet(row.planet)}</td>
                          <td>{row.longitude.toFixed(1)}°</td>
                          <td className="kp-desk-table__star" title={nak.name}>{nak.name.slice(0, 6)}</td>
                          <td>{nak.pada}</td>
                          <td>{shortPlanet(row.sign_lord)}</td>
                          <td>{shortPlanet(row.star_lord)}</td>
                          <td>{shortPlanet(row.sub_lord)}</td>
                          <td>{shortPlanet(row.sub_sub_lord)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="kp-desk-panel kp-desk-panel--cusps">
              <header className="kp-desk-panel__head"><h2>Cusps</h2><span>{viewLabel}</span></header>
              <div className="kp-desk-table-wrap">
                <table className="kp-desk-table">
                  <thead>
                    <tr>
                      <th>H</th><th>Deg</th><th>Star</th><th>Pd</th><th>SL</th><th>NL</th><th>SB</th><th>SS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cusps.map((row) => {
                      const nak = nakInfo(row.longitude);
                      return (
                        <tr key={row.cusp}>
                          <td className="kp-desk-table__planet">{row.cusp}</td>
                          <td>{row.longitude.toFixed(1)}°</td>
                          <td className="kp-desk-table__star" title={nak.name}>{nak.name.slice(0, 6)}</td>
                          <td>{nak.pada}</td>
                          <td>{shortPlanet(row.sign_lord)}</td>
                          <td>{shortPlanet(row.star_lord)}</td>
                          <td>{shortPlanet(row.sub_lord)}</td>
                          <td>{shortPlanet(row.sub_sub_lord)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="kp-desk-panel kp-desk-panel--sigs">
              <header className="kp-desk-panel__head">
                <h2>Significators</h2>
                <span>{viewLabel}</span>
                <div className="kp-desk-toggle kp-desk-toggle--sm">
                  <button type="button" className={sigPanel === 'house' ? 'is-active' : ''} onClick={() => setSigPanel('house')}>H-Sig</button>
                  <button type="button" className={sigPanel === 'planet' ? 'is-active' : ''} onClick={() => setSigPanel('planet')}>P-Sig</button>
                  <button type="button" className={sigPanel === 'steps' ? 'is-active' : ''} onClick={() => setSigPanel('steps')}>4-Step</button>
                </div>
              </header>
              <div className="kp-desk-sigs">
                {sigPanel === 'house' ? (
                  <div className="kp-desk-hsig">
                    {Array.from({ length: 12 }, (_, i) => String(i + 1)).map((house) => {
                      const sigs = significators[house] || significators[Number(house)] || [];
                      return (
                        <div key={house} className="kp-desk-hsig__row">
                          <strong>H{house}</strong>
                          <div className="kp-desk-chips">
                            {asList(sigs).map((sig) => (
                              <span key={`${house}-${typeof sig === 'string' ? sig : sig?.planet}`}>
                                {typeof sig === 'string' ? shortPlanet(sig) : shortPlanet(sig?.planet)}
                              </span>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : null}

                {sigPanel === 'planet' ? (
                  <div className="kp-desk-psig">
                    {Object.entries(planetSignificators).map(([planet, houses]) => (
                      <div key={planet} className="kp-desk-hsig__row">
                        <strong>{shortPlanet(planet)}</strong>
                        <div className="kp-desk-chips">
                          {asList(houses).map((h) => <span key={`${planet}-${h}`}>H{h}</span>)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : null}

                {sigPanel === 'steps' ? (
                  <div className="kp-desk-steps">
                    <div className="kp-desk-steps__pick">
                      {PLANET_ORDER.map((p) => (
                        <button
                          key={p}
                          type="button"
                          className={selectedPlanet === p ? 'is-active' : ''}
                          onClick={() => setSelectedPlanet(p)}
                        >
                          {shortPlanet(p)}
                        </button>
                      ))}
                    </div>
                    {selectedSteps ? (
                      <div className="kp-desk-steps__list">
                        {[
                          ['1 Pl', selectedSteps.planet],
                          ['2 NL', selectedSteps.star_lord],
                          ['3 SB', selectedSteps.sub_lord],
                          ['4 SS', selectedSteps.sub_sub_lord],
                        ].map(([label, step]) => (
                          <div key={label} className="kp-desk-steps__item">
                            <span>{label}</span>
                            <strong>{shortPlanet(step?.name)}</strong>
                            <div className="kp-desk-chips">
                              {asList(step?.houses).map((h) => <span key={h}>{h}</span>)}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="kp-desk-muted">Select a planet</div>
                    )}
                  </div>
                ) : null}
              </div>
            </section>

            <section className="kp-desk-panel kp-desk-panel--fruct">
              <header className="kp-desk-panel__head">
                <h2>Predictions</h2>
                <div className="kp-desk-toggle kp-desk-toggle--sm" role="tablist" aria-label="Prediction scope">
                  <button
                    type="button"
                    className={fructScope === 'today' ? 'is-active' : ''}
                    onClick={() => setFructScope('today')}
                  >
                    Today
                    <em>{asList(todayBlock?.houses_giving_results).length}</em>
                  </button>
                  <button
                    type="button"
                    className={fructScope === 'hour' ? 'is-active' : ''}
                    onClick={() => setFructScope('hour')}
                  >
                    This hour
                    <em>{asList(hourBlock?.houses_giving_results).length}</em>
                  </button>
                </div>
                <span>{asOfDate} {asOfTime}</span>
              </header>
              <div className="kp-desk-fruct">
                {fructLoading && !fruct ? (
                  <div className="kp-desk-muted kp-desk-fruct__status">Loading day & hour predictions…</div>
                ) : !fruct ? (
                  <div className="kp-desk-muted kp-desk-fruct__status">
                    Predictions unavailable. Check as-of date/time or refresh.
                  </div>
                ) : (
                  <>
                    <div className="kp-desk-fruct__main">
                      <p className="kp-desk-fruct__blurb">
                        {fructScope === 'hour'
                          ? 'Sharper timing for this hour — AD/PD ∩ Sookshma ∩ Prana ∩ hour ruling planets.'
                          : 'Houses that can give results today — Day Lord + Moon star lord, including hour confirms.'}
                      </p>

                      {Object.keys(asOfRps || {}).length ? (
                        <div className="kp-desk-fruct__rps" aria-label="Ruling planets used">
                          {Object.entries(asOfRps)
                            .filter(([, v]) => v && typeof v === 'string')
                            .map(([role, planet]) => (
                              <span key={role}>
                                <em>{RP_ROLE_SHORT[role] || role}</em>
                                {shortPlanet(planet)}
                              </span>
                            ))}
                        </div>
                      ) : null}

                      {gate.prana_fallback ? (
                        <div className="kp-desk-fruct__notice">
                          Prana did not confirm this hour — showing Sookshma ∩ ruling planets instead.
                        </div>
                      ) : null}

                      <button
                        type="button"
                        className="kp-desk-fruct__calc-toggle"
                        onClick={() => setCalcOpen((v) => !v)}
                      >
                        {calcOpen ? 'Hide calculation' : 'Show calculation'}
                        <span>{calc.formula || (fructScope === 'hour' ? 'AD/PD ∩ SK ∩ PR ∩ RPs' : 'AD/PD ∩ SK ∩ Day RPs ∪ hour')}</span>
                      </button>
                      {calcOpen && asList(calc.steps).length ? (
                        <div className="kp-desk-fruct__calc">
                          {asList(calc.steps).map((step) => (
                            <div key={`${fructScope}-calc-${step.step}`}>
                              <strong>Step {step.step} · {step.title}</strong>
                              <p>{step.detail}</p>
                            </div>
                          ))}
                        </div>
                      ) : null}

                      <h3>Houses giving results</h3>
                      {primaryHouses.length ? (
                        <div className="kp-desk-fruct__houses">
                          {primaryHouses.map((row) => {
                            const key = `${fructScope}-p-${row.house}`;
                            const open = expandedHouse === key;
                            return (
                              <div key={key} className={`kp-desk-house-card tone-${row.tone || 'neutral'}`}>
                                <button
                                  type="button"
                                  className="kp-desk-house-card__head"
                                  onClick={() => setExpandedHouse(open ? null : key)}
                                >
                                  <strong>H{row.house}</strong>
                                  <div>
                                    <b>{row.label || `House ${row.house}`}</b>
                                    <span>
                                      {(row.activating_rps || []).join(' · ') || '—'}
                                      {row.included_from_hour ? ' · hour' : ''}
                                    </span>
                                  </div>
                                  <em>{toneLabel(row.tone)}</em>
                                  <u>{open ? 'Hide' : 'Why'}</u>
                                </button>
                                {open && row.how?.summary ? (
                                  <div className="kp-desk-house-card__why">
                                    <p>{row.how.summary}</p>
                                    {asList(row.how.steps).map((step) => (
                                      <div key={`${key}-${step.step}`}>
                                        <strong>
                                          {step.title}
                                          {typeof step.passed === 'boolean' ? (step.passed ? ' · Pass' : ' · Fail') : ''}
                                        </strong>
                                        <p>{step.detail}</p>
                                      </div>
                                    ))}
                                  </div>
                                ) : null}
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <div className="kp-desk-fruct__empty">
                          {fructLoading
                            ? 'Refreshing…'
                            : `No primary fructifying houses for ${fructScope === 'hour' ? 'this hour' : 'today'}.`}
                        </div>
                      )}

                      {secondaryHouses.length ? (
                        <>
                          <h3>Background</h3>
                          <div className="kp-desk-chips">
                            {secondaryHouses.map((row) => (
                              <span key={`sec-${row.house || row}`} className="tone-neutral">
                                H{row.house || row}
                              </span>
                            ))}
                          </div>
                        </>
                      ) : null}
                    </div>

                    <div className="kp-desk-fruct__themes-col">
                      <h3>Life themes</h3>
                      {themeGroups.length ? (
                        themeGroups.map((group) => (
                          <div key={group.subject} className="kp-desk-theme-group">
                            <h4>{subjectLabel(group.subject)}</h4>
                            {group.items.map((item) => (
                              <article
                                key={item.manifestation_id || item.label}
                                className={`kp-desk-theme tone-${item.outcome_tone || 'neutral'}`}
                              >
                                <header>
                                  <strong>{item.label || 'Theme'}</strong>
                                  <em>{toneLabel(item.outcome_tone)}</em>
                                </header>
                                {item.summary ? <p>{item.summary}</p> : null}
                                {asList(item.possibilities).length ? (
                                  <ul>
                                    {asList(item.possibilities).slice(0, 5).map((p) => (
                                      <li key={p}>{p}</li>
                                    ))}
                                  </ul>
                                ) : null}
                                {asList(item.house_roles).length ? (
                                  <div className="kp-desk-chips">
                                    {asList(item.house_roles).map((role) => (
                                      <span key={`${item.manifestation_id}-${role.native_house}-${role.relative_house}`}>
                                        {group.subject === 'self'
                                          ? `H${role.native_house}`
                                          : `H${role.relative_house}←${role.native_house}`}
                                      </span>
                                    ))}
                                  </div>
                                ) : null}
                              </article>
                            ))}
                          </div>
                        ))
                      ) : (
                        <div className="kp-desk-fruct__empty">
                          {fructLoading ? 'Synthesizing themes…' : 'No combined life themes for this scope.'}
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            </section>
          </div>
        </>
      )}

      <BirthFormModal
        isOpen={showBirthModal}
        onClose={() => setShowBirthModal(false)}
        onSubmit={(data) => {
          setBirthData(data);
          setShowBirthModal(false);
        }}
        title="Select chart for KP Desk"
        description="Choose the native for the KP workspace."
        prefilledData={birthData}
      />
    </div>
  );
}

export default KPDeskPage;
