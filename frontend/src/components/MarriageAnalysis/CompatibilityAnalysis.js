import React, { useState } from 'react';
import PartnerForm from './PartnerForm';
import GunaScoreCard from './GunaScoreCard';
import CompatibilityReport from './CompatibilityReport';

const CompatibilityAnalysis = () => {
  const [partnerData, setPartnerData] = useState(null);
  const [compatibilityResult, setCompatibilityResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
        <button onClick={handleReset} className="btn-reset">Try Again</button>
      </div>
    );
  }

  if (!compatibilityResult) {
    return <PartnerForm onSubmit={handlePartnerSubmit} />;
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