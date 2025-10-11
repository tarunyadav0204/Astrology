import React, { useState, useEffect } from 'react';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './styles/mobile-fixes.css';
import BirthForm from './components/BirthForm/BirthForm';
import Dashboard from './components/Dashboard/Dashboard';
import PredictionsPage from './components/PredictionsPage/PredictionsPage';
import LandingPage from './components/LandingPage/LandingPage';
import ChartSelector from './components/ChartSelector/ChartSelector';
import UnifiedHeader from './components/UnifiedHeader/UnifiedHeader';
import { AstrologyProvider } from './context/AstrologyContext';
import { APP_CONFIG } from './config/app.config';
import { authService } from './services/authService';


function App() {
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('selector'); // selector, form, dashboard, predictions
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      try {
        // Try to use saved user data first
        const userData = JSON.parse(savedUser);
        setUser(userData);
        setLoading(false);
        
        // Verify token in background
        authService.getCurrentUser()
          .catch(() => {
            // If verification fails, clear auth and redirect to login
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setUser(null);
          });
      } catch {
        // If saved user data is corrupted, clear everything
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setCurrentView('selector');
  };

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>;
  }

  if (!user) {
    return (
      <>
        <LandingPage onLogin={handleLogin} onRegister={handleLogin} />
        <ToastContainer />
      </>
    );
  }

  return (
    <AstrologyProvider>
      <div style={{ 
        padding: currentView === 'dashboard' || currentView === 'predictions' || currentView === 'selector' ? '0' : (window.innerWidth <= 768 ? '10px' : '20px'), 
        maxWidth: currentView === 'dashboard' || currentView === 'predictions' || currentView === 'selector' ? '100vw' : '1200px', 
        margin: currentView === 'dashboard' || currentView === 'predictions' || currentView === 'selector' ? '0' : '0 auto',
        minHeight: '100vh',
        background: currentView === 'dashboard' || currentView === 'predictions' ? 'transparent' : 
                   currentView === 'selector' ? 'transparent' : 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 50%, #ffcc80 100%)',
        overflowX: 'hidden'
      }}>
        {currentView === 'selector' && (
          <ChartSelector 
            onSelectChart={() => setCurrentView('dashboard')} 
            onCreateNew={() => setCurrentView('form')} 
            onLogout={handleLogout} 
          />
        )}
        {currentView === 'form' && (
          <div>
            <UnifiedHeader
              onViewAllCharts={() => setCurrentView('selector')}
              onNewChart={() => setCurrentView('form')}
              onLogout={handleLogout}
              user={user}
            />
            <BirthForm onSubmit={() => setCurrentView('dashboard')} onLogout={handleLogout} />
          </div>
        )}
        {currentView === 'dashboard' && (
          <Dashboard 
            onBack={() => setCurrentView('selector')} 
            onViewAllCharts={() => {
              console.log('onViewAllCharts called in App.js');
              setCurrentView('selector');
            }}
            currentView={currentView} 
            setCurrentView={setCurrentView} 
            onLogout={handleLogout}
            user={user} 
          />
        )}
        {currentView === 'predictions' && (
          <PredictionsPage onBack={() => setCurrentView('selector')} currentView={currentView} setCurrentView={setCurrentView} onLogout={handleLogout} />
        )}
        <ToastContainer
          position={APP_CONFIG.ui.toast.position}
          autoClose={APP_CONFIG.ui.toast.duration}
          hideProgressBar={false}
          newestOnTop
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />

      </div>
    </AstrologyProvider>
  );
}

export default App;