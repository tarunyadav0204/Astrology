import React, { useEffect, useState } from 'react';
import { panchangService } from '../services/panchangService';

const DAYLIGHT_SEGMENTS = {
  rahuKaal: { 0: 7, 1: 1, 2: 6, 3: 4, 4: 5, 5: 3, 6: 2 },
  yamaganda: { 0: 4, 1: 3, 2: 2, 3: 1, 4: 0, 5: 6, 6: 5 },
  gulika: { 0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0 }
};

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const InauspiciousTimings = ({ inauspiciousData, sunriseSunsetData, selectedDate, location }) => {
  const [weeklyRahuKaal, setWeeklyRahuKaal] = useState([]);

  useEffect(() => {
    let isMounted = true;

    const loadWeeklyRahuKaal = async () => {
      if (!selectedDate || !location?.latitude || !location?.longitude) {
        setWeeklyRahuKaal([]);
        return;
      }

      const weekStart = new Date(selectedDate);
      weekStart.setDate(selectedDate.getDate() - selectedDate.getDay());

      try {
        const rows = await Promise.all(
          DAY_NAMES.map(async (day, index) => {
            const date = new Date(weekStart);
            date.setDate(weekStart.getDate() + index);
            const dateString = date.toISOString().split('T')[0];
            const result = await panchangService.getRahuKaal(dateString, location.latitude, location.longitude);
            return {
              day,
              date,
              start_time: result?.rahu_kaal_start,
              end_time: result?.rahu_kaal_end
            };
          })
        );

        if (isMounted) {
          setWeeklyRahuKaal(rows);
        }
      } catch (error) {
        console.error('Failed to load weekly Rahu Kaal:', error);
        if (isMounted) {
          setWeeklyRahuKaal([]);
        }
      }
    };

    loadWeeklyRahuKaal();

    return () => {
      isMounted = false;
    };
  }, [selectedDate, location?.latitude, location?.longitude]);

  if (!inauspiciousData || !sunriseSunsetData) {
    return (
      <div className="inauspicious-timings">
        <div className="loading-message">
          <p>Loading inauspicious timings...</p>
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

  const calculateDaylightSegment = (sunriseTime, sunsetTime, segmentIndex) => {
    const sunrise = new Date(sunriseTime);
    const sunset = new Date(sunsetTime);

    if (Number.isNaN(sunrise.getTime()) || Number.isNaN(sunset.getTime())) {
      return { start: null, end: null };
    }

    const segmentDurationMs = (sunset.getTime() - sunrise.getTime()) / 8;
    const startTime = new Date(sunrise.getTime() + (segmentIndex * segmentDurationMs));
    const endTime = new Date(startTime.getTime() + segmentDurationMs);
    
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

  const backendOrSegment = (backendPeriod, segmentType) => {
    if (backendPeriod?.start_time && backendPeriod?.end_time) {
      return {
        start: backendPeriod.start_time,
        end: backendPeriod.end_time
      };
    }

    return calculateDaylightSegment(
      sunriseSunsetData.sunrise,
      sunriseSunsetData.sunset,
      DAYLIGHT_SEGMENTS[segmentType][weekday]
    );
  };
  
  const rahuKaalTiming = backendOrSegment(inauspiciousData.rahu_kaal, 'rahuKaal');
  const yamagandaTiming = backendOrSegment(inauspiciousData.yamaganda, 'yamaganda');
  const gulikaTiming = backendOrSegment(inauspiciousData.gulika, 'gulika');

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
    ...(inauspiciousData.dur_muhurta || []).map(timing => ({
      name: 'Dur Muhurta',
      description: 'General inauspicious period',
      start_time: timing.start_time,
      end_time: timing.end_time,
      severity: 'Low',
      avoid_activities: timing.avoid_activities || ['General activities'],
      icon: '⚠️',
      color: '#f39c12'
    })),
    ...(inauspiciousData.varjyam || []).map(timing => ({
      name: 'Varjyam',
      description: 'Time to avoid specific activities',
      start_time: timing.start_time,
      end_time: timing.end_time,
      severity: 'Medium',
      avoid_activities: timing.specific_activities || ['Specific activities'],
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
        <h4>📅 Weekly Rahu Kaal Timings</h4>
        <div className="pattern-grid">
          {DAY_NAMES.map((day, index) => {
            const isToday = index === weekday;
            const apiTiming = weeklyRahuKaal[index];
            const fallbackTiming = calculateDaylightSegment(
              sunriseSunsetData.sunrise,
              sunriseSunsetData.sunset,
              DAYLIGHT_SEGMENTS.rahuKaal[index]
            );
            const startTime = apiTiming?.start_time || fallbackTiming.start;
            const endTime = apiTiming?.end_time || fallbackTiming.end;
            
            return (
              <div key={day} className={`pattern-item ${isToday ? 'today' : ''}`}>
                <div className="day-name">{day}</div>
                <div className="timing-info">
                  {formatTime(startTime)} - {formatTime(endTime)}
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
