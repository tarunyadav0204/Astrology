import React, { useState, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './MarriageAnalysisTab.css';
import PartnerForm from './PartnerForm';
import GunaScoreCard from './GunaScoreCard';
import CompatibilityReport from './CompatibilityReport';
import { useCredits } from '../../context/CreditContext';

const timeForPartnerInput = (t) => {
  if (t == null || t === '') return '';
  const s = String(t);
  if (s.length >= 8 && s[5] === ':' && s[7] === ':') return s.slice(0, 5);
  return s;
};

const personToPartnerInitial = (p) => {
  if (!p || typeof p !== 'object') return undefined;
  return {
    name: p.name || '',
    date: p.date || '',
    time: timeForPartnerInput(p.time),
    place: p.place || '',
    latitude: p.latitude ?? null,
    longitude: p.longitude ?? null
  };
};

const CompatibilityAnalysis = ({ user, onLogin } = {}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { credits, marriageCost, partnershipCost, fetchBalance } = useCredits();
  const { initialBoy, initialGirl } = useMemo(() => {
    const pref = location.state?.prefilledData;
    if (!pref) return { initialBoy: undefined, initialGirl: undefined };
    return {
      initialBoy: personToPartnerInitial(pref.person1),
      initialGirl: personToPartnerInitial(pref.person2)
    };
  }, [location.state]);

  const [partnerData, setPartnerData] = useState(null);
  const [compatibilityResult, setCompatibilityResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [premiumLoading, setPremiumLoading] = useState(false);
  const [premiumReport, setPremiumReport] = useState(null);
  const [premiumError, setPremiumError] = useState(null);
  const [error, setError] = useState(null);
  const [formKey, setFormKey] = useState(0);

  const compatibilityAnalysis = compatibilityResult?.compatibility_analysis;
  const timingOverlay = compatibilityResult?.timing_overlay || compatibilityAnalysis?.timing_overlay;
  const premiumReportCost = marriageCost || 3;
  const premiumChatCost = partnershipCost || 2;

  const handlePartnerSubmit = async (boyData, girlData) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/compatibility-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          boy_birth_data: boyData,
          girl_birth_data: girlData
        })
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Please sign in to run Kundli matching (Ashtakoot Milan).');
        }
        throw new Error('Failed to analyze compatibility');
      }

      const result = await response.json();
      setCompatibilityResult(result);
      setPartnerData({ boy: boyData, girl: girlData });
      setPremiumReport(null);
      setPremiumError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUnlockPremiumReport = async (forceRegenerate = false) => {
    if (!partnerData?.boy || !partnerData?.girl) return;
    const token = localStorage.getItem('token');
    if (!token) {
      onLogin && onLogin();
      return;
    }

    if (!premiumReport && premiumReportCost > 0 && credits < premiumReportCost) {
      setPremiumError(`You need ${premiumReportCost} credits for the AI Kundli matching report. Your balance is ${credits}.`);
      return;
    }

    const action = forceRegenerate ? 'regenerate' : 'unlock';
    if (!window.confirm(`This will ${action} the AI Kundli matching report for ${premiumReportCost} credits. Continue?`)) {
      return;
    }

    try {
      setPremiumLoading(true);
      setPremiumError(null);
      const response = await fetch('/api/compatibility-analysis/premium-report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          boy_birth_data: partnerData.boy,
          girl_birth_data: partnerData.girl,
          language: 'english',
          force_regenerate: !!forceRegenerate
        })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to generate AI Kundli matching report');
      }
      setPremiumReport(data.premium_report || null);
      fetchBalance && fetchBalance();
      window.dispatchEvent(new Event('creditUpdated'));
    } catch (err) {
      setPremiumError(err.message);
    } finally {
      setPremiumLoading(false);
    }
  };

  const handlePremiumChat = () => {
    if (!partnerData?.boy || !partnerData?.girl) return;
    if (!localStorage.getItem('token')) {
      onLogin && onLogin();
      return;
    }
    if (premiumChatCost > 0 && credits < premiumChatCost) {
      setPremiumError(`You need ${premiumChatCost} credits for premium relationship chat. Your balance is ${credits}.`);
      return;
    }
    navigate('/', {
      state: {
        prefillPartnership: {
          nativeChart: partnerData.boy,
          partnerChart: partnerData.girl,
          relationshipType: 'Kundli matching follow-up',
          initialPrompt:
            `Explain the Kundli matching between ${partnerData.boy.name || 'person one'} and ${partnerData.girl.name || 'person two'} in practical relationship terms.`
        }
      }
    });
  };

  const handleReset = () => {
    setPartnerData(null);
    setCompatibilityResult(null);
    setPremiumReport(null);
    setPremiumError(null);
    setError(null);
    if (location.pathname === '/kundli-matching') {
      navigate(`${location.pathname}${location.search || ''}`, { replace: true, state: {} });
    }
    setFormKey((k) => k + 1);
  };

  if (loading) {
    return (
      <div className="compatibility-loading">
        <div className="loading-spinner"></div>
        <p>Analyzing compatibility...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="compatibility-error">
        <h4>Error</h4>
        <p>{error}</p>
        {onLogin && String(error).toLowerCase().includes('sign in') && (
          <button type="button" className="btn-reset" onClick={onLogin} style={{ marginRight: 8 }}>
            Sign in
          </button>
        )}
        <button onClick={handleReset} className="btn-reset">Try Again</button>
      </div>
    );
  }

  if (!compatibilityResult) {
    return (
      <PartnerForm
        key={formKey}
        onSubmit={handlePartnerSubmit}
        user={user}
        onLogin={onLogin}
        initialBoy={initialBoy}
        initialGirl={initialGirl}
      />
    );
  }

  return (
    <div className="compatibility-analysis">
      <div className="compatibility-header">
        <h3>💕 Compatibility Analysis</h3>
        <button onClick={handleReset} className="btn-new-analysis">New Analysis</button>
      </div>
      
      {/* Partner Details Summary at Top */}
      <div className="partners-summary-top">
        <div className="partner-card-top">
          <div className="partner-info">
            <h4>👨 {compatibilityResult.boy_details.name}</h4>
            <p className="birth-details">{compatibilityResult.boy_details.date} at {compatibilityResult.boy_details.time}</p>
            <p className="birth-place">{compatibilityResult.boy_details.place}</p>
          </div>
        </div>

        <div className="compatibility-vs">💕</div>

        <div className="partner-card-top">
          <div className="partner-info">
            <h4>👩 {compatibilityResult.girl_details.name}</h4>
            <p className="birth-details">{compatibilityResult.girl_details.date} at {compatibilityResult.girl_details.time}</p>
            <p className="birth-place">{compatibilityResult.girl_details.place}</p>
          </div>
        </div>
      </div>
      
      <div className="overall-compatibility-score">
        <h3>{compatibilityAnalysis.overall_score.percentage}%</h3>
        <p>{compatibilityAnalysis.overall_score.grade}</p>
        <span>Overall Compatibility</span>
      </div>

      {timingOverlay?.shared?.current_window && (
        <div className="overall-compatibility-score" style={{ marginTop: 16 }}>
          <h3>{Math.round(timingOverlay.shared.joint_readiness_score || 0)}%</h3>
          <p>{String(timingOverlay.shared.current_window.climate || 'unknown').replace(/_/g, ' ')}</p>
          <span>Current Marriage Timing Climate</span>
        </div>
      )}
      
      <GunaScoreCard 
        gunaMilan={compatibilityAnalysis.guna_milan}
        overallScore={compatibilityAnalysis.overall_score}
      />
      
      <CompatibilityReport 
        analysis={compatibilityAnalysis}
        boyDetails={compatibilityResult.boy_details}
        girlDetails={compatibilityResult.girl_details}
      />

      <PremiumCompatibilityReport
        premiumReport={premiumReport}
        loading={premiumLoading}
        error={premiumError}
        cost={premiumReportCost}
        chatCost={premiumChatCost}
        onUnlock={() => handleUnlockPremiumReport(false)}
        onRegenerate={() => handleUnlockPremiumReport(true)}
        onPremiumChat={handlePremiumChat}
      />
    </div>
  );
};

const cleanReportText = (value) => String(value || '').replace(/\*\*/g, '').trim();

const PremiumCompatibilityReport = ({
  premiumReport,
  loading,
  error,
  cost,
  chatCost,
  onUnlock,
  onRegenerate,
  onPremiumChat
}) => {
  if (!premiumReport) {
    return (
      <section className="kundli-premium-card">
        <div className="kundli-premium-header">
          <div>
            <p className="kundli-premium-eyebrow">AI compatibility report</p>
            <h3>Unlock detailed Kundli matching guidance</h3>
          </div>
          <span className="kundli-premium-cost">{cost} credits</span>
        </div>
        <p>
          Go beyond the score with a personalised report covering emotional strengths, caution areas,
          Manglik balance, timing climate, decision guidance, and practical next steps.
        </p>
        <ul className="kundli-premium-list">
          <li>Plain-language explanation of mixed compatibility signals</li>
          <li>Practical meaning for marriage and long-term partnership</li>
          <li>Priority actions and conversations before commitment</li>
        </ul>
        {error && <div className="kundli-premium-error">{error}</div>}
        <div className="kundli-premium-actions">
          <button type="button" className="btn-premium-primary" onClick={onUnlock} disabled={loading}>
            {loading ? 'Generating report...' : `Unlock AI report (${cost} credits)`}
          </button>
          <button type="button" className="btn-premium-secondary" onClick={onPremiumChat}>
            Ask AI follow-up ({chatCost} credits)
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="kundli-premium-card kundli-premium-card--unlocked">
      <div className="kundli-premium-header">
        <div>
          <p className="kundli-premium-eyebrow">AI compatibility report</p>
          <h3>{cleanReportText(premiumReport.headline || 'Detailed Kundli matching report')}</h3>
        </div>
      </div>

      {premiumReport.compatibility_verdict && (
        <div className="kundli-premium-verdict">
          {cleanReportText(premiumReport.compatibility_verdict)}
        </div>
      )}

      {(premiumReport.sections || []).map((section, index) => (
        <article key={`${section.key || section.title || 'section'}_${index}`} className="kundli-premium-section">
          <h4>{cleanReportText(section.title || `Section ${index + 1}`)}</h4>
          {section.static_summary && <p>{cleanReportText(section.static_summary)}</p>}
          {section.ai_interpretation && <p>{cleanReportText(section.ai_interpretation)}</p>}
          {section.practical_meaning && (
            <div className="kundli-premium-subblock">
              <strong>Practical meaning</strong>
              <p>{cleanReportText(section.practical_meaning)}</p>
            </div>
          )}
          {section.decision_guidance && (
            <div className="kundli-premium-subblock">
              <strong>Decision guidance</strong>
              <p>{cleanReportText(section.decision_guidance)}</p>
            </div>
          )}
          {section.facts?.length > 0 && (
            <ul>
              {section.facts.slice(0, 5).map((fact, factIndex) => (
                <li key={factIndex}>{cleanReportText(fact)}</li>
              ))}
            </ul>
          )}
        </article>
      ))}

      {premiumReport.final_summary && (
        <div className="kundli-premium-subblock kundli-premium-final">
          <strong>Final summary</strong>
          <p>{cleanReportText(premiumReport.final_summary)}</p>
        </div>
      )}

      {premiumReport.priority_actions?.length > 0 && (
        <div className="kundli-premium-subblock">
          <strong>Priority actions</strong>
          <ul>
            {premiumReport.priority_actions.slice(0, 5).map((action, index) => (
              <li key={index}>{cleanReportText(action)}</li>
            ))}
          </ul>
        </div>
      )}

      {error && <div className="kundli-premium-error">{error}</div>}
      <div className="kundli-premium-actions">
        <button type="button" className="btn-premium-primary" onClick={onPremiumChat}>
          Ask AI follow-up ({chatCost} credits)
        </button>
        <button type="button" className="btn-premium-secondary" onClick={onRegenerate} disabled={loading}>
          {loading ? 'Regenerating...' : `Regenerate (${cost} credits)`}
        </button>
      </div>
    </section>
  );
};

export default CompatibilityAnalysis;
