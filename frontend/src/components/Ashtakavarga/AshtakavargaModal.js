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

function formatLifePredictionsError(data) {
  if (!data) return 'Request failed';
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail) && data.detail.length) {
    return data.detail.map((d) => d.msg || JSON.stringify(d)).join('\n');
  }
  if (data.error) return String(data.error);
  return 'Request failed';
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

const AshtakavargaModal = ({ isOpen, onClose, birthData, chartType, transitDate, variant = 'modal', onLogin }) => {
  const { credits, fetchBalance } = useCredits();
  const [ashtakavargaData, setAshtakavargaData] = useState(null);
  const [transitData, setTransitData] = useState(null);
  const [ashtakLoading, setAshtakLoading] = useState(false);
  const [transitLoading, setTransitLoading] = useState(false);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('sarva');
  const [viewMode, setViewMode] = useState('birth'); // 'birth', 'transit', 'comparison'
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [eventPredictions, setEventPredictions] = useState(null);
  const [selectedEventType, setSelectedEventType] = useState('marriage');
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
  }, [isOpen, birthData, chartType, transitDate]);

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
  }, [isOpen, birthData, viewMode, selectedDate]);

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
      { id: 'sarva', label: 'SAV' },
      { id: 'individual', label: 'BAV' },
    ];

    if (viewMode === 'transit') {
      return baseTabs;
    }

    if (chartType === 'lagna') {
      return [...baseTabs, { id: 'analysis', label: 'Predictions' }];
    }
    if (chartType === 'navamsa') {
      return [...baseTabs, { id: 'analysis', label: short('Marriage Analysis', 'Marriage') }];
    }
    if (chartType === 'transit') {
      return [...baseTabs, { id: 'analysis', label: short('Timing Analysis', 'Analysis') }];
    }
    return [...baseTabs, { id: 'analysis', label: short('General Analysis', 'Analysis') }];
  }, [chartType, viewMode, isMobileLayout]);

  useEffect(() => {
    if (viewMode !== 'transit') return;
    if (['recommendations', 'events', 'analysis'].includes(activeTab)) {
      setActiveTab('sarva');
    }
  }, [viewMode, activeTab]);

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
      } else {
        const message = formatLifePredictionsError(data);
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
        showToast(formatLifePredictionsError(data), 'error');
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
              <p className="ashtakavarga-life-hero__eyebrow">Dots of Destiny</p>
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
                      ? 'Looking for a saved Dots of Destiny reading for this profile…'
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
                    "Vinay Aditya's Dots of Destiny"}
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
    const title = viewMode === 'transit' ? `Transit Sarvashtakavarga (${selectedDate})` : 'Birth Sarvashtakavarga';

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

  const renderComparison = () => {
    if (!ashtakavargaData || !transitData) return null;

    const birthData = ashtakavargaData.ashtakavarga.sarvashtakavarga;
    const transitAV = transitData.transit_ashtakavarga.sarvashtakavarga;
    const comparison = transitData.birth_transit_comparison;
    
    // Handle both old and new comparison format
    const comparisonData = comparison.summary ? comparison : 
      Object.keys(comparison).reduce((acc, sign) => {
        if (typeof comparison[sign] === 'object' && comparison[sign].birth_points !== undefined) {
          acc[sign] = comparison[sign];
        }
        return acc;
      }, {});

    return (
      <div className="comparison-chart">
        <h3>Birth vs Transit Comparison ({selectedDate})</h3>
        <div className="comparison-grid">
          {signNames.map((sign, index) => {
            const signData = comparisonData[sign] || comparison[sign];
            if (!signData) return null;
            
            const status = signData.status.includes('significantly') ? 
              signData.status : 
              signData.difference > 0 ? 'enhanced' : 
              signData.difference < 0 ? 'reduced' : 'stable';
            
            const houseNum = savHouseNumbersFromAsc[index];
            return (
              <div key={index} className={`comparison-cell ${status}`}>
                <div className="sign-name">{sign}</div>
                {houseNum != null ? (
                  <div className="bindu-house comparison-house" title={`House ${houseNum} from ascendant`}>
                    H{houseNum}
                  </div>
                ) : null}
                <div className="birth-count">B: {signData.birth_points}</div>
                <div className="transit-count">T: {signData.transit_points}</div>
                <div className={`difference ${status}`}>
                  {signData.difference > 0 ? '+' : ''}{signData.difference}
                  {signData.percentage_change !== 0 && (
                    <span className="percentage">({signData.percentage_change}%)</span>
                  )}
                </div>
                <div className="strength-category">{signData.strength_category}</div>
              </div>
            );
          })}
        </div>
        <div className="legend">
          <span className="significantly_enhanced">■ Significantly Enhanced</span>
          <span className="enhanced">■ Enhanced</span>
          <span className="stable">■ Stable</span>
          <span className="reduced">■ Reduced</span>
          <span className="significantly_reduced">■ Significantly Reduced</span>
        </div>
        {comparison.summary && (
          <div className="comparison-summary">
            <h4>Analysis Summary</h4>
            <div className="summary-stats">
              <span>Stability Index: {comparison.summary.stability_index}%</span>
              <span>Enhanced Signs: {comparison.summary.enhanced_signs}</span>
              <span>Reduced Signs: {comparison.summary.reduced_signs}</span>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderTransitRecommendations = () => {
    if (!transitData) {
      return transitLoading ? (
        <AshtakavargaProgressState
          title="Loading transit analysis"
          description="Personalized timing, favorable windows, and birth vs transit comparison…"
        />
      ) : (
        <div className="loading">
          <p>No transit data.</p>
        </div>
      );
    }

    const { recommendations, birth_transit_comparison } = transitData;

    return (
      <div className="transit-recommendations">
        <h3>Personalized Transit Analysis</h3>
        <div className="strength-indicator">
          <span className={`strength-badge ${recommendations.transit_strength}`}>
            {recommendations.transit_strength.toUpperCase()} PERIOD
          </span>
          {birth_transit_comparison?.summary && (
            <div className="transit-summary">
              <span className="change-indicator">
                Energy Redistribution: {birth_transit_comparison.summary.distribution_shift} bindus shifted 
                ({birth_transit_comparison.summary.distribution_percentage}% of total energy)
              </span>
            </div>
          )}
        </div>
        
        {recommendations.favorable_activities.length > 0 && (
          <div className="favorable-section">
            <h4 style={{color: '#4caf50'}}>✓ Favorable Activities</h4>
            <ul>
              {recommendations.favorable_activities.map((activity, index) => (
                <li key={index}>{activity}</li>
              ))}
            </ul>
          </div>
        )}
        
        {recommendations.avoid_activities.length > 0 && (
          <div className="avoid-section">
            <h4 style={{color: '#f44336'}}>⚠ Activities to Avoid</h4>
            <ul>
              {recommendations.avoid_activities.map((activity, index) => (
                <li key={index}>{activity}</li>
              ))}
            </ul>
          </div>
        )}
        
        {recommendations.best_timing && recommendations.best_timing.length > 0 && (
          <div className="timing-section">
            <h4 style={{color: '#2196f3'}}>⏰ Best Timing</h4>
            <ul>
              {recommendations.best_timing.map((timing, index) => (
                <li key={index}>{timing}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

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
                  ? 'Regenerate Dots of Destiny?'
                  : 'Dots of Destiny reading'}
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
        <h2>Ashtakavarga Analysis - {chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart</h2>
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
          <button type="button" className="close-btn" onClick={onClose} aria-label={variant === 'page' ? 'Back' : 'Close'}>
            ×
          </button>
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
              {tab.label}
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
            {activeTab === 'sarva' && renderSarvashtakavarga()}
            {activeTab === 'individual' && renderIndividualCharts()}
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