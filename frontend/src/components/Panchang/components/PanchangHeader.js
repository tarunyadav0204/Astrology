import React from 'react';
import { CALENDAR_SYSTEMS } from '../config/panchangConfig';

const PanchangHeader = ({ 
  selectedDate, 
  onDateChange, 
  location, 
  onLocationChange,
  calendarSystem,
  onCalendarSystemChange,
  festivals,
  showMonthlyLink = false
}) => {
  const isToday = selectedDate.toDateString() === new Date().toDateString();
  const formattedLongDate = selectedDate.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const formatDateForCalendar = (date) => {
    return date.toISOString().split('T')[0];
  };

  const handleDateChange = (event) => {
    const newDate = new Date(event.target.value);
    onDateChange(newDate);
  };

  const navigateDate = (days) => {
    const newDate = new Date(selectedDate);
    newDate.setDate(newDate.getDate() + days);
    onDateChange(newDate);
  };

  const goToToday = () => {
    onDateChange(new Date());
  };

  return (
    <div className="panchang-header">
      <div className="panchang-hero-copy">
        <span className="panchang-eyebrow">Daily Hindu Calendar</span>
        <h1>{isToday ? "Today's Panchang" : "Panchang"} for {formattedLongDate}</h1>
        <p>
          Check tithi, nakshatra, yoga, karana, sunrise, Rahu Kaal, Choghadiya,
          Hora and auspicious muhurat windows for your selected place.
        </p>
        <div className="panchang-hero-tags" aria-label="Panchang highlights">
          <span>Tithi</span>
          <span>Nakshatra</span>
          <span>Muhurat</span>
          <span>Rahu Kaal</span>
        </div>
      </div>

      <div className="header-row">
        <div className="date-navigation-container" aria-label="Date navigation">
          <button className="nav-btn" onClick={() => navigateDate(-1)}>←</button>
          <input 
            type="date" 
            value={formatDateForCalendar(selectedDate)} 
            onChange={handleDateChange} 
            className="date-input" 
          />
          <button className="nav-btn" onClick={() => navigateDate(1)}>→</button>
        </div>
        <button className="today-btn" onClick={goToToday}>Today</button>
        <select 
          value={calendarSystem} 
          onChange={(e) => onCalendarSystemChange(e.target.value)} 
          className="calendar-select"
        >
          <option value={CALENDAR_SYSTEMS.GREGORIAN}>Gregorian</option>
        </select>
        <div className="location-info">
          <span className="location-name">📍 {location.name}</span>
          <button className="change-location-btn" onClick={onLocationChange}>Change</button>
        </div>
        {showMonthlyLink && (
          <a href="/monthly-panchang" className="monthly-panchang-link">
            Monthly Panchang
          </a>
        )}
      </div>

      {festivals?.length > 0 && (
        <div className="festival-banner">
          <span className="festival-icon">Festival</span>
          <span className="festival-text">
            {festivals.map((festival) => festival.name || festival.title || festival).join(', ')}
          </span>
        </div>
      )}
    </div>
  );
};

export default PanchangHeader;
