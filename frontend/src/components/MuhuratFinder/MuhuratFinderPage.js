import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { muhuratService } from '../../services/muhuratService';
import NavigationHeader from '../Shared/NavigationHeader';
import SEOHead from '../SEO/SEOHead';
import { generatePageSEO } from '../../config/seo.config';
import './MuhuratFinderPage.css';

const MUHURAT_TYPES = [
  { id: 'vivah', name: 'Marriage Muhurat', icon: '💒', description: 'Wedding ceremony timing with Panchang support' },
  { id: 'property', name: 'Property Purchase', icon: '🏠', description: 'Registration, booking and property transaction windows' },
  { id: 'vehicle', name: 'Vehicle Purchase', icon: '🚗', description: 'Favorable periods for buying or receiving vehicles' },
  { id: 'griha-pravesh', name: 'Griha Pravesh', icon: '🏡', description: 'House warming and first entry ceremony timings' },
];

const MUHURAT_GUIDE_CARDS = [
  {
    title: 'Purpose-specific timing',
    body: 'Marriage, property, vehicle and griha pravesh muhurats need different filters because each activity activates a different life area.',
  },
  {
    title: 'Location-based day',
    body: 'Muhurat windows depend on local sunrise, sunset and Panchang calculations, so timings change by city.',
  },
  {
    title: 'Avoid caution periods',
    body: 'Strong muhurat selection avoids Rahu Kaal, Yamaganda, Gulika, Dur Muhurta and other difficult windows when possible.',
  },
  {
    title: 'Use as first shortlist',
    body: 'For ceremonies and contracts, use these results as a shortlist and confirm final timing with full chart context.',
  },
];

const MUHURAT_FAQS = [
  {
    question: 'What is a muhurat?',
    answer: 'A muhurat is an auspicious time window chosen using Vedic Panchang, weekday, tithi, nakshatra, yoga, karana, planetary support and the purpose of the activity.',
  },
  {
    question: 'Why are muhurat timings different for each location?',
    answer: 'Many Panchang calculations are anchored to local sunrise and sunset. Because these vary by city, a muhurat calculated for Delhi may not be correct for another location.',
  },
  {
    question: 'Can I use one muhurat for every activity?',
    answer: 'No. Marriage, vehicle purchase, property registration and griha pravesh have different astrological priorities. A good time for one purpose may not be ideal for another.',
  },
  {
    question: 'Should Rahu Kaal be avoided for muhurat?',
    answer: 'Yes, important new beginnings are generally avoided during Rahu Kaal, Yamaganda, Gulika and Dur Muhurta unless an emergency or tradition-specific exception applies.',
  },
  {
    question: 'Is this enough for a wedding or griha pravesh?',
    answer: 'This page helps shortlist auspicious windows. For major ceremonies, final selection should also consider birth charts, family customs, regional rules and priest guidance.',
  },
];

const MuhuratFinderPage = () => {
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [location] = useState({ latitude: 28.6139, longitude: 77.2090, name: 'New Delhi' });
  const [selectedMuhurat, setSelectedMuhurat] = useState('vivah');
  const [muhuratData, setMuhuratData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const locationKey = `${location.latitude},${location.longitude}`;

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        setUser(null);
      }
    }
  }, []);

  useEffect(() => {
    fetchMuhuratData();
  }, [selectedDate, locationKey, selectedMuhurat]);

  const fetchMuhuratData = async () => {
    setLoading(true);
    setError(null);

    try {
      let data;
      switch (selectedMuhurat) {
        case 'property':
          data = await muhuratService.getPropertyMuhurat(selectedDate, location.latitude, location.longitude);
          break;
        case 'vehicle':
          data = await muhuratService.getVehicleMuhurat(selectedDate, location.latitude, location.longitude);
          break;
        case 'griha-pravesh':
          data = await muhuratService.getGrihaPraveshMuhurat(selectedDate, location.latitude, location.longitude);
          break;
        case 'vivah':
        default:
          data = await muhuratService.getVivahMuhurat(selectedDate, location.latitude, location.longitude);
      }
      setMuhuratData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timeString) => {
    const date = new Date(timeString);
    if (Number.isNaN(date.getTime())) return 'Not available';
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getCurrentMuhurat = () => {
    if (!muhuratData?.muhurtas) return null;

    const now = new Date();
    return muhuratData.muhurtas.find((muhurat) => {
      const start = new Date(muhurat.start_time);
      const end = new Date(muhurat.end_time);
      return now >= start && now <= end;
    });
  };

  const currentMuhurat = getCurrentMuhurat();
  const selectedType = MUHURAT_TYPES.find((type) => type.id === selectedMuhurat) || MUHURAT_TYPES[0];
  const seoData = generatePageSEO('muhuratFinder', { path: '/muhurat-finder' });

  const structuredData = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebApplication',
        name: 'Muhurat Finder',
        description: 'Find location based auspicious muhurat timings for marriage, property purchase, vehicle purchase and griha pravesh using Vedic Panchang calculations.',
        applicationCategory: 'LifestyleApplication',
        operatingSystem: 'Web',
        url: seoData.canonical,
      },
      {
        '@type': 'Service',
        name: 'Auspicious Muhurat Timing Calculator',
        provider: {
          '@type': 'Organization',
          name: 'AstroRoshni',
        },
        areaServed: 'Worldwide',
        serviceType: 'Vedic muhurat calculation',
      },
      {
        '@type': 'FAQPage',
        mainEntity: MUHURAT_FAQS.map((item) => ({
          '@type': 'Question',
          name: item.question,
          acceptedAnswer: {
            '@type': 'Answer',
            text: item.answer,
          },
        })),
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://astroroshni.com/' },
          { '@type': 'ListItem', position: 2, name: 'Muhurat Finder', item: seoData.canonical },
        ],
      },
    ],
  };

  return (
    <div className="muhurat-finder-page">
      <SEOHead
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={structuredData}
      />
      <NavigationHeader
        compact={true}
        user={user}
        onLogin={() => navigate('/')}
        onLogout={() => {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
          navigate('/');
        }}
      />

      <div className="muhurat-container">
        <section className="muhurat-hero">
          <div className="muhurat-hero-copy">
            <span className="muhurat-eyebrow">Vedic Muhurat Calculator</span>
            <h1>Muhurat Finder for Marriage, Property, Vehicle and Griha Pravesh</h1>
            <p>
              Shortlist auspicious time windows using date, location and purpose-specific Vedic
              Panchang calculations before planning important ceremonies or purchases.
            </p>
            <div className="muhurat-hero-tags" aria-label="Muhurat finder highlights">
              <span>Marriage</span>
              <span>Property</span>
              <span>Vehicle</span>
              <span>Griha Pravesh</span>
            </div>
          </div>
          <div className="muhurat-hero-panel" aria-label="Selected muhurat search">
            <span>Selected</span>
            <strong>{selectedType.name}</strong>
            <p>{formatDate(selectedDate)}</p>
            <p>{location.name}</p>
          </div>
        </section>

        <div className="controls-section">
          <div className="date-location-controls">
            <div className="date-control">
              <label>Select Date</label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="date-input"
              />
            </div>

            <div className="location-control">
              <label>Location</label>
              <div className="location-display">
                <span>{location.name}</span>
                <button className="change-location-btn" type="button">Change</button>
              </div>
            </div>
          </div>

          <div className="muhurat-type-selector">
            {MUHURAT_TYPES.map((type) => (
              <button
                type="button"
                key={type.id}
                className={`muhurat-type-card ${selectedMuhurat === type.id ? 'active' : ''}`}
                onClick={() => setSelectedMuhurat(type.id)}
              >
                <span className="type-icon">{type.icon}</span>
                <span className="type-info">
                  <strong>{type.name}</strong>
                  <span>{type.description}</span>
                </span>
              </button>
            ))}
          </div>
        </div>

        {loading && (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Calculating auspicious times...</p>
          </div>
        )}

        {error && (
          <div className="error-container">
            <div className="error-message">
              <h3>Error</h3>
              <p>{error}</p>
              <button onClick={fetchMuhuratData} className="retry-btn" type="button">Try Again</button>
            </div>
          </div>
        )}

        {muhuratData && !loading && (
          <div className="muhurat-results">
            <div className="results-header">
              <span>Results</span>
              <h2>{selectedType.name} for {formatDate(selectedDate)}</h2>
              <div className="location-info">
                📍 {location.name} ({location.latitude.toFixed(2)}°, {location.longitude.toFixed(2)}°)
              </div>
            </div>

            {currentMuhurat && (
              <div className="current-muhurat-alert">
                <div className="alert-header">
                  <span className="alert-icon">✨</span>
                  <span className="alert-text">Currently Active Muhurat</span>
                </div>
                <div className="current-muhurat-info">
                  <div className="muhurat-name">Muhurta {currentMuhurat.muhurta}</div>
                  <div className="muhurat-time">
                    {formatTime(currentMuhurat.start_time)} - {formatTime(currentMuhurat.end_time)}
                  </div>
                  <div className="muhurat-suitability">{currentMuhurat.suitability}</div>
                </div>
              </div>
            )}

            <div className="muhurat-grid">
              {(muhuratData.muhurtas || []).map((muhurat, index) => {
                const isActive = currentMuhurat && currentMuhurat.muhurta === muhurat.muhurta;

                return (
                  <article key={index} className={`muhurat-card ${isActive ? 'active' : ''}`}>
                    <div className="muhurat-header">
                      <div className="muhurat-number">Muhurta {muhurat.muhurta}</div>
                      {isActive && <div className="active-badge">Active Now</div>}
                    </div>

                    <div className="muhurat-timing">
                      <div className="time-range">
                        <span className="start-time">{formatTime(muhurat.start_time)}</span>
                        <span className="time-separator">-</span>
                        <span className="end-time">{formatTime(muhurat.end_time)}</span>
                      </div>
                      <div className="duration">{muhurat.duration_minutes} minutes</div>
                    </div>

                    <div className="muhurat-suitability">
                      {muhurat.suitability}
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        )}

        <section className="muhurat-seo-section" aria-labelledby="muhurat-guide-title">
          <div className="muhurat-seo-intro">
            <span className="muhurat-eyebrow">Muhurat Guide</span>
            <h2 id="muhurat-guide-title">Choose auspicious timings with Panchang context, not generic clock slots</h2>
            <p>
              A reliable muhurat is not a fixed time copied across cities. It is calculated from local
              Panchang factors and matched with the purpose of the event. Use this tool to compare daily
              windows for marriage, property, vehicle and griha pravesh planning.
            </p>
          </div>

          <div className="muhurat-guide-grid">
            {MUHURAT_GUIDE_CARDS.map((card) => (
              <article className="muhurat-guide-card" key={card.title}>
                <h3>{card.title}</h3>
                <p>{card.body}</p>
              </article>
            ))}
          </div>

          <div className="muhurat-copy-grid">
            <article>
              <h3>What this Muhurat Finder checks</h3>
              <p>
                The page focuses on practical auspicious windows for common life events. It combines
                date, location and event type so the result is more useful than a generic calendar entry.
              </p>
            </article>
            <article>
              <h3>How to use the results</h3>
              <p>
                Pick your date, select the event type and review available windows. For high-stakes
                ceremonies, confirm the final time with chart compatibility, family tradition and priest guidance.
              </p>
            </article>
          </div>
        </section>

        <section className="muhurat-faq-section" aria-labelledby="muhurat-faq-title">
          <div className="muhurat-seo-intro">
            <span className="muhurat-eyebrow">Questions</span>
            <h2 id="muhurat-faq-title">Muhurat Finder FAQs</h2>
          </div>
          <div className="muhurat-faq-grid">
            {MUHURAT_FAQS.map((item) => (
              <article className="muhurat-faq-card" key={item.question}>
                <h3>{item.question}</h3>
                <p>{item.answer}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

export default MuhuratFinderPage;
