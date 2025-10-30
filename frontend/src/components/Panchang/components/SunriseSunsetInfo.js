import React from 'react';

const SunriseSunsetInfo = ({ sunriseSunsetData, location }) => {
  if (!sunriseSunsetData) {
    throw new Error('Sunrise/Sunset data is required');
  }

  const formatTime = (timeString) => {
    if (!timeString) {
      throw new Error('Time string is required');
    }
    return new Date(timeString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    });
  };

  const formatDuration = (hours) => {
    if (typeof hours !== 'number') {
      throw new Error('Duration must be a number');
    }
    const h = Math.floor(hours);
    const m = Math.floor((hours - h) * 60);
    return `${h}h ${m}m`;
  };

  const calculateDayProgress = () => {
    const now = new Date();
    const sunrise = new Date(sunriseSunsetData.sunrise);
    const sunset = new Date(sunriseSunsetData.sunset);
    
    if (now < sunrise) return 0;
    if (now > sunset) return 100;
    
    const totalDaylight = sunset - sunrise;
    const elapsed = now - sunrise;
    return (elapsed / totalDaylight) * 100;
  };

  return (
    <div className="sunrise-sunset-info">

      <div className="timing-grid">
        
        {/* Sunrise Information */}
        <div className="timing-card sunrise-card">
          <div className="timing-icon">🌅</div>
          <div className="timing-details">
            <h4>Sunrise</h4>
            <div className="main-time">{formatTime(sunriseSunsetData.sunrise)}</div>
            <div className="additional-info">
              <span>Civil Twilight: {formatTime(sunriseSunsetData.civil_twilight_begin)}</span>
            </div>
          </div>
        </div>

        {/* Sunset Information */}
        <div className="timing-card sunset-card">
          <div className="timing-icon">🌇</div>
          <div className="timing-details">
            <h4>Sunset</h4>
            <div className="main-time">{formatTime(sunriseSunsetData.sunset)}</div>
            <div className="additional-info">
              <span>Civil Twilight: {formatTime(sunriseSunsetData.civil_twilight_end)}</span>
            </div>
          </div>
        </div>

        {/* Moonrise Information */}
        <div className="timing-card moonrise-card">
          <div className="timing-icon">🌙</div>
          <div className="timing-details">
            <h4>Moonrise</h4>
            <div className="main-time">{formatTime(sunriseSunsetData.moonrise)}</div>
            <div className="additional-info">
              <span>Moon Phase: {sunriseSunsetData.moon_phase}</span>
            </div>
          </div>
        </div>

        {/* Moonset Information */}
        <div className="timing-card moonset-card">
          <div className="timing-icon">🌚</div>
          <div className="timing-details">
            <h4>Moonset</h4>
            <div className="main-time">{formatTime(sunriseSunsetData.moonset)}</div>
            <div className="additional-info">
              <span>Illumination: {sunriseSunsetData.moon_illumination}%</span>
            </div>
          </div>
        </div>

      </div>

      {/* Day/Night Duration */}
      <div className="duration-info">
        <div className="duration-card">
          <h4>☀️ Day Duration</h4>
          <div className="duration-value">{formatDuration(sunriseSunsetData.day_duration)}</div>
        </div>
        
        <div className="duration-card">
          <h4>🌙 Night Duration</h4>
          <div className="duration-value">{formatDuration(sunriseSunsetData.night_duration)}</div>
        </div>
      </div>

      {/* Day Progress */}
      <div className="day-progress">
        <h4>Day Progress</h4>
        <div className="progress-container">
          <div className="progress-bar">
            <div 
              className="progress-fill daylight-progress"
              style={{ width: `${calculateDayProgress()}%` }}
            ></div>
          </div>
          <div className="progress-labels">
            <span>Sunrise</span>
            <span>Sunset</span>
          </div>
        </div>
      </div>

      <div className="timing-section">
        <h4>🕉️ Special Timings</h4>
        <div className="timing-list">
          <div className="timing-item">
            <span className="timing-name">Brahma Muhurta</span>
            <span className="timing-duration">{formatTime(sunriseSunsetData.brahma_muhurta_start)} - {formatTime(sunriseSunsetData.brahma_muhurta_end)}</span>
            <span className="timing-description">Most auspicious time for spiritual practices</span>
          </div>
          
          <div className="timing-item">
            <span className="timing-name">Abhijit Muhurta</span>
            <span className="timing-duration">{formatTime(sunriseSunsetData.abhijit_muhurta_start)} - {formatTime(sunriseSunsetData.abhijit_muhurta_end)}</span>
            <span className="timing-description">Universal auspicious time</span>
          </div>
          
          <div className="timing-item">
            <span className="timing-name">Godhuli Muhurta</span>
            <span className="timing-duration">{formatTime(sunriseSunsetData.godhuli_muhurta_start)} - {formatTime(sunriseSunsetData.godhuli_muhurta_end)}</span>
            <span className="timing-description">Evening auspicious time</span>
          </div>
        </div>
      </div>

      <div className="timing-section">
        <h4>🌆 Twilight Timings</h4>
        <div className="timing-list">
          <div className="timing-item">
            <span className="timing-name">Civil Twilight</span>
            <span className="timing-duration">{formatTime(sunriseSunsetData.civil_twilight_begin)}</span>
            <span className="timing-duration">{formatTime(sunriseSunsetData.civil_twilight_end)}</span>
          </div>
          
          <div className="timing-item">
            <span className="timing-name">Nautical Twilight</span>
            <span className="timing-duration">{formatTime(sunriseSunsetData.nautical_twilight_begin)}</span>
            <span className="timing-duration">{formatTime(sunriseSunsetData.nautical_twilight_end)}</span>
          </div>
          
          <div className="timing-item">
            <span className="timing-name">Astronomical Twilight</span>
            <span className="timing-duration">{formatTime(sunriseSunsetData.astronomical_twilight_begin)}</span>
            <span className="timing-duration">{formatTime(sunriseSunsetData.astronomical_twilight_end)}</span>
          </div>
        </div>
      </div>

    </div>
  );
};

export default SunriseSunsetInfo;