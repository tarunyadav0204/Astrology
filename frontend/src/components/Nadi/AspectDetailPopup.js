import React from 'react';

const AspectDetailPopup = ({ aspect, period, onClose, onViewChart }) => {
  if (!aspect || !period) return null;

  const getAspectMeaning = (aspectType) => {
    const meanings = {
      '1st_ASPECT': 'Direct influence and conjunction energy',
      '2nd_ASPECT': 'Wealth, speech, and family matters',
      '5th_ASPECT': 'Creativity, children, intelligence, and speculation',
      '6th_ASPECT': 'Health, service, obstacles, and enemies',
      '7th_ASPECT': 'Partnerships, marriage, and public relations',
      '9th_ASPECT': 'Fortune, dharma, higher learning, and spirituality'
    };
    return meanings[aspectType] || 'Planetary influence and energy exchange';
  };

  const getPlanetaryEffect = (planet1, planet2, aspectType) => {
    const effects = {
      'Sun-Mars': {
        '5th_ASPECT': 'Increased energy, leadership drive, potential for conflicts in creative pursuits or with children. Favorable for sports, competitions, and bold initiatives.',
        '7th_ASPECT': 'Strong partnerships but potential for ego clashes. Leadership in relationships, possible conflicts with spouse or business partners.'
      },
      'Sun-Moon': {
        '7th_ASPECT': 'Emotional clarity, strong public image, but potential stress between ego and emotions. Good for leadership roles.',
        '6th_ASPECT': 'Health issues related to stress, conflicts between mind and body. Need for emotional balance.'
      },
      'Moon-Mars': {
        '5th_ASPECT': 'Emotional intensity in creative matters, passionate about children or artistic pursuits. Quick emotional reactions.',
        '7th_ASPECT': 'Emotional conflicts in partnerships, passionate relationships with potential for arguments.'
      }
    };
    
    const key = `${planet1}-${planet2}`;
    return effects[key]?.[aspectType] || `${planet1} influences ${planet2} through ${aspectType.replace('_ASPECT', '')} house themes.`;
  };

  const getTimingAdvice = (period) => {
    const now = new Date();
    const startDate = new Date(period.start_date);
    const endDate = new Date(period.end_date);
    
    if (endDate < now) {
      return 'This period has passed. Review events that occurred during this time for patterns.';
    } else if (startDate <= now && now <= endDate) {
      return 'This aspect is currently active! Pay attention to related themes and events happening now.';
    } else {
      return 'Prepare for this upcoming period. Plan activities related to this aspect\'s themes.';
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      weekday: 'short',
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const getStrengthDescription = (orb) => {
    if (orb <= 1) return 'Very Strong - Exact aspect with powerful effects';
    if (orb <= 3) return 'Strong - Clear and noticeable effects';
    if (orb <= 6) return 'Moderate - Subtle but meaningful influence';
    return 'Weak - Background influence';
  };

  return (
    <div className="aspect-popup-overlay" onClick={onClose}>
      <div className="aspect-popup" onClick={(e) => e.stopPropagation()}>
        <div className="popup-header">
          <h3>{aspect.planet1} → {aspect.planet2}</h3>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="popup-content">
          <div className="aspect-info">
            <h4>{aspect.aspect_type.replace('_ASPECT', '')} House Aspect</h4>
            <p className="aspect-meaning">{getAspectMeaning(aspect.aspect_type)}</p>
          </div>

          <div className="period-details">
            <h4>Period Details</h4>
            <div className="detail-row">
              <span className="label">Duration:</span>
              <span className="value">{formatDate(period.start_date)} - {formatDate(period.end_date)}</span>
            </div>
            <div className="detail-row">
              <span className="label">Peak Date:</span>
              <span className="value">{formatDate(period.peak_date || period.start_date)}</span>
            </div>
            <div className="detail-row">
              <span className="label">Orb Strength:</span>
              <span className="value">±{period.min_orb?.toFixed(1)}° - {getStrengthDescription(period.min_orb)}</span>
            </div>
          </div>

          <div className="prediction">
            <h4>Predicted Effects</h4>
            <p>{getPlanetaryEffect(aspect.planet1, aspect.planet2, aspect.aspect_type)}</p>
          </div>

          <div className="timing-advice">
            <h4>Timing Guidance</h4>
            <p>{getTimingAdvice(period)}</p>
          </div>

          <div className="popup-actions">
            <button 
              className="view-chart-btn"
              onClick={() => onViewChart(period.peak_date || period.start_date)}
            >
              View Chart for Peak Date
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AspectDetailPopup;