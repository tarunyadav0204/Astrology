// deploy.sh: any change under frontend/ sets needs_frontend_build so the VM runs npm run build.
// deploy.yml builds and ships the frontend artifact when files under frontend/ change.
import React, { useState, useEffect, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import { HelmetProvider } from 'react-helmet-async';
import AnalyticsTracker from './components/Analytics/AnalyticsTracker';
import RouteSEO from './components/SEO/RouteSEO';
import 'react-toastify/dist/ReactToastify.css';
import './styles/mobile-fixes.css';
import LandingPage from './components/LandingPage/LandingPage';
import AstroVishnuLanding from './components/AstroVishnu/AstroVishnuLanding';
import LoginForm from './components/Auth/LoginForm';
import RegisterForm from './components/Auth/RegisterForm';
import AuthModalShell from './components/Auth/AuthModalShell';
import FloatingChatButton from './components/FloatingChatButton/FloatingChatButton';
import { AstrologyProvider } from './context/AstrologyContext';
import { CreditProvider } from './context/CreditContext';
import { APP_CONFIG } from './config/app.config';
import { authService } from './services/authService';
import { getCurrentDomainConfig, getRedirectUrl } from './config/domains.config';

// When the static frontend is served from a GCS bucket/backend bucket, direct
// deep links can arrive as "/path/index.html". Normalize those URLs before the
// router mounts so React Router matches the clean application route.
if (typeof window !== 'undefined') {
  const { pathname, search, hash } = window.location;
  if (pathname !== '/index.html' && pathname.endsWith('/index.html')) {
    const normalizedPath = pathname.slice(0, -'/index.html'.length) || '/';
    window.history.replaceState(null, '', `${normalizedPath}${search}${hash}`);
  }
}

/** Shown briefly while lazy route chunks load (code-splitting). */
function RoutePageFallback() {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '40vh',
        padding: '24px',
        color: '#666',
        fontFamily: 'system-ui, -apple-system, Segoe UI, sans-serif',
        fontSize: '14px',
      }}
    >
      Loading…
    </div>
  );
}

/** Auth sheet for Vedic analysis routes when the guest taps Sign in / Create account on the tool page. */
function AnalysisGuestAuthModal({ isOpen, onClose, authView, setAuthView, description, onAuthenticated }) {
  return (
    <AuthModalShell isOpen={isOpen} onClose={onClose}>
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ textAlign: 'center', color: '#e91e63', marginBottom: '10px' }}>Sign in</h2>
        <p style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>{description}</p>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
          <button
            type="button"
            onClick={() => setAuthView('login')}
            style={{
              padding: '10px 20px',
              border: 'none',
              background: authView === 'login' ? '#e91e63' : 'transparent',
              color: authView === 'login' ? 'white' : '#e91e63',
              borderRadius: '25px 0 0 25px',
              cursor: 'pointer',
              borderRight: '1px solid #e91e63',
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => setAuthView('register')}
            style={{
              padding: '10px 20px',
              border: 'none',
              background: authView === 'register' ? '#e91e63' : 'transparent',
              color: authView === 'register' ? 'white' : '#e91e63',
              borderRadius: '0 25px 25px 0',
              cursor: 'pointer',
            }}
          >
            Sign Up
          </button>
        </div>
      </div>
      {authView === 'login' ? (
        <LoginForm
          onLogin={(userData) => {
            onAuthenticated(userData);
            onClose();
          }}
          onSwitchToRegister={() => setAuthView('register')}
        />
      ) : (
        <RegisterForm
          onRegister={(userData) => {
            onAuthenticated(userData);
            onClose();
          }}
          onSwitchToLogin={() => setAuthView('login')}
        />
      )}
    </AuthModalShell>
  );
}

const AstroRoshniHomepage = lazy(() => import('./components/AstroRoshniHomepage/AstroRoshniHomepage'));
const AdminPanel = lazy(() => import('./components/Admin/AdminPanel'));
const ChartSelector = lazy(() => import('./components/ChartSelector/ChartSelector'));
const BirthFormModal = lazy(() => import('./components/BirthForm/BirthFormModal'));
const BirthChartCreationPage = lazy(() => import('./components/BirthChart/BirthChartCreationPage'));
const ChartsDashasWorkspacePage = lazy(() => import('./components/BirthChart/ChartsDashasWorkspacePage'));
const Dashboard = lazy(() => import('./components/Dashboard/Dashboard'));
const PredictionsPage = lazy(() => import('./components/PredictionsPage/PredictionsPage'));
const PanchangPage = lazy(() => import('./components/Panchang/PanchangPage'));
const HoroscopePage = lazy(() => import('./components/Horoscope/HoroscopePage'));
const AstroRoshniPage = lazy(() => import('./components/AstroRoshni/AstroRoshniPage'));
const AnalysisDetailPage = lazy(() => import('./components/Analysis/AnalysisDetailPage'));
const MuhuratFinderPage = lazy(() => import('./components/MuhuratFinder/MuhuratFinderPage'));
const ChatPage = lazy(() => import('./components/Chat/ChatPage'));
const SpeechChatPage = lazy(() => import('./components/Chat/SpeechChatPage'));
const MythsVsReality = lazy(() => import('./components/Education/MythsVsReality'));
const AdvancedCourses = lazy(() => import('./components/Education/AdvancedCourses'));
const BeginnersGuide = lazy(() => import('./components/Education/BeginnersGuide'));
const LessonPage = lazy(() => import('./components/Education/Lessons/LessonPage'));
const NakshatraPage = lazy(() => import('./components/Nakshatra/NakshatraPage'));
const NakshatraListPage = lazy(() => import('./components/Nakshatra/NakshatraListPage'));
const MonthlyPanchangPage = lazy(() => import('./components/MonthlyPanchang/MonthlyPanchangPage'));
const FestivalsPage = lazy(() => import('./components/Festivals/FestivalsPage'));
const MonthlyFestivalsPage = lazy(() => import('./components/Festivals/MonthlyFestivalsPage'));
const KarmaAnalysis = lazy(() => import('./components/KarmaAnalysis/KarmaAnalysis'));
const SubscriptionPage = lazy(() => import('./components/Subscription/SubscriptionPage'));
const OrderManagementPage = lazy(() => import('./components/OrderManagement/OrderManagementPage'));
const ProfilePage = lazy(() => import('./components/Profile/ProfilePage'));
const PolicyPage = lazy(() => import('./components/Policy/PolicyPage'));
const TermsPage = lazy(() => import('./components/Policy/TermsPage'));
const DeleteAccountPage = lazy(() => import('./components/Policy/DeleteAccountPage'));
const ContactPage = lazy(() => import('./components/Contact/ContactPage'));
const AboutUs = lazy(() => import('./components/About/AboutUs'));
const Calendar2026 = lazy(() => import('./components/Calendar2026/Calendar2026'));
const AstroVastuTool = lazy(() => import('./components/AstroVastu/AstroVastuTool'));
const KundliMatchingPage = lazy(() => import('./components/MarriageAnalysis/KundliMatchingPage'));
const EventsTimelinePage = lazy(() => import('./components/Events/EventsTimelinePage'));
const AshtakavargaSeoPage = lazy(() => import('./components/Ashtakavarga/AshtakavargaSeoPage'));
const AshtakavargaToolPage = lazy(() => import('./components/Ashtakavarga/AshtakavargaToolPage'));
const BlogList = lazy(() => import('./components/Blog/BlogList'));
const BlogPost = lazy(() => import('./components/Blog/BlogPost'));
const BlogDashboard = lazy(() => import('./components/Blog/BlogDashboard'));

/** Hide “Ask Tara” FAB on full-page chat and dedicated tool pages (e.g. Ashtakavarga) where it overlaps the UI. */
function FloatingChatButtonUnlessOnChatPage({ user, onRequireLogin }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  if (pathname === '/chat' || pathname === '/speech-chat' || pathname.startsWith('/tools/')) return null;
  const handleOpenChat = () => {
    if (user) {
      navigate('/chat?app=1');
    } else if (onRequireLogin) {
      onRequireLogin();
    }
  };
  return <FloatingChatButton onOpenChat={handleOpenChat} />;
}

function ChatRouteGate({ children }) {
  const location = useLocation();
  const isAppRoute = new URLSearchParams(location.search).get('app') === '1';

  useEffect(() => {
    if (process.env.NODE_ENV === 'production' && !isAppRoute) {
      window.location.replace('/chat');
    }
  }, [isAppRoute]);

  if (process.env.NODE_ENV === 'production' && !isAppRoute) {
    return null;
  }

  return children;
}

/** Logged-in shell for chart selector, dashboard, and marketing home — only at `/`. */
function AuthenticatedRootShell({
  currentView,
  user,
  setCurrentView,
  onLogout,
  onAdminClick,
  onLogin,
  goToDomainHome,
}) {
  const location = useLocation();
  if (location.pathname !== '/') {
    return null;
  }

  const isFullBleed =
    currentView === 'dashboard' ||
    currentView === 'predictions' ||
    currentView === 'selector' ||
    currentView === 'user-home' ||
    currentView === 'astroroshnihomepage' ||
    currentView === 'admin';

  return (
    <div
      style={{
        padding: isFullBleed ? '0' : (window.innerWidth <= 768 ? '10px' : '20px'),
        maxWidth: isFullBleed ? '100vw' : '1200px',
        margin: isFullBleed ? '0' : '0 auto',
        minHeight: '100vh',
        background:
          currentView === 'dashboard' || currentView === 'predictions'
            ? 'transparent'
            : currentView === 'selector' ||
                currentView === 'user-home' ||
                currentView === 'astroroshnihomepage' ||
                currentView === 'admin'
              ? 'transparent'
              : 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 50%, #ffcc80 100%)',
        overflowX: 'hidden',
        width: '100%',
      }}
    >
      {currentView === 'astroroshnihomepage' && (
        <AstroRoshniHomepage
          user={user}
          onLogout={onLogout}
          onAdminClick={onAdminClick}
          onLogin={onLogin}
          setCurrentView={setCurrentView}
        />
      )}
      {currentView === 'admin' && (
        <AdminPanel
          user={user}
          onLogout={onLogout}
          onAdminClick={() => setCurrentView('astroroshnihomepage')}
          onLogin={onLogin}
          showLoginButton={false}
          onHomeClick={() => setCurrentView('astroroshnihomepage')}
        />
      )}
      {currentView === 'selector' && (
        <ChartSelector
          onSelectChart={() => setCurrentView('dashboard')}
          onCreateNew={() => setCurrentView('form')}
          onLogout={onLogout}
          onAdminClick={onAdminClick}
          onBackToUserHome={() => setCurrentView('user-home')}
          user={user}
        />
      )}
      {currentView === 'form' && (
        <BirthFormModal
          isOpen={true}
          onClose={() => setCurrentView('dashboard')}
          onSubmit={() => setCurrentView('dashboard')}
          title="Enter Birth Details"
          description="Please provide your birth information to generate your chart"
        />
      )}
      {currentView === 'dashboard' && (
        <Dashboard
          onBack={goToDomainHome}
          onViewAllCharts={goToDomainHome}
          onNewChart={() => setCurrentView('form')}
          currentView={currentView}
          setCurrentView={setCurrentView}
          onLogout={onLogout}
          user={user}
        />
      )}
      {currentView === 'predictions' && (
        <PredictionsPage
          onBack={() => setCurrentView('selector')}
          currentView={currentView}
          setCurrentView={setCurrentView}
          onLogout={onLogout}
        />
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
  );
}

//Harmless touch
function App() {
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('selector'); // user-home, selector, form, dashboard, predictions
  /** When false, first paint matches prerendered / (no token). When true, session restore runs before UI (see index.js). */
  const [loading, setLoading] = useState(() => {
    try {
      return !!localStorage.getItem('token');
    } catch {
      return false;
    }
  });
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [authView, setAuthView] = useState('login');

  const clearAstrologySessionCache = () => {
    localStorage.removeItem('astrology_birth_data');
    localStorage.removeItem('astrology_chart_data');
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      try {
        const userData = JSON.parse(savedUser);

        const applyAuthenticatedSession = (activeUser) => {
          setUser(activeUser);
          localStorage.setItem('user', JSON.stringify(activeUser));

          const redirectUrl = getRedirectUrl(activeUser);
          if (redirectUrl) {
            window.location.href = redirectUrl;
            return;
          }

          const urlParams = new URLSearchParams(window.location.search);
          const viewParam = urlParams.get('view');
          if (viewParam === 'dashboard') {
            setCurrentView('dashboard');
          } else {
            const domainConfig = getCurrentDomainConfig();
            setCurrentView(
              domainConfig.userType === 'general' ? 'astroroshnihomepage' : 'selector'
            );
          }
        };

        authService
          .getCurrentUser()
          .then((validated) => applyAuthenticatedSession(validated || userData))
          .catch((err) => {
            const isNetworkError =
              err?.name === 'TypeError' ||
              (typeof err?.message === 'string' && err.message.includes('Network'));
            if (isNetworkError) {
              applyAuthenticatedSession(userData);
              return;
            }
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setUser(null);
          })
          .finally(() => setLoading(false));
      } catch {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogin = (userData) => {
    // Reset cached native/chart from any previous session so another account
    // does not inherit stale localStorage birth details in header.
    clearAstrologySessionCache();
    setUser(userData);
    
    // Check if user should be redirected after login
    const redirectUrl = getRedirectUrl(userData);
    if (redirectUrl) {
      window.location.href = redirectUrl;
      return;
    }
    
    // Check URL parameters for view override
    const urlParams = new URLSearchParams(window.location.search);
    const viewParam = urlParams.get('view');
    
    if (viewParam === 'dashboard') {
      setCurrentView('dashboard');
    } else {
      // Set appropriate view based on domain configuration
      const domainConfig = getCurrentDomainConfig();
      
      if (domainConfig.userType === 'general') {
        setCurrentView('astroroshnihomepage'); // AstroRoshni domain shows homepage
      } else {
        setCurrentView('selector'); // AstroVishnu/other domains show chart selector
      }
    }
  };

  const handleLogout = () => {
    authService.logout();
    clearAstrologySessionCache();
    setUser(null);
    setCurrentView('selector');
  };

  const handleAdminClick = () => {
    if (user && user.role === 'admin') {
      setCurrentView('admin');
    }
  };

  /** Chart selector home (AstroVishnu) vs marketing homepage (AstroRoshni), matching getCurrentDomainConfig(). */
  const goToDomainHome = () => {
    const domainConfig = getCurrentDomainConfig();
    setCurrentView(domainConfig.userType === 'general' ? 'astroroshnihomepage' : 'selector');
  };

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>;
  }

  const domainConfig = getCurrentDomainConfig();

  return (
    <HelmetProvider>
      <Router>
        <AstrologyProvider>
          <CreditProvider>
            <AnalyticsTracker user={user} />
            <RouteSEO />
            <Suspense fallback={<RoutePageFallback />}>
              <Routes>
            <Route path="/login" element={<Navigate to="/" replace />} />
            <Route
              path="/panchang"
              element={
                <PanchangPage
                  user={user}
                  onLogout={user ? handleLogout : undefined}
                  onAdminClick={user ? handleAdminClick : undefined}
                  onLogin={!user ? () => setShowLoginModal(true) : undefined}
                  showLoginButton={!user}
                />
              }
            />
            <Route path="/" element={
              user ? (
                <AuthenticatedRootShell
                  currentView={currentView}
                  user={user}
                  setCurrentView={setCurrentView}
                  onLogout={handleLogout}
                  onAdminClick={handleAdminClick}
                  onLogin={() => setShowLoginModal(true)}
                  goToDomainHome={goToDomainHome}
                />
              ) : (
              domainConfig.userType === 'general' ? (
                <>
                  <AstroRoshniHomepage 
                    user={null} 
                    onLogin={() => setShowLoginModal(true)} 
                    showLoginButton={true} 
                  />
                  <AuthModalShell isOpen={showLoginModal} onClose={() => setShowLoginModal(false)}>
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
                  </AuthModalShell>
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
                  <AuthModalShell isOpen={showLoginModal} onClose={() => setShowLoginModal(false)}>
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
                  </AuthModalShell>
                </>
              ) : (
                <LandingPage onLogin={handleLogin} onRegister={handleLogin} domainConfig={domainConfig} />
              )
              )
            } />
            <Route path="/beginners-guide" element={
              <BeginnersGuide
                user={user}
                onLogout={user ? handleLogout : undefined}
                onAdminClick={user ? handleAdminClick : undefined}
              />
            } />
            <Route path="/advanced-courses" element={
              <AdvancedCourses
                user={user}
                onLogout={user ? handleLogout : undefined}
                onAdminClick={user ? handleAdminClick : undefined}
              />
            } />
            <Route path="/myths-vs-reality" element={
              <MythsVsReality
                user={user}
                onLogout={user ? handleLogout : undefined}
                onAdminClick={user ? handleAdminClick : undefined}
              />
            } />
            <Route path="/horoscope/:period" element={<HoroscopePage />} />
            <Route path="/horoscope" element={<HoroscopePage />} />
            <Route path="/birth-chart" element={<Navigate to="/ai-kundli-generator" replace />} />
            <Route path="/ai-kundli-generator" element={
              <>
                <BirthChartCreationPage
                  user={user}
                  onLogout={user ? handleLogout : undefined}
                  onAdminClick={user ? handleAdminClick : undefined}
                  onLogin={() => {
                    setAuthView('login');
                    setShowLoginModal(true);
                  }}
                  onOpenRegister={() => {
                    setAuthView('register');
                    setShowLoginModal(true);
                  }}
                />
                <AnalysisGuestAuthModal
                  isOpen={showLoginModal && !user}
                  onClose={() => setShowLoginModal(false)}
                  authView={authView}
                  setAuthView={setAuthView}
                  description="Sign in to create and save your birth chart so you can use it across AstroRoshni reports, matching, and AI chat."
                  onAuthenticated={handleLogin}
                />
              </>
            } />
            <Route path="/charts-dashas" element={
              <>
                <ChartsDashasWorkspacePage
                  user={user}
                  onLogout={user ? handleLogout : undefined}
                  onAdminClick={user ? handleAdminClick : undefined}
                  onLogin={() => {
                    setAuthView('login');
                    setShowLoginModal(true);
                  }}
                  onOpenRegister={() => {
                    setAuthView('register');
                    setShowLoginModal(true);
                  }}
                />
                <AnalysisGuestAuthModal
                  isOpen={showLoginModal && !user}
                  onClose={() => setShowLoginModal(false)}
                  authView={authView}
                  setAuthView={setAuthView}
                  description="Sign in to open your chart workspace and use your saved birth chart across charts and dasha timelines."
                  onAuthenticated={handleLogin}
                />
              </>
            } />
            <Route path="/marriage-analysis" element={
              <>
                <AnalysisDetailPage
                  analysisType="marriage"
                  user={user}
                  onLogout={user ? handleLogout : undefined}
                  onAdminClick={user ? handleAdminClick : undefined}
                  onLogin={() => {
                    setAuthView('login');
                    setShowLoginModal(true);
                  }}
                  onOpenRegister={() => {
                    setAuthView('register');
                    setShowLoginModal(true);
                  }}
                />
                <AnalysisGuestAuthModal
                  isOpen={showLoginModal && !user}
                  onClose={() => setShowLoginModal(false)}
                  authView={authView}
                  setAuthView={setAuthView}
                  description="Sign in to add your saved birth chart and run your personalised marriage analysis."
                  onAuthenticated={handleLogin}
                />
              </>
            } />
            <Route path="/career-guidance" element={
              <>
                <AnalysisDetailPage
                  analysisType="career"
                  user={user}
                  onLogout={user ? handleLogout : undefined}
                  onAdminClick={user ? handleAdminClick : undefined}
                  onLogin={() => {
                    setAuthView('login');
                    setShowLoginModal(true);
                  }}
                  onOpenRegister={() => {
                    setAuthView('register');
                    setShowLoginModal(true);
                  }}
                />
                <AnalysisGuestAuthModal
                  isOpen={showLoginModal && !user}
                  onClose={() => setShowLoginModal(false)}
                  authView={authView}
                  setAuthView={setAuthView}
                  description="Sign in to add your saved birth chart and run your personalised career analysis."
                  onAuthenticated={handleLogin}
                />
              </>
            } />
            <Route path="/muhurat-finder" element={<MuhuratFinderPage user={user} onLogout={user ? handleLogout : undefined} onAdminClick={user ? handleAdminClick : undefined} />} />
            <Route path="/health-analysis" element={
              <>
                <AnalysisDetailPage
                  analysisType="health"
                  user={user}
                  onLogout={user ? handleLogout : undefined}
                  onAdminClick={user ? handleAdminClick : undefined}
                  onLogin={() => {
                    setAuthView('login');
                    setShowLoginModal(true);
                  }}
                  onOpenRegister={() => {
                    setAuthView('register');
                    setShowLoginModal(true);
                  }}
                />
                <AnalysisGuestAuthModal
                  isOpen={showLoginModal && !user}
                  onClose={() => setShowLoginModal(false)}
                  authView={authView}
                  setAuthView={setAuthView}
                  description="Sign in to add your saved birth chart and run your personalised health and wellness analysis."
                  onAuthenticated={handleLogin}
                />
              </>
            } />
            <Route path="/wealth-analysis" element={
              <>
                <AnalysisDetailPage
                  analysisType="wealth"
                  user={user}
                  onLogout={user ? handleLogout : undefined}
                  onAdminClick={user ? handleAdminClick : undefined}
                  onLogin={() => {
                    setAuthView('login');
                    setShowLoginModal(true);
                  }}
                  onOpenRegister={() => {
                    setAuthView('register');
                    setShowLoginModal(true);
                  }}
                />
                <AnalysisGuestAuthModal
                  isOpen={showLoginModal && !user}
                  onClose={() => setShowLoginModal(false)}
                  authView={authView}
                  setAuthView={setAuthView}
                  description="Sign in to add your saved birth chart and run your personalised wealth and finance analysis."
                  onAuthenticated={handleLogin}
                />
              </>
            } />
            <Route path="/lesson/:lessonId" element={
              <LessonPage
                user={user}
                onLogout={user ? handleLogout : undefined}
                onAdminClick={user ? handleAdminClick : undefined}
              />
            } />
          <Route path="/nakshatras" element={<NakshatraListPage />} />
          <Route path="/nakshatra/:nakshatraName/:year" element={<NakshatraPage />} />
          <Route path="/monthly-panchang" element={
            <MonthlyPanchangPage 
              user={user}
              onLogout={user ? handleLogout : undefined}
              onAdminClick={user ? handleAdminClick : undefined}
              onLogin={!user ? () => setShowLoginModal(true) : undefined}
              showLoginButton={!user}
            />
          } />
          <Route path="/festivals" element={<FestivalsPage />} />
          <Route path="/festivals/monthly" element={<MonthlyFestivalsPage />} />
          {/* CRA route: in-app navigation + fallback when static HTML is not served. SEO HTML: build/karma-analysis.html */}
          <Route
            path="/karma-analysis"
            element={
              <>
                <KarmaAnalysis
                  user={user}
                  onLogout={user ? handleLogout : () => {}}
                  onAdminClick={user ? handleAdminClick : () => {}}
                  onLogin={() => setShowLoginModal(true)}
                  showLoginButton={!user}
                />
                <AuthModalShell isOpen={showLoginModal && !user} onClose={() => setShowLoginModal(false)}>
                  <div style={{ marginBottom: '20px' }}>
                    <h2 style={{ textAlign: 'center', color: '#e91e63', marginBottom: '10px' }}>Sign in required</h2>
                    <p style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>
                      Sign in to run your personalised past-life karma analysis.
                    </p>
                    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                      <button
                        type="button"
                        onClick={() => setAuthView('login')}
                        style={{
                          padding: '10px 20px',
                          border: 'none',
                          background: authView === 'login' ? '#e91e63' : 'transparent',
                          color: authView === 'login' ? 'white' : '#e91e63',
                          borderRadius: '25px 0 0 25px',
                          cursor: 'pointer',
                          borderRight: '1px solid #e91e63',
                        }}
                      >
                        Sign In
                      </button>
                      <button
                        type="button"
                        onClick={() => setAuthView('register')}
                        style={{
                          padding: '10px 20px',
                          border: 'none',
                          background: authView === 'register' ? '#e91e63' : 'transparent',
                          color: authView === 'register' ? 'white' : '#e91e63',
                          borderRadius: '0 25px 25px 0',
                          cursor: 'pointer',
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
                </AuthModalShell>
              </>
            }
          />
          <Route
            path="/kundli-matching"
            element={
              <>
                <KundliMatchingPage
                  user={user}
                  onLogout={user ? handleLogout : () => {}}
                  onAdminClick={user ? handleAdminClick : () => {}}
                  onLogin={() => setShowLoginModal(true)}
                  showLoginButton={!user}
                />
                <AuthModalShell isOpen={showLoginModal && !user} onClose={() => setShowLoginModal(false)}>
                  <div style={{ marginBottom: '20px' }}>
                    <h2 style={{ textAlign: 'center', color: '#e91e63', marginBottom: '10px' }}>Sign in required</h2>
                    <p style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>
                      Sign in to use saved charts and run Kundli matching with your account.
                    </p>
                    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                      <button
                        type="button"
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
                        type="button"
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
                </AuthModalShell>
              </>
            }
          />
          <Route
            path="/astrovastu"
            element={
              <AstroVastuTool
                user={user}
                onLogout={user ? handleLogout : () => {}}
                onAdminClick={user ? handleAdminClick : () => {}}
                onLogin={() => setShowLoginModal(true)}
              />
            }
          />
          <Route
            path="/life-events"
            element={
              <EventsTimelinePage
                user={user}
                onLogout={user ? handleLogout : undefined}
                onAdminClick={user ? handleAdminClick : undefined}
                onLogin={!user ? () => setShowLoginModal(true) : undefined}
              />
            }
          />
          <Route
            path="/ashtakavarga"
            element={
              <>
                <AshtakavargaSeoPage
                  user={user}
                  onLogout={user ? handleLogout : () => {}}
                  onAdminClick={user ? handleAdminClick : () => {}}
                  onLogin={() => setShowLoginModal(true)}
                  onOpenRegister={() => {
                    setAuthView('register');
                    setShowLoginModal(true);
                  }}
                />
                <AuthModalShell isOpen={showLoginModal && !user} onClose={() => setShowLoginModal(false)}>
                  <div style={{ maxWidth: 420, margin: '0 auto' }}>
                    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
                      <div style={{
                        display: 'flex',
                        background: '#f8f9fa',
                        borderRadius: 25,
                        padding: 4,
                        width: 'fit-content'
                      }}>
                        <button
                          type="button"
                          onClick={() => setAuthView('login')}
                          style={{
                            padding: '10px 20px',
                            border: 'none',
                            background: authView === 'login' ? '#e91e63' : 'transparent',
                            color: authView === 'login' ? 'white' : '#e91e63',
                            borderRadius: '25px 0 0 25px',
                            cursor: 'pointer'
                          }}
                        >
                          Login
                        </button>
                        <button
                          type="button"
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
                </AuthModalShell>
              </>
            }
          />
          <Route
            path="/tools/ashtakavarga"
            element={
              <AshtakavargaToolPage
                user={user}
                onLogout={user ? handleLogout : () => {}}
                onAdminClick={user ? handleAdminClick : () => {}}
                onLogin={() => setShowLoginModal(true)}
              />
            }
          />
          <Route path="/policy" element={<PolicyPage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route
            path="/account/delete"
            element={
              <>
                <DeleteAccountPage
                  user={user}
                  onLogout={handleLogout}
                  onLogin={() => {
                    setAuthView('login');
                    setShowLoginModal(true);
                  }}
                />
                <AuthModalShell isOpen={showLoginModal && !user} onClose={() => setShowLoginModal(false)}>
                  <div style={{ marginBottom: '20px' }}>
                    <h2 style={{ textAlign: 'center', color: '#e91e63', marginBottom: '10px' }}>Sign in required</h2>
                    <p style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>
                      Sign in to confirm your identity before deleting your account.
                    </p>
                    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                      <button
                        type="button"
                        onClick={() => setAuthView('login')}
                        style={{
                          padding: '10px 20px',
                          border: 'none',
                          background: authView === 'login' ? '#e91e63' : 'transparent',
                          color: authView === 'login' ? 'white' : '#e91e63',
                          borderRadius: '25px 0 0 25px',
                          cursor: 'pointer',
                          borderRight: '1px solid #e91e63',
                        }}
                      >
                        Sign In
                      </button>
                      <button
                        type="button"
                        onClick={() => setAuthView('register')}
                        style={{
                          padding: '10px 20px',
                          border: 'none',
                          background: authView === 'register' ? '#e91e63' : 'transparent',
                          color: authView === 'register' ? 'white' : '#e91e63',
                          borderRadius: '0 25px 25px 0',
                          cursor: 'pointer',
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
                </AuthModalShell>
              </>
            }
          />
          <Route path="/contact" element={<ContactPage />} />
          <Route
            path="/subscription"
            element={
              <SubscriptionPage
                user={user}
                onLogin={() => setShowLoginModal(true)}
                onLogout={handleLogout}
                onAdminClick={handleAdminClick}
              />
            }
          />
          <Route
            path="/order-management"
            element={
              <OrderManagementPage
                user={user}
                onLogin={() => setShowLoginModal(true)}
                onLogout={handleLogout}
                onAdminClick={handleAdminClick}
              />
            }
          />
          <Route path="/about" element={<AboutUs />} />
          <Route path="/calendar-2026" element={
            <Calendar2026
              user={user}
              onLogout={user ? handleLogout : undefined}
              onLogin={!user ? () => setShowLoginModal(true) : undefined}
            />
          } />
            <Route path="/blog" element={<BlogList />} />
            <Route path="/blog/:slug" element={<BlogPost />} />
            <Route
              path="/progeny-analysis"
              element={
                <>
                  <AnalysisDetailPage
                    analysisType="progeny"
                    user={user}
                    onLogout={user ? handleLogout : undefined}
                    onAdminClick={user ? handleAdminClick : undefined}
                    onLogin={() => {
                      setAuthView('login');
                      setShowLoginModal(true);
                    }}
                    onOpenRegister={() => {
                      setAuthView('register');
                      setShowLoginModal(true);
                    }}
                  />
                  <AnalysisGuestAuthModal
                    isOpen={showLoginModal && !user}
                    onClose={() => setShowLoginModal(false)}
                    authView={authView}
                    setAuthView={setAuthView}
                    description="Sign in to add your saved birth chart and run your personalised progeny analysis."
                    onAuthenticated={handleLogin}
                  />
                </>
              }
            />
            <Route path="/education" element={
              <>
                <AnalysisDetailPage
                  analysisType="education"
                  user={user}
                  onLogout={user ? handleLogout : undefined}
                  onAdminClick={user ? handleAdminClick : undefined}
                  onLogin={() => {
                    setAuthView('login');
                    setShowLoginModal(true);
                  }}
                  onOpenRegister={() => {
                    setAuthView('register');
                    setShowLoginModal(true);
                  }}
                />
                <AnalysisGuestAuthModal
                  isOpen={showLoginModal && !user}
                  onClose={() => setShowLoginModal(false)}
                  authView={authView}
                  setAuthView={setAuthView}
                  description="Sign in to add your saved birth chart and run your personalised education analysis."
                  onAuthenticated={handleLogin}
                />
              </>
            } />
            {/* CRA route: SEO HTML at build/chat.html; ?app=1 loads this shell */}
            <Route
              path="/chat"
              element={
                <ChatRouteGate>
                  <ChatPage onLogin={() => setShowLoginModal(true)} />
                  <AuthModalShell isOpen={showLoginModal && !user} onClose={() => setShowLoginModal(false)}>
                    <div style={{ marginBottom: '20px' }}>
                      <h2 style={{ textAlign: 'center', color: '#e91e63', marginBottom: '10px' }}>Sign in required</h2>
                      <p style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>
                        Sign in to chat with your saved birth chart and use credits.
                      </p>
                      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                        <button
                          type="button"
                          onClick={() => setAuthView('login')}
                          style={{
                            padding: '10px 20px',
                            border: 'none',
                            background: authView === 'login' ? '#e91e63' : 'transparent',
                            color: authView === 'login' ? 'white' : '#e91e63',
                            borderRadius: '25px 0 0 25px',
                            cursor: 'pointer',
                            borderRight: '1px solid #e91e63',
                          }}
                        >
                          Sign In
                        </button>
                        <button
                          type="button"
                          onClick={() => setAuthView('register')}
                          style={{
                            padding: '10px 20px',
                            border: 'none',
                            background: authView === 'register' ? '#e91e63' : 'transparent',
                            color: authView === 'register' ? 'white' : '#e91e63',
                            borderRadius: '0 25px 25px 0',
                            cursor: 'pointer',
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
                  </AuthModalShell>
                </ChatRouteGate>
              }
            />
            <Route path="/speech-chat" element={user ? <SpeechChatPage /> : <Navigate to="/" replace />} />
            <Route path="/profile" element={user ? <ProfilePage user={user} onLogout={handleLogout} /> : <Navigate to="/" replace />} />
            <Route path="/admin/blog" element={
              user && user.role === 'admin' ? (
                <BlogDashboard />
              ) : (
                <Navigate to="/" replace />
              )
            } />
            <Route path="/astroroshni" element={<AstroRoshniPage />} />
              </Routes>
            </Suspense>
            <ToastContainer />
          {(!user || currentView !== 'dashboard') && (
            <FloatingChatButtonUnlessOnChatPage user={user} onRequireLogin={() => setShowLoginModal(true)} />
          )}
          </CreditProvider>
        </AstrologyProvider>
      </Router>
    </HelmetProvider>
  );
}

export default App;
