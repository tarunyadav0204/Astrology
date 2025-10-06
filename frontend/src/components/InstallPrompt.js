import React, { useState, useEffect } from 'react';

const InstallPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showInstall, setShowInstall] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstall(true);
    };

    window.addEventListener('beforeinstallprompt', handler);
    
    // Show fallback install prompt after 3 seconds if no PWA prompt
    const timer = setTimeout(() => {
      if (!deferredPrompt && !dismissed) {
        setShowInstall(true);
      }
    }, 3000);
    
    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      clearTimeout(timer);
    };
  }, [deferredPrompt, dismissed]);

  const handleInstall = async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      
      if (outcome === 'accepted') {
        setShowInstall(false);
      }
      setDeferredPrompt(null);
    } else {
      // Fallback: Show manual instructions
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
      const isAndroid = /Android/.test(navigator.userAgent);
      
      if (isIOS) {
        alert('To install: Tap the Share button (⬆️) at the bottom, then "Add to Home Screen"');
      } else if (isAndroid) {
        alert('To install: Tap the menu (⋮) in your browser, then "Add to Home screen" or "Install app"');
      } else {
        alert('To install: Look for the install icon in your browser\'s address bar or menu');
      }
      setShowInstall(false);
    }
  };
  
  const handleDismiss = () => {
    setShowInstall(false);
    setDismissed(true);
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
          onClick={handleDismiss}
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