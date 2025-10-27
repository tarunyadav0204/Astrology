import React from 'react';

const CareerTiming = ({ careerData }) => {
  if (!careerData?.career_timing) return <div>Loading timing...</div>;
  
  const timing = careerData.career_timing;
  
  return (
    <div className="career-timing">
      <h3>⏰ Career Timing Analysis</h3>
      
      <div className="current-period">
        <h4>📅 Current Period</h4>
        {timing.current_period ? (
          <div className="period-info">
            <p><strong>Mahadasha:</strong> {timing.current_period.planet}</p>
            <p><strong>Period:</strong> {timing.current_period.start} - {timing.current_period.end}</p>
          </div>
        ) : (
          <p>Current period analysis in progress...</p>
        )}
      </div>
      
      <div className="favorable-periods">
        <h4>🌟 Favorable Periods</h4>
        <ul>
          {timing.favorable_periods.map((period, index) => (
            <li key={index}>{period}</li>
          ))}
        </ul>
      </div>
      
      <div className="timing-recommendations">
        <h4>💡 Timing Recommendations</h4>
        <ul>
          {timing.timing_recommendations.map((rec, index) => (
            <li key={index}>{rec}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default CareerTiming;