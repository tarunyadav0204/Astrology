import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import NativeSelector from '../Shared/NativeSelector';
import MarriageAnalysisTab from '../MarriageAnalysis/MarriageAnalysisTab';
import BirthForm from '../BirthForm/BirthForm';
import { useAstrology } from '../../context/AstrologyContext';
import { ZODIAC_SIGNS } from '../../config/career.config';
import './MarriageAnalysisPage.css';

const MarriageAnalysisPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { chartData, birthData } = useAstrology();
  const [showForm, setShowForm] = useState(!chartData || !birthData);
  const [prefilledData, setPrefilledData] = useState(null);

  useEffect(() => {
    if (location.state?.prefilledData) {
      setPrefilledData(location.state.prefilledData);
      setShowForm(true); // Show form with prefilled data
    }
  }, [location.state]);



  const handleAdminClick = () => {
    if (onAdminClick) {
      onAdminClick();
    }
  };

  const handleFormSubmit = () => {
    setShowForm(false);
  };

  return (
    <div className="marriage-analysis-page">
      <NavigationHeader 
        showZodiacSelector={false}
        zodiacSigns={ZODIAC_SIGNS}
        user={user}
        onAdminClick={handleAdminClick}
        onLogout={onLogout}
        onLogin={onLogin}
        showLoginButton={showLoginButton}
      />

      <div className="page-content">
        <div className="container">
          <div className="page-header">
            <button className="back-btn" onClick={() => navigate('/')}>
              ← Back to Home
            </button>
            <h1>💍 Marriage Analysis Report</h1>
            <p>Get comprehensive insights about your marriage prospects and spouse characteristics</p>
          </div>

          {showForm ? (
            <div className="form-section">
              <div className="form-card">
                <h2>Enter Your Birth Details</h2>
                <p>Please provide your birth information to generate your marriage analysis report</p>
                <BirthForm onSubmit={handleFormSubmit} prefilledData={prefilledData} />
              </div>
            </div>
          ) : (
            <div className="analysis-section">
              <NativeSelector 
                birthData={birthData} 
                onNativeChange={() => window.location.reload()}
              />
              <MarriageAnalysisTab chartData={chartData} birthDetails={birthData} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MarriageAnalysisPage;