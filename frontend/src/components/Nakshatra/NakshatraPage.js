import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import SEOHead from '../SEO/SEOHead';
import ColorLegend from './ColorLegend';
import './NakshatraPage.css';

const NakshatraPage = () => {
  const { nakshatraName, year } = useParams();
  const navigate = useNavigate();
  const [nakshatraData, setNakshatraData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedYear, setSelectedYear] = useState(parseInt(year) || new Date().getFullYear());

  useEffect(() => {
    fetchNakshatraData();
  }, [nakshatraName, selectedYear]);

  const fetchNakshatraData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/nakshatra/${nakshatraName}/${selectedYear}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch nakshatra data');
      }
      
      const data = await response.json();
      setNakshatraData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleYearChange = (newYear) => {
    const yearNum = parseInt(newYear);
    setSelectedYear(yearNum);
    navigate(`/nakshatra/${nakshatraName}/${yearNum}`);
  };

  if (loading) {
    return (
      <div className="nakshatra-page">
        <div className="loading">Loading {nakshatraName} nakshatra data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="nakshatra-page">
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  if (!nakshatraData) {
    return (
      <div className="nakshatra-page">
        <div className="error">No data found</div>
      </div>
    );
  }

  const currentYear = new Date().getFullYear();

  return (
    <div className="nakshatra-page">
      <SEOHead 
        title={nakshatraData.seo?.title}
        description={nakshatraData.seo?.description}
        keywords={nakshatraData.seo?.keywords}
      />
      
      <div className="nakshatra-navigation">
        <button 
          onClick={() => navigate(`/nakshatra/${nakshatraData.navigation.previous}/${selectedYear}`)}
          className="nav-button prev"
        >
          « {nakshatraData.navigation.previous}
        </button>
        <div className="nav-center">
          <button 
            onClick={() => navigate('/')}
            className="nav-button home-btn"
          >
            🏠 Home
          </button>
          <button 
            onClick={() => navigate('/nakshatras')}
            className="nav-button list-btn"
          >
            All Nakshatras
          </button>
        </div>
        <button 
          onClick={() => navigate(`/nakshatra/${nakshatraData.navigation.next}/${selectedYear}`)}
          className="nav-button next"
        >
          {nakshatraData.navigation.next} »
        </button>
      </div>

      <div className="nakshatra-header">
        <h1>
          <span className="nakshatra-symbol">{nakshatraData.properties.symbol}</span>
          {nakshatraData.nakshatra} Nakshatra
        </h1>
        <div className="nakshatra-properties">
          <div className="property">
            <span className="label">Swami:</span>
            <span className="value">{nakshatraData.properties.lord}</span>
          </div>
          <div className="property">
            <span className="label">Swabhava:</span>
            <span className="value">{nakshatraData.properties.nature}</span>
          </div>
          <div className="property">
            <span className="label">Deity:</span>
            <span className="value">{nakshatraData.properties.deity}</span>
          </div>
        </div>
      </div>

      <div className="year-navigation">
        <button 
          onClick={() => handleYearChange(selectedYear - 1)}
          className="year-nav-button"
        >
          ❮ {selectedYear - 1}
        </button>
        <span className="current-year">{selectedYear}</span>
        <button 
          onClick={() => handleYearChange(selectedYear + 1)}
          className="year-nav-button"
          disabled={selectedYear >= currentYear + 5}
        >
          {selectedYear + 1} ❯
        </button>
      </div>

      <div className="nakshatra-periods">
        <h2>{nakshatraData.nakshatra} Nakshatra in {selectedYear}</h2>
        <p>This page lists all {nakshatraData.nakshatra} Nakshatra in the year {selectedYear} with their begin and end timings.</p>
        
        <ColorLegend />
        
        {nakshatraData.periods.length === 0 ? (
          <div className="no-periods">
            No {nakshatraData.nakshatra} nakshatra periods found for {selectedYear}.
          </div>
        ) : (
          <div className="periods-list">
            {nakshatraData.periods.map((period, index) => (
              <div key={index} className={`period-card ${period.auspiciousness}`}>
                <div className="period-date">
                  <div className="day">{period.day_number || new Date(period.start_datetime).getDate()}</div>
                  <div className="month">{period.month_name || new Date(period.start_datetime).toLocaleDateString('en-US', { month: 'short' })}</div>
                  <div className="weekday">{period.weekday}</div>
                </div>
                <div className="period-content">
                  <div className="period-title">{nakshatraData.nakshatra} Nakshatra</div>
                  <div className="period-timing">
                    <div>Begins: {period.start_time}, {period.start_date}</div>
                    <div>Ends: {period.end_time}, {period.end_date}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="nakshatra-details">
        <div className="characteristics-grid">
          <div className="char-card">
            <h4>📖 Description</h4>
            <p>{nakshatraData.properties.description || 'Ancient lunar mansion with deep spiritual significance.'}</p>
          </div>
          
          {nakshatraData.properties.characteristics && (
            <div className="char-card">
              <h4>✨ Characteristics</h4>
              <p>{nakshatraData.properties.characteristics}</p>
            </div>
          )}
          
          {nakshatraData.properties.positive_traits && (
            <div className="char-card positive">
              <h4>✅ Positive Traits</h4>
              <p>{nakshatraData.properties.positive_traits}</p>
            </div>
          )}
          
          {nakshatraData.properties.negative_traits && (
            <div className="char-card negative">
              <h4>⚠️ Challenges</h4>
              <p>{nakshatraData.properties.negative_traits}</p>
            </div>
          )}
          
          {nakshatraData.properties.careers && (
            <div className="char-card">
              <h4>💼 Career Fields</h4>
              <p>{nakshatraData.properties.careers}</p>
            </div>
          )}
          
          {nakshatraData.properties.compatibility && (
            <div className="char-card">
              <h4>💕 Compatibility</h4>
              <p>{nakshatraData.properties.compatibility}</p>
            </div>
          )}
        </div>
        
        <div className="properties-summary">
          <h3>{nakshatraData.nakshatra} Nakshatra Properties</h3>
          <div className="properties-grid">
            <div className="prop-item">
              <span className="prop-label">Swami (Lord):</span>
              <span className="prop-value">{nakshatraData.properties.lord}</span>
            </div>
            <div className="prop-item">
              <span className="prop-label">Swabhava (Nature):</span>
              <span className="prop-value">{nakshatraData.properties.nature}</span>
            </div>
            <div className="prop-item">
              <span className="prop-label">Deity:</span>
              <span className="prop-value">{nakshatraData.properties.deity}</span>
            </div>
            <div className="prop-item">
              <span className="prop-label">Guna:</span>
              <span className="prop-value">{nakshatraData.properties.guna}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="footer-note">
        <p><strong>Notes:</strong> All timings are represented in 12-hour notation in local time of {nakshatraData.location.name} with DST adjustment (if applicable).</p>
        <p>Hours which are past midnight are suffixed with next day date. In Panchang day starts and ends with sunrise.</p>
      </div>
    </div>
  );
};

export default NakshatraPage;