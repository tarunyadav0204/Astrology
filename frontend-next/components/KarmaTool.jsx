'use client';

import { useCallback, useEffect, useState } from 'react';
import { authHeaders, getApiBase, loadBirthChart, loadStoredUser } from '@/lib/api';
import { karmaAppHref } from '@/lib/navigation';

function CreditModal({ onClose, onConfirm, credits, cost, title }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        <p>This will use {cost} credits</p>
        <p className="modal-balance">Your balance: {credits} credits</p>
        <div className="modal-buttons">
          <button type="button" className="modal-button" onClick={onClose}>
            Cancel
          </button>
          <button type="button" className="modal-button modal-button-primary" onClick={onConfirm}>
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}

function KarmaCard({ title, content, index }) {
  const [expanded, setExpanded] = useState(true);
  const icons = ['🕉️', '🌟', '🎯', '⚖️', '💎', '🔱', '👪', '🦋', '🙏', '⏳', '🕉️'];
  const isIntroduction = title === 'Introduction';

  const escapeHtml = (text) =>
    String(text || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');

  const formatContent = (text) =>
    escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');

  return (
    <div className={`karma-card ${isIntroduction ? 'karma-card-intro' : ''}`}>
      <div
        className="karma-card-header"
        onClick={() => setExpanded(!expanded)}
        onKeyDown={(e) => e.key === 'Enter' && setExpanded(!expanded)}
        role="button"
        tabIndex={0}
      >
        <div className={`karma-icon-circle ${isIntroduction ? 'intro-icon' : ''}`}>
          {icons[index % icons.length]}
        </div>
        <h3>{title}</h3>
        <span className="expand-icon">{expanded ? '▼' : '▶'}</span>
      </div>
      {expanded && (
        <div className="karma-card-content">
          <div className="content-divider" />
          <div dangerouslySetInnerHTML={{ __html: formatContent(content) }} />
        </div>
      )}
    </div>
  );
}

export default function KarmaTool() {
  const [user, setUser] = useState(null);
  const [birthData, setBirthData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [credits, setCredits] = useState(0);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [karmaCost, setKarmaCost] = useState(25);
  const [showStartModal, setShowStartModal] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showProgress, setShowProgress] = useState(false);
  const [progressTimer, setProgressTimer] = useState(null);

  const refreshSession = useCallback(() => {
    setUser(loadStoredUser());
    const { birthData: b, chartData: c } = loadBirthChart();
    setBirthData(b);
    setChartData(c);
  }, []);

  useEffect(() => {
    refreshSession();
    loadInitialData();
  }, [refreshSession]);

  const loadInitialData = async () => {
    try {
      const base = getApiBase();
      const headers = { ...authHeaders(), 'Content-Type': 'application/json' };
      let hasUserSpecificCost = false;
      if (headers.Authorization) {
        const res = await fetch(`${base}/api/credits/settings/my-pricing`, { headers });
        if (res.ok) {
          const data = await res.json();
          const cost = data?.pricing?.karma;
          if (cost != null) {
            setKarmaCost(Number(cost) || 25);
            hasUserSpecificCost = true;
          }
        }
      }
      if (!hasUserSpecificCost) {
        const costRes = await fetch(`${base}/api/credits/settings/karma-cost`);
        if (costRes.ok) {
          const data = await costRes.json();
          setKarmaCost(data.cost || 25);
        }
      }
      const balRes = await fetch(`${base}/api/credits/balance`, { headers });
      if (balRes.ok) {
        const data = await balRes.json();
        setCredits(data.balance ?? data.credits ?? 0);
      }
    } catch (err) {
      console.error('Error loading karma pricing:', err);
    }
  };

  const checkExistingAnalysis = async () => {
    const chartId = birthData?.chart_id || chartData?.id;
    if (!chartId || !localStorage.getItem('token')) return;

    try {
      setLoading(true);
      setError(null);
      const base = getApiBase();
      const res = await fetch(`${base}/api/karma-analysis/status?chart_id=${chartId}`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      if ((data.status === 'complete' || data.status === 'completed') && data.data) {
        setAnalysis(data.data);
      }
    } catch (err) {
      console.error('Error checking existing analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const chartId = birthData?.chart_id || chartData?.id;
    if (chartId && user) {
      setAnalysis(null);
      checkExistingAnalysis();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [birthData?.chart_id, chartData?.id, user]);

  const stopProgressBar = useCallback(() => {
    if (progressTimer) clearInterval(progressTimer);
    setProgressTimer(null);
    setShowProgress(false);
    setProgress(0);
  }, [progressTimer]);

  const startProgressBar = () => {
    if (progressTimer) clearInterval(progressTimer);
    setProgress(0);
    setShowProgress(true);
    const duration = 60000;
    const steps = 600;
    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep += 1;
      setProgress((currentStep / steps) * 100);
      if (currentStep >= steps) clearInterval(timer);
    }, duration / steps);
    setProgressTimer(timer);
  };

  const startPolling = (jobId) => {
    const base = getApiBase();
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${base}/api/karma-analysis/status/${jobId}`, { headers: authHeaders() });
        const data = await res.json();
        if ((data.status === 'complete' || data.status === 'completed') && data.data) {
          stopProgressBar();
          setAnalysis(data.data);
          setLoading(false);
          clearInterval(interval);
          loadInitialData();
        } else if (data.status === 'failed' || data.status === 'error') {
          stopProgressBar();
          setError(data.error || 'Analysis failed');
          setLoading(false);
          clearInterval(interval);
        }
      } catch (err) {
        stopProgressBar();
        setError(err.message);
        setLoading(false);
        clearInterval(interval);
      }
    }, 2000);
  };

  const initiateAnalysis = async (forceRegenerate = false) => {
    const chartId = birthData?.chart_id || chartData?.id;
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = karmaAppHref({ login: true, hash: 'karma-tool' });
      return;
    }
    if (!chartId) {
      setError('Chart not found. Please set up your birth chart on AstroRoshni.');
      setLoading(false);
      stopProgressBar();
      return;
    }

    try {
      const base = getApiBase();
      const res = await fetch(`${base}/api/karma-analysis/start`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ chart_id: String(chartId), force_regenerate: !!forceRegenerate }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to start analysis');
      if ((data.status === 'complete' || data.status === 'completed') && data.data) {
        stopProgressBar();
        setAnalysis(data.data);
        setLoading(false);
        loadInitialData();
      } else if (data.job_id) {
        startPolling(data.job_id);
      }
    } catch (err) {
      stopProgressBar();
      setError(err.message);
      setLoading(false);
    }
  };

  const handleStartAnalysis = () => {
    if (!localStorage.getItem('token')) {
      window.location.href = karmaAppHref({ login: true, hash: 'karma-tool' });
      return;
    }
    if (credits < karmaCost) {
      alert(`You need ${karmaCost} credits for karma analysis.`);
      return;
    }
    setShowStartModal(true);
  };

  const chartId = birthData?.chart_id || chartData?.id;
  const hasChart = !!(chartData && birthData);

  let inner;
  if (!hasChart) {
    inner = (
      <div className="karma-start">
        <div className="om-symbol-large">🕉️</div>
        <h2 className="karma-tool-h2">Start your chart-based report</h2>
        <p>
          Sign in on AstroRoshni and save your birth chart (date, time, place). Your chart is shared with the main app
          on this device.
        </p>
        <a href={karmaAppHref({ login: true, hash: 'karma-tool' })} className="start-button karma-link-button">
          Sign in & set up birth chart
        </a>
      </div>
    );
  } else if (loading) {
    inner = (
      <div className="karma-loading">
        <div className="cosmic-loader">
          <div className="om-symbol">🕉️</div>
        </div>
        <div className="spinner" />
        <h2>Accessing Akashic Records</h2>
        <p>{showProgress ? "Analyzing your soul's journey through time..." : 'This is taking longer than usual...'}</p>
        {showProgress && (
          <div className="progress-container">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <div className="progress-text">{Math.round(progress)}%</div>
          </div>
        )}
      </div>
    );
  } else if (error) {
    inner = (
      <div className="karma-error">
        <div className="error-icon">⚠️</div>
        <h2>Unable to Access Records</h2>
        <p>{error}</p>
        <button type="button" className="retry-button" onClick={() => { setError(null); checkExistingAnalysis(); }}>
          Try Again
        </button>
      </div>
    );
  } else if (!analysis) {
    inner = (
      <>
        <div className="karma-start">
          <div className="om-symbol-large">🕉️</div>
          <h2 className="karma-tool-h2">Ready for your report</h2>
          <p>Chart loaded for {birthData.name || 'selected native'}.</p>
          <button type="button" className="start-button" onClick={handleStartAnalysis}>
            Start Analysis ({karmaCost} credits)
          </button>
          <div className="credit-balance">Your balance: {credits} credits</div>
          <p className="karma-tool-hint">
            <a href={karmaAppHref({ hash: 'karma-tool' })}>Open chart picker in full app</a>
          </p>
        </div>
        {showStartModal && (
          <CreditModal
            onClose={() => setShowStartModal(false)}
            onConfirm={async () => {
              setShowStartModal(false);
              setLoading(true);
              startProgressBar();
              await initiateAnalysis(false);
            }}
            credits={credits}
            cost={karmaCost}
            title="Start Karma Analysis"
          />
        )}
      </>
    );
  } else {
    const sections = analysis.sections || {};
    inner = (
      <>
        <div className="karma-content" aria-live="polite">
          <div className="karma-title-section">
            <div className="om-header">🕉️</div>
            <h2 className="karma-tool-h2">Your past life karma report</h2>
            <p>Personalised from your birth chart</p>
          </div>
          {Object.entries(sections).map(([title, content], index) => (
            <KarmaCard key={title} title={title} content={content} index={index} />
          ))}
          <div className="karma-footer">
            <div className="footer-icon">✨</div>
            <div className="footer-text">Analyzed by AstroRoshni</div>
            <div className="footer-subtext">Artificial Intelligence</div>
          </div>
        </div>
        {showRegenerateModal && (
          <CreditModal
            onClose={() => setShowRegenerateModal(false)}
            onConfirm={async () => {
              setShowRegenerateModal(false);
              setAnalysis(null);
              setLoading(true);
              startProgressBar();
              await initiateAnalysis(true);
            }}
            credits={credits}
            cost={karmaCost}
            title="Regenerate Karma Analysis"
          />
        )}
      </>
    );
  }

  return (
    <section id="karma-tool" className="karma-tool-section" aria-labelledby="karma-tool-heading">
      <div className="karma-container karma-container--tool">
        <p className="karma-tool-app-banner">
          <a href={karmaAppHref({ hash: 'karma-tool' })} className="karma-tool-app-banner-link">
            Open in full app (main menu, sign-in, chart picker) →
          </a>
        </p>
        <div className="karma-header">
          <h2 id="karma-tool-heading" className="karma-tool-page-title">
            🕉️ Personalised karma report
          </h2>
          {hasChart && (
            <>
              <span className="native-chip">{birthData.name || 'Chart'}</span>
              {analysis && (
                <button
                  type="button"
                  className="regenerate-button"
                  onClick={() => {
                    if (credits < karmaCost) {
                      alert(`You need ${karmaCost} credits.`);
                      return;
                    }
                    setShowRegenerateModal(true);
                  }}
                  title="Regenerate"
                >
                  ↻
                </button>
              )}
            </>
          )}
        </div>
        {inner}
      </div>
    </section>
  );
}
