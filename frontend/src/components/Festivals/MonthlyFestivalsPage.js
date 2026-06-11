import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import { generatePageSEO } from '../../config/seo.config';
import './MonthlyFestivalsPage.css';

const POPULAR_LOCATIONS = [
  { name: 'Delhi, India', lat: 28.6139, lon: 77.2090 },
  { name: 'Mumbai, India', lat: 19.0760, lon: 72.8777 },
  { name: 'Bangalore, India', lat: 12.9716, lon: 77.5946 },
  { name: 'Chennai, India', lat: 13.0827, lon: 80.2707 },
  { name: 'Kolkata, India', lat: 22.5726, lon: 88.3639 },
  { name: 'Hyderabad, India', lat: 17.3850, lon: 78.4867 },
];

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const MONTHLY_FAQS = [
  {
    question: 'How should I use the monthly Hindu festival calendar?',
    answer: 'Use it to scan the month, then open individual observances to see tithi, parana, significance and ritual details where available.',
  },
  {
    question: 'Why do some calendar days show multiple observances?',
    answer: 'A single civil date can include a festival, vrat, sankranti or regional observance depending on the lunar day and local Panchang rules.',
  },
  {
    question: 'Does the monthly calendar adjust by city?',
    answer: 'Yes. Festival data is fetched with latitude, longitude and timezone so location-sensitive observance dates and timings can be calculated.',
  },
  {
    question: 'What is Adhika Maas?',
    answer: 'Adhika Maas is an extra lunar month used to align the lunar and solar calendars. It has special spiritual importance in Hindu tradition.',
  },
];

const GUIDE_CARDS = [
  ['Month view for planning', 'See upcoming festivals and vrats in one scan before choosing a specific date.'],
  ['Click any observance', 'Open festival details directly from the calendar without leaving the monthly view.'],
  ['Location-sensitive calendar', 'Use the location picker when planning observances outside your current city.'],
  ['Daily detail path', 'Click a date to open the daily festival page for that exact observance day.'],
];

const eventTypeLabel = (type) => String(type || 'Festival').replace(/_/g, ' ');

const formatDateKey = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const formatLongDate = (dateStr) => new Date(`${dateStr}T12:00:00`).toLocaleDateString('en-US', {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
});

const getEventIcon = (event = {}) => {
  const name = String(event.name || '').toLowerCase();
  const specific = [
    ['diwali', '🪔'],
    ['holi', '🌈'],
    ['dussehra', '🏹'],
    ['navratri', '💃'],
    ['janmashtami', '🐄'],
    ['shivratri', '🔱'],
    ['ram navami', '🏹'],
    ['hanuman', '🙏'],
    ['karva', '🌙'],
    ['teej', '🌿'],
    ['ganesh', '🐘'],
    ['guru purnima', '📚'],
    ['makar sankranti', '🪁'],
    ['ekadashi', '🌕'],
    ['pradosh', '🔱'],
    ['sankashti', '🐘'],
  ];

  const match = specific.find(([key]) => name.includes(key));
  if (match) return match[1];

  const fallback = {
    major_festival: '🎉',
    vrat: '🙏',
    seasonal_festival: '🌾',
    regional_festival: '🏛️',
    spiritual_festival: '🕉️',
  };
  return fallback[event.type] || '🎊';
};

const buildCalendarDays = (currentDate) => {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const firstDay = new Date(year, month, 1);
  const startDate = new Date(firstDay);
  startDate.setDate(startDate.getDate() - firstDay.getDay());

  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(startDate);
    day.setDate(startDate.getDate() + index);
    return day;
  });
};

const MonthlyFestivalsPage = () => {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [monthlyData, setMonthlyData] = useState({ festivals: [], vrats: [] });
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [location, setLocation] = useState(POPULAR_LOCATIONS[0]);
  const [showLocationPicker, setShowLocationPicker] = useState(false);
  const [transits, setTransits] = useState([]);
  const [showTransits, setShowTransits] = useState(false);
  const [userTimezone] = useState(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch {
      return 'Asia/Kolkata';
    }
  });

  const locationKey = `${location.lat},${location.lon}`;
  const calendarDays = useMemo(() => buildCalendarDays(currentDate), [currentDate]);
  const monthTitle = `${MONTH_NAMES[currentDate.getMonth()]} ${currentDate.getFullYear()}`;
  const allEvents = useMemo(
    () => [...(monthlyData.festivals || []), ...(monthlyData.vrats || [])].sort((a, b) => String(a.date).localeCompare(String(b.date))),
    [monthlyData.festivals, monthlyData.vrats]
  );
  const seoData = generatePageSEO('festivalsMonthly', { path: '/festivals/monthly' });

  const structuredData = useMemo(() => ({
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebPage',
        name: seoData.title,
        description: seoData.description,
        url: seoData.canonical,
        isPartOf: { '@type': 'WebSite', name: 'AstroRoshni', url: 'https://astroroshni.com' },
      },
      {
        '@type': 'CollectionPage',
        name: `Monthly Hindu Festivals - ${monthTitle}`,
        description: 'Month calendar of Hindu festivals, vrats and Panchang observances.',
      },
      {
        '@type': 'FAQPage',
        mainEntity: MONTHLY_FAQS.map((item) => ({
          '@type': 'Question',
          name: item.question,
          acceptedAnswer: { '@type': 'Answer', text: item.answer },
        })),
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' },
          { '@type': 'ListItem', position: 2, name: 'Festivals', item: 'https://astroroshni.com/festivals' },
          { '@type': 'ListItem', position: 3, name: 'Monthly Festivals', item: seoData.canonical },
        ],
      },
    ],
  }), [monthTitle, seoData.canonical, seoData.description, seoData.title]);

  useEffect(() => {
    const fetchMonthlyData = async () => {
      try {
        setLoading(true);
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth() + 1;
        const [festivalResponse, transitResponse] = await Promise.all([
          fetch(`/api/festivals/month/${year}/${month}?lat=${location.lat}&lon=${location.lon}&timezone=${encodeURIComponent(userTimezone)}`),
          fetch(`/api/transits/monthly/${year}/${month}`),
        ]);

        if (festivalResponse.ok) {
          const data = await festivalResponse.json();
          setMonthlyData({
            festivals: data.festivals || [],
            vrats: data.vrats || [],
            is_adhika_month: data.is_adhika_month,
          });
          const firstEvent = [...(data.festivals || []), ...(data.vrats || [])][0] || null;
          setSelectedEvent(firstEvent);
        } else {
          setMonthlyData({ festivals: [], vrats: [] });
          setSelectedEvent(null);
        }

        if (transitResponse.ok) {
          const data = await transitResponse.json();
          setTransits(data.transits || []);
        } else {
          setTransits([]);
        }
      } catch (error) {
        console.error('Error fetching monthly festivals:', error);
        setMonthlyData({ festivals: [], vrats: [] });
        setSelectedEvent(null);
        setTransits([]);
      } finally {
        setLoading(false);
      }
    };

    fetchMonthlyData();
  }, [currentDate, locationKey, location.lat, location.lon, userTimezone]);

  const navigateMonth = (direction) => {
    const nextDate = new Date(currentDate);
    nextDate.setMonth(nextDate.getMonth() + direction);
    setCurrentDate(nextDate);
  };

  const getEventsForDate = (date) => {
    const dateStr = formatDateKey(date);
    return allEvents.filter((event) => event.date === dateStr);
  };

  const selectedRituals = Array.isArray(selectedEvent?.rituals)
    ? selectedEvent.rituals
    : selectedEvent?.rituals
      ? [selectedEvent.rituals]
      : [];

  return (
    <div className="monthly-festivals-page">
      <SEOHead {...seoData} structuredData={structuredData} />
      <NavigationHeader compact />

      <main className="monthly-festivals-shell">
        <section className={`monthly-festivals-hero ${monthlyData.is_adhika_month ? 'is-adhika' : ''}`}>
          <div className="monthly-festivals-hero__copy">
            <span className="monthly-festivals-eyebrow">Monthly Hindu Calendar</span>
            <h1>Monthly Festivals and Vrat Calendar</h1>
            <p>
              Browse Hindu festivals, Ekadashi, Pradosh, Purnima, Amavasya and sacred observances by month,
              with location-aware dates and festival details.
            </p>
            <div className="monthly-festivals-hero__actions">
              <button type="button" className="monthly-festival-btn monthly-festival-btn--primary" onClick={() => navigate('/festivals')}>
                Daily View
              </button>
              <button type="button" className="monthly-festival-btn monthly-festival-btn--secondary" onClick={() => setShowLocationPicker(true)}>
                {location.name}
              </button>
            </div>
          </div>
          <div className="monthly-festivals-hero__panel">
            <span>Showing</span>
            <strong>{monthTitle}</strong>
            <div className="monthly-festival-stats">
              <div><strong>{monthlyData.festivals?.length || 0}</strong><span>Festivals</span></div>
              <div><strong>{monthlyData.vrats?.length || 0}</strong><span>Vrats</span></div>
            </div>
            {monthlyData.is_adhika_month && <p className="monthly-adhika-note">Adhika Maas - sacred leap month</p>}
          </div>
        </section>

        <section className="monthly-toolbar">
          <button type="button" className="monthly-nav-btn" onClick={() => navigateMonth(-1)} aria-label="Previous month">‹</button>
          <div className="monthly-toolbar__title">
            <span className="monthly-festivals-eyebrow">Calendar</span>
            <h2>{monthTitle}</h2>
          </div>
          <button type="button" className="monthly-nav-btn" onClick={() => navigateMonth(1)} aria-label="Next month">›</button>
          <button type="button" className="monthly-festival-btn monthly-festival-btn--ghost" onClick={() => setShowTransits((value) => !value)}>
            {showTransits ? 'Hide Transits' : 'Show Transits'}
          </button>
        </section>

        {showTransits && (
          <section className="monthly-panel">
            <div className="monthly-panel__header">
              <span className="monthly-festivals-eyebrow">Planetary Transits</span>
              <h2>Transits in {monthTitle}</h2>
            </div>
            {transits.length > 0 ? (
              <div className="monthly-transits">
                {transits.map((transit, index) => (
                  <article className="monthly-transit" key={`${transit.planet}-${transit.date}-${index}`}>
                    <strong>{transit.planet}</strong>
                    <span>{transit.sign}</span>
                    <small>{transit.date ? new Date(transit.date).toLocaleDateString('en-GB') : 'This month'}</small>
                  </article>
                ))}
              </div>
            ) : (
              <p className="monthly-muted">No major transits found for this month.</p>
            )}
          </section>
        )}

        {loading ? (
          <div className="monthly-loading">
            <div className="monthly-spinner" />
            <p>Loading monthly festival calendar...</p>
          </div>
        ) : (
          <section className="monthly-calendar-layout">
            <div className="monthly-calendar-panel">
              <div className="monthly-calendar-grid">
                {DAY_NAMES.map((day) => (
                  <div className="monthly-day-header" key={day}>{day}</div>
                ))}
                {calendarDays.map((day) => {
                  const dateKey = formatDateKey(day);
                  const events = getEventsForDate(day);
                  const isCurrentMonth = day.getMonth() === currentDate.getMonth();
                  const isToday = dateKey === formatDateKey(new Date());

                  return (
                    <button
                      type="button"
                      key={dateKey}
                      className={`monthly-day ${!isCurrentMonth ? 'is-muted' : ''} ${isToday ? 'is-today' : ''}`}
                      onClick={() => navigate(`/festivals?date=${dateKey}`)}
                    >
                      <span className="monthly-day__number">{day.getDate()}</span>
                      {events.length > 0 && (
                        <span className="monthly-day__events">
                          {events.slice(0, 3).map((event, index) => (
                            <span
                              className="monthly-day__event"
                              key={`${event.name}-${index}`}
                              title={event.name}
                              onClick={(clickEvent) => {
                                clickEvent.stopPropagation();
                                setSelectedEvent(event);
                              }}
                            >
                              <span aria-hidden>{getEventIcon(event)}</span>
                              <span>{event.name}</span>
                            </span>
                          ))}
                          {events.length > 3 && <span className="monthly-day__more">+{events.length - 3} more</span>}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            <aside className="monthly-detail-panel">
              {selectedEvent ? (
                <article className="monthly-event-detail">
                  <div className="monthly-event-detail__header">
                    <span aria-hidden>{getEventIcon(selectedEvent)}</span>
                    <div>
                      <small>{eventTypeLabel(selectedEvent.type)}</small>
                      <h2>{selectedEvent.name}</h2>
                      <p>{selectedEvent.date ? formatLongDate(selectedEvent.date) : monthTitle}</p>
                    </div>
                  </div>

                  {selectedEvent.description && (
                    <section>
                      <h3>Description</h3>
                      <p>{selectedEvent.description}</p>
                    </section>
                  )}
                  {selectedEvent.significance && (
                    <section>
                      <h3>Significance</h3>
                      <p>{selectedEvent.significance}</p>
                    </section>
                  )}
                  {selectedRituals.length > 0 && (
                    <section>
                      <h3>Rituals</h3>
                      <ul>
                        {selectedRituals.slice(0, 6).map((ritual, index) => (
                          <li key={`${selectedEvent.name}-ritual-${index}`}>{ritual}</li>
                        ))}
                      </ul>
                    </section>
                  )}
                  <section>
                    <h3>Date and Timing</h3>
                    <div className="monthly-time-grid">
                      <span><strong>Tithi</strong>{selectedEvent.tithi_at_sunrise || 'Not available'}</span>
                      <span><strong>Tithi ends</strong>{selectedEvent.tithi_end_time || 'Not available'}</span>
                      {selectedEvent.parana_time && <span><strong>Parana</strong>{selectedEvent.parana_time}</span>}
                      {selectedEvent.deity && <span><strong>Deity</strong>{selectedEvent.deity}</span>}
                    </div>
                  </section>
                  {selectedEvent.benefits && (
                    <section>
                      <h3>Benefits</h3>
                      <p>{selectedEvent.benefits}</p>
                    </section>
                  )}
                </article>
              ) : (
                <div className="monthly-empty">
                  <span aria-hidden>🎊</span>
                  <h2>Select a festival</h2>
                  <p>Choose any event from the calendar to read details, timing and observance information.</p>
                </div>
              )}
            </aside>
          </section>
        )}

        <section className="monthly-list-panel">
          <div className="monthly-panel__header">
            <span className="monthly-festivals-eyebrow">This Month</span>
            <h2>Festival and vrat list for {monthTitle}</h2>
          </div>
          {allEvents.length > 0 ? (
            <div className="monthly-event-list">
              {allEvents.map((event, index) => (
                <button
                  type="button"
                  className={`monthly-event-row ${selectedEvent === event ? 'is-active' : ''}`}
                  key={`${event.name}-${event.date}-${index}`}
                  onClick={() => setSelectedEvent(event)}
                >
                  <span aria-hidden>{getEventIcon(event)}</span>
                  <strong>{event.name}</strong>
                  <small>{event.date ? formatLongDate(event.date) : monthTitle}</small>
                </button>
              ))}
            </div>
          ) : (
            <p className="monthly-muted">No festivals or vrats found for this month and location.</p>
          )}
        </section>

        <section className="monthly-seo-section">
          <div className="monthly-panel__header">
            <span className="monthly-festivals-eyebrow">Festival Planning</span>
            <h2>Monthly Hindu festival calendar with practical Panchang context</h2>
            <p>
              Use this page to plan upcoming puja dates, fasting days, parana windows and major celebrations.
              Monthly browsing helps you prepare before the festival day arrives.
            </p>
          </div>
          <div className="monthly-guide-grid">
            {GUIDE_CARDS.map(([title, body]) => (
              <article className="monthly-guide-card" key={title}>
                <h3>{title}</h3>
                <p>{body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="monthly-faq-section">
          <div className="monthly-panel__header">
            <span className="monthly-festivals-eyebrow">Questions</span>
            <h2>Monthly Festival Calendar FAQs</h2>
          </div>
          <div className="monthly-faq-grid">
            {MONTHLY_FAQS.map((item) => (
              <article className="monthly-faq-card" key={item.question}>
                <h3>{item.question}</h3>
                <p>{item.answer}</p>
              </article>
            ))}
          </div>
        </section>
      </main>

      {showLocationPicker && (
        <div className="monthly-modal-overlay">
          <div className="monthly-modal" role="dialog" aria-modal="true" aria-label="Select location">
            <div className="monthly-modal__header">
              <h3>Select Location</h3>
              <button type="button" onClick={() => setShowLocationPicker(false)} aria-label="Close location picker">×</button>
            </div>
            <button
              type="button"
              className="monthly-modal__option monthly-modal__option--strong"
              onClick={() => {
                if (!navigator.geolocation) return;
                navigator.geolocation.getCurrentPosition((position) => {
                  setLocation({
                    lat: position.coords.latitude,
                    lon: position.coords.longitude,
                    name: 'Your Location',
                  });
                  setShowLocationPicker(false);
                });
              }}
            >
              Use my current location
            </button>
            <div className="monthly-modal__grid">
              {POPULAR_LOCATIONS.map((loc) => (
                <button
                  type="button"
                  className="monthly-modal__option"
                  key={loc.name}
                  onClick={() => {
                    setLocation(loc);
                    setShowLocationPicker(false);
                  }}
                >
                  {loc.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MonthlyFestivalsPage;
