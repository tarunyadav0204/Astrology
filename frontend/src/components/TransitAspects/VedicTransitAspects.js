import React, { useState, useEffect } from 'react';
import './VedicTransitAspects.css';
import AstrologerPredictionPopup from './AstrologerPredictionPopup';

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
    setAspectTimelines({});
    fetchVedicAspects();
    fetchDashaTimeline();
  }, [birthData]);

  useEffect(() => {
    const scrollToCurrentYear = () => {
      const activeButton = document.querySelector('.year-scroll-container .active');
      if (activeButton) {
        activeButton.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
      }
    };
    
    const timer = setTimeout(scrollToCurrentYear, 100);
    return () => clearTimeout(timer);
  }, [currentYear]);

  const fetchVedicAspects = async () => {
    try {
      const response = await fetch('/api/vedic-transit-aspects', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ birth_data: birthData })
      });
      
      const data = await response.json();
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
      setDashaTimeline(data.dasha_timeline || []);
      setDashaDataReady(true);
    } catch (error) {
      console.error('Error fetching dasha timeline:', error);
      setDashaDataReady(false);
    }
  };

  const loadTimeline = async (aspect, year) => {
    try {
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
    if (aspectType === 'nakshatra_connection') {
      if (enhancementType === 'star_lord') {
        return 'Nakshatra Lord 🌟';
      } else if (enhancementType === 'natal_nakshatra') {
        return 'Natal Nakshatra ⭐';
      } else if (enhancementType === 'transit_nakshatra') {
        return 'Transit Nakshatra ⭐';
      } else if (enhancementType === 'nakshatra_return') {
        return 'Nakshatra Return 🔄';
      } else if (enhancementType === 'gandanta') {
        return 'Gandanta Point ⚠️';
      }
      return 'Nakshatra Connection';
    }
    
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
    
    const baseName = aspectMap[aspectType] || aspectType.replace('th_house', 'th');
    
    if (enhancementType === 'star_lord') {
      return `${baseName} 🌟`;
    } else if (enhancementType === 'natal_nakshatra') {
      return `${baseName} ⭐`;
    } else if (enhancementType === 'gandanta') {
      return `${baseName} ⚠️`;
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
    
    if (isDashaRelevant(aspect, period)) {
      baseClass += ' dasha-relevant';
    }
    
    return baseClass;
  };

  const getDashaForPeriod = (periodDate) => {
    if (!dashaTimeline.length) return null;
    
    const targetDate = new Date(periodDate);
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
    
    const dashaLords = [
      periodDashas.mahadasha,
      periodDashas.antardasha,
      periodDashas.pratyantardasha,
      periodDashas.sookshmadasha,
      periodDashas.pranadasha
    ].filter(Boolean);
    
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

  const getGroupedAspects = () => {
    const grouped = {};
    
    aspects.forEach(aspect => {
      const key = `${aspect.planet1}-${aspect.planet2}`;
      if (!grouped[key]) {
        grouped[key] = {
          planet1: aspect.planet1,
          planet2: aspect.planet2,
          aspects: []
        };
      }
      grouped[key].aspects.push(aspect);
    });
    
    return Object.values(grouped);
  };
  
  const getFilteredAspects = () => {
    return getGroupedAspects();
  };
  
  const getCombinedTimeline = (aspectGroup) => {
    const allPeriods = [];
    
    aspectGroup.aspects.forEach(aspect => {
      const timeline = aspectTimelines[`${aspect.planet1}-${aspect.planet2}-${aspect.aspect_type}`] || [];
      timeline.forEach(period => {
        if (!showDashaRelevantOnly || isDashaRelevant(aspect, period)) {
          allPeriods.push({
            ...period,
            aspectType: aspect.aspect_type,
            aspect: aspect
          });
        }
      });
    });
    
    return allPeriods.sort((a, b) => new Date(a.start_date) - new Date(b.start_date));
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
            onClick={() => {
              const container = document.querySelector('.year-scroll-container');
              if (container) container.scrollBy({ left: -200, behavior: 'smooth' });
            }}
          >
            ←
          </button>
          
          <div className="year-scroll-container">
            {Array.from({ length: 201 }, (_, i) => {
              const year = 1900 + i;
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
          </div>
          
          <button 
            className="nav-arrow"
            onClick={() => {
              const container = document.querySelector('.year-scroll-container');
              if (container) container.scrollBy({ left: 200, behavior: 'smooth' });
            }}
          >
            →
          </button>
        </div>
      </div>

      <div className="transit-aspects-list">
        {getFilteredAspects().map((aspectGroup, index) => {
          const combinedTimeline = getCombinedTimeline(aspectGroup);
          
          if (combinedTimeline.length === 0) {
            return null;
          }
          
          return (
            <div key={index} className="transit-aspect-row">
              <div className="aspect-info">
                <span className="transit-planet">{aspectGroup.planet1}</span>
                <span className="aspect-arrow">→</span>
                <span className="target-planet">{aspectGroup.planet2}</span>
              </div>
              <div className="timeline-chips">
                {combinedTimeline.slice(0, 3).map((period, pIndex) => (
                  <button
                    key={pIndex}
                    className={`timeline-chip ${getPeriodClass(period, period.aspect)}`}
                    onClick={(e) => {
                      if (e.shiftKey || e.ctrlKey || e.metaKey) {
                        handlePredictionClick(period.aspect, period, e);
                      } else {
                        onTimelineClick(new Date(period.peak_date || period.start_date));
                      }
                    }}
                    onContextMenu={(e) => {
                      e.preventDefault();
                      handlePredictionClick(period.aspect, period, e);
                    }}
                    title={`${getAspectName(period.aspectType)} aspect\n${period.start_date} to ${period.end_date}${getDashaContext(period.aspect, period) ? '\n' + getDashaContext(period.aspect, period) : ''}\n\nRight-click or Shift+click for prediction`}
                  >
                    <div className="chip-content">
                      <div className="aspect-number">{getAspectName(period.aspectType).replace(/th$/, '')}</div>
                      <div className="period-date">{formatPeriod(period)}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="transit-help-text">
        💡 Right-click or Shift+click on time periods for details
      </div>
      
      <AstrologerPredictionPopup
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