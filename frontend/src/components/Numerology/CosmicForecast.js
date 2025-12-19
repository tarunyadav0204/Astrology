import React from 'react';
import './CosmicForecast.css';

const CosmicForecast = ({ forecastData }) => {
  if (!forecastData) return null;

  const { current_energy, life_timeline } = forecastData;
  const { personal_year, personal_month, personal_day } = current_energy;

  return (
    <div className="forecast-container">
      
      {/* 1. Daily Dashboard (The Weather) */}
      <div className="weather-card">
        <div className="weather-header">
          <h4>Cosmic Weather</h4>
          <span style={{fontSize: '0.8rem', color: '#666'}}>{current_energy.analysis_date}</span>
        </div>

        <div className="current-cycle">
          <div className="cycle-badge">{personal_day.number}</div>
          <div className="cycle-label">Personal Day {personal_day.number}</div>
          <p style={{color: '#666', fontSize: '0.9rem', marginTop: '5px'}}>
            Month {personal_month.number} | Year {personal_year.number}
          </p>
        </div>

        <div className="advice-section">
          <p style={{margin: 0, fontStyle: 'italic', color: '#444'}}>
            "{personal_day.meaning}"
          </p>
        </div>
        
        {/* Add Daily Synthesis */}
        {current_energy.daily_guidance && (
          <div className="daily-synthesis" style={{ marginTop: '15px', padding: '15px', background: '#fff3e0', borderRadius: '8px', fontStyle: 'italic' }}>
            <p><strong>💡 Daily Insight:</strong> {current_energy.daily_guidance}</p>
            <p style={{ fontSize: '0.8em', color: '#888', marginTop: '5px' }}>
              🧮 Logic: {current_energy.calculation_logic}
            </p>
          </div>
        )}
      </div>

      {/* 2. Life Phases (Pinnacles) */}
      <div className="timeline-card">
        <h3 className="timeline-header">🗓️ Your Life Journey Map</h3>
        <p style={{fontSize: '0.9rem', color: '#666', marginBottom: '20px', fontStyle: 'italic'}}>
          Life unfolds in 4 major phases, each with its own energy and lessons. Here's your roadmap:
        </p>
        
        {life_timeline?.pinnacles && Object.entries(life_timeline.pinnacles).map(([key, phase], i) => {
          const phaseNames = {
            first: "🌱 Foundation Years",
            second: "🚀 Growth & Learning", 
            third: "🎯 Mastery & Achievement",
            fourth: "🌟 Wisdom & Legacy"
          };
          
          const phaseDescriptions = {
            first: "Building your identity and core skills",
            second: "Expanding horizons and developing talents",
            third: "Peak performance and major accomplishments", 
            fourth: "Sharing wisdom and leaving your mark"
          };
          
          return (
            <div className="phase-row" key={i} style={{marginBottom: '15px', padding: '15px', background: '#f8f9fa', borderRadius: '10px'}}>
              <div style={{flex: 1}}>
                <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px'}}>
                  <span className="phase-age" style={{background: '#e91e63', color: 'white', padding: '4px 8px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 'bold'}}>
                    Age {phase.age_range}
                  </span>
                  <strong style={{color: '#333'}}>{phaseNames[key] || key}</strong>
                </div>
                <div className="phase-info">
                  <p style={{margin: '5px 0', color: '#666', fontSize: '0.85rem'}}>
                    {phaseDescriptions[key]}
                  </p>
                  <p style={{margin: '5px 0', color: '#444', fontSize: '0.9rem'}}>
                    <strong>Focus:</strong> {phase.meaning.split('(')[0].trim()}
                  </p>
                  <p style={{margin: '0', color: '#888', fontSize: '0.8rem', fontStyle: 'italic'}}>
                    {phase.meaning.match(/\(([^)]+)\)/)?.[1] || 'Key life theme'}
                  </p>
                </div>
              </div>
              <div className="phase-number" style={{background: 'linear-gradient(135deg, #e91e63, #f06292)', color: 'white', width: '50px', height: '50px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', fontWeight: 'bold'}}>
                {phase.number}
              </div>
            </div>
          );
        })}
        
        <div style={{marginTop: '20px', padding: '15px', background: 'rgba(233, 30, 99, 0.1)', borderRadius: '10px', border: '1px solid rgba(233, 30, 99, 0.2)'}}>
          <p style={{margin: '0', fontSize: '0.85rem', color: '#666'}}>
            💡 <strong>How to use this:</strong> Each pinnacle number reveals the main energy and opportunities of that life phase. 
            Focus on developing the qualities of your current pinnacle number for maximum growth and success.
          </p>
        </div>
      </div>

    </div>
  );
};

export default CosmicForecast;