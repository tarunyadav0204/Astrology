import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BirthFormModal from '../BirthForm/BirthFormModal';
import SEOHead from '../SEO/SEOHead';
import ChartWidget from '../Charts/ChartWidget';
import TransitControls from '../TransitControls/TransitControls';
import { useAstrology } from '../../context/AstrologyContext';
import { generatePageSEO } from '../../config/seo.config';
import { apiService } from '../../services/apiService';
import './NadiDeskPage.css';

const ABBR = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
};

const PLANET_ORDER = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];

const LINK_LABELS = {
  trine: 'Trine',
  next: '2nd',
  prev: '12th',
  opposite: '7th',
};

const STATE_META = {
  strong: { short: 'Strong', hint: 'Multiple activation hits' },
  active: { short: 'Active', hint: 'Age or transit wake-up' },
  promise: { short: 'Promise', hint: 'Natal yoga only' },
};

const TOPIC_ORDER = ['career', 'marriage', 'wealth', 'self', 'all'];
const LINK_FILTER_ORDER = ['all', 'trine', 'next', 'prev', 'opposite'];

function abbr(name) {
  return ABBR[name] || String(name || '').slice(0, 2);
}

function formatAsOfIso(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
    return new Date().toISOString().slice(0, 10);
  }
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function extractTransitPlanets(transitPayload) {
  const planets = transitPayload?.planets
    || transitPayload?.transit_chart?.planets
    || transitPayload?.chart_data?.planets
    || transitPayload?.data?.planets
    || null;
  if (!planets || typeof planets !== 'object') return null;
  const out = {};
  Object.entries(planets).forEach(([name, data]) => {
    if (!data || typeof data !== 'object') return;
    out[name] = {
      sign: data.sign,
      house: data.house,
      longitude: data.longitude,
      degree: data.degree,
      retrograde: data.retrograde,
    };
  });
  return Object.keys(out).length ? out : null;
}

function lagnaSignIndex(chart) {
  const h0 = chart?.houses?.[0];
  if (h0?.sign != null) return Number(h0.sign);
  const asc = chart?.ascendant;
  if (typeof asc === 'number' && Number.isFinite(asc)) {
    return Math.floor((((asc % 360) + 360) % 360) / 30);
  }
  return 0;
}

function houseOfPlanet(chart, planetName) {
  const data = chart?.planets?.[planetName];
  if (!data) return null;
  if (data.house != null) return Number(data.house);
  if (data.sign == null) return null;
  return ((Number(data.sign) - lagnaSignIndex(chart) + 12) % 12) + 1;
}

function houseOfTransitPlanet(chart, transitPlanets, planetName) {
  const data = transitPlanets?.[planetName];
  if (!data || data.sign == null) return null;
  if (data.house != null) return Number(data.house);
  return ((Number(data.sign) - lagnaSignIndex(chart) + 12) % 12) + 1;
}

function formatLinkGroup(planets) {
  if (!planets?.length) return '—';
  return planets.map(abbr).join(' · ');
}

/**
 * Bhrigu Nandi Nadi desk — graha links, purushartha trikonas, age/transit activation.
 */
export default function NadiDeskPage({ user, onLogin }) {
  const navigate = useNavigate();
  const { birthData, chartData, setBirthData } = useAstrology();
  const [showBirthModal, setShowBirthModal] = useState(false);
  const [birthModalTab, setBirthModalTab] = useState('saved');
  const [asOfDate, setAsOfDate] = useState(new Date());
  const [desk, setDesk] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [topic, setTopic] = useState('career');
  const [linkFilter, setLinkFilter] = useState('all');
  const [selectedPlanet, setSelectedPlanet] = useState('Saturn');
  const [selectedActivationId, setSelectedActivationId] = useState(null);
  const [manualHighlight, setManualHighlight] = useState(null);
  const [transitPlanets, setTransitPlanets] = useState(null);
  const [mobileTab, setMobileTab] = useState('chart');
  const [mobileChart, setMobileChart] = useState('d1');
  const [mobileMore, setMobileMore] = useState('purushartha');
  const [nadiChartStyle, setNadiChartStyle] = useState('north');
  const seoData = generatePageSEO('chartsDashasWorkspace', { path: '/charts-dashas/nadi' });
  const hasChart = Boolean(birthData && chartData);

  useEffect(() => {
    let cancelled = false;
    if (!user || !birthData || !chartData) {
      setDesk(null);
      setTransitPlanets(null);
      setError(null);
      setLoading(false);
      return () => { cancelled = true; };
    }
    const asOf = formatAsOfIso(asOfDate);
    setLoading(true);
    setError(null);
    (async () => {
      try {
        let nextTransit = null;
        try {
          const transitRes = await apiService.calculateTransits({
            birth_data: birthData,
            transit_date: asOf,
          });
          nextTransit = extractTransitPlanets(transitRes);
        } catch (_) {
          nextTransit = null;
        }
        const data = await apiService.getNadiDesk({
          birthData,
          chartData,
          asOf,
          transitPlanets: nextTransit,
        });
        if (cancelled) return;
        setTransitPlanets(nextTransit);
        if (data?.success === false) {
          setDesk(null);
          setError(data.error || 'Could not load Nadi desk');
        } else {
          setDesk(data);
          setError(null);
        }
        setLoading(false);
      } catch (err) {
        if (cancelled) return;
        setDesk(null);
        setTransitPlanets(null);
        setLoading(false);
        const detail = err?.response?.data?.detail || err?.response?.data?.error;
        setError(typeof detail === 'string' ? detail : err?.message || 'Could not load Nadi desk');
      }
    })();
    return () => { cancelled = true; };
  }, [user, birthData, chartData, asOfDate]);

  const presets = desk?.topic_presets || {};
  const visibleKarakaReadout = useMemo(() => {
    const rows = desk?.karaka_readout || [];
    if (topic === 'all') return rows;
    const karakas = new Set(presets[topic]?.karakas || []);
    return karakas.size ? rows.filter((row) => karakas.has(row.planet)) : rows;
  }, [desk, topic, presets]);

  const activations = useMemo(() => {
    let rows = desk?.activations || [];
    if (linkFilter !== 'all') {
      rows = rows.filter((row) => row.link_type === linkFilter);
    }
    if (topic === 'all') return rows;
    const preset = presets[topic];
    if (!preset) return rows;
    const karakas = new Set(preset.karakas || []);
    return rows.filter((row) => (row.planets || []).some((p) => karakas.has(p)));
  }, [desk, topic, presets, linkFilter]);

  useEffect(() => {
    if (!activations.length) {
      setSelectedActivationId(null);
      return;
    }
    if (!selectedActivationId || !activations.some((row) => row.id === selectedActivationId)) {
      setSelectedActivationId(activations[0].id);
      setManualHighlight(null);
    }
  }, [activations, selectedActivationId]);

  const selectedActivation = activations.find((row) => row.id === selectedActivationId) || null;
  const linkRow = desk?.links?.[selectedPlanet] || null;

  const highlightedPlanets = useMemo(() => {
    if (manualHighlight?.length) return manualHighlight;
    if (selectedActivation?.planets?.length) return selectedActivation.planets;
    return selectedPlanet ? [selectedPlanet] : [];
  }, [manualHighlight, selectedActivation, selectedPlanet]);

  const natalHighlightHouses = useMemo(() => {
    if (!chartData || !highlightedPlanets.length) return [];
    return [...new Set(
      highlightedPlanets
        .map((name) => houseOfPlanet(chartData, name))
        .filter((h) => h != null)
    )];
  }, [chartData, highlightedPlanets]);

  const transitHighlightHouses = useMemo(() => {
    if (!chartData || !highlightedPlanets.length) return [];
    return [...new Set(
      highlightedPlanets
        .map((name) => houseOfTransitPlanet(chartData, transitPlanets, name))
        .filter((h) => h != null)
    )];
  }, [chartData, transitPlanets, highlightedPlanets]);

  const focusYoga = (row) => {
    setSelectedActivationId(row.id);
    setManualHighlight(null);
    if (row.planets?.[0]) setSelectedPlanet(row.planets[0]);
  };

  const focusPlanet = (planet) => {
    setSelectedPlanet(planet);
    setManualHighlight([planet]);
  };

  const focusKaraka = (row) => {
    const linked = Array.isArray(row.all_links) ? row.all_links : [];
    setSelectedPlanet(row.planet);
    setManualHighlight([row.planet, ...linked.filter((p) => p !== row.planet)]);
  };

  const openBirthModal = (tab) => {
    setBirthModalTab(tab);
    setShowBirthModal(true);
  };

  return (
    <div className="nadi-desk">
      <SEOHead {...seoData} />
      <header className="nadi-desk__bar">
        <div className="nadi-desk__bar-left">
          <button type="button" className="nadi-desk__back" onClick={() => navigate('/charts-dashas')}>
            ← Charts
          </button>
          <strong className="nadi-desk__brand">Nadi Desk</strong>
          <span className="nadi-desk__sub">Bhrigu Nandi Nadi</span>
          {hasChart ? (
            <span className="nadi-desk__native">{birthData?.name || 'Native'}</span>
          ) : null}
        </div>
        <div className="nadi-desk__bar-center">
          <button type="button" className="nadi-desk__chip" onClick={() => navigate('/charts-dashas')}>
            Parashari
          </button>
          <button type="button" className="nadi-desk__chip" onClick={() => navigate('/charts-dashas/kp')}>
            KP
          </button>
          <button type="button" className="nadi-desk__chip is-active">
            Nadi
          </button>
        </div>
        <div className="nadi-desk__bar-right">
          <button
            type="button"
            onClick={() => (user ? openBirthModal(hasChart ? 'saved' : 'new') : onLogin?.())}
          >
            {user ? (hasChart ? 'Change native' : 'Select chart') : 'Sign in'}
          </button>
        </div>
      </header>

      {user && hasChart ? (
        <nav className="nadi-desk__mobile-hub" role="tablist" aria-label="Nadi desk sections">
          {[
            { id: 'chart', label: 'Chart', icon: '◇' },
            { id: 'links', label: 'Links', icon: '⌁' },
            { id: 'act', label: 'Activations', icon: '✦' },
            { id: 'more', label: 'More', icon: '☷' },
          ].map(({ id, label, icon }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={mobileTab === id}
              className={mobileTab === id ? 'is-active' : ''}
              onClick={() => setMobileTab(id)}
            >
              <span className="nadi-desk__mobile-hub-icon" aria-hidden>{icon}</span>
              <span className="nadi-desk__mobile-hub-label">{label}</span>
              {id === 'act' && activations.length ? <em>{activations.length}</em> : null}
            </button>
          ))}
        </nav>
      ) : null}

      {!user ? (
        <div className="nadi-desk__empty">
          <h2>Sign in for the Nadi desk</h2>
          <button type="button" className="nadi-desk__primary" onClick={onLogin}>Sign in</button>
        </div>
      ) : !hasChart ? (
        <div className="nadi-desk__empty">
          <h2>Select a birth chart</h2>
          <button type="button" className="nadi-desk__primary" onClick={() => openBirthModal('new')}>
            Open chart
          </button>
        </div>
      ) : (
        <div className="nadi-desk__body">
          {mobileTab === 'chart' ? (
            <div className="nadi-desk__mobile-pills" role="tablist" aria-label="Chart type">
              <button type="button" className={mobileChart === 'd1' ? 'is-active' : ''} onClick={() => setMobileChart('d1')}>D1</button>
              <button type="button" className={mobileChart === 'transit' ? 'is-active' : ''} onClick={() => setMobileChart('transit')}>Transit</button>
            </div>
          ) : null}
          {mobileTab === 'more' ? (
            <div className="nadi-desk__mobile-pills nadi-desk__mobile-pills--more" role="tablist" aria-label="More sections">
              <button type="button" className={mobileMore === 'purushartha' ? 'is-active' : ''} onClick={() => setMobileMore('purushartha')}>Purushartha</button>
              <button type="button" className={mobileMore === 'ages' ? 'is-active' : ''} onClick={() => setMobileMore('ages')}>Age Progression</button>
            </div>
          ) : null}
          <div className={`nadi-desk__tools nadi-desk__tools--${mobileTab}`}>
            <div className={`nadi-desk__clock${mobileTab === 'act' || (mobileTab === 'chart' && mobileChart === 'transit') ? '' : ' is-mobile-hidden'}`}>
              <span>As-of</span>
              <TransitControls
                date={asOfDate}
                onChange={setAsOfDate}
                onResetToToday={() => setAsOfDate(new Date())}
                variant="light"
              />
            </div>
            <div className="nadi-desk__moon" title="Chandrakala-style Moon anchor">
              <em>Moon</em>
              <strong>{desk?.moon?.nakshatra || '—'}</strong>
              {desk?.moon?.pada != null ? <span>p{desk.moon.pada}</span> : null}
              <span>{desk?.moon?.sign_name || '—'}</span>
              {desk?.moon?.house != null ? <span>H{desk.moon.house}</span> : null}
            </div>
            {desk?.age != null ? <span className="nadi-desk__age">Age {desk.age}</span> : null}
            <div className="nadi-desk__topics" role="tablist" aria-label="Topic lens">
              {TOPIC_ORDER.map((id) => (
                <button
                  key={id}
                  type="button"
                  role="tab"
                  aria-selected={topic === id}
                  className={topic === id ? 'is-active' : ''}
                  onClick={() => setTopic(id)}
                >
                  {id === 'all' ? 'All topics' : (presets[id]?.label || id)}
                </button>
              ))}
            </div>
            <div className="nadi-desk__topics nadi-desk__topics--links" role="tablist" aria-label="Link type">
              {LINK_FILTER_ORDER.map((id) => (
                <button
                  key={id}
                  type="button"
                  role="tab"
                  aria-selected={linkFilter === id}
                  className={linkFilter === id ? 'is-active' : ''}
                  onClick={() => setLinkFilter(id)}
                >
                  {id === 'all' ? 'All links' : (LINK_LABELS[id] || id)}
                </button>
              ))}
            </div>
          </div>

          {visibleKarakaReadout.length ? (
            <div className={`nadi-desk__karaka-row${mobileTab === 'links' ? ' is-mobile-active' : ''}`} aria-label="Jeeva Karma Kalatra">
              {visibleKarakaReadout.map((row) => {
                const isActive = Boolean(
                  manualHighlight?.length
                  && manualHighlight[0] === row.planet
                );
                return (
                  <button
                    key={row.role}
                    type="button"
                    className={`nadi-desk__karaka-card${isActive ? ' is-active' : ''}`}
                    onClick={() => focusKaraka(row)}
                    title={`${row.label} karaka — click to highlight links`}
                  >
                    <header>
                      <strong>{row.label}</strong>
                      <span>{abbr(row.planet)}</span>
                    </header>
                    <p>
                      {row.sign_name || '—'}
                      {row.house != null ? ` · H${row.house}` : ''}
                      {row.nakshatra ? ` · ${row.nakshatra}` : ''}
                      {row.is_retro ? ' · R' : ''}
                      {row.is_exchange ? ' · exch' : ''}
                    </p>
                    <dl>
                      <div>
                        <dt>Trine</dt>
                        <dd>{formatLinkGroup(row.links?.trine)}</dd>
                      </div>
                      <div>
                        <dt>2nd</dt>
                        <dd>{formatLinkGroup(row.links?.next)}</dd>
                      </div>
                      <div>
                        <dt>12th</dt>
                        <dd>{formatLinkGroup(row.links?.prev)}</dd>
                      </div>
                      <div>
                        <dt>7th</dt>
                        <dd>{formatLinkGroup(row.links?.opposite)}</dd>
                      </div>
                    </dl>
                  </button>
                );
              })}
            </div>
          ) : null}

          {error ? (
            <div className="nadi-desk__banner nadi-desk__banner--err">{error}</div>
          ) : null}
          {loading && !desk ? (
            <div className="nadi-desk__banner">Reading BNN linkage & activation…</div>
          ) : null}

          <div className="nadi-desk__grid">
            <section className={`nadi-desk__panel nadi-desk__panel--d1${mobileTab === 'chart' && mobileChart === 'd1' ? ' is-mobile-active' : ''}`}>
              <header>
                <strong>D1</strong>
                <em>Natal</em>
                <button
                  type="button"
                  className="nadi-desk__chart-style"
                  onClick={() => setNadiChartStyle((style) => (style === 'north' ? 'south' : 'north'))}
                  aria-label={`Switch to ${nadiChartStyle === 'north' ? 'South' : 'North'} Indian chart`}
                  title="North / South Indian"
                >
                  {nadiChartStyle === 'north' ? 'N' : 'S'}
                </button>
              </header>
              <div className="nadi-desk__chart">
                <ChartWidget
                  title="D1"
                  chartType="lagna"
                  chartData={chartData}
                  birthData={birthData}
                  chartStyle={nadiChartStyle}
                  onChartStyleChange={setNadiChartStyle}
                  showFooterHint={false}
                  embedInDashboard
                  deskMode
                  highlightedPlanets={highlightedPlanets}
                  highlightedHouseNumbers={natalHighlightHouses}
                />
              </div>
            </section>

            <section className={`nadi-desk__panel nadi-desk__panel--tr${mobileTab === 'chart' && mobileChart === 'transit' ? ' is-mobile-active' : ''}`}>
              <header>
                <strong>Transit</strong>
                <em>{formatAsOfIso(asOfDate)}</em>
                <button
                  type="button"
                  className="nadi-desk__chart-style"
                  onClick={() => setNadiChartStyle((style) => (style === 'north' ? 'south' : 'north'))}
                  aria-label={`Switch to ${nadiChartStyle === 'north' ? 'South' : 'North'} Indian chart`}
                  title="North / South Indian"
                >
                  {nadiChartStyle === 'north' ? 'N' : 'S'}
                </button>
              </header>
              <div className="nadi-desk__chart">
                <ChartWidget
                  title="Transit"
                  chartType="transit"
                  chartData={chartData}
                  birthData={birthData}
                  transitDate={asOfDate}
                  chartStyle={nadiChartStyle}
                  onChartStyleChange={setNadiChartStyle}
                  showFooterHint={false}
                  embedInDashboard
                  deskMode
                  highlightedPlanets={highlightedPlanets}
                  highlightedHouseNumbers={transitHighlightHouses}
                />
              </div>
            </section>

            <aside className={`nadi-desk__panel nadi-desk__panel--ledger${mobileTab === 'act' ? ' is-mobile-active' : ''}`}>
              <header>
                <strong>Activations</strong>
                <em>Trine · 2nd · 12th · 7th</em>
              </header>
              <div className="nadi-desk__state-key">
                {Object.entries(STATE_META).map(([key, meta]) => (
                  <span key={key} title={meta.hint}>
                    <i className={`nadi-desk__swatch nadi-desk__swatch--${key}`} />
                    <b>{meta.short}</b>
                    <em>{meta.hint}</em>
                  </span>
                ))}
              </div>
              <ul className="nadi-desk__act-list">
                {activations.map((row) => (
                  <li key={row.id}>
                    <button
                      type="button"
                      className={`nadi-desk__act${selectedActivationId === row.id && !manualHighlight ? ' is-selected' : ''} nadi-desk__act--${row.state}`}
                      onClick={() => focusYoga(row)}
                    >
                      <strong>{(row.planets || []).map(abbr).join('–')}</strong>
                      <i>{STATE_META[row.state]?.short || row.state}</i>
                      <span>
                        <b className={`nadi-desk__link-tag nadi-desk__link-tag--${row.link_type}`}>
                          {row.link_label || LINK_LABELS[row.link_type] || row.link_type}
                        </b>
                        {(row.themes || []).slice(0, 1).join('')}
                      </span>
                    </button>
                  </li>
                ))}
                {!activations.length && !loading ? (
                  <li className="nadi-desk__empty-row">No yogas for this lens</li>
                ) : null}
              </ul>
            </aside>

            <section className={`nadi-desk__panel nadi-desk__panel--links${mobileTab === 'links' ? ' is-mobile-active' : ''}`}>
              <header>
                <strong>Link graph</strong>
                <em>BNN connections</em>
              </header>
              <div className="nadi-desk__planet-tabs">
                {PLANET_ORDER.map((planet) => (
                  <button
                    key={planet}
                    type="button"
                    className={selectedPlanet === planet ? 'is-active' : ''}
                    onClick={() => focusPlanet(planet)}
                  >
                    <span className="nadi-desk__planet-short">{abbr(planet)}</span>
                    <span className="nadi-desk__planet-full">{planet}</span>
                  </button>
                ))}
              </div>
              {linkRow ? (
                <div className="nadi-desk__link-card">
                  <div className="nadi-desk__link-head">
                    <strong>{selectedPlanet}</strong>
                    <span>
                      Sign {(linkRow.sign_info?.sign_id ?? 0) + 1}
                      {linkRow.sign_info?.is_retro ? ' · R' : ''}
                      {linkRow.sign_info?.is_exchange ? ' · Exchange' : ''}
                    </span>
                  </div>
                  {Object.entries(LINK_LABELS)
                    .filter(([key]) => linkFilter === 'all' || linkFilter === key)
                    .map(([key, label]) => {
                    const peers = linkRow.connections?.[key] || [];
                    return (
                      <div key={key} className="nadi-desk__link-row">
                        <em>{label}</em>
                        <strong>
                          {peers.length ? peers.map(abbr).join(' · ') : '—'}
                        </strong>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="nadi-desk__empty-row">No link data</p>
              )}
            </section>

            <section className={`nadi-desk__panel nadi-desk__panel--tri${mobileTab === 'more' && mobileMore === 'purushartha' ? ' is-mobile-active' : ''}`}>
              <header>
                <strong>Purushartha</strong>
                <em>Trikonas</em>
              </header>
              <div className="nadi-desk__trikonas">
                {(desk?.trikonas || []).map((tri) => (
                  <article key={tri.key} className={`nadi-desk__tri nadi-desk__tri--${tri.strength}`}>
                    <header>
                      <strong>{tri.label}</strong>
                      <span>H{tri.houses.join('·')}</span>
                    </header>
                    <p>
                      {(tri.occupants || []).length
                        ? tri.occupants.map((o) => `${abbr(o.planet)}@${o.house}`).join(' · ')
                        : 'Empty'}
                    </p>
                  </article>
                ))}
              </div>
            </section>

            <section className={`nadi-desk__panel nadi-desk__panel--ages${mobileTab === 'more' && mobileMore === 'ages' ? ' is-mobile-active' : ''}`}>
              <header>
                <strong>Age progression</strong>
                <em>Planet ages + nakṣatra milestones</em>
              </header>
              <div className="nadi-desk__ages">
                <div className="nadi-desk__age-table">
                  <em>Planet ages</em>
                  <div className="nadi-desk__age-table-head" aria-hidden="true">
                    <span>Planet</span><span>Age</span><span>Status</span>
                  </div>
                  <ul>
                    {(desk?.planet_ages || []).map((row) => (
                      <li key={row.planet} className={`is-${row.status}`}>
                        <strong>{abbr(row.planet)}</strong>
                        <span>{row.age}</span>
                        <i>{row.status}</i>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="nadi-desk__age-table nadi-desk__age-table--milestones">
                  <em>Nakṣatra milestones</em>
                  <div className="nadi-desk__age-table-head" aria-hidden="true">
                    <span>Age</span><span>Nakṣatra</span><span>Planets</span>
                  </div>
                  <ul>
                    {(desk?.nakshatra_milestones || []).map((row) => (
                      <li key={row.age} className={`is-${row.status}`}>
                        <strong>{row.age}</strong>
                        <span>{(row.nakshatras || []).join(' · ')}</span>
                        <i>
                          {(row.planets || []).length
                            ? row.planets.map((p) => abbr(p.planet)).join(' · ')
                            : '—'}
                        </i>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>

            <aside className={`nadi-desk__panel nadi-desk__panel--detail${mobileTab === 'act' ? ' is-mobile-active' : ''}`}>
              <header>
                <strong>Detail</strong>
                <em>Selected yoga</em>
              </header>
              {selectedActivation ? (
                <div className="nadi-desk__detail">
                  <div className="nadi-desk__detail-head">
                    <strong>{selectedActivation.planets.map(abbr).join(' → ')}</strong>
                    <b className={`nadi-desk__link-tag nadi-desk__link-tag--${selectedActivation.link_type}`}>
                      {selectedActivation.link_label || LINK_LABELS[selectedActivation.link_type]}
                    </b>
                    <i className={`nadi-desk__state nadi-desk__state--${selectedActivation.state}`}>
                      {STATE_META[selectedActivation.state]?.short}
                    </i>
                  </div>
                  <p className="nadi-desk__themes">
                    {(selectedActivation.themes || []).join(' · ')}
                  </p>
                  <em>Wake-up reasons</em>
                  {(selectedActivation.reasons || []).length ? (
                    <ul>
                      {selectedActivation.reasons.map((reason) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="nadi-desk__empty-row">Natal promise only — no age/transit hit yet</p>
                  )}
                  <em>Transit hits on members</em>
                  <ul>
                    {(desk?.transit_hits || [])
                      .filter((hit) => selectedActivation.planets.includes(hit.natal_planet))
                      .map((hit) => (
                        <li key={`${hit.transit_planet}-${hit.natal_planet}-${hit.relation}`}>
                          {abbr(hit.transit_planet)} {hit.relation} {abbr(hit.natal_planet)}
                        </li>
                      ))}
                  </ul>
                  {!(desk?.transit_hits || []).some(
                    (hit) => selectedActivation.planets.includes(hit.natal_planet)
                  ) ? (
                    <p className="nadi-desk__empty-row">No slow-planet transit hit on this yoga</p>
                  ) : null}
                </div>
              ) : (
                <p className="nadi-desk__empty-row">Select a yoga</p>
              )}
            </aside>
          </div>
        </div>
      )}

      <BirthFormModal
        isOpen={showBirthModal}
        onClose={() => setShowBirthModal(false)}
        onSubmit={(data) => {
          if (data) setBirthData?.(data);
          setShowBirthModal(false);
        }}
        defaultActiveTab={birthModalTab}
        title="Nadi Desk — Birth details"
        description="Create a new chart or choose a saved one for the BNN desk."
        prefilledData={birthData}
      />
    </div>
  );
}
