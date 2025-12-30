import React from 'react';

const AuspiciousTimings = ({ choghadiyaData, horaData, muhurtaData, selectedDate }) => {
  if (!choghadiyaData || !horaData || !muhurtaData) {
    return (
      <div className="auspicious-timings">
        <div className="loading-message">
          <p>Loading auspicious timings...</p>
        </div>
      </div>
    );
  }

  const formatTime = (timeString) => {
    if (!timeString) {
      return 'N/A';
    }
    try {
      return new Date(timeString).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
    } catch {
      return 'N/A';
    }
  };

  const isCurrentlyActive = (startTime, endTime) => {
    const now = new Date();
    const start = new Date(startTime);
    const end = new Date(endTime);
    return now >= start && now <= end;
  };

  const getCurrentChoghadiya = () => {
    if (!choghadiyaData || !choghadiyaData.day_choghadiya || !choghadiyaData.night_choghadiya) {
      return null;
    }
    const now = new Date();
    const allChoghadiya = [...choghadiyaData.day_choghadiya, ...choghadiyaData.night_choghadiya];
    return allChoghadiya.find(period => isCurrentlyActive(period.start_time, period.end_time));
  };

  const getCurrentHora = () => {
    if (!horaData || !horaData.day_horas || !horaData.night_horas) {
      return null;
    }
    const now = new Date();
    const allHoras = [...horaData.day_horas, ...horaData.night_horas];
    return allHoras.find(hora => isCurrentlyActive(hora.start_time, hora.end_time));
  };

  const getActiveMuhurtas = () => {
    if (!muhurtaData || !muhurtaData.muhurtas) {
      return [];
    }
    return muhurtaData.muhurtas.filter(muhurta => 
      isCurrentlyActive(muhurta.start_time, muhurta.end_time)
    );
  };

  const currentChoghadiya = getCurrentChoghadiya();
  const currentHora = getCurrentHora();
  const activeMuhurtas = getActiveMuhurtas();

  return (
    <div className="auspicious-timings">
      
      {/* Currently Active Auspicious Periods */}
      {(currentChoghadiya?.quality === 'Good' || currentChoghadiya?.quality === 'Best' || currentChoghadiya?.quality === 'Gain' || currentHora || activeMuhurtas.length > 0) && (
        <div className="active-auspicious">
          <div className="auspicious-header">
            <span className="auspicious-icon">✨</span>
            <span className="auspicious-text">Currently Active Auspicious Periods</span>
          </div>
          <div className="active-periods">
            {(currentChoghadiya?.quality === 'Good' || currentChoghadiya?.quality === 'Best' || currentChoghadiya?.quality === 'Gain') && (
              <div className="active-period">
                <span className="period-icon">🌟</span>
                <span className="period-name">{currentChoghadiya.name} - {currentChoghadiya.quality}</span>
                <span className="period-duration">
                  {formatTime(currentChoghadiya.start_time)} - {formatTime(currentChoghadiya.end_time)}
                </span>
              </div>
            )}
            {currentHora && (
              <div className="active-period">
                <span className="period-icon">⏰</span>
                <span className="period-name">{currentHora.planet} Hora</span>
                <span className="period-duration">
                  {formatTime(currentHora.start_time)} - {formatTime(currentHora.end_time)}
                </span>
              </div>
            )}
            {activeMuhurtas.map((muhurta, index) => (
              <div key={index} className="active-period">
                <span className="period-icon">🕉️</span>
                <span className="period-name">{muhurta.name}</span>
                <span className="period-duration">
                  {formatTime(muhurta.start_time)} - {formatTime(muhurta.end_time)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Special Muhurtas */}
      <div className="timing-section">
        <h4>🕉️ Special Muhurtas</h4>
        <div className="timing-list">
          {muhurtaData && muhurtaData.muhurtas && muhurtaData.muhurtas.map((muhurta, index) => {
            const isActive = isCurrentlyActive(muhurta.start_time, muhurta.end_time);
            
            return (
              <div key={index} className={`timing-item ${isActive ? 'active' : ''}`}>
                <div className="muhurta-header">
                  <span className="timing-name">{muhurta.name}</span>
                  <span className="timing-duration">
                    {formatTime(muhurta.start_time)} - {formatTime(muhurta.end_time)}
                  </span>
                  {isActive && <span className="active-badge">Active Now</span>}
                </div>
                <div className="muhurta-details">
                  <div className="significance">{muhurta.significance}</div>
                  <div className="activities">
                    <strong>Best for:</strong> {muhurta.activities ? muhurta.activities.join(', ') : muhurta.purpose || 'General auspicious activities'}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Choghadiya Periods */}
      <div className="timing-section">
        <h4>🌟 Choghadiya Periods</h4>
        
        <div className="choghadiya-sections">
          <div className="day-choghadiya">
            <h5>Day Choghadiya</h5>
            <div className="choghadiya-list">
              {choghadiyaData && choghadiyaData.day_choghadiya && choghadiyaData.day_choghadiya.map((period, index) => {
                const isActive = isCurrentlyActive(period.start_time, period.end_time);
                
                return (
                  <div key={index} className={`choghadiya-item ${period.quality.toLowerCase()} ${isActive ? 'active' : ''}`}>
                    <div className="choghadiya-header">
                      <span className="choghadiya-name">{period.name}</span>
                      <span className="choghadiya-time">
                        {formatTime(period.start_time)} - {formatTime(period.end_time)}
                      </span>
                      {isActive && <span className="active-indicator">●</span>}
                    </div>
                    <div className="choghadiya-quality">{period.quality}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="night-choghadiya">
            <h5>Night Choghadiya</h5>
            <div className="choghadiya-list">
              {choghadiyaData && choghadiyaData.night_choghadiya && choghadiyaData.night_choghadiya.map((period, index) => {
                const isActive = isCurrentlyActive(period.start_time, period.end_time);
                
                return (
                  <div key={index} className={`choghadiya-item ${period.quality.toLowerCase()} ${isActive ? 'active' : ''}`}>
                    <div className="choghadiya-header">
                      <span className="choghadiya-name">{period.name}</span>
                      <span className="choghadiya-time">
                        {formatTime(period.start_time)} - {formatTime(period.end_time)}
                      </span>
                      {isActive && <span className="active-indicator">●</span>}
                    </div>
                    <div className="choghadiya-quality">{period.quality}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Hora Periods */}
      <div className="timing-section">
        <h4>⏰ Planetary Hours (Hora)</h4>
        
        <div className="hora-sections">
          <div className="day-hora">
            <h5>Day Horas</h5>
            <div className="hora-list">
              {horaData && horaData.day_horas && horaData.day_horas.map((hora, index) => {
                const isActive = isCurrentlyActive(hora.start_time, hora.end_time);
                
                return (
                  <div key={index} className={`hora-item ${isActive ? 'active' : ''}`}>
                    <div className="hora-header">
                      <span className="hora-planet" data-planet={hora.planet}>{hora.planet}</span>
                      <span className="hora-time">
                        {formatTime(hora.start_time)} - {formatTime(hora.end_time)}
                      </span>
                      {isActive && <span className="active-indicator">●</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="night-hora">
            <h5>Night Horas</h5>
            <div className="hora-list">
              {horaData && horaData.night_horas && horaData.night_horas.map((hora, index) => {
                const isActive = isCurrentlyActive(hora.start_time, hora.end_time);
                
                return (
                  <div key={index} className={`hora-item ${isActive ? 'active' : ''}`}>
                    <div className="hora-header">
                      <span className="hora-planet" data-planet={hora.planet}>{hora.planet}</span>
                      <span className="hora-time">
                        {formatTime(hora.start_time)} - {formatTime(hora.end_time)}
                      </span>
                      {isActive && <span className="active-indicator">●</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};

export default AuspiciousTimings;