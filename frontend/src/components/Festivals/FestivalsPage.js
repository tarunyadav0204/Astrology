import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import { generatePageSEO } from '../../config/seo.config';
import './FestivalsPage.css';

const POPULAR_LOCATIONS = [
  { name: 'Delhi, India', lat: 28.6139, lon: 77.2090 },
  { name: 'Mumbai, India', lat: 19.0760, lon: 72.8777 },
  { name: 'Bangalore, India', lat: 12.9716, lon: 77.5946 },
  { name: 'Chennai, India', lat: 13.0827, lon: 80.2707 },
  { name: 'Kolkata, India', lat: 22.5726, lon: 88.3639 },
  { name: 'Hyderabad, India', lat: 17.3850, lon: 78.4867 },
  { name: 'London, UK', lat: 51.5074, lon: -0.1278 },
  { name: 'New York, USA', lat: 40.7128, lon: -74.0060 },
  { name: 'Toronto, Canada', lat: 43.6532, lon: -79.3832 },
];

const FESTIVAL_FAQS = [
  {
    question: 'Why can Hindu festival dates change by location?',
    answer: 'Festival observance depends on local sunrise, tithi, nakshatra and regional rules. The same lunar date can begin or end at different clock times in different cities.',
  },
  {
    question: 'What is the difference between a festival and a vrat?',
    answer: 'A festival usually marks a celebration or sacred event, while a vrat is a fast or observance connected to a deity, tithi or spiritual discipline.',
  },
  {
    question: 'Should I check Panchang before observing a vrat?',
    answer: 'Yes. Vrat timing often depends on tithi at sunrise, parana windows, moonrise and local Panchang conditions.',
  },
  {
    question: 'Can I search for festival significance and rituals?',
    answer: 'Yes. Use the search button to find festivals and vrats by name, deity, type or keyword when the festival is available in the database.',
  },
];

const GUIDE_CARDS = [
  ['Location-aware dates', 'Use local sunrise and tithi boundaries instead of a generic national date.'],
  ['Vrat and parana context', 'See fast-breaking windows, moonrise and tithi information when the backend provides it.'],
  ['Daily Panchang snapshot', 'Compare festival observance with sunrise, sunset, tithi, nakshatra and yoga.'],
  ['Monthly planning', 'Jump to the month calendar when you want to plan observances ahead of time.'],
];

const todayIso = () => {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const formatDate = (dateStr, options = {}) => {
  const date = new Date(`${dateStr}T12:00:00`);
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    ...options,
  });
};

const eventTypeLabel = (type) => String(type || 'Festival').replace(/_/g, ' ');

const getTypeIcon = (event = {}) => {
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
    ancestral_period: '🪔',
  };
  return fallback[event.type] || '🎊';
};

const getTypeClass = (type) => {
  if (type === 'vrat') return 'is-vrat';
  if (type === 'seasonal_festival') return 'is-seasonal';
  if (type === 'regional_festival') return 'is-regional';
  if (type === 'spiritual_festival') return 'is-spiritual';
  return 'is-festival';
};

const FestivalCard = ({ festival }) => {
  const rituals = Array.isArray(festival.rituals)
    ? festival.rituals
    : festival.rituals
      ? [festival.rituals]
      : [];

  return (
    <article className={`festival-card ${getTypeClass(festival.type)}`}>
      <div className="festival-card__header">
        <span className="festival-card__icon" aria-hidden>{getTypeIcon(festival)}</span>
        <div>
          <span className="festival-card__type">{eventTypeLabel(festival.type)}</span>
          <h3>{festival.name}</h3>
        </div>
      </div>

      {festival.description && <p className="festival-card__description">{festival.description}</p>}
      {festival.significance && (
        <section className="festival-card__section">
          <h4>Significance</h4>
          <p>{festival.significance}</p>
        </section>
      )}
      {rituals.length > 0 && (
        <section className="festival-card__section">
          <h4>Rituals and Observances</h4>
          <ul>
            {rituals.slice(0, 5).map((ritual, index) => (
              <li key={`${festival.name}-ritual-${index}`}>{ritual}</li>
            ))}
          </ul>
        </section>
      )}

      <div className="festival-card__timing">
        {festival.tithi_at_sunrise && <span><strong>Tithi:</strong> {festival.tithi_at_sunrise}</span>}
        {festival.tithi_end_time && <span><strong>Tithi ends:</strong> {festival.tithi_end_time}</span>}
        {festival.parana_time && <span><strong>Parana:</strong> {festival.parana_time}</span>}
        {festival.moonrise_time && <span><strong>Moonrise:</strong> {festival.moonrise_time}</span>}
        {festival.paksha && <span><strong>Paksha:</strong> {festival.paksha === 'shukla' ? 'Shukla' : 'Krishna'}</span>}
      </div>
    </article>
  );
};

const FestivalsPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState(() => {
    const dateParam = new URLSearchParams(window.location.search).get('date');
    return dateParam || todayIso();
  });
  const [todayFestivals, setTodayFestivals] = useState([]);
  const [panchangData, setPanchangData] = useState(null);
  const [transits, setTransits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showSearch, setShowSearch] = useState(false);
  const [showLocationPicker, setShowLocationPicker] = useState(false);
  const [showTransits, setShowTransits] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [location, setLocation] = useState(POPULAR_LOCATIONS[0]);
  const [userTimezone] = useState(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch {
      return 'Asia/Kolkata';
    }
  });

  const locationKey = `${location.lat},${location.lon}`;
  const selectedDateLabel = formatDate(selectedDate);
  const seoData = generatePageSEO('festivals', { path: '/festivals' });

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
        '@type': 'Dataset',
        name: 'Hindu Festival Calendar',
        description: 'Daily Hindu festival, vrat and Panchang observance data by date and location.',
        creator: { '@type': 'Organization', name: 'AstroRoshni' },
      },
      {
        '@type': 'FAQPage',
        mainEntity: FESTIVAL_FAQS.map((item) => ({
          '@type': 'Question',
          name: item.question,
          acceptedAnswer: { '@type': 'Answer', text: item.answer },
        })),
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' },
          { '@type': 'ListItem', position: 2, name: 'Festivals', item: seoData.canonical },
        ],
      },
    ],
  }), [seoData.canonical, seoData.description, seoData.title]);

  useEffect(() => {
    const fetchPageData = async () => {
      try {
        setLoading(true);
        const date = new Date(`${selectedDate}T12:00:00`);
        const year = date.getFullYear();
        const month = date.getMonth() + 1;

        const [festivalResponse, panchangResponse, transitResponse] = await Promise.all([
          fetch(`/api/festivals/month/${year}/${month}?lat=${location.lat}&lon=${location.lon}&timezone=${encodeURIComponent(userTimezone)}`),
          fetch(`/api/panchang/today?date=${selectedDate}&latitude=${location.lat}&longitude=${location.lon}&timezone=${encodeURIComponent(userTimezone)}`),
          fetch(`/api/transits/monthly/${year}/${month}`),
        ]);

        if (festivalResponse.ok) {
          const data = await festivalResponse.json();
          const allFestivals = [...(data.festivals || []), ...(data.vrats || [])];
          setTodayFestivals(allFestivals.filter((festival) => festival.date === selectedDate));
        } else {
          setTodayFestivals([]);
        }

        if (panchangResponse.ok) {
          setPanchangData(await panchangResponse.json());
        } else {
          setPanchangData(null);
        }

        if (transitResponse.ok) {
          const data = await transitResponse.json();
          setTransits(data.transits || []);
        } else {
          setTransits([]);
        }
      } catch (error) {
        console.error('Error fetching festival page data:', error);
        setTodayFestivals([]);
        setPanchangData(null);
        setTransits([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPageData();
  }, [selectedDate, locationKey, userTimezone, location.lat, location.lon]);

  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
          name: 'Your Location',
        });
      },
      () => {}
    );
  }, []);

  const searchFestivals = async () => {
    if (!searchTerm.trim()) return;

    try {
      setSearchLoading(true);
      const response = await fetch(`/api/festivals/search?q=${encodeURIComponent(searchTerm)}`);
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.festivals || []);
      } else {
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Error searching festivals:', error);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const panchangItems = [
    ['Sunrise', panchangData?.sunrise],
    ['Sunset', panchangData?.sunset],
    ['Moonrise', panchangData?.moonrise],
    ['Tithi', panchangData?.tithi?.name],
    ['Nakshatra', panchangData?.nakshatra?.name],
    ['Yoga', panchangData?.yoga?.name],
  ];

  return (
    <div className="festivals-page">
      <SEOHead {...seoData} structuredData={structuredData} />
      <NavigationHeader
        compact
        user={user}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
        onLogin={onLogin}
        showLoginButton={showLoginButton}
      />

      <main className="festivals-shell">
        <section className="festivals-hero">
          <div className="festivals-hero__copy">
            <span className="festivals-eyebrow">Hindu Festival Calendar</span>
            <h1>Today’s Hindu Festivals, Vrats and Panchang Observances</h1>
            <p>
              Check sacred observances for the selected date with location-aware tithi, Panchang context,
              vrat timings and festival significance.
            </p>
            <div className="festivals-hero__actions">
              <button type="button" className="festival-btn festival-btn--primary" onClick={() => navigate('/festivals/monthly')}>
                Monthly Calendar
              </button>
              <button type="button" className="festival-btn festival-btn--secondary" onClick={() => setShowSearch(true)}>
                Search Festivals
              </button>
            </div>
          </div>
          <div className="festivals-hero__panel">
            <span>Selected Date</span>
            <strong>{selectedDateLabel}</strong>
            <p>{location.name}</p>
            <div className="festivals-hero__count">
              <strong>{todayFestivals.length}</strong>
              <span>{todayFestivals.length === 1 ? 'observance' : 'observances'}</span>
            </div>
          </div>
        </section>

        <section className="festival-controls" aria-label="Festival filters">
          <label className="festival-field">
            <span>Date</span>
            <input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} />
          </label>
          <div className="festival-field">
            <span>Location</span>
            <button type="button" className="festival-location" onClick={() => setShowLocationPicker(true)}>
              {location.name}
            </button>
          </div>
          <button type="button" className="festival-btn festival-btn--ghost" onClick={() => setShowTransits((value) => !value)}>
            {showTransits ? 'Hide Transits' : 'Show Transits'}
          </button>
        </section>

        {showTransits && (
          <section className="festival-panel">
            <div className="festival-panel__header">
              <span className="festivals-eyebrow">Planetary Transits</span>
              <h2>Monthly transit notes</h2>
            </div>
            {transits.length > 0 ? (
              <div className="festival-transits">
                {transits.map((transit, index) => (
                  <article className="festival-transit" key={`${transit.planet}-${transit.date}-${index}`}>
                    <strong>{transit.planet}</strong>
                    <span>{transit.sign}</span>
                    <small>{transit.date ? new Date(transit.date).toLocaleDateString('en-GB') : 'This month'}</small>
                  </article>
                ))}
              </div>
            ) : (
              <p className="festival-muted">No major transits found for this month.</p>
            )}
          </section>
        )}

        {panchangData && (
          <section className="festival-panel">
            <div className="festival-panel__header">
              <span className="festivals-eyebrow">Daily Panchang</span>
              <h2>Panchang for {selectedDateLabel}</h2>
            </div>
            <div className="festival-panchang-grid">
              {panchangItems.map(([label, value]) => (
                <div className="festival-panchang-item" key={label}>
                  <span>{label}</span>
                  <strong>{value || 'Not available'}</strong>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="festival-panel">
          <div className="festival-panel__header festival-panel__header--split">
            <div>
              <span className="festivals-eyebrow">Observances</span>
              <h2>{todayFestivals.length > 0 ? 'Festivals and vrats for this date' : 'No major observance found'}</h2>
            </div>
            <button type="button" className="festival-btn festival-btn--secondary" onClick={() => navigate('/festivals/monthly')}>
              View Month
            </button>
          </div>

          {loading ? (
            <div className="festival-loading">
              <div className="festival-spinner" />
              <p>Loading festival calendar...</p>
            </div>
          ) : todayFestivals.length > 0 ? (
            <div className="festivals-grid">
              {todayFestivals.map((festival, index) => (
                <FestivalCard festival={festival} key={`${festival.name}-${festival.date}-${index}`} />
              ))}
            </div>
          ) : (
            <div className="festival-empty">
              <span aria-hidden>🌸</span>
              <h3>No special festivals or vrats on this date</h3>
              <p>Use the monthly calendar to browse upcoming Ekadashi, Pradosh, Purnima, Amavasya and major festivals.</p>
            </div>
          )}
        </section>

        <section className="festival-seo-section">
          <div className="festival-panel__header">
            <span className="festivals-eyebrow">Festival Guide</span>
            <h2>Plan Hindu festivals with date, location and Panchang context</h2>
            <p>
              AstroRoshni’s festival calendar is designed for practical observance planning. It keeps the
              focus on the exact day, vrat rules, tithi support and local Panchang factors that matter in daily use.
            </p>
          </div>
          <div className="festival-guide-grid">
            {GUIDE_CARDS.map(([title, body]) => (
              <article className="festival-guide-card" key={title}>
                <h3>{title}</h3>
                <p>{body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="festival-faq-section">
          <div className="festival-panel__header">
            <span className="festivals-eyebrow">Questions</span>
            <h2>Hindu Festival Calendar FAQs</h2>
          </div>
          <div className="festival-faq-grid">
            {FESTIVAL_FAQS.map((item) => (
              <article className="festival-faq-card" key={item.question}>
                <h3>{item.question}</h3>
                <p>{item.answer}</p>
              </article>
            ))}
          </div>
        </section>
      </main>

      {showLocationPicker && (
        <div className="festival-modal-overlay">
          <div className="festival-modal" role="dialog" aria-modal="true" aria-label="Select location">
            <div className="festival-modal__header">
              <h3>Select Location</h3>
              <button type="button" onClick={() => setShowLocationPicker(false)} aria-label="Close location picker">×</button>
            </div>
            <button
              type="button"
              className="festival-modal__option festival-modal__option--strong"
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
            <div className="festival-modal__grid">
              {POPULAR_LOCATIONS.map((loc) => (
                <button
                  type="button"
                  className="festival-modal__option"
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

      {showSearch && (
        <div className="festival-modal-overlay">
          <div className="festival-modal festival-modal--wide" role="dialog" aria-modal="true" aria-label="Search festivals">
            <div className="festival-modal__header">
              <h3>Search Festivals and Vrats</h3>
              <button type="button" onClick={() => setShowSearch(false)} aria-label="Close search">×</button>
            </div>
            <div className="festival-search-row">
              <input
                type="text"
                placeholder="Search by festival name, deity or type"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') searchFestivals();
                }}
              />
              <button type="button" className="festival-btn festival-btn--primary" disabled={!searchTerm.trim()} onClick={searchFestivals}>
                Search
              </button>
            </div>

            <div className="festival-modal__content">
              {searchLoading ? (
                <div className="festival-loading">
                  <div className="festival-spinner" />
                  <p>Searching festivals...</p>
                </div>
              ) : searchResults.length > 0 ? (
                <div className="festivals-grid festivals-grid--modal">
                  {searchResults.map((festival, index) => (
                    <FestivalCard festival={festival} key={`${festival.name}-search-${index}`} />
                  ))}
                </div>
              ) : searchTerm ? (
                <div className="festival-empty">
                  <span aria-hidden>🔎</span>
                  <h3>No festivals found</h3>
                  <p>Try another keyword such as Diwali, Ekadashi, Shiva, Navratri or Pradosh.</p>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FestivalsPage;
