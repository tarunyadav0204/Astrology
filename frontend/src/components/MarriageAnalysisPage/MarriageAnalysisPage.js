import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import NativeSelector from '../Shared/NativeSelector';
import MarriageAnalysisTab from '../MarriageAnalysis/MarriageAnalysisTab';
import BirthFormModal from '../BirthForm/BirthFormModal';
import SEOHead from '../SEO/SEOHead';
import { useAstrology } from '../../context/AstrologyContext';
import { ZODIAC_SIGNS } from '../../config/career.config';
import './MarriageAnalysisPage.css';

const MarriageAnalysisPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { chartData, birthData } = useAstrology();
  const [showModal, setShowModal] = useState(!chartData || !birthData);
  const [prefilledData, setPrefilledData] = useState(null);

  useEffect(() => {
    if (location.state?.prefilledData) {
      setPrefilledData(location.state.prefilledData);
      setShowModal(true); // Show modal with prefilled data
    }
  }, [location.state]);



  const handleAdminClick = () => {
    if (onAdminClick) {
      onAdminClick();
    }
  };

  const handleFormSubmit = () => {
    setShowModal(false);
  };

  return (
    <div className="marriage-analysis-page">
      <SEOHead 
        title="Marriage Analysis Report - Vedic Astrology Compatibility | AstroRoshni"
        description="Get detailed marriage analysis and compatibility report based on Vedic astrology. Discover spouse characteristics, marriage timing, and relationship insights."
        keywords="marriage analysis, horoscope matching, kundli matching, marriage compatibility, spouse prediction, marriage astrology, vedic marriage analysis"
        canonical="https://astroroshni.com/marriage-analysis"
        structuredData={{
          "@context": "https://schema.org",
          "@type": "Service",
          "name": "Marriage Analysis Report",
          "description": "Comprehensive Vedic astrology marriage analysis including compatibility, spouse characteristics, and marriage timing predictions",
          "provider": {
            "@type": "Organization",
            "name": "AstroRoshni"
          },
          "offers": {
            "@type": "Offer",
            "price": "199",
            "priceCurrency": "INR"
          }
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
            <h1>💍 Marriage Analysis Report</h1>
            <p>Get comprehensive insights about your marriage prospects and spouse characteristics</p>
          </div>

          <div className="analysis-section">
            {chartData && birthData ? (
              <>
                <NativeSelector 
                  birthData={birthData} 
                  onNativeChange={() => window.location.reload()}
                />
                <MarriageAnalysisTab chartData={chartData} birthDetails={birthData} />
              </>
            ) : (
              <div className="no-data-message">
                <h3>💍 Marriage Analysis Report</h3>
                <p>Your personalized marriage analysis will appear here once you provide your birth details.</p>
              </div>
            )}
          </div>
          
          <BirthFormModal
            isOpen={showModal}
            onClose={() => setShowModal(false)}
            onSubmit={handleFormSubmit}
            title="Marriage Analysis - Enter Birth Details"
            description="Please provide your birth information to generate your marriage analysis report"
            prefilledData={prefilledData}
          />
        </div>
      </div>
    </div>
  );
};

export default MarriageAnalysisPage;