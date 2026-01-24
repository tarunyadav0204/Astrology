import React, { useState, useEffect } from 'react';
import NavigationHeader from '../Shared/NavigationHeader';
import { APP_CONFIG } from '../../config/app.config';

const Calendar2026 = ({ user, onLogout, onLogin }) => {
  const [currentMonth, setCurrentMonth] = useState(0);
  const [calendarData, setCalendarData] = useState({});
  const [loading, setLoading] = useState(true);
  const [location, setLocation] = useState(() => {
    const saved = localStorage.getItem('astroRoshni_location');
    return saved ? JSON.parse(saved) : { lat: 28.6139, lon: 77.2090, name: 'Delhi, India' };
  });
  const [showLocationPicker, setShowLocationPicker] = useState(false);
  const [userTimezone, setUserTimezone] = useState(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch {
      return 'Asia/Kolkata';
    }
  });

  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  useEffect(() => {
    loadCalendarData();
  }, [currentMonth, location]);

  const loadCalendarData = async () => {
    setLoading(true);
    try {
      const year = 2026;
      const month = currentMonth + 1;
      
      const API_BASE_URL = process.env.NODE_ENV === 'production' 
        ? APP_CONFIG.api.prod 
        : APP_CONFIG.api.dev;
      
      const [panchangResponse, festivalResponse, transitResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/panchang/monthly?year=${year}&month=${month}&latitude=${location.lat}&longitude=${location.lon}&timezone=${encodeURIComponent(userTimezone)}`),
        fetch(`${API_BASE_URL}/api/festivals/month/${year}/${month}?lat=${location.lat}&lon=${location.lon}&timezone=${encodeURIComponent(userTimezone)}`),
        fetch(`${API_BASE_URL}/api/transits/monthly/${year}/${month}`)
      ]);
      
      if (panchangResponse.ok && festivalResponse.ok) {
        const panchangData = await panchangResponse.json();
        const festivalData = await festivalResponse.json();
        const transitData = transitResponse.ok ? await transitResponse.json() : { transits: [] };
        
        const monthData = {};
        const daysInMonth = getDaysInMonth(currentMonth);
        
        for (let day = 1; day <= daysInMonth; day++) {
          const dateStr = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
          
          const dayData = panchangData.days?.find(d => d.date === dateStr) || {};
          const panchang = dayData.basic_panchang || {};
          
          const allFestivals = [...(festivalData.festivals || []), ...(festivalData.vrats || [])];
          const festivals = allFestivals.filter(f => f.date === dateStr) || [];
          const transits = transitData.transits?.filter(t => t.date === dateStr) || [];
          
          monthData[day] = {
            panchang,
            festivals,
            transits,
            tithi: panchang.tithi?.name || panchang.tithi || '',
            nakshatra: panchang.nakshatra?.name || panchang.nakshatra || '',
            vara: panchang.vara?.name || panchang.vara || ''
          };
        }
        
        setCalendarData(monthData);
      } else {
        throw new Error('API response not ok');
      }
    } catch (error) {
      console.error('Error loading calendar data:', error);
      setCalendarData({});
    }
    setLoading(false);
  };

  const getDaysInMonth = (month) => {
    const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    return daysInMonth[month];
  };

  const getFirstDayOfMonth = (month) => {
    const firstDays = [3, 0, 0, 3, 5, 1, 3, 6, 2, 4, 0, 2];
    return firstDays[month];
  };

  const renderCalendar = () => {
    const daysInMonth = getDaysInMonth(currentMonth);
    const firstDay = getFirstDayOfMonth(currentMonth);
    const days = [];

    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} style={{ height: '120px', border: '1px solid #e0e0e0' }}></div>);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const dayData = calendarData[day] || {};
      const hasFestivals = dayData.festivals && dayData.festivals.length > 0;
      
      days.push(
        <div key={day} style={{
          height: '120px',
          border: '1px solid #e0e0e0',
          padding: '5px',
          backgroundColor: '#ffffff',
          color: '#333333',
          overflow: 'hidden'
        }}>
          <div style={{ fontWeight: 'bold', marginBottom: '2px' }}>{day}</div>
          
          {dayData.tithi && (
            <div style={{
              fontSize: '10px',
              background: '#ffd700',
              color: '#000',
              padding: '2px 6px',
              marginBottom: '1px',
              borderRadius: '8px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: 'inline-block',
              width: 'fit-content'
            }}>
              <div className="day-tithi">
                {dayData.tithi}
                {dayData.panchang?.tithi?.tithi_end_time && (
                  <div className="tithi-ends-grid" style={{
                    fontSize: '8px',
                    color: '#666',
                    marginTop: '1px'
                  }}>
                    Ends {dayData.panchang.tithi.tithi_end_time}
                  </div>
                )}
              </div>
            </div>
          )}
          
          {dayData.nakshatra && (
            <div style={{
              fontSize: '10px',
              background: '#87ceeb',
              color: '#000',
              padding: '2px 6px',
              marginBottom: '1px',
              borderRadius: '8px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: 'inline-block',
              width: 'fit-content'
            }}>
              {dayData.nakshatra}
            </div>
          )}
          
          {hasFestivals && dayData.festivals.map((festival, idx) => (
            <div key={idx} style={{
              fontSize: '10px',
              background: festival.type === 'major_festival' ? '#ff6f00' : 
                         festival.type === 'national' ? '#ff6f00' : 
                         festival.type === 'seasonal_festival' ? '#4caf50' : '#ffb74d',
              padding: '2px 6px',
              marginBottom: '1px',
              borderRadius: '8px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: 'inline-block',
              width: 'fit-content',
              cursor: 'pointer'
            }}
            title={`${festival.name}${festival.tithi_end_time ? ` - Ends: ${festival.tithi_end_time}` : ''}${festival.parana_time ? ` - Parana: ${festival.parana_time}` : ''}`}
            >
              {festival.name}
            </div>
          ))}
          
          {dayData.transits && dayData.transits.map((transit, idx) => (
            <div key={`transit-${idx}`} style={{
              fontSize: '9px',
              background: '#9c27b0',
              color: 'white',
              padding: '1px 4px',
              marginBottom: '1px',
              borderRadius: '6px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: 'inline-block',
              width: 'fit-content',
              cursor: 'pointer'
            }}
            title={`${transit.planet} enters ${transit.sign} at ${transit.time}`}
            >
              ♃ {transit.planet} → {transit.sign}
            </div>
          ))}
        </div>
      );
    }

    return days;
  };

  return (
    <div style={{ background: '#f8f9fa', minHeight: '100vh', color: '#333333' }}>
      <NavigationHeader 
        user={user}
        onLogout={onLogout}
        onLogin={onLogin}
        showLoginButton={!user}
      />
      
      <div style={{ padding: '160px 20px 40px', maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ fontSize: '3rem', marginBottom: '10px' }}>
            Vedic Calendar <span style={{ color: '#e91e63' }}>2026</span>
          </h1>
          <p style={{ fontSize: '1.2rem', color: '#666666' }}>
            Complete Panchang with Tithi, Nakshatra & Festival Dates
          </p>
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(233, 30, 99, 0.05)',
          padding: '20px',
          borderRadius: '15px',
          marginBottom: '20px',
          border: '1px solid rgba(233, 30, 99, 0.2)'
        }}>
          <button 
            onClick={() => setCurrentMonth(Math.max(0, currentMonth - 1))}
            style={{
              background: '#e91e63',
              border: 'none',
              color: 'white',
              padding: '10px 15px',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            ‹ Previous
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <h2 style={{ margin: 0, color: '#e91e63' }}>{months[currentMonth]} 2026</h2>
            <button 
              onClick={() => setShowLocationPicker(true)}
              style={{
                background: '#4caf50',
                border: 'none',
                color: 'white',
                padding: '8px 12px',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              📍 {location.name}
            </button>
          </div>
          <button 
            onClick={() => setCurrentMonth(Math.min(11, currentMonth + 1))}
            style={{
              background: '#e91e63',
              border: 'none',
              color: 'white',
              padding: '10px 15px',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            Next ›
          </button>
        </div>

        {loading && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(7, 1fr)',
            gap: '1px',
            background: '#e0e0e0',
            borderRadius: '10px',
            overflow: 'hidden',
            border: '1px solid #d0d0d0'
          }}>
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map(day => (
              <div key={day} style={{
                padding: '15px',
                textAlign: 'center',
                fontWeight: 'bold',
                color: '#e91e63',
                background: '#f5f5f5'
              }}>
                {day}
              </div>
            ))}
            {Array.from({ length: 35 }, (_, i) => (
              <div key={i} style={{
                height: '120px',
                border: '1px solid #e0e0e0',
                padding: '5px',
                backgroundColor: '#f8f8f8',
                display: 'flex',
                flexDirection: 'column',
                gap: '2px'
              }}>
                <div style={{ width: '20px', height: '16px', background: '#e0e0e0', borderRadius: '2px' }}></div>
                <div style={{ width: '60px', height: '12px', background: '#ffd700', borderRadius: '6px', opacity: 0.3 }}></div>
                <div style={{ width: '50px', height: '12px', background: '#87ceeb', borderRadius: '6px', opacity: 0.3 }}></div>
              </div>
            ))}
          </div>
        )}
        
        {!loading && Object.keys(calendarData).length === 0 && (
          <div style={{ textAlign: 'center', padding: '20px', color: '#ff6f00' }}>
            Unable to load panchang data. Please check API connection.
          </div>
        )}

        {!loading && Object.keys(calendarData).length > 0 && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(7, 1fr)',
            gap: '1px',
            background: '#e0e0e0',
            borderRadius: '10px',
            overflow: 'hidden',
            border: '1px solid #d0d0d0'
          }}>
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map(day => (
              <div key={day} style={{
                padding: '15px',
                textAlign: 'center',
                fontWeight: 'bold',
                color: '#e91e63',
                background: '#f5f5f5'
              }}>
                {day}
              </div>
            ))}
            
            {renderCalendar()}
          </div>
        )}

        <div style={{ marginTop: '30px', textAlign: 'center' }}>
          <h3 style={{ color: '#e91e63', marginBottom: '15px' }}>Legend</h3>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{ width: '15px', height: '15px', background: '#ffd700', borderRadius: '2px' }}></div>
              <span style={{ fontSize: '12px' }}>Tithi</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{ width: '15px', height: '15px', background: '#87ceeb', borderRadius: '2px' }}></div>
              <span style={{ fontSize: '12px' }}>Nakshatra</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{ width: '15px', height: '15px', background: '#ff6f00', borderRadius: '2px' }}></div>
              <span style={{ fontSize: '12px' }}>Major Festival</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{ width: '15px', height: '15px', background: '#4caf50', borderRadius: '2px' }}></div>
              <span style={{ fontSize: '12px' }}>Seasonal Festival</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{ width: '15px', height: '15px', background: '#ffb74d', borderRadius: '2px' }}></div>
              <span style={{ fontSize: '12px' }}>Other Festival</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{ width: '15px', height: '15px', background: '#9c27b0', borderRadius: '2px' }}></div>
              <span style={{ fontSize: '12px' }}>Planetary Transit</span>
            </div>
          </div>
        </div>

        <div style={{ marginTop: '60px', textAlign: 'center' }}>
          <h2 style={{ color: '#e91e63', marginBottom: '20px' }}>Vedic Calendar Features</h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '20px'
          }}>
            <div style={{ background: '#ffffff', padding: '20px', borderRadius: '10px', border: '1px solid #e0e0e0', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
              <h3>📅 Daily Panchang</h3>
              <p>Tithi, Nakshatra, Vara, Yoga & Karana for every day</p>
            </div>
            <div style={{ background: '#ffffff', padding: '20px', borderRadius: '10px', border: '1px solid #e0e0e0', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
              <h3>🎉 Festival Calendar</h3>
              <p>Complete Hindu festival dates with significance</p>
            </div>
            <div style={{ background: '#ffffff', padding: '20px', borderRadius: '10px', border: '1px solid #e0e0e0', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
              <h3>🌟 Auspicious Times</h3>
              <p>Shubh Muhurats and favorable periods</p>
            </div>
          </div>
        </div>
      </div>
      
      {showLocationPicker && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '15px',
            maxWidth: '400px',
            width: '90%',
            maxHeight: '80vh',
            overflow: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, color: '#e91e63' }}>📍 Select Location</h3>
              <button 
                onClick={() => setShowLocationPicker(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#666'
                }}
              >
                ×
              </button>
            </div>
            
            <button 
              onClick={() => {
                if (navigator.geolocation) {
                  navigator.geolocation.getCurrentPosition(
                    (position) => {
                      const newLocation = {
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        name: 'Your Location'
                      };
                      setLocation(newLocation);
                      localStorage.setItem('astroRoshni_location', JSON.stringify(newLocation));
                      setShowLocationPicker(false);
                    },
                    () => alert('Unable to get your location')
                  );
                }
              }}
              style={{
                width: '100%',
                padding: '12px',
                background: '#4caf50',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                marginBottom: '20px'
              }}
            >
              📍 Use My Current Location
            </button>
            
            <h4 style={{ color: '#e91e63', marginBottom: '15px' }}>Popular Locations</h4>
            {[
              { name: 'Delhi, India', lat: 28.6139, lon: 77.2090 },
              { name: 'Mumbai, India', lat: 19.0760, lon: 72.8777 },
              { name: 'Bangalore, India', lat: 12.9716, lon: 77.5946 },
              { name: 'Chennai, India', lat: 13.0827, lon: 80.2707 },
              { name: 'Kolkata, India', lat: 22.5726, lon: 88.3639 },
              { name: 'London, UK', lat: 51.5074, lon: -0.1278 },
              { name: 'New York, USA', lat: 40.7128, lon: -74.0060 },
              { name: 'Toronto, Canada', lat: 43.6532, lon: -79.3832 }
            ].map((loc, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setLocation(loc);
                  localStorage.setItem('astroRoshni_location', JSON.stringify(loc));
                  setShowLocationPicker(false);
                }}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#f5f5f5',
                  border: '1px solid #ddd',
                  borderRadius: '5px',
                  cursor: 'pointer',
                  marginBottom: '8px',
                  textAlign: 'left'
                }}
              >
                {loc.name}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Calendar2026;