import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import './NakshatraListPage.css';

const NakshatraListPage = () => {
  const navigate = useNavigate();
  const [nakshatras, setNakshatras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const currentYear = new Date().getFullYear();

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        // Invalid user data
      }
    }
  }, []);

  useEffect(() => {
    fetchNakshatras();
  }, []);

  const fetchNakshatras = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/nakshatras/list');
      
      if (!response.ok) {
        throw new Error('Failed to fetch nakshatras');
      }
      
      const data = await response.json();
      setNakshatras(data.nakshatras || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleNakshatraClick = (nakshatraName) => {
    navigate(`/nakshatra/${nakshatraName.toLowerCase()}/${currentYear}`);
  };

  if (loading) {
    return (
      <div className="nakshatra-list-page">
        <div className="loading">Loading nakshatras...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="nakshatra-list-page">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="nakshatra-list-page">
      <SEOHead 
        title="27 Nakshatras - Complete Vedic Astrology Guide"
        description="Explore all 27 nakshatras in Vedic astrology. Learn about nakshatra lords, deities, characteristics, and their significance in your horoscope."
        keywords="nakshatras, vedic astrology, moon signs, nakshatra list, astrology guide"
      />
      <NavigationHeader 
        user={user}
        onLogin={() => navigate('/')}
        onLogout={() => {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
          navigate('/');
        }}
      />
      
      <div className="page-header">
        <h1>27 Nakshatras in Vedic Astrology</h1>
        <p className="page-description">
          Explore the complete list of 27 nakshatras (lunar mansions) in Vedic astrology. 
          Click on any nakshatra to view its annual calendar with precise timings and detailed information.
        </p>
      </div>

      <div className="nakshatras-grid">
        {nakshatras.map((nakshatra, index) => (
          <div 
            key={nakshatra.name}
            className="nakshatra-card"
            onClick={() => handleNakshatraClick(nakshatra.name)}
          >
            <div className="nakshatra-number">{nakshatra.index}</div>
            <div className="nakshatra-content">
              <h3 className="nakshatra-name">
                <span className="nakshatra-symbol">{nakshatra.symbol}</span>
                {nakshatra.name}
              </h3>
              <div className="nakshatra-details">
                <div className="detail-row">
                  <span className="label">Lord:</span>
                  <span className="value">{nakshatra.lord}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Deity:</span>
                  <span className="value">{nakshatra.deity}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Range:</span>
                  <span className="value">{nakshatra.degree_range}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Nature:</span>
                  <span className="value">{nakshatra.nature}</span>
                </div>
              </div>
              {nakshatra.description && (
                <p className="nakshatra-description">
                  {nakshatra.description.substring(0, 120)}...
                </p>
              )}
            </div>
            <div className="view-calendar">
              View {currentYear} Calendar →
            </div>
          </div>
        ))}
      </div>

      <div className="page-footer">
        <div className="about-nakshatras">
          <h2>About Nakshatras</h2>
          <p>
            Nakshatras are the 27 lunar mansions in Vedic astrology, each spanning 13°20' of the zodiac. 
            They are fundamental to Vedic astrology and are used for determining auspicious timings, 
            personality analysis, and compatibility matching. Each nakshatra has its own ruling planet, 
            deity, and unique characteristics that influence various aspects of life.
          </p>
          
          <h3>How to Use This Guide</h3>
          <ul>
            <li>Click on any nakshatra to view its complete annual calendar</li>
            <li>Each calendar shows exact begin and end times for the nakshatra periods</li>
            <li>Use this information for planning important activities and ceremonies</li>
            <li>Learn about each nakshatra's characteristics and significance</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default NakshatraListPage;