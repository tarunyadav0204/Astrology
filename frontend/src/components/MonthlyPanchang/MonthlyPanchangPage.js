import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ModernNavigationHeader from '../Shared/ModernNavigationHeader';
import LocationFinder from '../Panchang/components/LocationFinder';
import SEOHead from '../SEO/SEOHead';
import { generatePageSEO } from '../../config/seo.config';
import './MonthlyPanchangPage.css';

const MONTHLY_FAQS = [
  {
    question: 'What does a monthly Panchang show?',
    answer: 'A monthly Panchang brings daily tithi, nakshatra, paksha, sunrise, sunset, Moon sign and festival information into one calendar so you can compare dates before opening the complete daily reading.'
  },
  {
    question: 'Why are monthly Panchang timings location dependent?',
    answer: 'Sunrise, sunset and several daily periods change with latitude, longitude and timezone. Selecting your location keeps the calendar aligned with the sky where you are.'
  },
  {
    question: 'Can I use this calendar to choose a Muhurat?',
    answer: 'Use the month view to shortlist promising dates, then open the full daily Panchang to compare Rahu Kaal, Choghadiya, Hora and special Muhurat windows for that date.'
  }
];

const MonthlyPanchangPage = ({ user: propUser, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const navigate = useNavigate();
  const [user, setUser] = useState(propUser);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [monthlyData, setMonthlyData] = useState(null);
  const [selectedDayData, setSelectedDayData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [location, setLocation] = useState({ name: 'New Delhi, India', latitude: 28.6139, longitude: 77.2090 });
  const [showLocationFinder, setShowLocationFinder] = useState(false);

  useEffect(() => {
    if (!propUser) {
      const token = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user');
      if (token && savedUser) {
        try {
          setUser(JSON.parse(savedUser));
        } catch (e) {
          // Invalid user data
        }
      }
    } else {
      setUser(propUser);
    }
  }, [propUser]);

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  useEffect(() => {
    fetchMonthlyData();
  }, [selectedDate, location.latitude, location.longitude]);

  const fetchMonthlyData = async () => {
    setLoading(true);
    try {
      const year = selectedDate.getFullYear();
      const month = selectedDate.getMonth() + 1;
      const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      
      const response = await fetch(
        `/api/panchang/monthly?year=${year}&month=${month}&latitude=${location.latitude}&longitude=${location.longitude}&timezone=${encodeURIComponent(userTimezone)}`
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
        } else {
          setSelectedDayData(data.days?.find(Boolean) || null);
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
    if (dayData) setSelectedDayData(dayData);
  };

  const goToCurrentMonth = () => {
    setSelectedDate(new Date());
    setSelectedDayData(null);
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
      calendarDays.push(<div key={`empty-${i}`} className="calendar-day empty" aria-hidden="true"></div>);
    }
    
    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const dayData = monthlyData.days.find(d => d.day === day);
      const isToday = new Date().toDateString() === new Date(year, month, day).toDateString();
      const isSelected = selectedDayData && selectedDayData.day === day;
      
      calendarDays.push(
        <button
          type="button"
          key={day}
          className={`calendar-day ${isToday ? 'today' : ''} ${isSelected ? 'selected' : ''}`}
          onClick={() => handleDayClick(dayData)}
          disabled={!dayData}
          aria-label={`View Panchang for ${monthNames[month]} ${day}, ${year}`}
        >
          <div className="day-number">{day}</div>
          {dayData && (
            <div className="day-info">
              <div className="sun-times">
                <div className="sunrise">🌅 {dayData.sunrise_sunset?.sunrise?.slice(0,5) || 'N/A'}</div>
                <div className="sunset">🌇 {dayData.sunrise_sunset?.sunset?.slice(0,5) || 'N/A'}</div>
              </div>
              <div className="tithi-info">
                <span className="tithi">{dayData.basic_panchang?.tithi?.name} {dayData.calendar_info?.paksha}</span>
              </div>
              <div className="moon-info">
                <span className="moon-sign">🌙 {dayData.moon_info?.moon_sign}</span>
              </div>
              <div className="nakshatra-info">
                <span className="nakshatra">⭐ {dayData.basic_panchang?.nakshatra?.name}</span>
              </div>
              {dayData.festivals && dayData.festivals.length > 0 && (
                <div className="festivals">
                  <span className="festival">🎉 {dayData.festivals[0]}</span>
                </div>
              )}
            </div>
          )}
        </button>
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
              <button className="ics-btn" type="button" onClick={() => navigate(`/panchang?date=${data.date}`)}>
                Open daily Panchang <span aria-hidden>↗</span>
              </button>
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

  const handleAdminClick = () => {
    if (onAdminClick) {
      onAdminClick();
    }
  };

  const seoData = generatePageSEO('monthlyPanchang', { path: '/monthly-panchang/' });
  const structuredData = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebApplication',
        name: 'Monthly Panchang Calendar',
        description: seoData.description,
        applicationCategory: 'LifestyleApplication',
        operatingSystem: 'Web',
        url: seoData.canonical
      },
      {
        '@type': 'FAQPage',
        mainEntity: MONTHLY_FAQS.map((item) => ({
          '@type': 'Question',
          name: item.question,
          acceptedAnswer: { '@type': 'Answer', text: item.answer }
        }))
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' },
          { '@type': 'ListItem', position: 2, name: 'Daily Panchang', item: 'https://astroroshni.com/panchang/' },
          { '@type': 'ListItem', position: 3, name: 'Monthly Panchang', item: seoData.canonical }
        ]
      }
    ]
  };

  const festivalDayCount = monthlyData?.days?.filter((day) => day.festivals?.length > 0).length || 0;
  const monthLabel = `${monthNames[selectedDate.getMonth()]} ${selectedDate.getFullYear()}`;

  return (
    <div className="monthly-panchang-page monthly-panchang-page--themed">
      <SEOHead
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={structuredData}
        themeColor="#210b17"
      />
      <ModernNavigationHeader
        sticky
        user={user}
        onAdminClick={handleAdminClick}
        onLogout={onLogout || (() => {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
          navigate('/');
        })}
        onLogin={onLogin || (() => navigate('/'))}
        showLoginButton={showLoginButton}
      />

      <main className="monthly-main">
        <header className="monthly-hero">
          <div className="monthly-hero__copy">
            <button type="button" className="monthly-back-link" onClick={() => navigate('/panchang')}>
              <span aria-hidden>←</span> Daily Panchang
            </button>
            <span className="monthly-eyebrow">The month at a glance · {location.name}</span>
            <h1>Plan with the<br /><em>lunar rhythm.</em></h1>
            <p>
              Compare tithi, nakshatra, Moon sign, sunrise and festivals across the whole month,
              then open any date for its complete timing map.
            </p>
          </div>
          <div className="monthly-hero__month" aria-hidden="true">
            <span>{monthNames[selectedDate.getMonth()]}</span>
            <strong>{selectedDate.getFullYear()}</strong>
            <div className="monthly-moon-track">
              <i></i><i></i><i></i><i></i><i></i>
            </div>
          </div>
          <div className="monthly-hero__proof">
            <span><strong>{new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0).getDate()}</strong> calendar days</span>
            <span><strong>{festivalDayCount || '—'}</strong> festival dates</span>
            <span><strong>Local</strong> sunrise timings</span>
          </div>
        </header>

        <section className="monthly-toolbar" aria-label="Month and location controls">
          <div>
            <span className="monthly-eyebrow">Calendar controls</span>
            <p>Choose your month and place. Every day recalculates together.</p>
          </div>
          <div className="monthly-toolbar__actions">
            <button type="button" onClick={goToCurrentMonth}>This month</button>
            <button type="button" onClick={() => setShowLocationFinder(true)}>
              {location.name} <span aria-hidden>↗</span>
            </button>
          </div>
        </section>

        <div className="monthly-workspace">
          <section className="calendar-section" aria-labelledby="monthly-calendar-title">
          <div className="calendar-header">
            <button type="button" className="nav-btn" aria-label="Previous month" onClick={() => handleDateChange(-1)}>
              ‹
            </button>
            <div>
              <span className="monthly-eyebrow">Monthly Panchang</span>
              <h2 id="monthly-calendar-title">{monthLabel}</h2>
            </div>
            <button type="button" className="nav-btn" aria-label="Next month" onClick={() => handleDateChange(1)}>
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
          </section>

          <aside className="details-section" aria-label="Selected date details">
            {renderDetailedPanel()}
          </aside>
        </div>

        <section className="monthly-explainer" aria-labelledby="monthly-guide-title">
          <div className="monthly-explainer__intro">
            <span className="monthly-eyebrow">Plan before you decide</span>
            <h2 id="monthly-guide-title">A wider view of Vedic time.</h2>
            <p>
              A month view is best for comparison. Use it to notice changing paksha, lunar milestones,
              festival dates and nakshatra patterns before studying the exact Muhurat of a shortlisted day.
            </p>
          </div>
          <div className="monthly-method-grid">
            <article><span>01</span><h3>Scan the lunar cycle</h3><p>Compare tithi and paksha across the month to understand waxing and waning lunar phases.</p></article>
            <article><span>02</span><h3>Shortlist dates</h3><p>Use nakshatra, Moon sign and festival context to identify dates worth examining more closely.</p></article>
            <article><span>03</span><h3>Open the full day</h3><p>Confirm local Rahu Kaal, Hora, Choghadiya and special Muhurat windows on the daily Panchang.</p></article>
          </div>
        </section>

        <section className="monthly-faq" aria-labelledby="monthly-faq-title">
          <span className="monthly-eyebrow">Questions</span>
          <h2 id="monthly-faq-title">Monthly Panchang FAQs</h2>
          <div>
            {MONTHLY_FAQS.map((item, index) => (
              <details key={item.question} open={index === 0}>
                <summary>{item.question}<span aria-hidden>+</span></summary>
                <p>{item.answer}</p>
              </details>
            ))}
          </div>
        </section>
      </main>

      <LocationFinder
        isOpen={showLocationFinder}
        onClose={() => setShowLocationFinder(false)}
        onLocationSelect={(nextLocation) => {
          setLocation(nextLocation);
          setShowLocationFinder(false);
        }}
        currentLocation={location}
      />
    </div>
  );
};

export default MonthlyPanchangPage;
