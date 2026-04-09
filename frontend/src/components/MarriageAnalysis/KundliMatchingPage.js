import React from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import CompatibilityAnalysis from './CompatibilityAnalysis';
import { useAstrology } from '../../context/AstrologyContext';
import './KundliMatchingPage.css';

const KundliMatchingPage = ({
  user,
  onLogout,
  onAdminClick,
  onLogin,
  showLoginButton = true
}) => {
  const navigate = useNavigate();
  const { birthData } = useAstrology();

  const handleAdmin = () => {
    if (onAdminClick) onAdminClick();
  };

  return (
    <div className="kundli-matching-page">
      <SEOHead
        title="Kundli Matching (Ashtakoot Guna Milan) | AstroRoshni"
        description="Traditional 36-point Ashtakoot compatibility (Guna Milan) for two birth charts — Vedic marriage matching."
        keywords="kundli matching, ashtakoot, guna milan, horoscope matching, marriage compatibility, vedic matching"
        canonical="https://astroroshni.com/kundli-matching"
      />
      <NavigationHeader
        compact
        showZodiacSelector={false}
        user={user}
        onAdminClick={handleAdmin}
        onLogout={onLogout}
        birthData={birthData}
        onChangeNative={() => navigate('/')}
        onCreditsClick={() => navigate('/credits')}
        onLogin={onLogin}
        showLoginButton={showLoginButton}
      />
      <main className="kundli-matching-main">
        <header className="kundli-matching-hero">
          <button type="button" className="kundli-matching-back" onClick={() => navigate(-1)}>
            ← Back
          </button>
          <h1>Kundli matching</h1>
          <p className="kundli-matching-sub">
            Ashtakoot Guna Milan and detailed compatibility for two charts (logged-in users).
          </p>
        </header>
        <div className="kundli-matching-panel">
          <CompatibilityAnalysis user={user} onLogin={onLogin} />
        </div>
      </main>
    </div>
  );
};

export default KundliMatchingPage;
