import React from 'react';
import { 
  TITHI_NAMES, 
  VARA_NAMES, 
  VARA_ENGLISH, 
  VARA_LORDS,
  NAKSHATRA_NAMES, 
  NAKSHATRA_LORDS,
  YOGA_NAMES, 
  KARANA_NAMES 
} from '../config/panchangConfig';

const CorePanchangElements = ({ panchangData }) => {
  if (!panchangData) {
    throw new Error('Panchang data is required');
  }

  const formatTime = (timeString) => {
    if (!timeString) return 'N/A';
    return new Date(timeString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const calculateProgress = (current, total) => {
    return Math.min((current / total) * 100, 100);
  };

  return (
    <div className="core-panchang-elements">
      <div className="panchang-grid">
        
        {/* Tithi */}
        <div className="panchang-element tithi-element">
          <div className="element-header">
            <h3>🌙 Tithi</h3>
            <span className="element-number">{panchangData.tithi.number}/30</span>
          </div>
          
          <div className="element-content">
            <div className="main-value">
              {TITHI_NAMES[panchangData.tithi.number - 1]}
            </div>
            
            <div className="timing-info">
              <div className="time-range">
                <span className="start-time">
                  Starts: {formatTime(panchangData.tithi.start_time)}
                </span>
                <span className="end-time">
                  Ends: {formatTime(panchangData.tithi.end_time)}
                </span>
              </div>
            </div>
            
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${calculateProgress(panchangData.tithi.elapsed, panchangData.tithi.duration)}%` }}
                ></div>
              </div>
              <span className="progress-text">
                {Math.round(calculateProgress(panchangData.tithi.elapsed, panchangData.tithi.duration))}% Complete
              </span>
            </div>
            
            <div className="significance">
              <strong>Lord:</strong> {panchangData.tithi.lord}
            </div>
            
            <div className="next-preview">
              <strong>Next:</strong> {TITHI_NAMES[panchangData.tithi.number % 30]}
            </div>
          </div>
        </div>

        {/* Vara */}
        <div className="panchang-element vara-element">
          <div className="element-header">
            <h3>📅 Vara (Day)</h3>
            <span className="element-number">{panchangData.vara.number}/7</span>
          </div>
          
          <div className="element-content">
            <div className="main-value">
              {VARA_NAMES[panchangData.vara.number - 1]}
            </div>
            
            <div className="english-name">
              {VARA_ENGLISH[panchangData.vara.number - 1]}
            </div>
            
            <div className="ruling-info">
              <div className="ruling-planet">
                <strong>Ruling Planet:</strong> {VARA_LORDS[panchangData.vara.number - 1]}
              </div>
              <div className="ruling-deity">
                <strong>Deity:</strong> {panchangData.vara.deity}
              </div>
            </div>
            
            <div className="day-recommendations">
              <div className="favorable">
                <strong>Favorable:</strong> {panchangData.vara.favorable_activities.join(', ')}
              </div>
              <div className="colors">
                <strong>Lucky Color:</strong> 
                <span 
                  className="color-swatch"
                  style={{ backgroundColor: panchangData.vara.lucky_color }}
                ></span>
                {panchangData.vara.lucky_color}
              </div>
            </div>
          </div>
        </div>

        {/* Nakshatra */}
        <div className="panchang-element nakshatra-element">
          <div className="element-header">
            <h3>⭐ Nakshatra</h3>
            <span className="element-number">{panchangData.nakshatra.number}/27</span>
          </div>
          
          <div className="element-content">
            <div className="main-value">
              {NAKSHATRA_NAMES[panchangData.nakshatra.number - 1]}
            </div>
            
            <div className="timing-info">
              <div className="time-range">
                <span className="start-time">
                  Starts: {formatTime(panchangData.nakshatra.start_time)}
                </span>
                <span className="end-time">
                  Ends: {formatTime(panchangData.nakshatra.end_time)}
                </span>
              </div>
            </div>
            
            <div className="pada-info">
              <strong>Pada:</strong> {panchangData.nakshatra.pada}/4
              <div className="pada-progress">
                <div 
                  className="pada-fill"
                  style={{ width: `${(panchangData.nakshatra.pada / 4) * 100}%` }}
                ></div>
              </div>
            </div>
            
            <div className="nakshatra-details">
              <div className="lord">
                <strong>Lord:</strong> {NAKSHATRA_LORDS[panchangData.nakshatra.number - 1]}
              </div>
              <div className="deity">
                <strong>Deity:</strong> {panchangData.nakshatra.deity}
              </div>
              <div className="nature">
                <strong>Nature:</strong> {panchangData.nakshatra.nature}
              </div>
            </div>
            
            <div className="career-hint">
              <strong>Career Focus:</strong> {panchangData.nakshatra.career_focus}
            </div>
          </div>
        </div>

        {/* Yoga */}
        <div className="panchang-element yoga-element">
          <div className="element-header">
            <h3>🧘 Yoga</h3>
            <span className="element-number">{panchangData.yoga.number}/27</span>
          </div>
          
          <div className="element-content">
            <div className="main-value">
              {YOGA_NAMES[panchangData.yoga.number - 1]}
            </div>
            
            <div className="timing-info">
              <div className="time-range">
                <span className="start-time">
                  Starts: {formatTime(panchangData.yoga.start_time)}
                </span>
                <span className="end-time">
                  Ends: {formatTime(panchangData.yoga.end_time)}
                </span>
              </div>
            </div>
            
            <div className="yoga-significance">
              <div className="effect">
                <strong>Effect:</strong> {panchangData.yoga.effect}
              </div>
              <div className="quality">
                <strong>Quality:</strong> 
                <span className={`quality-badge ${panchangData.yoga.quality.toLowerCase()}`}>
                  {panchangData.yoga.quality}
                </span>
              </div>
            </div>
            
            <div className="recommended-activities">
              <strong>Recommended:</strong> {panchangData.yoga.recommended_activities.join(', ')}
            </div>
            
            <div className="spiritual-practice">
              <strong>Spiritual Practice:</strong> {panchangData.yoga.spiritual_practice}
            </div>
          </div>
        </div>

        {/* Karana */}
        <div className="panchang-element karana-element">
          <div className="element-header">
            <h3>⚡ Karana</h3>
            <span className="element-number">{panchangData.karana.number}/11</span>
          </div>
          
          <div className="element-content">
            <div className="main-value">
              {KARANA_NAMES[panchangData.karana.number - 1]}
            </div>
            
            <div className="timing-info">
              <div className="duration">
                <strong>Duration:</strong> {panchangData.karana.duration} hours
              </div>
            </div>
            
            <div className="karana-significance">
              <div className="nature">
                <strong>Nature:</strong> {panchangData.karana.nature}
              </div>
              <div className="effect">
                <strong>Effect:</strong> {panchangData.karana.effect}
              </div>
            </div>
            
            <div className="suitable-activities">
              <strong>Suitable For:</strong> {panchangData.karana.suitable_activities.join(', ')}
            </div>
            
            <div className="business-recommendation">
              <strong>Business:</strong> 
              <span className={`recommendation ${panchangData.karana.business_suitable ? 'favorable' : 'unfavorable'}`}>
                {panchangData.karana.business_suitable ? 'Favorable' : 'Avoid'}
              </span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default CorePanchangElements;