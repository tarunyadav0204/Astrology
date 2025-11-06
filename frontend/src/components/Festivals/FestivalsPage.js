import React, { useState, useEffect } from 'react';
import './FestivalsPage.css';

const FestivalsPage = () => {
  const [todayFestivals, setTodayFestivals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

  useEffect(() => {
    fetchTodayFestivals();
  }, [selectedDate]);

  const fetchTodayFestivals = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8001/api/festivals/today`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTodayFestivals(data.festivals || []);
      }
    } catch (error) {
      console.error('Error fetching festivals:', error);
    } finally {
      setLoading(false);
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

  return (
    <div className="festivals-page">
      <div className="festivals-header">
        <div className="header-content">
          <h1>🎊 Hindu Festivals & Vrats</h1>
          <p>Sacred days and spiritual observances</p>
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
        <div className="today-section">
          <h2>Today's Observances</h2>
          <div className="date-display">
            {formatDate(selectedDate)}
          </div>

          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              <p>Loading festivals...</p>
            </div>
          ) : todayFestivals.length > 0 ? (
            <div className="festivals-grid">
              {todayFestivals.map((festival, index) => (
                <div 
                  key={index} 
                  className="festival-card"
                  style={{ borderLeftColor: getTypeColor(festival.type) }}
                >
                  <div className="festival-header">
                    <span className="festival-icon">{getTypeIcon(festival.type)}</span>
                    <div className="festival-title">
                      <h3>{festival.name}</h3>
                      <span className="festival-type">{festival.type.replace('_', ' ')}</span>
                    </div>
                  </div>
                  
                  <div className="festival-description">
                    <p>{festival.description}</p>
                  </div>

                  <div className="festival-significance">
                    <h4>🌟 Significance</h4>
                    <p>{festival.significance}</p>
                  </div>

                  <div className="festival-rituals">
                    <h4>🕯️ Rituals & Observances</h4>
                    <ul>
                      {festival.rituals.map((ritual, idx) => (
                        <li key={idx}>{ritual}</li>
                      ))}
                    </ul>
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
            onClick={() => {/* Add search functionality */}}
          >
            🔍 Search Festivals
          </button>
        </div>
      </div>
    </div>
  );
};

export default FestivalsPage;