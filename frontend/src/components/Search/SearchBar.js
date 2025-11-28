import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './SearchBar.css';

const SEARCH_DATA = [
  { title: 'Marriage Analysis', path: '/marriage-analysis', keywords: ['marriage', 'spouse', 'compatibility', 'wedding', 'partner'] },
  { title: 'Career Guidance', path: '/career-guidance', keywords: ['career', 'job', 'profession', 'work', 'business'] },
  { title: 'Wealth Analysis', path: '/wealth-analysis', keywords: ['wealth', 'money', 'finance', 'prosperity', 'income'] },
  { title: 'Health Analysis', path: '/health-analysis', keywords: ['health', 'medical', 'wellness', 'disease', 'fitness'] },
  { title: 'Education Analysis', path: '/education', keywords: ['education', 'study', 'learning', 'academic', 'school'] },
  { title: 'Daily Horoscope', path: '/horoscope?period=daily', keywords: ['horoscope', 'daily', 'prediction', 'zodiac', 'rashi'] },
  { title: 'Panchang', path: '/panchang', keywords: ['panchang', 'calendar', 'tithi', 'nakshatra', 'muhurat'] },
  { title: 'Muhurat Finder', path: '/muhurat-finder', keywords: ['muhurat', 'auspicious', 'timing', 'shubh'] },
  { title: 'Festivals', path: '/festivals', keywords: ['festival', 'celebration', 'holiday', 'event'] },
  { title: 'Nakshatras', path: '/nakshatras', keywords: ['nakshatra', 'constellation', 'lunar', 'star'] },
  { title: 'Chat with Astrologer', path: '/chat', keywords: ['chat', 'ask', 'question', 'astrologer', 'consultation'] },
  { title: 'Profile', path: '/profile', keywords: ['profile', 'account', 'settings', 'history'] }
];

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

    const searchQuery = query.toLowerCase();
    const filtered = SEARCH_DATA.filter(item => 
      item.title.toLowerCase().includes(searchQuery) ||
      item.keywords.some(keyword => keyword.startsWith(searchQuery))
    );

    setResults(filtered);
    setShowResults(filtered.length > 0);
  }, [query]);

  const handleResultClick = (path) => {
    if (!user && path !== '/horoscope?period=daily' && path !== '/panchang' && path !== '/festivals' && path !== '/nakshatras') {
      onLogin();
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
              key={index}
              className="search-result-item"
              onClick={() => handleResultClick(result.path)}
            >
              <span className="result-icon">🔮</span>
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
