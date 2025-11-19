import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import NativeSelector from '../Shared/NativeSelector';
import CompleteHealthAnalysisTab from '../Health/CompleteHealthAnalysisTab';
import AIInsightsTab from '../Health/AIInsightsTab';
import BirthFormModal from '../BirthForm/BirthFormModal';
import SEOHead from '../SEO/SEOHead';
import { useAstrology } from '../../context/AstrologyContext';
import { ZODIAC_SIGNS } from '../../config/career.config';
import { generatePageSEO } from '../../config/seo.config';
import './HealthAnalysisPage.css';

const HealthAnalysisPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const navigate = useNavigate();
  const { chartData, birthData } = useAstrology();
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
          ) : (
            <div className="no-data-message">
              <h3>🌿 Health Analysis Report</h3>
              <p>Your personalized health analysis will appear here once you provide your birth details.</p>
            </div>
          )}
          
          <BirthFormModal
            isOpen={showModal}
            onClose={() => setShowModal(false)}
            onSubmit={handleFormSubmit}
            title="Health Analysis - Enter Birth Details"
            description="Please provide your birth information to generate your health analysis report"
          />
        </div>
      </div>
    </div>
  );
};

export default HealthAnalysisPage;