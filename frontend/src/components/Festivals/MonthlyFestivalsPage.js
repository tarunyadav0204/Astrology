import React, { useState, useEffect } from 'react';
import './MonthlyFestivalsPage.css';

const MonthlyFestivalsPage = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [monthlyData, setMonthlyData] = useState({ festivals: [], vrats: [] });
  const [loading, setLoading] = useState(true);
  const [calendarDays, setCalendarDays] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);

  useEffect(() => {
    fetchMonthlyFestivals();
    generateCalendar();
  }, [currentDate]);

  const fetchMonthlyFestivals = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth() + 1;
      
      const response = await fetch(`http://localhost:8001/api/festivals/month/${year}/${month}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMonthlyData(data);
      }
    } catch (error) {
      console.error('Error fetching monthly festivals:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateCalendar = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    const days = [];
    const current = new Date(startDate);
    
    for (let i = 0; i < 42; i++) {
      days.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    
    setCalendarDays(days);
  };

  const getFestivalsForDate = (date) => {
    // Use local date string to avoid timezone issues
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const dateStr = `${year}-${month}-${day}`;
    
    const festivals = monthlyData.festivals.filter(f => f.date === dateStr);
    const vrats = monthlyData.vrats.filter(v => v.date === dateStr);
    return [...festivals, ...vrats];
  };

  const navigateMonth = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() + direction);
    setCurrentDate(newDate);
  };

  const getEventIcon = (event) => {
    // Specific festival icons
    const festivalIcons = {
      'diwali': '🪔',
      'holi': '🌈',
      'dussehra': '🏹',
      'navratri': '💃',
      'janmashtami': '🐄',
      'maha_shivratri': '🔱',
      'ram_navami': '🏹',
      'hanuman_jayanti': '🐒',
      'karva_chauth': '🌙',
      'teej': '🌿',
      'ganesh_chaturthi': '🐘',
      'guru_purnima': '📚',
      'makar_sankranti': '🪁',
      'onam': '🌺',
      'durga_puja': '⚔️'
    };
    
    // Vrat specific icons
    const vratIcons = {
      'ekadashi': '🌕',
      'pradosh': '🔱',
      'sankashti': '🐘',
      'shivaratri': '🌙'
    };
    
    const name = event.name?.toLowerCase() || '';
    
    // Check specific festivals first
    for (const [key, icon] of Object.entries(festivalIcons)) {
      if (name.includes(key)) return icon;
    }
    
    // Check vrats
    for (const [key, icon] of Object.entries(vratIcons)) {
      if (name.includes(key)) return icon;
    }
    
    // Fallback for vrats with deity
    if (event.deity) return '🙏';
    
    // Type-based fallback
    const typeIcons = {
      'major_festival': '🎉',
      'vrat': '🙏',
      'seasonal_festival': '🌾',
      'regional_festival': '🏛️',
      'spiritual_festival': '🕉️'
    };
    
    return typeIcons[event.type] || '🎊';
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="monthly-festivals-page">
      <div className="calendar-header">
        <button 
          className="nav-btn"
          onClick={() => navigateMonth(-1)}
        >
          ‹
        </button>
        <h1>
          {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
        </h1>
        <button 
          className="nav-btn"
          onClick={() => navigateMonth(1)}
        >
          ›
        </button>
      </div>

      <div className="calendar-stats">
        <div className="stat-card">
          <span className="stat-number">{monthlyData.festivals.length}</span>
          <span className="stat-label">Festivals</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">{monthlyData.vrats.length}</span>
          <span className="stat-label">Vrats</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">{monthlyData.festivals.length + monthlyData.vrats.length}</span>
          <span className="stat-label">Total Events</span>
        </div>
      </div>

      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading calendar...</p>
        </div>
      ) : (
        <div className="main-content">
          <div className="calendar-container">
            <div className="calendar-grid">
              {dayNames.map(day => (
                <div key={day} className="day-header">
                  {day}
                </div>
              ))}
              
              {calendarDays.map((day, index) => {
                const events = getFestivalsForDate(day);
                const isCurrentMonth = day.getMonth() === currentDate.getMonth();
                const isToday = day.toDateString() === new Date().toDateString();
                
                return (
                  <div 
                    key={index}
                    className={`calendar-day ${!isCurrentMonth ? 'other-month' : ''} ${isToday ? 'today' : ''}`}
                  >
                    <div className="day-number">
                      {day.getDate()}
                    </div>
                    
                    {events.length > 0 && (
                      <div className="day-events">
                        {events.map((event, idx) => (
                          <div 
                            key={idx}
                            className="event-dot"
                            title={event.name}
                            onClick={() => setSelectedEvent(event)}
                          >
                            <span className="event-icon">{getEventIcon(event)}</span>
                            <span className="event-name">{event.name}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          
          <div className="details-panel">
            {selectedEvent ? (
              <div className="event-details">
                <div className="event-header">
                  <span className="event-icon">{getEventIcon(selectedEvent)}</span>
                  <h3>{selectedEvent.name}</h3>
                </div>
                
                {selectedEvent.description && (
                  <div className="detail-section">
                    <h4>📜 Description</h4>
                    <p>{selectedEvent.description}</p>
                  </div>
                )}
                
                {selectedEvent.significance && (
                  <div className="detail-section">
                    <h4>🌟 Significance</h4>
                    <p>{selectedEvent.significance}</p>
                  </div>
                )}
                
                {selectedEvent.rituals && (
                  <div className="detail-section">
                    <h4>🕯️ Rituals</h4>
                    <ul>
                      {selectedEvent.rituals.map((ritual, idx) => (
                        <li key={idx}>{ritual}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                <div className="detail-section">
                  <h4>📅 Date & Time</h4>
                  <div className="time-info">
                    <p><strong>Date:</strong> {new Date(selectedEvent.date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
                    <p><strong>Start:</strong> 06:30 AM (Sunrise)</p>
                    <p><strong>End:</strong> 06:31 AM next day (Sunrise)</p>
                  </div>
                </div>
                
                {selectedEvent.deity && (
                  <div className="detail-section">
                    <h4>🙏 Deity</h4>
                    <p>{selectedEvent.deity}</p>
                  </div>
                )}
                
                {selectedEvent.benefits && (
                  <div className="detail-section">
                    <h4>✨ Benefits</h4>
                    <p>{selectedEvent.benefits}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="no-selection">
                <div className="no-selection-icon">🎊</div>
                <h3>Select a Festival</h3>
                <p>Click on any festival or vrat in the calendar to see detailed information.</p>
              </div>
            )}
          </div>
        </div>
      )}



      <div className="back-button">
        <button 
          className="btn-back"
          onClick={() => window.history.back()}
        >
          ← Back to Daily Festivals
        </button>
      </div>
    </div>
  );
};

export default MonthlyFestivalsPage;