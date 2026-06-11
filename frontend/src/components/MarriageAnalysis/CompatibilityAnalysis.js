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

const CompatibilityAnalysis = ({ user, onLogin, onBuyCredits } = {}) => {
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
      setPremiumError(`You need ${premiumReportCost} credits for the detailed Kundli matching report. Your balance is ${credits}.`);
      return;
    }

    const action = forceRegenerate ? 'regenerate' : 'unlock';
    if (!window.confirm(`This will ${action} the detailed Kundli matching report for ${premiumReportCost} credits. Continue?`)) {
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
        throw new Error(data.detail || 'Failed to generate detailed Kundli matching report');
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

  const currentWindow = timingOverlay?.shared?.current_window || {};
  const nextWindow = timingOverlay?.shared?.next_favorable_windows?.[0];
  const evidenceSummary = compatibilityAnalysis.evidence_summary || {};
  const evidenceObjects = compatibilityAnalysis.evidence_objects || {};
  const positives = evidenceSummary.positive_factors || [];
  const cautions = evidenceSummary.caution_factors || [];
  const contradictions = evidenceSummary.contradictions || [];
  const supportiveEvidence = evidenceObjects.supportive || [];
  const challengingEvidence = evidenceObjects.challenging || [];
  const neutralEvidence = evidenceObjects.neutral || [];
  const crossChart = compatibilityAnalysis.relationship_indicators?.cross_chart || {};
  const boyProfile = compatibilityAnalysis.profiles?.boy || compatibilityResult.boy_profile || {};
  const girlProfile = compatibilityAnalysis.profiles?.girl || compatibilityResult.girl_profile || {};
  const manglikStatus = compatibilityAnalysis.manglik_analysis?.compatibility?.status || '--';
  const effectiveGuna =
    compatibilityAnalysis.guna_milan?.effective_total_score ?? compatibilityAnalysis.guna_milan?.total_score;
  const resultVerdict = verdictFromResult(compatibilityAnalysis, timingOverlay);

  return (
    <div className="compatibility-analysis">
      <div className="compatibility-header">
        <h3>💕 Compatibility Analysis</h3>
        <button onClick={handleReset} className="btn-new-analysis">New Analysis</button>
      </div>

      <section className="kundli-result-hero">
        <div className="kundli-result-hero-main">
          <p className="kundli-result-eyebrow">Instant verdict</p>
          <h2>{resultVerdict}</h2>
          <p>
            Based on classical compatibility, Manglik balance, deeper marriage support, and current timing climate.
          </p>
          <div className="kundli-result-hero-actions">
            <button type="button" className="btn-premium-primary" onClick={() => handleUnlockPremiumReport(false)} disabled={premiumLoading}>
              {premiumLoading ? 'Generating report...' : `Unlock detailed report (${premiumReportCost} credits)`}
            </button>
            <button type="button" className="btn-premium-secondary" onClick={handlePremiumChat}>
              Ask follow-up ({premiumChatCost} credits)
            </button>
          </div>
          {premiumError && (
            <div className="kundli-premium-error kundli-premium-error--inline">
              <p>{premiumError}</p>
              {onBuyCredits && (
                <button type="button" className="btn-premium-buy-credits" onClick={onBuyCredits}>
                  Buy credits
                </button>
              )}
            </div>
          )}
        </div>
        <div className="kundli-result-score-block">
          <strong>{compatibilityAnalysis.overall_score.percentage}%</strong>
          <span>{compatibilityAnalysis.overall_score.grade}</span>
        </div>
      </section>

      <section className="kundli-result-trust" aria-label="Kundli match evidence summary">
        <article>
          <span>Ashtakoot</span>
          <strong>{effectiveGuna ?? '--'}/36</strong>
          <p>Effective Guna Milan score</p>
        </article>
        <article>
          <span>Manglik</span>
          <strong>{manglikStatus}</strong>
          <p>Pair-level compatibility</p>
        </article>
        <article>
          <span>D1/D9</span>
          <strong>{titleCase(crossChart.overall_relationship_quality?.band || 'Reviewed')}</strong>
          <p>Marriage support synthesis</p>
        </article>
        <article>
          <span>Timing</span>
          <strong>{climateLabel(currentWindow.climate)}</strong>
          <p>{scoreText(currentWindow.score)} current window</p>
        </article>
      </section>

      <section className="kundli-result-grid">
        <FactorList
          title="Key strengths"
          items={positives}
          tone="supportive"
          emptyText="No major supportive factors were highlighted in the free summary."
        />
        <FactorList
          title="Caution areas"
          items={cautions}
          tone="challenging"
          emptyText="No major caution factor was highlighted in the free summary."
        />
        <FactorList
          title="Mixed signals"
          items={contradictions}
          tone="neutral"
          emptyText="No major contradiction was found between surface score and deeper chart support."
        />
      </section>

      <section className="kundli-timing-panel">
        <div>
          <p className="kundli-result-eyebrow">Timing guidance</p>
          <h3>{climateLabel(currentWindow.climate)} current climate</h3>
          <p>
            {currentWindow.summary ||
              compatibilityAnalysis.recommendation?.timing_note ||
              'Current commitment timing is evaluated from the shared dasha and transit climate.'}
          </p>
        </div>
        {nextWindow && (
          <div className="kundli-next-window">
            <span>Visible favorable window</span>
            <strong>{formatWindowRange(nextWindow) || 'Available in report'}</strong>
            <p>{climateLabel(nextWindow.climate)} climate</p>
          </div>
        )}
      </section>

      <section className="kundli-marriage-support">
        <div className="kundli-section-heading">
          <p className="kundli-result-eyebrow">Marriage support</p>
          <h3>D1 and D9 stability signals</h3>
        </div>
        <div className="kundli-person-support-grid">
          <MarriageSupportCard label={compatibilityResult.boy_details.name || 'Boy'} profile={boyProfile} />
          <MarriageSupportCard label={compatibilityResult.girl_details.name || 'Girl'} profile={girlProfile} />
        </div>
      </section>

      <section className="kundli-result-grid">
        <EvidenceList
          title="Supportive evidence"
          items={supportiveEvidence}
          emptyText="Supportive evidence will appear here when available from the matching engine."
        />
        <EvidenceList
          title="Challenging evidence"
          items={challengingEvidence}
          emptyText="Challenging evidence will appear here when available from the matching engine."
        />
        <EvidenceList
          title="Neutral evidence"
          items={neutralEvidence}
          emptyText="Neutral evidence will appear here when available from the matching engine."
        />
      </section>
      
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
        onBuyCredits={onBuyCredits}
      />
    </div>
  );
};

const cleanReportText = (value) => String(value || '').replace(/\*\*/g, '').trim();

const titleCase = (value = '') =>
  String(value)
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());

const scoreText = (value, fallback = '--') =>
  typeof value === 'number' ? `${Math.round(value)}%` : fallback;

const combineScores = (...values) => {
  const valid = values.filter((value) => typeof value === 'number');
  if (!valid.length) return null;
  return valid.reduce((sum, value) => sum + value, 0) / valid.length;
};

const climateLabel = (value = 'mixed') => titleCase(value || 'mixed');

const formatWindowRange = (windowData) => {
  if (!windowData?.start_date || !windowData?.end_date) return null;
  const start = new Date(windowData.start_date);
  const end = new Date(windowData.end_date);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;
  const fmt = (date) => date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  return `${fmt(start)} - ${fmt(end)}`;
};

const verdictFromResult = (analysis, timingOverlay) => {
  const grade = analysis?.overall_score?.grade || 'Match';
  const currentClimate = timingOverlay?.shared?.current_window?.climate;
  const issues = analysis?.guna_milan?.critical_issues || [];
  if (issues.length) return `${grade} match with ${issues.length} serious adjustment area${issues.length > 1 ? 's' : ''}`;
  if (currentClimate && !['favorable', 'highly_favorable'].includes(currentClimate)) {
    return `${grade} match, but timing needs attention`;
  }
  return `${grade} match with supportive compatibility signals`;
};

const FactorList = ({ title, items = [], tone = 'supportive', emptyText }) => (
  <section className={`kundli-result-card kundli-result-card--${tone}`}>
    <h4>{title}</h4>
    {items.length ? (
      <ul>
        {items.slice(0, 3).map((item, index) => (
          <li key={`${title}_${index}`}>{cleanReportText(item.summary || item)}</li>
        ))}
      </ul>
    ) : (
      <p>{emptyText}</p>
    )}
  </section>
);

const EvidenceList = ({ title, items = [], emptyText }) => (
  <section className="kundli-result-card">
    <h4>{title}</h4>
    {items.length ? (
      <div className="kundli-evidence-list">
        {items.slice(0, 4).map((item, index) => (
          <div key={`${title}_${index}`} className={`kundli-evidence-item polarity-${item.polarity || 'neutral'}`}>
            <div>
              <strong>{titleCase(item.category || 'Evidence')}</strong>
              <p>{cleanReportText(item.summary || item)}</p>
            </div>
            {typeof item.weight === 'number' && <span>{Math.round(item.weight * 100)}%</span>}
          </div>
        ))}
      </div>
    ) : (
      <p>{emptyText}</p>
    )}
  </section>
);

const MarriageSupportCard = ({ label, profile = {} }) => {
  const seventh = profile.seventh_house || {};
  const navamsa = profile.navamsa_synthesis || {};
  const d9Score = combineScores(seventh?.d9_strength?.score, navamsa?.score);
  return (
    <article className="kundli-person-support">
      <div>
        <h4>{label}</h4>
        <span>{profile.ascendant_sign_name || 'Chart'} ascendant</span>
      </div>
      <div className="kundli-person-metrics">
        <div>
          <strong>{scoreText(seventh?.d1_strength?.score)}</strong>
          <span>D1 marriage</span>
        </div>
        <div>
          <strong>{scoreText(d9Score)}</strong>
          <span>D9 marriage</span>
        </div>
      </div>
      <p>{titleCase(navamsa?.root_vs_fruit || 'consistent')} root-fruit pattern</p>
    </article>
  );
};

const PremiumCompatibilityReport = ({
  premiumReport,
  loading,
  error,
  cost,
  chatCost,
  onUnlock,
  onRegenerate,
  onPremiumChat,
  onBuyCredits
}) => {
  if (!premiumReport) {
    return (
      <section className="kundli-premium-card">
        <div className="kundli-premium-header">
          <div>
            <p className="kundli-premium-eyebrow">Detailed compatibility report</p>
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
        {error && (
          <div className="kundli-premium-error">
            <p>{error}</p>
            {onBuyCredits && (
              <button type="button" className="btn-premium-buy-credits" onClick={onBuyCredits}>
                Buy credits
              </button>
            )}
          </div>
        )}
        <div className="kundli-premium-actions">
          <button type="button" className="btn-premium-primary" onClick={onUnlock} disabled={loading}>
            {loading ? 'Generating report...' : `Unlock detailed report (${cost} credits)`}
          </button>
          <button type="button" className="btn-premium-secondary" onClick={onPremiumChat}>
            Ask follow-up ({chatCost} credits)
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="kundli-premium-card kundli-premium-card--unlocked">
      <div className="kundli-premium-header">
        <div>
          <p className="kundli-premium-eyebrow">Detailed compatibility report</p>
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

      {error && (
        <div className="kundli-premium-error">
          <p>{error}</p>
          {onBuyCredits && (
            <button type="button" className="btn-premium-buy-credits" onClick={onBuyCredits}>
              Buy credits
            </button>
          )}
        </div>
      )}
      <div className="kundli-premium-actions">
        <button type="button" className="btn-premium-primary" onClick={onPremiumChat}>
          Ask follow-up ({chatCost} credits)
        </button>
        <button type="button" className="btn-premium-secondary" onClick={onRegenerate} disabled={loading}>
          {loading ? 'Regenerating...' : `Regenerate (${cost} credits)`}
        </button>
      </div>
    </section>
  );
};

export default CompatibilityAnalysis;
