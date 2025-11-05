import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import NativeSelector from '../Shared/NativeSelector';
import CareerAnalysisTab from '../Career/CareerAnalysisTab';
import BirthForm from '../BirthForm/BirthForm';
import SEOHead from '../SEO/SEOHead';
import { useAstrology } from '../../context/AstrologyContext';
import { ZODIAC_SIGNS } from '../../config/career.config';
import { generatePageSEO } from '../../config/seo.config';
import './CareerGuidancePage.css';

const CareerGuidancePage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
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

  const seoData = generatePageSEO('careerGuidance', { path: '/career-guidance' });

  return (
    <div className="career-guidance-page">
      <SEOHead 
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={{
          "@context": "https://schema.org",
          "@type": "Service",
          "name": "Career Guidance Report",
          "description": "Professional career guidance based on Vedic astrology for job prospects and business success",
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
            <h1>🚀 Career Guidance Report</h1>
            <p>Get comprehensive insights about your career prospects, suitable fields, and professional timing</p>
          </div>

          {showForm ? (
            <div className="form-section">
              <div className="form-card">
                <h2>Enter Your Birth Details</h2>
                <p>Please provide your birth information to generate your career guidance report</p>
                <BirthForm onSubmit={handleFormSubmit} />
              </div>
            </div>
          ) : (
            <div className="analysis-section">
              <NativeSelector 
                birthData={birthData} 
                onNativeChange={() => window.location.reload()}
              />
              <CareerAnalysisTab chartData={chartData} birthDetails={birthData} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CareerGuidancePage;