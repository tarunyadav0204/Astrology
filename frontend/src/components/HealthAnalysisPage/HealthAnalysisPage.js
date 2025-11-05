import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import NativeSelector from '../Shared/NativeSelector';
import CompleteHealthAnalysisTab from '../Health/CompleteHealthAnalysisTab';
import AIInsightsTab from '../Health/AIInsightsTab';
import BirthForm from '../BirthForm/BirthForm';
import SEOHead from '../SEO/SEOHead';
import { useAstrology } from '../../context/AstrologyContext';
import { ZODIAC_SIGNS } from '../../config/career.config';
import { generatePageSEO } from '../../config/seo.config';
import './HealthAnalysisPage.css';

const HealthAnalysisPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const navigate = useNavigate();
  const { chartData, birthData } = useAstrology();
  const [showForm, setShowForm] = useState(!chartData || !birthData);
  const [activeTab, setActiveTab] = useState('insights');

  const handleAdminClick = () => {
    if (onAdminClick) {
      onAdminClick();
    }
  };

  const handleFormSubmit = () => {
    setShowForm(false);
  };

  const seoData = generatePageSEO('healthAnalysis', { path: '/health-analysis' });

  return (
    <div className="health-analysis-page">
      <SEOHead 
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={{
          "@context": "https://schema.org",
          "@type": "Service",
          "name": "Health Analysis Report",
          "description": "Comprehensive health analysis using Vedic medical astrology for wellness insights",
          "provider": { "@type": "Organization", "name": "AstroRoshni" }
        }}
      />
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
                <div className="tab-navigation">
                  <button 
                    className={`tab-btn ${activeTab === 'insights' ? 'active' : ''}`}
                    onClick={() => setActiveTab('insights')}
                  >
                    Personalized Health Insights
                  </button>
                  <button 
                    className={`tab-btn ${activeTab === 'detailed' ? 'active' : ''}`}
                    onClick={() => setActiveTab('detailed')}
                  >
                    Detailed Technical Analysis
                  </button>
                </div>
                
                <div className="tab-content">
                  {activeTab === 'insights' && (
                    <AIInsightsTab chartData={chartData} birthDetails={birthData} />
                  )}
                  {activeTab === 'detailed' && (
                    <CompleteHealthAnalysisTab chartData={chartData} birthDetails={birthData} />
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default HealthAnalysisPage;