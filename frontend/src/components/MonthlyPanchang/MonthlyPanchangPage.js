import React, { useState, useEffect } from 'react';
import './MonthlyPanchangPage.css';

const MonthlyPanchangPage = () => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [monthlyData, setMonthlyData] = useState(null);
  const [selectedDayData, setSelectedDayData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [location] = useState({ latitude: 28.6139, longitude: 77.2090 }); // Default Delhi

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  useEffect(() => {
    fetchMonthlyData();
  }, [selectedDate]);

  const fetchMonthlyData = async () => {
    setLoading(true);
    try {
      const year = selectedDate.getFullYear();
      const month = selectedDate.getMonth() + 1;
      
      const response = await fetch(
        `/api/panchang/monthly?year=${year}&month=${month}&latitude=${location.latitude}&longitude=${location.longitude}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setMonthlyData(data);
        
        // Auto-select today if in current month
        const today = new Date();
        if (year === today.getFullYear() && month === today.getMonth() + 1) {
          const todayData = data.days.find(day => day.day === today.getDate());
          if (todayData) {
            setSelectedDayData(todayData);
          }
        }
      }
    } catch (error) {
      console.error('Error fetching monthly panchang:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDateChange = (direction) => {
    const newDate = new Date(selectedDate);
    newDate.setMonth(newDate.getMonth() + direction);
    setSelectedDate(newDate);
    setSelectedDayData(null);
  };

  const handleDayClick = (dayData) => {
    setSelectedDayData(dayData);
  };

  const renderCalendar = () => {
    if (!monthlyData) return null;

    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    const calendarDays = [];
    
    // Empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      calendarDays.push(<div key={`empty-${i}`} className="calendar-day empty"></div>);
    }
    
    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const dayData = monthlyData.days.find(d => d.day === day);
      const isToday = new Date().toDateString() === new Date(year, month, day).toDateString();
      const isSelected = selectedDayData && selectedDayData.day === day;
      
      calendarDays.push(
        <div
          key={day}
          className={`calendar-day ${isToday ? 'today' : ''} ${isSelected ? 'selected' : ''}`}
          onClick={() => handleDayClick(dayData)}
        >
          <div className="day-number">{day}</div>
          {dayData && (
            <div className="day-info">
              <div className="tithi">{dayData.basic_panchang.tithi.name}</div>
              <div className="nakshatra">{dayData.basic_panchang.nakshatra.name}</div>
            </div>
          )}
        </div>
      );
    }
    
    return calendarDays;
  };

  const renderDetailedPanel = () => {
    if (!selectedDayData) {
      return (
        <div className="no-selection">
          <h3>Select a date from the calendar</h3>
          <p>Click on any date to view detailed panchang information</p>
        </div>
      );
    }

    const data = selectedDayData;
    
    return (
      <div className="detailed-panel">
        <div className="panel-header">
          <div className="date-info">
            <h2>{new Date(data.date).toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}</h2>
            <div className="download-ics">
              <button className="ics-btn">📅 ICS File Download</button>
            </div>
          </div>
        </div>

        <div className="panel-content">
          {/* Clock Section */}
          <div className="section clock-section">
            <h3>🕐 Time</h3>
            <div className="clock-formats">
              <div className="clock-item">
                <span className="label">12 Hour:</span>
                <span className="value">{new Date().toLocaleTimeString('en-US', { hour12: true })}</span>
              </div>
              <div className="clock-item">
                <span className="label">24 Hour:</span>
                <span className="value">{new Date().toLocaleTimeString('en-US', { hour12: false })}</span>
              </div>
            </div>
          </div>

          {/* Sun & Moon Section */}
          <div className="section sun-moon-section">
            <h3>☀️ Sun & Moon</h3>
            <div className="sun-moon-grid">
              <div className="sun-moon-item">
                <span className="label">Sunrise:</span>
                <span className="value">{data.sunrise_sunset?.sunrise || 'N/A'}</span>
              </div>
              <div className="sun-moon-item">
                <span className="label">Sunset:</span>
                <span className="value">{data.sunrise_sunset?.sunset || 'N/A'}</span>
              </div>
              <div className="sun-moon-item">
                <span className="label">Moonrise:</span>
                <span className="value">{data.sunrise_sunset?.moonrise || 'N/A'}</span>
              </div>
              <div className="sun-moon-item">
                <span className="label">Moonset:</span>
                <span className="value">{data.sunrise_sunset?.moonset || 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Samvat Section */}
          <div className="section samvat-section">
            <h3>📅 Calendar Systems</h3>
            <div className="samvat-grid">
              <div className="samvat-item">
                <span className="label">Shaka Samvat:</span>
                <span className="value">{data.calendar_info?.shaka_samvat}</span>
              </div>
              <div className="samvat-item">
                <span className="label">Vikram Samvat:</span>
                <span className="value">{data.calendar_info?.vikram_samvat}</span>
              </div>
              <div className="samvat-item">
                <span className="label">Gujarati Samvat:</span>
                <span className="value">{data.calendar_info?.gujarati_samvat}</span>
              </div>
            </div>
          </div>

          {/* Lunar Months */}
          <div className="section lunar-section">
            <h3>🌙 Lunar Calendar</h3>
            <div className="lunar-grid">
              <div className="lunar-item">
                <span className="label">Amanta Month:</span>
                <span className="value">{data.calendar_info?.amanta_month}</span>
              </div>
              <div className="lunar-item">
                <span className="label">Purnimanta Month:</span>
                <span className="value">{data.calendar_info?.purnimanta_month}</span>
              </div>
              <div className="lunar-item">
                <span className="label">Paksha:</span>
                <span className="value">{data.calendar_info?.paksha}</span>
              </div>
            </div>
          </div>

          {/* Panchang Elements */}
          <div className="section panchang-section">
            <h3>🕉️ Panchang Elements</h3>
            <div className="panchang-grid">
              <div className="panchang-item">
                <span className="label">Weekday:</span>
                <span className="value">{data.weekday}</span>
              </div>
              <div className="panchang-item">
                <span className="label">Tithi:</span>
                <span className="value">{data.basic_panchang?.tithi?.name}</span>
              </div>
              <div className="panchang-item">
                <span className="label">Nakshatra:</span>
                <span className="value">{data.basic_panchang?.nakshatra?.name}</span>
              </div>
              <div className="panchang-item">
                <span className="label">Yoga:</span>
                <span className="value">{data.basic_panchang?.yoga?.name}</span>
              </div>
              <div className="panchang-item">
                <span className="label">Karana:</span>
                <span className="value">{data.basic_panchang?.karana?.name}</span>
              </div>
            </div>
          </div>

          {/* Planetary Signs */}
          <div className="section planetary-section">
            <h3>🪐 Planetary Positions</h3>
            <div className="planetary-grid">
              <div className="planetary-item">
                <span className="label">Sun Sign:</span>
                <span className="value">{data.moon_info?.sun_sign}</span>
              </div>
              <div className="planetary-item">
                <span className="label">Moon Sign:</span>
                <span className="value">{data.moon_info?.moon_sign}</span>
              </div>
            </div>
          </div>

          {/* Inauspicious Times */}
          <div className="section inauspicious-section">
            <h3>⚠️ Inauspicious Times</h3>
            <div className="inauspicious-grid">
              {data.special_times?.rahu_kalam && (
                <div className="inauspicious-item">
                  <span className="label">Rahu Kalam:</span>
                  <span className="value">{data.special_times.rahu_kalam.start} to {data.special_times.rahu_kalam.end}</span>
                </div>
              )}
              {data.special_times?.gulikai_kalam && (
                <div className="inauspicious-item">
                  <span className="label">Gulikai Kalam:</span>
                  <span className="value">{data.special_times.gulikai_kalam.start} to {data.special_times.gulikai_kalam.end}</span>
                </div>
              )}
              {data.special_times?.yamaganda && (
                <div className="inauspicious-item">
                  <span className="label">Yamaganda:</span>
                  <span className="value">{data.special_times.yamaganda.start} to {data.special_times.yamaganda.end}</span>
                </div>
              )}
              {data.special_times?.dur_muhurtam?.map((dur, index) => (
                <div key={index} className="inauspicious-item">
                  <span className="label">Dur Muhurtam:</span>
                  <span className="value">{dur.start} to {dur.end}</span>
                </div>
              ))}
              {data.special_times?.varjyam && (
                <div className="inauspicious-item">
                  <span className="label">Varjyam:</span>
                  <span className="value">{data.special_times.varjyam.start} to {data.special_times.varjyam.end}</span>
                </div>
              )}
            </div>
          </div>

          {/* Auspicious Times */}
          <div className="section auspicious-section">
            <h3>✨ Auspicious Times</h3>
            <div className="auspicious-grid">
              {data.special_times?.abhijit && (
                <div className="auspicious-item">
                  <span className="label">Abhijit:</span>
                  <span className="value">{data.special_times.abhijit.start} to {data.special_times.abhijit.end}</span>
                </div>
              )}
              {data.special_times?.amrit_kalam?.map((amrit, index) => (
                <div key={index} className="auspicious-item">
                  <span className="label">Amrit Kalam:</span>
                  <span className="value">{amrit.start} to {amrit.end}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="monthly-panchang-page">
      <div className="page-header">
        <h1>Monthly Panchang</h1>
        <p>Complete Vedic calendar with daily panchang details</p>
      </div>

      <div className="panchang-container">
        {/* Calendar Section */}
        <div className="calendar-section">
          <div className="calendar-header">
            <button className="nav-btn" onClick={() => handleDateChange(-1)}>
              ‹
            </button>
            <h2>{monthNames[selectedDate.getMonth()]} {selectedDate.getFullYear()}</h2>
            <button className="nav-btn" onClick={() => handleDateChange(1)}>
              ›
            </button>
          </div>

          <div className="calendar-weekdays">
            <div className="weekday">Sun</div>
            <div className="weekday">Mon</div>
            <div className="weekday">Tue</div>
            <div className="weekday">Wed</div>
            <div className="weekday">Thu</div>
            <div className="weekday">Fri</div>
            <div className="weekday">Sat</div>
          </div>

          <div className="calendar-grid">
            {loading ? (
              <div className="loading">Loading calendar...</div>
            ) : (
              renderCalendar()
            )}
          </div>
        </div>

        {/* Detailed Panel */}
        <div className="details-section">
          {renderDetailedPanel()}
        </div>
      </div>
    </div>
  );
};

export default MonthlyPanchangPage;