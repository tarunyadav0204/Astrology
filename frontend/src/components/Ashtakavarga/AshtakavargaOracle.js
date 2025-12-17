import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../config';
import './AshtakavargaOracle.css';

const AshtakavargaOracle = ({ birthData, ashtakavargaData, onClose }) => {
  const [completeOracleData, setCompleteOracleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTimelineCategory, setSelectedTimelineCategory] = useState('general');

  useEffect(() => {
    if (birthData && ashtakavargaData) {
      fetchCompleteOracle();
    }
  }, [birthData, ashtakavargaData]);

  const fetchCompleteOracle = async () => {
    try {
      const token = localStorage.getItem('token');
      const apiUrl = API_BASE_URL.includes('/api') 
        ? `${API_BASE_URL}/ashtakavarga/oracle-insight`
        : `${API_BASE_URL}/api/ashtakavarga/oracle-insight`;

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: birthData,
          ashtakvarga_data: ashtakavargaData,
          date: new Date().toISOString().split('T')[0]
        })
      });

      if (response.ok) {
        const completeData = await response.json();
        console.log('Complete oracle data received:', completeData);
        setCompleteOracleData(completeData);
      } else {
        throw new Error(`Failed to fetch oracle data: ${response.status}`);
      }
    } catch (error) {
      console.error('Error fetching oracle:', error);
    } finally {
      setLoading(false);
    }
  };

  const timelineCategories = [
    { id: 'general', name: 'General', icon: '🌟' },
    { id: 'love', name: 'Love', icon: '❤️' },
    { id: 'wealth', name: 'Wealth', icon: '💰' },
    { id: 'career', name: 'Career', icon: '💼' },
    { id: 'health', name: 'Health', icon: '🏥' }
  ];

  const renderTimelineEvents = () => {
    if (!completeOracleData?.timeline_events) {
      return <div className="no-events">No timeline data available</div>;
    }

    const events = completeOracleData.timeline_events[selectedTimelineCategory] || [];
    
    if (events.length === 0) {
      return <div className="no-events">No predictions for {selectedTimelineCategory}</div>;
    }

    return events.map((event, index) => (
      <div key={index} className="timeline-event">
        <div className={`event-score score-${Math.floor(event.score / 3)}`}>
          {event.score}/10
        </div>
        <div className="event-content">
          <h4>{event.title}</h4>
          <div className="event-date">{event.date_range}</div>
          <p>{event.description}</p>
        </div>
      </div>
    ));
  };

  if (loading) {
    return (
      <div className="oracle-modal">
        <div className="oracle-content">
          <div className="loading">🔮 Consulting the Oracle...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="oracle-modal">
      <div className="oracle-content">
        <div className="oracle-header">
          <h2>Ashtakvarga Oracle</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {completeOracleData && (
          <>
            <div className="oracle-insight">
              <div className="cosmic-strength">
                <div className="strength-circle">
                  <span className="strength-value">{completeOracleData.cosmic_strength}%</span>
                  <span className="strength-label">Cosmic Strength</span>
                </div>
              </div>
              
              <div className="oracle-message">
                <h3>Today's Oracle</h3>
                <p>{completeOracleData.oracle_message}</p>
              </div>

              <div className="power-actions">
                <h3>Power Actions</h3>
                <div className="actions-grid">
                  {completeOracleData.power_actions?.map((action, index) => (
                    <div key={index} className={`action-card ${action.type}`}>
                      <span className="action-icon">
                        {action.type === 'do' ? '✅' : '⚠️'}
                      </span>
                      <span className="action-text">{action.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="timeline-section">
              <h3>Timeline Predictions</h3>
              
              <div className="timeline-tabs">
                {timelineCategories.map(category => (
                  <button
                    key={category.id}
                    className={`timeline-tab ${selectedTimelineCategory === category.id ? 'active' : ''}`}
                    onClick={() => setSelectedTimelineCategory(category.id)}
                  >
                    <span className="tab-icon">{category.icon}</span>
                    <span className="tab-name">{category.name}</span>
                  </button>
                ))}
              </div>

              <div className="timeline-events">
                {renderTimelineEvents()}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AshtakavargaOracle;