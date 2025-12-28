import React, { useState, useEffect } from 'react';
import NavigationHeader from '../Shared/NavigationHeader';
import './FestivalsPage.css';

const FestivalsPage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton }) => {
  const [todayFestivals, setTodayFestivals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const dateParam = urlParams.get('date');
    return dateParam || new Date().toISOString().split('T')[0];
  });
  const [showSearch, setShowSearch] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [location, setLocation] = useState({ lat: 28.6139, lon: 77.2090, name: 'Delhi, India' });
  const [showLocationPicker, setShowLocationPicker] = useState(false);
  const [transits, setTransits] = useState([]);
  const [showTransits, setShowTransits] = useState(false);

  useEffect(() => {
    fetchTodayFestivals();
    fetchTransits();
  }, [selectedDate, location]);

  useEffect(() => {
    // Try to get user's location on first load
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
            name: 'Your Location'
          });
        },
        () => {
          // Keep default Delhi location if geolocation fails
        }
      );
    }
  }, []);

  const fetchTodayFestivals = async () => {
    try {
      setLoading(true);
      const date = new Date(selectedDate);
      const year = date.getFullYear();
      const month = date.getMonth() + 1;
      
      const response = await fetch(`/api/festivals/month/${year}/${month}?lat=${location.lat}&lon=${location.lon}&timezone_offset=5.5`, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        // Filter festivals for the selected date
        const allFestivals = [...(data.festivals || []), ...(data.vrats || [])];
        const selectedDateStr = selectedDate;
        const dayFestivals = allFestivals.filter(f => f.date === selectedDateStr);
        console.log('Selected date:', selectedDateStr);
        console.log('All festivals:', allFestivals);
        console.log('Filtered festivals:', dayFestivals);
        setTodayFestivals(dayFestivals);
      } else {
        console.error('API response error:', response.status, response.statusText);
        setTodayFestivals([]);
      }
    } catch (error) {
      console.error('Error fetching festivals:', error);
      setTodayFestivals([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchTransits = async () => {
    try {
      const date = new Date(selectedDate);
      const year = date.getFullYear();
      const month = date.getMonth() + 1;
      
      const response = await fetch(`/api/transits/monthly/${year}/${month}`);
      if (response.ok) {
        const data = await response.json();
        setTransits(data.transits || []);
      }
    } catch (error) {
      console.error('Error fetching transits:', error);
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getTypeIcon = (event) => {
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
    
    // Check for specific festival/vrat name
    const name = event.name?.toLowerCase() || '';
    
    for (const [key, icon] of Object.entries(festivalIcons)) {
      if (name.includes(key)) return icon;
    }
    
    for (const [key, icon] of Object.entries(vratIcons)) {
      if (name.includes(key)) return icon;
    }
    
    // Fallback to type icons
    const typeIcons = {
      'major_festival': '🎉',
      'vrat': '🙏',
      'seasonal_festival': '🌾',
      'regional_festival': '🏛️',
      'spiritual_festival': '🕉️',
      'ancestral_period': '👴'
    };
    
    return typeIcons[event.type] || '🎊';
  };

  const getTypeColor = (type) => {
    const colors = {
      'major_festival': '#ff6b35',
      'vrat': '#8e44ad',
      'seasonal_festival': '#27ae60',
      'regional_festival': '#3498db',
      'spiritual_festival': '#f39c12',
      'ancestral_period': '#95a5a6'
    };
    return colors[type] || '#e74c3c';
  };

  const searchFestivals = async () => {
    if (!searchTerm.trim()) return;
    
    try {
      setSearchLoading(true);
      const response = await fetch(`/api/festivals/search?q=${encodeURIComponent(searchTerm)}`, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.festivals || []);
      } else {
        console.error('Search API error:', response.status);
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Error searching festivals:', error);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  return (
    <div className="festivals-page">
      <NavigationHeader 
        user={user}
        onLogout={onLogout}
        onAdminClick={onAdminClick}
        onLogin={onLogin}
        showLoginButton={showLoginButton}
      />
      <div className="festivals-header">
        <div className="header-left">
          <button 
            className="header-btn monthly-btn"
            onClick={() => window.location.href = '/festivals/monthly'}
          >
            📅 Monthly Calendar
          </button>
          <button 
            className="header-btn search-btn"
            onClick={() => setShowSearch(!showSearch)}
          >
            🔍 Search Festivals
          </button>
          <button 
            className="header-btn location-btn"
            onClick={() => setShowLocationPicker(!showLocationPicker)}
          >
            📍 {location.name}
          </button>
          <button 
            className="header-btn transit-btn"
            onClick={() => setShowTransits(!showTransits)}
          >
            🪐 Planetary Transits
          </button>
        </div>
        <div className="header-content">
          <h1>🎊 Today's Festivals</h1>
          <p>Sacred days and spiritual observances • {formatDate(selectedDate)}</p>
        </div>
        <div className="date-selector">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="date-input"
          />
        </div>
      </div>

      <div className="festivals-content">
        {showTransits && (
          <div className="transits-section">
            <h2>🪐 Current Planetary Transits</h2>
            {transits.length > 0 ? (
              <div className="transits-grid">
                {transits.map((transit, index) => (
                  <div key={index} className="transit-card">
                    <div className="transit-header">
                      <span className="planet-name">{transit.planet}</span>
                      <span className="transit-arrow">→</span>
                      <span className="sign-name">{transit.sign}</span>
                    </div>
                    <div className="transit-date">{new Date(transit.date).toLocaleDateString()}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p>No major transits this month</p>
            )}
          </div>
        )}

        <div className="today-section">

          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              <p>Loading festivals...</p>
            </div>
          ) : todayFestivals.length > 0 ? (
            <div className="festivals-grid">
              {todayFestivals.map((festival, index) => (
                <div 
                  key={`${festival.name}-${festival.date}-${index}`} 
                  className="festival-card"
                  style={{ borderLeftColor: getTypeColor(festival.type || 'festival') }}
                >
                  <div className="festival-header">
                    <span className="festival-icon">{getTypeIcon(festival)}</span>
                    <div className="festival-title">
                      <h3>{festival.name}</h3>
                      <span className="festival-type">{festival.type?.replace('_', ' ') || 'Festival'}</span>
                    </div>
                  </div>
                  
                  {festival.description && (
                    <div className="festival-description">
                      <p>{festival.description}</p>
                    </div>
                  )}

                  {festival.significance && (
                    <div className="festival-significance">
                      <h4>🌟 Significance</h4>
                      <p>{festival.significance}</p>
                    </div>
                  )}

                  {festival.rituals && festival.rituals.length > 0 && (
                    <div className="festival-rituals">
                      <h4>🕯️ Rituals & Observances</h4>
                      <ul>
                        {festival.rituals.map((ritual, idx) => (
                          <li key={idx}>{ritual}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  <div className="festival-timing">
                    <h4>⏰ Timing Details</h4>
                    <div className="timing-info">
                      {festival.tithi_at_sunrise && (
                        <p><strong>Tithi at Sunrise:</strong> {festival.tithi_at_sunrise}</p>
                      )}
                      {festival.tithi_end_time && (
                        <p><strong>Tithi Ends:</strong> {festival.tithi_end_time}</p>
                      )}
                      {festival.parana_time && (
                        <p><strong>Parana Time:</strong> {festival.parana_time}</p>
                      )}
                      {festival.moonrise_time && (
                        <p><strong>Moonrise Time:</strong> {festival.moonrise_time}</p>
                      )}
                      {festival.paksha && (
                        <p><strong>Paksha:</strong> {festival.paksha === 'shukla' ? 'Shukla (Bright)' : 'Krishna (Dark)'}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-festivals">
              <div className="no-festivals-icon">🌸</div>
              <h3>No Special Observances Today</h3>
              <p>Every day is sacred in its own way. Use this time for personal reflection and spiritual practice.</p>
            </div>
          )}
        </div>

        <div className="quick-actions">
          <button 
            className="action-btn monthly-btn"
            onClick={() => window.location.href = '/festivals/monthly'}
          >
            📅 Monthly Calendar
          </button>
          <button 
            className="action-btn search-btn"
            onClick={() => setShowSearch(!showSearch)}
          >
            🔍 Search Festivals
          </button>
        </div>

      {showLocationPicker && (
        <div className="search-modal-overlay">
          <div className="search-modal">
            <div className="search-header">
              <h3>📍 Select Location</h3>
              <button 
                className="close-search"
                onClick={() => setShowLocationPicker(false)}
              >
                ×
              </button>
            </div>
            <div className="location-content">
              <button 
                className="location-option"
                onClick={() => {
                  if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                      (position) => {
                        setLocation({
                          lat: position.coords.latitude,
                          lon: position.coords.longitude,
                          name: 'Your Location'
                        });
                        setShowLocationPicker(false);
                      },
                      () => alert('Unable to get your location')
                    );
                  }
                }}
              >
                📍 Use My Current Location
              </button>
              
              <div className="popular-locations">
                <h4>Popular Locations</h4>
                {[
                  { name: 'Delhi, India', lat: 28.6139, lon: 77.2090 },
                  { name: 'Mumbai, India', lat: 19.0760, lon: 72.8777 },
                  { name: 'Bangalore, India', lat: 12.9716, lon: 77.5946 },
                  { name: 'Chennai, India', lat: 13.0827, lon: 80.2707 },
                  { name: 'Kolkata, India', lat: 22.5726, lon: 88.3639 },
                  { name: 'Hyderabad, India', lat: 17.3850, lon: 78.4867 },
                  { name: 'London, UK', lat: 51.5074, lon: -0.1278 },
                  { name: 'New York, USA', lat: 40.7128, lon: -74.0060 },
                  { name: 'Toronto, Canada', lat: 43.6532, lon: -79.3832 }
                ].map((loc, idx) => (
                  <button
                    key={idx}
                    className="location-option"
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
        </div>
      )}
      
      {showSearch && (
        <div className="search-modal-overlay">
          <div className="search-modal">
            <div className="search-header">
              <h3>🔍 Search Festivals & Vrats</h3>
              <button 
                className="close-search"
                onClick={() => setShowSearch(false)}
              >
                ×
              </button>
            </div>
            <div className="search-input-container">
              <input
                type="text"
                placeholder="Search by festival name, deity, or type..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchFestivals()}
                className="search-input"
              />
              <button 
                className="search-submit-btn"
                onClick={searchFestivals}
                disabled={!searchTerm.trim()}
              >
                Search
              </button>
            </div>
            
            <div className="search-content">
              {searchLoading ? (
                <div className="loading">
                  <div className="spinner"></div>
                  <p>Searching festivals...</p>
                </div>
              ) : searchResults.length > 0 ? (
                <div className="search-results">
                  <h4>Search Results ({searchResults.length} found)</h4>
                  <div className="festivals-grid">
                    {searchResults.map((festival, index) => (
                      <div 
                        key={index} 
                        className="festival-card"
                        style={{ borderLeftColor: getTypeColor(festival.type || 'festival') }}
                      >
                        <div className="festival-header">
                          <span className="festival-icon">{getTypeIcon(festival)}</span>
                          <div className="festival-title">
                            <h3>{festival.name}</h3>
                            <span className="festival-type">{festival.type?.replace('_', ' ')}</span>
                          </div>
                        </div>
                        
                        <div className="festival-description">
                          <p>{festival.description}</p>
                        </div>

                        <div className="festival-significance">
                          <h4>🌟 Significance</h4>
                          <p>{festival.significance}</p>
                        </div>

                        {festival.rituals && (
                          <div className="festival-rituals">
                            <h4>🕯️ Rituals & Observances</h4>
                            <ul>
                              {Array.isArray(festival.rituals) ? 
                                festival.rituals.map((ritual, idx) => (
                                  <li key={idx}>{ritual}</li>
                                )) :
                                <li>{festival.rituals}</li>
                              }
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : searchTerm && !searchLoading ? (
                <div className="no-results">
                  <div className="no-results-icon">🔍</div>
                  <h3>No festivals found</h3>
                  <p>Try searching with different keywords like "Diwali", "Ekadashi", or "Shiva"</p>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

export default FestivalsPage;