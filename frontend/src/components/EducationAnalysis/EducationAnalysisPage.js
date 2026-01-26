import React, { useState, useEffect } from 'react';
import NavigationHeader from '../Shared/NavigationHeader';
import NativeSelector from '../Shared/NativeSelector';
import TechnicalAnalysisTab from './TechnicalAnalysisTab';
import AIQuestionsTab from './AIQuestionsTab';
import { useAstrology } from '../../context/AstrologyContext';
import './EducationAnalysisPage.css';

// Added promo code edit and delete functionality with custom confirmation modal

const EducationAnalysisPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const { birthData } = useAstrology();
  const [activeTab, setActiveTab] = useState('ai');
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [birthDetails, setBirthDetails] = useState(null);

  useEffect(() => {
    console.log('EducationAnalysisPage useEffect triggered, user:', user);
    
    // Use birth data from context if available, otherwise try localStorage
    if (birthData) {
      setBirthDetails(birthData);
    } else {
      const savedBirthData = localStorage.getItem('currentBirthData') || 
                            localStorage.getItem('birthData') ||
                            localStorage.getItem('userBirthData');
      
      if (savedBirthData) {
        try {
          const parsedBirthData = JSON.parse(savedBirthData);
          setBirthDetails(parsedBirthData);
        } catch (error) {
          console.error('Error parsing birth data:', error);
        }
      }
    }
    
    if (user) {
      console.log('User exists, calling fetchEducationAnalysis');
      fetchEducationAnalysis();
    } else {
      console.log('No user found, skipping API call');
    }
  }, [user, birthData]);

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
        compact={true}
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
            <NativeSelector 
              birthData={birthDetails} 
              onNativeChange={() => window.location.reload()}
            />
            <div className="analysis-section">
            <div className="tab-navigation">
              <button 
                className={`tab-btn ${activeTab === 'ai' ? 'active' : ''}`}
                onClick={() => setActiveTab('ai')}
              >
                Personalized Education Analysis
              </button>
              <button 
                className={`tab-btn ${activeTab === 'technical' ? 'active' : ''}`}
                onClick={() => setActiveTab('technical')}
              >
                Detailed Technical Analysis
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
                  {activeTab === 'ai' && (
                    <AIQuestionsTab 
                      chartData={null}
                      birthDetails={birthDetails}
                    />
                  )}
                  {activeTab === 'technical' && (
                    <TechnicalAnalysisTab 
                      analysisData={analysisData}
                      onRefresh={fetchEducationAnalysis}
                    />
                  )}
                </>
              )}
            </div>
          </div>
          </>
        )}
      </div>
    </div>
  );
};

export default EducationAnalysisPage;