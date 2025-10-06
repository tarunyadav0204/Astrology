import React, { useState, useEffect } from 'react';

const InstallPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showInstall, setShowInstall] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstall(true);
    };

    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      setShowInstall(false);
    }
    setDeferredPrompt(null);
  };

  if (!showInstall) return null;

  return (
    <div style={{
      position: 'fixed',
      bottom: '20px',
      left: '20px',
      right: '20px',
      background: '#e91e63',
      color: 'white',
      padding: '15px',
      borderRadius: '10px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      zIndex: 1000,
      boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
    }}>
      <span>📱 Install this app for better experience!</span>
      <div>
        <button 
          onClick={handleInstall}
          style={{
            background: 'white',
            color: '#e91e63',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '5px',
            marginRight: '10px',
            fontWeight: 'bold'
          }}
        >
          Install
        </button>
        <button 
          onClick={() => setShowInstall(false)}
          style={{
            background: 'transparent',
            color: 'white',
            border: '1px solid white',
            padding: '8px 16px',
            borderRadius: '5px'
          }}
        >
          Later
        </button>
      </div>
    </div>
  );
};

export default InstallPrompt;