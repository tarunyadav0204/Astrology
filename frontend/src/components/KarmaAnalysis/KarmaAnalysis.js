import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useCredits } from '../../context/CreditContext';
import { useAstrology } from '../../context/AstrologyContext';
import NavigationHeader from '../Shared/NavigationHeader';
import NativeSelector from '../Shared/NativeSelector';
import BirthFormModal from '../BirthForm/BirthFormModal';
import './KarmaAnalysis.css';

const KarmaAnalysis = () => {
  const { credits, refreshBalance } = useCredits();
  const { chartData, birthData } = useAstrology();
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [karmaCost, setKarmaCost] = useState(25);
  const [showStartModal, setShowStartModal] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [showBirthFormModal, setShowBirthFormModal] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showProgress, setShowProgress] = useState(false);
  const [progressTimer, setProgressTimer] = useState(null);

  const handleFormSubmit = () => {
    setShowBirthFormModal(false);
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    const chartId = birthData?.chart_id || chartData?.id;
    if (chartId) {
      setAnalysis(null);
      setShowBirthFormModal(false);
      checkExistingAnalysis();
    }
  }, [birthData?.chart_id, chartData?.id]);

  const loadInitialData = async () => {
    try {
      const token = localStorage.getItem('token');
      const costResponse = await axios.get('/api/credits/settings/karma-cost', {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
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
      const response = await axios.get(`/api/karma-analysis/status?chart_id=${chartId}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      
      if (response.data.status === 'complete' && response.data.data) {
        setAnalysis(response.data.data);
      } else if (response.data.status === 'pending' || response.data.status === 'processing') {
        startProgressBar();
        startPolling();
      }
    } catch (err) {
      console.error('Error checking existing analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartAnalysis = () => {
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
    console.log('Initiating analysis with chartId:', chartId, 'birthData:', birthData);
    
    if (!chartId) {
      setError('Chart not found. Please select a birth chart.');
      setLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const url = `/api/karma-analysis${forceRegenerate ? '?force_regenerate=true' : ''}`;
      const response = await axios.post(url, 
        { chart_id: String(chartId) },
        { headers: token ? { 'Authorization': `Bearer ${token}` } : {} }
      );
      
      if (response.data.status === 'complete') {
        stopProgressBar();
        setAnalysis(response.data.data);
        setLoading(false);
        refreshBalance();
      } else if (response.data.status === 'pending') {
        startPolling();
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
      currentStep++;
      const newProgress = (currentStep / steps) * 100;
      setProgress(newProgress);
      
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

  const startPolling = () => {
    const interval = setInterval(async () => {
      try {
        const token = localStorage.getItem('token');
        const chartId = birthData?.chart_id || chartData?.id;
        const response = await axios.get(`/api/karma-analysis/status?chart_id=${chartId}`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        
        if (response.data.status === 'complete') {
          stopProgressBar();
          setAnalysis(response.data.data);
          setLoading(false);
          clearInterval(interval);
          refreshBalance();
        } else if (response.data.status === 'error') {
          stopProgressBar();
          setError(response.data.error);
          setLoading(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Polling error:', err);
        stopProgressBar();
        setError(err.message);
        setLoading(false);
        clearInterval(interval);
      }
    }, 2000);
  };

  if (!chartData || !birthData) {
    return (
      <>
        <NavigationHeader 
          compact={true}
          showZodiacSelector={false}
          user={null}
          onLogin={() => setShowBirthFormModal(true)}
          showLoginButton={true}
        />
        <div className="karma-container">
          <div className="karma-header">
            <h1>🕉️ Past Life Karma Analysis</h1>
          </div>
          <div className="karma-start">
            <div className="om-symbol-large">🕉️</div>
            <h2>Past Life Karma Analysis</h2>
            <p>Please provide birth details to begin</p>
            <button className="start-button" onClick={() => setShowBirthFormModal(true)}>
              Enter Birth Details
            </button>
          </div>
          <BirthFormModal
            isOpen={showBirthFormModal}
            onClose={() => setShowBirthFormModal(false)}
            onSubmit={handleFormSubmit}
            title="Enter Birth Details"
            description="Please provide your birth information for karma analysis"
          />
        </div>
      </>
    );
  }

  if (loading) {
    return (
      <>
        <NavigationHeader 
          compact={true}
          showZodiacSelector={false}
          user={null}
          showLoginButton={false}
          birthData={birthData}
        />
        <div className="karma-container">
          <div className="karma-header">
            <h1>🕉️ Past Life Karma Analysis</h1>
            <NativeSelector birthData={birthData} onNativeChange={() => setShowBirthFormModal(true)} />
          </div>
          <div className="karma-loading">
            <div className="cosmic-loader">
              <div className="om-symbol">🕉️</div>
            </div>
            <div className="spinner"></div>
            <h2>Accessing Akashic Records</h2>
            <p>{showProgress ? "Analyzing your soul's journey through time..." : "This is taking longer than usual..."}</p>
            {showProgress && (
              <div className="progress-container">
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                </div>
                <div className="progress-text">{Math.round(progress)}%</div>
              </div>
            )}
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <NavigationHeader 
          compact={true}
          showZodiacSelector={false}
          user={null}
          showLoginButton={false}
          birthData={birthData}
        />
        <div className="karma-container">
          <div className="karma-header">
            <h1>🕉️ Past Life Karma Analysis</h1>
            <NativeSelector birthData={birthData} onNativeChange={() => setShowBirthFormModal(true)} />
          </div>
          <div className="karma-error">
            <div className="error-icon">⚠️</div>
            <h2>Unable to Access Records</h2>
            <p>{error}</p>
            <button className="retry-button" onClick={() => { setError(null); checkExistingAnalysis(); }}>
              Try Again
            </button>
          </div>
        </div>
      </>
    );
  }

  if (!analysis) {
    return (
      <>
        <NavigationHeader 
          compact={true}
          showZodiacSelector={false}
          user={null}
          showLoginButton={false}
          birthData={birthData}
        />
        <div className="karma-container">
          <div className="karma-header">
            <h1>🕉️ Past Life Karma Analysis</h1>
            <NativeSelector birthData={birthData} onNativeChange={() => setShowBirthFormModal(true)} />
          </div>
          <div className="karma-start">
            <div className="om-symbol-large">🕉️</div>
            <h2>Past Life Karma Analysis</h2>
            <p>Discover your soul's eternal journey</p>
            <button className="start-button" onClick={handleStartAnalysis}>
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
        </div>
      </>
    );
  }

  const sections = analysis.sections || {};

  return (
    <>
      <NavigationHeader 
        compact={true}
        showZodiacSelector={false}
        user={null}
        showLoginButton={false}
        birthData={birthData}
      />
      <div className="karma-container">
        <div className="karma-header">
          <h1>🕉️ Past Life Karma Analysis</h1>
          <NativeSelector birthData={birthData} onNativeChange={() => setShowBirthFormModal(true)} />
          <button className="regenerate-button" onClick={handleRegenerate} title="Regenerate">
            ↻
          </button>
        </div>

        <div className="karma-content">
          <div className="karma-title-section">
            <div className="om-header">🕉️</div>
            <h2>Past Life Karma</h2>
            <p>Your Soul's Eternal Journey</p>
          </div>

          {Object.entries(sections).map(([title, content], index) => (
            <KarmaCard key={index} title={title} content={content} index={index} />
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
            onConfirm={confirmRegenerate}
            credits={credits}
            cost={karmaCost}
            title="Regenerate Karma Analysis"
          />
        )}
        
        <BirthFormModal
          isOpen={showBirthFormModal}
          onClose={() => setShowBirthFormModal(false)}
          onSubmit={handleFormSubmit}
          title="Select Different Native"
          description="Choose a different person's birth details for analysis"
        />
      </div>
    </>
  );
};

const CreditModal = ({ onClose, onConfirm, credits, cost, title }) => (
  <div className="modal-overlay" onClick={onClose}>
    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
      <h3>{title}</h3>
      <p>This will use {cost} credits</p>
      <p className="modal-balance">Your balance: {credits} credits</p>
      <div className="modal-buttons">
        <button className="modal-button" onClick={onClose}>Cancel</button>
        <button className="modal-button modal-button-primary" onClick={onConfirm}>Confirm</button>
      </div>
    </div>
  </div>
);

const KarmaCard = ({ title, content, index }) => {
  const [expanded, setExpanded] = useState(true);
  const icons = ['🕉️', '🌟', '🎯', '⚖️', '💎', '🔱', '👪', '🦋', '🙏', '⏳', '🕉️'];
  const isIntroduction = title === 'Introduction';

  const formatContent = (text) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  };

  return (
    <div className={`karma-card ${isIntroduction ? 'karma-card-intro' : ''}`}>
      <div className="karma-card-header" onClick={() => setExpanded(!expanded)}>
        <div className={`karma-icon-circle ${isIntroduction ? 'intro-icon' : ''}`}>
          {icons[index % icons.length]}
        </div>
        <h3>{title}</h3>
        <span className="expand-icon">{expanded ? '▼' : '▶'}</span>
      </div>
      {expanded && (
        <div className="karma-card-content">
          <div className="content-divider"></div>
          <div dangerouslySetInnerHTML={{ __html: formatContent(content) }} />
        </div>
      )}
    </div>
  );
};

export default KarmaAnalysis;
