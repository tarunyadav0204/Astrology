import React, { useState, useEffect } from 'react';
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
import { panchangService } from './services/panchangService';
import { CALENDAR_SYSTEMS } from './config/panchangConfig';
import './PanchangPage.css';

const PanchangPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [location, setLocation] = useState({
    name: 'New Delhi, India',
    latitude: 28.6139,
    longitude: 77.2090,
    timezone: 'UTC+5:30'
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
      
      // Load all data in parallel
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
      ] = await Promise.all([
        panchangService.calculatePanchang(
          dateString, 
          location.latitude, 
          location.longitude, 
          location.timezone
        ),
        panchangService.calculateSunriseSunset(
          dateString,
          location.latitude,
          location.longitude
        ),
        panchangService.calculateMoonPhase(dateString),
        panchangService.calculatePlanetaryPositions(
          dateString,
          location.latitude,
          location.longitude,
          location.timezone
        ),
        panchangService.getInauspiciousTimes(
          dateString,
          location.latitude,
          location.longitude
        ),
        panchangService.calculateChoghadiya(
          dateString,
          location.latitude,
          location.longitude
        ),
        panchangService.calculateHora(
          dateString,
          location.latitude,
          location.longitude
        ),
        panchangService.calculateSpecialMuhurtas(
          dateString,
          location.latitude,
          location.longitude
        ),
        panchangService.getFestivals(dateString).catch(() => [])
      ]);

      setPanchangData(panchang);
      setSunriseSunsetData(sunriseSunset);
      setLunarData(lunar);
      setPlanetaryData(planetary);
      setInauspiciousData(inauspicious);
      setChoghadiyaData(choghadiya);
      setHoraData(hora);
      setMuhurtaData(muhurta);
      setFestivals(festivalData);

    } catch (err) {
      setError(err.message);
      toast.error(`Failed to load Panchang data: ${err.message}`);
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
          onLogout={onLogout}
          onLogin={onLogin}
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
          onLogout={onLogout}
          onLogin={onLogin}
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

  return (
    <div className="panchang-page">
      <NavigationHeader 
        showZodiacSelector={false}
        user={user}
        onAdminClick={handleAdminClick}
        onLogout={onLogout}
        onLogin={onLogin}
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
          />

          <div className="page-header">
            <h1>Today's Panchang</h1>
            <p>{selectedDate.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })} • {location.name}</p>
          </div>

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