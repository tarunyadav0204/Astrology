import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'react-toastify';
import NavigationHeader from '../Shared/NavigationHeader';
import PanchangHeader from './components/PanchangHeader';
import LocationFinder from './components/LocationFinder';
import CorePanchangElements from './components/CorePanchangElements';
import SunriseSunsetInfo from './components/SunriseSunsetInfo';
import LunarInformation from './components/LunarInformation';
import PlanetaryPositions from './components/PlanetaryPositions';
import InauspiciousTimings from './components/InauspiciousTimings';
import AuspiciousTimings from './components/AuspiciousTimings';
import SEOHead from '../SEO/SEOHead';
import { panchangService } from './services/panchangService';
import { CALENDAR_SYSTEMS } from './config/panchangConfig';
import { generatePageSEO } from '../../config/seo.config';
import './PanchangPage.css';

const PANCHANG_GUIDE_CARDS = [
  {
    title: 'Five Panchang limbs',
    body: 'Read tithi, vara, nakshatra, yoga and karana together instead of relying on only one daily calendar factor.'
  },
  {
    title: 'Location based timings',
    body: 'Sunrise, sunset, Rahu Kaal, Yamaganda, Gulika and Choghadiya depend on the selected city and date.'
  },
  {
    title: 'Auspicious windows',
    body: 'Use Choghadiya, Hora and special muhurat periods to plan worship, travel, business tasks and important starts.'
  },
  {
    title: 'Festival context',
    body: 'Combine daily Panchang with festivals and lunar phase details for a clearer Hindu calendar view.'
  }
];

const PANCHANG_FAQS = [
  {
    question: 'What is Panchang?',
    answer: 'Panchang is the traditional Hindu calendar that combines five Vedic time factors: tithi, vara, nakshatra, yoga and karana. It is used to understand the quality of a day and choose suitable timings.'
  },
  {
    question: 'Why does Panchang change by location?',
    answer: 'Panchang timings depend on sunrise, sunset and local astronomical calculations. The same date can have different Rahu Kaal, Choghadiya, tithi ending time or nakshatra ending time in different cities.'
  },
  {
    question: 'Which Panchang details are useful for daily planning?',
    answer: 'For daily use, check tithi, nakshatra, weekday, sunrise, sunset, Rahu Kaal, Yamaganda, Gulika, Choghadiya and Hora. For ceremonies, also compare muhurat quality and avoid inauspicious periods.'
  },
  {
    question: 'Can I use this Panchang outside India?',
    answer: 'Yes. Select your city or coordinates so the Panchang can use local sunrise and sunset based calculations for your place.'
  },
  {
    question: 'What is the difference between Panchang and Muhurat?',
    answer: 'Panchang describes the daily Vedic calendar factors. Muhurat is the process of choosing a specific favorable time window using Panchang, weekday, nakshatra, planetary strength and the purpose of the activity.'
  }
];

const PanchangPage = ({ user: propUser, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const navigate = useNavigate();
  const urlLocation = useLocation();
  const [user, setUser] = useState(propUser);

  useEffect(() => {
    setUser(propUser ?? null);
  }, [propUser]);
  const [selectedDate, setSelectedDate] = useState(() => {
    const urlParams = new URLSearchParams(urlLocation.search);
    const dateParam = urlParams.get('date');
    return dateParam ? new Date(dateParam) : new Date();
  });
  const [location, setLocation] = useState({
    name: 'New Delhi, India',
    latitude: 28.6139,
    longitude: 77.2090
    // timezone will be detected by backend
  });
  const [calendarSystem, setCalendarSystem] = useState(CALENDAR_SYSTEMS.GREGORIAN);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showLocationFinder, setShowLocationFinder] = useState(false);
  
  // Data states
  const [panchangData, setPanchangData] = useState(null);
  const [sunriseSunsetData, setSunriseSunsetData] = useState(null);
  const [lunarData, setLunarData] = useState(null);
  const [planetaryData, setPlanetaryData] = useState(null);
  const [inauspiciousData, setInauspiciousData] = useState(null);
  const [choghadiyaData, setChoghadiyaData] = useState(null);
  const [horaData, setHoraData] = useState(null);
  const [muhurtaData, setMuhurtaData] = useState(null);
  const [festivals, setFestivals] = useState([]);

  useEffect(() => {
    loadPanchangData();
  }, [selectedDate, location]);

  const loadPanchangData = async () => {
    setLoading(true);
    setError(null);

    try {
      const dateString = selectedDate.toISOString().split('T')[0];
      
      // Load data with error handling for each service
      const results = await Promise.allSettled([
        panchangService.calculatePanchang(
          dateString, 
          location.latitude, 
          location.longitude
        ).catch(() => null),
        panchangService.calculateSunriseSunset(
          dateString,
          location.latitude,
          location.longitude
        ).catch(() => null),
        panchangService.calculateMoonPhase(dateString).catch(() => null),
        panchangService.calculatePlanetaryPositions(
          dateString,
          location.latitude,
          location.longitude
        ).catch(() => null),
        panchangService.getInauspiciousTimes(
          dateString,
          location.latitude,
          location.longitude
        ).catch(() => null),
        panchangService.calculateChoghadiya(
          dateString,
          location.latitude,
          location.longitude
        ).catch(() => null),
        panchangService.calculateHora(
          dateString,
          location.latitude,
          location.longitude
        ).catch(() => null),
        panchangService.calculateSpecialMuhurtas(
          dateString,
          location.latitude,
          location.longitude
        ).catch(() => null),
        panchangService.getFestivals(dateString).catch(() => [])
      ]);

      // Extract successful results
      const [
        panchang,
        sunriseSunset,
        lunar,
        planetary,
        inauspicious,
        choghadiya,
        hora,
        muhurta,
        festivalData
      ] = results.map(result => result.status === 'fulfilled' ? result.value : null);

      setPanchangData(panchang);
      setSunriseSunsetData(sunriseSunset);
      setLunarData(lunar);
      setPlanetaryData(planetary);
      setInauspiciousData(inauspicious);
      setChoghadiyaData(choghadiya);
      setHoraData(hora);
      setMuhurtaData(muhurta);
      setFestivals(festivalData || []);

    } catch (err) {
      console.error('Panchang loading error:', err);
      // Don't show error toast for API failures, just log them
    } finally {
      setLoading(false);
    }
  };

  const handleDateChange = (newDate) => {
    setSelectedDate(newDate);
  };

  const handleLocationChange = () => {
    setShowLocationFinder(true);
  };
  
  const handleLocationSelect = (newLocation) => {
    setLocation(newLocation);
    toast.success(`Location changed to ${newLocation.name}`);
  };

  const handleCalendarSystemChange = (newSystem) => {
    setCalendarSystem(newSystem);
  };

  const handleAdminClick = () => {
    if (onAdminClick) {
      onAdminClick();
    }
  };

  const seoData = generatePageSEO('panchang', { path: '/panchang' });
  const structuredData = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebApplication",
        "name": "Daily Panchang Calculator",
        "description": "Location based Hindu Panchang with tithi, nakshatra, yoga, karana, sunrise, sunset, Rahu Kaal, Choghadiya, Hora and muhurat timings.",
        "applicationCategory": "LifestyleApplication",
        "operatingSystem": "Web",
        "url": seoData.canonical
      },
      {
        "@type": "Service",
        "name": "Today Panchang and Muhurat Timings",
        "provider": {
          "@type": "Organization",
          "name": "AstroRoshni"
        },
        "areaServed": "Worldwide",
        "serviceType": "Hindu calendar and Vedic Panchang calculation"
      },
      {
        "@type": "FAQPage",
        "mainEntity": PANCHANG_FAQS.map((item) => ({
          "@type": "Question",
          "name": item.question,
          "acceptedAnswer": {
            "@type": "Answer",
            "text": item.answer
          }
        }))
      },
      {
        "@type": "BreadcrumbList",
        "itemListElement": [
          {
            "@type": "ListItem",
            "position": 1,
            "name": "Home",
            "item": "https://astroroshni.com/"
          },
          {
            "@type": "ListItem",
            "position": 2,
            "name": "Daily Panchang",
            "item": seoData.canonical
          }
        ]
      }
    ]
  };

  return (
    <div className="panchang-page">
      <SEOHead 
        title={seoData.title}
        description={seoData.description}
        keywords={seoData.keywords}
        canonical={seoData.canonical}
        structuredData={structuredData}
      />
      <NavigationHeader 
        compact={true}
        showZodiacSelector={false}
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

      <div className="panchang-content">
        <div className="container">
          
          <PanchangHeader
            selectedDate={selectedDate}
            onDateChange={handleDateChange}
            location={location}
            onLocationChange={handleLocationChange}
            calendarSystem={calendarSystem}
            onCalendarSystemChange={handleCalendarSystemChange}
            festivals={festivals}
            showMonthlyLink={true}
          />

          {loading && (
            <div className="panchang-inline-loading" role="status">
              <div className="loading-spinner"></div>
              <span>Loading live Panchang timings for {location.name}...</span>
            </div>
          )}

          {error && (
            <div className="panchang-inline-error">
              <span>{error}</span>
              <button className="retry-btn" onClick={loadPanchangData}>Retry</button>
            </div>
          )}

          <div className="panchang-section">
            <div className="section-header">
              <span>Daily Calendar</span>
              <h2>Core Panchang Elements</h2>
            </div>
            <div className="section-content">
              <CorePanchangElements panchangData={panchangData} />
            </div>
          </div>

          <div className="timing-grid">
            
            <div className="timing-card">
              <h3>Sunrise & Sunset</h3>
              <SunriseSunsetInfo 
                sunriseSunsetData={sunriseSunsetData}
                location={location}
              />
            </div>

            <div className="timing-card">
              <h3>Lunar Information</h3>
              <LunarInformation 
                lunarData={lunarData}
                panchangData={panchangData}
              />
            </div>

            <div className="timing-card">
              <h3>Inauspicious Times</h3>
              <InauspiciousTimings 
                inauspiciousData={inauspiciousData}
                sunriseSunsetData={sunriseSunsetData}
                selectedDate={selectedDate}
                location={location}
              />
            </div>

          </div>

          <div className="panchang-section">
            <div className="section-header">
              <span>Muhurat Planning</span>
              <h2>Auspicious Times</h2>
            </div>
            <div className="section-content">
              <AuspiciousTimings 
                choghadiyaData={choghadiyaData}
                horaData={horaData}
                muhurtaData={muhurtaData}
                selectedDate={selectedDate}
              />
            </div>
          </div>

          <div className="panchang-section">
            <div className="section-header">
              <span>Transit Snapshot</span>
              <h2>Planetary Positions</h2>
            </div>
            <div className="section-content">
              <PlanetaryPositions planetaryData={planetaryData} />
            </div>
          </div>

          <section className="panchang-seo-section" aria-labelledby="panchang-guide-title">
            <div className="panchang-seo-intro">
              <span className="panchang-eyebrow">Panchang Guide</span>
              <h2 id="panchang-guide-title">Daily Panchang for tithi, nakshatra, muhurat and Hindu calendar planning</h2>
              <p>
                AstroRoshni Panchang is built for practical daily decisions: checking the current lunar day,
                understanding the Moon nakshatra, avoiding difficult periods, and finding cleaner windows
                for worship, travel, purchases, meetings and new beginnings.
              </p>
            </div>

            <div className="panchang-guide-grid">
              {PANCHANG_GUIDE_CARDS.map((card) => (
                <article className="panchang-guide-card" key={card.title}>
                  <h3>{card.title}</h3>
                  <p>{card.body}</p>
                </article>
              ))}
            </div>

            <div className="panchang-copy-grid">
              <article>
                <h3>How to read today Panchang</h3>
                <p>
                  Start with sunrise because the Vedic day is anchored to local sunrise. Then read the
                  tithi for lunar energy, nakshatra for the Moon's active star field, yoga for the day
                  quality and karana for action suitability. The strongest Panchang reading comes from
                  combining these factors with the purpose of the activity.
                </p>
              </article>
              <article>
                <h3>Choosing a better time today</h3>
                <p>
                  Avoid Rahu Kaal, Yamaganda and Gulika for important launches whenever possible. For
                  everyday work, Choghadiya and Hora provide quick timing guidance. For major life events,
                  use a dedicated muhurat because marriage, property, vehicle, griha pravesh and business
                  starts each require different astrological checks.
                </p>
              </article>
            </div>
          </section>

          <section className="panchang-faq-section" aria-labelledby="panchang-faq-title">
            <div className="panchang-seo-intro">
              <span className="panchang-eyebrow">Questions</span>
              <h2 id="panchang-faq-title">Daily Panchang FAQs</h2>
            </div>
            <div className="panchang-faq-grid">
              {PANCHANG_FAQS.map((item) => (
                <article className="panchang-faq-card" key={item.question}>
                  <h3>{item.question}</h3>
                  <p>{item.answer}</p>
                </article>
              ))}
            </div>
          </section>

        </div>
      </div>
      
      <LocationFinder
        isOpen={showLocationFinder}
        onClose={() => setShowLocationFinder(false)}
        onLocationSelect={handleLocationSelect}
        currentLocation={location}
      />
    </div>
  );
};

export default PanchangPage;
