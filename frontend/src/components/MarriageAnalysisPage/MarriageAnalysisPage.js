import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import MarriageAnalysisTab from '../MarriageAnalysis/MarriageAnalysisTab';
import BirthForm from '../BirthForm/BirthForm';
import { AstrologyContext } from '../../context/AstrologyContext';
import './MarriageAnalysisPage.css';

const MarriageAnalysisPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const navigate = useNavigate();
  const { chartData, birthDetails } = useContext(AstrologyContext);
  const [showForm, setShowForm] = useState(!chartData || !birthDetails);

  const zodiacSigns = [
    { name: 'aries', symbol: '♈', displayName: 'Aries' },
    { name: 'taurus', symbol: '♉', displayName: 'Taurus' },
    { name: 'gemini', symbol: '♊', displayName: 'Gemini' },
    { name: 'cancer', symbol: '♋', displayName: 'Cancer' },
    { name: 'leo', symbol: '♌', displayName: 'Leo' },
    { name: 'virgo', symbol: '♍', displayName: 'Virgo' },
    { name: 'libra', symbol: '♎', displayName: 'Libra' },
    { name: 'scorpio', symbol: '♏', displayName: 'Scorpio' },
    { name: 'sagittarius', symbol: '♐', displayName: 'Sagittarius' },
    { name: 'capricorn', symbol: '♑', displayName: 'Capricorn' },
    { name: 'aquarius', symbol: '♒', displayName: 'Aquarius' },
    { name: 'pisces', symbol: '♓', displayName: 'Pisces' }
  ];

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
        zodiacSigns={zodiacSigns}
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
                <BirthForm onSubmit={handleFormSubmit} />
              </div>
            </div>
          ) : (
            <div className="analysis-section">
              <MarriageAnalysisTab chartData={chartData} birthDetails={birthDetails} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MarriageAnalysisPage;