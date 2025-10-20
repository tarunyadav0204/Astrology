import React, { useState, useEffect } from 'react';
import './VedicTransitAspects.css';
import PredictionPopup from './PredictionPopup';

const VedicTransitAspects = ({ birthData, onTimelineClick, natalChart }) => {
  const [aspectTimelines, setAspectTimelines] = useState({});
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [yearOffset, setYearOffset] = useState(0);
  const [aspects, setAspects] = useState([]);
  const [dashaTimeline, setDashaTimeline] = useState([]);
  const [showDashaRelevantOnly, setShowDashaRelevantOnly] = useState(false);
  const [dashaDataReady, setDashaDataReady] = useState(false);
  const [showPredictionPopup, setShowPredictionPopup] = useState(false);
  const [selectedAspect, setSelectedAspect] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState(null);

  useEffect(() => {
    // Clear cached timelines when birthData changes
    setAspectTimelines({});
    fetchVedicAspects();
    fetchDashaTimeline();
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

  const fetchDashaTimeline = async () => {
    try {
      const response = await fetch('/api/dasha-timeline', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Cache-Control': 'no-cache'
        },
        body: JSON.stringify({
          birth_data: birthData,
          start_year: 2020,
          end_year: 2030,
          _cache_bust: Date.now()
        })
      });
      
      const data = await response.json();
      console.log('[DASHA_DEBUG] Fresh dasha timeline received:', data.dasha_timeline?.[0]);
      setDashaTimeline(data.dasha_timeline || []);
      setDashaDataReady(true);
    } catch (error) {
      console.error('Error fetching dasha timeline:', error);
      setDashaDataReady(false);
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
          year_range: 1,
          required_transit_house: aspect.required_transit_house,
          enhancement_type: aspect.enhancement_type
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
    // Clear cached timelines for new year
    setAspectTimelines({});
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
  
  const getAspectTooltip = (aspect) => {
    if (aspect.description) {
      return aspect.description;
    }
    
    let tooltip = `${aspect.planet1} → ${aspect.planet2}`;
    
    if (aspect.aspect_type === 'nakshatra_connection') {
      if (aspect.enhancement_type === 'star_lord') {
        tooltip += ` - ${aspect.planet1} is the star lord of ${aspect.planet2}'s nakshatra`;
      } else if (aspect.enhancement_type === 'natal_nakshatra') {
        tooltip += ` - ${aspect.planet2} is placed in ${aspect.planet1}'s nakshatra`;
      }
      if (aspect.natal_nakshatra) {
        tooltip += ` (${aspect.natal_nakshatra})`;
      }
    } else {
      tooltip += ` - ${getAspectName(aspect.aspect_type, aspect.enhancement_type)} aspect`;
    }
    
    return tooltip;
  };

  const getAspectName = (aspectType, enhancementType) => {
    // Handle nakshatra-only connections
    if (aspectType === 'nakshatra_connection') {
      if (enhancementType === 'star_lord') {
        return 'Nakshatra Lord 🌟';
      } else if (enhancementType === 'natal_nakshatra') {
        return 'Natal Nakshatra ⭐';
      } else if (enhancementType === 'transit_nakshatra') {
        return 'Transit Nakshatra ⭐';
      } else if (enhancementType === 'nakshatra_return') {
        return 'Nakshatra Return 🔄';
      }
      return 'Nakshatra Connection';
    }
    
    // Regular geometric aspects
    const aspectMap = {
      '1th_house': '1st',
      '2th_house': '2nd', 
      '3th_house': '3rd',
      '4th_house': '4th', 
      '5th_house': '5th',
      '6th_house': '6th',
      '7th_house': '7th',
      '8th_house': '8th',
      '9th_house': '9th',
      '10th_house': '10th',
      '11th_house': '11th',
      '12th_house': '12th'
    };
    
    const baseName = aspectMap[aspectType] || aspectType;
    
    // Add enhancement indicators to regular aspects
    if (enhancementType === 'star_lord') {
      return `${baseName} 🌟`;
    } else if (enhancementType === 'natal_nakshatra') {
      return `${baseName} ⭐`;
    }
    
    return baseName;
  };

  const getPeriodClass = (period, aspect) => {
    const now = new Date();
    const startDate = new Date(period.start_date);
    const endDate = new Date(period.end_date);
    
    let baseClass = '';
    if (endDate < now) {
      baseClass = 'past';
    } else if (startDate <= now && now <= endDate) {
      baseClass = 'current';
    } else {
      baseClass = 'future';
    }
    
    // Add dasha-relevant class
    if (isDashaRelevant(aspect, period)) {
      baseClass += ' dasha-relevant';
    }
    
    return baseClass;
  };

  const getDashaForPeriod = (periodDate) => {
    if (!dashaTimeline.length) return null;
    
    const targetDate = new Date(periodDate);
    // Find the closest dasha entry before or on the target date
    let closestDasha = null;
    
    for (const dasha of dashaTimeline) {
      const dashaDate = new Date(dasha.date);
      if (dashaDate <= targetDate) {
        closestDasha = dasha;
      } else {
        break;
      }
    }
    
    return closestDasha;
  };

  const isDashaRelevant = (aspect, period) => {
    if (!dashaDataReady) return false;
    
    const periodDashas = getDashaForPeriod(period.start_date);
    if (!periodDashas) return false;
    
    // Get all dasha levels from the data structure
    const dashaLords = [
      periodDashas.mahadasha,
      periodDashas.antardasha,
      periodDashas.pratyantardasha,
      periodDashas.sookshmadasha,
      periodDashas.pranadasha
    ].filter(Boolean);
    
    // Debug for Mars->Sun aspects
    if (aspect.planet1 === 'Mars' && aspect.planet2 === 'Sun') {
      console.log(`[DASHA_DEBUG] Mars->Sun dasha check for ${period.start_date}:`);
      console.log(`[DASHA_DEBUG] Full dasha data:`, periodDashas);
      console.log(`[DASHA_DEBUG] All dashas: ${dashaLords.join(', ')}`);
      console.log(`[DASHA_DEBUG] Relevant: ${dashaLords.includes(aspect.planet1) || dashaLords.includes(aspect.planet2)}`);
    }
    
    return dashaLords.includes(aspect.planet1) || dashaLords.includes(aspect.planet2);
  };

  const getDashaContext = (aspect, period) => {
    if (!dashaDataReady) return '';
    
    const periodDashas = getDashaForPeriod(period.start_date);
    if (!periodDashas) return '';
    
    const relevantDashas = [];
    if (periodDashas.mahadasha === aspect.planet1 || periodDashas.mahadasha === aspect.planet2) {
      relevantDashas.push(`${periodDashas.mahadasha} Maha`);
    }
    if (periodDashas.antardasha === aspect.planet1 || periodDashas.antardasha === aspect.planet2) {
      relevantDashas.push(`${periodDashas.antardasha} Antar`);
    }
    return relevantDashas.length > 0 ? `During ${relevantDashas.join('-')} period` : '';
  };

  const getFilteredAspects = () => {
    if (!showDashaRelevantOnly) return aspects;
    
    return aspects.filter(aspect => {
      const timeline = aspectTimelines[`${aspect.planet1}-${aspect.planet2}-${aspect.aspect_type}`] || [];
      return timeline.some(period => isDashaRelevant(aspect, period));
    });
  };

  const handlePredictionClick = (aspect, period, event) => {
    event.stopPropagation();
    setSelectedAspect(aspect);
    setSelectedPeriod(period);
    setShowPredictionPopup(true);
  };

  const getDashaDataForPeriod = (period) => {
    const periodDashas = getDashaForPeriod(period.start_date);
    if (!periodDashas) return null;
    
    return {
      mahadasha: periodDashas.mahadasha,
      antardasha: periodDashas.antardasha,
      pratyantardasha: periodDashas.pratyantardasha
    };
  };

  return (
    <div className="vedic-transit-aspects">
      {/* Year Navigation */}
      <div className="transit-year-nav">
        <div className="nav-title">Transit Aspects</div>
        
        <div className="nav-controls">
          <button 
            className={`dasha-filter ${showDashaRelevantOnly ? 'active' : ''}`}
            onClick={() => setShowDashaRelevantOnly(!showDashaRelevantOnly)}
            title={dashaDataReady ? "Show only dasha-relevant aspects" : "Loading dasha data..."}
            disabled={!dashaDataReady}
          >
            {dashaDataReady ? '🎯' : '⏳'}
          </button>
          <button 
            className="nav-arrow"
            onClick={() => setYearOffset(prev => prev - 1)}
            disabled={yearOffset <= -10}
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
            disabled={yearOffset >= 10}
          >
            →
          </button>
        </div>
      </div>

      {/* Compact Aspects List */}
      <div className="transit-aspects-list">
        {getFilteredAspects().slice(0, 8).map((aspect, index) => {
          const aspectKey = `${aspect.planet1}-${aspect.planet2}-${aspect.aspect_type}`;
          const timeline = aspectTimelines[aspectKey] || [];
          
          return (
            <div key={index} className="transit-aspect-row" title={getAspectTooltip(aspect)}>
              <div className="aspect-info">
                <span className="transit-planet">{aspect.planet1}</span>
                <span className="aspect-arrow">→</span>
                <span className="target-planet">{aspect.planet2}</span>
                <span className={`aspect-house ${aspect.enhancement_type || 'regular'}`}>
                  ({getAspectName(aspect.aspect_type, aspect.enhancement_type)})
                </span>
              </div>
              <div className="timeline-chips">
                {timeline.slice(0, 3).map((period, pIndex) => (
                  <button
                    key={pIndex}
                    className={`timeline-chip ${getPeriodClass(period, aspect)}`}
                    onClick={(e) => {
                      if (e.shiftKey || e.ctrlKey || e.metaKey) {
                        handlePredictionClick(aspect, period, e);
                      } else {
                        onTimelineClick(new Date(period.peak_date || period.start_date));
                      }
                    }}
                    onContextMenu={(e) => {
                      e.preventDefault();
                      handlePredictionClick(aspect, period, e);
                    }}
                    title={`${period.start_date} to ${period.end_date}${getDashaContext(aspect, period) ? '\n' + getDashaContext(aspect, period) : ''}\n\nRight-click or Shift+click for prediction`}
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
      
      <PredictionPopup
        isOpen={showPredictionPopup}
        onClose={() => setShowPredictionPopup(false)}
        aspect={selectedAspect}
        period={selectedPeriod}
        birthData={birthData}
        natalChart={natalChart}
        dashaData={selectedPeriod ? getDashaDataForPeriod(selectedPeriod) : null}
      />
    </div>
  );
};

export default VedicTransitAspects;