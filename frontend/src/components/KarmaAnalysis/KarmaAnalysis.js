import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useCredits } from '../../context/CreditContext';
import { useAstrology } from '../../context/AstrologyContext';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import SEOHead from '../SEO/SEOHead';
import { generatePageSEO } from '../../config/seo.config';
import { buildKarmaStructuredData } from './karmaSeoContent';
import KarmaAnalysisLanding from './KarmaAnalysisLanding';
import './KarmaAnalysis.css';

const KarmaAnalysis = ({
  user: propUser,
  onLogin,
  onLogout,
  onAdminClick,
}) => {
  const { credits, refreshBalance } = useCredits();
  const { chartData, birthData } = useAstrology();
  const [user, setUser] = useState(propUser ?? null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [karmaCost, setKarmaCost] = useState(25);
  const [showStartModal, setShowStartModal] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [showBirthFormModal, setShowBirthFormModal] = useState(false);
  const [birthFormDefaultTab, setBirthFormDefaultTab] = useState('saved');
  const [progress, setProgress] = useState(0);
  const [showProgress, setShowProgress] = useState(false);
  const [progressTimer, setProgressTimer] = useState(null);

  const seoData = generatePageSEO('karmaAnalysis', { path: '/karma-analysis' });

  useEffect(() => {
    setUser(propUser ?? null);
  }, [propUser]);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('login') === '1' && onLogin) {
      onLogin();
    }
    if (window.location.hash === '#karma-tool') {
      requestAnimationFrame(() => {
        document.getElementById('karma-tool')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
  }, [onLogin]);

  useEffect(() => {
    const chartId = birthData?.chart_id || chartData?.id;
    if (chartId) {
      setAnalysis(null);
      setShowBirthFormModal(false);
      checkExistingAnalysis();
    }
  }, [birthData?.chart_id, chartData?.id]);

  const handleGetStarted = useCallback(() => {
    document.getElementById('karma-tool')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const token = localStorage.getItem('token');
    if (!token && onLogin) {
      onLogin();
      return;
    }
    if (!chartData || !birthData) {
      setBirthFormDefaultTab('saved');
      setShowBirthFormModal(true);
    }
  }, [chartData, birthData, onLogin]);

  const loadInitialData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const res = await axios.get('/api/credits/settings/my-pricing', {
            headers: { Authorization: `Bearer ${token}` },
          });
          const cost = res.data?.pricing?.karma;
          if (cost != null) {
            setKarmaCost(Number(cost) || 25);
            return;
          }
        } catch (_) {
          /* use public default */
        }
      }
      const costResponse = await axios.get('/api/credits/settings/karma-cost');
      setKarmaCost(costResponse.data.cost || 25);
    } catch (err) {
      console.error('Error loading initial data:', err);
    }
  };

  const checkExistingAnalysis = async () => {
    const chartId = birthData?.chart_id || chartData?.id;
    if (!chartId) {
      setError(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get(`/api/karma-analysis/status?chart_id=${chartId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (
        (response.data.status === 'complete' || response.data.status === 'completed') &&
        response.data.data
      ) {
        setAnalysis(response.data.data);
      }
    } catch (err) {
      console.error('Error checking existing analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartAnalysis = () => {
    const token = localStorage.getItem('token');
    if (!token && onLogin) {
      onLogin();
      return;
    }
    if (credits < karmaCost) {
      alert(`You need ${karmaCost} credits for karma analysis.`);
      return;
    }
    setShowStartModal(true);
  };

  const confirmStartAnalysis = async () => {
    setShowStartModal(false);
    setLoading(true);
    startProgressBar();
    await initiateAnalysis(false);
  };

  const handleRegenerate = () => {
    if (credits < karmaCost) {
      alert(`You need ${karmaCost} credits for karma analysis.`);
      return;
    }
    setShowRegenerateModal(true);
  };

  const confirmRegenerate = async () => {
    setShowRegenerateModal(false);
    setAnalysis(null);
    setLoading(true);
    startProgressBar();
    await initiateAnalysis(true);
  };

  const initiateAnalysis = async (forceRegenerate = false) => {
    const chartId = birthData?.chart_id || chartData?.id;
    const token = localStorage.getItem('token');

    if (!token && onLogin) {
      onLogin();
      setLoading(false);
      stopProgressBar();
      return;
    }

    if (!chartId) {
      setError('Chart not found. Please select a birth chart.');
      setLoading(false);
      stopProgressBar();
      return;
    }

    try {
      const response = await axios.post(
        '/api/karma-analysis/start',
        { chart_id: String(chartId), force_regenerate: !!forceRegenerate },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (
        (response.data.status === 'complete' || response.data.status === 'completed') &&
        response.data.data
      ) {
        stopProgressBar();
        setAnalysis(response.data.data);
        setLoading(false);
        refreshBalance();
      } else if (response.data.job_id) {
        startPolling(response.data.job_id);
      }
    } catch (err) {
      stopProgressBar();
      setError(err.response?.data?.detail || 'Failed to initiate analysis');
      setLoading(false);
    }
  };

  const startProgressBar = () => {
    if (progressTimer) {
      clearInterval(progressTimer);
    }

    setProgress(0);
    setShowProgress(true);
    const duration = 60000;
    const steps = 600;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep += 1;
      setProgress((currentStep / steps) * 100);
      if (currentStep >= steps) {
        clearInterval(timer);
      }
    }, duration / steps);

    setProgressTimer(timer);
  };

  const stopProgressBar = () => {
    if (progressTimer) {
      clearInterval(progressTimer);
      setProgressTimer(null);
    }
    setShowProgress(false);
    setProgress(0);
  };

  const startPolling = (jobId) => {
    const interval = setInterval(async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`/api/karma-analysis/status/${jobId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (
          (response.data.status === 'complete' || response.data.status === 'completed') &&
          response.data.data
        ) {
          stopProgressBar();
          setAnalysis(response.data.data);
          setLoading(false);
          clearInterval(interval);
          refreshBalance();
        } else if (response.data.status === 'failed' || response.data.status === 'error') {
          stopProgressBar();
          setError(response.data.error);
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

  const handleFormSubmit = () => {
    setShowBirthFormModal(false);
  };

  const renderToolInner = () => {
    if (!chartData || !birthData) {
      return (
        <div className="karma-start">
          <div className="karma-orbit-mark" aria-hidden="true"><span>ॐ</span></div>
          <p className="karma-state-label">Chart required</p>
          <h2 className="karma-tool-h2">Start your chart-based report</h2>
          <p>Sign in and enter birth details (date, time, place) to generate your personalised karma analysis.</p>
          <button type="button" className="start-button" onClick={handleGetStarted}>
            {user ? 'Enter birth details' : 'Sign in & enter birth details'}
          </button>
        </div>
      );
    }

    if (loading) {
      return (
        <div className="karma-loading">
          <div className="karma-loading-orbit" aria-hidden="true"><span>कर्म</span></div>
          <p className="karma-state-label">Calculation in progress</p>
          <h2>Reading your karmic pattern</h2>
          <p>{showProgress ? 'Synthesizing chart layers, nodes, houses, and timing…' : 'This is taking longer than usual…'}</p>
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
    }

    if (error) {
      return (
        <div className="karma-error">
          <span className="karma-error-code" aria-hidden="true">!</span>
          <p className="karma-state-label">Reading interrupted</p>
          <h2>We could not complete the analysis</h2>
          <p>{error}</p>
          <button type="button" className="retry-button" onClick={() => { setError(null); checkExistingAnalysis(); }}>
            Try Again
          </button>
        </div>
      );
    }

    if (!analysis) {
      return (
        <>
          <div className="karma-start">
            <div className="karma-orbit-mark" aria-hidden="true"><span>ॐ</span></div>
            <p className="karma-state-label">Chart ready</p>
            <h2 className="karma-tool-h2">Ready for your report</h2>
            <p>Chart loaded for {birthData.name || 'selected native'}. Run the analysis when you are ready.</p>
            <button type="button" className="start-button" onClick={handleStartAnalysis}>
              Start Analysis ({karmaCost} credits)
            </button>
            <div className="credit-balance">Your balance: {credits} credits</div>
          </div>
          {showStartModal && (
            <CreditModal
              onClose={() => setShowStartModal(false)}
              onConfirm={confirmStartAnalysis}
              credits={credits}
              cost={karmaCost}
              title="Start Karma Analysis"
            />
          )}
        </>
      );
    }

    const sections = analysis.sections || {};

    return (
      <>
        <div className="karma-content" aria-live="polite">
          <div className="karma-title-section">
            <p className="karma-state-label">Private · Chart-grounded</p>
            <h2 className="karma-tool-h2">Your past life karma report</h2>
            <p>Personalised for {birthData?.name || 'your selected chart'} and never indexed publicly.</p>
          </div>

          {Object.entries(sections).map(([title, content], index) => (
            <KarmaCard key={title} title={title} content={content} index={index} />
          ))}

          <div className="karma-footer">
            <div className="footer-text">Synthesised by AstroRoshni</div>
            <div className="footer-subtext">Parashari · Nadi · Jaimini · KP</div>
          </div>
        </div>

        {showRegenerateModal && (
          <CreditModal
            onClose={() => setShowRegenerateModal(false)}
            onConfirm={confirmRegenerate}
            credits={credits}
            cost={karmaCost}
            title="Regenerate Karma Analysis"
          />
        )}
      </>
    );
  };

  return (
    <>
      <SEOHead
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        ogImage={seoData.ogImage}
        twitterImage={seoData.twitterImage}
        structuredData={buildKarmaStructuredData()}
        themeColor="#210b17"
      />

      <ModernNavigationHeader
        sticky
        user={user}
        onLogin={onLogin}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
      />

      <div className="karma-page-wrap">
        <KarmaAnalysisLanding onGetStarted={handleGetStarted} />

        <section id="karma-tool" className="karma-tool-section" aria-labelledby="karma-tool-heading">
          <div className="karma-container karma-container--tool">
            <div className="karma-header">
              <div>
                <p className="karma-tool-kicker">Your private reading</p>
                <h2 id="karma-tool-heading" className="karma-tool-page-title">
                  Personalised karma analysis
                </h2>
              </div>
              {birthData && (
                <div className="karma-native-actions">
                  <button
                    type="button"
                    className="karma-native-button"
                    onClick={() => {
                      setBirthFormDefaultTab('saved');
                      setShowBirthFormModal(true);
                    }}
                  >
                    <span>
                      <small>Reading for</small>
                      <strong>{birthData.name || 'Selected native'}</strong>
                    </span>
                    <span aria-hidden="true">Change ↗</span>
                  </button>
                  {analysis && (
                    <button
                      type="button"
                      className="regenerate-button"
                      onClick={handleRegenerate}
                      title="Regenerate"
                    >
                      Regenerate
                    </button>
                  )}
                </div>
              )}
            </div>
            {renderToolInner()}
          </div>
        </section>
      </div>

      <BirthFormModal
        isOpen={showBirthFormModal}
        onClose={() => setShowBirthFormModal(false)}
        onSubmit={handleFormSubmit}
        defaultActiveTab={birthFormDefaultTab}
        title={birthData ? 'Select Different Native' : 'Enter Birth Details'}
        description={
          birthData
            ? 'Choose a different person\'s birth details for analysis'
            : 'Please provide your birth information for karma analysis'
        }
      />
    </>
  );
};

const CreditModal = ({ onClose, onConfirm, credits, cost, title }) => (
  <div className="karma-modal-overlay" onClick={onClose}>
    <div className="karma-modal" role="dialog" aria-modal="true" aria-labelledby="karma-credit-title" onClick={(e) => e.stopPropagation()}>
      <p className="karma-modal-kicker">Confirm reading</p>
      <h3 id="karma-credit-title">{title}</h3>
      <p>This personalised calculation will use <strong>{cost} credits</strong>.</p>
      <p className="karma-modal-balance">Your balance: {credits} credits</p>
      <div className="karma-modal-buttons">
        <button type="button" className="karma-modal-button" onClick={onClose}>
          Cancel
        </button>
        <button type="button" className="karma-modal-button karma-modal-button-primary" onClick={onConfirm}>
          Confirm &amp; begin
        </button>
      </div>
    </div>
  </div>
);

const KarmaCard = ({ title, content, index }) => {
  const [expanded, setExpanded] = useState(true);
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
      <button type="button" className="karma-card-header" onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>
        <div className={`karma-icon-circle ${isIntroduction ? 'intro-icon' : ''}`}>
          {String(index + 1).padStart(2, '0')}
        </div>
        <h3>{title}</h3>
        <span className="expand-icon" aria-hidden="true">{expanded ? '−' : '+'}</span>
      </button>
      {expanded && (
        <div className="karma-card-content">
          <div className="content-divider" />
          <div dangerouslySetInnerHTML={{ __html: formatContent(content) }} />
        </div>
      )}
    </div>
  );
};

export default KarmaAnalysis;
