import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import NativeSelector from '../Shared/NativeSelector';
import CompleteWealthAnalysisTab from '../Wealth/CompleteWealthAnalysisTab';
import AIInsightsTab from '../Wealth/AIInsightsTab';
import BirthForm from '../BirthForm/BirthForm';
import SEOHead from '../SEO/SEOHead';
import { useAstrology } from '../../context/AstrologyContext';
import { ZODIAC_SIGNS } from '../../config/career.config';
import { generatePageSEO } from '../../config/seo.config';
import './WealthAnalysisPage.css';

const WealthAnalysisPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
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

  const seoData = generatePageSEO('wealthAnalysis', { path: '/wealth-analysis' });

  return (
    <div className="wealth-analysis-page">
      <SEOHead 
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={{
          "@context": "https://schema.org",
          "@type": "Service",
          "name": "Wealth Analysis Report",
          "description": "Detailed wealth and finance analysis based on Vedic astrology for financial growth",
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
            <h1>💰 Wealth Analysis Report</h1>
            <p>Get comprehensive insights about your financial prospects, income sources, and wealth-building potential</p>
          </div>

          {showForm ? (
            <div className="form-section">
              <div className="form-card">
                <h2>Enter Your Birth Details</h2>
                <p>Please provide your birth information to generate your wealth analysis report</p>
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
                    Personalized Wealth Insights
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
                    <CompleteWealthAnalysisTab chartData={chartData} birthDetails={birthData} />
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

export default WealthAnalysisPage;