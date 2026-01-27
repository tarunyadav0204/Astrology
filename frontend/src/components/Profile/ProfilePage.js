import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import ConsultationHistory from './ConsultationHistory';
import CreditLedger from './CreditLedger';
import './ProfilePage.css';

const ProfilePage = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('consultations');

  return (
    <div className="profile-page">
      <NavigationHeader 
        compact={true}
        user={user}
        onLogout={onLogout}
        onHomeClick={() => navigate('/')}
      />
      
      <div className="profile-content">
        <div className="profile-tabs">
          <button 
            className={`tab-btn ${activeTab === 'consultations' ? 'active' : ''}`}
            onClick={() => setActiveTab('consultations')}
          >
            📋 Past Consultations
          </button>
          <button 
            className={`tab-btn ${activeTab === 'credits' ? 'active' : ''}`}
            onClick={() => setActiveTab('credits')}
          >
            💳 Credit Ledger
          </button>
        </div>
        
        <div className="tab-content">
          {activeTab === 'consultations' && <ConsultationHistory user={user} />}
          {activeTab === 'credits' && <CreditLedger user={user} />}
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;