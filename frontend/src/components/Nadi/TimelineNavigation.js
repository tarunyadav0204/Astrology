import React, { useState } from 'react';

const TimelineNavigation = ({ aspect, natalPlanets, onTimelineLoad }) => {
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false);

  const loadTimeline = async (year) => {
    setLoading(true);
    console.log('Loading timeline for aspect:', aspect);
    try {
      const response = await fetch('/api/nadi-timeline', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          natal_planets: natalPlanets,
          aspect_type: aspect.aspect_type,
          planet1: aspect.planet1,
          planet2: aspect.planet2,
          start_year: year,
          year_range: 1
        })
      });
      
      console.log('Request sent:', {
        aspect_type: aspect.aspect_type,
        planet1: aspect.planet1,
        planet2: aspect.planet2,
        year: year
      });
      
      const data = await response.json();
      console.log('Timeline data received:', data);
      console.log('Timeline periods:', data.timeline);
      onTimelineLoad(aspect, data.timeline);
    } catch (error) {
      console.error('Error loading timeline:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePrevYear = () => {
    const newYear = currentYear - 1;
    setCurrentYear(newYear);
    loadTimeline(newYear);
  };

  const handleNextYear = () => {
    const newYear = currentYear + 1;
    setCurrentYear(newYear);
    loadTimeline(newYear);
  };

  const handleCurrentYear = () => {
    const thisYear = new Date().getFullYear();
    setCurrentYear(thisYear);
    loadTimeline(thisYear);
  };

  return (
    <div className="timeline-navigation">
      <button 
        onClick={handlePrevYear} 
        disabled={loading}
        className="nav-button"
      >
        ← {currentYear - 1}
      </button>
      
      <button 
        onClick={handleCurrentYear}
        disabled={loading}
        className="current-year-button"
      >
        {currentYear} {loading && '⏳'}
      </button>
      
      <button 
        onClick={handleNextYear}
        disabled={loading}
        className="nav-button"
      >
        {currentYear + 1} →
      </button>
    </div>
  );
};

export default TimelineNavigation;