import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import NavigationHeader from '../Shared/NavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import NativeSelector from '../Shared/NativeSelector';
import CreditsModal from '../Credits/CreditsModal';
import SEOHead from '../SEO/SEOHead';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import { apiService } from '../../services/apiService';
import { generatePageSEO } from '../../config/seo.config';
import MonthlyEventAccordion, { monthLabel } from './MonthlyEventAccordion';
import './EventsTimelinePage.css';

const START_YEAR_FALLBACK = 1950;
const END_YEAR = 2100;

const LOADING_MESSAGES = [
  { icon: '🌟', text: 'Analyzing planetary positions...' },
  { icon: '🔮', text: 'Calculating dasha periods...' },
  { icon: '✨', text: 'Examining transit patterns...' },
  { icon: '🌙', text: 'Consulting the cosmic calendar...' },
  { icon: '⭐', text: 'Mapping celestial influences...' },
  { icon: '🪐', text: 'Decoding planetary alignments...' },
  { icon: '💫', text: 'Synthesizing astrological insights...' },
  { icon: '🎯', text: 'Identifying key life events...' },
  { icon: '✅', text: 'Finalizing your predictions...' }
];

function resolveBirthChartId(birthData, chartData) {
  if (birthData?.id != null) return Number(birthData.id);
  if (birthData?.chart_id != null) return Number(birthData.chart_id);
  if (chartData?.id != null) return Number(chartData.id);
  return null;
}

function extractBirthYear(data) {
  if (!data || typeof data !== 'object') return null;
  const candidates = [
    data.date,
    data.birth_date,
    data.dob,
    data.birthDate,
    data.birth_date_iso,
    data.birth_details?.date,
    data.birthDetails?.date,
  ];
  for (const raw of candidates) {
    if (!raw) continue;
    const s = String(raw).trim();
    let m = s.match(/^(\d{4})[-/.]/);
    if (!m) m = s.match(/\b(19\d{2}|20\d{2})\b/);
    if (!m) continue;
    const y = Number(m[1]);
    if (Number.isFinite(y) && y >= 1900 && y <= END_YEAR) return y;
  }
  return null;
}

export default function EventsTimelinePage({
  user: propUser,
  onLogout,
  onAdminClick,
  onLogin
}) {
  const navigate = useNavigate();
  const { birthData, chartData } = useAstrology();
  const { credits, fetchBalance, eventsCost } = useCredits();

  const [user, setUser] = useState(propUser);
  useEffect(() => {
    if (!propUser) {
      const token = localStorage.getItem('token');
      const saved = localStorage.getItem('user');
      if (token && saved) {
        try {
          setUser(JSON.parse(saved));
        } catch {
          setUser(null);
        }
      }
    } else {
      setUser(propUser);
    }
  }, [propUser]);

  const deviceNow = useMemo(() => new Date(), []);
  const deviceYear = deviceNow.getFullYear();
  const deviceMonth = deviceNow.getMonth() + 1;
  const deviceDay = deviceNow.getDate();
  const recommendedMonth = deviceDay <= 15 ? deviceMonth : Math.min(deviceMonth + 1, 12);

  const [readingMode, setReadingMode] = useState('yearly');
  const [selectedYear, setSelectedYear] = useState(deviceYear);
  const [selectedMonth, setSelectedMonth] = useState(recommendedMonth);

  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [timelineData, setTimelineData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMsgIndex, setLoadingMsgIndex] = useState(0);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [streamProgress, setStreamProgress] = useState({ monthsReady: 0, totalMonths: 12, quarterLabel: '' });

  const [showBirthModal, setShowBirthModal] = useState(false);
  const [showCreditModal, setShowCreditModal] = useState(false);
  const [showCreditsPurchaseModal, setShowCreditsPurchaseModal] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);
  const [cachedYears, setCachedYears] = useState([]);
  const [cachedMonths, setCachedMonths] = useState([]);

  const loadingIntervalRef = useRef(null);
  const progressIntervalRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const pollTimeoutRef = useRef(null);
  const jobRunningRef = useRef(false);
  const timelineStreamAbortRef = useRef(null);
  const yearlyStripRef = useRef(null);
  const compactStripRef = useRef(null);
  const autoScrolledYearRef = useRef(false);

  const seoData = useMemo(
    () => generatePageSEO('lifeEvents', { path: '/life-events' }),
    []
  );

  const birthChartId = resolveBirthChartId(birthData, chartData);
  const hasBirthCore = Boolean(
    birthData?.name &&
      birthData?.date &&
      birthData?.time &&
      birthData?.latitude != null &&
      birthData?.longitude != null
  );

  const startYear = useMemo(() => extractBirthYear(birthData) ?? START_YEAR_FALLBACK, [birthData]);

  const years = useMemo(
    () => Array.from({ length: Math.max(1, END_YEAR - startYear + 1) }, (_, i) => startYear + i),
    [startYear]
  );
  const cachedYearSet = useMemo(() => new Set((cachedYears || []).map((y) => Number(y))), [cachedYears]);
  const cachedMonthSet = useMemo(() => new Set((cachedMonths || []).map((m) => Number(m))), [cachedMonths]);

  useEffect(() => {
    if (selectedYear < startYear) {
      setSelectedYear(startYear);
    }
  }, [selectedYear, startYear]);

  useEffect(() => {
    if (autoScrolledYearRef.current) return;

    const targetYear = years.includes(deviceYear) ? deviceYear : selectedYear;
    if (!Number.isFinite(targetYear)) return;

    const stripEl =
      readingMode === 'yearly' ? yearlyStripRef.current : compactStripRef.current;
    if (!stripEl) return;

    const chipEl = stripEl.querySelector(`[data-year="${targetYear}"]`);
    if (!chipEl) return;

    chipEl.scrollIntoView({ behavior: 'auto', inline: 'center', block: 'nearest' });
    autoScrolledYearRef.current = true;
  }, [readingMode, years, deviceYear, selectedYear]);

  useEffect(() => {
    let cancelled = false;
    const loadCachedYears = async () => {
      if (!birthChartId) {
        if (!cancelled) setCachedYears([]);
        return;
      }
      try {
        const res = await apiService.getCachedEventTimelineYears(birthChartId);
        if (!cancelled) {
          setCachedYears(Array.isArray(res?.years) ? res.years : []);
        }
      } catch {
        if (!cancelled) setCachedYears([]);
      }
    };
    loadCachedYears();
    return () => {
      cancelled = true;
    };
  }, [birthChartId]);

  useEffect(() => {
    let cancelled = false;
    const loadCachedMonths = async () => {
      if (!birthData || !birthChartId || !selectedYear) {
        if (!cancelled) setCachedMonths([]);
        return;
      }
      try {
        const dateStr = String(birthData.date).split('T')[0];
        const timeStr = String(birthData.time).includes('T')
          ? String(birthData.time).split('T')[1]?.slice(0, 5) || '12:00'
          : String(birthData.time || '12:00').slice(0, 5);
        const basePayload = {
          name: birthData.name,
          date: dateStr,
          time: timeStr,
          place: birthData.place || '',
          latitude: parseFloat(birthData.latitude),
          longitude: parseFloat(birthData.longitude),
          timezone: birthData.timezone || 'UTC+0',
          gender: birthData.gender || '',
          birth_chart_id: birthChartId,
          selectedYear,
        };
        const checks = await Promise.all(
          Array.from({ length: 12 }, (_, i) => i + 1).map(async (m) => {
            try {
              const res = await apiService.getCachedEventTimeline({ ...basePayload, selectedMonth: m });
              return res?.cached ? m : null;
            } catch {
              return null;
            }
          })
        );
        if (!cancelled) {
          setCachedMonths(checks.filter((m) => Number.isFinite(m)));
        }
      } catch {
        if (!cancelled) setCachedMonths([]);
      }
    };
    loadCachedMonths();
    return () => {
      cancelled = true;
    };
  }, [birthData, birthChartId, selectedYear]);

  const buildPayload = useCallback(() => {
    if (!birthData || !birthChartId) return null;
    const dateStr = String(birthData.date).split('T')[0];
    const timeStr = String(birthData.time).includes('T')
      ? String(birthData.time).split('T')[1]?.slice(0, 5) || '12:00'
      : String(birthData.time || '12:00').slice(0, 5);

    return {
      name: birthData.name,
      date: dateStr,
      time: timeStr,
      place: birthData.place || '',
      latitude: parseFloat(birthData.latitude),
      longitude: parseFloat(birthData.longitude),
      timezone: birthData.timezone || 'UTC+0',
      gender: birthData.gender || '',
      birth_chart_id: birthChartId,
      selectedYear,
      ...(readingMode === 'monthly' ? { selectedMonth } : {})
    };
  }, [birthData, birthChartId, selectedYear, readingMode, selectedMonth]);

  const clearTimers = useCallback(() => {
    if (loadingIntervalRef.current) {
      clearInterval(loadingIntervalRef.current);
      loadingIntervalRef.current = null;
    }
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    if (pollTimeoutRef.current) {
      clearTimeout(pollTimeoutRef.current);
      pollTimeoutRef.current = null;
    }
    if (timelineStreamAbortRef.current) {
      timelineStreamAbortRef.current.abort();
      timelineStreamAbortRef.current = null;
    }
  }, []);

  /** Normalize status API payload — backend uses `data`; guard if the timeline is ever returned at the top level */
  const extractTimelinePayload = useCallback((statusResponse) => {
    if (!statusResponse || typeof statusResponse !== 'object') return null;
    if (statusResponse.data != null) return statusResponse.data;
    if (Array.isArray(statusResponse.monthly_predictions) || Array.isArray(statusResponse.macro_trends)) {
      return statusResponse;
    }
    return null;
  }, []);

  const runTimelineJob = useCallback(async () => {
    const payload = buildPayload();
    if (!payload) return;

    // Keep UI in "analysis" state throughout async streaming/polling retries.
    setAnalysisStarted(true);
    jobRunningRef.current = true;
    setLoading(true);
    setTimelineData(null);
    setStreamProgress({ monthsReady: 0, totalMonths: 12, quarterLabel: '' });
    setLoadingMsgIndex(0);
    setLoadingProgress(0);

    loadingIntervalRef.current = setInterval(() => {
      setLoadingMsgIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 3000);

    let elapsed = 0;
    progressIntervalRef.current = setInterval(() => {
      elapsed += 100;
      if (elapsed <= 100000) {
        setLoadingProgress((elapsed / 100000) * 90);
      } else {
        setLoadingProgress(-1);
      }
    }, 100);

    const finishLoading = () => {
      setLoading(false);
      jobRunningRef.current = false;
    };

    const onCompleted = async (statusResponse) => {
      clearTimers();
      const timelinePayload = extractTimelinePayload(statusResponse);
      setTimelineData(timelinePayload);
        setStreamProgress({ monthsReady: 12, totalMonths: 12, quarterLabel: 'Done' });
      try {
        await fetchBalance();
      } catch {
        /* balance refresh is best-effort */
      } finally {
        finishLoading();
      }
    };

    const onFailed = (message) => {
      clearTimers();
      finishLoading();
      toast.error(message || 'Analysis failed');
    };

    try {
      const startResponse = await apiService.startEventTimeline(payload);

      if (startResponse?.data && !startResponse?.job_id) {
        setTimelineData(startResponse.data);
        try {
          await fetchBalance();
        } catch {
          /* ignore */
        } finally {
          finishLoading();
        }
        return;
      }

      const jobId = startResponse?.job_id;
      if (!jobId) {
        throw new Error('No job id returned from server.');
      }

      const streamController = new AbortController();
      timelineStreamAbortRef.current = streamController;
      let streamDeliveredTerminal = false;
      apiService
        .streamEventTimeline(
          jobId,
          async (eventName, payload) => {
            if (!jobRunningRef.current) return;
            if (payload?.partial_data) {
              const partial = payload.partial_data;
              setTimelineData((prev) => ({
                ...(prev || {}),
                macro_trends: partial.macro_trends || [],
                monthly_predictions: partial.monthly_predictions || [],
              }));
              const completedQ = Number(payload.completed_quarters || partial.completed_quarters || 0);
              const totalQ = Number(payload.total_quarters || partial.total_quarters || 4);
              const monthsReady = Number(payload.months_ready || partial.months_ready || (partial.monthly_predictions || []).length || 0);
              setStreamProgress({
                monthsReady,
                totalMonths: 12,
                quarterLabel: completedQ > 0 ? `Q${Math.min(completedQ, totalQ)} ready` : '',
              });
            }
            if (eventName === 'completed') {
              streamDeliveredTerminal = true;
              await onCompleted(payload);
            } else if (eventName === 'failed') {
              streamDeliveredTerminal = true;
              onFailed(payload?.error || 'Analysis failed');
            }
          },
          streamController.signal
        )
        .catch(() => {
          // Polling remains active as fallback when stream is unavailable.
        })
        .finally(() => {
          timelineStreamAbortRef.current = null;
          if (!streamDeliveredTerminal && jobRunningRef.current) {
            // fallback polling will continue
          }
        });

      const pollOnce = async () => {
        const statusResponse = await apiService.getEventTimelineStatus(jobId);
        const status = String(statusResponse?.status ?? '').toLowerCase();

        if (status === 'completed') {
          await onCompleted(statusResponse);
          return true;
        }
        if (status === 'failed') {
          onFailed(statusResponse?.error || 'Analysis failed');
          return true;
        }
        return false;
      };

      try {
        await pollOnce();
        if (!jobRunningRef.current) {
          return;
        }
      } catch (e) {
        // Non-fatal: stream may still be alive, and next poll can succeed.
        console.warn('Initial timeline poll failed (will retry):', e?.message || e);
      }

      pollIntervalRef.current = setInterval(async () => {
        try {
          const done = await pollOnce();
          if (done && pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        } catch (e) {
          // Keep trying; transient network/proxy hiccups should not kick user back to setup page.
          console.warn('Timeline poll tick failed (continuing):', e?.message || e);
        }
      }, 3000);

      pollTimeoutRef.current = setTimeout(() => {
        if (jobRunningRef.current) {
          clearTimers();
          finishLoading();
          toast.error('Analysis is taking longer than expected. Please try again.');
        }
      }, 300000);
    } catch (err) {
      clearTimers();
      finishLoading();
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        'Failed to load timeline. Please try again.';
      if (err?.response?.status === 401) {
        toast.error('Session expired. Please sign in again.');
      } else if (err?.response?.status === 402) {
        toast.error('Insufficient credits for this analysis. Add credits to continue.');
        setShowCreditsPurchaseModal(true);
      } else if (err?.response?.status === 404) {
        toast.error('Birth chart not found. Re-select your chart from the dashboard.');
      } else {
        toast.error(typeof msg === 'string' ? msg : 'Request failed');
      }
      setAnalysisStarted(false);
    }
  }, [buildPayload, clearTimers, extractTimelinePayload, fetchBalance, navigate]);

  useEffect(() => {
    return () => {
      clearTimers();
    };
  }, [clearTimers]);

  const fetchFreshCredits = async () => {
    const token = localStorage.getItem('token');
    if (!token) return 0;
    const res = await fetch('/api/credits/balance', {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) return 0;
    const data = await res.json();
    return data.credits ?? 0;
  };

  const handleContinue = async () => {
    const token = localStorage.getItem('token');
    if (!token || !user) {
      onLogin?.();
      toast.info('Please sign in to generate your life-events timeline.');
      return;
    }
    if (!hasBirthCore) {
      setShowBirthModal(true);
      return;
    }
    if (!birthChartId) {
      toast.error(
        'This feature needs a saved birth chart. Open “Change Native” and choose a saved profile from your account.'
      );
      setShowBirthModal(true);
      return;
    }

    try {
      const cacheResponse = await apiService.getCachedEventTimeline(buildPayload());
      if (cacheResponse?.cached && cacheResponse?.data) {
        setTimelineData(cacheResponse.data);
        setAnalysisStarted(true);
        fetchBalance();
        return;
      }

      await fetchBalance();
      const bal = await fetchFreshCredits();
      if (bal < eventsCost) {
        toast.error(`You need ${eventsCost} credits. You have ${bal}.`);
        setShowCreditsPurchaseModal(true);
        return;
      }
      setPendingAction('generate');
      setShowCreditModal(true);
    } catch (e) {
      console.error(e);
      toast.error('Could not check for saved predictions. Try again.');
    }
  };

  const handleCreditConfirm = () => {
    setShowCreditModal(false);
    if (pendingAction === 'generate') {
      setAnalysisStarted(true);
      runTimelineJob();
    } else if (pendingAction === 'regenerate') {
      runTimelineJob();
    }
    setPendingAction(null);
  };

  const handleRegenerate = async () => {
    setShowRegenerateModal(false);
    await fetchBalance();
    const bal = await fetchFreshCredits();
    if (bal < eventsCost) {
      toast.error(`You need ${eventsCost} credits to regenerate. You have ${bal}.`);
      setShowCreditsPurchaseModal(true);
      return;
    }
    setPendingAction('regenerate');
    setShowCreditModal(true);
  };

  const handleYearChange = (y) => {
    setSelectedYear(y);
    setTimelineData(null);
  };

  const handleBack = () => {
    if (analysisStarted) {
      setAnalysisStarted(false);
      setTimelineData(null);
      clearTimers();
      setLoading(false);
    } else {
      navigate(-1);
    }
  };

  const openCredits = () => setShowCreditsPurchaseModal(true);

  const yearLabel = String(selectedYear);
  const monthlyPredictions = timelineData?.monthly_predictions || [];
  const macroTrends = (timelineData?.macro_trends || []).filter((trend) => {
    const t = String(trend || '').replace(/\s+/g, ' ').trim();
    if (!t) return false;
    const wc = t.split(' ').filter(Boolean).length;
    return wc > 3 && t.length >= 28;
  });

  const diveDeepForMonth = (data) => {
    if (!data?.month_id) return;
    setReadingMode('monthly');
    setSelectedMonth(data.month_id);
    setSelectedYear(selectedYear);
    setAnalysisStarted(false);
    setTimelineData(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="events-timeline-page">
      <SEOHead
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={{
          '@context': 'https://schema.org',
          '@type': 'WebPage',
          name: 'Life events timeline',
          description: seoData.description
        }}
      />

      <NavigationHeader
        compact
        showZodiacSelector={false}
        user={user}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
        onLogin={onLogin}
        showLoginButton={!user}
        onCreditsClick={openCredits}
        birthData={birthData}
        onChangeNative={() => setShowBirthModal(true)}
        onHomeClick={() => navigate('/')}
      />

      <div className="events-timeline__shell">
        <header className="events-timeline__hero">
          <button type="button" className="events-timeline__back" onClick={handleBack}>
            ← Back
          </button>
          <div className="events-timeline__hero-text">
            <p className="events-timeline__kicker">What will manifest</p>
            <h1 className="events-timeline__title">
              {analysisStarted
                ? readingMode === 'monthly'
                  ? `Deep dive · ${monthLabel(selectedMonth)} ${yearLabel}`
                  : `Your year · ${yearLabel}`
                : 'Major life events'}
            </h1>
            <p className="events-timeline__subtitle">
              {analysisStarted
                ? 'Personalized timeline from your saved chart—review the yearly vibe, then open any month.'
                : 'Choose a full-year overview with twelve monthly chapters, or one intensive month.'}
            </p>
          </div>
          {analysisStarted && timelineData && !loading && (
            <div className="events-timeline__hero-actions">
              <button
                type="button"
                className="events-timeline__icon-btn"
                onClick={() => setShowRegenerateModal(true)}
                title="Regenerate"
              >
                ↻
              </button>
            </div>
          )}
        </header>

        {!hasBirthCore ? (
          <section className="events-timeline__card events-timeline__card--center">
            <h2>Add birth details</h2>
            <p>We need your chart to compute dasha and transits for this timeline.</p>
            <button type="button" className="events-timeline__cta" onClick={() => setShowBirthModal(true)}>
              Enter birth details
            </button>
          </section>
        ) : analysisStarted || loading || timelineData ? (
          <div className="events-timeline__results">
            {hasBirthCore && (
              <div className="events-timeline__native-row events-timeline__native-row--compact">
                <NativeSelector birthData={birthData} onNativeChange={() => setShowBirthModal(true)} />
              </div>
            )}

            {loading && (
              <section className="events-timeline__loading">
                <div className="events-timeline__loading-inner">
                  <div className="events-timeline__spinner" aria-hidden />
                  <p className="events-timeline__loading-icon">{LOADING_MESSAGES[loadingMsgIndex].icon}</p>
                  <p className="events-timeline__loading-text">{LOADING_MESSAGES[loadingMsgIndex].text}</p>
                  {streamProgress.monthsReady > 0 && (
                    <p className="events-timeline__loading-text">
                      {streamProgress.monthsReady}/12 months ready
                      {streamProgress.quarterLabel ? ` · ${streamProgress.quarterLabel}` : ''}
                    </p>
                  )}
                  {loadingProgress >= 0 ? (
                    <div className="events-timeline__progress">
                      <div className="events-timeline__progress-track">
                        <div
                          className="events-timeline__progress-fill"
                          style={{ width: `${Math.min(loadingProgress, 90)}%` }}
                        />
                      </div>
                      <span className="events-timeline__progress-label">
                        {loadingProgress < 85 ? `${Math.round(loadingProgress)}%` : 'Almost there…'}
                      </span>
                    </div>
                  ) : (
                    <p className="events-timeline__slow">Taking longer than usual…</p>
                  )}
                </div>
              </section>
            )}
            {!loading && (
              <>
                {macroTrends.length > 0 && (
                  <section className="events-timeline__macro">
                    <h2 className="events-timeline__section-title">
                      {readingMode === 'monthly' ? `Themes · ${monthLabel(selectedMonth)} ${yearLabel}` : `The vibe of ${yearLabel}`}
                    </h2>
                    <ul className="events-timeline__macro-list">
                      {macroTrends.map((t, i) => (
                        <li key={i}>{t}</li>
                      ))}
                    </ul>
                  </section>
                )}

                {monthlyPredictions.length > 0 ? (
                  <section className="events-timeline__months">
                    <h2 className="events-timeline__section-title">
                      {readingMode === 'monthly' ? 'Month deep dive' : 'Monthly guide'}
                    </h2>
                    <div className="events-timeline__accordion-list">
                      {monthlyPredictions.map((month, index) => (
                        <MonthlyEventAccordion
                          key={`${month.month_id || index}-${index}`}
                          data={{
                            ...month,
                            month: month.month || monthLabel(month.month_id)
                          }}
                          yearLabel={yearLabel}
                          onDiveDeep={readingMode === 'yearly' ? diveDeepForMonth : null}
                        />
                      ))}
                    </div>
                  </section>
                ) : timelineData ? (
                  <p className="events-timeline__empty">No predictions in this response. Try regenerating.</p>
                ) : null}

                <div className="events-timeline__footer-actions">
                  <button type="button" className="events-timeline__secondary" onClick={() => navigate('/chat')}>
                    Open Tara chat
                  </button>
                  <button
                    type="button"
                    className="events-timeline__secondary"
                    onClick={() => {
                      setAnalysisStarted(false);
                      setTimelineData(null);
                      setLoading(false);
                    }}
                  >
                    New reading
                  </button>
                </div>
              </>
            )}
            {loading && monthlyPredictions.length > 0 && (
              <section className="events-timeline__months">
                <h2 className="events-timeline__section-title">Monthly guide (streaming)</h2>
                <div className="events-timeline__accordion-list">
                  {monthlyPredictions.map((month, index) => (
                    <MonthlyEventAccordion
                      key={`${month.month_id || index}-${index}`}
                      data={{
                        ...month,
                        month: month.month || monthLabel(month.month_id)
                      }}
                      yearLabel={yearLabel}
                      onDiveDeep={null}
                    />
                  ))}
                </div>
              </section>
            )}
          </div>
        ) : !birthChartId ? (
          <section className="events-timeline__card events-timeline__card--center">
            <h2>Saved chart required</h2>
            <p>
              Connect a profile that is stored in your account (not just typed once). Use Change Native and pick a saved
              chart, or save your chart from the dashboard.
            </p>
            <button type="button" className="events-timeline__cta" onClick={() => setShowBirthModal(true)}>
              Choose saved chart
            </button>
          </section>
        ) : (
          <section className="events-timeline__setup">
            <div className="events-timeline__native-row">
              <NativeSelector birthData={birthData} onNativeChange={() => setShowBirthModal(true)} />
            </div>

            <div className="events-timeline__mode-toggle" role="tablist" aria-label="Reading mode">
              <button
                type="button"
                role="tab"
                aria-selected={readingMode === 'yearly'}
                className={`events-timeline__mode-btn ${readingMode === 'yearly' ? 'is-active' : ''}`}
                onClick={() => setReadingMode('yearly')}
              >
                <span className="events-timeline__mode-title">Whole year</span>
                <span className="events-timeline__mode-desc">Twelve monthly chapters</span>
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={readingMode === 'monthly'}
                className={`events-timeline__mode-btn ${readingMode === 'monthly' ? 'is-active' : ''}`}
                onClick={() => setReadingMode('monthly')}
              >
                <span className="events-timeline__mode-title">One month</span>
                <span className="events-timeline__mode-desc">Deep detail & scenarios</span>
              </button>
            </div>

            <p className="events-timeline__hint">
              {readingMode === 'yearly'
                ? 'You’ll get the year’s overall themes plus twelve expandable months.'
                : `Pick a month in ${selectedYear} for an exhaustive single-month analysis.`}
            </p>

            {readingMode === 'yearly' ? (
              <>
                <div className="events-timeline__strip-wrap">
                  <div className="events-timeline__strip-label">Year</div>
                  <div ref={yearlyStripRef} className="events-timeline__year-strip" role="list">
                    {years.map((y) => (
                      <button
                        key={y}
                        type="button"
                        role="listitem"
                        data-year={y}
                        className={`events-timeline__chip ${selectedYear === y ? 'is-selected' : ''} ${cachedYearSet.has(Number(y)) ? 'is-cached' : ''}`}
                        onClick={() => handleYearChange(y)}
                      >
                        {y}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="events-timeline__quick">
                  <button type="button" className="events-timeline__quick-btn" onClick={() => handleYearChange(deviceYear)}>
                    This year
                  </button>
                  <button
                    type="button"
                    className="events-timeline__quick-btn"
                    onClick={() => handleYearChange(deviceYear + 1)}
                  >
                    Next year
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="events-timeline__strip-wrap">
                  <div className="events-timeline__strip-label">Year</div>
                  <div
                    ref={compactStripRef}
                    className="events-timeline__year-strip"
                    role="list"
                  >
                    {years.map((y) => (
                      <button
                        key={y}
                        type="button"
                        data-year={y}
                        className={`events-timeline__chip ${selectedYear === y ? 'is-selected' : ''} ${cachedYearSet.has(Number(y)) ? 'is-cached' : ''}`}
                        onClick={() => handleYearChange(y)}
                      >
                        {y}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="events-timeline__strip-wrap">
                  <div className="events-timeline__strip-label">Month</div>
                  <div className="events-timeline__month-strip" role="list">
                    {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                      <button
                        key={m}
                        type="button"
                        className={`events-timeline__chip events-timeline__chip--month ${
                          cachedMonthSet.has(Number(m)) ? 'is-cached' : ''
                        } ${
                          selectedMonth === m ? 'is-selected' : ''
                        }`}
                        onClick={() => setSelectedMonth(m)}
                      >
                        {monthLabel(m)}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            <div className="events-timeline__features">
              <h3 className="events-timeline__features-title">What’s included</h3>
              <ul className="events-timeline__features-list">
                <li>✓ {readingMode === 'yearly' ? 'Twelve monthly forecasts' : 'One month deep dive'}</li>
                <li>✓ Major life events & timing hints</li>
                <li>✓ Classic Vedic methods: Parashari, Nadi, Jaimini</li>
                <li>✓ Continue the conversation in Tara chat</li>
              </ul>
            </div>

            <div className="events-timeline__cost-row">
              <span className="events-timeline__cost-pill">{eventsCost} credits</span>
              {user && <span className="events-timeline__balance">Your balance: {credits}</span>}
            </div>

            <button type="button" className="events-timeline__cta events-timeline__cta--wide" onClick={handleContinue}>
              {readingMode === 'yearly' ? 'Continue' : `Generate ${monthLabel(selectedMonth)} ${selectedYear}`}
            </button>
          </section>
        )}
      </div>

      {showCreditModal && (
        <div className="events-timeline-modal-overlay" role="presentation" onClick={() => setShowCreditModal(false)}>
          <div
            className="events-timeline-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="evt-credit-title"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 id="evt-credit-title">Confirm credits</h3>
            <p>
              This uses <strong>{eventsCost}</strong> credits for{' '}
              {readingMode === 'monthly'
                ? `the deep dive for ${monthLabel(selectedMonth)} ${selectedYear}`
                : `your ${selectedYear} timeline`}
              .
            </p>
            <p className="events-timeline-modal__balance">Your balance: {credits} credits</p>
            <div className="events-timeline-modal__actions">
              <button type="button" className="events-timeline-modal__btn" onClick={() => setShowCreditModal(false)}>
                Cancel
              </button>
              <button type="button" className="events-timeline-modal__btn events-timeline-modal__btn--primary" onClick={handleCreditConfirm}>
                Continue
              </button>
            </div>
          </div>
        </div>
      )}

      {showRegenerateModal && (
        <div className="events-timeline-modal-overlay" role="presentation" onClick={() => setShowRegenerateModal(false)}>
          <div
            className="events-timeline-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="evt-regen-title"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 id="evt-regen-title">Regenerate predictions?</h3>
            <p>
              A fresh run will charge <strong>{eventsCost}</strong> credits again for {selectedYear}
              {readingMode === 'monthly' ? ` · ${monthLabel(selectedMonth)}` : ''}.
            </p>
            <div className="events-timeline-modal__actions">
              <button type="button" className="events-timeline-modal__btn" onClick={() => setShowRegenerateModal(false)}>
                Cancel
              </button>
              <button type="button" className="events-timeline-modal__btn events-timeline-modal__btn--primary" onClick={handleRegenerate}>
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}

      <BirthFormModal
        isOpen={showBirthModal}
        onClose={() => setShowBirthModal(false)}
        onSubmit={() => setShowBirthModal(false)}
        title="Birth details"
        description="Select a saved chart or enter details to save a profile."
      />

      <CreditsModal
        isOpen={showCreditsPurchaseModal}
        onClose={() => setShowCreditsPurchaseModal(false)}
        onLogin={onLogin}
      />
    </div>
  );
}
