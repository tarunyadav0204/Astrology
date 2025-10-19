import React from 'react';

const TimelinePicker = ({ timeline, onTimeClick }) => {
  console.log('TimelinePicker received timeline:', timeline);
  const formatPeriod = (period) => {
    if (period.start_date === period.end_date) {
      return period.start_date;
    }
    return `${period.start_date.slice(5)} to ${period.end_date.slice(5)}`;
  };

  const getPeriodClass = (period) => {
    const now = new Date();
    const startDate = new Date(period.start_date);
    const endDate = new Date(period.end_date);
    
    if (endDate < now) {
      return 'period-past';
    } else if (startDate <= now && now <= endDate) {
      return 'period-current';
    } else {
      return 'period-future';
    }
  };

  const handlePeriodClick = (period) => {
    // Use peak date for most accurate timing
    const targetDate = period.peak_date || period.start_date;
    onTimeClick(targetDate);
  };

  if (!timeline || timeline.length === 0) {
    return <div className="timeline-picker">No periods found for selected year</div>;
  }

  return (
    <div className="timeline-picker">
      {timeline.map((period, index) => (
        <button
          key={index}
          className={`period-button ${getPeriodClass(period)}`}
          onClick={() => handlePeriodClick(period)}
          title={`Orb: ±${period.min_orb.toFixed(1)}° | Peak: ${period.peak_date}`}
        >
          {formatPeriod(period)}
        </button>
      ))}
    </div>
  );
};

export default TimelinePicker;