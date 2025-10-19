import React, { useState, useEffect } from 'react';
import './VedicTransitAspects.css';

const VedicTransitAspects = ({ birthData, onTimelineClick }) => {
  const [aspectTimelines, setAspectTimelines] = useState({});
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [yearOffset, setYearOffset] = useState(0);
  const [aspects, setAspects] = useState([]);

  useEffect(() => {
    fetchVedicAspects();
  }, [birthData]);

  const fetchVedicAspects = async () => {
    try {
      console.log('Fetching Vedic aspects for:', birthData);
      const response = await fetch('/api/vedic-transit-aspects', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ birth_data: birthData })
      });
      
      const data = await response.json();
      console.log('Received aspects data:', data);
      setAspects(data.aspects || []);
    } catch (error) {
      console.error('Error fetching Vedic aspects:', error);
    }
  };

  const loadTimeline = async (aspect, year) => {
    try {
      console.log('Loading timeline for:', aspect, 'year:', year);
      const response = await fetch('/api/vedic-transit-timeline', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          birth_data: birthData,
          aspect_type: aspect.aspect_type,
          planet1: aspect.planet1,
          planet2: aspect.planet2,
          start_year: year,
          year_range: 1
        })
      });
      
      const data = await response.json();
      console.log('Received timeline data:', data);
      const aspectKey = `${aspect.planet1}-${aspect.planet2}-${aspect.aspect_type}`;
      setAspectTimelines(prev => ({
        ...prev,
        [aspectKey]: data.timeline || []
      }));
    } catch (error) {
      console.error('Error loading timeline:', error);
    }
  };

  const handleYearChange = (year) => {
    setCurrentYear(year);
    aspects.forEach(aspect => {
      loadTimeline(aspect, year);
    });
  };

  useEffect(() => {
    if (aspects.length > 0) {
      handleYearChange(currentYear);
    }
  }, [aspects]);

  const formatPeriod = (period) => {
    const start = new Date(period.start_date);
    const end = new Date(period.end_date);
    
    if (period.start_date === period.end_date) {
      return start.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
    }
    
    const startStr = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const endStr = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const startYear = start.getFullYear().toString().slice(-2);
    const endYear = end.getFullYear().toString().slice(-2);
    
    if (startYear === endYear) {
      return `${startStr} - ${endStr} '${startYear}`;
    } else {
      return `${startStr} '${startYear} - ${endStr} '${endYear}`;
    }
  };
  
  const getAspectName = (aspectType) => {
    const aspectMap = {
      '3th_house': '3rd',
      '4th_house': '4th', 
      '5th_house': '5th',
      '7th_house': '7th',
      '8th_house': '8th',
      '9th_house': '9th',
      '10th_house': '10th'
    };
    return aspectMap[aspectType] || aspectType;
  };

  const getPeriodClass = (period) => {
    const now = new Date();
    const startDate = new Date(period.start_date);
    const endDate = new Date(period.end_date);
    
    if (endDate < now) {
      return 'past';
    } else if (startDate <= now && now <= endDate) {
      return 'current';
    } else {
      return 'future';
    }
  };

  return (
    <div className="vedic-transit-aspects">
      {/* Year Navigation */}
      <div className="transit-year-nav">
        <div className="nav-title">Transit Aspects</div>
        
        <div className="nav-controls">
          <button 
            className="nav-arrow"
            onClick={() => setYearOffset(prev => prev - 1)}
            disabled={yearOffset <= -3}
          >
            ←
          </button>
          
          {Array.from({ length: 5 }, (_, i) => {
            const year = new Date().getFullYear() + yearOffset + i - 2;
            return (
              <button
                key={year}
                className={currentYear === year ? 'active' : ''}
                onClick={() => handleYearChange(year)}
              >
                {year}
              </button>
            );
          })}
          
          <button 
            className="nav-arrow"
            onClick={() => setYearOffset(prev => prev + 1)}
            disabled={yearOffset >= 3}
          >
            →
          </button>
        </div>
      </div>

      {/* Compact Aspects List */}
      <div className="transit-aspects-list">
        {aspects.slice(0, 8).map((aspect, index) => {
          const aspectKey = `${aspect.planet1}-${aspect.planet2}-${aspect.aspect_type}`;
          const timeline = aspectTimelines[aspectKey] || [];
          
          return (
            <div key={index} className="transit-aspect-row">
              <div className="aspect-info">
                <span className="transit-planet">{aspect.planet1}</span>
                <span className="aspect-arrow">→</span>
                <span className="target-planet">{aspect.planet2}</span>
                <span className="aspect-house">({getAspectName(aspect.aspect_type)})</span>
              </div>
              <div className="timeline-chips">
                {timeline.slice(0, 3).map((period, pIndex) => (
                  <button
                    key={pIndex}
                    className={`timeline-chip ${getPeriodClass(period)}`}
                    onClick={() => onTimelineClick(new Date(period.peak_date || period.start_date))}
                    title={`${period.start_date} to ${period.end_date}`}
                  >
                    {formatPeriod(period)}
                  </button>
                ))}
                {timeline.length === 0 && (
                  <span className="no-periods">No periods</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default VedicTransitAspects;