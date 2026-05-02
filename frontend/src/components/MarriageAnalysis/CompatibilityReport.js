import React from 'react';

const CompatibilityReport = ({ analysis, boyDetails, girlDetails }) => {
  const { manglik_analysis, recommendation, timing_overlay: timingOverlay } = analysis;

  const getManglikSeverityColor = (severity) => {
    switch (severity) {
      case 'High': return '#f44336';
      case 'Medium': return '#ff9800';
      case 'Low': return '#ffc107';
      default: return '#4caf50';
    }
  };

  const getCompatibilityStatusColor = (status) => {
    return status === 'Compatible' ? '#4caf50' : '#f44336';
  };

  return (
    <div className="compatibility-report">
      <div className="partners-summary">
        <div className="partner-card">
          <h4>👨 {boyDetails.name}</h4>
          <p>{boyDetails.date} at {boyDetails.time}</p>
          <div className="manglik-status">
            <span className="status-label">Manglik Status:</span>
            <span 
              className="status-value"
              style={{ color: getManglikSeverityColor(manglik_analysis.boy_manglik.severity) }}
            >
              {manglik_analysis.boy_manglik.is_manglik 
                ? `Yes (${manglik_analysis.boy_manglik.severity})` 
                : 'No'
              }
            </span>
          </div>
        </div>

        <div className="compatibility-arrow">💕</div>

        <div className="partner-card">
          <h4>👩 {girlDetails.name}</h4>
          <p>{girlDetails.date} at {girlDetails.time}</p>
          <div className="manglik-status">
            <span className="status-label">Manglik Status:</span>
            <span 
              className="status-value"
              style={{ color: getManglikSeverityColor(manglik_analysis.girl_manglik.severity) }}
            >
              {manglik_analysis.girl_manglik.is_manglik 
                ? `Yes (${manglik_analysis.girl_manglik.severity})` 
                : 'No'
              }
            </span>
          </div>
        </div>
      </div>

      <div className="manglik-compatibility">
        <h4>🔥 Manglik Compatibility</h4>
        <div className="compatibility-status">
          <span 
            className="status-indicator"
            style={{ color: getCompatibilityStatusColor(manglik_analysis.compatibility.status) }}
          >
            {manglik_analysis.compatibility.status}
          </span>
          <span className="status-description">
            {manglik_analysis.compatibility.description}
          </span>
        </div>
      </div>

      <div className="recommendation-section">
        <h4>📋 Recommendation</h4>
        <div className={`recommendation-card ${recommendation.proceed ? 'positive' : 'negative'}`}>
          <div className="recommendation-text">
            {recommendation.recommendation}
          </div>
          <div className="proceed-indicator">
            {recommendation.proceed ? '✅ Proceed' : '❌ Not Recommended'}
          </div>
        </div>

        {recommendation.timing_note && (
          <div className="recommendation-card" style={{ marginTop: 12 }}>
            <div className="recommendation-text">
              <strong>Timing note:</strong> {recommendation.timing_note}
            </div>
          </div>
        )}

        {timingOverlay?.shared?.next_favorable_windows?.length > 0 && (
          <div className="remedies-section">
            <h5>🗓 Best Joint Windows</h5>
            <ul>
              {timingOverlay.shared.next_favorable_windows.slice(0, 3).map((window, index) => (
                <li key={index}>
                  {window.start_date} to {window.end_date} - {String(window.climate || '').replace(/_/g, ' ')}
                </li>
              ))}
            </ul>
          </div>
        )}

        {recommendation.remedies && recommendation.remedies.length > 0 && (
          <div className="remedies-section">
            <h5>🔮 Suggested Remedies</h5>
            <ul>
              {recommendation.remedies.map((remedy, index) => (
                <li key={index}>{remedy}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompatibilityReport;
