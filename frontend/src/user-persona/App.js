import React from 'react';
import HomePage from './pages/HomePage';
import './styles/global.css';

function UserPersonaApp({ onGetStarted }) {
  return (
    <div className="user-persona-app">
      <HomePage onGetStarted={onGetStarted} />
    </div>
  );
}

export default UserPersonaApp;