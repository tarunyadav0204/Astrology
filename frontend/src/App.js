import React, { useState } from 'react';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import BirthForm from './components/BirthForm/BirthForm';
import Dashboard from './components/Dashboard/Dashboard';
import PredictionsPage from './components/PredictionsPage/PredictionsPage';
import { AstrologyProvider } from './context/AstrologyContext';
import { APP_CONFIG } from './config/app.config';

function App() {
  const [showDashboard, setShowDashboard] = useState(false);
  const [currentView, setCurrentView] = useState('dashboard');

  return (
    <AstrologyProvider>
      <div style={{ 
        padding: showDashboard ? '0' : '20px', 
        maxWidth: showDashboard ? '100vw' : '1200px', 
        margin: showDashboard ? '0' : '0 auto',
        minHeight: '100vh',
        background: showDashboard ? 'transparent' : 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 50%, #ffcc80 100%)'
      }}>
        {!showDashboard ? (
          <BirthForm onSubmit={() => setShowDashboard(true)} />
        ) : (
          <div>
            {currentView === 'dashboard' && <Dashboard onBack={() => setShowDashboard(false)} currentView={currentView} setCurrentView={setCurrentView} />}
            {currentView === 'predictions' && <PredictionsPage onBack={() => setShowDashboard(false)} currentView={currentView} setCurrentView={setCurrentView} />}
          </div>
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