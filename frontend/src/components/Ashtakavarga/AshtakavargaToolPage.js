import React, { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAstrology } from '../../context/AstrologyContext';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import AshtakavargaModal from './AshtakavargaModal';
import './AshtakavargaModal.css';

/**
 * Full-page Ashtakavarga (same UI as chart modal) for mobile web parity and future “tools hub” routes.
 */
function AshtakavargaToolPage({ user, onLogout, onAdminClick, onLogin }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { birthData } = useAstrology();
  const [showBirthModal, setShowBirthModal] = useState(false);
  const transitDate = useMemo(() => new Date().toISOString().split('T')[0], []);
  const initialActiveTab = location.state?.initialActiveTab || 'matrix';

  const handleBack = () => {
    navigate('/ashtakavarga');
  };

  return (
    <div className="ashtakavarga-tool-page-root">
      <ModernNavigationHeader
        sticky
        user={user}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
        onLogin={onLogin}
      />
      <header className="ashtakavarga-tool-masthead">
        <button type="button" className="ashtakavarga-tool-back" onClick={handleBack}>
          <span aria-hidden>←</span> Back to Ashtakavarga
        </button>
        <div className="ashtakavarga-tool-masthead__copy">
          <span>Chart strength workspace</span>
          <h1>Ashtakavarga</h1>
          <p>{birthData?.name ? `Reading the bindu field for ${birthData.name}.` : 'Begin with an accurate sidereal birth chart.'}</p>
        </div>
      </header>
      {birthData ? (
        <AshtakavargaModal
          variant="page"
          isOpen
          onClose={handleBack}
          birthData={birthData}
          chartType="lagna"
          transitDate={transitDate}
          onLogin={onLogin}
          initialActiveTab={initialActiveTab}
        />
      ) : (
        <div className="ashtakavarga-tool-empty">
          <p className="ashtakavarga-tool-empty__title">Ashtakavarga</p>
          <p className="ashtakavarga-tool-empty__text">
            Add your birth date, time, and place to compute Sarvashtakavarga, planetary BAV, transits, and timing notes.
          </p>
          <button type="button" className="ashtakavarga-tool-empty__btn" onClick={() => setShowBirthModal(true)}>
            Enter birth details
          </button>
        </div>
      )}
      <BirthFormModal
        isOpen={showBirthModal}
        onClose={() => setShowBirthModal(false)}
        onSubmit={() => setShowBirthModal(false)}
        title="Birth details for Ashtakavarga"
        description="Accurate sidereal chart data is required for bindus and transit comparisons."
      />
    </div>
  );
}

export default AshtakavargaToolPage;
