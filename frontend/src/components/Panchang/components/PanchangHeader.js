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
      <div className="header-row">
        <div className="date-navigation-container">
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
          <span>📍 {location.name}</span>
          <button className="change-location-btn" onClick={onLocationChange}>Change</button>
        </div>
        {showMonthlyLink && (
          <a href="/monthly-panchang" className="monthly-panchang-link">
            📅 View Monthly Panchang Calendar
          </a>
        )}
      </div>
      <div className="date-display">
        <h1>{selectedDate.toDateString() === new Date().toDateString() ? "Today's" : ""} Panchang - {selectedDate.toLocaleDateString('en-US', { 
          weekday: 'long', 
          year: 'numeric', 
          month: 'long', 
          day: 'numeric' 
        })}</h1>
      </div>
    </div>
  );
};

export default PanchangHeader;