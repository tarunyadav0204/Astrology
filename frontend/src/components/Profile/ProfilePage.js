import React from 'react';
import { useNavigate } from 'react-router-dom';
import ConsultationHistory from './ConsultationHistory';
import './ProfilePage.css';

const ProfilePage = ({ user, onLogout }) => {
  const navigate = useNavigate();

  return (
    <div className="profile-page">
      <div className="profile-header">
        <button className="back-btn" onClick={() => navigate('/')}>
          ← Back to Home
        </button>
        <div className="profile-info">
          <div className="profile-avatar">👤</div>
          <div className="profile-details">
            <h1>{user?.name || 'User Profile'}</h1>
            <p>{user?.phone || user?.email}</p>
          </div>
        </div>
        <button className="logout-btn" onClick={onLogout}>
          Logout
        </button>
      </div>
      
      <div className="profile-content">
        <ConsultationHistory user={user} />
      </div>
    </div>
  );
};

export default ProfilePage;