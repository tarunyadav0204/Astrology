import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'react-toastify';
import NavigationHeader from '../Shared/NavigationHeader';
import PanchangHeader from './components/PanchangHeader';
import LocationFinder from './components/LocationFinder';
import CorePanchangElements from './components/CorePanchangElements';
import SunriseSunsetInfo from './components/SunriseSunsetInfo';
import LunarInformation from './components/LunarInformation';
import PlanetaryPositions from './components/PlanetaryPositions';
import InauspiciousTimings from './components/InauspiciousTimings';
import AuspiciousTimings from './components/AuspiciousTimings';
import SEOHead from '../SEO/SEOHead';
import { panchangService } from './services/panchangService';
import { CALENDAR_SYSTEMS } from './config/panchangConfig';
import { generatePageSEO } from '../../config/seo.config';
import './PanchangPage.css';

const PanchangPage = ({ user: propUser, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const navigate = useNavigate();
  const urlLocation = useLocation();
  const [user, setUser] = useState(propUser);

  useEffect(() => {
    if (!propUser) {
      const token = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user');
      if (token && savedUser) {
        try {
          setUser(JSON.parse(savedUser));
        } catch (e) {
          // Invalid user data
        }
      }
    } else {
      setUser(propUser);
    }
  }, [propUser]);
  const [selectedDate, setSelectedDate] = useState(() => {
    const urlParams = new URLSearchParams(urlLocation.search);
    const dateParam = urlParams.get('date');
    return dateParam ? new Date(dateParam) : new Date();
  });
  const [location, setLocation] = useState({
    name: 'New Delhi, India',
    latitude: 28.6139,
    longitude: 77.2090
    // timezone will be detected by backend
  });
  const [calendarSystem, setCalendarSystem] = useState(CALENDAR_SYSTEMS.GREGORIAN);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showLocationFinder, setShowLocationFinder] = useState(false);
  
  // Data states
  const [panchangData, setPanchangData] = useState(null);
  const [sunriseSunsetData, setSunriseSunsetData] = useState(null);
  const [lunarData, setLunarData] = useState(null);
  const [planetaryData, setPlanetaryData] = useState(null);
  const [inauspiciousData, setInauspiciousData] = useState(null);
  const [choghadiyaData, setChoghadiyaData] = useState(null);
  const [horaData, setHoraData] = useState(null);
  const [muhurtaData, setMuhurtaData] = useState(null);
  const [festivals, setFestivals] = useState([]);

  useEffect(() => {
    loadPanchangData();
  }, [selectedDate, location]);

  const loadPanchangData = async () => {
    setLoading(true);
    setError(null);

    try {
      const dateString = selectedDate.toISOString().split('T')[0];
      
      // Load data with error handling for each service
      const results = await Promise.allSettled([
        panchangService.calculatePanchang(
          dateString, 
          location.latitude, 
          location.longitude
        ).catch(() => null),
        panchangService.calculateSunriseSunset(
          dateString,
          location.latitude,
          location.longitude
        ).catch(() => null),
        panchangService.calculateMoonPhase(dateString).catch(() => null),
        panchangService.calculatePlanetaryPositions(
          dateString,
          location.latitude,
          location.longitude
        ).catch(() => null),
        panchangService.getInauspiciousTimes(
          dateString,
          location.latitude,
          location.longitude
        ).catch(() => null),
        panchangService.calculateChoghadiya(
          dateString,
          location.latitude,
          location.longitude
        ).catch(() => null),
        panchangService.calculateHora(
          dateString,
          location.latitude,
          location.longitude
        ).catch(() => null),
        panchangService.calculateSpecialMuhurtas(
          dateString,
          location.latitude,
          location.longitude
        ).catch(() => null),
        panchangService.getFestivals(dateString).catch(() => [])
      ]);

      // Extract successful results
      const [
        panchang,
        sunriseSunset,
        lunar,
        planetary,
        inauspicious,
        choghadiya,
        hora,
        muhurta,
        festivalData
      ] = results.map(result => result.status === 'fulfilled' ? result.value : null);

      setPanchangData(panchang);
      setSunriseSunsetData(sunriseSunset);
      setLunarData(lunar);
      setPlanetaryData(planetary);
      setInauspiciousData(inauspicious);
      setChoghadiyaData(choghadiya);
      setHoraData(hora);
      setMuhurtaData(muhurta);
      setFestivals(festivalData || []);

    } catch (err) {
      console.error('Panchang loading error:', err);
      // Don't show error toast for API failures, just log them
    } finally {
      setLoading(false);
    }
  };

  const handleDateChange = (newDate) => {
    setSelectedDate(newDate);
  };

  const handleLocationChange = () => {
    setShowLocationFinder(true);
  };
  
  const handleLocationSelect = (newLocation) => {
    setLocation(newLocation);
    toast.success(`Location changed to ${newLocation.name}`);
  };

  const handleCalendarSystemChange = (newSystem) => {
    setCalendarSystem(newSystem);
  };

  const handleAdminClick = () => {
    if (onAdminClick) {
      onAdminClick();
    }
  };

  if (loading) {
    return (
      <div className="panchang-page">
        <NavigationHeader 
          showZodiacSelector={false}
          user={user}
          onAdminClick={handleAdminClick}
          onLogout={onLogout || (() => {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setUser(null);
            navigate('/');
          })}
          onLogin={onLogin || (() => navigate('/'))}
          showLoginButton={showLoginButton}
        />
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <div className="loading-text">Loading Panchang data...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panchang-page">
        <NavigationHeader 
          showZodiacSelector={false}
          user={user}
          onAdminClick={handleAdminClick}
          onLogout={onLogout || (() => {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            setUser(null);
            navigate('/');
          })}
          onLogin={onLogin || (() => navigate('/'))}
          showLoginButton={showLoginButton}
        />
        <div className="error-container">
          <div className="error-message">
            <h3>Error Loading Panchang</h3>
            <p>{error}</p>
            <button 
              className="retry-btn"
              onClick={loadPanchangData}
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const seoData = generatePageSEO('panchang', { path: '/panchang' });

  return (
    <div className="panchang-page">
      <SEOHead 
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={{
          "@context": "https://schema.org",
          "@type": "WebApplication",
          "name": "Daily Panchang",
          "description": "Complete Hindu calendar with Tithi, Nakshatra, Yoga, Karana and muhurat times",
          "applicationCategory": "LifestyleApplication",
          "operatingSystem": "Web"
        }}
      />
      <NavigationHeader 
        compact={true}
        showZodiacSelector={false}
        user={user}
        onAdminClick={handleAdminClick}
        onLogout={onLogout || (() => {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
          navigate('/');
        })}
        onLogin={onLogin || (() => navigate('/'))}
        showLoginButton={showLoginButton}
      />

      <div className="panchang-content">
        <div className="container">
          
          <PanchangHeader
            selectedDate={selectedDate}
            onDateChange={handleDateChange}
            location={location}
            onLocationChange={handleLocationChange}
            calendarSystem={calendarSystem}
            onCalendarSystemChange={handleCalendarSystemChange}
            festivals={festivals}
            showMonthlyLink={true}
          />

          <div className="panchang-section">
            <div className="section-header">
              <h2>🕐 Core Panchang Elements</h2>
            </div>
            <div className="section-content">
              <CorePanchangElements panchangData={panchangData} />
            </div>
          </div>

          <div className="timing-grid">
            
            <div className="timing-card">
              <h3>🌅 Sunrise & Sunset</h3>
              <SunriseSunsetInfo 
                sunriseSunsetData={sunriseSunsetData}
                location={location}
              />
            </div>

            <div className="timing-card">
              <h3>🌙 Lunar Information</h3>
              <LunarInformation 
                lunarData={lunarData}
                panchangData={panchangData}
              />
            </div>

            <div className="timing-card">
              <h3>🚫 Inauspicious Times</h3>
              <InauspiciousTimings 
                inauspiciousData={inauspiciousData}
                sunriseSunsetData={sunriseSunsetData}
                selectedDate={selectedDate}
              />
            </div>

          </div>

          <div className="panchang-section">
            <div className="section-header">
              <h2>✨ Auspicious Times</h2>
            </div>
            <div className="section-content">
              <AuspiciousTimings 
                choghadiyaData={choghadiyaData}
                horaData={horaData}
                muhurtaData={muhurtaData}
                selectedDate={selectedDate}
              />
            </div>
          </div>

          <div className="panchang-section">
            <div className="section-header">
              <h2>⭐ Planetary Positions</h2>
            </div>
            <div className="section-content">
              <PlanetaryPositions planetaryData={planetaryData} />
            </div>
          </div>

        </div>
      </div>
      
      <LocationFinder
        isOpen={showLocationFinder}
        onClose={() => setShowLocationFinder(false)}
        onLocationSelect={handleLocationSelect}
        currentLocation={location}
      />
    </div>
  );
};

export default PanchangPage;