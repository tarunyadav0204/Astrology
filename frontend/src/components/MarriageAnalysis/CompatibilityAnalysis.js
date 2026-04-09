import React, { useState, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import PartnerForm from './PartnerForm';
import GunaScoreCard from './GunaScoreCard';
import CompatibilityReport from './CompatibilityReport';

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
  const [error, setError] = useState(null);
  const [formKey, setFormKey] = useState(0);

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
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setPartnerData(null);
    setCompatibilityResult(null);
    setError(null);
    if (location.pathname === '/kundli-matching') {
      navigate(location.pathname, { replace: true, state: {} });
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
        <h3>{compatibilityResult.compatibility_analysis.overall_score.percentage}%</h3>
        <p>{compatibilityResult.compatibility_analysis.overall_score.grade}</p>
        <span>Overall Compatibility</span>
      </div>
      
      <GunaScoreCard 
        gunaMilan={compatibilityResult.compatibility_analysis.guna_milan}
        overallScore={compatibilityResult.compatibility_analysis.overall_score}
      />
      
      <CompatibilityReport 
        analysis={compatibilityResult.compatibility_analysis}
        boyDetails={compatibilityResult.boy_details}
        girlDetails={compatibilityResult.girl_details}
      />
    </div>
  );
};

export default CompatibilityAnalysis;