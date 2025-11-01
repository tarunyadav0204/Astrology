import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import NativeSelector from '../Shared/NativeSelector';
import CompleteHealthAnalysisTab from '../Health/CompleteHealthAnalysisTab';
import BirthForm from '../BirthForm/BirthForm';
import { useAstrology } from '../../context/AstrologyContext';
import { ZODIAC_SIGNS } from '../../config/career.config';
import './HealthAnalysisPage.css';

const HealthAnalysisPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const navigate = useNavigate();
  const { chartData, birthData } = useAstrology();
  const [showForm, setShowForm] = useState(!chartData || !birthData);

  const handleAdminClick = () => {
    if (onAdminClick) {
      onAdminClick();
    }
  };

  const handleFormSubmit = () => {
    setShowForm(false);
  };

  return (
    <div className="health-analysis-page">
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
            <h1>🌿 Health Analysis Report</h1>
            <p>Get comprehensive insights about your health, vitality, and wellness prospects</p>
          </div>

          {showForm ? (
            <div className="form-section">
              <div className="form-card">
                <h2>Enter Your Birth Details</h2>
                <p>Please provide your birth information to generate your health analysis report</p>
                <BirthForm onSubmit={handleFormSubmit} />
              </div>
            </div>
          ) : (
            <>
              <NativeSelector 
                birthData={birthData} 
                onNativeChange={() => window.location.reload()}
              />
              <div className="analysis-section">
                <CompleteHealthAnalysisTab chartData={chartData} birthDetails={birthData} />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default HealthAnalysisPage;