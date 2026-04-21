import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAstrology } from '../../context/AstrologyContext';
import NavigationHeader from '../Shared/NavigationHeader';
import BirthFormModal from '../BirthForm/BirthFormModal';
import CreditsModal from '../Credits/CreditsModal';
import AshtakavargaModal from './AshtakavargaModal';
import './AshtakavargaModal.css';

/**
 * Full-page Ashtakavarga (same UI as chart modal) for mobile web parity and future “tools hub” routes.
 */
function AshtakavargaToolPage({ user, onLogout, onAdminClick, onLogin }) {
  const navigate = useNavigate();
  const { birthData } = useAstrology();
  const [showBirthModal, setShowBirthModal] = useState(false);
  const [showCreditsModal, setShowCreditsModal] = useState(false);
  const transitDate = useMemo(() => new Date().toISOString().split('T')[0], []);

  const handleBack = () => {
    if (typeof window !== 'undefined' && window.history.length > 1) {
      navigate(-1);
    } else {
      navigate('/');
    }
  };

  return (
    <div className="ashtakavarga-tool-page-root">
      <NavigationHeader
        compact
        showZodiacSelector={false}
        user={user}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
        onLogin={onLogin}
        showLoginButton={!user}
        onCreditsClick={() => setShowCreditsModal(true)}
        birthData={birthData}
        onChangeNative={() => setShowBirthModal(true)}
        onHomeClick={() => navigate('/')}
      />
      {birthData ? (
        <AshtakavargaModal
          variant="page"
          isOpen
          onClose={handleBack}
          birthData={birthData}
          chartType="lagna"
          transitDate={transitDate}
          onLogin={onLogin}
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
      <CreditsModal isOpen={showCreditsModal} onClose={() => setShowCreditsModal(false)} onLogin={onLogin} />
    </div>
  );
}

export default AshtakavargaToolPage;
