import React from 'react';

const TimingAnalysis = ({ data, loading }) => {
  if (loading) {
    return <div className="analysis-loading">Analyzing Career Timing...</div>;
  }

  if (!data) {
    return <div className="analysis-error">Unable to load timing analysis</div>;
  }

  return (
    <div className="timing-analysis">
      <h3>⏰ Career Timing Analysis</h3>
      
      {data.current_period && (
        <div className="current-period">
          <h4>🔄 Current Career Period</h4>
          <div className="period-card current">
            <div className="period-header">
              <h5>{data.current_period.dasha_lord} Mahadasha</h5>
              <span className="period-dates">
                {data.current_period.start_date} - {data.current_period.end_date}
              </span>
            </div>
            <div className="period-analysis">
              <div className="career-impact">
                <span className="impact-label">Career Impact:</span>
                <span className={`impact-value impact-${data.current_period.career_impact?.toLowerCase()}`}>
                  {data.current_period.career_impact}
                </span>
              </div>
              <p>{data.current_period.interpretation}</p>
            </div>
          </div>
        </div>
      )}

      {data.upcoming_periods && data.upcoming_periods.length > 0 && (
        <div className="upcoming-periods">
          <h4>📈 Upcoming Career Periods</h4>
          <div className="periods-timeline">
            {data.upcoming_periods.map((period, index) => (
              <div key={index} className="period-card upcoming">
                <div className="period-header">
                  <h5>{period.dasha_lord} Period</h5>
                  <span className="period-dates">
                    {period.start_date} - {period.end_date}
                  </span>
                </div>
                <div className="period-analysis">
                  <div className="career-impact">
                    <span className="impact-label">Expected Impact:</span>
                    <span className={`impact-value impact-${period.career_impact?.toLowerCase()}`}>
                      {period.career_impact}
                    </span>
                  </div>
                  <p>{period.interpretation}</p>
                  {period.key_opportunities && (
                    <div className="opportunities">
                      <strong>Key Opportunities:</strong>
                      <ul>
                        {period.key_opportunities.map((opp, idx) => (
                          <li key={idx}>{opp}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.major_transits && data.major_transits.length > 0 && (
        <div className="major-transits">
          <h4>🌟 Major Career Transits</h4>
          <div className="transits-list">
            {data.major_transits.map((transit, index) => (
              <div key={index} className="transit-card">
                <div className="transit-header">
                  <h5>{transit.planet} Transit</h5>
                  <span className="transit-date">{transit.date}</span>
                </div>
                <div className="transit-details">
                  <div className="transit-info">
                    <span className="label">Through:</span>
                    <span className="value">{transit.through_house}th House</span>
                  </div>
                  <div className="transit-info">
                    <span className="label">Impact:</span>
                    <span className={`value impact-${transit.impact?.toLowerCase()}`}>
                      {transit.impact}
                    </span>
                  </div>
                  <p>{transit.interpretation}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.career_peaks && data.career_peaks.length > 0 && (
        <div className="career-peaks">
          <h4>🏆 Career Peak Periods</h4>
          <div className="peaks-timeline">
            {data.career_peaks.map((peak, index) => (
              <div key={index} className="peak-card">
                <div className="peak-age">Age {peak.age}</div>
                <div className="peak-year">{peak.year}</div>
                <div className="peak-description">{peak.description}</div>
                <div className="peak-strength">
                  <span className="strength-label">Strength:</span>
                  <div className="strength-meter">
                    <div 
                      className="meter-fill" 
                      style={{ width: `${peak.strength}%` }}
                    ></div>
                    <span className="strength-value">{peak.strength}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.recommendations && (
        <div className="timing-recommendations">
          <h4>💡 Timing Recommendations</h4>
          <div className="recommendations-list">
            {data.recommendations.map((rec, index) => (
              <div key={index} className="recommendation-item">
                <div className="rec-type">{rec.type}</div>
                <div className="rec-timing">{rec.timing}</div>
                <div className="rec-description">{rec.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TimingAnalysis;