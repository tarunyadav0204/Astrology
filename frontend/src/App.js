import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './styles/mobile-fixes.css';
import BirthForm from './components/BirthForm/BirthForm';
import Dashboard from './components/Dashboard/Dashboard';
import PredictionsPage from './components/PredictionsPage/PredictionsPage';
import LandingPage from './components/LandingPage/LandingPage';
import AstroVishnuLanding from './components/AstroVishnu/AstroVishnuLanding';
import LoginForm from './components/Auth/LoginForm';
import RegisterForm from './components/Auth/RegisterForm';
import ChartSelector from './components/ChartSelector/ChartSelector';
import UnifiedHeader from './components/UnifiedHeader/UnifiedHeader';
import UserPersonaHomePage from './user-persona/pages/SimpleHomePage';

import AstroRoshniHomepage from './components/AstroRoshniHomepage/AstroRoshniHomepage';
import HoroscopePage from './components/Horoscope/HoroscopePage';
import AstroRoshniPage from './components/AstroRoshni/AstroRoshniPage';
import MarriageAnalysisPage from './components/MarriageAnalysisPage/MarriageAnalysisPage';
import CareerGuidancePage from './components/CareerGuidancePage/CareerGuidancePage';
import PanchangPage from './components/Panchang/PanchangPage';
import MuhuratFinderPage from './components/MuhuratFinder/MuhuratFinderPage';
import AdminPanel from './components/Admin/AdminPanel';
import { AstrologyProvider } from './context/AstrologyContext';
import { APP_CONFIG } from './config/app.config';
import { authService } from './services/authService';
import { getCurrentDomainConfig, hasAccess, getRedirectUrl } from './config/domains.config';


function App() {
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('selector'); // user-home, selector, form, dashboard, predictions
  const [loading, setLoading] = useState(true);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [authView, setAuthView] = useState('login');

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      try {
        // Try to use saved user data first
        const userData = JSON.parse(savedUser);
        setUser(userData);
        
        // Check if user should be redirected based on domain
        const redirectUrl = getRedirectUrl(userData);
        if (redirectUrl) {
          window.location.href = redirectUrl;
          return;
        }
        
        // Set appropriate view based on domain configuration
        const domainConfig = getCurrentDomainConfig();
        
        if (domainConfig.userType === 'general') {
          setCurrentView('astroroshnihomepage'); // AstroRoshni domain shows homepage
        } else {
          setCurrentView('selector'); // AstroVishnu/other domains show chart selector
        }
        
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
    
    // Check if user should be redirected after login
    const redirectUrl = getRedirectUrl(userData);
    if (redirectUrl) {
      window.location.href = redirectUrl;
      return;
    }
    
    // Set appropriate view based on domain configuration
    const domainConfig = getCurrentDomainConfig();
    
    if (domainConfig.userType === 'general') {
      setCurrentView('astroroshnihomepage'); // AstroRoshni domain shows homepage
    } else {
      setCurrentView('selector'); // AstroVishnu/other domains show chart selector
    }
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
    setCurrentView('selector');
  };

  const handleAdminClick = () => {
    if (user && user.role === 'admin') {
      setCurrentView('admin');
    }
  };

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>;
  }

  // Show domain-specific page for non-authenticated users
  if (!user) {
    const domainConfig = getCurrentDomainConfig();
    
    return (
      <Router>
        <AstrologyProvider>
          <Routes>
            <Route path="/" element={
              domainConfig.userType === 'general' ? (
                <>
                  <AstroRoshniHomepage 
                    user={null} 
                    onLogin={() => setShowLoginModal(true)} 
                    showLoginButton={true} 
                  />
                  {showLoginModal && (
                    <div style={{
                      position: 'fixed',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      background: 'rgba(0,0,0,0.5)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      zIndex: 1000
                    }}>
                      <div style={{
                        background: 'white',
                        borderRadius: '15px',
                        padding: '30px',
                        maxWidth: '450px',
                        width: '90%',
                        position: 'relative'
                      }}>
                        <button 
                          onClick={() => setShowLoginModal(false)}
                          style={{
                            position: 'absolute',
                            top: '15px',
                            right: '15px',
                            background: 'none',
                            border: 'none',
                            fontSize: '24px',
                            cursor: 'pointer',
                            color: '#666'
                          }}
                        >
                          ×
                        </button>
                        <div style={{ marginBottom: '20px' }}>
                          <h2 style={{ textAlign: 'center', color: '#e91e63', marginBottom: '20px' }}>Welcome to AstroRoshni</h2>
                          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                            <button 
                              onClick={() => setAuthView('login')}
                              style={{
                                padding: '10px 20px',
                                border: 'none',
                                background: authView === 'login' ? '#e91e63' : 'transparent',
                                color: authView === 'login' ? 'white' : '#e91e63',
                                borderRadius: '25px 0 0 25px',
                                cursor: 'pointer',
                                borderRight: '1px solid #e91e63'
                              }}
                            >
                              Sign In
                            </button>
                            <button 
                              onClick={() => setAuthView('register')}
                              style={{
                                padding: '10px 20px',
                                border: 'none',
                                background: authView === 'register' ? '#e91e63' : 'transparent',
                                color: authView === 'register' ? 'white' : '#e91e63',
                                borderRadius: '0 25px 25px 0',
                                cursor: 'pointer'
                              }}
                            >
                              Sign Up
                            </button>
                          </div>
                        </div>
                        {authView === 'login' ? (
                          <LoginForm 
                            onLogin={(userData) => {
                              handleLogin(userData);
                              setShowLoginModal(false);
                            }} 
                            onSwitchToRegister={() => setAuthView('register')} 
                          />
                        ) : (
                          <RegisterForm 
                            onRegister={(userData) => {
                              handleLogin(userData);
                              setShowLoginModal(false);
                            }} 
                            onSwitchToLogin={() => setAuthView('login')} 
                          />
                        )}
                      </div>
                    </div>
                  )}
                </>
              ) : domainConfig.userType === 'software' ? (
                <>
                  <AstroVishnuLanding 
                    onLogin={() => {
                      setAuthView('login');
                      setShowLoginModal(true);
                    }} 
                    onRegister={() => {
                      setAuthView('register');
                      setShowLoginModal(true);
                    }} 
                  />
                  {showLoginModal && (
                    <div style={{
                      position: 'fixed',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      background: 'rgba(0,0,0,0.5)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      zIndex: 1000
                    }}>
                      <div style={{
                        background: 'white',
                        borderRadius: '15px',
                        padding: '30px',
                        maxWidth: '450px',
                        width: '90%',
                        position: 'relative'
                      }}>
                        <button 
                          onClick={() => setShowLoginModal(false)}
                          style={{
                            position: 'absolute',
                            top: '15px',
                            right: '15px',
                            background: 'none',
                            border: 'none',
                            fontSize: '24px',
                            cursor: 'pointer',
                            color: '#666'
                          }}
                        >
                          ×
                        </button>
                        <div style={{ marginBottom: '20px' }}>
                          <h2 style={{ textAlign: 'center', color: '#ff6b35', marginBottom: '20px' }}>Welcome to AstroVishnu</h2>
                          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                            <button 
                              onClick={() => setAuthView('login')}
                              style={{
                                padding: '10px 20px',
                                border: 'none',
                                background: authView === 'login' ? '#ff6b35' : 'transparent',
                                color: authView === 'login' ? 'white' : '#ff6b35',
                                borderRadius: '25px 0 0 25px',
                                cursor: 'pointer',
                                borderRight: '1px solid #ff6b35'
                              }}
                            >
                              Sign In
                            </button>
                            <button 
                              onClick={() => setAuthView('register')}
                              style={{
                                padding: '10px 20px',
                                border: 'none',
                                background: authView === 'register' ? '#ff6b35' : 'transparent',
                                color: authView === 'register' ? 'white' : '#ff6b35',
                                borderRadius: '0 25px 25px 0',
                                cursor: 'pointer'
                              }}
                            >
                              Sign Up
                            </button>
                          </div>
                        </div>
                        {authView === 'login' ? (
                          <LoginForm 
                            onLogin={(userData) => {
                              handleLogin(userData);
                              setShowLoginModal(false);
                            }} 
                            onSwitchToRegister={() => setAuthView('register')} 
                          />
                        ) : (
                          <RegisterForm 
                            onRegister={(userData) => {
                              handleLogin(userData);
                              setShowLoginModal(false);
                            }} 
                            onSwitchToLogin={() => setAuthView('login')} 
                          />
                        )}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <LandingPage onLogin={handleLogin} onRegister={handleLogin} domainConfig={domainConfig} />
              )
            } />
            <Route path="/horoscope/:period" element={<HoroscopePage />} />
            <Route path="/marriage-analysis" element={
              <>
                <AstroRoshniHomepage 
                  user={null} 
                  onLogin={() => setShowLoginModal(true)} 
                  showLoginButton={true} 
                />
                {showLoginModal && (
                  <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0,0,0,0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000
                  }}>
                    <div style={{
                      background: 'white',
                      borderRadius: '15px',
                      padding: '30px',
                      maxWidth: '450px',
                      width: '90%',
                      position: 'relative'
                    }}>
                      <button 
                        onClick={() => setShowLoginModal(false)}
                        style={{
                          position: 'absolute',
                          top: '15px',
                          right: '15px',
                          background: 'none',
                          border: 'none',
                          fontSize: '24px',
                          cursor: 'pointer',
                          color: '#666'
                        }}
                      >
                        ×
                      </button>
                      <div style={{ marginBottom: '20px' }}>
                        <h2 style={{ textAlign: 'center', color: '#e91e63', marginBottom: '10px' }}>Login Required</h2>
                        <p style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>Please login to access Marriage Analysis</p>
                        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                          <button 
                            onClick={() => setAuthView('login')}
                            style={{
                              padding: '10px 20px',
                              border: 'none',
                              background: authView === 'login' ? '#e91e63' : 'transparent',
                              color: authView === 'login' ? 'white' : '#e91e63',
                              borderRadius: '25px 0 0 25px',
                              cursor: 'pointer',
                              borderRight: '1px solid #e91e63'
                            }}
                          >
                            Sign In
                          </button>
                          <button 
                            onClick={() => setAuthView('register')}
                            style={{
                              padding: '10px 20px',
                              border: 'none',
                              background: authView === 'register' ? '#e91e63' : 'transparent',
                              color: authView === 'register' ? 'white' : '#e91e63',
                              borderRadius: '0 25px 25px 0',
                              cursor: 'pointer'
                            }}
                          >
                            Sign Up
                          </button>
                        </div>
                      </div>
                      {authView === 'login' ? (
                        <LoginForm 
                          onLogin={(userData) => {
                            handleLogin(userData);
                            setShowLoginModal(false);
                            window.location.href = '/marriage-analysis';
                          }} 
                          onSwitchToRegister={() => setAuthView('register')} 
                        />
                      ) : (
                        <RegisterForm 
                          onRegister={(userData) => {
                            handleLogin(userData);
                            setShowLoginModal(false);
                            window.location.href = '/marriage-analysis';
                          }} 
                          onSwitchToLogin={() => setAuthView('login')} 
                        />
                      )}
                    </div>
                  </div>
                )}
              </>
            } />
            <Route path="/career-guidance" element={
              <>
                <AstroRoshniHomepage 
                  user={null} 
                  onLogin={() => setShowLoginModal(true)} 
                  showLoginButton={true} 
                />
                {showLoginModal && (
                  <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0,0,0,0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000
                  }}>
                    <div style={{
                      background: 'white',
                      borderRadius: '15px',
                      padding: '30px',
                      maxWidth: '450px',
                      width: '90%',
                      position: 'relative'
                    }}>
                      <button 
                        onClick={() => setShowLoginModal(false)}
                        style={{
                          position: 'absolute',
                          top: '15px',
                          right: '15px',
                          background: 'none',
                          border: 'none',
                          fontSize: '24px',
                          cursor: 'pointer',
                          color: '#666'
                        }}
                      >
                        ×
                      </button>
                      <div style={{ marginBottom: '20px' }}>
                        <h2 style={{ textAlign: 'center', color: '#e91e63', marginBottom: '10px' }}>Login Required</h2>
                        <p style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>Please login to access Career Guidance</p>
                        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                          <button 
                            onClick={() => setAuthView('login')}
                            style={{
                              padding: '10px 20px',
                              border: 'none',
                              background: authView === 'login' ? '#e91e63' : 'transparent',
                              color: authView === 'login' ? 'white' : '#e91e63',
                              borderRadius: '25px 0 0 25px',
                              cursor: 'pointer',
                              borderRight: '1px solid #e91e63'
                            }}
                          >
                            Sign In
                          </button>
                          <button 
                            onClick={() => setAuthView('register')}
                            style={{
                              padding: '10px 20px',
                              border: 'none',
                              background: authView === 'register' ? '#e91e63' : 'transparent',
                              color: authView === 'register' ? 'white' : '#e91e63',
                              borderRadius: '0 25px 25px 0',
                              cursor: 'pointer'
                            }}
                          >
                            Sign Up
                          </button>
                        </div>
                      </div>
                      {authView === 'login' ? (
                        <LoginForm 
                          onLogin={(userData) => {
                            handleLogin(userData);
                            setShowLoginModal(false);
                            window.location.href = '/career-guidance';
                          }} 
                          onSwitchToRegister={() => setAuthView('register')} 
                        />
                      ) : (
                        <RegisterForm 
                          onRegister={(userData) => {
                            handleLogin(userData);
                            setShowLoginModal(false);
                            window.location.href = '/career-guidance';
                          }} 
                          onSwitchToLogin={() => setAuthView('login')} 
                        />
                      )}
                    </div>
                  </div>
                )}
              </>
            } />
            <Route path="/panchang" element={
              <>
                <AstroRoshniHomepage 
                  user={null} 
                  onLogin={() => setShowLoginModal(true)} 
                  showLoginButton={true} 
                />
                {showLoginModal && (
                  <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0,0,0,0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000
                  }}>
                    <div style={{
                      background: 'white',
                      borderRadius: '15px',
                      padding: '30px',
                      maxWidth: '450px',
                      width: '90%',
                      position: 'relative'
                    }}>
                      <button 
                        onClick={() => setShowLoginModal(false)}
                        style={{
                          position: 'absolute',
                          top: '15px',
                          right: '15px',
                          background: 'none',
                          border: 'none',
                          fontSize: '24px',
                          cursor: 'pointer',
                          color: '#666'
                        }}
                      >
                        ×
                      </button>
                      <div style={{ marginBottom: '20px' }}>
                        <h2 style={{ textAlign: 'center', color: '#e91e63', marginBottom: '10px' }}>Login Required</h2>
                        <p style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>Please login to access Panchang</p>
                        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                          <button 
                            onClick={() => setAuthView('login')}
                            style={{
                              padding: '10px 20px',
                              border: 'none',
                              background: authView === 'login' ? '#e91e63' : 'transparent',
                              color: authView === 'login' ? 'white' : '#e91e63',
                              borderRadius: '25px 0 0 25px',
                              cursor: 'pointer',
                              borderRight: '1px solid #e91e63'
                            }}
                          >
                            Sign In
                          </button>
                          <button 
                            onClick={() => setAuthView('register')}
                            style={{
                              padding: '10px 20px',
                              border: 'none',
                              background: authView === 'register' ? '#e91e63' : 'transparent',
                              color: authView === 'register' ? 'white' : '#e91e63',
                              borderRadius: '0 25px 25px 0',
                              cursor: 'pointer'
                            }}
                          >
                            Sign Up
                          </button>
                        </div>
                      </div>
                      {authView === 'login' ? (
                        <LoginForm 
                          onLogin={(userData) => {
                            handleLogin(userData);
                            setShowLoginModal(false);
                            window.location.href = '/panchang';
                          }} 
                          onSwitchToRegister={() => setAuthView('register')} 
                        />
                      ) : (
                        <RegisterForm 
                          onRegister={(userData) => {
                            handleLogin(userData);
                            setShowLoginModal(false);
                            window.location.href = '/panchang';
                          }} 
                          onSwitchToLogin={() => setAuthView('login')} 
                        />
                      )}
                    </div>
                  </div>
                )}
              </>
            } />
            <Route path="/muhurat-finder" element={
              <>
                <AstroRoshniHomepage 
                  user={null} 
                  onLogin={() => setShowLoginModal(true)} 
                  showLoginButton={true} 
                />
                {showLoginModal && (
                  <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0,0,0,0.5)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000
                  }}>
                    <div style={{
                      background: 'white',
                      borderRadius: '15px',
                      padding: '30px',
                      maxWidth: '450px',
                      width: '90%',
                      position: 'relative'
                    }}>
                      <button 
                        onClick={() => setShowLoginModal(false)}
                        style={{
                          position: 'absolute',
                          top: '15px',
                          right: '15px',
                          background: 'none',
                          border: 'none',
                          fontSize: '24px',
                          cursor: 'pointer',
                          color: '#666'
                        }}
                      >
                        ×
                      </button>
                      <div style={{ marginBottom: '20px' }}>
                        <h2 style={{ textAlign: 'center', color: '#e91e63', marginBottom: '10px' }}>Login Required</h2>
                        <p style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>Please login to access Muhurat Finder</p>
                        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                          <button 
                            onClick={() => setAuthView('login')}
                            style={{
                              padding: '10px 20px',
                              border: 'none',
                              background: authView === 'login' ? '#e91e63' : 'transparent',
                              color: authView === 'login' ? 'white' : '#e91e63',
                              borderRadius: '25px 0 0 25px',
                              cursor: 'pointer',
                              borderRight: '1px solid #e91e63'
                            }}
                          >
                            Sign In
                          </button>
                          <button 
                            onClick={() => setAuthView('register')}
                            style={{
                              padding: '10px 20px',
                              border: 'none',
                              background: authView === 'register' ? '#e91e63' : 'transparent',
                              color: authView === 'register' ? 'white' : '#e91e63',
                              borderRadius: '0 25px 25px 0',
                              cursor: 'pointer'
                            }}
                          >
                            Sign Up
                          </button>
                        </div>
                      </div>
                      {authView === 'login' ? (
                        <LoginForm 
                          onLogin={(userData) => {
                            handleLogin(userData);
                            setShowLoginModal(false);
                            window.location.href = '/muhurat-finder';
                          }} 
                          onSwitchToRegister={() => setAuthView('register')} 
                        />
                      ) : (
                        <RegisterForm 
                          onRegister={(userData) => {
                            handleLogin(userData);
                            setShowLoginModal(false);
                            window.location.href = '/muhurat-finder';
                          }} 
                          onSwitchToLogin={() => setAuthView('login')} 
                        />
                      )}
                    </div>
                  </div>
                )}
              </>
            } />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <ToastContainer />
        </AstrologyProvider>
      </Router>
    );
  }

  return (
    <Router>
      <AstrologyProvider>
        <Routes>
          <Route path="/horoscope/:period" element={<HoroscopePage />} />
          <Route path="/marriage-analysis" element={
            <MarriageAnalysisPage 
              user={user} 
              onLogout={handleLogout} 
              onAdminClick={handleAdminClick} 
            />
          } />
          <Route path="/career-guidance" element={
            <CareerGuidancePage 
              user={user} 
              onLogout={handleLogout} 
              onAdminClick={handleAdminClick} 
            />
          } />
          <Route path="/panchang" element={
            <PanchangPage 
              user={user} 
              onLogout={handleLogout} 
              onAdminClick={handleAdminClick} 
            />
          } />
          <Route path="/muhurat-finder" element={
            <MuhuratFinderPage 
              user={user} 
              onLogout={handleLogout} 
              onAdminClick={handleAdminClick} 
            />
          } />

          <Route path="/astroroshni" element={<AstroRoshniPage />} />
          <Route path="/*" element={
            <div style={{ 
              padding: currentView === 'dashboard' || currentView === 'predictions' || currentView === 'selector' || currentView === 'user-home' || currentView === 'astroroshnihomepage' || currentView === 'admin' ? '0' : (window.innerWidth <= 768 ? '10px' : '20px'), 
              maxWidth: currentView === 'dashboard' || currentView === 'predictions' || currentView === 'selector' || currentView === 'user-home' || currentView === 'astroroshnihomepage' || currentView === 'admin' ? '100vw' : '1200px', 
              margin: currentView === 'dashboard' || currentView === 'predictions' || currentView === 'selector' || currentView === 'user-home' || currentView === 'astroroshnihomepage' || currentView === 'admin' ? '0' : '0 auto',
              minHeight: '100vh',
              background: currentView === 'dashboard' || currentView === 'predictions' ? 'transparent' : 
                         currentView === 'selector' || currentView === 'user-home' || currentView === 'astroroshnihomepage' || currentView === 'admin' ? 'transparent' : 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 50%, #ffcc80 100%)',
              overflowX: 'hidden',
              width: '100%'
            }}>

        {currentView === 'astroroshnihomepage' && (
          <AstroRoshniHomepage user={user} onLogout={handleLogout} onAdminClick={handleAdminClick} />
        )}
        {currentView === 'admin' && (
          <AdminPanel user={user} onLogout={handleLogout} />
        )}
        {currentView === 'selector' && (
          <ChartSelector 
            onSelectChart={() => setCurrentView('dashboard')} 
            onCreateNew={() => setCurrentView('form')} 
            onLogout={handleLogout}
            onAdminClick={handleAdminClick}
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