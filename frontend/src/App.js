import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './styles/mobile-fixes.css';
import BirthForm from './components/BirthForm/BirthForm';
import Dashboard from './components/Dashboard/Dashboard';
import PredictionsPage from './components/PredictionsPage/PredictionsPage';
import LandingPage from './components/LandingPage/LandingPage';
import ChartSelector from './components/ChartSelector/ChartSelector';
import UnifiedHeader from './components/UnifiedHeader/UnifiedHeader';
import UserPersonaHomePage from './user-persona/pages/SimpleHomePage';
import InvestorHomepage from './components/Homepage/InvestorHomepage';
import HoroscopePage from './components/Horoscope/HoroscopePage';
import AstroRoshniPage from './components/AstroRoshni/AstroRoshniPage';
import { AstrologyProvider } from './context/AstrologyContext';
import { APP_CONFIG } from './config/app.config';
import { authService } from './services/authService';


function App() {
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('selector'); // user-home, selector, form, dashboard, predictions
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

  // Show landing page for non-authenticated users
  if (!user) {
    return (
      <Router>
        <Routes>
          <Route path="/" element={
            <LandingPage onLogin={handleLogin} onRegister={handleLogin} />
          } />
          <Route path="/horoscope/:period" element={<HoroscopePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <ToastContainer />
      </Router>
    );
  }

  return (
    <Router>
      <AstrologyProvider>
        <Routes>
          <Route path="/horoscope/:period" element={<HoroscopePage />} />
          <Route path="/investor" element={<InvestorHomepage />} />
          <Route path="/astroroshni" element={<AstroRoshniPage />} />
          <Route path="/*" element={
            <div style={{ 
              padding: currentView === 'dashboard' || currentView === 'predictions' || currentView === 'selector' || currentView === 'user-home' ? '0' : (window.innerWidth <= 768 ? '10px' : '20px'), 
              maxWidth: currentView === 'dashboard' || currentView === 'predictions' || currentView === 'selector' || currentView === 'user-home' ? '100vw' : '1200px', 
              margin: currentView === 'dashboard' || currentView === 'predictions' || currentView === 'selector' || currentView === 'user-home' ? '0' : '0 auto',
              minHeight: '100vh',
              background: currentView === 'dashboard' || currentView === 'predictions' ? 'transparent' : 
                         currentView === 'selector' || currentView === 'user-home' ? 'transparent' : 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 50%, #ffcc80 100%)',
              overflowX: 'hidden',
              width: '100%'
            }}>
        {currentView === 'user-home' && (
          <InvestorHomepage onGetStarted={() => setCurrentView('selector')} />
        )}
        {currentView === 'selector' && (
          <ChartSelector 
            onSelectChart={() => setCurrentView('dashboard')} 
            onCreateNew={() => setCurrentView('form')} 
            onLogout={handleLogout}
            onBackToUserHome={() => setCurrentView('user-home')}
            user={user}
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
          } />
        </Routes>
      </AstrologyProvider>
    </Router>
  );
}

export default App;