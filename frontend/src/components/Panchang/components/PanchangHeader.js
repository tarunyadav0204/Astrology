import React from 'react';
import { CALENDAR_SYSTEMS } from '../config/panchangConfig';

const PanchangHeader = ({ 
  selectedDate, 
  onDateChange, 
  location, 
  onLocationChange,
  calendarSystem,
  onCalendarSystemChange,
  festivals 
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
      <div className="single-row-header">
        <button className="nav-btn" onClick={() => navigateDate(-1)}>←</button>
        <input type="date" value={formatDateForCalendar(selectedDate)} onChange={handleDateChange} className="date-input" />
        <button className="today-btn" onClick={goToToday}>Today</button>
        <button className="nav-btn" onClick={() => navigateDate(1)}>→</button>
        <select value={calendarSystem} onChange={(e) => onCalendarSystemChange(e.target.value)} className="calendar-select">
          <option value={CALENDAR_SYSTEMS.GREGORIAN}>Gregorian</option>
        </select>
        <span className="location-icon">📍</span>
        <span className="location-text">{location.name}</span>
        <button className="change-location-btn" onClick={onLocationChange}>Change</button>
        <h1 className="main-date">
          {selectedDate.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </h1>
      </div>
    </div>
  );
};

export default PanchangHeader;