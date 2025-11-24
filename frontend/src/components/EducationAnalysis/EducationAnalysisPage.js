import React, { useState, useEffect } from 'react';
import NavigationHeader from '../Shared/NavigationHeader';
import TechnicalAnalysisTab from './TechnicalAnalysisTab';
import AIQuestionsTab from './AIQuestionsTab';
import './EducationAnalysisPage.css';

const EducationAnalysisPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const [activeTab, setActiveTab] = useState('technical');
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('EducationAnalysisPage useEffect triggered, user:', user);
    if (user) {
      console.log('User exists, calling fetchEducationAnalysis');
      fetchEducationAnalysis();
    } else {
      console.log('No user found, skipping API call');
    }
  }, [user]);

  const fetchEducationAnalysis = async () => {
    try {
      setLoading(true);
      console.log('fetchEducationAnalysis called');
      
      // Debug: Check all localStorage keys
      console.log('All localStorage keys:', Object.keys(localStorage));
      
      let savedBirthData = localStorage.getItem('currentBirthData') || 
                          localStorage.getItem('birthData') ||
                          localStorage.getItem('userBirthData');
      
      console.log('Saved birth data from localStorage:', savedBirthData ? 'Found' : 'Not found');
      
      // For testing: create sample birth data if none exists
      if (!savedBirthData) {
        const sampleBirthData = {
          name: 'Test User',
          date: '1990-01-01',
          time: '12:00',
          latitude: 28.6139,
          longitude: 77.2090,
          timezone: 'UTC+5:30',
          place: 'Delhi, India'
        };
        savedBirthData = JSON.stringify(sampleBirthData);
        console.log('Using sample birth data for testing');
      }
      
      // Try to get from user object if still no data
      if (!savedBirthData && user && user.birth_data) {
        savedBirthData = JSON.stringify(user.birth_data);
        console.log('Using birth data from user object');
      }

      const birthData = JSON.parse(savedBirthData);
      console.log('Making education API call with data:', birthData);
      
      const token = localStorage.getItem('token');
      console.log('Using token:', token ? 'Token found' : 'No token');
      
      const response = await fetch('/api/education/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(birthData)
      });
      
      console.log('API response status:', response.status);
      console.log('API response headers:', response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API error response:', errorText);
        throw new Error(`Failed to fetch analysis: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      console.log('API response data:', data);
      setAnalysisData(data.analysis);
    } catch (error) {
      console.error('Error fetching education analysis:', error);
      setAnalysisData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="education-analysis-page">
      <NavigationHeader 
        user={user}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
        onLogin={onLogin}
        showLoginButton={showLoginButton}
      />
      
      <div className="education-header">
        <button 
          className="back-button"
          onClick={() => window.history.back()}
        >
          ← Back
        </button>
        <div className="header-content">
          <h1>🎓 Education Analysis</h1>
          <p>Get comprehensive insights about your educational journey and academic potential</p>
        </div>
      </div>

      <div className="education-content">
        {!user && (
          <div className="auth-required">
            <p>Please log in to access education analysis.</p>
          </div>
        )}
        
        {user && (
          <>
            <div className="tab-navigation">
              <button 
                className={`tab-btn ${activeTab === 'technical' ? 'active' : ''}`}
                onClick={() => setActiveTab('technical')}
              >
                📊 Technical Analysis
              </button>
              <button 
                className={`tab-btn ${activeTab === 'ai' ? 'active' : ''}`}
                onClick={() => setActiveTab('ai')}
              >
                🤖 AI Q&A
              </button>
            </div>

            <div className="tab-content">
              {loading ? (
                <div className="loading-container">
                  <div className="spinner"></div>
                  <p>Analyzing your educational prospects...</p>
                </div>
              ) : (
                <>
                  {activeTab === 'technical' && (
                    <TechnicalAnalysisTab 
                      analysisData={analysisData}
                      onRefresh={fetchEducationAnalysis}
                    />
                  )}
                  {activeTab === 'ai' && (
                    <AIQuestionsTab 
                      analysisData={analysisData}
                      user={user}
                    />
                  )}
                </>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default EducationAnalysisPage;