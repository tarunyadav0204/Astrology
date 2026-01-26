import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import NativeSelector from '../Shared/NativeSelector';
import CompleteWealthAnalysisTab from '../Wealth/CompleteWealthAnalysisTab';
import AIInsightsTab from '../Wealth/AIInsightsTab';
import AstrologicalContextTab from '../Wealth/AstrologicalContextTab';
import BirthFormModal from '../BirthForm/BirthFormModal';
import SEOHead from '../SEO/SEOHead';
import { useAstrology } from '../../context/AstrologyContext';
import { useCredits } from '../../context/CreditContext';
import { ZODIAC_SIGNS } from '../../config/career.config';
import { generatePageSEO } from '../../config/seo.config';
import './WealthAnalysisPage.css';

const WealthAnalysisPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const navigate = useNavigate();
  const { chartData, birthData } = useAstrology();
  const { wealthCost } = useCredits();
  const [showModal, setShowModal] = useState(!chartData || !birthData);
  const [activeTab, setActiveTab] = useState('insights');

  const handleAdminClick = () => {
    if (onAdminClick) {
      onAdminClick();
    }
  };

  const handleFormSubmit = () => {
    setShowModal(false);
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
        compact={true}
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

          {chartData && birthData ? (
            <>
              <NativeSelector 
                birthData={birthData} 
                onNativeChange={() => setShowModal(true)}
              />
              <div className="analysis-section">
                <div className="tab-navigation">
                  <button 
                    className={`tab-btn ${activeTab === 'insights' ? 'active' : ''}`}
                    onClick={() => setActiveTab('insights')}
                  >
                    Wealth Insights ({wealthCost} credits)
                  </button>
                  <button 
                    className={`tab-btn ${activeTab === 'detailed' ? 'active' : ''}`}
                    onClick={() => setActiveTab('detailed')}
                  >
                    Detailed Technical Analysis
                  </button>
                  {user?.role === 'admin' && (
                    <button 
                      className={`tab-btn ${activeTab === 'context' ? 'active' : ''}`}
                      onClick={() => setActiveTab('context')}
                    >
                      Astrological Context
                    </button>
                  )}
                </div>
                
                <div className="tab-content">
                  {activeTab === 'insights' && (
                    <AIInsightsTab chartData={chartData} birthDetails={birthData} />
                  )}
                  {activeTab === 'detailed' && (
                    <CompleteWealthAnalysisTab chartData={chartData} birthDetails={birthData} />
                  )}
                  {activeTab === 'context' && user?.role === 'admin' && (
                    <AstrologicalContextTab birthDetails={birthData} user={user} />
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="no-data-message">
              <h3>💰 Wealth Analysis Report</h3>
              <p>Your personalized wealth analysis will appear here once you provide your birth details.</p>
            </div>
          )}
          
          <BirthFormModal
            isOpen={showModal}
            onClose={() => setShowModal(false)}
            onSubmit={handleFormSubmit}
            title="Wealth Analysis - Enter Birth Details"
            description="Please provide your birth information to generate your wealth analysis report"
          />
        </div>
      </div>
    </div>
  );
};

export default WealthAnalysisPage;