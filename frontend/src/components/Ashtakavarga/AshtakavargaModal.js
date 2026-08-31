import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import './AshtakavargaModal.css';
import { API_BASE_URL } from '../../config';
import { useCredits } from '../../context/CreditContext';
import { showToast } from '../../utils/toast';

const LIFE_PREDICTION_DOMAIN_LABELS = {
  vitality_and_personality: 'Vitality & personality',
  wealth_family_speech: 'Wealth, family & speech',
  courage_siblings_skills: 'Courage, siblings & skills',
  home_comfort_mother: 'Home, comfort & mother',
  children_creativity_speculation: 'Children, creativity & speculation',
  health_service_obstacles: 'Health, service & obstacles',
  partnerships_marriage: 'Partnerships & marriage',
  longevity_shared_resources: 'Longevity & shared resources',
  fortune_dharma_father: 'Fortune, dharma & father-guru line',
  career_reputation: 'Career & reputation',
  gains_network_aspirations: 'Gains, network & aspirations',
  expenses_moksha_rest: 'Expenses, rest & liberation themes',
};

function formatLifePredictionsError(data, status) {
  if (status === 503) {
    return 'Predictions are temporarily unavailable (server busy or restarting). Please try again in a moment.';
  }
  if (status === 502 || status === 504) {
    return 'The request timed out or the gateway could not reach the API. Try again; if it keeps happening, the AI step may need a longer proxy timeout on the server.';
  }
  if (!data) return 'Request failed';
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail) && data.detail.length) {
    return data.detail.map((d) => d.msg || JSON.stringify(d)).join('\n');
  }
  if (data.error) return String(data.error);
  return 'Request failed';
}

/** Match chat-v2: poll every 3s, stop after 6 minutes */
const LIFE_PREDICTIONS_POLL_MS = 3000;
const LIFE_PREDICTIONS_MAX_POLLS = 120;

function lifePredictionsStatusUrl(jobId) {
  return API_BASE_URL.includes('/api')
    ? `${API_BASE_URL}/ashtakavarga/life-predictions/status/${jobId}`
    : `${API_BASE_URL}/api/ashtakavarga/life-predictions/status/${jobId}`;
}

function pollLifePredictionsJob(jobId) {
  const token = localStorage.getItem('token');
  return new Promise((resolve, reject) => {
    let pollCount = 0;

    const poll = async () => {
      try {
        const res = await fetch(lifePredictionsStatusUrl(jobId), {
          headers: { Authorization: `Bearer ${token}` },
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          reject(new Error(formatLifePredictionsError(body, res.status)));
          return;
        }
        if (body.status === 'completed' && body.result) {
          resolve(body.result);
          return;
        }
        if (body.status === 'failed') {
          const errMsg =
            body.error ||
            body.result?.error ||
            body.result?.predictions?.error ||
            'Generation failed';
          reject(new Error(String(errMsg)));
          return;
        }
        pollCount += 1;
        if (pollCount >= LIFE_PREDICTIONS_MAX_POLLS) {
          reject(new Error('TIMEOUT'));
          return;
        }
        setTimeout(() => poll().catch(reject), LIFE_PREDICTIONS_POLL_MS);
      } catch (e) {
        reject(e);
      }
    };

    poll().catch(reject);
  });
}

/** Indeterminate progress + message for chart load, transits, and AI steps */
function AshtakavargaProgressState({ title, description, hint, compact = false, className = '' }) {
  return (
    <div
      className={`ashtakavarga-progress-state${compact ? ' ashtakavarga-progress-state--compact' : ''} ${className}`.trim()}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="ashtakavarga-progress-state__spinner" aria-hidden />
      <h3 className="ashtakavarga-progress-state__title">{title}</h3>
      {description ? <p className="ashtakavarga-progress-state__desc">{description}</p> : null}
      <div className="ashtakavarga-progress-state__track" aria-hidden>
        <div className="ashtakavarga-progress-state__bar" />
      </div>
      {hint != null ? (
        <p className="ashtakavarga-progress-state__hint">{hint}</p>
      ) : compact ? null : (
        <p className="ashtakavarga-progress-state__hint">Usually finishes within a few seconds</p>
      )}
    </div>
  );
}

const MATRIX_PLANETS = [
  { key: 'Sun', abbr: 'Su' },
  { key: 'Moon', abbr: 'Mo' },
  { key: 'Mars', abbr: 'Ma' },
  { key: 'Mercury', abbr: 'Me' },
  { key: 'Jupiter', abbr: 'Ju' },
  { key: 'Venus', abbr: 'Ve' },
  { key: 'Saturn', abbr: 'Sa' },
];
const ASHTAKAVARGA_PROFILES = [
  { id: 'pvr_narasimha_rao', label: 'P.V.R. Narasimha Rao', detail: 'Replacement rule · seven grahas' },
  { id: 'parasharas_light_7', label: "Parashara’s Light 7", detail: 'Published-table profile · Lagna occupancy' },
];

function binduAt(bindus, signIndex) {
  if (bindus == null) return 0;
  if (Array.isArray(bindus)) return Number(bindus[signIndex]) || 0;
  const v = bindus[signIndex] ?? bindus[String(signIndex)];
  return Number(v) || 0;
}

function bavTone(count) {
  if (count >= 4) return 'high';
  if (count >= 2) return 'mid';
  return 'low';
}

function savTone(count) {
  if (count >= 30) return 'strong';
  if (count <= 25) return 'weak';
  return 'average';
}

const AshtakavargaModal = ({ isOpen, onClose, birthData, chartType, transitDate, variant = 'modal', onLogin, initialActiveTab = 'matrix' }) => {
  const { credits, fetchBalance } = useCredits();
  const [ashtakavargaData, setAshtakavargaData] = useState(null);
  const [transitData, setTransitData] = useState(null);
  const [ashtakLoading, setAshtakLoading] = useState(false);
  const [transitLoading, setTransitLoading] = useState(false);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(initialActiveTab);
  const [viewMode, setViewMode] = useState('birth'); // 'birth', 'transit', 'comparison'
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [eventPredictions, setEventPredictions] = useState(null);
  const [selectedEventType, setSelectedEventType] = useState('marriage');
  const [selectedAdvancedPlanet, setSelectedAdvancedPlanet] = useState('Saturn');
  const [ashtakavargaProfile, setAshtakavargaProfile] = useState('pvr_narasimha_rao');
  const [transitEventFilter, setTransitEventFilter] = useState('all');
  const ashtakRequestIdRef = useRef(0);
  const transitRequestIdRef = useRef(0);
  const eventsRequestIdRef = useRef(0);

  const [isMobileLayout, setIsMobileLayout] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(max-width: 768px)').matches
  );

  const [lifePredictions, setLifePredictions] = useState(null);
  const [loadingLifePredictions, setLoadingLifePredictions] = useState(false);
  const [lifePredictionsCacheChecking, setLifePredictionsCacheChecking] = useState(false);
  const [lifePredictionsCreditModalMode, setLifePredictionsCreditModalMode] = useState(null);
  const [lifePredictionsCreditCost, setLifePredictionsCreditCost] = useState(15);

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 768px)');
    const onChange = () => setIsMobileLayout(mq.matches);
    onChange();
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  const signNames = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

  /** House 1–12 from ascendant for each fixed zodiac sign index 0–11 (SAV keys). */
  const savHouseNumbersFromAsc = useMemo(() => {
    const chart = ashtakavargaData?.chart_data;
    const asc = chart?.ascendant;
    if (asc !== undefined && asc !== null && Number.isFinite(Number(asc))) {
      const ascSign = Math.floor(Number(asc) / 30) % 12;
      return Array.from({ length: 12 }, (_, signIndex) => ((signIndex - ascSign + 12) % 12) + 1);
    }
    const cav = ashtakavargaData?.chart_ashtakavarga;
    if (cav && typeof cav === 'object') {
      const out = Array(12).fill(null);
      for (let h = 1; h <= 12; h += 1) {
        const row = cav[String(h)];
        if (row && row.sign != null && row.sign !== '') {
          const si = Number(row.sign);
          if (si >= 0 && si <= 11) out[si] = h;
        }
      }
      return out;
    }
    return Array(12).fill(null);
  }, [ashtakavargaData]);

  useEffect(() => {
    if (!isOpen) {
      ashtakRequestIdRef.current += 1;
      transitRequestIdRef.current += 1;
      eventsRequestIdRef.current += 1;
      setAshtakavargaData(null);
      setTransitData(null);
      setEventPredictions(null);
      setAshtakLoading(false);
      setTransitLoading(false);
      setEventsLoading(false);
      setLifePredictions(null);
      setLoadingLifePredictions(false);
      setLifePredictionsCacheChecking(false);
      setLifePredictionsCreditModalMode(null);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    setActiveTab(initialActiveTab || 'matrix');
  }, [initialActiveTab, isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch('/api/credits/settings/analysis-pricing');
        if (!res.ok || cancelled) return;
        const data = await res.json();
        const n = Number(data?.pricing?.ashtakavarga);
        if (!cancelled && Number.isFinite(n) && n >= 1) setLifePredictionsCreditCost(n);
      } catch {
        /* keep default */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  // Birth ashtakavarga only when modal opens or core chart inputs change — not on tab / viewMode changes.
  useEffect(() => {
    if (!isOpen || !birthData) return;

    const apiUrl = API_BASE_URL.includes('/api')
      ? `${API_BASE_URL}/calculate-ashtakavarga`
      : `${API_BASE_URL}/api/calculate-ashtakavarga`;

    const rid = ++ashtakRequestIdRef.current;
    setAshtakLoading(true);

    (async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            birth_data: birthData,
            chart_type: chartType,
            transit_date: transitDate,
            ashtakavarga_profile: ashtakavargaProfile,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (rid === ashtakRequestIdRef.current) {
          setAshtakavargaData(data);
        }
      } catch (error) {
        console.error('Error fetching Ashtakavarga:', error);
        if (rid === ashtakRequestIdRef.current) {
          setAshtakavargaData(null);
        }
      } finally {
        if (rid === ashtakRequestIdRef.current) {
          setAshtakLoading(false);
        }
      }
    })();
  }, [isOpen, birthData, chartType, transitDate, ashtakavargaProfile]);

  useEffect(() => {
    if (!isOpen || !birthData) return;
    if (viewMode !== 'transit' && viewMode !== 'comparison') return;

    const apiUrl = API_BASE_URL.includes('/api')
      ? `${API_BASE_URL}/ashtakavarga/transit-analysis`
      : `${API_BASE_URL}/api/ashtakavarga/transit-analysis`;

    const rid = ++transitRequestIdRef.current;
    setTransitLoading(true);

    (async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            birth_data: birthData,
            transit_date: selectedDate,
            window_days: 30,
            ashtakavarga_profile: ashtakavargaProfile,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (rid === transitRequestIdRef.current) {
          setTransitData(data);
        }
      } catch (error) {
        console.error('Error fetching Transit Ashtakavarga:', error);
        if (rid === transitRequestIdRef.current) {
          setTransitData(null);
        }
      } finally {
        if (rid === transitRequestIdRef.current) {
          setTransitLoading(false);
        }
      }
    })();
  }, [isOpen, birthData, viewMode, selectedDate, ashtakavargaProfile]);

  useEffect(() => {
    if (!isOpen || !birthData) return;
    if (activeTab !== 'events') return;
    if (viewMode !== 'transit' && viewMode !== 'comparison') return;

    const apiUrl = API_BASE_URL.includes('/api')
      ? `${API_BASE_URL}/ashtakavarga/predict-specific-event`
      : `${API_BASE_URL}/api/ashtakavarga/predict-specific-event`;

    const rid = ++eventsRequestIdRef.current;
    const eventType = selectedEventType;
    setEventsLoading(true);
    setEventPredictions(null);

    (async () => {
      try {
        const token = localStorage.getItem('token');
        const currentYear = new Date().getFullYear();
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            birth_data: birthData,
            event_type: eventType,
            start_year: currentYear,
            end_year: currentYear + 5,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (rid === eventsRequestIdRef.current) {
          setEventPredictions(data);
        }
      } catch (error) {
        console.error('Error fetching Event Predictions:', error);
        if (rid === eventsRequestIdRef.current) {
          setEventPredictions(null);
        }
      } finally {
        if (rid === eventsRequestIdRef.current) {
          setEventsLoading(false);
        }
      }
    })();
  }, [isOpen, birthData, activeTab, viewMode, selectedEventType]);

  const getTabsForChartType = useCallback(() => {
    const short = (long, compact) => (isMobileLayout ? compact : long);

    /* Compare: no sub-tabs — only birth vs transit SAV grid in content. */
    if (viewMode === 'comparison') {
      return [];
    }

    const baseTabs = [
      { id: 'matrix', label: 'Matrix', icon: '▦' },
      { id: 'sarva', label: 'SAV', icon: 'Σ' },
      { id: 'individual', label: 'BAV', icon: '◫' },
    ];

    if (viewMode === 'transit') {
      return [{ id: 'transitDesk', label: short('Transit Desk', 'Transits'), icon: '◎' }, ...baseTabs];
    }

    if (chartType === 'lagna') {
      return [...baseTabs, { id: 'advanced', label: short('Kakshya & Pinda', 'Pinda'), icon: '⌘' }, { id: 'analysis', label: 'Predictions', icon: '✦' }];
    }
    if (chartType === 'navamsa') {
      return [...baseTabs, { id: 'analysis', label: short('Marriage Analysis', 'Marriage') }];
    }
    if (chartType === 'transit') {
      return [...baseTabs, { id: 'analysis', label: short('Timing Analysis', 'Analysis') }];
    }
    return [...baseTabs, { id: 'analysis', label: short('General Analysis', 'Analysis') }];
  }, [chartType, viewMode, isMobileLayout]);

  const renderAdvancedAshtakavarga = () => {
    const advanced = ashtakavargaData?.advanced_ashtakavarga;
    if (!advanced) return <div className="loading"><p>Advanced Ashtakavarga data is unavailable.</p></div>;
    const planets = MATRIX_PLANETS.map(({ key }) => key);
    const selected = advanced.shodhya_pinda?.[selectedAdvancedPlanet];
    const selectedPrastara = advanced.prastara?.[selectedAdvancedPlanet];
    const timingLabels = {
      father: 'Father · Sun H9', mother: 'Mother · Moon H4', siblings: 'Siblings · Mars H3',
      profession: 'Profession · Mercury H10', children: 'Children · Jupiter H5',
      marriage: 'Marriage · Venus H7', longevity: 'Longevity · Saturn H8',
    };
    const reductionRows = [
      ['Raw BAV', selected?.raw_bav],
      ['After Trikona', selected?.after_trikona],
      ['After Ekadhipatya', selected?.after_ekadhipatya],
    ];
    return <div className="av-advanced">
      <section className="av-advanced__intro">
        <div><p>Classical reduction chain</p><h3>Kakshya, Prastara & Shodhya Pinda</h3></div>
        <span>{advanced.convention?.school}</span>
      </section>

      <section className="av-profile-selector" aria-label="Select Shodhya Pinda convention" aria-busy={ashtakLoading}>
        <div><b>Shodhya Pinda convention</b><span>Changes Ekadhipatya Shodhana and derived timing only. Raw BAV, SAV and Kakshya geometry remain unchanged.</span></div>
        <div>{ASHTAKAVARGA_PROFILES.map((profile) => <button type="button" key={profile.id} className={ashtakavargaProfile === profile.id ? 'active' : ''} aria-pressed={ashtakavargaProfile === profile.id} onClick={() => setAshtakavargaProfile(profile.id)}><b>{profile.label}</b><span>{profile.detail}</span></button>)}</div>
        <small>{ashtakLoading ? 'Recalculating…' : `Active calculation: ${advanced.convention?.school}`}</small>
      </section>

      <section className="av-advanced__panel">
        <div className="av-advanced__heading"><div><p>Purified planetary aggregates</p><h4>Shodhya Pinda table</h4></div><small>Rāśi Pinda + Graha Pinda</small></div>
        <div className="av-advanced__table-wrap"><table className="av-advanced__table"><thead><tr><th>Graha</th><th>Raw</th><th>Reduced</th><th>Rāśi</th><th>Graha</th><th>Shodhya</th></tr></thead><tbody>
          {planets.map((planet) => { const row = advanced.shodhya_pinda?.[planet]; return <tr key={planet} className={selectedAdvancedPlanet === planet ? 'selected' : ''} onClick={() => setSelectedAdvancedPlanet(planet)}><th>{planet}</th><td>{Object.values(row?.raw_bav || {}).reduce((sum, value) => sum + Number(value), 0)}</td><td>{Object.values(row?.after_ekadhipatya || {}).reduce((sum, value) => sum + Number(value), 0)}</td><td>{row?.rashi_pinda}</td><td>{row?.graha_pinda}</td><td><b>{row?.shodhya_pinda}</b></td></tr>; })}
        </tbody></table></div>
      </section>

      <section className="av-advanced__panel">
        <div className="av-advanced__heading"><div><p>Auditable calculation</p><h4>{selectedAdvancedPlanet} reduction inspector</h4></div><small>Tap another graha in the table above</small></div>
        <div className="av-reduction-grid">
          <div className="av-reduction-grid__head"><span>Stage</span>{signNames.map((sign) => <b key={sign}>{sign.slice(0, 2)}</b>)}</div>
          {reductionRows.map(([label, values]) => <div className="av-reduction-grid__row" key={label}><span>{label}</span>{Array.from({ length: 12 }, (_, sign) => <b key={sign}>{values?.[String(sign)] ?? 0}</b>)}</div>)}
        </div>
        <div className="av-reduction-trace">
          <div><b>Trikona Shodhana</b>{selected?.trikona_trace?.map((row) => <span key={row.signs.join('-')}>{row.signs.join(' · ')}: {row.before.join('/')} → {row.after.join('/')} ({row.action.replaceAll('_', ' ')})</span>)}</div>
          <div><b>Ekadhipatya Shodhana</b>{selected?.ekadhipatya_trace?.map((row) => <span key={row.lord}>{row.signs.join(' · ')}: {row.before.join('/')} → {row.after.join('/')} ({row.action.replaceAll('_', ' ')})</span>)}</div>
        </div>
        <div className="av-advanced__heading av-advanced__heading--sub"><div><p>Eight contributors × twelve signs</p><h4>{selectedAdvancedPlanet} Prastara matrix</h4></div><small>Each column sums to the corresponding raw BAV value</small></div>
        <div className="av-reduction-grid av-prastara-grid">
          <div className="av-reduction-grid__head"><span>Contributor</span>{signNames.map((sign) => <b key={sign}>{sign.slice(0, 2)}</b>)}</div>
          {selectedPrastara?.contributors?.map((contributor) => <div className="av-reduction-grid__row" key={contributor}><span>{contributor}</span>{Array.from({ length: 12 }, (_, sign) => <b className={selectedPrastara.matrix?.[contributor]?.[String(sign)] ? 'has-bindu' : ''} key={sign}>{selectedPrastara.matrix?.[contributor]?.[String(sign)] ?? 0}</b>)}</div>)}
          <div className="av-reduction-grid__row av-prastara-total"><span>BAV total</span>{Array.from({ length: 12 }, (_, sign) => <b key={sign}>{selectedPrastara?.sign_totals?.[String(sign)] ?? 0}</b>)}</div>
        </div>
      </section>

      <section className="av-advanced__panel">
        <div className="av-advanced__heading"><div><p>Exact 3°45′ orbital zones</p><h4>Natal Kakshya activation</h4></div><small>Bindu is read from the named ruler’s Prastara row</small></div>
        <div className="av-kakshya-grid">{planets.map((planet) => { const row = advanced.natal_kakshya?.[planet]; return <article key={planet} className={row?.active ? 'active' : 'inactive'}><header><b>{planet}</b><em>{row?.active ? 'Bindu' : 'No bindu'}</em></header><strong>{row?.sign} {Number(row?.degree_in_sign || 0).toFixed(2)}°</strong><span>K{row?.kakshya_number} · {row?.kakshya_ruler}</span><small>{row?.start_degree}° ≤ degree &lt; {row?.end_degree}° · sign BAV {row?.sign_bav_total}</small></article>; })}</div>
      </section>

      <section className="av-advanced__panel">
        <div className="av-advanced__heading"><div><p>Rekhas × Shodhya Pinda</p><h4>Classical transit timing coordinates</h4></div><small>Remainders 0 map to 27 / 12</small></div>
        <div className="av-timing-grid">{Object.entries(advanced.classical_timing || {}).map(([key, row]) => <article key={key}><b>{timingLabels[key] || key}</b><strong>{row.nakshatra} · {row.rashi}</strong><span>{row.raw_rekhas} × {row.shodhya_pinda} = {row.product}</span><small>Nakshatra group: {row.vimshottari_group?.join(', ')}<br />Rāśi trines: {row.rashi_trines?.join(', ')}</small></article>)}</div>
      </section>
    </div>;
  };

  useEffect(() => {
    if (viewMode === 'transit') setActiveTab('transitDesk');
  }, [viewMode]);

  const lifePredictionsApiUrl = API_BASE_URL.includes('/api')
    ? `${API_BASE_URL}/ashtakavarga/life-predictions`
    : `${API_BASE_URL}/api/ashtakavarga/life-predictions`;

  const buildLifePredictionsBirthPayload = useCallback(() => {
    if (!birthData) return null;
    const date =
      typeof birthData.date === 'string'
        ? birthData.date.split('T')[0]
        : birthData.date;
    return {
      name: birthData.name || '',
      date,
      time: birthData.time,
      latitude: Number(birthData.latitude),
      longitude: Number(birthData.longitude),
      place: birthData.place || '',
      gender: birthData.gender || '',
    };
  }, [birthData]);

  const applyCreditCostFromResponse = useCallback((data) => {
    if (data?.credit_cost_next != null && !Number.isNaN(Number(data.credit_cost_next))) {
      setLifePredictionsCreditCost(Math.max(1, Number(data.credit_cost_next)));
    }
  }, []);

  const generateLifePredictions = async (forceRegenerate = false) => {
    const payload = buildLifePredictionsBirthPayload();
    if (!payload) {
      showToast('Birth details are required.', 'error');
      return;
    }
    const token = localStorage.getItem('token');
    if (!token) {
      showToast('Please sign in to generate life predictions.', 'info');
      onLogin?.();
      return;
    }

    setLoadingLifePredictions(true);
    try {
      const response = await fetch(lifePredictionsApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          birth_data: payload,
          force_regenerate: Boolean(forceRegenerate),
        }),
      });
      const data = await response.json().catch(() => ({}));
      applyCreditCostFromResponse(data);

      if (response.ok) {
        if (data.job_id) {
          try {
            const result = await pollLifePredictionsJob(data.job_id);
            applyCreditCostFromResponse(result);
            const serverErr =
              result.error ||
              result.predictions?.error ||
              (typeof result.detail === 'string' ? result.detail : null);
            if (serverErr) {
              showToast(String(serverErr), 'error');
            } else {
              setLifePredictions(result);
              if (Number(result.credits_charged) > 0) fetchBalance();
            }
          } catch (e) {
            const msg =
              e?.message === 'TIMEOUT'
                ? 'Still processing after 6 minutes. You can close this and open Life predictions again to check for a saved reading.'
                : e?.message || 'Could not complete predictions. Try again.';
            showToast(msg, 'error');
          }
        } else {
          const serverErr =
            data.error ||
            data.predictions?.error ||
            (typeof data.detail === 'string' ? data.detail : null);
          if (serverErr) {
            showToast(String(serverErr), 'error');
          } else {
            setLifePredictions(data);
            if (Number(data.credits_charged) > 0) fetchBalance();
          }
        }
      } else {
        const message = formatLifePredictionsError(data, response.status);
        showToast(message, 'error');
        if (response.status === 402) fetchBalance();
      }
    } catch (e) {
      console.error('Life predictions:', e);
      showToast('Could not generate predictions. Try again.', 'error');
    } finally {
      setLoadingLifePredictions(false);
    }
  };

  const onLifePredictionsMainCta = async () => {
    const payload = buildLifePredictionsBirthPayload();
    if (!payload) return;
    const token = localStorage.getItem('token');
    if (!token) {
      showToast('Please sign in to generate life predictions.', 'info');
      onLogin?.();
      return;
    }

    setLifePredictionsCacheChecking(true);
    try {
      const response = await fetch(lifePredictionsApiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          birth_data: payload,
          cache_probe: true,
          force_regenerate: false,
        }),
      });
      const data = await response.json().catch(() => ({}));
      applyCreditCostFromResponse(data);

      if (!response.ok) {
        showToast(formatLifePredictionsError(data, response.status), 'error');
        return;
      }

      if (data.cached === true && !data.error && !data.predictions?.error) {
        setLifePredictions(data);
        return;
      }

      setLifePredictionsCreditModalMode('open');
    } catch (e) {
      console.error('Life predictions cache probe:', e);
      showToast('Could not check for a saved reading. Try again.', 'error');
    } finally {
      setLifePredictionsCacheChecking(false);
    }
  };

  const onConfirmLifePredictionsCreditModal = () => {
    const mode = lifePredictionsCreditModalMode;
    setLifePredictionsCreditModalMode(null);
    generateLifePredictions(mode === 'regenerate');
  };

  const renderLifePredictionsSections = (pred) => {
    if (!pred || typeof pred !== 'object') return null;

    const insights = pred.life_domain_insights;
    const timing = pred.timing_highlights;
    const transit = pred.transit_predictions;
    const dasha = pred.dasha_analysis;
    const sav = pred.sav_strength_analysis;
    const life = pred.life_predictions;

    return (
      <>
        {pred.current_life_phase ? (
          <section className="ashtakavarga-life-section">
            <h4 className="ashtakavarga-life-section__title">Current life phase</h4>
            <p className="ashtakavarga-life-section__text">{pred.current_life_phase}</p>
          </section>
        ) : null}

        {sav?.overall_pattern ? (
          <section className="ashtakavarga-life-section">
            <h4 className="ashtakavarga-life-section__title">SAV overall pattern</h4>
            <p className="ashtakavarga-life-section__text">{sav.overall_pattern}</p>
          </section>
        ) : null}

        {insights && typeof insights === 'object' ? (
          <section className="ashtakavarga-life-section">
            <h4 className="ashtakavarga-life-section__title">Life areas (from houses)</h4>
            {Object.entries(insights).map(([key, text]) => {
              if (text == null || String(text).trim() === '') return null;
              const label = LIFE_PREDICTION_DOMAIN_LABELS[key] || key.replace(/_/g, ' ');
              return (
                <div key={key} className="ashtakavarga-life-domain-card">
                  <h5 className="ashtakavarga-life-domain-card__title">{label}</h5>
                  <p className="ashtakavarga-life-section__text">{String(text)}</p>
                </div>
              );
            })}
          </section>
        ) : null}

        {Array.isArray(timing) && timing.length > 0 ? (
          <section className="ashtakavarga-life-section">
            <h4 className="ashtakavarga-life-section__title">Timing windows</h4>
            {timing.map((item, index) => {
              if (item == null) return null;
              if (typeof item === 'string') {
                return (
                  <p key={index} className="ashtakavarga-life-bullet">
                    • {item}
                  </p>
                );
              }
              const windowLabel = item.window || item.period || item.label || `Period ${index + 1}`;
              const focus = item.focus || item.summary;
              const basis = item.ashtakavarga_basis || item.basis;
              return (
                <div key={index} className="ashtakavarga-life-timing-card">
                  <h5 className="ashtakavarga-life-timing-card__title">{windowLabel}</h5>
                  {focus ? <p className="ashtakavarga-life-section__text">{focus}</p> : null}
                  {basis ? <p className="ashtakavarga-life-timing-card__basis">Ashtakavarga: {basis}</p> : null}
                </div>
              );
            })}
          </section>
        ) : null}

        {transit ? (
          <section className="ashtakavarga-life-section">
            <h4 className="ashtakavarga-life-section__title">Transits</h4>
            {transit.saturn_influence ? (
              <>
                <h5 className="ashtakavarga-life-subtitle">Saturn</h5>
                <p className="ashtakavarga-life-section__text">{transit.saturn_influence}</p>
              </>
            ) : null}
            {transit.jupiter_influence ? (
              <>
                <h5 className="ashtakavarga-life-subtitle">Jupiter</h5>
                <p className="ashtakavarga-life-section__text">{transit.jupiter_influence}</p>
              </>
            ) : null}
            {transit.rahu_ketu_influence ? (
              <>
                <h5 className="ashtakavarga-life-subtitle">Rahu & Ketu</h5>
                <p className="ashtakavarga-life-section__text">{transit.rahu_ketu_influence}</p>
              </>
            ) : null}
            {Array.isArray(transit.timing_recommendations) && transit.timing_recommendations.length > 0 ? (
              <>
                <h5 className="ashtakavarga-life-subtitle">Timing tips</h5>
                {transit.timing_recommendations.map((line, i) => (
                  <p key={i} className="ashtakavarga-life-bullet">
                    • {line}
                  </p>
                ))}
              </>
            ) : null}
          </section>
        ) : null}

        {dasha ? (
          <section className="ashtakavarga-life-section">
            <h4 className="ashtakavarga-life-section__title">Dasha</h4>
            {dasha.current_period_strength ? (
              <>
                <h5 className="ashtakavarga-life-subtitle">Period strength</h5>
                <p className="ashtakavarga-life-section__text">{dasha.current_period_strength}</p>
              </>
            ) : null}
            {dasha.expected_results ? (
              <>
                <h5 className="ashtakavarga-life-subtitle">What to expect</h5>
                <p className="ashtakavarga-life-section__text">{dasha.expected_results}</p>
              </>
            ) : null}
            {Array.isArray(dasha.recommendations) && dasha.recommendations.length > 0 ? (
              <>
                <h5 className="ashtakavarga-life-subtitle">Dasha recommendations</h5>
                {dasha.recommendations.map((line, i) => (
                  <p key={i} className="ashtakavarga-life-bullet">
                    • {line}
                  </p>
                ))}
              </>
            ) : null}
          </section>
        ) : null}

        {sav?.strong_areas && sav.strong_areas.length > 0 ? (
          <section className="ashtakavarga-life-section">
            <h4 className="ashtakavarga-life-section__title">Strong areas</h4>
            {sav.strong_areas.map((area, index) => (
              <p key={index} className="ashtakavarga-life-bullet">
                • {area}
              </p>
            ))}
          </section>
        ) : null}

        {sav?.challenging_areas && sav.challenging_areas.length > 0 ? (
          <section className="ashtakavarga-life-section">
            <h4 className="ashtakavarga-life-section__title">Challenging areas</h4>
            {sav.challenging_areas.map((area, index) => (
              <p key={index} className="ashtakavarga-life-bullet">
                • {area}
              </p>
            ))}
          </section>
        ) : null}

        {life?.next_6_months ? (
          <section className="ashtakavarga-life-section">
            <h4 className="ashtakavarga-life-section__title">Next 6 months</h4>
            <p className="ashtakavarga-life-section__text">{life.next_6_months}</p>
          </section>
        ) : null}

        {life?.next_year ? (
          <section className="ashtakavarga-life-section">
            <h4 className="ashtakavarga-life-section__title">Next year</h4>
            <p className="ashtakavarga-life-section__text">{life.next_year}</p>
          </section>
        ) : null}

        {life?.major_themes && life.major_themes.length > 0 ? (
          <section className="ashtakavarga-life-section">
            <h4 className="ashtakavarga-life-section__title">Major themes</h4>
            {life.major_themes.map((theme, index) => (
              <p key={index} className="ashtakavarga-life-bullet">
                • {theme}
              </p>
            ))}
          </section>
        ) : null}

        {pred.remedial_measures && pred.remedial_measures.length > 0 ? (
          <section className="ashtakavarga-life-section">
            <h4 className="ashtakavarga-life-section__title">Remedial measures</h4>
            {pred.remedial_measures.map((remedy, index) => (
              <p key={index} className="ashtakavarga-life-bullet">
                • {remedy}
              </p>
            ))}
          </section>
        ) : null}
      </>
    );
  };

  const renderLagnaBirthLifeAnalysis = () => {
    const busy = loadingLifePredictions || lifePredictionsCacheChecking;
    const pred = lifePredictions?.predictions;

    return (
      <div className="ashtakavarga-life-predictions">
        {loadingLifePredictions && lifePredictions
          ? createPortal(
              <div
                className="ashtakavarga-life-regen-overlay ashtakavarga-life-regen-overlay--viewport"
                role="alertdialog"
                aria-busy="true"
                aria-live="polite"
                aria-label="Updating reading"
              >
                <div className="ashtakavarga-life-regen-overlay__inner">
                  <div
                    className="ashtakavarga-progress-state__spinner ashtakavarga-progress-state__spinner--sm"
                    aria-hidden
                  />
                  <p className="ashtakavarga-life-regen-overlay__title">Updating reading…</p>
                  <div
                    className="ashtakavarga-progress-state__track ashtakavarga-progress-state__track--overlay"
                    aria-hidden
                  >
                    <div className="ashtakavarga-progress-state__bar" />
                  </div>
                </div>
              </div>,
              document.body
            )
          : null}

        {!lifePredictions ? (
          <>
            <div className="ashtakavarga-life-hero">
              <p className="ashtakavarga-life-hero__eyebrow">Life analysis</p>
              <p className="ashtakavarga-life-hero__teaser">
                AI reading from your Sarvashtakavarga, houses, transits, and dasha — grounded in bindus from your chart.
              </p>
              <div className="ashtakavarga-life-hero__chips">
                <span>12 houses</span>
                <span>Transits</span>
                <span>Dasha</span>
              </div>
              <button
                type="button"
                className="ashtakavarga-life-hero__cta"
                onClick={onLifePredictionsMainCta}
                disabled={busy}
              >
                {busy ? (lifePredictionsCacheChecking ? 'Checking saved reading…' : 'Generating…') : 'Open life predictions'}
              </button>
              {busy ? (
                <AshtakavargaProgressState
                  compact
                  className="ashtakavarga-progress-state--hero"
                  title={lifePredictionsCacheChecking ? 'Checking cache' : 'Generating reading'}
                  description={
                    lifePredictionsCacheChecking
                      ? 'Looking for a saved Life Analysis reading for this profile…'
                      : 'Running the model on your bindus, houses, transits, and dasha. This may take up to a minute.'
                  }
                  hint={lifePredictionsCacheChecking ? 'Almost there…' : 'Safe to keep this tab open'}
                />
              ) : null}
              <div className="ashtakavarga-life-hero__foot">
                <p className="ashtakavarga-life-hero__hint">
                  <span className="ashtakavarga-life-hero__hint-credits">{lifePredictionsCreditCost} credits</span>
                  <span className="ashtakavarga-life-hero__hint-line">
                    first run · saved reading replays free
                  </span>
                </p>
                <p className="ashtakavarga-life-hero__sub">
                  <span className="ashtakavarga-life-hero__sub-label">Methodology</span>
                  <span className="ashtakavarga-life-hero__sub-text">Vinay Aditya · Ashtakavarga</span>
                </p>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="ashtakavarga-life-results-header">
              <div>
                <h3 className="ashtakavarga-life-results-title">Life predictions</h3>
                <p className="ashtakavarga-life-results-sub">
                  {lifePredictions?.methodology ||
                    lifePredictions?.predictions?.methodology ||
                    'Vinay Aditya · Ashtakavarga'}
                </p>
                {lifePredictions?.cached ? (
                  <p className="ashtakavarga-life-results-cached">
                    Saved reading — no credits to view again. Regenerate for a fresh pass ({lifePredictionsCreditCost}{' '}
                    credits).
                  </p>
                ) : null}
              </div>
              <button
                type="button"
                className="ashtakavarga-life-regenerate-btn"
                onClick={() => setLifePredictionsCreditModalMode('regenerate')}
                disabled={loadingLifePredictions}
              >
                Regenerate
              </button>
            </div>
            <div className="ashtakavarga-life-results-body">{renderLifePredictionsSections(pred)}</div>
          </>
        )}
      </div>
    );
  };

  const renderBinduMatrix = () => {
    if (viewMode === 'birth' && !ashtakavargaData) return null;
    if (viewMode === 'transit' && !transitData) {
      return transitLoading ? (
        <AshtakavargaProgressState
          title="Loading transit Ashtakavarga"
          description="Placing transit grahas against the fixed natal bindu ledger…"
        />
      ) : (
        <div className="loading">
          <p>Could not load transit data.</p>
        </div>
      );
    }

    const data = viewMode === 'transit' ? transitData?.transit_ashtakavarga : ashtakavargaData?.ashtakavarga;
    if (!data) return null;

    const { individual_charts = {}, sarvashtakavarga, total_bindus, lagna_chart } = data;
    const title = viewMode === 'transit'
      ? `Transit bindu matrix (${selectedDate})`
      : 'Birth bindu matrix';

    const rows = Array.from({ length: 12 }, (_, i) => {
      const house = i + 1;
      let signIndex = savHouseNumbersFromAsc.findIndex((h) => h === house);
      if (signIndex < 0) signIndex = i;
      return { house, signIndex, signName: signNames[signIndex] };
    });

    const planetTotals = MATRIX_PLANETS.map(({ key }) => {
      const chart = individual_charts[key];
      if (chart?.total != null) return Number(chart.total) || 0;
      if (!chart?.bindus) return 0;
      return Array.from({ length: 12 }, (_, si) => binduAt(chart.bindus, si)).reduce((a, b) => a + b, 0);
    });

    const lagnaBindus = lagna_chart?.bindus;
    const lagnaTotal = lagna_chart
      ? (lagna_chart.total != null
        ? Number(lagna_chart.total) || 0
        : Array.from({ length: 12 }, (_, si) => binduAt(lagnaBindus, si)).reduce((a, b) => a + b, 0))
      : null;

    const savTotal = total_bindus != null
      ? Number(total_bindus) || 0
      : Array.from({ length: 12 }, (_, si) => binduAt(sarvashtakavarga, si)).reduce((a, b) => a + b, 0);

    return (
      <div className="av-matrix" aria-label="House by planet bindu matrix">
        <header className="av-matrix__head">
          <h3>{title}</h3>
          <p>
            Houses from lagna · BAV columns · SAV total
            {savTotal ? ` · ${savTotal} bindus` : ''}
          </p>
        </header>
        <div className="av-matrix__scroll">
          <table className="av-matrix__table">
            <thead>
              <tr>
                <th scope="col" className="av-matrix__sticky">H</th>
                <th scope="col" className="av-matrix__sign">Sign</th>
                {MATRIX_PLANETS.map((p) => (
                  <th key={p.key} scope="col" title={p.key}>{p.abbr}</th>
                ))}
                {lagna_chart ? <th scope="col" title="Lagna BAV">La</th> : null}
                <th scope="col" className="av-matrix__sav" title="Sarvashtakavarga">SAV</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const sav = binduAt(sarvashtakavarga, row.signIndex);
                return (
                  <tr key={row.house}>
                    <th scope="row" className="av-matrix__sticky">{row.house}</th>
                    <td className="av-matrix__sign">{row.signName.slice(0, 3)}</td>
                    {MATRIX_PLANETS.map((p) => {
                      const count = binduAt(individual_charts[p.key]?.bindus, row.signIndex);
                      return (
                        <td
                          key={p.key}
                          className={`av-matrix__cell av-matrix__cell--${bavTone(count)}`}
                          title={`${p.key} in ${row.signName} (H${row.house}): ${count}`}
                        >
                          {count}
                        </td>
                      );
                    })}
                    {lagna_chart ? (
                      <td
                        className={`av-matrix__cell av-matrix__cell--${bavTone(binduAt(lagnaBindus, row.signIndex))}`}
                        title={`Lagna in ${row.signName} (H${row.house})`}
                      >
                        {binduAt(lagnaBindus, row.signIndex)}
                      </td>
                    ) : null}
                    <td
                      className={`av-matrix__sav av-matrix__cell--${savTone(sav)}`}
                      title={`SAV for ${row.signName} (H${row.house}): ${sav}`}
                    >
                      {sav}
                    </td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr>
                <th scope="row" className="av-matrix__sticky" colSpan={2}>Σ</th>
                {planetTotals.map((total, idx) => (
                  <td key={MATRIX_PLANETS[idx].key}>{total}</td>
                ))}
                {lagna_chart ? <td>{lagnaTotal}</td> : null}
                <td className="av-matrix__sav">{savTotal}</td>
              </tr>
            </tfoot>
          </table>
        </div>
        <div className="av-matrix__legend" aria-hidden="true">
          <span className="av-matrix__cell--high">BAV 4+</span>
          <span className="av-matrix__cell--mid">BAV 2–3</span>
          <span className="av-matrix__cell--low">BAV 0–1</span>
          <span className="av-matrix__cell--strong">SAV 30+</span>
          <span className="av-matrix__cell--weak">SAV ≤25</span>
        </div>
      </div>
    );
  };

  const renderSarvashtakavarga = () => {
    if (viewMode === 'birth' && !ashtakavargaData) return null;
    if ((viewMode === 'transit' || viewMode === 'comparison') && !transitData) {
      return transitLoading ? (
        <AshtakavargaProgressState
          title="Loading transit Ashtakavarga"
          description="Computing transit positions and bindus for your selected date…"
        />
      ) : (
        <div className="loading">
          <p>Could not load transit data.</p>
        </div>
      );
    }

    if (viewMode === 'comparison' && ashtakavargaData && transitData) {
      return renderComparison();
    }

    const data = viewMode === 'transit' ? transitData.transit_ashtakavarga : ashtakavargaData.ashtakavarga;
    const { sarvashtakavarga, total_bindus } = data;
    const title = viewMode === 'transit' ? `Natal SAV reference for transits (${selectedDate})` : 'Birth Sarvashtakavarga';

    return (
      <div className="sarva-chart">
        <h3>{title} ({total_bindus} total bindus)</h3>
        <div className="bindu-grid">
          {signNames.map((sign, index) => {
            const houseNum = savHouseNumbersFromAsc[index];
            return (
              <div key={index} className={`bindu-cell ${sarvashtakavarga[index] >= 30 ? 'strong' : sarvashtakavarga[index] <= 25 ? 'weak' : 'average'}`}>
                <div className="sign-name">{sign}</div>
                {houseNum != null ? (
                  <div className="bindu-house" title={`House ${houseNum} from ascendant`}>
                    H{houseNum}
                  </div>
                ) : null}
                <div className="bindu-count">{sarvashtakavarga[index]}</div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderClassicalTransitDesk = () => {
    const transit = transitData?.classical_transit;
    if (!transit) {
      return transitLoading ? (
        <AshtakavargaProgressState
          title="Building the classical transit desk"
          description="Resolving each graha against natal BAV, SAV, Prastara, Kakshya and Shodhya-sensitive places…"
        />
      ) : (
        <div className="loading"><p>No classical transit data.</p></div>
      );
    }
    const filterOptions = [
      ['all', 'All'], ['kakshya_ingress', 'Kakshya'], ['rashi_ingress', 'Rāśi'],
      ['nakshatra_ingress', 'Nakshatra'], ['direction_station', 'Stations'],
    ];
    const events = transit.calendar_window?.events || [];
    const visibleEvents = transitEventFilter === 'all' ? events : events.filter((row) => row.type === transitEventFilter);
    const eventLabels = {
      kakshya_ingress: 'Kakshya ingress', rashi_ingress: 'Rāśi ingress',
      nakshatra_ingress: 'Nakshatra ingress', direction_station: 'Direction station',
    };
    return <div className="av-transit-desk">
      <section className="av-advanced__intro">
        <div><p>Fixed natal AV ledger</p><h3>Classical transit desk · {selectedDate}</h3></div>
        <span>{transit.convention?.school}</span>
      </section>

      <section className="av-profile-selector" aria-label="Select transit Shodhya convention" aria-busy={transitLoading}>
        <div><b>Shodhya Pinda convention</b><span>BAV, SAV and Prastara stay natal and fixed. The profile changes Shodhya-sensitive transit coordinates only.</span></div>
        <div>{ASHTAKAVARGA_PROFILES.map((profile) => <button type="button" key={profile.id} className={ashtakavargaProfile === profile.id ? 'active' : ''} aria-pressed={ashtakavargaProfile === profile.id} onClick={() => setAshtakavargaProfile(profile.id)}><b>{profile.label}</b><span>{profile.detail}</span></button>)}</div>
        <small>{transitLoading ? 'Recalculating…' : `Basis: ${transit.basis.replaceAll('_', ' ')}`}</small>
      </section>

      <section className="av-advanced__panel">
        <div className="av-advanced__heading"><div><p>Seven grahas at the selected moment</p><h4>Natal-reference transit evidence</h4></div><small>Snapshot {transit.snapshot_utc}</small></div>
        <div className="av-transit-table-wrap"><table className="av-transit-table"><thead><tr><th>Graha</th><th>Position</th><th>House</th><th>Natal BAV</th><th>Natal SAV</th><th>Kakshya</th><th>Sensitive place</th></tr></thead><tbody>
          {transit.planet_transits?.map((row) => <tr key={row.planet}><th>{row.planet}<small>{row.retrograde ? ' Rx' : ' Direct'}</small></th><td>{row.sign} {Number(row.degree_in_sign).toFixed(2)}°<small>{row.nakshatra}</small></td><td>H{row.natal_house}</td><td><b>{row.natal_bav_bindus}</b><small>{row.natal_bav_band.replaceAll('_', ' ')}</small></td><td><b>{row.natal_sav_bindus}</b><small>{row.natal_sav_band}</small></td><td className={row.kakshya?.active ? 'has-bindu' : 'no-bindu'}>K{row.kakshya?.kakshya_number} · {row.kakshya?.kakshya_ruler}<small>{row.kakshya?.active ? 'Contributor bindu' : 'No contributor bindu'}</small></td><td>{row.sensitive_timing?.double_match ? 'Rāśi + Nakshatra' : row.sensitive_timing?.rashi_match ? 'Rāśi match' : row.sensitive_timing?.nakshatra_match ? 'Nakshatra match' : 'No match'}<small>{row.sensitive_timing?.topic}</small></td></tr>)}
        </tbody></table></div>
      </section>

      <section className="av-advanced__panel">
        <div className="av-advanced__heading"><div><p>Shodhya-sensitive coordinates</p><h4>Current sensitive-place matches</h4></div><small>{transit.sensitive_hits?.length || 0} of 7 grahas</small></div>
        <div className="av-transit-hit-grid">{transit.sensitive_hits?.length ? transit.sensitive_hits.map((row) => <article key={row.planet}><b>{row.planet} · {row.sensitive_timing.topic}</b><strong>{row.sign} · {row.nakshatra}</strong><span>{row.sensitive_timing.rashi_match ? 'Rāśi trine matched' : 'Rāśi not matched'} · {row.sensitive_timing.nakshatra_match ? 'Nakshatra group matched' : 'Nakshatra not matched'}</span><small>Reference: {row.sensitive_timing.reference_rashi} · {row.sensitive_timing.reference_nakshatra}</small></article>) : <p>No Shodhya-sensitive rāśi or nakshatra match at this snapshot.</p>}</div>
      </section>

      <section className="av-advanced__panel">
        <div className="av-advanced__heading"><div><p>Exact UTC boundary search</p><h4>Next {transit.calendar_window?.days} days</h4></div><small>Rāśi · nakshatra · Kakshya · stations</small></div>
        <div className="av-transit-filters">{filterOptions.map(([id, label]) => <button type="button" key={id} className={transitEventFilter === id ? 'active' : ''} onClick={() => setTransitEventFilter(id)}>{label}</button>)}</div>
        <div className="av-transit-events">{visibleEvents.map((event, index) => <article key={`${event.timestamp_utc}-${event.planet}-${event.type}-${index}`}><time>{new Date(event.timestamp_utc).toLocaleString()}</time><div><b>{event.planet} · {eventLabels[event.type]}</b><span>{event.sign} · {event.nakshatra} · K{event.kakshya_number} {event.kakshya_ruler}</span><small>Natal BAV {event.natal_bav_bindus} · SAV {event.natal_sav_bindus} · Kakshya {event.kakshya_bindu ? 'bindu' : 'no bindu'}{event.sensitive_timing?.double_match ? ' · double sensitive match' : event.sensitive_timing?.rashi_match || event.sensitive_timing?.nakshatra_match ? ' · sensitive-place match' : ''}</small></div></article>)}</div>
      </section>
      <aside className="av-transit-guardrail">{transit.interpretation_guardrail}</aside>
    </div>;
  };

  const renderComparison = () => renderClassicalTransitDesk();
  const renderTransitRecommendations = () => renderClassicalTransitDesk();

  const eventTypeSelect = (
    <select
      value={selectedEventType}
      onChange={(e) => setSelectedEventType(e.target.value)}
    >
      <option value="marriage">Marriage</option>
      <option value="career">Career Change</option>
      <option value="children">Children</option>
      <option value="property">Property</option>
      <option value="education">Education</option>
      <option value="health">Health</option>
      <option value="travel">Travel</option>
      <option value="spirituality">Spirituality</option>
    </select>
  );

  const renderEventPredictions = () => {
    const payload = eventPredictions && (eventPredictions.data != null ? eventPredictions.data : eventPredictions);
    const predictions = (payload && Array.isArray(payload.predictions)) ? payload.predictions : [];

    if (eventsLoading) {
      return (
        <div className="event-predictions">
          <h3>Event Predictions</h3>
          <div className="event-type-selector">
            <label>Select Event Type:</label>
            {eventTypeSelect}
          </div>
          <AshtakavargaProgressState
            compact
            title="Loading event predictions"
            description="Scoring windows for the selected life area…"
          />
        </div>
      );
    }

    if (!eventPredictions) {
      return (
        <div className="event-predictions">
          <h3>Event Predictions</h3>
          <div className="event-type-selector">
            <label>Select Event Type:</label>
            {eventTypeSelect}
          </div>
          <div className="loading">
            <p>Could not load predictions. Try again or pick another event type.</p>
          </div>
        </div>
      );
    }

    return (
      <div className="event-predictions">
        <h3>{selectedEventType.charAt(0).toUpperCase() + selectedEventType.slice(1)} Predictions</h3>
        
        <div className="event-type-selector">
          <label>Event Type:</label>
          {eventTypeSelect}
        </div>

        <div className="predictions-list">
          {predictions.map((prediction, index) => {
            if (!prediction || typeof prediction !== 'object') return null;
            const prob = (prediction.probability || '').toString().toLowerCase().replace(/\s+/g, '-');
            const bestMonths = Array.isArray(prediction.best_months) ? prediction.best_months : [];
            return (
              <div key={index} className={`prediction-card ${prob || 'unknown'}`}>
                <div className="prediction-header">
                  <span className="year">{prediction.year ?? '—'}</span>
                  <span className={`probability ${prob || 'unknown'}`}>
                    {prediction.probability ?? '—'}
                  </span>
                </div>
                <div className="prediction-details">
                  <div className="strength-bar">
                    <div 
                      className="strength-fill" 
                      style={{ width: `${Math.min(100, ((prediction.strength ?? 0) / 360) * 100)}%` }}
                    />
                  </div>
                  <p>{prediction.analysis ?? ''}</p>
                  {bestMonths.length > 0 && (
                    <div className="best-months">
                      <strong>Best Months:</strong> {bestMonths.join(', ')}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderIndividualCharts = () => {
    if (!ashtakavargaData) return null;

    const { individual_charts } = ashtakavargaData.ashtakavarga;

    return (
      <div className="individual-charts">
        <h3>Individual Planet Charts</h3>
        {Object.entries(individual_charts).map(([planet, data]) => (
          <div key={planet} className="planet-chart">
            <h4>{planet} ({data.total} bindus)</h4>
            <div className="bindu-row">
              {signNames.map((sign, index) => {
                const count = data.bindus[index];
                let className = 'mini-bindu ';
                if (count >= 4) className += 'high-bindu';
                else if (count >= 2) className += 'medium-bindu';
                else className += 'low-bindu';
                
                return (
                  <div key={index} className={className}>
                    <span className="mini-sign">{sign.slice(0, 3)}</span>
                    <span className="mini-count">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
        <div style={{ height: '120px' }}></div>
      </div>
    );
  };

  const renderAnalysis = () => {
    if (!ashtakavargaData) return null;
    if (chartType === 'lagna' && viewMode === 'birth') {
      return renderLagnaBirthLifeAnalysis();
    }

    const { analysis } = ashtakavargaData;
    if (!analysis) {
      return (
        <div className="analysis-content">
          <p>No analysis available.</p>
        </div>
      );
    }

    return (
      <div className="analysis-content">
        <h3>Analysis</h3>
        {analysis.strongest_sign && (
          <div className="strength-analysis">
            <div className="strong-sign">
              <strong>Strongest Sign:</strong> {analysis.strongest_sign.name} ({analysis.strongest_sign.bindus} bindus)
            </div>
            <div className="weak-sign">
              <strong>Weakest Sign:</strong> {analysis.weakest_sign.name} ({analysis.weakest_sign.bindus} bindus)
            </div>
          </div>
        )}

        {analysis.recommendations && (
          <div className="recommendations">
            <h4>Recommendations:</h4>
            <ul>
              {analysis.recommendations.map((rec, index) => (
                <li key={index}>{rec}</li>
              ))}
            </ul>
          </div>
        )}

        {analysis.focus && (
          <div className="focus-area">
            <h4>Focus Area:</h4>
            <p>{analysis.focus}</p>
            <p>{analysis.analysis}</p>
          </div>
        )}
        <div style={{ height: '120px' }}></div>
      </div>
    );
  };

  if (!isOpen) return null;

  const creditConfirmModal =
    lifePredictionsCreditModalMode !== null
      ? createPortal(
          <div
            className="ashtakavarga-credit-confirm-overlay"
            role="dialog"
            aria-modal="true"
            aria-labelledby="ashtakavarga-credit-title"
            onClick={() => setLifePredictionsCreditModalMode(null)}
          >
            <div className="ashtakavarga-credit-confirm-dialog" onClick={(e) => e.stopPropagation()}>
              <h3 id="ashtakavarga-credit-title">
                {lifePredictionsCreditModalMode === 'regenerate'
                  ? 'Regenerate life analysis?'
                  : 'Life analysis reading'}
              </h3>
              <p className="ashtakavarga-credit-confirm-desc">
                {lifePredictionsCreditModalMode === 'regenerate'
                  ? `This runs a fresh AI reading and replaces your saved one. It will use ${lifePredictionsCreditCost} credits if generation succeeds. Your balance: ${credits} credits.`
                  : `Starting a new AI reading uses up to ${lifePredictionsCreditCost} credits if you do not already have one saved for this profile. Your balance: ${credits} credits.`}
              </p>
              <div className="ashtakavarga-credit-confirm-cost">{lifePredictionsCreditCost} credits</div>
              <div className="ashtakavarga-credit-confirm-actions">
                <button
                  type="button"
                  className="ashtakavarga-credit-confirm-cancel"
                  onClick={() => setLifePredictionsCreditModalMode(null)}
                >
                  Cancel
                </button>
                <button type="button" className="ashtakavarga-credit-confirm-ok" onClick={onConfirmLifePredictionsCreditModal}>
                  Start analysis
                </button>
              </div>
            </div>
          </div>,
          document.body
        )
      : null;

  const sectionTabs = getTabsForChartType();

  const modalPanel = (
    <div
      className={`ashtakavarga-modal ${variant === 'page' ? 'ashtakavarga-modal--embedded' : ''}`}
      onClick={variant === 'modal' ? (e) => e.stopPropagation() : undefined}
    >
      <div className="modal-header">
        <h2>{variant === 'page' ? 'Bindu analysis' : 'Ashtakavarga Analysis'} · {chartType.charAt(0).toUpperCase() + chartType.slice(1)} chart</h2>
        <div className="header-controls">
          <div className="view-mode-toggle">
            <button
              type="button"
              className={viewMode === 'birth' ? 'active' : ''}
              onClick={() => setViewMode('birth')}
            >
              Birth
            </button>
            <button
              type="button"
              className={viewMode === 'transit' ? 'active' : ''}
              onClick={() => setViewMode('transit')}
            >
              Transit
            </button>
            <button
              type="button"
              className={viewMode === 'comparison' ? 'active' : ''}
              onClick={() => setViewMode('comparison')}
            >
              Compare
            </button>
          </div>
          {(viewMode === 'transit' || viewMode === 'comparison') && (
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="date-picker"
            />
          )}
          {variant === 'modal' ? (
            <button type="button" className="close-btn" onClick={onClose} aria-label="Close">×</button>
          ) : null}
        </div>
      </div>

      {sectionTabs.length > 0 ? (
        <div className="modal-tabs" role="tablist" aria-label="Ashtakavarga sections">
          {sectionTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {variant === 'page' && isMobileLayout ? (
                <>
                  <span className="av-tab-icon" aria-hidden>{tab.icon || '•'}</span>
                  <span className="av-tab-label">{tab.label}</span>
                </>
              ) : tab.label}
            </button>
          ))}
        </div>
      ) : null}

      <div className="modal-content">
        {ashtakLoading && !ashtakavargaData ? (
          <AshtakavargaProgressState
            title="Computing Ashtakavarga"
            description="Sarvashtakavarga totals, planetary BAV, and chart context from Swiss Ephemeris…"
            hint={variant === 'page' ? 'Full-page tool — charts appear below when ready' : undefined}
          />
        ) : !ashtakavargaData ? (
          <div className="loading">
            <p>Failed to load Ashtakavarga data. Please try again.</p>
            <p style={{ fontSize: '0.8rem', color: '#666', marginTop: '10px' }}>
              Debug: Check browser console for errors
            </p>
          </div>
        ) : viewMode === 'comparison' ? (
          renderSarvashtakavarga()
        ) : (
          <>
            {activeTab === 'matrix' && renderBinduMatrix()}
            {activeTab === 'sarva' && renderSarvashtakavarga()}
            {activeTab === 'individual' && renderIndividualCharts()}
            {activeTab === 'advanced' && renderAdvancedAshtakavarga()}
            {activeTab === 'transitDesk' && renderClassicalTransitDesk()}
            {activeTab === 'recommendations' && renderTransitRecommendations()}
            {activeTab === 'events' && renderEventPredictions()}
            {activeTab === 'analysis' && renderAnalysis()}
          </>
        )}
      </div>
    </div>
  );

  if (variant === 'page') {
    return (
      <>
        <div className="ashtakavarga-tool-page">{modalPanel}</div>
        {creditConfirmModal}
      </>
    );
  }

  return (
    <>
      {createPortal(
        <div className="ashtakavarga-modal-overlay" onClick={onClose}>
          {modalPanel}
        </div>,
        document.body
      )}
      {creditConfirmModal}
    </>
  );
};

export default AshtakavargaModal;
