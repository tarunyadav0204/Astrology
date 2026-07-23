import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './SearchBar.css';

/** Site pages available in header search. `public: true` = reachable without login. */
const SEARCH_DATA = [
  // Core
  { title: 'Home', path: '/', keywords: ['home', 'homepage', 'main'], public: true },
  { title: 'AI Kundli Generator (Birth Chart)', path: '/ai-kundli-generator', keywords: ['birth chart', 'kundli', 'janam kundli', 'create chart', 'generator', 'horoscope chart'], public: true },
  { title: 'Charts & Dashas Workspace', path: '/charts-dashas', keywords: ['charts', 'dashas', 'vimshottari', 'divisional', 'd1', 'd9', 'workspace'], public: true },

  // Your Life
  { title: 'Marriage Analysis', path: '/marriage-analysis', keywords: ['marriage', 'spouse', 'compatibility', 'wedding', 'partner'] },
  { title: 'Progeny Analysis', path: '/progeny-analysis', keywords: ['progeny', 'children', 'child', 'santaan', 'pregnancy', 'kids'] },
  { title: 'Career Guidance', path: '/career-guidance', keywords: ['career', 'job', 'profession', 'work', 'business'] },
  { title: 'Education Analysis', path: '/education', keywords: ['education', 'study', 'learning', 'academic', 'school', 'college'] },
  { title: 'Health Analysis', path: '/health-analysis', keywords: ['health', 'medical', 'wellness', 'disease', 'fitness'] },
  { title: 'Wealth Analysis', path: '/wealth-analysis', keywords: ['wealth', 'money', 'finance', 'prosperity', 'income'] },
  { title: 'Life Events Timeline', path: '/life-events', keywords: ['life events', 'timeline', 'yearly', 'monthly', 'predictions', 'manifest', 'forecast'] },
  { title: 'Past Life / Karma Analysis', path: '/karma-analysis', keywords: ['karma', 'past life', 'pastlife', 'sanchita', 'prarabdha', 'rebirth'], public: true },

  // Matching & reports
  { title: 'Kundli Matching (Ashtakoot)', path: '/kundli-matching', keywords: ['kundli', 'matching', 'ashtakoot', 'guna', 'milan', 'gun milan', 'horoscope match'], public: true },
  { title: 'Reports Studio', path: '/reports', keywords: ['reports', 'studio', 'pdf', 'janam kundli report', 'download report'], public: true },

  // Tools
  { title: 'Ashtakavarga', path: '/ashtakavarga', keywords: ['ashtakavarga', 'ashtak', 'bindu', 'transit strength'], public: true },
  { title: 'AstroVastu', path: '/astrovastu', keywords: ['vastu', 'astrovastu', 'home vastu', 'office vastu', 'direction'], public: true },
  { title: 'Numerology', path: '/#numerology', keywords: ['numerology', 'numbers', 'name number', 'life path'], public: true },
  { title: 'Astrology Tools', path: '/#astrology', keywords: ['astrology', 'vedic', 'tools', 'planets'], public: true },

  // Calendar & timing
  { title: 'Panchang', path: '/panchang', keywords: ['panchang', 'calendar', 'tithi', 'nakshatra', 'rahu kaal', 'choghadiya'], public: true },
  { title: 'Monthly Panchang', path: '/monthly-panchang', keywords: ['monthly panchang', 'month calendar', 'hindu calendar'], public: true },
  { title: 'Muhurat Finder', path: '/muhurat-finder', keywords: ['muhurat', 'auspicious', 'timing', 'shubh', 'marriage muhurat', 'griha pravesh'], public: true },
  { title: 'Festivals', path: '/festivals', keywords: ['festival', 'celebration', 'holiday', 'diwali', 'holi'], public: true },
  { title: 'Monthly Festivals', path: '/festivals/monthly', keywords: ['monthly festivals', 'festival calendar'], public: true },
  { title: 'Nakshatras', path: '/nakshatras', keywords: ['nakshatra', 'constellation', 'lunar', 'star', 'birth star'], public: true },
  { title: 'Calendar 2026', path: '/calendar-2026', keywords: ['calendar', '2026', 'hindu calendar', 'yearly calendar'], public: true },

  // Horoscope
  { title: 'Daily Horoscope', path: '/horoscope?period=daily', keywords: ['horoscope', 'daily', 'prediction', 'zodiac', 'rashi'], public: true },
  { title: 'Weekly Horoscope', path: '/horoscope?period=weekly', keywords: ['weekly horoscope', 'week prediction'], public: true },
  { title: 'Monthly Horoscope', path: '/horoscope?period=monthly', keywords: ['monthly horoscope', 'month prediction'], public: true },

  // Chat & learning
  { title: 'AI Astrologer Chat (Ask Tara)', path: '/chat?app=1', keywords: ['chat', 'astrologer', 'ai', 'tara', 'ask tara', 'consultation', 'kundli chat'] },
  { title: 'Beginners Guide', path: '/beginners-guide', keywords: ['beginners', 'guide', 'learn', 'basics', 'introduction'], public: true },
  { title: 'Advanced Courses', path: '/advanced-courses', keywords: ['advanced', 'courses', 'learning', 'study astrology'], public: true },
  { title: 'Myths vs Reality', path: '/myths-vs-reality', keywords: ['myths', 'reality', 'misconceptions', 'facts'], public: true },
  { title: 'Blog', path: '/blog', keywords: ['blog', 'articles', 'posts', 'insights', 'reading'], public: true },

  // Account & company
  { title: 'VIP Membership', path: '/subscription', keywords: ['vip', 'membership', 'subscription', 'premium', 'plan'], public: true },
  { title: 'Orders & Billing', path: '/order-management', keywords: ['orders', 'billing', 'invoice', 'payment', 'purchase'] },
  { title: 'Profile', path: '/profile', keywords: ['profile', 'account', 'settings', 'history'] },
  { title: 'Contact Us', path: '/contact', keywords: ['contact', 'support', 'help', 'email', 'reach'], public: true },
  { title: 'About Us', path: '/about', keywords: ['about', 'company', 'astroroshni', 'who we are'], public: true },
  { title: 'Privacy Policy', path: '/policy', keywords: ['privacy', 'policy', 'data'], public: true },
  { title: 'Terms of Service', path: '/terms', keywords: ['terms', 'conditions', 'tos', 'legal'], public: true },
];

const matchesQuery = (item, searchQuery) => {
  if (item.title.toLowerCase().includes(searchQuery)) return true;
  return item.keywords.some((keyword) => keyword.toLowerCase().includes(searchQuery));
};

const SearchBar = ({ user, onLogin }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const navigate = useNavigate();
  const searchRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      setShowResults(false);
      return;
    }

    const searchQuery = query.toLowerCase().trim();
    const filtered = SEARCH_DATA.filter((item) => matchesQuery(item, searchQuery));

    setResults(filtered);
    setShowResults(filtered.length > 0);
  }, [query]);

  const handleResultClick = (result) => {
    const { path, public: isPublic } = result;
    if (!user && !isPublic) {
      if (onLogin) onLogin();
      else navigate('/');
    } else {
      navigate(path);
    }
    setQuery('');
    setShowResults(false);
  };

  return (
    <div className="search-bar-container" ref={searchRef}>
      <div className="search-input-wrapper">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          className="search-input"
          placeholder="Search for services, horoscopes, analysis..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.length >= 2 && setShowResults(true)}
        />
        {query && (
          <button className="clear-btn" onClick={() => setQuery('')}>×</button>
        )}
      </div>

      {showResults && results.length > 0 && (
        <div className="search-results">
          {results.map((result, index) => (
            <div
              key={`${result.path}-${index}`}
              className="search-result-item"
              onClick={() => handleResultClick(result)}
            >
              <span className="result-icon" aria-hidden>
                <svg viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="10" cy="10" r="8.25" stroke="currentColor" strokeWidth="1.5" />
                  <path d="M8 7.5h4.5V12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M12.5 7.5 7.5 12.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </span>
              <span className="result-title">{result.title}</span>
              <span className="result-arrow">→</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
