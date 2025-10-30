import React from 'react';
import { RAHU_KAAL_TIMINGS, YAMAGANDA_TIMINGS, GULIKA_TIMINGS } from '../config/panchangConfig';

const InauspiciousTimings = ({ inauspiciousData, sunriseSunsetData, selectedDate }) => {
  if (!inauspiciousData || !sunriseSunsetData) {
    throw new Error('Inauspicious timings data and sunrise/sunset data are required');
  }

  const formatTime = (timeString) => {
    if (!timeString) {
      throw new Error('Time string is required');
    }
    return new Date(timeString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const calculateTimingFromSunrise = (sunriseTime, startHour, duration) => {
    const sunrise = new Date(sunriseTime);
    const startTime = new Date(sunrise.getTime() + (startHour * 60 * 60 * 1000));
    const endTime = new Date(startTime.getTime() + (duration * 60 * 60 * 1000));
    
    return {
      start: startTime.toISOString(),
      end: endTime.toISOString()
    };
  };

  const isCurrentlyActive = (startTime, endTime) => {
    const now = new Date();
    const start = new Date(startTime);
    const end = new Date(endTime);
    return now >= start && now <= end;
  };

  const getWeekday = (date) => {
    return date.getDay(); // 0 = Sunday, 1 = Monday, etc.
  };

  const weekday = getWeekday(selectedDate);
  
  // Calculate standard timings based on sunrise
  const rahuKaalTiming = calculateTimingFromSunrise(
    sunriseSunsetData.sunrise,
    RAHU_KAAL_TIMINGS[weekday].start,
    RAHU_KAAL_TIMINGS[weekday].duration
  );
  
  const yamagandaTiming = calculateTimingFromSunrise(
    sunriseSunsetData.sunrise,
    YAMAGANDA_TIMINGS[weekday].start,
    YAMAGANDA_TIMINGS[weekday].duration
  );
  
  const gulikaTiming = calculateTimingFromSunrise(
    sunriseSunsetData.sunrise,
    GULIKA_TIMINGS[weekday].start,
    GULIKA_TIMINGS[weekday].duration
  );

  const inauspiciousTimings = [
    {
      name: 'Rahu Kaal',
      description: 'Period ruled by Rahu - avoid new beginnings',
      start_time: rahuKaalTiming.start,
      end_time: rahuKaalTiming.end,
      severity: 'High',
      avoid_activities: ['New ventures', 'Important meetings', 'Travel', 'Investments'],
      icon: '👹',
      color: '#e74c3c'
    },
    {
      name: 'Yamaganda Kaal',
      description: 'Death-related inauspicious period',
      start_time: yamagandaTiming.start,
      end_time: yamagandaTiming.end,
      severity: 'Medium',
      avoid_activities: ['Medical procedures', 'Risky activities', 'Important decisions'],
      icon: '💀',
      color: '#8e44ad'
    },
    {
      name: 'Gulika Kaal',
      description: 'Saturn\'s inauspicious period',
      start_time: gulikaTiming.start,
      end_time: gulikaTiming.end,
      severity: 'Medium',
      avoid_activities: ['Celebrations', 'Auspicious ceremonies', 'New purchases'],
      icon: '🪐',
      color: '#34495e'
    },
    ...inauspiciousData.dur_muhurta.map(timing => ({
      name: 'Dur Muhurta',
      description: 'General inauspicious period',
      start_time: timing.start_time,
      end_time: timing.end_time,
      severity: 'Low',
      avoid_activities: timing.avoid_activities,
      icon: '⚠️',
      color: '#f39c12'
    })),
    ...inauspiciousData.varjyam.map(timing => ({
      name: 'Varjyam',
      description: 'Time to avoid specific activities',
      start_time: timing.start_time,
      end_time: timing.end_time,
      severity: 'Medium',
      avoid_activities: timing.specific_activities,
      icon: '🚫',
      color: '#e67e22'
    }))
  ];

  const getCurrentlyActiveTimings = () => {
    return inauspiciousTimings.filter(timing => 
      isCurrentlyActive(timing.start_time, timing.end_time)
    );
  };

  const activeTimings = getCurrentlyActiveTimings();

  return (
    <div className="inauspicious-timings">

      {/* Currently Active Warning */}
      {activeTimings.length > 0 && (
        <div className="active-warning">
          <div className="warning-header">
            <span className="warning-icon">⚠️</span>
            <span className="warning-text">Currently Active Inauspicious Period</span>
          </div>
          <div className="active-timings">
            {activeTimings.map((timing, index) => (
              <div key={index} className="active-timing">
                <span className="timing-icon">{timing.icon}</span>
                <span className="timing-name">{timing.name}</span>
                <span className="timing-duration">
                  {formatTime(timing.start_time)} - {formatTime(timing.end_time)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="timings-grid">
        {inauspiciousTimings.map((timing, index) => {
          const isActive = isCurrentlyActive(timing.start_time, timing.end_time);
          
          return (
            <div 
              key={index} 
              className={`timing-card ${isActive ? 'active' : ''}`}
              style={{ borderLeftColor: timing.color }}
            >
              <div className="timing-header">
                <div className="timing-title">
                  <span className="timing-icon">{timing.icon}</span>
                  <span className="timing-name">{timing.name}</span>
                </div>
                <div className={`severity-badge ${timing.severity.toLowerCase()}`}>
                  {timing.severity}
                </div>
              </div>

              <div className="timing-content">
                <div className="timing-duration">
                  <div className="time-range">
                    <span className="start-time">{formatTime(timing.start_time)}</span>
                    <span className="time-separator">-</span>
                    <span className="end-time">{formatTime(timing.end_time)}</span>
                  </div>
                  
                  {isActive && (
                    <div className="active-indicator">
                      <span className="pulse-dot"></span>
                      <span className="active-text">Active Now</span>
                    </div>
                  )}
                </div>

                <div className="timing-description">
                  {timing.description}
                </div>

                <div className="avoid-activities">
                  <h5>Avoid These Activities:</h5>
                  <div className="activities-list">
                    {timing.avoid_activities.map((activity, actIndex) => (
                      <span key={actIndex} className="activity-tag">
                        {activity}
                      </span>
                    ))}
                  </div>
                </div>

                {timing.remedies && (
                  <div className="timing-remedies">
                    <h5>Remedies:</h5>
                    <div className="remedies-list">
                      {timing.remedies.map((remedy, remIndex) => (
                        <div key={remIndex} className="remedy-item">
                          {remedy}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="general-advice">
        <h5>General Advice:</h5>
        <ul>
          <li>Use inauspicious periods for routine work, cleaning, or spiritual practices</li>
          <li>Avoid starting new ventures or making important decisions</li>
          <li>Emergency activities can be performed with proper remedies</li>
          <li>Rahu Kaal is the most important period to avoid</li>
        </ul>
      </div>

      {/* Weekly Pattern */}
      <div className="weekly-pattern">
        <h4>📅 Weekly Rahu Kaal Pattern</h4>
        <div className="pattern-grid">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day, index) => {
            const timing = RAHU_KAAL_TIMINGS[index];
            const isToday = index === weekday;
            
            return (
              <div key={day} className={`pattern-item ${isToday ? 'today' : ''}`}>
                <div className="day-name">{day}</div>
                <div className="timing-info">
                  {timing.start}:00 - {timing.start + timing.duration}:00
                </div>
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
};

export default InauspiciousTimings;