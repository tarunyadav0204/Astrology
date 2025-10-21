import React, { useState, useEffect } from 'react';
import AspectDetailPopup from './AspectDetailPopup';

const CompactAspectsTable = ({ aspects, natalPlanets, onTimelineClick }) => {
  const [aspectTimelines, setAspectTimelines] = useState({});
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [yearOffset, setYearOffset] = useState(0);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [selectedAspect, setSelectedAspect] = useState(null);

  const loadTimeline = async (aspect, year) => {
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
      
      const data = await response.json();
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
    // Load timelines for all aspects for this year
    aspects?.forEach(aspect => {
      loadTimeline(aspect, year);
    });
  };

  // Auto-load timelines for current year on mount
  useEffect(() => {
    if (aspects && aspects.length > 0) {
      handleYearChange(currentYear);
    }
  }, [aspects]);

  const formatPeriod = (period) => {
    const start = new Date(period.start_date);
    const end = new Date(period.end_date);
    
    if (period.start_date === period.end_date) {
      return start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
    
    // Show full start to end range
    const startStr = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const endStr = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    
    return `${startStr} - ${endStr}`;
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

  const getStrengthColor = (strength) => {
    const colors = {
      'VERY_STRONG': '#28a745',
      'STRONG': '#20c997', 
      'MODERATE': '#ffc107',
      'WEAK': '#fd7e14',
      'VERY_WEAK': '#dc3545'
    };
    return colors[strength] || '#6c757d';
  };

  const isMobile = window.innerWidth <= 768;

  return (
    <div className="nadi-aspects-compact">
      {/* Year Navigation with Title */}
      <div className="year-nav" style={{ background: 'linear-gradient(135deg, #e91e63 0%, #ff6f00 100%)', marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0, paddingTop: '10px', paddingBottom: '10px', paddingLeft: '16px', paddingRight: '16px' }}>
        <div className="nav-title" style={{ background: 'transparent' }}>{isMobile ? 'Nadi Aspects' : 'Nadi Aspects with Timeline'}</div>
        
        <div className="nav-controls" style={{ background: 'transparent' }}>
          <button 
            className="nav-arrow"
            onClick={() => setYearOffset(prev => prev - 1)}
            disabled={yearOffset <= -5}
          >
            ←
          </button>
          
          {Array.from({ length: isMobile ? 5 : 7 }, (_, i) => {
            const year = new Date().getFullYear() + yearOffset + i - (isMobile ? 2 : 3);
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
            disabled={yearOffset >= 5}
          >
            →
          </button>
        </div>
      </div>

      {/* Compact Aspects List */}
      <div className="aspects-list">
        {aspects?.map((aspect, index) => {
          const aspectKey = `${aspect.planet1}-${aspect.planet2}-${aspect.aspect_type}`;
          const timeline = aspectTimelines[aspectKey] || [];
          
          if (isMobile) {
            return (
              <div key={index} className="aspect-row">
                <div className="aspect-info-mobile">
                  <span className="aspect-planet">{aspect.planet1}</span>
                  <span className="aspect-target">→ {aspect.planet2}</span>
                  <span className="aspect-type">
                    {aspect.aspect_type.replace('_ASPECT', '')} Aspect
                  </span>
                </div>
                <div 
                  className="aspect-strength"
                  style={{ color: getStrengthColor(aspect.strength) }}
                >
                  {aspect.strength.replace('_', ' ').substring(0, 6)}
                </div>
                <div className="timeline-chips">
                  {timeline.map((period, pIndex) => (
                    <button
                      key={pIndex}
                      className={`timeline-chip ${getPeriodClass(period)}`}
                      onClick={() => {
                        setSelectedPeriod(period);
                        setSelectedAspect(aspect);
                      }}
                      title={`${period.start_date} to ${period.end_date} (±${period.min_orb?.toFixed(1)}°)`}
                    >
                      {formatPeriod(period)}
                    </button>
                  ))}
                  {timeline.length === 0 && (
                    <span style={{ fontSize: '12px', color: '#999' }}>No periods</span>
                  )}
                </div>
              </div>
            );
          }
          
          return (
            <div key={index} className="aspect-row">
              <div className="aspect-planet">{aspect.planet1}</div>
              <div className="aspect-target">→ {aspect.planet2}</div>
              <div className="aspect-type">
                {aspect.aspect_type.replace('_ASPECT', '')} Aspect
              </div>
              <div className="timeline-chips">
                {timeline.map((period, pIndex) => (
                  <button
                    key={pIndex}
                    className={`timeline-chip ${getPeriodClass(period)}`}
                    onClick={() => {
                      setSelectedPeriod(period);
                      setSelectedAspect(aspect);
                    }}
                    title={`${period.start_date} to ${period.end_date} (±${period.min_orb?.toFixed(1)}°)`}
                  >
                    {formatPeriod(period)}
                  </button>
                ))}
                {timeline.length === 0 && (
                  <span style={{ fontSize: '11px', color: '#999' }}>No periods</span>
                )}
              </div>
              <div 
                className="aspect-strength"
                style={{ color: getStrengthColor(aspect.strength) }}
              >
                {aspect.strength.replace('_', ' ').substring(0, 4)}
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Aspect Detail Popup */}
      {selectedPeriod && selectedAspect && (
        <AspectDetailPopup 
          aspect={selectedAspect}
          period={selectedPeriod}
          onClose={() => {
            setSelectedPeriod(null);
            setSelectedAspect(null);
          }}
          onViewChart={(date) => {
            setSelectedPeriod(null);
            setSelectedAspect(null);
            onTimelineClick(date);
          }}
        />
      )}
    </div>
  );
};

export default CompactAspectsTable;