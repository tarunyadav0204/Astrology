import React, { useState, useEffect } from 'react';
import { muhuratService } from '../../services/muhuratService';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import { generatePageSEO } from '../../config/seo.config';
import './MuhuratFinderPage.css';

const MuhuratFinderPage = () => {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [location, setLocation] = useState({ latitude: 28.6139, longitude: 77.2090, name: 'New Delhi' });
  const [selectedMuhurat, setSelectedMuhurat] = useState('vivah');
  const [muhuratData, setMuhuratData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const muhuratTypes = [
    { id: 'vivah', name: 'Marriage Muhurat', icon: '💒', description: 'Auspicious times for wedding ceremonies' },
    { id: 'property', name: 'Property Purchase', icon: '🏠', description: 'Best times for property transactions' },
    { id: 'vehicle', name: 'Vehicle Purchase', icon: '🚗', description: 'Favorable periods for buying vehicles' },
    { id: 'griha-pravesh', name: 'Griha Pravesh', icon: '🏡', description: 'House warming ceremony timings' }
  ];

  useEffect(() => {
    fetchMuhuratData();
  }, [selectedDate, location, selectedMuhurat]);

  const fetchMuhuratData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let data;
      switch (selectedMuhurat) {
        case 'vivah':
          data = await muhuratService.getVivahMuhurat(selectedDate, location.latitude, location.longitude);
          break;
        case 'property':
          data = await muhuratService.getPropertyMuhurat(selectedDate, location.latitude, location.longitude);
          break;
        case 'vehicle':
          data = await muhuratService.getVehicleMuhurat(selectedDate, location.latitude, location.longitude);
          break;
        case 'griha-pravesh':
          data = await muhuratService.getGrihaPraveshMuhurat(selectedDate, location.latitude, location.longitude);
          break;
        default:
          data = await muhuratService.getVivahMuhurat(selectedDate, location.latitude, location.longitude);
      }
      setMuhuratData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timeString) => {
    return new Date(timeString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getCurrentMuhurat = () => {
    if (!muhuratData?.muhurtas) return null;
    
    const now = new Date();
    return muhuratData.muhurtas.find(muhurat => {
      const start = new Date(muhurat.start_time);
      const end = new Date(muhurat.end_time);
      return now >= start && now <= end;
    });
  };

  const currentMuhurat = getCurrentMuhurat();

  const seoData = generatePageSEO('muhuratFinder', { path: '/muhurat-finder' });

  return (
    <div className="muhurat-finder-page">
      <SEOHead 
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={{
          "@context": "https://schema.org",
          "@type": "WebApplication",
          "name": "Muhurat Finder",
          "description": "Find auspicious muhurat times for marriage, business, travel and important events",
          "applicationCategory": "LifestyleApplication"
        }}
      />
      <NavigationHeader />
      <div className="container">
        <div className="page-header">
          <h1>🕉️ Muhurat Finder</h1>
          <p>Find the most auspicious times for important life events</p>
        </div>

        <div className="controls-section">
          <div className="date-location-controls">
            <div className="date-control">
              <label>📅 Select Date</label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="date-input"
              />
            </div>
            
            <div className="location-control">
              <label>📍 Location</label>
              <div className="location-display">
                <span>{location.name}</span>
                <button className="change-location-btn">Change</button>
              </div>
            </div>
          </div>

          <div className="muhurat-type-selector">
            {muhuratTypes.map(type => (
              <div
                key={type.id}
                className={`muhurat-type-card ${selectedMuhurat === type.id ? 'active' : ''}`}
                onClick={() => setSelectedMuhurat(type.id)}
              >
                <div className="type-icon">{type.icon}</div>
                <div className="type-info">
                  <h3>{type.name}</h3>
                  <p>{type.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {loading && (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Calculating auspicious times...</p>
          </div>
        )}

        {error && (
          <div className="error-container">
            <div className="error-message">
              <h3>⚠️ Error</h3>
              <p>{error}</p>
              <button onClick={fetchMuhuratData} className="retry-btn">Try Again</button>
            </div>
          </div>
        )}

        {muhuratData && !loading && (
          <div className="muhurat-results">
            <div className="results-header">
              <h2>Auspicious Times for {formatDate(selectedDate)}</h2>
              <div className="location-info">
                📍 {location.name} ({location.latitude.toFixed(2)}°, {location.longitude.toFixed(2)}°)
              </div>
            </div>

            {currentMuhurat && (
              <div className="current-muhurat-alert">
                <div className="alert-header">
                  <span className="alert-icon">✨</span>
                  <span className="alert-text">Currently Active Muhurat</span>
                </div>
                <div className="current-muhurat-info">
                  <div className="muhurat-name">Muhurta {currentMuhurat.muhurta}</div>
                  <div className="muhurat-time">
                    {formatTime(currentMuhurat.start_time)} - {formatTime(currentMuhurat.end_time)}
                  </div>
                  <div className="muhurat-suitability">{currentMuhurat.suitability}</div>
                </div>
              </div>
            )}

            <div className="muhurat-grid">
              {muhuratData.muhurtas.map((muhurat, index) => {
                const isActive = currentMuhurat && currentMuhurat.muhurta === muhurat.muhurta;
                
                return (
                  <div key={index} className={`muhurat-card ${isActive ? 'active' : ''}`}>
                    <div className="muhurat-header">
                      <div className="muhurat-number">Muhurta {muhurat.muhurta}</div>
                      {isActive && <div className="active-badge">Active Now</div>}
                    </div>
                    
                    <div className="muhurat-timing">
                      <div className="time-range">
                        <span className="start-time">{formatTime(muhurat.start_time)}</span>
                        <span className="time-separator">-</span>
                        <span className="end-time">{formatTime(muhurat.end_time)}</span>
                      </div>
                      <div className="duration">{muhurat.duration_minutes} minutes</div>
                    </div>
                    
                    <div className="muhurat-suitability">
                      {muhurat.suitability}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="muhurat-guide">
              <h3>📚 Muhurat Guide</h3>
              <div className="guide-content">
                <div className="guide-item">
                  <h4>What is a Muhurat?</h4>
                  <p>A muhurat is an auspicious time period calculated based on planetary positions and Vedic principles. Each day is divided into 15 muhurtas, each lasting approximately 48 minutes.</p>
                </div>
                <div className="guide-item">
                  <h4>How to Use?</h4>
                  <p>Plan your important activities during the highlighted auspicious muhurtas for maximum success and positive outcomes. Avoid inauspicious periods for new beginnings.</p>
                </div>
                <div className="guide-item">
                  <h4>Accuracy</h4>
                  <p>All calculations are based on Swiss Ephemeris astronomical data and traditional Vedic formulas for precise timing.</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MuhuratFinderPage;